# Evaluation Progress Report — 2026-11-22_14-47-29 vs. 2026-11-22_14-27-51 (and Full Campaign)

## 1. Overall Verdict

**Target achieved — 10/10 scenarios (100%) and 60/60 checks (100%) across all 4 deterministic and 2 LLM-as-a-Judge evaluators:**

- Commit `06ee2b4` (turn-grouped `_format_trajectory()` in `llm_judge.py`) resolved the sole remaining failure (`multi_turn_unit_followup` #6) cleanly, taking the suite from **9/10 (59/60)** to **10/10 (60/60)** with **zero regressions**.
- Across the full 10-run optimization campaign, scenario pass rate doubled from **5/10 (50%) → 10/10 (100%)** (+50%), individual checks rose from **49/60 (81.7%) → 60/60 (100%)** (+18.3%), and runtime improved from **8m 19s → 7m 57s** (-22.7s).

---

## 2. Full Campaign Progression

| Run | Timestamp | Git HEAD | Scenarios | Checks | Duration | Key Milestone / Takeaway |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 1 | `2026-11-22_08-45-32` | `72e1b54` | 5/10 (50%) | 49/60 (81.7%) | 8m 19s | Baseline; uncovered missing `checkpointer` breaking multi-turn flows |
| 2 | `2026-11-22_10-19-46` | `693633d` | 7/10 (70%) | 53/60 (88.3%) | 7m 38s | `MemorySaver` fixed multi-turn state; proved `SKILL.md` not loaded under progressive disclosure |
| 3 | `2026-11-22_10-34-09` | `71b0281` | 7/10 (70%) | 55/60 (91.7%) | 6m 52s | Propagated rules to `AGENTS.md` + `system_prompt`; `tool_policy` hit 10/10 |
| 4 | `2026-11-22_10-49-24` | `d4731c9` | 8/10 (80%) | 58/60 (96.7%) | 6m 59s | Fixed `madrid_happy_path`; caught `12°C` hallucination & judge Turn 1 blind spot |
| 5 | `2026-11-22_11-06-47` | `2bb48bf` | 9/10 (90%) | 57/60 (95.0%) | 8m 01s | Fixed #5 & #9; caught manual °C→°F miscalculation (`56.0°F` vs `55.4°F`) on #6 |
| 6 | `2026-11-22_11-23-34` | `0b26153` | 9/10 (90%) | 58/60 (96.7%) | 9m 52s | First 40/40 (100%) deterministic run; caught ambiguous Kelvin *"either/or"* branch |
| 7 | `2026-11-22_11-40-01` | `4c3818c` | 8/10 (80%) | 56/60 (93.3%) | 9m 00s | Fixed #9 Kelvin; uncovered `system_prompt` bloat (#8 empty) & brittle synonym list (#7) |
| 8 | `2026-11-22_14-05-35` | `b1d7d79` | 7/10 (70%) | 51/60 (85.0%) | 8m 12s | Fixed #7 & #8; proved which invariants must remain in `system_prompt` vs. `AGENTS.md` |
| 9 | `2026-11-22_14-27-51` | `90e84ee` | 9/10 (90%) | 59/60 (98.3%) | 8m 36s | Compact 4-invariant `system_prompt` achieved 100% real agent accuracy; caught judge turn-label bug |
| **10** | **`2026-11-22_14-47-29`** | **`06ee2b4`** | **10/10 (100%)** | **60/60 (100%)** | **7m 57s** | **Turn-grouped `_format_trajectory()` locked in 10/10 scenarios & 60/60 checks** |

---

## 3. Evaluator Pass Rate Comparison (Baseline → Final)

| Evaluator | Baseline (Run 1) | Previous (Run 9) | Final (Run 10) | Total Gain |
| :--- | :---: | :---: | :---: | :---: |
| `efficiency_budget` | 10/10 (100%) | 10/10 (100%) | **10/10 (100%)** | `0%` |
| `trajectory_match` | 8/10 (80%) | 10/10 (100%) | **10/10 (100%)** | **+20%** |
| `tool_policy` | 8/10 (80%) | 10/10 (100%) | **10/10 (100%)** | **+20%** |
| `groundedness` | 6/10 (60%) | 10/10 (100%) | **10/10 (100%)** | **+40%** |
| `trajectory_quality` (Judge) | 7/10 (70%) | 9/10 (90%) | **10/10 (100%)** | **+30%** |
| `response_quality` (Judge) | 10/10 (100%) | 10/10 (100%) | **10/10 (100%)** | `0%` *(hardened with empty-response & full-conversation checks)* |
