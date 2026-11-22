# Proposed Improvement Tasks — 2026-11-22_14-05-35

Synthesized from [analysis.md](./analysis.md) and [progress.md](./progress.md) (raw output: [report](./report)).

**Goal:** Combine the wins from Runs 6, 7, and 8 (all 10 scenarios have now passed individually!) to achieve **10/10 (100%)** by restoring the two proven high-attention invariants (`get_weather` omits temperature + anti-hallucination for every city) into a **compact (~90-word)** `system_prompt` while keeping the tool-error recovery rule.

---

## 1. Code Fixes

- [x] **Refine `system_prompt` in [`src/agent_evaluation/weather_agent.py`](../../src/agent_evaluation/weather_agent.py) to the compact 4-invariant sweet spot:**
  Keep `system_prompt` concise (~90 words, ~40% shorter than Run 7's bloated prompt) while retaining the 4 invariants proven necessary in `system_prompt`:
  1. `IMPORTANT: get_weather only returns sky, humidity, and wind — it does NOT return temperature. For ANY general weather question (such as 'What is the weather like in <city>?' or 'What's the weather in <city>?'), you MUST call BOTH get_weather AND get_temperature (defaulting to unit='celsius') for EVERY city mentioned.`
  2. `NEVER mention or guess a temperature for any city unless you called get_temperature for that city and received it from the tool.`
  3. `NEVER manually convert temperatures between units: call get_temperature for Celsius/Fahrenheit follow-ups, and for unsupported units (e.g., Kelvin) call no tools and ask whether they prefer Celsius or Fahrenheit.`
  4. `If any tool returns an error, always reply with a brief, honest explanation or apology — never return an empty response.`

---

## 2. Skill & Agent Memory Updates

- [x] **No skill or `AGENTS.md` changes required:**
  - [`AGENTS.md`](../../AGENTS.md) and [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md) are already complete and consistent.

---

## 3. Scenario Updates

- [x] **No scenario changes required:**
  - Every single one of the 10 scenarios in [`evals/datasets/weather_flows.yaml`](../../evals/datasets/weather_flows.yaml) has passed cleanly without brittle false negatives. Keep all 10 unchanged to verify **10/10 (100%)**.
