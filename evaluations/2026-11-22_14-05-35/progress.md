# Evaluation Progress Report — 2026-11-22_14-05-35 vs. 2026-11-22_11-40-01

## 1. Overall Verdict

**Regression on overall score (7/10 vs. 8/10; 51/60 vs. 56/60 checks), but high diagnostic value:**

- **Both Run 7 targets succeeded:**
  - `unknown_city_error_recovery` (#7) → **PASS (6/6)** (`b1d7d79`).
  - `service_outage_error_recovery` (#8) → **PASS (6/6)** (`a000186` tool-error rule + slimmer prompt).
  - Wall-clock time improved by **48s (-8.8%)** (540.53s → 492.75s).
- **Over-trimming `system_prompt` (`a000186`) caused all 3 regressions (#1, #3, #6):**
  - Dropping the explicit *"get_weather does NOT return temperature"* + concrete question examples + *"never invent a temperature without calling `get_temperature`"* lines from `system_prompt` proved that this local LLM gives much higher weight to `system_prompt` than to `MemoryMiddleware`-injected `AGENTS.md`.
  - We now know the **exact minimal set of rules** that must remain in `system_prompt` vs. what can safely live in `AGENTS.md` alone.

---

## 2. High-Level Metric Comparison

| Metric | Run 1 (`08-45-32`) | Run 6 (`11-23-34`) | Run 7 (`11-40-01`) | Current (`14-05-35`) | Delta (vs. Run 7) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Scenarios Passed** | 5/10 (50%) | 9/10 (90%) | 8/10 (80%) | **7/10 (70%)** | `-1 (-10%)` |
| **Individual Checks** | 49/60 (81.7%) | 58/60 (96.7%) | 56/60 (93.3%) | **51/60 (85.0%)** | `-5 (-8.3%)` |
| **Wall-Clock Time** | 8m 19s | 9m 52s | 9m 00s | **8m 12s** | **-48s (-8.8%)** |

### Evaluator Pass Rate Comparison

| Evaluator | Run 6 | Run 7 | Current | Delta (vs. Run 7) |
| :--- | :---: | :---: | :---: | :---: |
| `efficiency_budget` | 10/10 | 10/10 | **10/10 (100%)** | `0%` |
| `tool_policy` | 10/10 | 10/10 | **9/10 (90%)** | `-10%` (#6) |
| `trajectory_match` | 10/10 | 10/10 | **8/10 (80%)** | `-20%` (#1, #3) |
| `groundedness` | 10/10 | 8/10 | **8/10 (80%)** | `0%` (#7/#8 fixed; #1/#3 regressed) |
| `trajectory_quality` (Judge) | 9/10 | 9/10 | **8/10 (80%)** | `-10%` (#8 fixed; #1/#3 regressed) |
| `response_quality` (Judge) | 9/10 | 9/10 | **8/10 (80%)** | `-10%` (#8 fixed; #1/#3 regressed) |

---

## 3. Scenario-by-Scenario Diff

| Scenario | Run 7 (`11-40-01`) | Current (`14-05-35`) | Impact of Last Changes |
| :--- | :---: | :---: | :--- |
| `madrid_happy_path_default_celsius` | PASS (6/6) | FAIL (2/6) | **Regression** (`a000186`): skipped `get_temperature` after `get_weather`-omits-temp note was cut from `system_prompt` |
| `tokyo_explicit_fahrenheit` | PASS (6/6) | PASS (6/6) | Stable |
| `multi_city_comparison` | PASS (6/6) | FAIL (2/6) | **Regression** (`a000186`): skipped `get_temperature(Berlin)` and fabricated `12.5°C` |
| `vague_location_no_tools` | PASS (6/6) | PASS (6/6) | Stable |
| `multi_turn_clarification_flow` | PASS (6/6) | PASS (6/6) | Stable |
| `multi_turn_unit_followup` | PASS (6/6) | FAIL (5/6) | **Regression** (`a000186`): Turn 0 skipped `get_temperature` (Turn 1 still worked) |
| `unknown_city_error_recovery` | FAIL (5/6) | **PASS (6/6)** | **Fixed** by `b1d7d79` |
| `service_outage_error_recovery` | FAIL (3/6) | **PASS (6/6)** | **Fixed** by `a000186` (tool-error recovery rule + slimmer prompt) |
| `unsupported_unit_kelvin` | PASS (6/6) | PASS (6/6) | Stable (confirming Kelvin rule works cleanly from `AGENTS.md`) |
| `out_of_scope_forecast` | PASS (6/6) | PASS (6/6) | Stable |

---

## 4. Assessment of Each Commit

1. **`b1d7d79` (Scenario Updates — remove brittle synonym list from #7):** **Clean win.** Fixed `unknown_city_error_recovery` permanently without weakening factual or semantic checks.
2. **`a000186` (Code Fixes — slim `system_prompt` + tool-error rule):** **Half win, half over-correction.** The tool-error recovery rule fixed #8 and sped up the suite by 48s, but cutting the explicit `get_weather`-omits-temperature and anti-hallucination sentences from `system_prompt` regressed #1, #3, and #6 Turn 0. Restoring just those two concise invariants into `system_prompt` (keeping it compact at ~90 words) should combine the wins of Runs 6, 7, and 8 to hit **10/10 (100%)**.
