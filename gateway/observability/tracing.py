from __future__ import annotations

from typing import Mapping

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

from gateway.config.settings import AppSettings

_TRACING_CONFIGURED = False


def configure_tracing(app: FastAPI | None, settings: AppSettings) -> None:
    """Configure OpenTelemetry tracing based on runtime settings."""

    global _TRACING_CONFIGURED

    if _TRACING_CONFIGURED or not settings.tracing_enabled:
        return

    resource = Resource.create({"service.name": settings.tracing_service_name})
    sampler = ParentBased(TraceIdRatioBased(settings.tracing_sample_ratio))
    provider = TracerProvider(resource=resource, sampler=sampler)

    exporter = _select_exporter(settings)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    # Optionally mirror spans to stdout in addition to OTLP export.
    if settings.tracing_console_export and settings.tracing_endpoint:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)

    # Client libraries used throughout the gateway leverage requests; instrument once.
    RequestsInstrumentor().instrument()
    if app is not None:
        FastAPIInstrumentor().instrument_app(app, tracer_provider=provider)
        app.state.tracing_enabled = True
    _TRACING_CONFIGURED = True


def _select_exporter(settings: AppSettings):
    headers = _parse_headers(settings.tracing_headers)
    if settings.tracing_endpoint:
        return OTLPSpanExporter(endpoint=settings.tracing_endpoint, headers=headers)
    if settings.tracing_console_export:
        return ConsoleSpanExporter()
    # Default to OTLP environment variables if provided externally; otherwise console.
    return ConsoleSpanExporter()


def _parse_headers(header_string: str | None) -> Mapping[str, str] | None:
    if not header_string:
        return None

    header_pairs: dict[str, str] = {}
    for item in header_string.split(","):
        if not item or "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            continue
        header_pairs[key] = value.strip()
    return header_pairs or None


def reset_tracing_for_tests() -> None:
    """Reset module-level state so tests can reconfigure tracing cleanly."""

    global _TRACING_CONFIGURED
    _TRACING_CONFIGURED = False
    RequestsInstrumentor().uninstrument()
    trace.set_tracer_provider(TracerProvider())
