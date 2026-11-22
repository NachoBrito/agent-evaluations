# Proposed Improvement Tasks — 2026-11-22_11-40-01

Synthesized from [analysis.md](./analysis.md) and [progress.md](./progress.md) (raw output: [report](./report)).

**Goal:** Reach **10/10 (100%)** and **60/60 (100%)** by eliminating `system_prompt` bloat (fixing the empty response on `service_outage_error_recovery`) and removing the brittle English-synonym list from `unknown_city_error_recovery`.

---

## 1. Code Fixes

- [x] **De-duplicate and slim `system_prompt` + add explicit tool-error rule in [`src/agent_evaluation/weather_agent.py`](../../src/agent_evaluation/weather_agent.py):**
  - Replace the bloated ~150-word `system_prompt` (which duplicates `AGENTS.md`) with a concise, high-signal prompt covering the key behavioral invariants:
    1. Call both `get_weather` and `get_temperature` (default `celsius`) for general weather queries; never guess a temperature without calling `get_temperature`.
    2. Never manually convert temperatures (call `get_temperature` for °C/°F follow-ups; for unsupported units like Kelvin, call no tools and ask whether they prefer Celsius or Fahrenheit).
    3. **Tool-error recovery:** *"If any tool returns an error, always reply to the user with a brief, honest explanation/apology—never return an empty response."*
    4. Stay within current-conditions scope (no multi-day forecasts).

---

## 2. Skill & Agent Memory Updates

- [x] **No skill changes required:**
  - [`AGENTS.md`](../../AGENTS.md) and [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md) already express all rules clearly and consistently (all 8 non-error-recovery scenarios passed 6/6, and `AGENTS.md` already includes honest error reporting).

---

## 3. Scenario Updates

- [x] **Remove the brittle English-synonym list from `unknown_city_error_recovery` in [`evals/datasets/weather_flows.yaml`](../../evals/datasets/weather_flows.yaml):**
  - Keep deterministic `grounded_any_of` focused on objective factual grounding (`- ["Atlantis"]`) and keep `forbidden_substrings: ["°C", "°F"]` to prevent hallucinated temperatures.
  - Rely on `trajectory_quality` and `response_quality` (which already grade semantic accuracy and honesty) to evaluate whether the agent plainly informed the user that Atlantis could not be found—ending the whack-a-mole false negatives (`"does not match"`, `"could not be found"`, `"is not recognized as a valid city"`).
