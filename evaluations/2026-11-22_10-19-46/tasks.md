# Proposed Improvement Tasks — 2026-11-22_10-19-46

Synthesized from [analysis.md](./analysis.md) and [progress.md](./progress.md) (raw output: [report](./report)).

**Goal:** Eliminate the remaining 3 failures (`madrid_happy_path_default_celsius`, `multi_turn_unit_followup` Turn 0, and `unsupported_unit_kelvin`) by fixing the root cause uncovered in `progress.md` — the agent bypasses `skills/weather/SKILL.md` under progressive disclosure — without weakening any evaluation criteria.

---

## 1. Code Fixes

- [x] **Enforce skill usage and strengthen tool docstrings in [`src/agent_evaluation/weather_agent.py`](../../src/agent_evaluation/weather_agent.py):**
  - Update `system_prompt` in `create_weather_agent()` to explicitly instruct the agent to follow the `weather` skill and call **both** `get_weather` and `get_temperature` for general weather queries, and never convert to unsupported units (such as Kelvin).
  - Clarify `get_weather` docstring: note that it returns *conditions only (humidity/wind, not temperature)* and that `get_temperature` should also be called when reporting general weather.
  - Clarify `get_temperature` docstring: explicitly state that only `'celsius'` and `'fahrenheit'` are supported and that unsupported units (e.g., Kelvin) must not be manually converted.
- [x] **Add skill-load observability to [`evals/harness.py`](../../evals/harness.py) and [`tests/test_agentic_flows.py`](../../tests/test_agentic_flows.py):**
  - Record middleware tool calls (e.g., whether `skills/weather/SKILL.md` was read via `read_file`) on `FlowRunResult` (without polluting `domain_tool_calls` or `openai_trajectory`), and print `Skill loaded: True/False` in `test_agentic_flows.py` failure diagnostics so future evaluations immediately distinguish unread-skill failures from instruction-following failures.
  - Add a fast offline unit test in [`tests/test_eval_framework.py`](../../tests/test_eval_framework.py) verifying skill-load detection.

---

## 2. Skill & Agent Memory Updates

- [x] **Propagate critical behavioral rules to eagerly loaded [`AGENTS.md`](../../AGENTS.md):**
  Because `MemoryMiddleware` eagerly injects `AGENTS.md` on every turn (whereas `SkillsMiddleware` relies on optional progressive-disclosure `read_file` calls that local models skip), align `AGENTS.md` with `skills/weather/SKILL.md`:
  - **Core Rule 2:** Explicitly state that for general weather queries (e.g., *"What is the weather like in Madrid?"*), the agent must call **both** `get_weather` and `get_temperature` (defaulting to `"celsius"`). Only omit `get_temperature` for narrow condition-only questions (e.g., *"Is it raining in London?"*).
  - **Core Rule 3:** Explicitly state that **only Celsius and Fahrenheit are supported**. If the user asks for an unsupported unit (e.g., Kelvin), **do not manually convert** the temperature; clearly inform the user that only Celsius and Fahrenheit are supported and ask which they prefer (or report in Celsius).
  - **Core Rule 4:** Explicitly prohibit offering multi-day or future forecasts in closing follow-up questions.
- [x] **Keep [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md) frontmatter description clear and imperative:**
  Update the `description` field in the YAML frontmatter so `SkillsMiddleware` clearly signals that the skill must be read before answering weather requests.

---

## 3. Scenario Updates

- [x] **No scenario relaxations required:**
  All 3 remaining failures (`madrid_happy_path_default_celsius`, `multi_turn_unit_followup` Turn 0, and `unsupported_unit_kelvin`) reflect real agentic flow defects rather than brittle or ambiguous test definitions. Keep all 10 scenarios in [`evals/datasets/weather_flows.yaml`](../../evals/datasets/weather_flows.yaml) unchanged so the next evaluation run cleanly measures whether the code and `AGENTS.md` fixes achieve **10/10 (100%)**.
