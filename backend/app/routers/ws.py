"""WebSocket endpoint for real-time seat map updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket_manager import seat_ws_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/seats/{showtime_id}")
async def seat_updates(showtime_id: int, ws: WebSocket):
    await seat_ws_manager.connect(showtime_id, ws)
    try:
        while True:
            # Keep alive; client can send pings
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        seat_ws_manager.disconnect(showtime_id, ws)
