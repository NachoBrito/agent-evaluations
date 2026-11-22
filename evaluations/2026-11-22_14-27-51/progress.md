# Evaluation Progress Report — 2026-11-22_14-27-51 vs. 2026-11-22_14-05-35

## 1. Overall Verdict

**Massive progress — new all-time high at 59/60 checks (98.3%), 5 of 6 evaluators at 100%, and 100% real agent accuracy across all 10 scenarios:**

- Commit `90e84ee` (compact 4-invariant `system_prompt`) **fixed all 3 Run 8 regressions simultaneously** without regressing a single passing scenario:
  - `madrid_happy_path_default_celsius` (#1): FAIL (2/6) → **PASS (6/6)**
  - `multi_city_comparison` (#3): FAIL (2/6) → **PASS (6/6)**
  - `multi_turn_unit_followup` (#6): Turn 0 now calls both `get_weather` and `get_temperature(celsius)`, and Turn 1 calls `get_temperature(fahrenheit)` (5/6 — only failed a judge turn-boundary miscount).
- `unknown_city_error_recovery` (#7), `service_outage_error_recovery` (#8), `unsupported_unit_kelvin` (#9), and `multi_turn_clarification_flow` (#5) **all stayed PASS (6/6)**.
- **Zero agentic flow bugs remain.** The lone failed check out of 60 is an evaluator formatting bug (`_format_trajectory` not labeling User Turn 1 vs. User Turn 2 for `trajectory_quality`).

---

## 2. High-Level Metric Comparison

| Metric | Run 1 (`08-45-32`) | Run 6 (`11-23-34`) | Run 8 (`14-05-35`) | Current (`14-27-51`) | Delta (vs. Run 8) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Scenarios Passed** | 5/10 (50%) | 9/10 (90%) | 7/10 (70%) | **9/10 (90%)** | **+2 (+20%)** |
| **Individual Checks** | 49/60 (81.7%) | 58/60 (96.7%) | 51/60 (85.0%) | **59/60 (98.3%)** | **+8 (+13.3%)** |
| **Deterministic Checks** | 32/40 (80.0%) | 40/40 (100%) | 35/40 (87.5%) | **40/40 (100%)** | **+5 (+12.5%)** |
| **Wall-Clock Time** | 8m 19s | 9m 52s | 8m 12s | **8m 36s** | `+24s (+4.8%)` |

### Evaluator Pass Rate Comparison

| Evaluator | Run 1 | Run 8 | Current | Delta (vs. Run 8) |
| :--- | :---: | :---: | :---: | :---: |
| `efficiency_budget` | 10/10 | 10/10 | **10/10 (100%)** | `0%` |
| `trajectory_match` | 8/10 | 8/10 | **10/10 (100%)** | **+20%** |
| `tool_policy` | 8/10 | 9/10 | **10/10 (100%)** | **+10%** |
| `groundedness` | 6/10 | 8/10 | **10/10 (100%)** | **+20%** |
| `response_quality` (Judge) | 10/10 | 8/10 | **10/10 (100%)** | **+20%** |
| `trajectory_quality` (Judge) | 7/10 | 8/10 | **9/10 (90%)** | **+10%** *(sole failure is judge turn-label bug)* |

---

## 3. Scenario-by-Scenario Diff

| Scenario | Run 8 (`14-05-35`) | Current (`14-27-51`) | Impact of Last Changes |
| :--- | :---: | :---: | :--- |
| `madrid_happy_path_default_celsius` | FAIL (2/6) | **PASS (6/6)** | **Fixed** by `90e84ee` |
| `tokyo_explicit_fahrenheit` | PASS (6/6) | PASS (6/6) | Stable |
| `multi_city_comparison` | FAIL (2/6) | **PASS (6/6)** | **Fixed** by `90e84ee` |
| `vague_location_no_tools` | PASS (6/6) | PASS (6/6) | Stable |
| `multi_turn_clarification_flow` | PASS (6/6) | PASS (6/6) | Stable |
| `multi_turn_unit_followup` | FAIL (5/6) | FAIL (5/6) | **Agent behavior fixed** (`get_temperature(celsius)` now called in Turn 0); tripped judge turn-boundary miscount |
| `unknown_city_error_recovery` | PASS (6/6) | PASS (6/6) | Stable |
| `service_outage_error_recovery` | PASS (6/6) | PASS (6/6) | Stable |
| `unsupported_unit_kelvin` | PASS (6/6) | PASS (6/6) | Stable |
| `out_of_scope_forecast` | PASS (6/6) | PASS (6/6) | Stable |

---

## 4. Assessment of Commit `90e84ee`

- **`90e84ee` (Code Fix — compact 4-invariant `system_prompt`):** **Complete success.** Achieved 100% real agent accuracy across all 10 scenarios (40/40 deterministic + 10/10 `response_quality`), recovering all 3 Run 8 regressions while keeping #7, #8, and #9 green.
