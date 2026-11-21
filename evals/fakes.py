"""Deterministic fake WeatherClient for repeatable agentic flow evaluations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent_evaluation.weather_client import TemperatureReading, WeatherConditions


@dataclass(frozen=True)
class CityWeatherFixture:
    location: str
    description: str
    temperature_c: float
    feels_like_c: float
    humidity_percent: int
    wind_speed_kmh: float

    @property
    def temperature_f(self) -> float:
        return round(self.temperature_c * 9 / 5 + 32, 1)

    @property
    def feels_like_f(self) -> float:
        return round(self.feels_like_c * 9 / 5 + 32, 1)


DEFAULT_CITY_FIXTURES: dict[str, CityWeatherFixture] = {
    "madrid": CityWeatherFixture(
        location="Madrid, Spain",
        description="Clear sky",
        temperature_c=14.0,
        feels_like_c=13.0,
        humidity_percent=45,
        wind_speed_kmh=10.5,
    ),
    "tokyo": CityWeatherFixture(
        location="Tokyo, Japan",
        description="Partly cloudy",
        temperature_c=20.0,
        feels_like_c=19.5,
        humidity_percent=60,
        wind_speed_kmh=14.0,
    ),
    "london": CityWeatherFixture(
        location="London, United Kingdom",
        description="Moderate rain",
        temperature_c=11.0,
        feels_like_c=9.5,
        humidity_percent=85,
        wind_speed_kmh=22.0,
    ),
    "berlin": CityWeatherFixture(
        location="Berlin, Germany",
        description="Overcast",
        temperature_c=8.0,
        feels_like_c=6.0,
        humidity_percent=72,
        wind_speed_kmh=16.5,
    ),
    "paris": CityWeatherFixture(
        location="Paris, France",
        description="Mainly clear",
        temperature_c=16.0,
        feels_like_c=15.5,
        humidity_percent=52,
        wind_speed_kmh=11.0,
    ),
}


@dataclass
class FakeWeatherClient:
    """Deterministic WeatherClient implementation with optional fault injection."""

    fixtures: dict[str, CityWeatherFixture] = field(
        default_factory=lambda: dict(DEFAULT_CITY_FIXTURES)
    )
    fail_mode: str | None = None
    call_log: list[dict[str, Any]] = field(default_factory=list)

    def _resolve_city(self, city: str) -> CityWeatherFixture:
        if self.fail_mode == "service_outage":
            raise RuntimeError("Failed to reach weather service: simulated outage.")

        query = city.strip()
        if not query:
            raise ValueError("City name cannot be empty.")

        normalized = query.lower()
        # Accept either "Madrid" or "Madrid, Spain"
        for key, fixture in self.fixtures.items():
            if normalized == key or normalized == fixture.location.lower():
                return fixture

        raise ValueError(f"Could not find a location matching '{city}'.")

    def get_weather(self, city: str) -> WeatherConditions:
        self.call_log.append({"tool": "get_weather", "city": city})
        fixture = self._resolve_city(city)
        return WeatherConditions(
            location=fixture.location,
            description=fixture.description,
            humidity_percent=fixture.humidity_percent,
            wind_speed_kmh=fixture.wind_speed_kmh,
        )

    def get_temperature(self, city: str, unit: str = "celsius") -> TemperatureReading:
        self.call_log.append({"tool": "get_temperature", "city": city, "unit": unit})
        normalized_unit = unit.strip().lower()
        if normalized_unit not in ("celsius", "fahrenheit"):
            raise ValueError(
                f"Unsupported temperature unit '{unit}'. Use 'celsius' or 'fahrenheit'."
            )

        fixture = self._resolve_city(city)
        if normalized_unit == "fahrenheit":
            temp = fixture.temperature_f
            feels = fixture.feels_like_f
        else:
            temp = fixture.temperature_c
            feels = fixture.feels_like_c

        return TemperatureReading(
            location=fixture.location,
            temperature=temp,
            feels_like=feels,
            unit=normalized_unit,
        )
