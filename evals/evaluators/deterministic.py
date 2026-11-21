"""Deterministic evaluators for agentic flow trajectories and outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from agentevals.trajectory.match import create_trajectory_match_evaluator

from evals.harness import DomainToolCall, FlowRunResult


@dataclass(frozen=True)
class EvalOutcome:
    """Standardized result for a single evaluator check."""

    name: str
    passed: bool
    score: float
    reason: str


def _normalize_city(value: Any) -> str:
    if not isinstance(value, str):
        return str(value).strip().lower()
    # Allow "Madrid" to match "Madrid, Spain"
    return value.strip().lower().split(",")[0].strip()


def _normalize_unit(value: Any) -> str:
    if value is None:
        return "celsius"
    norm = str(value).strip().lower()
    if norm in ("c", "°c", "celsius"):
        return "celsius"
    if norm in ("f", "°f", "fahrenheit"):
        return "fahrenheit"
    return norm


def _match_weather_args(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    if "city" in expected:
        if _normalize_city(actual.get("city")) != _normalize_city(expected["city"]):
            return False
    return True


def _match_temperature_args(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    if "city" in expected:
        if _normalize_city(actual.get("city")) != _normalize_city(expected["city"]):
            return False
    if "unit" in expected:
        if _normalize_unit(actual.get("unit")) != _normalize_unit(expected["unit"]):
            return False
    return True


def _build_reference_trajectory(expected_tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not expected_tool_calls:
        return []
    return [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc.get("args") or {}, sort_keys=True),
                    }
                }
                for tc in expected_tool_calls
            ],
        }
    ]


def evaluate_trajectory_match(
    run: FlowRunResult,
    case: dict[str, Any],
) -> EvalOutcome:
    """Compare captured domain tool-call trajectory against expected reference calls."""
    expected_calls: list[dict[str, Any]] = list(case.get("expected_tool_calls") or [])
    mode: str = case.get("trajectory_match_mode", "unordered")

    if not expected_calls:
        if mode == "strict":
            passed = len(run.domain_tool_calls) == 0
            reason = (
                "No domain tool calls made as expected."
                if passed
                else f"Expected 0 domain tool calls, got: {[(c.name, c.args) for c in run.domain_tool_calls]}"
            )
            return EvalOutcome(
                name="trajectory_match",
                passed=passed,
                score=1.0 if passed else 0.0,
                reason=reason,
            )
        return EvalOutcome(
            name="trajectory_match",
            passed=True,
            score=1.0,
            reason=f"No mandatory reference tool calls required (mode={mode}).",
        )

    evaluator = create_trajectory_match_evaluator(
        trajectory_match_mode=mode,
        tool_args_match_mode="exact",
        tool_args_match_overrides={
            "get_weather": _match_weather_args,
            "get_temperature": _match_temperature_args,
        },
    )
    reference_outputs = _build_reference_trajectory(expected_calls)
    result = evaluator(outputs=run.openai_trajectory, reference_outputs=reference_outputs)
    passed = bool(result.get("score"))
    actual_summary = [(c.name, c.args) for c in run.domain_tool_calls]
    expected_summary = [(c["name"], c.get("args", {})) for c in expected_calls]
    reason = (
        f"Trajectory matched ({mode}): {actual_summary}"
        if passed
        else f"Trajectory mismatch ({mode}). Expected {expected_summary}, got {actual_summary}"
    )
    return EvalOutcome(
        name="trajectory_match",
        passed=passed,
        score=1.0 if passed else 0.0,
        reason=reason,
    )


def evaluate_forbidden_and_turn_tools(
    run: FlowRunResult,
    case: dict[str, Any],
) -> EvalOutcome:
    """Verify overall forbidden tools and per-turn forbidden/required tool constraints."""
    violations: list[str] = []

    overall_forbidden = set(case.get("forbidden_tools") or [])
    if overall_forbidden:
        called = [c.name for c in run.domain_tool_calls if c.name in overall_forbidden]
        if called:
            violations.append(f"Forbidden tool(s) called: {called}")

    for assertion in case.get("turn_assertions") or []:
        turn_idx = int(assertion["turn_index"])
        if turn_idx >= len(run.turns):
            violations.append(f"Turn {turn_idx} missing from run (only {len(run.turns)} turns).")
            continue

        turn_tool_names = [c.name for c in run.turns[turn_idx].domain_tool_calls]
        turn_forbidden = set(assertion.get("forbidden_tools") or [])
        bad = [t for t in turn_tool_names if t in turn_forbidden]
        if bad:
            violations.append(f"Turn {turn_idx} called forbidden tool(s): {bad}")

        turn_required = list(assertion.get("required_tools") or [])
        missing = [t for t in turn_required if t not in turn_tool_names]
        if missing:
            violations.append(
                f"Turn {turn_idx} missed required tool(s): {missing} (called: {turn_tool_names})"
            )

    passed = len(violations) == 0
    return EvalOutcome(
        name="tool_policy",
        passed=passed,
        score=1.0 if passed else 0.0,
        reason="All tool policy and per-turn constraints satisfied."
        if passed
        else "; ".join(violations),
    )


def _canonical_call_key(call: DomainToolCall) -> tuple[int, str, str]:
    normalized_args = dict(call.args)
    if "city" in normalized_args:
        normalized_args["city"] = _normalize_city(normalized_args["city"])
    if call.name == "get_temperature":
        normalized_args["unit"] = _normalize_unit(normalized_args.get("unit"))
    return (call.turn_index, call.name, json.dumps(normalized_args, sort_keys=True))


def evaluate_efficiency_budget(
    run: FlowRunResult,
    case: dict[str, Any],
) -> EvalOutcome:
    """Check domain tool-call budget and detect redundant duplicate tool calls."""
    issues: list[str] = []
    max_calls = case.get("max_tool_calls")
    if max_calls is not None and len(run.domain_tool_calls) > int(max_calls):
        issues.append(
            f"Exceeded max_tool_calls ({len(run.domain_tool_calls)} > {max_calls})."
        )

    if not case.get("allow_duplicate_calls", False):
        seen: set[tuple[int, str, str]] = set()
        duplicates: list[str] = []
        for call in run.domain_tool_calls:
            key = _canonical_call_key(call)
            if key in seen:
                duplicates.append(f"turn {call.turn_index}: {call.name}({call.args})")
            seen.add(key)
        if duplicates:
            issues.append(f"Duplicate redundant tool call(s) detected: {duplicates}")

    passed = len(issues) == 0
    return EvalOutcome(
        name="efficiency_budget",
        passed=passed,
        score=1.0 if passed else 0.0,
        reason=f"Within budget ({len(run.domain_tool_calls)} tool calls, no duplicate loops)."
        if passed
        else "; ".join(issues),
    )


def evaluate_groundedness(
    run: FlowRunResult,
    case: dict[str, Any],
) -> EvalOutcome:
    """Verify grounded tokens appear in the final response and forbidden strings do not."""
    response_lower = run.final_response.lower()
    issues: list[str] = []

    if not response_lower.strip():
        issues.append("Final agent response is empty.")
    else:
        for group in case.get("grounded_any_of") or []:
            if not any(token.lower() in response_lower for token in group):
                issues.append(f"Expected one of {group} in final response.")

        for forbidden in case.get("forbidden_substrings") or []:
            if forbidden.lower() in response_lower:
                issues.append(f"Found forbidden substring {forbidden!r} in final response.")

    passed = len(issues) == 0
    return EvalOutcome(
        name="groundedness",
        passed=passed,
        score=1.0 if passed else 0.0,
        reason="Final response is grounded in expected tool outputs."
        if passed
        else "; ".join(issues),
    )


def run_deterministic_evaluators(
    run: FlowRunResult,
    case: dict[str, Any],
) -> list[EvalOutcome]:
    """Run the full deterministic evaluator suite for a flow run."""
    return [
        evaluate_trajectory_match(run, case),
        evaluate_forbidden_and_turn_tools(run, case),
        evaluate_efficiency_budget(run, case),
        evaluate_groundedness(run, case),
    ]
