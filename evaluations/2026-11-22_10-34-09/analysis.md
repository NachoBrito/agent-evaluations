# Agentic Flow Evaluation Analysis — 2026-11-22_10-34-09

## 1. Execution Summary & Metrics

| Metric | Value |
| :--- | :--- |
| **Timestamp** | `2026-11-22_10-34-09` |
| **Git HEAD** | `71b0281` (`feat(skill): propagate core weather rules to AGENTS.md and sharpen skill description`) |
| **Command** | `uv run pytest tests/test_agentic_flows.py --run-live-agent --run-judge` |
| **Scenarios** | 10 total (**7 passed**, **3 failed** — **70% pass rate**) |
| **Individual Checks** | **55/60 passed (91.7%)** (only 5 failed checks total) |
| **Total Duration** | 412.82s (6m 52s, ~41.3s avg/scenario) |
| **Warnings** | 17 `DeprecationWarning`s from `langsmith/_internal/_beta_decorator.py` (`asyncio.iscoroutinefunction`) |
| **Raw Output** | [report](./report) |
| **Progress Comparison** | [progress.md](./progress.md) |
| **Proposed Tasks** | [tasks.md](./tasks.md) |

### Scenario Breakdown

| # | Scenario (`weather_flows.yaml`) | Category | Status | Failed Evaluators |
| :---: | :--- | :--- | :---: | :--- |
| 1 | `madrid_happy_path_default_celsius` | `happy_path` | **FAIL** | `trajectory_match`, `groundedness`, `trajectory_quality` |
| 2 | `tokyo_explicit_fahrenheit` | `unit_normalization` | **PASS** | — |
| 3 | `multi_city_comparison` | `multi_city` | **PASS** | — |
| 4 | `vague_location_no_tools` | `input_validation` | **PASS** | — |
| 5 | `multi_turn_clarification_flow` | `multi_turn` | **FAIL** | `response_quality` |
| 6 | `multi_turn_unit_followup` | `multi_turn` | **PASS** | — |
| 7 | `unknown_city_error_recovery` | `error_recovery` | **FAIL** | `groundedness` |
| 8 | `service_outage_error_recovery` | `error_recovery` | **PASS** | — |
| 9 | `unsupported_unit_kelvin` | `edge_case` | **PASS** | — |
| 10 | `out_of_scope_forecast` | `scope_adherence` | **PASS** | — |

### Evaluator Pass Rates (Across 10 Scenarios)

| Evaluator | Type | Pass Rate | Failed Scenarios |
| :--- | :--- | :---: | :--- |
| `efficiency_budget` | Deterministic | **10/10 (100%)** | None |
| `tool_policy` | Deterministic | **10/10 (100%)** | None |
| `trajectory_match` | Deterministic | **9/10 (90%)** | #1 |
| `trajectory_quality` | LLM Judge | **9/10 (90%)** | #1 |
| `response_quality` | LLM Judge | **9/10 (90%)** | #5 |
| `groundedness` | Deterministic | **8/10 (80%)** | #1, #7 |

---

## 2. Root-Cause Analysis

Of the 3 failures, **only 1 is a remaining agentic flow defect (#1)**; the other **2 (#5 and #7) are false negatives caused by an overly rigid judge prompt and a brittle substring list**. Additionally, our new `Skill loaded (SKILL.md)` diagnostic confirmed `False` on all 3 failing cases, proving that the local LLM continues to act directly from `system_prompt` + `AGENTS.md` + tool docstrings rather than calling `read_file` on `SKILL.md`.

---

### A. Remaining Agentic Flow Defect (#1)

#### 1. `madrid_happy_path_default_celsius` (#1) — Still skips `get_temperature` on `"What is the weather like in Madrid?"`
* **Observed behavior:**
  * Called only `get_weather(city="Madrid")` (`Skill loaded (SKILL.md): False`).
  * Response improved: no longer offers out-of-scope multi-day forecasts, and passed `response_quality`.
  * Failed `trajectory_match`, `groundedness` (missing `14°C`), and `trajectory_quality`.
* **Why it happened:** Interestingly, `multi_turn_unit_followup` Turn 0 (`"What's the weather in Madrid?"`) **did** call both `get_weather` and `get_temperature` and passed 6/6, whereas `"What is the weather like in Madrid?"` still stopped after calling `get_weather` alone. When the local model emits a single `get_weather` call and receives `"The weather in Madrid, Spain is clear sky (humidity 45%, wind 10.5 km/h)."`, it treats that output as sufficient to answer `"What is the weather like..."` and does not make a second tool call for `get_temperature`.
* **Classification:** **Agent prompt / tool-calling behavior gap.** Making the parallel-call requirement explicit and concrete in `system_prompt` (and simplifying the exception wording so the model doesn't treat `"What is the weather like..."` as condition-only) will close this last real agent gap.

---

### B. Evaluator / Judge Prompt Bug (#5)

#### 2. `multi_turn_clarification_flow` (#5) — `response_quality` judge penalizes missing temperature on a rain-only query
* **Observed behavior:**
  * Turns: `["Is it raining here?", "Sorry, I meant London."]`
  * Agent called `[(1, 'get_weather', {'city': 'London'})]` and answered: `'The weather in London is currently experiencing moderate rain. The conditions include 85% humidity and windspeed of 22.0 km/h. Would you like additional details or assistance with something else?'`
  * Passed **5 of 6** checks (all 4 deterministic checks + `trajectory_quality`).
  * Failed **only** `[response_quality]`: *"The response fails to include temperature when weather data was retrieved. The guidelines require temperature (°C/°F) to be included if available, but the response does not mention it."*
* **Root cause:** `RESPONSE_QUALITY_TEMPLATE` in [`evals/evaluators/llm_judge.py`](../../evals/evaluators/llm_judge.py) line 32 states:
  `- Includes city name, conditions, and temperature with °C or °F when weather data was retrieved`
  Because `evaluate_response_quality` does not pass the tool-call trajectory to the judge, the judge assumes temperature must appear whenever *any* weather data is retrieved—even for a narrow rain-only question (`"Is it raining here?"`) where `AGENTS.md`, `SKILL.md`, and the scenario's own `rubric_criteria` only require `get_weather` and reporting moderate rain.
* **Classification:** **Evaluator prompt bug** in [`evals/evaluators/llm_judge.py`](../../evals/evaluators/llm_judge.py).

---

### C. Scenario Definition Too Strict (#7)

#### 3. `unknown_city_error_recovery` (#7) — Brittle `grounded_any_of` missed `"could not be found"`
* **Observed behavior:**
  * Agent called `get_weather(city="Atlantis")` and replied: `'The location "Atlantis" could not be found. Please verify the city name or check for spelling errors. If you meant a different location, feel free to clarify!'`
  * Passed **5 of 6** checks (including both LLM judges and `forbidden_substrings`).
  * Failed **only** `[groundedness]` because `grounded_any_of` listed `'not found'` and `'could not find'`, neither of which is a substring of `'could not be found'`!
* **Classification:** **Scenario definition too strict** in [`evals/datasets/weather_flows.yaml`](../../evals/datasets/weather_flows.yaml).
