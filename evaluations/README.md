# Evaluation Reports

Historical reports from live agentic flow evaluation runs (`tests/test_agentic_flows.py`), including metrics, root-cause analysis, progress comparisons, proposed improvement tasks, and raw pytest output.

For the repeatable evaluation-driven improvement workflow, lessons learned, and guidelines for future iterations, see [HOWTO.md](./HOWTO.md).

## Reports

| Timestamp | Git HEAD | Command / Mode | Result | Checks | Duration | Analysis | Progress | Tasks | Raw Output |
| :--- | :---: | :--- | :---: | :---: | :---: | :--- | :--- | :--- | :--- |
| `2026-11-22_08-45-32` | `72e1b54` | `pytest tests/test_agentic_flows.py --run-live-agent --run-judge` | 5/10 (50%) | 49/60 (81.7%) | 8m 19s | [analysis.md](./2026-11-22_08-45-32/analysis.md) | — (baseline) | [tasks.md](./2026-11-22_08-45-32/tasks.md) | [report](./2026-11-22_08-45-32/report) |
| `2026-11-22_10-19-46` | `693633d` | `pytest tests/test_agentic_flows.py --run-live-agent --run-judge` | 7/10 (70%) | 53/60 (88.3%) | 7m 38s | [analysis.md](./2026-11-22_10-19-46/analysis.md) | [progress.md](./2026-11-22_10-19-46/progress.md) | [tasks.md](./2026-11-22_10-19-46/tasks.md) | [report](./2026-11-22_10-19-46/report) |
| `2026-11-22_10-34-09` | `71b0281` | `pytest tests/test_agentic_flows.py --run-live-agent --run-judge` | 7/10 (70%) | 55/60 (91.7%) | 6m 52s | [analysis.md](./2026-11-22_10-34-09/analysis.md) | [progress.md](./2026-11-22_10-34-09/progress.md) | [tasks.md](./2026-11-22_10-34-09/tasks.md) | [report](./2026-11-22_10-34-09/report) |
| `2026-11-22_10-49-24` | `d4731c9` | `pytest tests/test_agentic_flows.py --run-live-agent --run-judge` | 8/10 (80%) | 58/60 (96.7%) | 6m 59s | [analysis.md](./2026-11-22_10-49-24/analysis.md) | [progress.md](./2026-11-22_10-49-24/progress.md) | [tasks.md](./2026-11-22_10-49-24/tasks.md) | [report](./2026-11-22_10-49-24/report) |
| `2026-11-22_11-06-47` | `2bb48bf` | `pytest tests/test_agentic_flows.py --run-live-agent --run-judge` | 9/10 (90%) | 57/60 (95.0%) | 8m 01s | [analysis.md](./2026-11-22_11-06-47/analysis.md) | [progress.md](./2026-11-22_11-06-47/progress.md) | [tasks.md](./2026-11-22_11-06-47/tasks.md) | [report](./2026-11-22_11-06-47/report) |
| `2026-11-22_11-23-34` | `0b26153` | `pytest tests/test_agentic_flows.py --run-live-agent --run-judge` | 9/10 (90%) | 58/60 (96.7%) *(40/40 det.)* | 9m 52s | [analysis.md](./2026-11-22_11-23-34/analysis.md) | [progress.md](./2026-11-22_11-23-34/progress.md) | [tasks.md](./2026-11-22_11-23-34/tasks.md) | [report](./2026-11-22_11-23-34/report) |
| `2026-11-22_11-40-01` | `4c3818c` | `pytest tests/test_agentic_flows.py --run-live-agent --run-judge` | 8/10 (80%) | 56/60 (93.3%) | 9m 00s | [analysis.md](./2026-11-22_11-40-01/analysis.md) | [progress.md](./2026-11-22_11-40-01/progress.md) | [tasks.md](./2026-11-22_11-40-01/tasks.md) | [report](./2026-11-22_11-40-01/report) |
| `2026-11-22_14-05-35` | `b1d7d79` | `pytest tests/test_agentic_flows.py --run-live-agent --run-judge` | 7/10 (70%) | 51/60 (85.0%) | 8m 12s | [analysis.md](./2026-11-22_14-05-35/analysis.md) | [progress.md](./2026-11-22_14-05-35/progress.md) | [tasks.md](./2026-11-22_14-05-35/tasks.md) | [report](./2026-11-22_14-05-35/report) |
| `2026-11-22_14-27-51` | `90e84ee` | `pytest tests/test_agentic_flows.py --run-live-agent --run-judge` | 9/10 (90%) | 59/60 (98.3%) *(5/6 evals 100%)* | 8m 36s | [analysis.md](./2026-11-22_14-27-51/analysis.md) | [progress.md](./2026-11-22_14-27-51/progress.md) | [tasks.md](./2026-11-22_14-27-51/tasks.md) | [report](./2026-11-22_14-27-51/report) |
| `2026-11-22_14-47-29` | `06ee2b4` | `pytest tests/test_agentic_flows.py --run-live-agent --run-judge` | **10/10 (100%)** | **60/60 (100%)** | **7m 57s** | [analysis.md](./2026-11-22_14-47-29/analysis.md) | [progress.md](./2026-11-22_14-47-29/progress.md) | [tasks.md](./2026-11-22_14-47-29/tasks.md) | [report](./2026-11-22_14-47-29/report) |
