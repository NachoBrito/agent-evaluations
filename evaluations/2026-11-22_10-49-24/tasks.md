# Proposed Improvement Tasks — 2026-11-22_10-49-24

Synthesized from [analysis.md](./analysis.md) and [progress.md](./progress.md) (raw output: [report](./report)).

**Goal:** Eliminate the last 2 failures (reaching **10/10** and **60/60**), fix the temperature hallucination caught on `multi_turn_clarification_flow`, prevent internal tool-name leakage and Kelvin math on `unsupported_unit_kelvin`, and fix the multi-turn context blind spot in `evaluate_response_quality`.

---

## 1. Code Fixes

- [x] **Prevent temperature hallucination and Kelvin formula / tool-name leakage in [`src/agent_evaluation/weather_agent.py`](../../src/agent_evaluation/weather_agent.py):**
  - Update `system_prompt` in `create_weather_agent()` to add two crisp guardrails:
    1. **Anti-hallucination:** *"NEVER mention or guess a temperature unless you called `get_temperature` and received a temperature from the tool; if you only called `get_weather`, report only the conditions it returned."*
    2. **Strict Kelvin refusal & no tool-name leaks:** *"If asked for an unsupported unit like Kelvin, do NOT calculate or show a Kelvin value or conversion formula, and never mention internal tool names like `get_temperature`—simply state that only Celsius and Fahrenheit are supported and report the Celsius temperature (or ask which unit they prefer)."*
- [x] **Fix multi-turn context blind spot in `evaluate_response_quality` in [`evals/evaluators/llm_judge.py`](../../evals/evaluators/llm_judge.py):**
  - Pass the full user+assistant turn transcript (e.g., `Turn 1 User / Turn 1 Assistant / Turn 2 User / Turn 2 Assistant`) to `RESPONSE_QUALITY_TEMPLATE` instead of hiding prior assistant turns, so the judge can accurately grade multi-turn rubrics (like `multi_turn_clarification_flow`) without falsely claiming Turn 1 skipped asking for a city.
  - Add an offline unit test in [`tests/test_eval_framework.py`](../../tests/test_eval_framework.py) verifying multi-turn transcript formatting for `evaluate_response_quality`.

---

## 2. Skill & Agent Memory Updates

- [x] **Add anti-hallucination and no-formula / no-tool-name rules to [`AGENTS.md`](../../AGENTS.md) and [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md):**
  - Under Core Rule 2 (`AGENTS.md`) and Section 2 (`SKILL.md`): explicitly state that the agent must **never mention a temperature unless `get_temperature` was called** and must report only values actually returned by tools.
  - Under Core Rule 3 (`AGENTS.md`) and Section 1 (`SKILL.md`): explicitly forbid outputting conversion formulas (e.g., `+ 273.15`) or Kelvin values, and forbid mentioning internal tool/function names (e.g., `get_temperature`) in responses.

---

## 3. Scenario Updates

- [x] **No scenario relaxations required:**
  - Keep `unsupported_unit_kelvin` (`forbidden_substrings: ["281.15"]`) strict to verify the agent truly stops converting to Kelvin.
  - *(Optional hardening)* In [`evals/datasets/weather_flows.yaml`](../../evals/datasets/weather_flows.yaml), keep `multi_turn_clarification_flow` focused on Turn 1 clarification + Turn 2 rain check; once the anti-hallucination rule and multi-turn `response_quality` fix are in place, both remaining failures should cleanly flip to PASS.
