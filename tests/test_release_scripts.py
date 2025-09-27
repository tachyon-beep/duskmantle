from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"


def _env_with_venv() -> dict[str, str]:
    env = os.environ.copy()
    venv_bin = REPO_ROOT / ".venv" / "bin"
    if venv_bin.exists():
        env["PATH"] = f"{venv_bin}:{env['PATH']}"
    return env


def test_build_wheel_script(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    subprocess.run(
        ["bash", str(SCRIPTS_DIR / "build-wheel.sh"), str(dist_dir)],
        check=True,
        cwd=REPO_ROOT,
        env=_env_with_venv(),
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert wheels, "Expected wheel artifacts in dist directory"


def test_checksums_script(tmp_path: Path) -> None:
    target_dir = tmp_path / "artifacts"
    target_dir.mkdir()
    (target_dir / "file_a.txt").write_text("alpha", encoding="utf-8")
    (target_dir / "file_b.txt").write_text("beta", encoding="utf-8")

    output_file = tmp_path / "SHA256SUMS"
    subprocess.run(
        ["bash", str(SCRIPTS_DIR / "checksums.sh"), str(target_dir), str(output_file)],
        check=True,
        cwd=REPO_ROOT,
        env=_env_with_venv(),
    )

    lines = output_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    for line in lines:
        digest, filename = line.split(maxsplit=1)
        assert len(digest) == 64
        assert filename.startswith(str(target_dir))

def test_generate_changelog(tmp_path: Path) -> None:
    repo_copy = tmp_path / "repo"
    subprocess.run(
        ["rsync", "-a", f"{REPO_ROOT}/", f"{repo_copy}/", "--exclude", ".git"],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    changelog = repo_copy / "CHANGELOG.md"

    subprocess.run(["git", "init"], cwd=repo_copy, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "ci@example.com"], cwd=repo_copy, check=True)
    subprocess.run(["git", "config", "user.name", "CI"], cwd=repo_copy, check=True)
    subprocess.run(["git", "add", "CHANGELOG.md", "scripts/generate-changelog.py"], cwd=repo_copy, check=True)
    subprocess.run(["git", "commit", "-m", "chore: seed changelog"], cwd=repo_copy, check=True, stdout=subprocess.DEVNULL)

    (repo_copy / "tmp.txt").write_text("alpha", encoding="utf-8")
    subprocess.run(["git", "add", "tmp.txt"], cwd=repo_copy, check=True)
    subprocess.run(["git", "commit", "-m", "feat: add alpha"], cwd=repo_copy, check=True, stdout=subprocess.DEVNULL)
    (repo_copy / "tmp.txt").write_text("beta", encoding="utf-8")
    subprocess.run(["git", "commit", "-am", "fix: correct alpha"], cwd=repo_copy, check=True, stdout=subprocess.DEVNULL)

    script = repo_copy / "scripts" / "generate-changelog.py"
    subprocess.run(
        [
            "python",
            str(script),
            "0.0.1",
            "--since",
            "HEAD~2",
            "--date",
            "2024-09-10",
        ],
        cwd=repo_copy,
        check=True,
        stdout=subprocess.DEVNULL,
    )

    updated = changelog.read_text(encoding="utf-8")
    assert "## 0.0.1 - 2024-09-10" in updated
    assert "### Added" in updated and "feat: add alpha" in updated
    assert "### Fixed" in updated and "fix: correct alpha" in updated
