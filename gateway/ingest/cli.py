from __future__ import annotations

import argparse
import logging

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Create an argument parser for the ingestion CLI."""
    parser = argparse.ArgumentParser(description="Knowledge gateway ingestion commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    rebuild_parser = subparsers.add_parser("rebuild", help="Trigger a full ingestion run")
    rebuild_parser.add_argument(
        "--profile",
        default="local",
        help="Ingestion profile to run (e.g., local, dev, prod)",
    )

    return parser


def rebuild(*, profile: str = "local") -> None:
    """Placeholder implementation for the rebuild command."""
    logger.warning("Ingestion rebuild invoked for profile=%s (stub)", profile)


def main(argv: list[str] | None = None) -> None:
    """Entry point for the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "rebuild":
        rebuild(profile=args.profile)
    else:  # pragma: no cover - safety fallback
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    main()
