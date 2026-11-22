# Agentic Flow Evaluation Analysis — 2026-11-22_11-40-01

## 1. Execution Summary & Metrics

| Metric | Value |
| :--- | :--- |
| **Timestamp** | `2026-11-22_11-40-01` |
| **Git HEAD** | `4c3818c` (`feat(skill): remove ambiguous unsupported-unit branch in AGENTS.md and SKILL.md`) |
| **Command** | `uv run pytest tests/test_agentic_flows.py --run-live-agent --run-judge` |
| **Scenarios** | 10 total (**8 passed**, **2 failed** — **80% pass rate**) |
| **Individual Checks** | **56/60 passed (93.3%)** (4 failed checks: 1 on #7, 3 on #8) |
| **Total Duration** | 540.53s (9m 00s, ~54.1s avg/scenario) |
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
| 7 | `unknown_city_error_recovery` | `error_recovery` | **FAIL** | `groundedness` |
| 8 | `service_outage_error_recovery` | `error_recovery` | **FAIL** | `groundedness`, `trajectory_quality`, `response_quality` |
| 9 | `unsupported_unit_kelvin` | `edge_case` | **PASS** | — |
| 10 | `out_of_scope_forecast` | `scope_adherence` | **PASS** | — |

### Evaluator Pass Rates (Across 10 Scenarios)

| Evaluator | Type | Pass Rate | Failed Scenarios |
| :--- | :--- | :---: | :--- |
| `efficiency_budget` | Deterministic | **10/10 (100%)** | None |
| `trajectory_match` | Deterministic | **10/10 (100%)** | None |
| `tool_policy` | Deterministic | **10/10 (100%)** | None |
| `trajectory_quality` | LLM Judge | **9/10 (90%)** | #8 |
| `response_quality` | LLM Judge | **9/10 (90%)** | #8 |
| `groundedness` | Deterministic | **8/10 (80%)** | #7, #8 |

---

## 2. Root-Cause Analysis

`unsupported_unit_kelvin` (#9) is now **PASS (6/6)**, and all trajectory/tool evaluators (`efficiency_budget`, `trajectory_match`, `tool_policy`) remain at **10/10 (100%)**. The 2 failures on error-recovery scenarios expose two distinct issues:

---

### A. `unknown_city_error_recovery` (#7) — Brittle Synonym-List Anti-Pattern in `grounded_any_of`

* **Observed behavior:**
  * `Domain tool calls`: `[(0, 'get_weather', {'city': 'Atlantis'})]`.
  * `Final response`: `'The location "Atlantis" is not recognized as a valid city for weather information. Please check the city name or try a different location. If you meant a specific real-world city, let me know!'`
  * Passed **5 of 6** checks (including both LLM judges and `forbidden_substrings`).
  * Failed **only** `[groundedness]` because `"not recognized"` was not in the 17-item keyword list (even though `"not a valid"` was, and the agent wrote `"not recognized as a valid"`).
* **Root cause:** Testing open-ended natural-language error phrasing with a deterministic substring list has now caused **3 false negatives across 7 runs** (`"does not match"`, `"could not be found"`, `"is not recognized as a valid city"`).
* **Classification:** **Scenario design anti-pattern.** Deterministic `grounded_any_of` should assert objective factual tokens (`["Atlantis"]`) alongside `forbidden_substrings` (`["°C", "°F"]`), while semantic error communication is already graded by `trajectory_quality` and `response_quality`.

---

### B. `service_outage_error_recovery` (#8) — Empty Final Response After Tool Error

* **Observed behavior:**
  * `Domain tool calls`: `[(0, 'get_weather', {'city': 'Paris'})]`.
  * `Final response`: `''` (empty).
  * Failed `groundedness`, `trajectory_quality`, and `response_quality` (caught cleanly by our empty-response guard from `0a4886c`).
* **Root cause:**
  * Across iterations, `system_prompt` in [`src/agent_evaluation/weather_agent.py`](../../src/agent_evaluation/weather_agent.py) grew to ~150 words of stacked negative constraints (`NEVER ... do NOT ...`), duplicating rules already injected eagerly from [`AGENTS.md`](../../AGENTS.md) while omitting an explicit instruction on how to respond to tool errors.
  * Under prompt bloat + a `RuntimeError` tool output, the local LLM returned an empty assistant message.
* **Classification:** **Code / prompt bloat issue** in [`src/agent_evaluation/weather_agent.py`](../../src/agent_evaluation/weather_agent.py). Slimming `system_prompt` (removing verbatim duplication of `AGENTS.md`) and adding a concise 1-line tool-error response rule will restore reliability and reduce latency.
