#!/usr/bin/env python
"""Convenience wrapper to run a full ingest with BGE-M3 + CLIP embeddings."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_TEXT_MODEL = "BAAI/bge-m3"
DEFAULT_IMAGE_MODEL = "sentence-transformers/clip-ViT-L-14"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run gateway ingest with BGE-M3 + CLIP embeddings")
    parser.add_argument("--profile", default="staging", help="Ingest profile to run (default: staging)")
    parser.add_argument(
        "--repo",
        default=Path.cwd(),
        type=Path,
        help="Repository root to index (default: current working directory)",
    )
    parser.add_argument(
        "--state-path",
        default=Path.cwd() / ".state" / "gateway",
        type=Path,
        help="Writable state directory for reports/ledgers (default: .state/gateway)",
    )
    parser.add_argument(
        "--text-model",
        default=os.environ.get("KM_TEXT_EMBEDDING_MODEL", DEFAULT_TEXT_MODEL),
        help="Override text embedding model (default: BAAI/bge-m3)",
    )
    parser.add_argument(
        "--image-model",
        default=os.environ.get("KM_IMAGE_EMBEDDING_MODEL", DEFAULT_IMAGE_MODEL),
        help="Override image embedding model (default: sentence-transformers/clip-ViT-L-14)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run discovery/chunking only (no writes to Qdrant/Neo4j)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    repo_root = args.repo.resolve()
    state_path = args.state_path.resolve()
    state_path.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.update(
        {
            "KM_AUTH_ENABLED": env.get("KM_AUTH_ENABLED", "false"),
            "KM_SYMBOLS_ENABLED": env.get("KM_SYMBOLS_ENABLED", "true"),
            "KM_REPO_PATH": str(repo_root),
            "KM_STATE_PATH": str(state_path),
            "KM_TEXT_EMBEDDING_MODEL": args.text_model,
            "KM_IMAGE_EMBEDDING_MODEL": args.image_model,
            "KM_EMBEDDING_MODEL": args.text_model,
            # Force BGE to stay single-process
            "FLAG_EMBEDDING_USE_MULTI_PROCESS": "0",
            "FLAG_EMBEDDING_USE_FP16": "1" if env.get("CUDA_VISIBLE_DEVICES") else env.get("FLAG_EMBEDDING_USE_FP16", "0"),
        }
    )

    cmd = [
        sys.executable,
        "-m",
        "gateway.ingest.cli",
        "rebuild",
        "--profile",
        args.profile,
    ]
    if args.dry_run:
        cmd.append("--dry-run")
    cmd.extend(["--repo", str(repo_root)])

    print(f"Running ingest: {' '.join(cmd)}")
    print(f"Using text model: {args.text_model}")
    print(f"Using image model: {args.image_model}")
    print(f"State path: {state_path}")

    completed = subprocess.run(cmd, env=env, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
