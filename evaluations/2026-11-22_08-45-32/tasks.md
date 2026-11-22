# Proposed Improvement Tasks — 2026-11-22_08-45-32

Derived from [analysis.md](./analysis.md) and raw pytest output in [report](./report).

---

## 1. Code Fixes

- [x] **Enable multi-turn state persistence in [`src/agent_evaluation/weather_agent.py`](../../src/agent_evaluation/weather_agent.py):**
  Add a `checkpointer` parameter to `create_weather_agent()` (defaulting to `MemorySaver()` from `langgraph.checkpoint.memory`, or injected by [`evals/harness.py`](../../evals/harness.py)) and pass it to `create_deep_agent(..., checkpointer=checkpointer)`. This fixes conversation memory across turns and prevents `messages[prev_count:]` slicing corruption in `evals/harness.py`.
- [x] **Guard against empty responses in [`evals/evaluators/llm_judge.py`](../../evals/evaluators/llm_judge.py):**
  In `evaluate_response_quality()`, short-circuit and return `EvalOutcome(name="response_quality", passed=False, score=0.0, reason="Final agent response is empty.")` when `not run.final_response.strip()`.

---

## 2. Skill Updates

- [x] **Narrow the no-tool input validation rule in [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md) (Section 1):**
  Restrict the no-tool rule to *missing or vague* locations (`"here"`, `"outside"`, `"my location"`), allowing the weather tools to validate whether a specific named place exists (resolving the contradiction with `unknown_city_error_recovery`).
- [x] **Clarify unsupported unit handling in [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md) (Section 1):**
  Explicitly instruct the agent **not** to manually convert temperatures to unsupported units (e.g., Kelvin), and always state explicitly that only **Celsius** and **Fahrenheit** are supported before asking for a preference or reporting in Celsius.
- [x] **Make `get_temperature` default for general weather queries in [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md) (Section 2 & Quality Checklist):**
  Instruct the agent to call **both** `get_weather` and `get_temperature` by default for general weather queries (e.g., *"What is the weather like in X?"*), omitting `get_temperature` only for narrow condition-only questions (e.g., *"Is it raining in X?"*).
- [x] **Prevent out-of-scope follow-up offers in [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md) (Section 3):**
  Add a reminder not to offer multi-day or future forecasts in closing follow-up questions (reinforcing [`AGENTS.md`](../../AGENTS.md) Core Rule 4).

---

## 3. Scenario Updates

- [x] **Relax overly strict `grounded_any_of` for `unknown_city_error_recovery` in [`evals/datasets/weather_flows.yaml`](../../evals/datasets/weather_flows.yaml):**
  Expand `grounded_any_of` to include natural error paraphrases (`"does not match"`, `"doesn't match"`, `"non-existent"`, `"does not exist"`, `"doesn't exist"`, `"not a valid"`, `"fictional"`, `"invalid"`), and add `forbidden_substrings: ["°C", "°F"]` to deterministically guard against hallucinated temperatures.
- [x] **Clean up `unsupported_unit_kelvin` in [`evals/datasets/weather_flows.yaml`](../../evals/datasets/weather_flows.yaml):**
  Remove redundant lowercase duplicates in `grounded_any_of` (`["Celsius", "Fahrenheit"]`), and add `forbidden_substrings` (e.g., `["281.15"]`) if manual Kelvin conversion is disallowed.
- [x] **Align `turn_assertions` and `rubric_criteria` for `multi_turn_unit_followup` in [`evals/datasets/weather_flows.yaml`](../../evals/datasets/weather_flows.yaml):**
  Add `get_temperature` to `turn_index: 0` `required_tools` so deterministic assertions match `rubric_criteria` (*"On turn 1, the agent checks Madrid in Celsius"*).
