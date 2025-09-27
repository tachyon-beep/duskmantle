"""Command-line entry point for the MCP server."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence

from gateway import get_version

from .config import MCPSettings
from .server import build_server

_TRANSPORT_CHOICES = ["stdio", "http", "sse", "streamable-http"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Duskmantle MCP server")
    parser.add_argument(
        "--transport",
        choices=_TRANSPORT_CHOICES,
        help="Transport to use (defaults to KM_MCP_TRANSPORT or stdio)",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Host to bind when using HTTP-based transports",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind when using HTTP-based transports",
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Disable startup banner",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version information and exit",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s | %(name)s | %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    settings = MCPSettings()

    if args.version:
        print(f"Duskmantle MCP server {get_version()}")
        return 0

    transport = args.transport or settings.transport
    if transport not in _TRANSPORT_CHOICES:
        parser.error(f"Unsupported transport: {transport}")

    server = build_server(settings=settings)

    transport_kwargs: dict[str, object] = {}
    if transport in {"http", "sse", "streamable-http"}:
        transport_kwargs["host"] = args.host or "127.0.0.1"
        transport_kwargs["port"] = args.port or 8787

    try:
        server.run(
            transport=transport,
            show_banner=not args.no_banner,
            **transport_kwargs,
        )
    except KeyboardInterrupt:  # pragma: no cover - manual interruption
        return 0

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
