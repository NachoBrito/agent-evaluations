import os

from deepagents import create_deep_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from .weather_client import OpenMeteoClient, WeatherClient

DEFAULT_LLM_BASE_URL = "http://localhost:8080/v1"
DEFAULT_LLM_MODEL = "local-model"


def create_weather_tools(client: WeatherClient):
    """Build LangChain weather tools backed by the given WeatherClient."""

    @tool
    def get_weather(city: str) -> str:
        """Get the current weather conditions for a city."""
        try:
            conditions = client.get_weather(city)
        except (ValueError, RuntimeError) as exc:
            return f"Error: {exc}"

        details = []
        if conditions.humidity_percent is not None:
            details.append(f"humidity {conditions.humidity_percent}%")
        if conditions.wind_speed_kmh is not None:
            details.append(f"wind {conditions.wind_speed_kmh} km/h")

        suffix = f" ({', '.join(details)})" if details else ""
        return f"The weather in {conditions.location} is {conditions.description.lower()}{suffix}."

    @tool
    def get_temperature(city: str, unit: str = "celsius") -> str:
        """Get the temperature for a city in celsius or fahrenheit."""
        try:
            reading = client.get_temperature(city, unit=unit)
        except (ValueError, RuntimeError) as exc:
            return f"Error: {exc}"

        symbol = "°F" if reading.unit == "fahrenheit" else "°C"
        feels_like = (
            f" (feels like {reading.feels_like}{symbol})"
            if reading.feels_like is not None
            else ""
        )
        return f"The temperature in {reading.location} is {reading.temperature}{symbol}{feels_like}."

    return [get_weather, get_temperature]


def create_weather_agent(
    weather_client: WeatherClient | None = None,
    base_url: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
):
    """Create a weather agent configured by filesystem files."""
    client = weather_client or OpenMeteoClient()
    resolved_base_url = base_url or os.environ.get("LLM_BASE_URL") or DEFAULT_LLM_BASE_URL
    resolved_model = model or os.environ.get("LLM_MODEL") or DEFAULT_LLM_MODEL
    resolved_api_key = api_key or os.environ.get("LLM_API_KEY") or "not_needed"

    local_llm = ChatOpenAI(
        base_url=resolved_base_url,
        model=resolved_model,
        api_key=lambda: resolved_api_key,
        temperature=0,
        use_responses_api=False,  # Required: llama.cpp uses Chat Completions, not Responses API
    )
    return create_deep_agent(
        model=local_llm,
        memory=["./AGENTS.md"],           # Loaded by MemoryMiddleware
        skills=["./skills/"],             # Loaded by SkillsMiddleware
        tools=create_weather_tools(client),
        system_prompt=(
            "You are a helpful weather assistant. "
            "Use your tools to look up conditions and temperatures before answering."
        ),
    )
        
