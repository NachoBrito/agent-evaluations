"""Execution harness for single-turn and multi-turn agentic flow evaluations."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agent_evaluation.weather_agent import create_weather_agent

from .fakes import FakeWeatherClient

DOMAIN_TOOLS: frozenset[str] = frozenset({"get_weather", "get_temperature"})
DEFAULT_DATASET_PATH = Path(__file__).parent / "datasets" / "weather_flows.yaml"


@dataclass(frozen=True)
class DomainToolCall:
    """A single domain-level tool invocation captured from an agent trajectory."""

    name: str
    args: dict[str, Any]
    turn_index: int
    call_id: str | None = None


@dataclass
class TurnResult:
    """Captured state for a single user turn in a flow."""

    turn_index: int
    user_input: str
    new_messages: list[Any]
    domain_tool_calls: list[DomainToolCall]
    final_response: str
    latency_seconds: float


@dataclass
class FlowRunResult:
    """Complete execution trace and metrics for an agentic flow run."""

    case_id: str
    turns: list[TurnResult]
    all_messages: list[Any]
    domain_tool_calls: list[DomainToolCall]
    openai_trajectory: list[dict[str, Any]]
    final_response: str
    total_latency_seconds: float
    fake_client_log: list[dict[str, Any]] = field(default_factory=list)


def extract_text_content(content: Any) -> str:
    """Extract plain text from a LangChain message content field."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        ]
        return "\n".join(p for p in parts if p).strip()
    return str(content).strip()


def extract_domain_tool_calls(
    messages: list[Any],
    turn_index: int = 0,
    domain_tools: frozenset[str] = DOMAIN_TOOLS,
) -> list[DomainToolCall]:
    """Extract only domain tool calls from LangChain messages, ignoring middleware tools."""
    calls: list[DomainToolCall] = []
    for msg in messages:
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                name = tc.get("name", "")
                if name in domain_tools:
                    calls.append(
                        DomainToolCall(
                            name=name,
                            args=dict(tc.get("args") or {}),
                            turn_index=turn_index,
                            call_id=tc.get("id"),
                        )
                    )
    return calls


def to_openai_domain_trajectory(
    messages: list[Any],
    domain_tools: frozenset[str] = DOMAIN_TOOLS,
) -> list[dict[str, Any]]:
    """Convert LangChain messages into OpenAI-style trajectory dicts for agentevals.

    Internal middleware tool calls (e.g., reading SKILL.md or AGENTS.md) and their
    corresponding ToolMessages are filtered out so trajectory matching focuses on
    domain agent behavior.
    """
    trajectory: list[dict[str, Any]] = []
    domain_call_ids: set[str] = set()

    for msg in messages:
        if isinstance(msg, HumanMessage):
            trajectory.append(
                {"role": "user", "content": extract_text_content(msg.content)}
            )
        elif isinstance(msg, AIMessage):
            raw_calls = getattr(msg, "tool_calls", None) or []
            filtered_calls = []
            for tc in raw_calls:
                name = tc.get("name", "")
                if name in domain_tools:
                    call_id = tc.get("id")
                    if call_id:
                        domain_call_ids.add(call_id)
                    filtered_calls.append(
                        {
                            "function": {
                                "name": name,
                                "arguments": json.dumps(tc.get("args") or {}, sort_keys=True),
                            }
                        }
                    )

            text = extract_text_content(msg.content)
            if filtered_calls:
                entry: dict[str, Any] = {
                    "role": "assistant",
                    "content": text,
                    "tool_calls": filtered_calls,
                }
                trajectory.append(entry)
            elif text:
                trajectory.append({"role": "assistant", "content": text})
        elif isinstance(msg, ToolMessage):
            name = getattr(msg, "name", "")
            call_id = getattr(msg, "tool_call_id", None)
            if name in domain_tools or (call_id and call_id in domain_call_ids):
                trajectory.append(
                    {
                        "role": "tool",
                        "content": extract_text_content(msg.content),
                    }
                )

    return trajectory


def load_flow_cases(path: Path | str = DEFAULT_DATASET_PATH) -> list[dict[str, Any]]:
    """Load evaluation flow cases from a YAML dataset file."""
    dataset_path = Path(path)
    with dataset_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return list(data.get("cases", []))


def build_fake_client(case: dict[str, Any]) -> FakeWeatherClient:
    """Instantiate a FakeWeatherClient configured for a specific flow case."""
    cfg = case.get("fake_client") or {}
    return FakeWeatherClient(fail_mode=cfg.get("fail_mode"))


async def run_flow_case(
    case: dict[str, Any],
    *,
    base_url: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    thread_id: str | None = None,
) -> FlowRunResult:
    """Run a single-turn or multi-turn evaluation case against the Weather Agent."""
    fake_client = build_fake_client(case)
    agent = create_weather_agent(
        weather_client=fake_client,
        base_url=base_url,
        model=model,
        api_key=api_key,
    )
    resolved_thread_id = thread_id or f"eval-{case['id']}-{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": resolved_thread_id}}

    turns: list[TurnResult] = []
    all_messages: list[Any] = []
    all_domain_calls: list[DomainToolCall] = []
    total_latency = 0.0

    for idx, user_prompt in enumerate(case["turns"]):
        prev_count = len(all_messages)
        start = time.perf_counter()
        result = await agent.ainvoke(
            {"messages": [("user", user_prompt)]},
            config=config,
        )
        latency = time.perf_counter() - start
        total_latency += latency

        messages = list(result.get("messages", []))
        new_messages = messages[prev_count:]
        all_messages = messages

        turn_calls = extract_domain_tool_calls(new_messages, turn_index=idx)
        all_domain_calls.extend(turn_calls)

        turn_final = ""
        for msg in reversed(new_messages):
            if isinstance(msg, AIMessage):
                text = extract_text_content(msg.content)
                if text:
                    turn_final = text
                    break

        turns.append(
            TurnResult(
                turn_index=idx,
                user_input=user_prompt,
                new_messages=new_messages,
                domain_tool_calls=turn_calls,
                final_response=turn_final,
                latency_seconds=latency,
            )
        )

    final_response = turns[-1].final_response if turns else ""
    openai_traj = to_openai_domain_trajectory(all_messages)

    return FlowRunResult(
        case_id=case["id"],
        turns=turns,
        all_messages=all_messages,
        domain_tool_calls=all_domain_calls,
        openai_trajectory=openai_traj,
        final_response=final_response,
        total_latency_seconds=total_latency,
        fake_client_log=list(fake_client.call_log),
    )
