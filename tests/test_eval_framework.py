"""Fast offline unit tests for the evaluation harness, fakes, and deterministic evaluators."""

from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from evals.evaluators.deterministic import (
    evaluate_efficiency_budget,
    evaluate_forbidden_and_turn_tools,
    evaluate_groundedness,
    evaluate_trajectory_match,
    run_deterministic_evaluators,
)
from evals.fakes import FakeWeatherClient
from evals.harness import (
    FlowRunResult,
    TurnResult,
    extract_domain_tool_calls,
    load_flow_cases,
    to_openai_domain_trajectory,
)


def _make_run(case_id: str, turns_messages: list[tuple[str, list]]) -> FlowRunResult:
    all_messages = []
    all_calls = []
    turns = []
    for idx, (user_input, msgs) in enumerate(turns_messages):
        all_messages.extend(msgs)
        turn_calls = extract_domain_tool_calls(msgs, turn_index=idx)
        all_calls.extend(turn_calls)
        final_text = ""
        for m in reversed(msgs):
            if isinstance(m, AIMessage) and isinstance(m.content, str) and m.content.strip():
                final_text = m.content.strip()
                break
        turns.append(
            TurnResult(
                turn_index=idx,
                user_input=user_input,
                new_messages=msgs,
                domain_tool_calls=turn_calls,
                final_response=final_text,
                latency_seconds=0.1,
            )
        )
    return FlowRunResult(
        case_id=case_id,
        turns=turns,
        all_messages=all_messages,
        domain_tool_calls=all_calls,
        openai_trajectory=to_openai_domain_trajectory(all_messages),
        final_response=turns[-1].final_response if turns else "",
        total_latency_seconds=0.1 * len(turns),
    )


def test_dataset_loads_all_cases():
    cases = load_flow_cases()
    assert len(cases) >= 10
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids)), "Case IDs must be unique"
    assert "madrid_happy_path_default_celsius" in ids
    assert "multi_turn_clarification_flow" in ids


def test_fake_weather_client_happy_and_error_paths():
    client = FakeWeatherClient()
    cond = client.get_weather("Madrid")
    assert cond.location == "Madrid, Spain"
    assert cond.description == "Clear sky"

    temp_c = client.get_temperature("Madrid", unit="celsius")
    assert temp_c.temperature == 14.0
    assert temp_c.unit == "celsius"

    temp_f = client.get_temperature("Tokyo", unit="fahrenheit")
    assert temp_f.temperature == 68.0
    assert temp_f.unit == "fahrenheit"

    with pytest.raises(ValueError, match="Could not find"):
        client.get_weather("Atlantis")

    with pytest.raises(ValueError, match="Unsupported temperature unit"):
        client.get_temperature("Berlin", unit="kelvin")

    outage_client = FakeWeatherClient(fail_mode="service_outage")
    with pytest.raises(RuntimeError, match="simulated outage"):
        outage_client.get_weather("Paris")


def test_middleware_tool_calls_are_filtered_from_domain_trajectory():
    messages = [
        HumanMessage(content="What is the weather in Madrid?"),
        AIMessage(
            content="",
            tool_calls=[
                {"name": "read_file", "args": {"path": "./skills/weather/SKILL.md"}, "id": "mw-1"},
            ],
        ),
        ToolMessage(content="# Weather Skill ...", name="read_file", tool_call_id="mw-1"),
        AIMessage(
            content="",
            tool_calls=[
                {"name": "get_temperature", "args": {"city": "madrid"}, "id": "dom-1"},
                {"name": "get_weather", "args": {"city": "Madrid, Spain"}, "id": "dom-2"},
            ],
        ),
        ToolMessage(content="The temperature in Madrid, Spain is 14.0°C.", name="get_temperature", tool_call_id="dom-1"),
        ToolMessage(content="The weather in Madrid, Spain is clear sky.", name="get_weather", tool_call_id="dom-2"),
        AIMessage(content="In Madrid, it's clear sky and 14°C—great weather for a walk!"),
    ]
    run = _make_run("madrid_happy_path_default_celsius", [("What is the weather in Madrid?", messages)])
    assert [c.name for c in run.domain_tool_calls] == ["get_temperature", "get_weather"]

    case = next(c for c in load_flow_cases() if c["id"] == "madrid_happy_path_default_celsius")
    outcomes = run_deterministic_evaluators(run, case)
    assert all(o.passed for o in outcomes), [(o.name, o.reason) for o in outcomes]


def test_forbidden_tools_fails_when_vague_prompt_calls_weather_tool():
    messages = [
        HumanMessage(content="What's the weather outside?"),
        AIMessage(
            content="",
            tool_calls=[{"name": "get_weather", "args": {"city": "outside"}, "id": "c1"}],
        ),
        ToolMessage(content="Error: Could not find a location matching 'outside'.", name="get_weather", tool_call_id="c1"),
        AIMessage(content="Which city would you like me to check?"),
    ]
    run = _make_run("vague_location_no_tools", [("What's the weather outside?", messages)])
    case = next(c for c in load_flow_cases() if c["id"] == "vague_location_no_tools")

    traj_outcome = evaluate_trajectory_match(run, case)
    policy_outcome = evaluate_forbidden_and_turn_tools(run, case)
    assert not traj_outcome.passed
    assert not policy_outcome.passed


