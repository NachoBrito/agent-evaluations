# Agentic Flow Evaluation Analysis — 2026-11-22_08-45-32

## 1. Execution Summary & Metrics

| Metric | Value |
| :--- | :--- |
| **Timestamp** | `2026-11-22_08-45-32` |
| **Command** | `uv run pytest tests/test_agentic_flows.py --run-live-agent --run-judge` |
| **Scenarios** | 10 total (**5 passed**, **5 failed** — **50% pass rate**) |
| **Total Duration** | 499.89s (8m 19s, ~50s avg/scenario) |
| **Warnings** | 17 `DeprecationWarning`s from `langsmith/_internal/_beta_decorator.py` (`asyncio.iscoroutinefunction`) |
| **Raw Output** | [report](./report) |
| **Proposed Tasks** | [tasks.md](./tasks.md) |

### Scenario Breakdown

| # | Scenario (`weather_flows.yaml`) | Category | Status | Failed Evaluators |
| :---: | :--- | :--- | :---: | :--- |
| 1 | `madrid_happy_path_default_celsius` | `happy_path` | **FAIL** | `trajectory_match`, `groundedness`, `trajectory_quality` |
| 2 | `tokyo_explicit_fahrenheit` | `unit_normalization` | **PASS** | — |
| 3 | `multi_city_comparison` | `multi_city` | **PASS** | — |
| 4 | `vague_location_no_tools` | `input_validation` | **PASS** | — |
| 5 | `multi_turn_clarification_flow` | `multi_turn` | **FAIL** | `tool_policy` |
| 6 | `multi_turn_unit_followup` | `multi_turn` | **FAIL** | `trajectory_match`, `tool_policy`, `groundedness`, `trajectory_quality` |
| 7 | `unknown_city_error_recovery` | `error_recovery` | **FAIL** | `groundedness` |
| 8 | `service_outage_error_recovery` | `error_recovery` | **PASS** | — |
| 9 | `unsupported_unit_kelvin` | `edge_case` | **FAIL** | `groundedness`, `trajectory_quality` |
| 10 | `out_of_scope_forecast` | `scope_adherence` | **PASS** | — |

### Evaluator Pass Rates (Across 10 Scenarios)

