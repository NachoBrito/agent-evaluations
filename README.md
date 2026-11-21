# Agent Evaluation — Weather Agent

A local-first AI weather agent built with [`deepagents`](https://github.com/langchain-ai/deepagents) and LangChain, powered by a local LLM via `llama.cpp` (`llama-server`), live weather data from [Open-Meteo](https://open-meteo.com/), and local OpenTelemetry tracing via [Arize Phoenix](https://phoenix.arize.com/).

## Project Structure

```text
.
├── AGENTS.md                              # Agent persona, rules, and formatting guidelines
├── pyproject.toml                         # Project metadata and dependencies
├── skills/
│   └── weather/
│       └── SKILL.md                       # Step-by-step weather lookup skill
└── src/
    └── agent_evaluation/
        ├── __init__.py                    # CLI entry point and streaming loop
        ├── display_utils.py               # Rich terminal UI (panels, spinner, tool status)
        ├── telemetry.py                   # OpenTelemetry / Arize Phoenix setup
        ├── weather_agent.py               # Agent factory and LangChain tools
        └── weather_client.py              # WeatherClient protocol + OpenMeteoClient
```

## Prerequisites

- **Python 3.14+**
- **[uv](https://docs.astral.sh/uv/)** package manager
- **[llama.cpp](https://github.com/ggml-org/llama.cpp)** (`llama-server`) for serving a local GGUF model
- *(Optional)* **Docker** or **`uvx`** to run the local Arize Phoenix UI for traces

## Quick Start

### 1. Install dependencies

```bash
uv sync
```

### 2. Start the local LLM (`llama-server`)

Start `llama-server` on port `8080` with `--jinja` enabled (required for proper tool-call parsing).

Example tuned for a **4 GB VRAM** GPU (e.g., RTX 3050 Ti Laptop) with Vulkan:

```bash
llama-server \
  -hf Qwen/Qwen3-4B-GGUF:Q4_K_M \
  --device Vulkan1 \
  -ngl 99 \
  --port 8080 \
  --jinja \
  --flash-attn on \
  -ctk q8_0 -ctv q8_0 \
  -c 8192 \
  -np 1
```

> **Tip:** Adjust `--device` (e.g., remove it for CUDA/Metal or pick your GPU) and `-c` (context length) to match your hardware. If you have more VRAM, you can increase `-c 16384` or use a larger model/quant.

### 3. (Optional) Start Arize Phoenix for local telemetry

In a separate terminal, launch the Phoenix trace collector and UI:

**With Docker (recommended):**
```bash
docker run --rm -p 6006:6006 -p 4317:4317 arizephoenix/phoenix:latest
```

*(To skip authentication for local development, add `-e PHOENIX_ENABLE_AUTH=false` to the `docker run` command above.)*

**Or with `uvx` (no Docker needed):**
```bash
uvx arize-phoenix serve
```

Then open [http://localhost:6006](http://localhost:6006) in your browser to inspect LLM calls, prompts, latencies, token usage, and tool executions.

If Phoenix prompts you to log in (when authentication is enabled), the default admin credentials are:
- **Email:** `admin@localhost`
- **Password:** `admin` *(you will be prompted to change this on first login)*

When authentication is enabled, create an API key in Phoenix (**Settings → API Keys**) and export it before running the agent (otherwise span exports will fail with `401 Unauthorized`):

```bash
export PHOENIX_API_KEY="<your-api-key>"
```

### 4. Run the agent

Run with the default prompt (*"What is the weather like in Madrid?"*):

```bash
uv run agent-evaluation
```

Or pass your own question as arguments:

```bash
uv run agent-evaluation "What is the weather and temperature in Tokyo in fahrenheit?"
```

## Configuration

| Environment Variable | Default | Description |
| :--- | :--- | :--- |
| `LLM_BASE_URL` | `http://localhost:8080/v1` | OpenAI-compatible base URL for the agent LLM |
| `LLM_MODEL` | `local-model` | Model identifier sent to the LLM server |
| `LLM_API_KEY` | `not_needed` | API key for the agent LLM server |
| `EVAL_JUDGE_BASE_URL` | *(falls back to `LLM_BASE_URL`)* | OpenAI-compatible base URL for LLM-as-a-Judge evals |
| `EVAL_JUDGE_MODEL` | *(falls back to `LLM_MODEL`)* | Model name for LLM-as-a-Judge evals |
| `EVAL_JUDGE_API_KEY` | *(falls back to `LLM_API_KEY`)* | API key for LLM-as-a-Judge evals |
| `PHOENIX_ENABLED` | `true` | Set to `false` to disable OpenTelemetry tracing |
| `PHOENIX_BASE_URL` | `http://localhost:6006` | Base URL for Arize Phoenix Experiments API |
| `PHOENIX_COLLECTOR_ENDPOINT` | `http://localhost:6006/v1/traces` | OTLP HTTP endpoint for Phoenix |
| `PHOENIX_API_KEY` | *(unset)* | API key from Phoenix **Settings → API Keys** (required if Phoenix auth is enabled) |

To run without telemetry (for example, when Phoenix is not running):

```bash
PHOENIX_ENABLED=false uv run agent-evaluation "Weather in Berlin?"
```

## Agentic Flow Evaluations

Evaluation datasets, deterministic trajectory evaluators (`agentevals`), LLM-as-a-Judge rubrics (`arize-phoenix-evals`), and Arize Phoenix Experiments live under `evals/` and `tests/`.

For a full technical walkthrough of the evaluation architecture, custom YAML schema, `pytest` flags, LLM-as-a-Judge setup, and Arize Phoenix UI guide, see [docs/EVALUATIONS.md](docs/EVALUATIONS.md).

### Install evaluation dependencies

```bash
uv sync --group eval
```

### 1. Run offline framework unit tests (no LLM required)

```bash
uv run pytest
```

### 2. Run end-to-end agentic flow evals (requires `llama-server`)

Uses `FakeWeatherClient` (no external Open-Meteo network calls) to verify single-turn, multi-turn, error-recovery, and scope-adherence trajectories defined in `evals/datasets/weather_flows.yaml`:

```bash
uv run pytest tests/test_agentic_flows.py --run-live-agent
```

To also run LLM-as-a-Judge rubric checks (trajectory quality + tone/formatting):

```bash
uv run pytest tests/test_agentic_flows.py --run-live-agent --run-judge
```

### 3. Run as a tracked Arize Phoenix Experiment

With `llama-server` and Arize Phoenix running locally:

```bash
uv run python -m evals.run_phoenix_experiment --experiment-name weather-v1
```

Pass `--with-judge` to include LLM-as-a-Judge scores, or `--dry-run 2` to test on the first 2 examples before uploading.

## Swapping the Weather Provider

Weather API calls are encapsulated behind the `WeatherClient` protocol in `src/agent_evaluation/weather_client.py`. To use another provider (or a mock client in evaluations/tests), implement `get_weather(city)` and `get_temperature(city, unit)` and pass your client to `create_weather_agent`:

```python
from agent_evaluation.weather_agent import create_weather_agent

agent = create_weather_agent(weather_client=MyCustomWeatherClient())
```
