"""Filter processing helpers for search queries."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from gateway.search.models import FilterState


def build_filter_state(filters: Mapping[str, Any] | None) -> FilterState:
    """Normalise raw filter payloads into a `FilterState`."""

    filters = dict(filters) if filters is not None else {}

    raw_subsystems = filters.get("subsystems") or []
    raw_types = filters.get("artifact_types") or []
    raw_namespaces = filters.get("namespaces") or []
    raw_tags = filters.get("tags") or []
    raw_symbols = filters.get("symbols") or []
    raw_symbol_kinds = filters.get("symbol_kinds") or []
    raw_symbol_languages = filters.get("symbol_languages") or []
    updated_after_filter = filters.get("updated_after")
    max_age_filter = filters.get("max_age_days")

    allowed_subsystems = {str(value).strip().lower() for value in raw_subsystems if isinstance(value, str)}
    allowed_types = {str(value).strip().lower() for value in raw_types if isinstance(value, str)}
    allowed_namespaces = {str(value).strip().lower() for value in raw_namespaces if isinstance(value, str)}
    allowed_tags = {str(value).strip().lower() for value in raw_tags if isinstance(value, str)}
    allowed_symbol_names = {str(value).strip().lower() for value in raw_symbols if isinstance(value, str)}
    allowed_symbol_kinds = {str(value).strip().lower() for value in raw_symbol_kinds if isinstance(value, str)}
    allowed_symbol_languages = {str(value).strip().lower() for value in raw_symbol_languages if isinstance(value, str)}

    parsed_updated_after: datetime | None = None
    if isinstance(updated_after_filter, datetime):
        parsed_updated_after = updated_after_filter.astimezone(UTC)
    elif isinstance(updated_after_filter, str):
        parsed_updated_after = parse_iso_datetime(updated_after_filter)

    recency_cutoff: datetime | None = parsed_updated_after
    recency_max_age_days: float | None = None
    if max_age_filter is not None:
        try:
            recency_max_age_days = float(max_age_filter)
        except (TypeError, ValueError):
            recency_max_age_days = None
    if recency_max_age_days is not None:
        now = datetime.now(UTC)
        age_cutoff = now - timedelta(days=recency_max_age_days)
        if recency_cutoff is None or age_cutoff > recency_cutoff:
            recency_cutoff = age_cutoff

    filters_applied: dict[str, Any] = {}
    if allowed_subsystems:
        filters_applied["subsystems"] = sorted(
            {str(value).strip() for value in raw_subsystems if isinstance(value, str) and value.strip()},
        )
    if allowed_types:
        filters_applied["artifact_types"] = sorted(
            {str(value).strip().lower() for value in raw_types if isinstance(value, str) and value.strip()},
        )
    if allowed_namespaces:
        filters_applied["namespaces"] = sorted(
            {str(value).strip() for value in raw_namespaces if isinstance(value, str) and value.strip()},
        )
    if allowed_tags:
        filters_applied["tags"] = sorted(
            {str(value).strip() for value in raw_tags if isinstance(value, str) and value.strip()},
        )
    if allowed_symbol_names:
        unique_symbols: list[str] = []
        seen_symbols: set[str] = set()
        for value in raw_symbols:
            if not isinstance(value, str):
                continue
            trimmed = value.strip()
            if not trimmed:
                continue
            key = trimmed.lower()
            if key in seen_symbols:
                continue
            seen_symbols.add(key)
            unique_symbols.append(trimmed)
        if unique_symbols:
            filters_applied["symbols"] = unique_symbols
    if allowed_symbol_kinds:
        filters_applied["symbol_kinds"] = sorted(
            {str(value).strip().lower() for value in raw_symbol_kinds if isinstance(value, str) and value.strip()},
        )
    if allowed_symbol_languages:
        filters_applied["symbol_languages"] = sorted(
            {str(value).strip().lower() for value in raw_symbol_languages if isinstance(value, str) and value.strip()},
        )
    if parsed_updated_after is not None:
        filters_applied["updated_after"] = parsed_updated_after.astimezone(UTC).isoformat()
    if max_age_filter is not None:
        try:
            filters_applied["max_age_days"] = int(max_age_filter)
        except (TypeError, ValueError):  # pragma: no cover - defensive conversion guard
            pass

    return FilterState(
        allowed_subsystems=allowed_subsystems,
        allowed_types=allowed_types,
        allowed_namespaces=allowed_namespaces,
        allowed_tags=allowed_tags,
        allowed_symbol_names=allowed_symbol_names,
        allowed_symbol_kinds=allowed_symbol_kinds,
        allowed_symbol_languages=allowed_symbol_languages,
        filters_applied=filters_applied,
        recency_cutoff=recency_cutoff,
    )


def payload_passes_filters(payload: Mapping[str, Any], state: FilterState) -> bool:
    """Return True when the payload matches the provided filter state."""

    artifact_type = str(payload.get("artifact_type") or "").lower()
    if state.allowed_types and artifact_type not in state.allowed_types:
        return False

    namespace_value = str(payload.get("namespace") or "").strip().lower()
    if state.allowed_namespaces and namespace_value not in state.allowed_namespaces:
        return False

    if state.allowed_tags:
        payload_tags = _normalise_payload_tags(payload.get("tags"))
        if not payload_tags.intersection(state.allowed_tags):
            return False

    if state.allowed_symbol_names:
        payload_symbol_names = _payload_symbol_names(payload)
        if not payload_symbol_names.intersection(state.allowed_symbol_names):
            return False

    if state.allowed_symbol_kinds:
        payload_symbol_kinds = _payload_symbol_kinds(payload)
        if not payload_symbol_kinds.intersection(state.allowed_symbol_kinds):
            return False

    if state.allowed_symbol_languages:
        payload_symbol_languages = _payload_symbol_languages(payload)
        if not payload_symbol_languages.intersection(state.allowed_symbol_languages):
            return False

    return True


def parse_iso_datetime(value: object) -> datetime | None:
    """Parse integers, floats, or ISO-8601 strings into timezone-aware datetimes."""

    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=UTC)
        except (OverflowError, ValueError):
            return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _normalise_payload_tags(raw_tags: Sequence[object] | set[object] | None) -> set[str]:
    if isinstance(raw_tags, (list, tuple, set)):
        return {str(tag).strip().lower() for tag in raw_tags if str(tag).strip()}
    return set()


def _payload_symbol_names(payload: Mapping[str, Any]) -> set[str]:
    names = _normalise_string_iterable(payload.get("symbol_names"))
    if names:
        return names
    symbols = payload.get("symbols")
    if isinstance(symbols, (list, tuple)):
        extracted: set[str] = set()
        for entry in symbols:
            if isinstance(entry, Mapping):
                text = str(entry.get("qualified_name") or entry.get("name") or "").strip()
                if text:
                    extracted.add(text.lower())
        return extracted
    return set()


def _payload_symbol_kinds(payload: Mapping[str, Any]) -> set[str]:
    kinds = _normalise_string_iterable(payload.get("symbol_kinds"))
    if kinds:
        return kinds
    symbols = payload.get("symbols")
    if isinstance(symbols, (list, tuple)):
        extracted: set[str] = set()
        for entry in symbols:
            if isinstance(entry, Mapping):
                text = str(entry.get("kind") or "").strip()
                if text:
                    extracted.add(text.lower())
        return extracted
    return set()


def _payload_symbol_languages(payload: Mapping[str, Any]) -> set[str]:
    languages = _normalise_string_iterable(payload.get("symbol_languages"))
    if languages:
        return languages
    symbols = payload.get("symbols")
    if isinstance(symbols, (list, tuple)):
        extracted: set[str] = set()
        for entry in symbols:
            if isinstance(entry, Mapping):
                text = str(entry.get("language") or "").strip()
                if text:
                    extracted.add(text.lower())
        return extracted
    return set()


def _normalise_string_iterable(values: Any) -> set[str]:
    if isinstance(values, (list, tuple, set)):
        return {str(value).strip().lower() for value in values if isinstance(value, str) and value.strip()}
    return set()


__all__ = ["build_filter_state", "payload_passes_filters", "parse_iso_datetime"]
