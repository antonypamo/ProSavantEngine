"""Entry points for running the Prosavant Engine in different modes."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
from typing import Iterable

from .config import DEFAULT_SERVER_URI, DEFAULT_USER
from .core import AGIRRFCore
from .networking import listen_to_field, send_to_field, start_server

DEFAULT_ACTIVATION_MESSAGE = "AGI–RRF Φ9.0-Δ field activation"


def launch(
    mode: str | None = None,
    *,
    server_uri: str = DEFAULT_SERVER_URI,
    user: str = DEFAULT_USER,
    host: str = "0.0.0.0",
    port: int = 8765,
    activation_message: str = DEFAULT_ACTIVATION_MESSAGE,
) -> None:
    """Launch the engine in the requested *mode*."""

    resolved_mode = _resolve_mode(mode)
    if resolved_mode == "server":
        try:
            asyncio.run(start_server(host=host, port=port))
        except KeyboardInterrupt:
            pass
    elif resolved_mode == "client":
        try:
            asyncio.run(
                _client_mode(
                    server_uri=server_uri,
                    user=user,
                    activation_message=activation_message,
                )
            )
        except KeyboardInterrupt:
            pass
    else:
        _run_cli()


def _resolve_mode(mode: str | None) -> str:
    value = mode or input("Mode [core/server/client]: ").strip().lower()
    if value not in {"core", "server", "client"}:
        return "core"
    return value


def _run_cli() -> None:
    core = AGIRRFCore()
    while True:
        try:
            query = input("🔹 Input: ")
        except EOFError:
            break
        if query.lower() in {"exit", "quit"}:
            break
        if not query:
            continue
        response = core.query(query)
        summary = core.omega_summary()
        payload = dict(response)
        if summary:
            payload["omega_summary"] = summary
        print(json.dumps(payload, indent=2))


async def _client_mode(
    *,
    server_uri: str,
    user: str,
    activation_message: str,
) -> None:
    listener_task = asyncio.create_task(listen_to_field(server_uri))
    try:
        await asyncio.sleep(1)
        await send_to_field(activation_message, user, server_uri)
        await listener_task
    finally:
        listener_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await listener_task


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the Prosavant Engine")
    parser.add_argument("--mode", choices=["core", "server", "client"], help="Execution mode")
    parser.add_argument("--server-uri", default=DEFAULT_SERVER_URI, help="WebSocket server URI")
    parser.add_argument("--user", default=DEFAULT_USER, help="Username for AGORA field publication")
    parser.add_argument("--host", default="0.0.0.0", help="Host for server mode")
    parser.add_argument("--port", type=int, default=8765, help="Port for server mode")
    parser.add_argument(
        "--activation-message",
        default=DEFAULT_ACTIVATION_MESSAGE,
        help="Activation message sent in client mode",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    launch(
        mode=args.mode,
        server_uri=args.server_uri,
        user=args.user,
        host=args.host,
        port=args.port,
        activation_message=args.activation_message,
    )


if __name__ == "__main__":
    main()