| Evaluator | Type | Pass Rate | Failed Scenarios |
| :--- | :--- | :---: | :--- |
| `efficiency_budget` | Deterministic | **10/10 (100%)** | None |
| `response_quality` | LLM Judge | **10/10 (100%)**\* | None (*passed even on an empty response in #6*) |
| `trajectory_match` | Deterministic | **8/10 (80%)** | #1, #6 |
| `tool_policy` | Deterministic | **8/10 (80%)** | #5, #6 |
| `trajectory_quality` | LLM Judge | **7/10 (70%)** | #1, #6, #9 |
| `groundedness` | Deterministic | **6/10 (60%)** | #1, #6, #7, #9 |

---

## 2. Root-Cause Analysis

The 5 failures fall into three distinct categories: **Agent/Harness bugs**, **Skill/Instruction gaps**, and **Scenario/Evaluator strictness or ambiguity**.

### A. Agent & Harness Bugs (Blocks All Multi-Turn Flows: #5 & #6)

* **Affected scenarios:** `multi_turn_clarification_flow` (#5) and `multi_turn_unit_followup` (#6).
* **Observed evidence:**
  * **#5 (`multi_turn_clarification_flow`):** Failed only `[tool_policy] Turn 1 missed required tool(s): ['get_weather'] (called: [])`. However, the final response reported the exact London fixture data (`moderate rain`, `Humidity: 85%`, `Wind speed: 22.0 km/h`) and `trajectory_match` passed.
  * **#6 (`multi_turn_unit_followup`):** Failed `trajectory_match`, `tool_policy`, `groundedness` (`Final agent response is empty`), and `trajectory_quality`. `Domain tool calls` recorded only `[(0, 'get_weather', {'city': 'Madrid'})]` and `Final response` was `''`. The judge noted that on Turn 2 the agent asked for clarification on `"there"` instead of resolving it to `"Madrid"`.
* **Root cause:** `create_weather_agent()` in [`src/agent_evaluation/weather_agent.py`](../../src/agent_evaluation/weather_agent.py) calls `create_deep_agent(...)` **without a `checkpointer`** (`agent.checkpointer` is `None`). Consequently:
  1. LangGraph does not persist conversation history for `config={"configurable": {"thread_id": ...}}` across `agent.ainvoke(...)` calls in [`evals/harness.py`](../../evals/harness.py), so Turn 2 has no memory of Turn 1 (`"Madrid"`).
  2. `evals/harness.py` assumes `result["messages"]` accumulates across turns and slices `new_messages = messages[prev_count:]`. Because `result["messages"]` resets on Turn 2, slicing by `prev_count` drops Turn 2's tool calls (causing `domain_tool_calls: []` in #5) or slices to an empty list `[]` (causing `final_response: ''` in #6).
* **Secondary evaluator finding:** `response_quality` (LLM Judge) passed #6 despite `final_response` being `''`. [`evals/evaluators/llm_judge.py`](../../evals/evaluators/llm_judge.py) does not short-circuit on empty responses, and the local judge model was too lenient on that degenerate input.

---

### B. Skill Changes Required (#1, #6 Turn 1, and #9)

#### 1. `madrid_happy_path_default_celsius` (#1) — `get_temperature` treated as optional
* **Observed behavior:** For `"What is the weather like in Madrid?"`, the agent called only `get_weather(city="Madrid")` and omitted `get_temperature`. It also closed with *"Would you like additional details or forecasts for a specific period?"*—offering out-of-scope forecasts.
* **Root cause:** [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md) (Section 2 & Quality Checklist) frames `get_temperature` as conditional (*"when the user asks for temperature or a full weather report"* / *"when relevant"*). Because the prompt did not contain the word "temperature", the agent skipped `get_temperature`. Scenarios #2 and #3 explicitly asked for "temperature" and passed.
* **Classification:** **Skill change required.** Both [`AGENTS.md`](../../AGENTS.md) and the example in [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md) expect standard weather queries to return both conditions and temperature. This same gap affects Turn 1 of #6 (`"What's the weather in Madrid?"`).

#### 2. `unsupported_unit_kelvin` (#9) — Silent conversion to Kelvin instead of stating supported units
* **Observed behavior:** The agent safely called `get_temperature(city="Berlin", unit="celsius")`, then responded with `8.0°C` and a LaTeX conversion to `281.15 K` without stating that Kelvin is unsupported or naming Celsius/Fahrenheit.
* **Root cause:** [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md) (Section 1) says *"let them know you support Celsius and Fahrenheit and ask which they prefer (or report in Celsius)"*, but does not prohibit manually converting temperatures to unsupported units.
* **Classification:** **Skill change required** if refusing manual Kelvin conversion is the intended policy.

---

### C. Scenario Definition Issues: Too Strict or Ambiguous (#7, #9, #6)

#### 1. `unknown_city_error_recovery` (#7) — `grounded_any_of` too strict + Skill/Scenario contradiction
* **Observed behavior:** The agent called `get_weather(city="Atlantis")`, avoided hallucinating weather data, and replied: *"The location 'Atlantis' does not match any valid city or region in the weather database... non-existent place."* Both LLM judges passed it; it failed **only** `groundedness` because its phrasing did not contain an exact match from `['not found', "couldn't find", 'could not find', 'unable', 'sorry', "don't have", 'no location']`.
* **Classification:** **Scenario is too strict.** Valid natural paraphrases (`"does not match"`, `"non-existent"`) are rejected by a brittle keyword list.
* **Skill/Scenario contradiction:** [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md) (Section 1, item 2) instructs *"If the city is ... not a recognizable place, **do NOT call any tool**"*, while [`evals/datasets/weather_flows.yaml`](../../evals/datasets/weather_flows.yaml) requires calling `get_weather(city="Atlantis")`. A stricter model obeying `SKILL.md` literally would fail `trajectory_match`.

#### 2. `unsupported_unit_kelvin` (#9) — Redundant / narrow `grounded_any_of`
* [`evals/datasets/weather_flows.yaml`](../../evals/datasets/weather_flows.yaml) lists `["Celsius", "Fahrenheit", "celsius", "fahrenheit"]`. Lowercase duplicates are redundant because `evaluate_groundedness()` is already case-insensitive, and `"°C"` is not accepted if the agent reports `8°C`.

#### 3. `multi_turn_unit_followup` (#6) — Mismatch between `turn_assertions` and `rubric_criteria`
* `turn_assertions` for `turn_index: 0` only requires `get_weather`, while `rubric_criteria` states *"On turn 1, the agent checks Madrid in Celsius"*, which implies `get_temperature` as well.
