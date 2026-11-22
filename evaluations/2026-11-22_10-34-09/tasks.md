# Proposed Improvement Tasks — 2026-11-22_10-34-09

Synthesized from [analysis.md](./analysis.md) and [progress.md](./progress.md) (raw output: [report](./report)).

**Goal:** Reach **10/10 (100%)** by fixing the single remaining agentic flow defect (#1) and removing the two evaluator/scenario false negatives (#5 and #7) without weakening any real requirement.

---

## 1. Code Fixes

- [x] **Make parallel `get_weather` + `get_temperature` calling explicit in [`src/agent_evaluation/weather_agent.py`](../../src/agent_evaluation/weather_agent.py):**
  - Strengthen `system_prompt` in `create_weather_agent()` to explicitly instruct the model: when answering any general weather question (such as *"What is the weather like in <city>?"* or *"What's the weather in <city>?"*), call **both `get_weather` and `get_temperature` together** before writing the final answer, and never finish a general weather response without a temperature reading.
  - Clarify in `get_weather`'s return string or docstring that temperature is not included and must be fetched via `get_temperature` when giving a general weather summary.
- [x] **Fix the overly rigid temperature rule in `RESPONSE_QUALITY_TEMPLATE` in [`evals/evaluators/llm_judge.py`](../../evals/evaluators/llm_judge.py):**
  - Update line 32 from:
    `- Includes city name, conditions, and temperature with °C or °F when weather data was retrieved`
    to:
    `- Includes city name, conditions, and temperature with °C or °F when temperature was retrieved or required by the Task Rubric (do not penalize omitting temperature on narrow condition-only questions like "Is it raining?")`
  - This eliminates the false negative on `multi_turn_clarification_flow` (#5) while keeping temperature mandatory for all general weather and temperature queries.

---

## 2. Skill & Agent Memory Updates

- [x] **Tighten Core Rule 2 in [`AGENTS.md`](../../AGENTS.md) and Section 2 in [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md):**
  - Emphasize calling `get_weather` and `get_temperature` **together in parallel** for general weather questions (`"What is the weather like in <city>?"`), and explicitly note that `get_weather` does **not** return temperature.

---

## 3. Scenario Updates

- [x] **Add `"could not be found"` / `"not be found"` to `grounded_any_of` for `unknown_city_error_recovery` in [`evals/datasets/weather_flows.yaml`](../../evals/datasets/weather_flows.yaml):**
  - The agent's actual reply (`'The location "Atlantis" could not be found.'`) is completely accurate and passed both LLM judges, failing only because `'could not be found'` was absent from the substring list alongside `'not found'` and `'could not find'`.
