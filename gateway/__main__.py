from __future__ import annotations

import uvicorn


def main() -> None:  # pragma: no cover - thin wrapper
    """Run the gateway API using Uvicorn."""
    uvicorn.run("gateway.api.app:create_app", factory=True, host="0.0.0.0", port=8000)


if __name__ == "__main__":  # pragma: no cover
    main()
