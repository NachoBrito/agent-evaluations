"""End-to-end agentic flow evaluation suite against weather_flows.yaml.

Run with:
    uv run pytest tests/test_agentic_flows.py --run-live-agent
    uv run pytest tests/test_agentic_flows.py --run-live-agent --run-judge
"""

from __future__ import annotations

import pytest

from evals.evaluators.deterministic import run_deterministic_evaluators
from evals.evaluators.llm_judge import run_llm_judge_evaluators
from evals.harness import load_flow_cases, run_flow_case

FLOW_CASES = load_flow_cases()


@pytest.mark.live_agent
@pytest.mark.asyncio
@pytest.mark.parametrize("case", FLOW_CASES, ids=[c["id"] for c in FLOW_CASES])
async def test_weather_agentic_flow(case: dict, request: pytest.FixtureRequest) -> None:
    run_result = await run_flow_case(case)

    outcomes = run_deterministic_evaluators(run_result, case)
    if request.config.getoption("--run-judge"):
        outcomes.extend(run_llm_judge_evaluators(run_result, case))

    failures = [f"[{o.name}] {o.reason}" for o in outcomes if not o.passed]
    assert not failures, (
        f"Flow '{case['id']}' failed {len(failures)} check(s):\n"
        + "\n".join(f"  - {f}" for f in failures)
        + f"\nFinal response: {run_result.final_response!r}"
        + f"\nDomain tool calls: {[(c.turn_index, c.name, c.args) for c in run_result.domain_tool_calls]}"
        + f"\nSkill loaded (SKILL.md): {run_result.skill_loaded}"
    )
