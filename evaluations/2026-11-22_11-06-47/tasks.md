# Proposed Improvement Tasks — 2026-11-22_11-06-47

Synthesized from [analysis.md](./analysis.md) and [progress.md](./progress.md) (raw output: [report](./report)).

**Goal:** Fix the single remaining failure (`multi_turn_unit_followup` #6) to achieve **10/10 scenarios (100%)** and **60/60 checks (100%)** by prohibiting manual Celsius ↔ Fahrenheit conversions and requiring a fresh `get_temperature` tool call whenever the user asks for a different unit.

---

## 1. Code Fixes

- [x] **Forbid manual °C ↔ °F conversion in `system_prompt` and `get_temperature` docstring in [`src/agent_evaluation/weather_agent.py`](../../src/agent_evaluation/weather_agent.py):**
  - Update `system_prompt` in `create_weather_agent()` to state explicitly: *"NEVER manually convert temperatures between units (not even Celsius ↔ Fahrenheit): if the user asks for a temperature in another supported unit (e.g., Fahrenheit after a Celsius reading), ALWAYS call `get_temperature` with the requested unit."*
  - Update `get_temperature` docstring to note: *"Always call this tool whenever the user requests a temperature in a different unit (e.g., Fahrenheit after Celsius); never convert units manually."*

---

## 2. Skill & Agent Memory Updates

- [x] **Extend Core Rule 3 in [`AGENTS.md`](../../AGENTS.md) and Section 1/2 in [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md):**
  - Explicitly state: *"Never manually convert temperatures between Celsius and Fahrenheit — if the user asks for a temperature in a different unit on a follow-up turn, always call `get_temperature` with that unit (`'celsius'` or `'fahrenheit'`) to get the exact tool reading."*

---

## 3. Scenario Updates

- [x] **No scenario changes required:**
  - `multi_turn_unit_followup` caught a real numeric error (`56.0°F` instead of `55.4°F` for `feels like`). Keep all 10 scenarios in [`evals/datasets/weather_flows.yaml`](../../evals/datasets/weather_flows.yaml) unchanged to verify **10/10 (100%)** cleanly.
