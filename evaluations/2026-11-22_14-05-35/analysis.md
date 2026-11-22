# Agentic Flow Evaluation Analysis — 2026-11-22_14-05-35

## 1. Execution Summary & Metrics

| Metric | Value |
| :--- | :--- |
| **Timestamp** | `2026-11-22_14-05-35` |
| **Git HEAD** | `b1d7d79` (`test(evals): remove brittle synonym list from unknown_city_error_recovery`) |
| **Command** | `uv run pytest tests/test_agentic_flows.py --run-live-agent --run-judge` |
| **Scenarios** | 10 total (**7 passed**, **3 failed** — **70% pass rate**) |
| **Individual Checks** | **51/60 passed (85.0%)** (9 failed checks: 4 on #1, 4 on #3, 1 on #6) |
| **Total Duration** | 492.75s (8m 12s, ~49.3s avg/scenario) |
| **Warnings** | 17 `DeprecationWarning`s from `langsmith/_internal/_beta_decorator.py` (`asyncio.iscoroutinefunction`) |
| **Raw Output** | [report](./report) |
| **Progress Comparison** | [progress.md](./progress.md) |
| **Proposed Tasks** | [tasks.md](./tasks.md) |

### Scenario Breakdown

| # | Scenario (`weather_flows.yaml`) | Category | Status | Failed Evaluators |
| :---: | :--- | :--- | :---: | :--- |
| 1 | `madrid_happy_path_default_celsius` | `happy_path` | **FAIL** | `trajectory_match`, `groundedness`, `trajectory_quality`, `response_quality` |
| 2 | `tokyo_explicit_fahrenheit` | `unit_normalization` | **PASS** | — |
| 3 | `multi_city_comparison` | `multi_city` | **FAIL** | `trajectory_match`, `groundedness`, `trajectory_quality`, `response_quality` |
| 4 | `vague_location_no_tools` | `input_validation` | **PASS** | — |
| 5 | `multi_turn_clarification_flow` | `multi_turn` | **PASS** | — |
| 6 | `multi_turn_unit_followup` | `multi_turn` | **FAIL** | `tool_policy` |
| 7 | `unknown_city_error_recovery` | `error_recovery` | **PASS** | — |
| 8 | `service_outage_error_recovery` | `error_recovery` | **PASS** | — |
| 9 | `unsupported_unit_kelvin` | `edge_case` | **PASS** | — |
| 10 | `out_of_scope_forecast` | `scope_adherence` | **PASS** | — |

### Evaluator Pass Rates (Across 10 Scenarios)

| Evaluator | Type | Pass Rate | Failed Scenarios |
| :--- | :--- | :---: | :--- |
| `efficiency_budget` | Deterministic | **10/10 (100%)** | None |
| `tool_policy` | Deterministic | **9/10 (90%)** | #6 |
| `trajectory_match` | Deterministic | **8/10 (80%)** | #1, #3 |
| `groundedness` | Deterministic | **8/10 (80%)** | #1, #3 |
| `trajectory_quality` | LLM Judge | **8/10 (80%)** | #1, #3 |
| `response_quality` | LLM Judge | **8/10 (80%)** | #1, #3 |

---

## 2. Root-Cause Analysis

Both targets from Run 7 — **`unknown_city_error_recovery` (#7)** and **`service_outage_error_recovery` (#8)** — flipped to **PASS (6/6)**, and `unsupported_unit_kelvin` (#9) and `multi_turn_clarification_flow` (#5) stayed **PASS (6/6)**.

However, **all 3 failures (#1, #3, #6) share a single root cause: over-trimming `system_prompt` in commit `a000186`**:

* **#1 (`madrid_happy_path_default_celsius`):** Called only `get_weather(Madrid)` — skipped `get_temperature(Madrid)`.
* **#3 (`multi_city_comparison`):** Called `get_weather(Madrid)`, `get_weather(Berlin)`, `get_temperature(Madrid)` — skipped `get_temperature(Berlin)` and fabricated `12.5°C` for Berlin (actual fixture: `8.0°C`).
* **#6 (`multi_turn_unit_followup`):** Turn 0 called only `get_weather(Madrid)` — skipped `get_temperature(Madrid)` (Turn 1 called `get_temperature(Madrid, fahrenheit)` and passed 5/6 checks).

### Why This Happened
* In Runs 4–7 (when #1, #3, and #6 Turn 0 all passed **4 consecutive runs**), `system_prompt` in [`src/agent_evaluation/weather_agent.py`](../../src/agent_evaluation/weather_agent.py) explicitly stated:
  1. `IMPORTANT: get_weather only returns sky conditions, humidity, and wind — it does NOT return temperature.`
  2. Concrete examples (`'What is the weather like in <city>?'`, `'What's the weather in <city>?'`) requiring BOTH `get_weather` and `get_temperature`.
  3. Explicit anti-hallucination: `NEVER mention, guess, or invent a temperature unless you called get_temperature and received it from the tool.`
* When commit `a000186` removed those lines from `system_prompt` (relying on [`AGENTS.md`](../../AGENTS.md) alone), the local LLM paid significantly less attention to the `MemoryMiddleware`-injected `AGENTS.md` block and immediately reverted to skipping `get_temperature` (and hallucinating `12.5°C` for Berlin).
* Conversely, trimming the verbose Kelvin rules out of `system_prompt` caused **zero** regression on #9, and adding the 1-line tool-error rule fixed #8 immediately.

**Conclusion:** `system_prompt` needs a **compact (~90-word) high-attention set of the 4 proven invariants** (explicitly noting `get_weather` omits temperature + call both for **every** city + never invent a temperature without calling `get_temperature` + no manual unit conversion + always reply on tool error), without restoring the bloated 150-word repetition from Run 7.
