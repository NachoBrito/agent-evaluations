# Agentic Flow Evaluation Analysis — 2026-11-22_10-19-46

## 1. Execution Summary & Metrics

| Metric | Value |
| :--- | :--- |
| **Timestamp** | `2026-11-22_10-19-46` |
| **Git HEAD** | `693633d` (`test(evals): refine weather flow scenarios for error recovery, kelvin, and multi-turn assertions`) |
| **Command** | `uv run pytest tests/test_agentic_flows.py --run-live-agent --run-judge` |
| **Scenarios** | 10 total (**7 passed**, **3 failed** — **70% pass rate**) |
| **Individual Checks** | 53/60 passed (**88.3%**) |
| **Total Duration** | 458.45s (7m 38s, ~45.8s avg/scenario) |
| **Warnings** | 17 `DeprecationWarning`s from `langsmith/_internal/_beta_decorator.py` (`asyncio.iscoroutinefunction`) |
| **Raw Output** | [report](./report) |
| **Progress Comparison** | [progress.md](./progress.md) |
| **Proposed Tasks** | [tasks.md](./tasks.md) |

### Scenario Breakdown

| # | Scenario (`weather_flows.yaml`) | Category | Status | Failed Evaluators |
| :---: | :--- | :--- | :---: | :--- |
| 1 | `madrid_happy_path_default_celsius` | `happy_path` | **FAIL** | `trajectory_match`, `groundedness`, `trajectory_quality`, `response_quality` |
| 2 | `tokyo_explicit_fahrenheit` | `unit_normalization` | **PASS** | — |
| 3 | `multi_city_comparison` | `multi_city` | **PASS** | — |
| 4 | `vague_location_no_tools` | `input_validation` | **PASS** | — |
| 5 | `multi_turn_clarification_flow` | `multi_turn` | **PASS** | — |
| 6 | `multi_turn_unit_followup` | `multi_turn` | **FAIL** | `tool_policy` |
| 7 | `unknown_city_error_recovery` | `error_recovery` | **PASS** | — |
| 8 | `service_outage_error_recovery` | `error_recovery` | **PASS** | — |
| 9 | `unsupported_unit_kelvin` | `edge_case` | **FAIL** | `groundedness`, `trajectory_quality` |
| 10 | `out_of_scope_forecast` | `scope_adherence` | **PASS** | — |

### Evaluator Pass Rates (Across 10 Scenarios)

| Evaluator | Type | Pass Rate | Failed Scenarios |
| :--- | :--- | :---: | :--- |
| `efficiency_budget` | Deterministic | **10/10 (100%)** | None |
| `trajectory_match` | Deterministic | **9/10 (90%)** | #1 |
| `tool_policy` | Deterministic | **9/10 (90%)** | #6 |
| `response_quality` | LLM Judge | **9/10 (90%)** | #1 |
| `trajectory_quality` | LLM Judge | **8/10 (80%)** | #1, #9 |
| `groundedness` | Deterministic | **8/10 (80%)** | #1, #9 |

---

## 2. Root-Cause Analysis

### Primary Finding: `skills/weather/SKILL.md` Is Not Being Loaded at Runtime

All 3 remaining failures share a single structural root cause: **the agent produced byte-for-byte identical outputs on #1 and #9 compared to the previous run (`2026-11-22_08-45-32`)**, despite substantial edits to [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md) in commit `4a914e7`.

* **`deepagents` middleware asymmetry:**
  * `MemoryMiddleware` (`memory=["./AGENTS.md"]`) **eagerly injects** [`AGENTS.md`](../../AGENTS.md) into the model's prompt on every turn.
  * `SkillsMiddleware` (`skills=["./skills/"]`) uses **progressive disclosure** — it exposes only the skill's `name` and `description` and relies on the model to proactively call `read_file` on `SKILL.md` before invoking domain tools.
* Because `get_weather` and `get_temperature` are already bound as direct tools and `system_prompt` in [`src/agent_evaluation/weather_agent.py`](../../src/agent_evaluation/weather_agent.py) does not require reading the skill first, the local LLM (at `temperature=0`) calls the weather tools directly and **never reads `SKILL.md`**.
* Additionally, [`evals/harness.py`](../../evals/harness.py) filters out middleware tool calls without recording whether `SKILL.md` was read, masking this blind spot during test failures.

---

### Per-Case Failure Breakdown

#### 1. `madrid_happy_path_default_celsius` (#1) — Missing `get_temperature` & out-of-scope follow-up
* **Observed behavior:** Called only `get_weather(city="Madrid")`; omitted `get_temperature`; ended with *"Would you like additional details or forecasts for a specific period?"*. Identical word-for-word to `2026-11-22_08-45-32`.
* **Root cause:** `SKILL.md` was not read. [`AGENTS.md`](../../AGENTS.md) (Core Rule 2) only says *"Call `get_weather` for current conditions and `get_temperature` for temperature readings"* without stating that general weather queries require **both** tools. The `get_weather` tool docstring in [`src/agent_evaluation/weather_agent.py`](../../src/agent_evaluation/weather_agent.py) also does not clarify that it omits temperature.
* **Classification:** **Agent instruction / prompt / tool docstring gap** (not a scenario issue).

#### 2. `multi_turn_unit_followup` (#6) — Turn 0 missing `get_temperature` (Turn 1 memory now works)
* **Observed behavior:**
  * Turn 0 (`"What's the weather in Madrid?"`): Called only `get_weather(city="Madrid")` — failed `[tool_policy] Turn 0 missed required tool(s): ['get_temperature']`.
  * Turn 1 (`"What is the temperature there in Fahrenheit?"`): Successfully resolved `"there"` to `"Madrid"` via the new `MemorySaver` checkpointer, called `get_temperature(city="Madrid", unit="fahrenheit")`, and returned `'The temperature in Madrid, Spain is 57.2°F (feels like 55.4°F).'`. Passed `trajectory_match`, `groundedness`, `trajectory_quality`, `response_quality`, and `efficiency_budget` (5/6 checks).
* **Root cause:** Same as #1 — Turn 0 (`"What's the weather in Madrid?"`) did not trigger `get_temperature` because `SKILL.md` was not read and `AGENTS.md` / tool docstrings do not require both tools for general weather queries.
* **Classification:** **Agent instruction / prompt / tool docstring gap** (exact same root cause as #1).

#### 3. `unsupported_unit_kelvin` (#9) — Manual Kelvin conversion instead of stating supported units
* **Observed behavior:** Called `get_temperature(city="Berlin", unit="celsius")` and answered with a LaTeX conversion `K = °C + 273.15 = 281.15 K` without stating that Kelvin is unsupported or mentioning Celsius/Fahrenheit. Identical word-for-word to `2026-11-22_08-45-32`.
* **Root cause:** `SKILL.md` was not read. [`AGENTS.md`](../../AGENTS.md) (Core Rule 3) only says *"Default to Celsius: Use `'celsius'` unless the user explicitly asks for `'fahrenheit'`"* and says nothing about rejecting or avoiding manual conversion for unsupported units like Kelvin.
* **Classification:** **Agent instruction / prompt / tool docstring gap** (not a scenario issue).
