from __future__ import annotations

import json
from pathlib import Path

import pytest

from gateway.lifecycle.cli import main as lifecycle_main


def test_lifecycle_cli_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report_path = tmp_path / "lifecycle_report.json"
    payload = {
        "generated_at_iso": "2025-09-28T00:00:00+00:00",
        "isolated": {"DesignDoc": [{"id": "DesignDoc:docs/orphan.md"}]},
        "stale_docs": [],
        "missing_tests": [],
    }
    report_path.write_text(json.dumps(payload), encoding="utf-8")

    lifecycle_main(["--json", "--report-path", str(report_path)])
    captured = capsys.readouterr()
    assert "DesignDoc:docs/orphan.md" in captured.out


def test_lifecycle_cli_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report_path = tmp_path / "missing.json"
    with pytest.raises(SystemExit):
        lifecycle_main(["--report-path", str(report_path)])
    captured = capsys.readouterr()
    assert "Lifecycle report not found" in captured.out
