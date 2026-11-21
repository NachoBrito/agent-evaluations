import os

from opentelemetry.sdk.trace import TracerProvider
from phoenix.otel import register


DEFAULT_PHOENIX_ENDPOINT = "http://localhost:6006/v1/traces"


def setup_telemetry(
    project_name: str = "weather-agent",
    endpoint: str | None = None,
) -> TracerProvider | None:
    """Configure OpenTelemetry tracing exported to a local Arize Phoenix instance.

    Set ``PHOENIX_ENABLED=false`` to disable tracing, or override the collector
    URL with ``PHOENIX_COLLECTOR_ENDPOINT``.
    """
    enabled = os.environ.get("PHOENIX_ENABLED", "true").strip().lower()
    if enabled in ("0", "false", "no", "off"):
        return None

    collector_endpoint = (
        endpoint
        or os.environ.get("PHOENIX_COLLECTOR_ENDPOINT")
        or DEFAULT_PHOENIX_ENDPOINT
    )

    return register(
        project_name=project_name,
        endpoint=collector_endpoint,
        auto_instrument=True,
        verbose=False,
    )
