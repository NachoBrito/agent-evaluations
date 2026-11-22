# Agentic Flow Evaluation Analysis — 2026-11-22_11-06-47

## 1. Execution Summary & Metrics

| Metric | Value |
| :--- | :--- |
| **Timestamp** | `2026-11-22_11-06-47` |
| **Git HEAD** | `2bb48bf` (`feat(skill): forbid temperature hallucination, kelvin formulas, and tool-name leaks`) |
| **Command** | `uv run pytest tests/test_agentic_flows.py --run-live-agent --run-judge` |
| **Scenarios** | 10 total (**9 passed**, **1 failed** — **90% pass rate**) |
| **Individual Checks** | **57/60 passed (95.0%)** (all 3 failed checks on a single scenario) |
| **Total Duration** | 481.70s (8m 01s, ~48.2s avg/scenario) |
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
| 6 | `multi_turn_unit_followup` | `multi_turn` | **FAIL** | `trajectory_match`, `tool_policy`, `trajectory_quality` |
| 7 | `unknown_city_error_recovery` | `error_recovery` | **PASS** | — |
| 8 | `service_outage_error_recovery` | `error_recovery` | **PASS** | — |
| 9 | `unsupported_unit_kelvin` | `edge_case` | **PASS** | — |
| 10 | `out_of_scope_forecast` | `scope_adherence` | **PASS** | — |

### Evaluator Pass Rates (Across 10 Scenarios)

| Evaluator | Type | Pass Rate | Failed Scenarios |
| :--- | :--- | :---: | :--- |
| `efficiency_budget` | Deterministic | **10/10 (100%)** | None |
| `groundedness` | Deterministic | **10/10 (100%)** | None |
| `response_quality` | LLM Judge | **10/10 (100%)** | None |
| `trajectory_match` | Deterministic | **9/10 (90%)** | #6 |
| `tool_policy` | Deterministic | **9/10 (90%)** | #6 |
| `trajectory_quality` | LLM Judge | **9/10 (90%)** | #6 |

---

## 2. Root-Cause Analysis

**9 of 10 scenarios passed (all 6/6)**, including both previously failing scenarios (`multi_turn_clarification_flow` #5 and `unsupported_unit_kelvin` #9). Only **1 scenario failed (`multi_turn_unit_followup` #6)**, revealing a genuine arithmetic/tool-use issue:

### `multi_turn_unit_followup` (#6) — Manual °C → °F Conversion Instead of Calling `get_temperature`

* **Observed behavior:**
  * **Turn 0** (`"What's the weather in Madrid?"`): Correctly called both `(0, 'get_weather', {'city': 'Madrid'})` and `(0, 'get_temperature', {'city': 'Madrid', 'unit': 'celsius'})`, receiving `14.0°C (feels like 13.0°C)`.
  * **Turn 1** (`"What is the temperature there in Fahrenheit?"`): Did **not** call `get_temperature(city='Madrid', unit='fahrenheit')` (`called: []`). Instead, the agent manually converted `14.0°C` → `57.2°F` and **miscalculated** `feels like 13.0°C` as **`56.0°F`** (exact value in [`evals/fakes.py`](../../evals/fakes.py) is **`55.4°F`**).
  * `Final response`: `'The temperature in Madrid, Spain is **57.2°F** (feels like 56.0°F). Let me know if you need further details!'`
  * Failed checks: `trajectory_match`, `tool_policy` (`Turn 1 missed required tool(s): ['get_temperature']`), and `trajectory_quality`.
* **Root cause:**
  * Previously, our no-conversion rule in [`src/agent_evaluation/weather_agent.py`](../../src/agent_evaluation/weather_agent.py), [`AGENTS.md`](../../AGENTS.md), and [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md) only prohibited manual conversion for *unsupported units like Kelvin*.
  * Because Turn 0 already retrieved `14.0°C`, the model assumed it could shortcut Turn 1 by doing mental math from Celsius to Fahrenheit—introducing an actual numeric error (`56.0°F` instead of `55.4°F`).
* **Classification:** **Genuine agentic flow defect** (not a scenario issue). Generalizing the no-manual-conversion rule to cover **all unit conversions (including Celsius ↔ Fahrenheit)** forces the agent to call `get_temperature(city=..., unit='fahrenheit')` and guarantees exact tool-backed values.
