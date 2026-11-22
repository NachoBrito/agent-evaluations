# Evaluation Progress Report — 2026-11-22_10-49-24 vs. 2026-11-22_10-34-09

## 1. Overall Verdict

**Strong net progress — new high-water mark at 8/10 scenarios (80%) and 58/60 individual checks (96.7%):**

- **4 of 6 evaluators reached 10/10 (100%)**: `efficiency_budget`, `tool_policy`, `trajectory_match`, and `trajectory_quality`.
- **`madrid_happy_path_default_celsius` (#1) passed for the first time (6/6)** — validating that requiring parallel `get_weather` + `get_temperature` calls in `system_prompt` and `AGENTS.md` (`f332c3f`, `2a8a282`) fixed the last general-weather tool-selection failure.
- **`unknown_city_error_recovery` (#7) returned to PASS (6/6)** after adding `"could not be found"` (`d4731c9`).
- **One subtle side effect uncovered:** Pressuring the model to report temperature in `system_prompt` caused it to **hallucinate `12°C`** on the rain-only `multi_turn_clarification_flow` (#5) where it didn't call `get_temperature`. Catching this early is a valuable win for agent safety/honesty.

---

## 2. High-Level Metric Comparison

| Metric | Run 1 (`08-45-32`) | Run 2 (`10-19-46`) | Run 3 (`10-34-09`) | Current (`10-49-24`) | Delta (vs. Run 3) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Scenarios Passed** | 5 / 10 (50%) | 7 / 10 (70%) | 7 / 10 (70%) | **8 / 10 (80%)** | **+1 (+10%)** |
| **Individual Checks Passed** | 49 / 60 (81.7%) | 53 / 60 (88.3%) | 55 / 60 (91.7%) | **58 / 60 (96.7%)** | **+3 (+5.0%)** |
| **Total Wall-Clock Time** | 499.89s (8m 19s) | 458.45s (7m 38s) | 412.82s (6m 52s) | **419.59s (6m 59s)** | `+6.77s (+1.6%)` |

### Evaluator Pass Rate Comparison

| Evaluator | Run 1 | Run 2 | Run 3 | Current | Delta (vs. Run 3) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `efficiency_budget` | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | **10/10 (100%)** | `0%` |
| `tool_policy` | 8/10 (80%) | 9/10 (90%) | 10/10 (100%) | **10/10 (100%)** | `0%` |
| `trajectory_match` | 8/10 (80%) | 9/10 (90%) | 9/10 (90%) | **10/10 (100%)** | **+10%** |
| `trajectory_quality` (Judge) | 7/10 (70%) | 8/10 (80%) | 9/10 (90%) | **10/10 (100%)** | **+10%** |
| `groundedness` | 6/10 (60%) | 8/10 (80%) | 8/10 (80%) | **9/10 (90%)** | **+10%** |
| `response_quality` (Judge) | 10/10 (100%) | 9/10 (90%) | 9/10 (90%) | **9/10 (90%)** | `0%` |

---

## 3. Scenario-by-Scenario Diff

| Scenario | Run 3 (`10-34-09`) | Current (`10-49-24`) | Impact of Last Changes |
| :--- | :---: | :---: | :--- |
| `madrid_happy_path_default_celsius` | FAIL (3/6) | **PASS (6/6)** | **Fixed** by `f332c3f` + `2a8a282` (now calls both tools and reports 14°C!) |
| `tokyo_explicit_fahrenheit` | PASS (6/6) | PASS (6/6) | Stable |
| `multi_city_comparison` | PASS (6/6) | PASS (6/6) | Stable |
| `vague_location_no_tools` | PASS (6/6) | PASS (6/6) | Stable |
| `multi_turn_clarification_flow` | FAIL (5/6) | FAIL (5/6) | Judge now fails for missing Turn 1 context in `response_quality`; agent also hallucinated `12°C` without calling `get_temperature` |
| `multi_turn_unit_followup` | PASS (6/6) | PASS (6/6) | Stable |
| `unknown_city_error_recovery` | FAIL (5/6) | **PASS (6/6)** | **Fixed** by `d4731c9` |
| `service_outage_error_recovery` | PASS (6/6) | PASS (6/6) | Stable |
| `unsupported_unit_kelvin` | PASS (6/6) | FAIL (5/6) | Minor regression: acknowledged Celsius/Fahrenheit but still appended `281.15 K` formula and leaked `` `get_temperature` `` |
| `out_of_scope_forecast` | PASS (6/6) | PASS (6/6) | Stable |

---

## 4. Assessment of Each Commit

1. **`f332c3f` (Code Fixes — parallel tool prompt + judge temperature clause):** **Net positive, with one side effect to tighten.** Solved `madrid_happy_path_default_celsius` (6/6) and eliminated the rain-only temperature complaint from `response_quality`, but the strong phrasing about reporting temperature nudged the agent to fabricate `12°C` on `multi_turn_clarification_flow` when `get_temperature` wasn't called.
2. **`2a8a282` (Skill & Agent Memory Updates — parallel call emphasis):** **Positive.** Reinforced parallel tool calling in `AGENTS.md` and `SKILL.md` with zero regressions on multi-turn or multi-city flows.
3. **`d4731c9` (Scenario Updates — `'could not be found'`):** **Positive.** Restored `unknown_city_error_recovery` to PASS (6/6).
