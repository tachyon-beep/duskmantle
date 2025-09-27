from __future__ import annotations

from opentelemetry.sdk.trace import TracerProvider

from gateway.api.app import create_app
from gateway.config.settings import get_settings
from gateway.observability.tracing import reset_tracing_for_tests


def test_tracing_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("KM_TRACING_ENABLED", raising=False)
    monkeypatch.delenv("KM_TRACING_CONSOLE_EXPORT", raising=False)
    get_settings.cache_clear()
    reset_tracing_for_tests()

    app = create_app()

    assert not hasattr(app.state, "tracing_enabled")

    # clean up for downstream tests
    reset_tracing_for_tests()


def test_tracing_enabled_instruments_app(monkeypatch) -> None:
    monkeypatch.setenv("KM_TRACING_ENABLED", "true")
    monkeypatch.setenv("KM_TRACING_CONSOLE_EXPORT", "true")
    get_settings.cache_clear()
    reset_tracing_for_tests()

    instrument_calls: dict[str, int] = {"count": 0}

    def fake_instrument_app(self, app, tracer_provider=None):  # type: ignore[override]
        instrument_calls["count"] += 1

    from gateway.observability import tracing

    monkeypatch.setattr(
        tracing.FastAPIInstrumentor,
        "instrument_app",
        fake_instrument_app,
        raising=True,
    )

    app = create_app()

    assert instrument_calls["count"] == 1
    assert getattr(app.state, "tracing_enabled", False) is True
    assert isinstance(tracing.trace.get_tracer_provider(), TracerProvider)

    # cleanup for subsequent tests
    monkeypatch.delenv("KM_TRACING_ENABLED", raising=False)
    monkeypatch.delenv("KM_TRACING_CONSOLE_EXPORT", raising=False)
    get_settings.cache_clear()
    reset_tracing_for_tests()