def test_multi_turn_clarification_flow_pass_and_turn1_violation():
    turn1_ok = [
        HumanMessage(content="Is it raining here?"),
        AIMessage(content="Which city would you like me to check the weather for?"),
    ]
    turn2_ok = [
        HumanMessage(content="Sorry, I meant London."),
        AIMessage(
            content="",
            tool_calls=[{"name": "get_weather", "args": {"city": "London"}, "id": "c2"}],
        ),
        ToolMessage(content="The weather in London, United Kingdom is moderate rain.", name="get_weather", tool_call_id="c2"),
        AIMessage(content="Yes, London currently has moderate rain—bring an umbrella!"),
    ]
    case = next(c for c in load_flow_cases() if c["id"] == "multi_turn_clarification_flow")
    ok_run = _make_run(case["id"], [("Is it raining here?", turn1_ok), ("Sorry, I meant London.", turn2_ok)])
    outcomes = run_deterministic_evaluators(ok_run, case)
    assert all(o.passed for o in outcomes), [(o.name, o.reason) for o in outcomes]

    # Now violate Turn 1 by calling get_weather prematurely
    turn1_bad = [
        HumanMessage(content="Is it raining here?"),
        AIMessage(
            content="",
            tool_calls=[{"name": "get_weather", "args": {"city": "here"}, "id": "c1"}],
        ),
        ToolMessage(content="Error: Could not find 'here'.", name="get_weather", tool_call_id="c1"),
        AIMessage(content="Which city?"),
    ]
    bad_run = _make_run(case["id"], [("Is it raining here?", turn1_bad), ("Sorry, I meant London.", turn2_ok)])
    policy_outcome = evaluate_forbidden_and_turn_tools(bad_run, case)
    assert not policy_outcome.passed
    assert "Turn 0" in policy_outcome.reason


def test_efficiency_budget_detects_duplicate_tool_loop():
    messages = [
        HumanMessage(content="Weather in Madrid?"),
        AIMessage(
            content="",
            tool_calls=[
                {"name": "get_weather", "args": {"city": "Madrid"}, "id": "c1"},
                {"name": "get_weather", "args": {"city": "madrid"}, "id": "c2"},
            ],
        ),
        AIMessage(content="It is 14°C and clear in Madrid."),
    ]
    run = _make_run("loop_case", [("Weather in Madrid?", messages)])
    outcome = evaluate_efficiency_budget(run, {"max_tool_calls": 4})
    assert not outcome.passed
    assert "Duplicate" in outcome.reason


def test_groundedness_fails_on_missing_expected_token():
    messages = [
        HumanMessage(content="Weather in Madrid?"),
        AIMessage(content="It is sunny and warm today."),
    ]
    run = _make_run("madrid_happy_path_default_celsius", [("Weather in Madrid?", messages)])
    case = next(c for c in load_flow_cases() if c["id"] == "madrid_happy_path_default_celsius")
    outcome = evaluate_groundedness(run, case)
    assert not outcome.passed
    assert "14°C" in outcome.reason


def test_phoenix_llm_judge_instantiation():
    from evals.evaluators.llm_judge import (
        TRAJECTORY_QUALITY_TEMPLATE,
        build_judge_llm,
    )
    from phoenix.evals import create_classifier

    llm = build_judge_llm(
        base_url="http://localhost:8080/v1",
        model="local-model",
        api_key="not-needed",
    )
    classifier = create_classifier(
        name="trajectory_quality",
        prompt_template=TRAJECTORY_QUALITY_TEMPLATE,
        llm=llm,
        choices={"pass": 1.0, "fail": 0.0},
    )
    assert classifier.name == "trajectory_quality"


def test_weather_agent_has_default_checkpointer():
    from agent_evaluation.weather_agent import create_weather_agent

    agent = create_weather_agent(weather_client=FakeWeatherClient())
    assert getattr(agent, "checkpointer", None) is not None


def test_response_quality_fails_immediately_on_empty_response():
    from evals.evaluators.llm_judge import evaluate_response_quality

    run = _make_run("empty_case", [("Hello", [HumanMessage(content="Hello"), AIMessage(content="   ")])])
    outcome = evaluate_response_quality(run, {"rubric_criteria": "Must answer."})
    assert not outcome.passed
    assert outcome.score == 0.0
    assert "empty" in outcome.reason.lower()


def test_detect_skill_loaded():
    from evals.harness import detect_skill_loaded

    with_skill = [
        AIMessage(
            content="",
            tool_calls=[{"name": "read_file", "args": {"path": "./skills/weather/SKILL.md"}, "id": "mw-1"}],
        ),
    ]
    without_skill = [
        AIMessage(
            content="",
            tool_calls=[{"name": "get_weather", "args": {"city": "Madrid"}, "id": "dom-1"}],
        ),
    ]
    assert detect_skill_loaded(with_skill) is True
    assert detect_skill_loaded(without_skill) is False
