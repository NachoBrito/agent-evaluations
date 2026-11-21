"""Run agentic flow evaluations as a tracked Arize Phoenix Experiment."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from collections.abc import Mapping
from typing import Any

from phoenix.client import Client
from phoenix.client.experiments import run_experiment
from rich.console import Console
from rich.table import Table

from agent_evaluation.telemetry import setup_telemetry
from evals.evaluators.deterministic import (
    evaluate_efficiency_budget,
    evaluate_forbidden_and_turn_tools,
    evaluate_groundedness,
    evaluate_trajectory_match,
)
from evals.evaluators.llm_judge import (
    build_judge_llm,
    evaluate_response_quality,
    evaluate_trajectory_quality,
)
from evals.harness import (
    DEFAULT_DATASET_PATH,
    DomainToolCall,
    FlowRunResult,
    TurnResult,
    load_flow_cases,
    run_flow_case,
)

console = Console()


def _serialize_run(run: FlowRunResult) -> dict[str, Any]:
    return {
        "case_id": run.case_id,
        "final_response": run.final_response,
        "total_latency_seconds": round(run.total_latency_seconds, 3),
        "openai_trajectory": run.openai_trajectory,
        "domain_tool_calls": [
            {"name": c.name, "args": c.args, "turn_index": c.turn_index}
            for c in run.domain_tool_calls
        ],
        "turns": [
            {
                "turn_index": t.turn_index,
                "user_input": t.user_input,
                "final_response": t.final_response,
                "latency_seconds": round(t.latency_seconds, 3),
                "domain_tool_calls": [
                    {"name": c.name, "args": c.args, "turn_index": c.turn_index}
                    for c in t.domain_tool_calls
                ],
            }
            for t in run.turns
        ],
    }


def _deserialize_run(output: dict[str, Any]) -> FlowRunResult:
    turns = [
        TurnResult(
            turn_index=t["turn_index"],
            user_input=t["user_input"],
            new_messages=[],
            domain_tool_calls=[
                DomainToolCall(
                    name=c["name"],
                    args=c["args"],
                    turn_index=c["turn_index"],
                )
                for c in t.get("domain_tool_calls", [])
            ],
            final_response=t["final_response"],
            latency_seconds=float(t.get("latency_seconds", 0.0)),
        )
        for t in output.get("turns", [])
    ]
    domain_calls = [
        DomainToolCall(
            name=c["name"],
            args=c["args"],
            turn_index=c["turn_index"],
        )
        for c in output.get("domain_tool_calls", [])
    ]
    return FlowRunResult(
        case_id=output["case_id"],
        turns=turns,
        all_messages=[],
        domain_tool_calls=domain_calls,
        openai_trajectory=output.get("openai_trajectory", []),
        final_response=output.get("final_response", ""),
        total_latency_seconds=float(output.get("total_latency_seconds", 0.0)),
    )


def _outcome_to_phoenix(outcome) -> dict[str, Any]:
    return {
        "score": outcome.score,
        "label": "pass" if outcome.passed else "fail",
        "explanation": outcome.reason,
    }


def _get_or_create_dataset(client: Client, name: str, cases: list[dict[str, Any]]):
    inputs = [
        {
            "case_id": case["id"],
            "category": case.get("category", "general"),
            "description": case.get("description", ""),
            "turns": case.get("turns", []),
        }
        for case in cases
    ]
    try:
        return client.datasets.get_dataset(dataset=name)
    except Exception:
        return client.datasets.create_dataset(
            name=name,
            inputs=inputs,
            outputs=[{} for _ in inputs],
        )


def _resolve_case(
    example_input: Mapping[str, Any],
    cases_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    case_id = example_input.get("case_id")
    if isinstance(case_id, str) and case_id in cases_by_id:
        return cases_by_id[case_id]
    raw_case = example_input.get("case")
    if isinstance(raw_case, dict):
        return raw_case
    if isinstance(raw_case, str):
        return json.loads(raw_case)
    raise ValueError(f"Could not resolve flow case from example input: {example_input!r}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Weather Agent flow evaluations as an Arize Phoenix Experiment."
    )
    parser.add_argument(
        "--dataset-file",
        default=str(DEFAULT_DATASET_PATH),
        help="Path to YAML dataset file.",
    )
    parser.add_argument(
        "--dataset-name",
        default="weather-agent-flows",
        help="Dataset name in Arize Phoenix.",
    )
    parser.add_argument(
        "--experiment-name",
        default="weather-agent-flow-eval",
        help="Experiment name in Arize Phoenix.",
    )
    parser.add_argument(
        "--with-judge",
        action="store_true",
        help="Also run LLM-as-a-Judge rubric evaluators.",
    )
    parser.add_argument(
        "--dry-run",
        type=int,
        default=None,
        help="Run only the first N examples without persisting to Phoenix.",
    )
    args = parser.parse_args()

    tracer_provider = setup_telemetry(project_name="weather-agent-evals")
    try:
        cases = load_flow_cases(args.dataset_file)
        cases_by_id = {case["id"]: case for case in cases}
        phoenix_base_url = os.environ.get("PHOENIX_BASE_URL", "http://localhost:6006")
        client = Client(base_url=phoenix_base_url)
        dataset = _get_or_create_dataset(client, args.dataset_name, cases)

        def run_agent_task(example) -> dict[str, Any]:
            example_input = example["input"] if isinstance(example, Mapping) else example.input
            case = _resolve_case(example_input, cases_by_id)
            run_result = asyncio.run(run_flow_case(case))
            return _serialize_run(run_result)

        def trajectory_match(input, output):
            case = _resolve_case(input, cases_by_id)
            return _outcome_to_phoenix(
                evaluate_trajectory_match(_deserialize_run(output), case)
            )

        def tool_policy(input, output):
            case = _resolve_case(input, cases_by_id)
            return _outcome_to_phoenix(
                evaluate_forbidden_and_turn_tools(_deserialize_run(output), case)
            )

        def efficiency_budget(input, output):
            case = _resolve_case(input, cases_by_id)
            return _outcome_to_phoenix(
                evaluate_efficiency_budget(_deserialize_run(output), case)
            )

        def groundedness(input, output):
            case = _resolve_case(input, cases_by_id)
            return _outcome_to_phoenix(
                evaluate_groundedness(_deserialize_run(output), case)
            )

        evaluators: list[Any] = [
            trajectory_match,
            tool_policy,
            efficiency_budget,
            groundedness,
        ]

        if args.with_judge:
            judge_llm = build_judge_llm()

            def trajectory_quality(input, output):
                case = _resolve_case(input, cases_by_id)
                return _outcome_to_phoenix(
                    evaluate_trajectory_quality(
                        _deserialize_run(output), case, judge_llm=judge_llm
                    )
                )

            def response_quality(input, output):
                case = _resolve_case(input, cases_by_id)
                return _outcome_to_phoenix(
                    evaluate_response_quality(
                        _deserialize_run(output), case, judge_llm=judge_llm
                    )
                )

            evaluators.extend([trajectory_quality, response_quality])

        experiment = run_experiment(
            dataset=dataset,
            task=run_agent_task,
            evaluators=evaluators,
            experiment_name=args.experiment_name,
            dry_run=args.dry_run if args.dry_run is not None else False,
            timeout=180,
            client=client,
        )

        table = Table(title=f"Phoenix Experiment: {args.experiment_name}")
        table.add_column("Metric", style="bold cyan")
        table.add_column("Details", style="green")
        table.add_row("Dataset", args.dataset_name)
        table.add_row("Examples", str(len(cases)))
        table.add_row("Phoenix UI", phoenix_base_url)
        if getattr(experiment, "id", None):
            table.add_row("Experiment ID", str(experiment.id))
        console.print(table)
    finally:
        if tracer_provider is not None:
            tracer_provider.shutdown()


if __name__ == "__main__":
    main()
