from __future__ import annotations

from datetime import UTC, datetime, timedelta

from gateway.search.filtering import build_filter_state, parse_iso_datetime, payload_passes_filters


def test_build_filter_state_normalises_filters() -> None:
    base_time = datetime(2024, 1, 10, tzinfo=UTC)
    filters = {
        "subsystems": ["Telemetry", " telemetry "],
        "artifact_types": ["Code", "DOC"],
        "namespaces": [" src ", "docs"],
        "tags": ["Ops", "ops"],
        "symbols": ["Example.method", " example.method "],
        "symbol_kinds": ["Method"],
        "symbol_languages": ["Python"],
        "updated_after": base_time.isoformat(),
        "max_age_days": 7,
    }

    state = build_filter_state(filters)

    assert state.allowed_subsystems == {"telemetry"}
    assert state.allowed_types == {"code", "doc"}
    assert state.allowed_namespaces == {"src", "docs"}
    assert state.allowed_tags == {"ops"}
    assert state.allowed_symbol_names == {"example.method"}
    assert state.allowed_symbol_kinds == {"method"}
    assert state.allowed_symbol_languages == {"python"}
    assert "updated_after" in state.filters_applied
    assert "max_age_days" in state.filters_applied
    assert state.filters_applied["symbols"] == ["Example.method"]
    assert state.filters_applied["symbol_kinds"] == ["method"]
    assert state.filters_applied["symbol_languages"] == ["python"]
    assert state.recency_cutoff is not None
    assert state.recency_cutoff >= base_time - timedelta(days=7)


def test_payload_passes_filters_checks_all_fields() -> None:
    state = build_filter_state(
        {
            "artifact_types": ["code"],
            "namespaces": ["src"],
            "tags": ["ops"],
        }
    )

    payload = {
        "artifact_type": "code",
        "namespace": "SRC",
        "tags": ["Ops", "Other"],
    }

    assert payload_passes_filters(payload, state) is True
    assert payload_passes_filters({**payload, "artifact_type": "doc"}, state) is False
    assert payload_passes_filters({**payload, "namespace": "docs"}, state) is False
    assert payload_passes_filters({**payload, "tags": ["misc"]}, state) is False


def test_parse_iso_datetime_handles_multiple_formats() -> None:
    ts_numeric = parse_iso_datetime(1700000000)
    ts_string = parse_iso_datetime("2024-01-01T12:34:56Z")
    ts_invalid = parse_iso_datetime("not-a-date")

    assert ts_numeric is not None and ts_numeric.tzinfo is not None
    assert ts_string is not None and ts_string.tzinfo is not None
    assert ts_invalid is None

def test_payload_symbol_filters() -> None:
    state = build_filter_state(
        {
            "symbols": ["Demo.call"],
            "symbol_kinds": ["method"],
            "symbol_languages": ["python"],
        }
    )

    payload = {
        "symbol_names": ["Demo.call"],
        "symbol_kinds": ["method"],
        "symbol_languages": ["python"],
    }

    assert payload_passes_filters(payload, state) is True
    assert payload_passes_filters({**payload, "symbol_names": ["Other"]}, state) is False
    assert payload_passes_filters({**payload, "symbol_kinds": ["class"]}, state) is False
    assert payload_passes_filters({**payload, "symbol_languages": ["typescript"]}, state) is False
