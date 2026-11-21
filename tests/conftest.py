"""Pytest configuration and CLI options for agentic flow evaluations."""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-live-agent",
        action="store_true",
        default=False,
        help="Run end-to-end agentic flow evals against the local LLM (llama-server).",
    )
    parser.addoption(
        "--run-judge",
        action="store_true",
        default=False,
        help="Also run LLM-as-a-Judge rubric evaluators on live agent flows.",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "live_agent: marks end-to-end tests that require a running LLM server (use --run-live-agent).",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--run-live-agent"):
        return
    skip_live = pytest.mark.skip(reason="Pass --run-live-agent to run live LLM flow evals.")
    for item in items:
        if "live_agent" in item.keywords:
            item.add_marker(skip_live)
