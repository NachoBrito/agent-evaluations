# Agentic Flow Evaluation Analysis — 2026-11-22_14-47-29

## 1. Execution Summary & Metrics

| Metric | Value |
| :--- | :--- |
| **Timestamp** | `2026-11-22_14-47-29` |
| **Git HEAD** | `06ee2b4` (`fix(evals): group trajectory_quality input by explicit user turn`) |
| **Command** | `uv run pytest tests/test_agentic_flows.py --run-live-agent --run-judge` |
| **Scenarios** | **10 / 10 passed (100%)** |
| **Individual Checks** | **60 / 60 passed (100%)** |
| **Deterministic Checks** | **40 / 40 passed (100%)** |
| **LLM-as-a-Judge Checks** | **20 / 20 passed (100%)** |
| **Total Duration** | 477.20s (7m 57s, ~47.7s avg/scenario) |
| **Warnings** | 17 `DeprecationWarning`s from `langsmith/_internal/_beta_decorator.py` (`asyncio.iscoroutinefunction`) |
| **Raw Output** | [report](./report) |
| **Progress Comparison** | [progress.md](./progress.md) |
| **Proposed Tasks** | [tasks.md](./tasks.md) |

### Scenario Breakdown

| # | Scenario (`weather_flows.yaml`) | Category | Status | Failed Evaluators |
| :---: | :--- | :--- | :---: | :--- |
| 1 | `madrid_happy_path_default_celsius` | `happy_path` | **PASS** | — |
| 2 | `tokyo_explicit_fahrenheit` | `unit_normalization` | **PASS** | — |
| 3 | `multi_city_comparison` | `multi_city` | **PASS** | — |
| 4 | `vague_location_no_tools` | `input_validation` | **PASS** | — |
| 5 | `multi_turn_clarification_flow` | `multi_turn` | **PASS** | — |
| 6 | `multi_turn_unit_followup` | `multi_turn` | **PASS** | — |
| 7 | `unknown_city_error_recovery` | `error_recovery` | **PASS** | — |
| 8 | `service_outage_error_recovery` | `error_recovery` | **PASS** | — |
| 9 | `unsupported_unit_kelvin` | `edge_case` | **PASS** | — |
| 10 | `out_of_scope_forecast` | `scope_adherence` | **PASS** | — |

### Evaluator Pass Rates (Across 10 Scenarios)

| Evaluator | Type | Pass Rate | Failed Scenarios |
| :--- | :--- | :---: | :--- |
| `efficiency_budget` | Deterministic | **10/10 (100%)** | None |
| `trajectory_match` | Deterministic | **10/10 (100%)** | None |
| `tool_policy` | Deterministic | **10/10 (100%)** | None |
| `groundedness` | Deterministic | **10/10 (100%)** | None |
| `trajectory_quality` | LLM Judge | **10/10 (100%)** | None |
| `response_quality` | LLM Judge | **10/10 (100%)** | None |

---

## 2. Assessment

* **Zero failures across all 10 scenarios and all 60 deterministic + LLM-as-a-Judge checks.**
* Grouping `_format_trajectory()` by explicit user turn in [`evals/evaluators/llm_judge.py`](../../evals/evaluators/llm_judge.py) (`06ee2b4`) completely eliminated the `trajectory_quality` turn-boundary miscount on `multi_turn_unit_followup` (#6) without touching the agent, skill, or scenario definitions.
* Wall-clock time also improved by **39.4s** vs. Run 9 (516.63s → **477.20s**, and **-22.7s** vs. Run 1 baseline).
* The only remaining terminal noise is the upstream `langsmith` `DeprecationWarning` for `asyncio.iscoroutinefunction` on Python 3.14 (non-blocking).
