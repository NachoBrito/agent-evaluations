"""LLM-as-a-Judge rubric evaluators backed by Arize Phoenix Evals."""

from __future__ import annotations

import json
import os
from typing import Any

from phoenix.evals import LLM, create_classifier

from agent_evaluation.weather_agent import DEFAULT_LLM_BASE_URL, DEFAULT_LLM_MODEL
from evals.evaluators.deterministic import EvalOutcome
from evals.harness import FlowRunResult

TRAJECTORY_QUALITY_TEMPLATE = """You are an expert evaluator of AI weather agents.
Review the multi-turn conversation and tool-call trajectory below, and judge whether the
agent followed the required behavior cleanly, efficiently, and honestly.

Rubric Criteria:
{rubric_criteria}

Agent Trajectory:
{trajectory}

Did the agent's trajectory satisfy the rubric criteria?
Respond with 'pass' if all key requirements were met, or 'fail' if the agent violated any requirement."""

RESPONSE_QUALITY_TEMPLATE = """You are an expert evaluator grading a Weather Assistant's final response.
The assistant must follow these style and accuracy guidelines:
- Friendly, clear, and concise (human-friendly, not raw tool output)
- Accurate to the tool results (never fabricates weather data or multi-day forecasts)
- Includes city name, conditions, and temperature with °C or °F when temperature was retrieved or required by the Task Rubric (do not penalize omitting temperature on narrow condition-only questions like "Is it raining?")
- Honest and transparent when a city is not found, a service fails, or a request is out of scope

Task Rubric:
{rubric_criteria}

User Input(s):
{user_inputs}

Final Assistant Response:
{final_response}

Does the final response meet these quality guidelines?
Respond with 'pass' or 'fail'."""


def build_judge_llm(
    *,
    base_url: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> LLM:
    """Create a Phoenix Evals LLM configured for a local or remote OpenAI-compatible server."""
    resolved_base_url = (
        base_url
        or os.environ.get("EVAL_JUDGE_BASE_URL")
        or os.environ.get("LLM_BASE_URL")
        or DEFAULT_LLM_BASE_URL
    )
    resolved_model = (
        model
        or os.environ.get("EVAL_JUDGE_MODEL")
        or os.environ.get("LLM_MODEL")
        or DEFAULT_LLM_MODEL
    )
    resolved_api_key = (
        api_key
        or os.environ.get("EVAL_JUDGE_API_KEY")
        or os.environ.get("LLM_API_KEY")
        or "not-needed"
    )
    return LLM(
        provider="openai",
        model=resolved_model,
        base_url=resolved_base_url,
        api_key=resolved_api_key,
    )


def _format_trajectory(run: FlowRunResult) -> str:
    return json.dumps(run.openai_trajectory, indent=2, ensure_ascii=False)


def _score_to_outcome(name: str, eval_result: Any) -> EvalOutcome:
    # phoenix.evals classifiers return a list[Score] or a single Score object
    score_obj = eval_result[0] if isinstance(eval_result, list) else eval_result
    label = str(getattr(score_obj, "label", "")).strip().lower()
    numeric = getattr(score_obj, "score", None)
    explanation = str(getattr(score_obj, "explanation", "") or f"Judge label: {label}")
    passed = label == "pass" or (numeric is not None and float(numeric) >= 0.5)
    final_score = float(numeric) if numeric is not None else (1.0 if passed else 0.0)
    return EvalOutcome(
        name=name,
        passed=passed,
        score=final_score,
        reason=explanation,
    )


def evaluate_trajectory_quality(
    run: FlowRunResult,
    case: dict[str, Any],
    *,
    judge_llm: LLM | None = None,
) -> EvalOutcome:
    """Grade overall multi-turn trajectory quality using an LLM judge."""
    llm = judge_llm or build_judge_llm()
    evaluator = create_classifier(
        name="trajectory_quality",
        prompt_template=TRAJECTORY_QUALITY_TEMPLATE,
        llm=llm,
        choices={"pass": 1.0, "fail": 0.0},
    )
    result = evaluator.evaluate(
        {
            "rubric_criteria": case.get("rubric_criteria", "Follow weather assistant rules."),
            "trajectory": _format_trajectory(run),
        }
    )
    return _score_to_outcome("trajectory_quality", result)


def evaluate_response_quality(
    run: FlowRunResult,
    case: dict[str, Any],
    *,
    judge_llm: LLM | None = None,
) -> EvalOutcome:
    """Grade final response tone, formatting, and honesty using an LLM judge."""
    if not run.final_response.strip():
        return EvalOutcome(
            name="response_quality",
            passed=False,
            score=0.0,
            reason="Final agent response is empty.",
        )

    llm = judge_llm or build_judge_llm()
    evaluator = create_classifier(
        name="response_quality",
        prompt_template=RESPONSE_QUALITY_TEMPLATE,
        llm=llm,
        choices={"pass": 1.0, "fail": 0.0},
    )
    result = evaluator.evaluate(
        {
            "rubric_criteria": case.get("rubric_criteria", "Follow weather assistant rules."),
            "user_inputs": "\n".join(
                f"Turn {i + 1}: {t.user_input}" for i, t in enumerate(run.turns)
            ),
            "final_response": run.final_response,
        }
    )
    return _score_to_outcome("response_quality", result)


def run_llm_judge_evaluators(
    run: FlowRunResult,
    case: dict[str, Any],
    *,
    judge_llm: LLM | None = None,
) -> list[EvalOutcome]:
    """Run all LLM-as-a-Judge rubric evaluators."""
    llm = judge_llm or build_judge_llm()
    return [
        evaluate_trajectory_quality(run, case, judge_llm=llm),
        evaluate_response_quality(run, case, judge_llm=llm),
    ]
