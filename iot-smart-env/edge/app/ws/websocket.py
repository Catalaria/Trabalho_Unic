"""
Gerencia conexões WebSocket e expõe a rota /ws
"""

from __future__ import annotations
import threading
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

ws_router = APIRouter()


class WSManager:
    def __init__(self) -> None:
        self.connections: list[WebSocket] = []
        self.lock = threading.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        with self.lock:
            self.connections.append(ws)

    def remove(self, ws: WebSocket):
        with self.lock:
            if ws in self.connections:
                self.connections.remove(ws)

    async def broadcast_json(self, data: dict):
        to_remove = []
        for ws in list(self.connections):
            try:
                await ws.send_json(data)
            except Exception:
                to_remove.append(ws)
        for ws in to_remove:
            self.remove(ws)


ws_manager = WSManager()


@ws_router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Mantém socket vivo (cliente pode enviar "ping")
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.remove(websocket)
