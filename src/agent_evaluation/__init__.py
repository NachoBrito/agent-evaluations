
import sys
import asyncio

from rich.console import Console
from rich.live import Live

from .display_utils import AgentDisplay
from .telemetry import setup_telemetry
from .weather_agent import create_weather_agent

'''
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
'''

console = Console()

async def _run():
    """Run the weather agent with streaming output."""
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = "What is the weather like in Madrid?"

    console.print()
    console.print("[bold blue]Weather Agent[/]")
    console.print(f"[dim]Task: {task}[/]")
    console.print()

    agent = create_weather_agent()
    display = AgentDisplay(console)

    console.print()

    # Use Live display for spinner during waiting periods
    with Live(display.spinner, console=console, refresh_per_second=10, transient=True) as live:
        async for chunk in agent.astream(
            {"messages": [("user", task)]},
            config={"configurable": {"thread_id": "weather-agent-demo"}},
            stream_mode="values",
        ):
            if "messages" in chunk:
                messages = chunk["messages"]
                if len(messages) > display.printed_count:
                    # Temporarily stop spinner to print
                    live.stop()
                    for msg in messages[display.printed_count:]:
                        display.print_message(msg)
                    display.printed_count = len(messages)
                    # Resume spinner
                    live.start()
                    live.update(display.spinner)

    console.print()
    console.print("[bold green]✓ Done![/]")


def main():
    tracer_provider = setup_telemetry()
    try:
        asyncio.run(_run())
    finally:
        if tracer_provider is not None:
            tracer_provider.shutdown()