import json
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class SeatWebSocketManager:
    """Manages WebSocket connections grouped by showtime_id."""

    def __init__(self):
        self._connections: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, showtime_id: int, ws: WebSocket):
        await ws.accept()
        self._connections[showtime_id].append(ws)

    def disconnect(self, showtime_id: int, ws: WebSocket):
        conns = self._connections.get(showtime_id, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, showtime_id: int, event: dict[str, Any]):
        dead = []
        for ws in list(self._connections.get(showtime_id, [])):
            try:
                await ws.send_text(json.dumps(event))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(showtime_id, ws)


seat_ws_manager = SeatWebSocketManager()
