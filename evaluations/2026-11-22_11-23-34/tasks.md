# Proposed Improvement Tasks — 2026-11-22_11-23-34

Synthesized from [analysis.md](./analysis.md) and [progress.md](./progress.md) (raw output: [report](./report)).

**Goal:** Resolve the single remaining judge failure (`unsupported_unit_kelvin` #9) to achieve **10/10 scenarios (100%)** and **60/60 checks (100%)** by replacing the ambiguous unsupported-unit *"either/or"* branch with one crisp, deterministic behavior.

---

## 1. Code Fixes

- [x] **Make unsupported-unit handling unambiguous and concise in [`src/agent_evaluation/weather_agent.py`](../../src/agent_evaluation/weather_agent.py):**
  - Update `system_prompt` in `create_weather_agent()` so that for unsupported units (e.g., Kelvin), the agent follows **one** clear path: **do NOT call any tool**, do NOT convert to Kelvin or mention internal tool names, simply state that only **Celsius** and **Fahrenheit** are supported, and explicitly **ask which unit the user prefers** (e.g., *"Would you like the temperature in Celsius or Fahrenheit?"*). Never end with a dangling *"Let me check..."*.

---

## 2. Skill & Agent Memory Updates

- [x] **Remove the ambiguous *"either/or"* branch for unsupported units in [`AGENTS.md`](../../AGENTS.md) (Core Rule 3) and [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md) (Section 1):**
  - Replace *"either ask which they prefer or provide the temperature in Celsius"* with: *"do NOT call any tool; state clearly that you only support **Celsius** and **Fahrenheit**, and explicitly ask which unit they prefer (for example, 'Would you like the temperature in Celsius or Fahrenheit?')."*

---

## 3. Scenario Updates

- [x] **No scenario changes required:**
  - All 40/40 deterministic checks already pass. Keep all 10 scenarios in [`evals/datasets/weather_flows.yaml`](../../evals/datasets/weather_flows.yaml) unchanged to verify **10/10 (100%)** and **60/60 (100%)**.
