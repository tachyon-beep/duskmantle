from __future__ import annotations

import runpy
import sys
from pathlib import Path

from prometheus_client import REGISTRY

module = runpy.run_path("bin/km-watch", run_name="km_watch")


def _metric_value(name: str, labels: dict[str, str]) -> float:
    value = REGISTRY.get_sample_value(name, labels)
    return float(value) if value is not None else 0.0


compute_fingerprints = module["compute_fingerprints"]
diff_fingerprints = module["diff_fingerprints"]


def test_compute_fingerprints(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "dir").mkdir()
    (tmp_path / "dir" / "b.txt").write_text("world")
    fp = compute_fingerprints(tmp_path)
    assert set(fp.keys()) == {"a.txt", "dir/b.txt"}
    assert all(len(v) == 64 for v in fp.values())


def test_diff_fingerprints_detects_changes() -> None:
    old = {"file": "hash1"}
    new_same = {"file": "hash1"}
    new_changed = {"file": "hash2"}
    new_added = {"file": "hash1", "extra": "hash3"}

    assert diff_fingerprints(old, new_same) is False
    assert diff_fingerprints(old, new_changed) is True
    assert diff_fingerprints(old, new_added) is True


def test_watch_metrics_increment(tmp_path: Path):
    main = module["main"]

    root_success = tmp_path / "success"
    root_success.mkdir(parents=True)
    (root_success / "file.txt").write_text("content")
    fingerprint_success = tmp_path / "fingerprints-success.json"
    before_success = _metric_value("km_watch_runs_total", {"result": "success"})
    exit_code = main(
        [
            "--root",
            str(root_success),
            "--fingerprints",
            str(fingerprint_success),
            "--command",
            f"{sys.executable} -c 'import sys'",
            "--once",
        ]
    )
    assert exit_code == 0
    after_success = _metric_value("km_watch_runs_total", {"result": "success"})
    assert after_success == before_success + 1

    root_failure = tmp_path / "failure"
    root_failure.mkdir(parents=True)
    (root_failure / "file.txt").write_text("content")
    fingerprint_failure = tmp_path / "fingerprints-failure.json"
    before_error = _metric_value("km_watch_runs_total", {"result": "error"})
    exit_code = main(
        [
            "--root",
            str(root_failure),
            "--fingerprints",
            str(fingerprint_failure),
            "--command",
            f"{sys.executable} -c 'import sys; sys.exit(1)'",
            "--once",
        ]
    )
    assert exit_code == 0
    after_error = _metric_value("km_watch_runs_total", {"result": "error"})
    assert after_error == before_error + 1

    root_no_change = tmp_path / "no-change"
    root_no_change.mkdir(parents=True)
    fingerprint_no_change = tmp_path / "fingerprints-nochange.json"
    before_no_change = _metric_value("km_watch_runs_total", {"result": "no_change"})
    exit_code = main(
        [
            "--root",
            str(root_no_change),
            "--fingerprints",
            str(fingerprint_no_change),
            "--command",
            f"{sys.executable} -c 'import sys'",
            "--once",
        ]
    )
    assert exit_code == 0
    after_no_change = _metric_value("km_watch_runs_total", {"result": "no_change"})
    assert after_no_change == before_no_change + 1
