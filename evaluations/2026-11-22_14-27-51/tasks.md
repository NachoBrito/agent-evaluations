# Proposed Improvement Tasks — 2026-11-22_14-27-51

Synthesized from [analysis.md](./analysis.md) and [progress.md](./progress.md) (raw output: [report](./report)).

**Goal:** Fix the single remaining evaluator formatting bug in `evals/evaluators/llm_judge.py` so `trajectory_quality` sees explicit user-turn boundaries and the suite achieves **10/10 scenarios (100%)** and **60/60 checks (100%)** with zero changes to the agent, skill, or scenarios.

---

## 1. Code Fixes

- [x] **Group `_format_trajectory()` by explicit user turn in [`evals/evaluators/llm_judge.py`](../../evals/evaluators/llm_judge.py):**
  - Instead of dumping a flat `run.openai_trajectory` list without turn markers (which caused the judge to miscount two sequential tool calls in Turn 1 as Turn 1 and Turn 2), format the trajectory as a turn-structured JSON list:
    `[{"turn": 1, "user_input": ..., "messages": to_openai_domain_trajectory(turn.new_messages)}, ...]` (falling back to `run.openai_trajectory` if `run.turns` is empty).
  - Add an offline unit test in [`tests/test_eval_framework.py`](../../tests/test_eval_framework.py) verifying `_format_trajectory()` groups sequential tool calls under `"turn": 1` and separates `"turn": 2`.

---

## 2. Skill & Agent Memory Updates

- [x] **No skill or `AGENTS.md` changes required:**
  - The agent passed 100% of deterministic checks (40/40) and 100% of `response_quality` (10/10). Leave [`src/agent_evaluation/weather_agent.py`](../../src/agent_evaluation/weather_agent.py), [`AGENTS.md`](../../AGENTS.md), and [`skills/weather/SKILL.md`](../../skills/weather/SKILL.md) untouched.

---

## 3. Scenario Updates

- [x] **No scenario changes required:**
  - Leave [`evals/datasets/weather_flows.yaml`](../../evals/datasets/weather_flows.yaml) untouched.
