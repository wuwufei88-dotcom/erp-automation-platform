from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, project_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(project_id, []).append(ws)

    def disconnect(self, project_id: str, ws: WebSocket) -> None:
        if project_id in self._connections:
            self._connections[project_id] = [c for c in self._connections[project_id] if c != ws]

    async def broadcast(self, project_id: str, event: dict) -> None:
        if project_id not in self._connections:
            return
        dead: list[WebSocket] = []
        message = json.dumps(event)
        for ws in self._connections[project_id]:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(project_id, ws)


manager = ConnectionManager()


@router.websocket("/projects/{project_id}")
async def project_ws(ws: WebSocket, project_id: str) -> None:
    await manager.connect(project_id, ws)
    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "subscribe":
                await ws.send_text(json.dumps({"type": "subscribed", "project_id": project_id}))
    except WebSocketDisconnect:
        manager.disconnect(project_id, ws)


def notify_agent_state(project_id: str, agent_type: str, status: str, message: str = "") -> None:
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        return
    if loop.is_running():
        loop.create_task(
            manager.broadcast(
                project_id,
                {"type": "agent_state", "agent_type": agent_type, "status": status, "message": message},
            )
        )
