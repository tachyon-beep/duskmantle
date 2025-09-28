from __future__ import annotations

from pathlib import Path
import runpy


module = runpy.run_path("bin/km-watch", run_name="km_watch")
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
