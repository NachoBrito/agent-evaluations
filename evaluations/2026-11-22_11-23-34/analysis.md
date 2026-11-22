# Agentic Flow Evaluation Analysis — 2026-11-22_11-23-34

## 1. Execution Summary & Metrics

| Metric | Value |
| :--- | :--- |
| **Timestamp** | `2026-11-22_11-23-34` |
| **Git HEAD** | `0b26153` (`feat(skill): require fresh get_temperature call on unit follow-ups`) |
| **Command** | `uv run pytest tests/test_agentic_flows.py --run-live-agent --run-judge` |
| **Scenarios** | 10 total (**9 passed**, **1 failed** — **90% pass rate**) |
| **Individual Checks** | **58/60 passed (96.7%)** (all 4 deterministic evaluators at **100%**) |
| **Total Duration** | 592.09s (9m 52s, ~59.2s avg/scenario) |
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
| 9 | `unsupported_unit_kelvin` | `edge_case` | **FAIL** | `trajectory_quality`, `response_quality` |
| 10 | `out_of_scope_forecast` | `scope_adherence` | **PASS** | — |

### Evaluator Pass Rates (Across 10 Scenarios)

| Evaluator | Type | Pass Rate | Failed Scenarios |
| :--- | :--- | :---: | :--- |
| `efficiency_budget` | Deterministic | **10/10 (100%)** | None |
| `trajectory_match` | Deterministic | **10/10 (100%)** | None |
| `tool_policy` | Deterministic | **10/10 (100%)** | None |
| `groundedness` | Deterministic | **10/10 (100%)** | None |
| `trajectory_quality` | LLM Judge | **9/10 (90%)** | #9 |
| `response_quality` | LLM Judge | **9/10 (90%)** | #9 |

---

## 2. Root-Cause Analysis

**Milestone achieved:** All **4 deterministic evaluators hit 10/10 (100%)** simultaneously for the first time, and `multi_turn_unit_followup` (#6) flipped back to **PASS (6/6)**. Only **1 scenario failed (`unsupported_unit_kelvin` #9)** on the two LLM judges:

### `unsupported_unit_kelvin` (#9) — Incomplete "Let me check..." Reply Without Calling `get_temperature` or Asking Preference

* **Observed behavior:**
  * `Domain tool calls`: `[(0, 'get_weather', {'city': 'Berlin'})]` (did not call `get_temperature`).
  * `Final response`: `'The weather service does not support temperature in Kelvin. I can provide the temperature in Celsius or Fahrenheit. Let me check the current weather and temperature for Berlin.'`
  * Passed all 4 deterministic checks, but failed `trajectory_quality` and `response_quality` because the agent promised *"Let me check the current weather and temperature for Berlin"* and stopped—neither reporting `8°C` nor asking the user which unit they prefer.
* **Root cause:**
  * Our unsupported-unit instruction in [`src/agent_evaluation/weather_agent.py`](../../src/agent_evaluation/weather_agent.py), [`AGENTS.md`](../../AGENTS.md), and [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md) gave the model an **open-ended choice** (*"either ask which they prefer or provide the temperature in Celsius"*). Under that ambiguity, the local model called `get_weather` (instead of `get_temperature`), hesitated, and emitted a dangling *"Let me check..."* sentence.
  * Additionally, `system_prompt` has grown verbose across iterations, increasing prompt pressure on the small local model (and contributing to longer latency).
* **Classification:** **Agent instruction ambiguity.** Replacing the open-ended *"either ask ... or provide Celsius"* branch with a **single, deterministic action** — *"do NOT call any tool; state that you only support Celsius and Fahrenheit and ask which unit they prefer (e.g., 'Would you like the temperature in Celsius or Fahrenheit?')"* — eliminates both the dangling *"Let me check..."* reply AND any risk of Kelvin arithmetic (`281.15 K`), while staying 100% compliant with the scenario rubric.
