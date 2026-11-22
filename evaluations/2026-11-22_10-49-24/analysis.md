# Agentic Flow Evaluation Analysis — 2026-11-22_10-49-24

## 1. Execution Summary & Metrics

| Metric | Value |
| :--- | :--- |
| **Timestamp** | `2026-11-22_10-49-24` |
| **Git HEAD** | `d4731c9` (`test(evals): accept 'could not be found' phrasing in unknown_city_error_recovery`) |
| **Command** | `uv run pytest tests/test_agentic_flows.py --run-live-agent --run-judge` |
| **Scenarios** | 10 total (**8 passed**, **2 failed** — **80% pass rate**) |
| **Individual Checks** | **58/60 passed (96.7%)** (only 2 failed checks total) |
| **Total Duration** | 419.59s (6m 59s, ~42.0s avg/scenario) |
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
| 5 | `multi_turn_clarification_flow` | `multi_turn` | **FAIL** | `response_quality` |
| 6 | `multi_turn_unit_followup` | `multi_turn` | **PASS** | — |
| 7 | `unknown_city_error_recovery` | `error_recovery` | **PASS** | — |
| 8 | `service_outage_error_recovery` | `error_recovery` | **PASS** | — |
| 9 | `unsupported_unit_kelvin` | `edge_case` | **FAIL** | `groundedness` |
| 10 | `out_of_scope_forecast` | `scope_adherence` | **PASS** | — |

### Evaluator Pass Rates (Across 10 Scenarios)

| Evaluator | Type | Pass Rate | Failed Scenarios |
| :--- | :--- | :---: | :--- |
| `efficiency_budget` | Deterministic | **10/10 (100%)** | None |
| `tool_policy` | Deterministic | **10/10 (100%)** | None |
| `trajectory_match` | Deterministic | **10/10 (100%)** | None |
| `trajectory_quality` | LLM Judge | **10/10 (100%)** | None |
| `groundedness` | Deterministic | **9/10 (90%)** | #9 |
| `response_quality` | LLM Judge | **9/10 (90%)** | #5 |

---

## 2. Root-Cause Analysis

4 of the 6 evaluators (`efficiency_budget`, `tool_policy`, `trajectory_match`, and `trajectory_quality`) hit **10/10 (100%)**, and only **2 individual checks failed out of 60**. However, inspecting the raw responses reveals **two genuine agentic flow issues** plus **one multi-turn evaluator blind spot**:

---

### A. `multi_turn_clarification_flow` (#5) — Hallucinated Temperature + Multi-Turn Judge Blind Spot

* **Observed behavior:**
  * `Domain tool calls`: `[(1, 'get_weather', {'city': 'London'})]` (did **not** call `get_temperature`).
  * `Final response`: `'The weather in London, United Kingdom is **moderate rain** with humidity at 85% and wind speed of 22.0 km/h. The current temperature is **12°C**.'`
  * Failed check: `[response_quality]`.
* **Root cause 1 — Genuine agent hallucination (high severity):**
  * The agent fabricated `12°C` without calling `get_temperature` (London's fixture temperature in [`evals/fakes.py`](../../evals/fakes.py) is `11.0°C`).
  * Our stronger `system_prompt` in `f332c3f` (*"report both conditions and temperature in your response"*) pressured the model to include a temperature even when it only called `get_weather` on a rain-only question (`"Is it raining here?"`).
  * Neither `groundedness` nor `trajectory_quality` caught this hallucination because `multi_turn_clarification_flow` does not forbid ungrounded temperature tokens when `get_temperature` is not called.
* **Root cause 2 — Evaluator blind spot in `evaluate_response_quality` ([`evals/evaluators/llm_judge.py`](../../evals/evaluators/llm_judge.py)):**
  * `response_quality` actually failed #5 for the *wrong* reason: it claimed *"On Turn 1, the agent must not call any weather tool and must ask for a city. The response incorrectly called the weather tool immediately..."*
  * That happened because `evaluate_response_quality()` sends the multi-turn `rubric_criteria` and all `user_inputs`, but **only sends `run.final_response` (Turn 2's reply)**—hiding Turn 1's assistant clarification from the judge!

---

### B. `unsupported_unit_kelvin` (#9) — Still Computes Kelvin Conversion & Leaks Internal Tool Name

* **Observed behavior:**
  * `Domain tool calls`: `[(0, 'get_temperature', {'city': 'Berlin', 'unit': 'celsius'})]`.
  * `Final response`: `"The temperature in Berlin is **8.0°C** (celsius). \n\nSince the \`get_temperature\` function only supports Celsius and Fahrenheit, I cannot directly retrieve the temperature in Kelvin. However, I can calculate it for you using the formula:  \n**Kelvin = Celsius + 273.15**  \n\nSo, **8.0°C = 281.15 K**.  \n\nLet me know if you'd like further clarification!"`
  * Failed check: `[groundedness] Found forbidden substring '281.15' in final response.` (Passed all 5 other checks including both LLM judges.)
* **Root cause:**
  * The agent acknowledged that only Celsius and Fahrenheit are supported and reported `8.0°C`, but still disobeyed `"never manually convert temperatures to unsupported units like Kelvin"` by adding a `"However, I can calculate it for you..."` section with `281.15 K`.
  * It also leaked an internal tool name (`` `get_temperature` function ``) in the user-facing response.
* **Classification:** **Agent instruction/prompt precision gap** (needs explicit prohibition against outputting any Kelvin value, conversion formula, or internal tool names).
