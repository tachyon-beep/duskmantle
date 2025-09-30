from __future__ import annotations

import pytest

from gateway.config.settings import SEARCH_WEIGHT_PROFILES, AppSettings


@pytest.fixture(autouse=True)
def clear_weight_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KM_SEARCH_WEIGHT_PROFILE", raising=False)
    monkeypatch.delenv("KM_SEARCH_W_SUBSYSTEM", raising=False)
    monkeypatch.delenv("KM_SEARCH_W_RELATIONSHIP", raising=False)
    monkeypatch.delenv("KM_SEARCH_W_SUPPORT", raising=False)
    monkeypatch.delenv("KM_SEARCH_W_COVERAGE_PENALTY", raising=False)


def test_resolved_search_weights_default() -> None:
    settings = AppSettings()
    profile, weights = settings.resolved_search_weights()

    assert profile == "default"
    assert weights == SEARCH_WEIGHT_PROFILES["default"]


def test_resolved_search_weights_profile_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_SEARCH_WEIGHT_PROFILE", "analysis")
    settings = AppSettings()

    profile, weights = settings.resolved_search_weights()
    assert profile == "analysis"
    assert weights == SEARCH_WEIGHT_PROFILES["analysis"]


def test_resolved_search_weights_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KM_SEARCH_WEIGHT_PROFILE", "docs-heavy")
    monkeypatch.setenv("KM_SEARCH_W_SUPPORT", "0.25")
    settings = AppSettings()

    profile, weights = settings.resolved_search_weights()

    assert profile == "docs-heavy+overrides"
    assert weights["weight_support"] == pytest.approx(0.25)
    # Non-overridden weights fall back to the profile defaults
    assert weights["weight_subsystem"] == pytest.approx(SEARCH_WEIGHT_PROFILES["docs-heavy"]["weight_subsystem"])
