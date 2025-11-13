"""Networking helpers for the AGORA distributed resonant field."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import time
from threading import Lock
from typing import List

import numpy as np
import plotly.graph_objects as go
import websockets
from websockets.server import WebSocketServerProtocol

from .config import VERSION


def _get_embedder():
    from .resonance import get_embedder

    return get_embedder()


UMAP_AVAILABLE = importlib.util.find_spec("umap") is not None
if UMAP_AVAILABLE:
    from umap import UMAP
else:  # pragma: no cover - fallback path when UMAP is absent
    UMAP = None  # type: ignore

_field_vectors: List[np.ndarray] = []
_field_texts: List[str] = []
_field_lock = Lock()
_visualization_warning_emitted = False


async def start_server(host: str = "0.0.0.0", port: int = 8765) -> None:
    """Launch the AGORA relay server and run until cancelled."""

    connected: set[WebSocketServerProtocol] = set()
    connection_lock = asyncio.Lock()

    async def relay_handler(ws: WebSocketServerProtocol) -> None:
        await _register_client(ws, connected, connection_lock)
        try:
            async for message in ws:
                await _broadcast(message, ws, connected, connection_lock)
        finally:
            await _unregister_client(ws, connected, connection_lock)

    async with websockets.serve(relay_handler, host, port):
        print(f"🌀 AGORA Relay Server running on {host}:{port}")
        await asyncio.Future()


async def _register_client(
    ws: WebSocketServerProtocol,
    connected: set[WebSocketServerProtocol],
    lock: asyncio.Lock,
) -> None:
    async with lock:
        connected.add(ws)


async def _unregister_client(
    ws: WebSocketServerProtocol,
    connected: set[WebSocketServerProtocol],
    lock: asyncio.Lock,
) -> None:
    async with lock:
        connected.discard(ws)


async def _broadcast(
    message: str,
    sender: WebSocketServerProtocol,
    connected: set[WebSocketServerProtocol],
    lock: asyncio.Lock,
) -> None:
    async with lock:
        peers = list(connected)
    coroutines = [peer.send(message) for peer in peers if peer is not sender]
    if coroutines:
        await asyncio.gather(*coroutines)


async def send_to_field(text: str, user: str, server_uri: str) -> None:
    """Encode *text* and publish it to the AGORA field."""

    vector = _get_embedder().encode(text).tolist()
    payload = {
        "user": user,
        "text": text,
        "vector": vector,
        "timestamp": time.time(),
    }
    async with websockets.connect(server_uri) as ws:
        await ws.send(json.dumps(payload))
        print(f"📡 Sent → AGORA: {text}")


async def listen_to_field(server_uri: str) -> None:
    """Listen for messages from the AGORA field and visualize updates."""

    async with websockets.connect(server_uri) as ws:
        async for message in ws:
            data = json.loads(message)
            _store_field_update(data["text"], np.array(data["vector"]))
            visualize_field()


def _store_field_update(text: str, vector: np.ndarray) -> None:
    with _field_lock:
        _field_texts.append(text)
        _field_vectors.append(vector)


def visualize_field() -> None:
    """Render the AGORA field if the environment supports it."""

    global _visualization_warning_emitted

    with _field_lock:
        if len(_field_vectors) < 3:
            return
        vectors = np.array(_field_vectors)
        labels = list(_field_texts)

    if not UMAP_AVAILABLE:
        if not _visualization_warning_emitted:
            print("⚠️ UMAP unavailable; skipping AGORA visualization.")
            _visualization_warning_emitted = True
        return

    if not _can_render():
        if not _visualization_warning_emitted:
            print("⚠️ Headless environment detected; visualization disabled.")
            _visualization_warning_emitted = True
        return

    reducer = UMAP(
        n_neighbors=min(5, len(vectors) - 1),
        n_components=3,
        random_state=42,
    )
    embedding = reducer.fit_transform(vectors)
    figure = go.Figure(
        data=[
            go.Scatter3d(
                x=embedding[:, 0],
                y=embedding[:, 1],
                z=embedding[:, 2],
                text=labels,
                mode="markers+text",
                marker=dict(
                    size=6,
                    color=np.arange(len(labels)),
                    colorscale="Viridis",
                ),
            )
        ]
    )
    figure.update_layout(title=f"AGORA Resonant Field {VERSION}")
    figure.show()


def _can_render() -> bool:
    if os.name == "nt":
        return True
    return bool(os.environ.get("DISPLAY"))


__all__ = [
    "start_server",
    "send_to_field",
    "listen_to_field",
    "visualize_field",
]
