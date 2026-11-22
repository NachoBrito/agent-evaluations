# Agentic Flow Evaluation Analysis — 2026-11-22_14-27-51

## 1. Execution Summary & Metrics

| Metric | Value |
| :--- | :--- |
| **Timestamp** | `2026-11-22_14-27-51` |
| **Git HEAD** | `90e84ee` (`fix: refine system_prompt to compact 4-invariant sweet spot`) |
| **Command** | `uv run pytest tests/test_agentic_flows.py --run-live-agent --run-judge` |
| **Scenarios** | 10 total (**9 passed**, **1 failed** — **90% pass rate**) |
| **Individual Checks** | **59/60 passed (98.3%) — new all-time high!** |
| **Deterministic Checks** | **40/40 passed (100%)** |
| **Total Duration** | 516.63s (8m 36s, ~51.7s avg/scenario) |
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
| 6 | `multi_turn_unit_followup` | `multi_turn` | **FAIL** | `trajectory_quality` *(judge turn-boundary miscount)* |
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
| `response_quality` | LLM Judge | **10/10 (100%)** | None |
| `trajectory_quality` | LLM Judge | **9/10 (90%)** | #6 *(false negative)* |

---

## 2. Root-Cause Analysis

**The agent itself performed 100% correctly across all 10 scenarios** (40/40 deterministic checks + 10/10 `response_quality` = **59/60 total checks**).

### Sole Failed Check: `multi_turn_unit_followup` (#6) — `trajectory_quality` Judge Turn-Boundary Miscount

* **Actual agent execution (100% correct):**
  * **Turn 0 (User Turn 1 — `"What's the weather in Madrid?"`):** Called BOTH `(0, 'get_weather', {'city': 'Madrid'})` AND `(0, 'get_temperature', {'city': 'Madrid', 'unit': 'celsius'})`.
  * **Turn 1 (User Turn 2 — `"What is the temperature there in Fahrenheit?"`):** Resolved `"there"` → `"Madrid"`, called `(1, 'get_temperature', {'city': 'Madrid', 'unit': 'fahrenheit'})`, and replied `'The temperature in Madrid, Spain is 57.2°F (feels like 55.4°F).'`.
  * Passed all 4 deterministic evaluators (`trajectory_match`, `tool_policy`, `efficiency_budget`, `groundedness`) AND `response_quality`.
* **Why `trajectory_quality` failed:**
  * The judge wrote: *"the agent's first tool call (turn 1) is for `get_weather`..., and the first temperature check (Celsius) occurs on turn 2."*
  * **Root cause in [`evals/evaluators/llm_judge.py`](../../evals/evaluators/llm_judge.py):** `_format_trajectory(run)` serializes `run.openai_trajectory` as a flat JSON array of messages **without turn labels**. When the agent makes two sequential tool calls inside User Turn 1 (`assistant` → `tool` → `assistant` → `tool` → `assistant`), the local judge mistakes the second `assistant` tool-call message for "Turn 2"!
* **Classification:** **Evaluator formatting bug** in [`evals/evaluators/llm_judge.py`](../../evals/evaluators/llm_judge.py) — zero agent, skill, or scenario defects remain.
