from __future__ import annotations

from pathlib import Path

import pytest

from gateway.search import cli


@pytest.fixture(autouse=True)
def clear_settings_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path))
    from gateway.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_show_weights_command(capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["show-weights"])
    stdout = capsys.readouterr().out
    assert "Active profile" in stdout
    assert "Subsystem Criticality" in stdout
