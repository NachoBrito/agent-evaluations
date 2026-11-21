from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner


class AgentDisplay:
    """Manages the display of agent progress."""

    def __init__(self, console: Console):
        self.console = console
        self.printed_count = 0
        self.current_status = ""
        self.spinner = Spinner("dots", text="Thinking...")

    def update_status(self, status: str):
        self.current_status = status
        self.spinner = Spinner("dots", text=status)

    def print_message(self, msg):
        """Print a message with nice formatting."""
        if isinstance(msg, HumanMessage):
            self.console.print(Panel(str(msg.content), title="You", border_style="blue"))

        elif isinstance(msg, AIMessage):
            content = msg.content
            if isinstance(content, list):
                text_parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
                content = "\n".join(text_parts)

            if content and content.strip():
                self.console.print(Panel(Markdown(content), title="Agent", border_style="green"))

            if msg.tool_calls:
                for tc in msg.tool_calls:
                    name = tc.get("name", "unknown")
                    args = tc.get("args", {})

                    if name == "get_weather":
                        city = args.get("city", "unknown location")
                        self.console.print(f"  [bold cyan]>> Checking weather:[/] {city}")
                        self.update_status(f"Checking weather for {city}...")
                    elif name == "get_temperature":
                        city = args.get("city", "unknown location")
                        unit = args.get("unit", "celsius")
                        self.console.print(f"  [bold yellow]>> Checking temperature:[/] {city} ({unit})")
                        self.update_status(f"Checking temperature for {city}...")
                    else:
                        self.console.print(f"  [bold blue]>> Calling tool:[/] {name}")
                        self.update_status(f"Running {name}...")

        elif isinstance(msg, ToolMessage):
            name = getattr(msg, "name", "")
            content_str = str(msg.content)
            if name in ("get_weather", "get_temperature"):
                if content_str.lower().startswith("error"):
                    self.console.print(f"  [red]✗ {name} failed: {content_str}[/]")
                else:
                    self.console.print(f"  [green]✓ {content_str}[/]")
            elif name:
                self.console.print(f"  [green]✓ {name} complete[/]")
