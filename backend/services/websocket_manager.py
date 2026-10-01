from fastapi import WebSocket
from typing import Dict, List
import json


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = []
        self.active_connections[room].append(websocket)

    def disconnect(self, websocket: WebSocket, room: str):
        if room in self.active_connections:
            self.active_connections[room] = [
                ws for ws in self.active_connections[room] if ws != websocket
            ]

    async def broadcast(self, room: str, data: dict):
        if room not in self.active_connections:
            return
        dead = []
        for ws in self.active_connections[room]:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active_connections[room].remove(ws)

    async def broadcast_global(self, data: dict):
        await self.broadcast("global", data)


manager = ConnectionManager()
