import json
from dataclasses import dataclass
from typing import Protocol
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen


WMO_WEATHER_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


@dataclass(frozen=True)
class WeatherConditions:
    location: str
    description: str
    humidity_percent: int | float | None = None
    wind_speed_kmh: float | None = None


@dataclass(frozen=True)
class TemperatureReading:
    location: str
    temperature: float
    feels_like: float | None
    unit: str


class WeatherClient(Protocol):
    """Interface for weather data providers."""

    def get_weather(self, city: str) -> WeatherConditions: ...

    def get_temperature(self, city: str, unit: str = "celsius") -> TemperatureReading: ...


class OpenMeteoClient:
    """WeatherClient implementation backed by the free Open-Meteo API."""

    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def _get_json(self, base_url: str, params: dict[str, object]) -> dict:
        url = f"{base_url}?{urlencode(params)}"
        try:
            with urlopen(url, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except URLError as exc:
            raise RuntimeError(f"Failed to reach Open-Meteo API: {exc}") from exc

    def _geocode(self, city: str) -> tuple[str, float, float]:
        query = city.strip()
        if not query:
            raise ValueError("City name cannot be empty.")

        data = self._get_json(
            self.GEOCODING_URL,
            {"name": query, "count": 1, "language": "en", "format": "json"},
        )
        results = data.get("results")
        if not results:
            raise ValueError(f"Could not find a location matching '{city}'.")

        match = results[0]
        name = match["name"]
        country = match.get("country")
        location = f"{name}, {country}" if country else name
        return location, float(match["latitude"]), float(match["longitude"])

    def _fetch_current(self, latitude: float, longitude: float, unit: str = "celsius") -> dict:
        normalized_unit = unit.strip().lower()
        if normalized_unit not in ("celsius", "fahrenheit"):
            raise ValueError(f"Unsupported temperature unit '{unit}'. Use 'celsius' or 'fahrenheit'.")

        data = self._get_json(
            self.FORECAST_URL,
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code",
                "temperature_unit": normalized_unit,
            },
        )
        current = data.get("current")
        if not current:
            raise RuntimeError("Open-Meteo API returned no current weather data.")
        return current

    def get_weather(self, city: str) -> WeatherConditions:
        location, lat, lon = self._geocode(city)
        current = self._fetch_current(lat, lon)
        code = int(current.get("weather_code", -1))
        description = WMO_WEATHER_CODES.get(code, f"Weather code {code}")
        return WeatherConditions(
            location=location,
            description=description,
            humidity_percent=current.get("relative_humidity_2m"),
            wind_speed_kmh=current.get("wind_speed_10m"),
        )

    def get_temperature(self, city: str, unit: str = "celsius") -> TemperatureReading:
        normalized_unit = unit.strip().lower()
        location, lat, lon = self._geocode(city)
        current = self._fetch_current(lat, lon, unit=normalized_unit)
        return TemperatureReading(
            location=location,
            temperature=float(current["temperature_2m"]),
            feels_like=(
                float(current["apparent_temperature"])
                if current.get("apparent_temperature") is not None
                else None
            ),
            unit=normalized_unit,
        )
