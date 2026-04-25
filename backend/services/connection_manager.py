import asyncio
import json
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Fan-out WebSocket broadcaster.

    Two channels:
      - stream_subscribers[camera_id] -> list of sockets watching one camera's frames
      - event_subscribers -> list of sockets watching the global event feed
    """

    def __init__(self) -> None:
        self.stream_subscribers: dict[str, list[WebSocket]] = {}
        self.event_subscribers: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def subscribe_stream(self, camera_id: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self.stream_subscribers.setdefault(camera_id, []).append(ws)

    async def unsubscribe_stream(self, camera_id: str, ws: WebSocket) -> None:
        async with self._lock:
            subs = self.stream_subscribers.get(camera_id, [])
            if ws in subs:
                subs.remove(ws)

    async def subscribe_events(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self.event_subscribers.append(ws)

    async def unsubscribe_events(self, ws: WebSocket) -> None:
        async with self._lock:
            if ws in self.event_subscribers:
                self.event_subscribers.remove(ws)

    async def send_frame(self, camera_id: str, jpeg_b64: str, ts: float) -> None:
        subs = list(self.stream_subscribers.get(camera_id, []))
        if not subs:
            return
        payload = json.dumps(
            {"type": "frame", "camera_id": camera_id, "jpeg_b64": jpeg_b64, "ts": ts}
        )
        await self._broadcast(subs, payload, channel=("stream", camera_id))

    async def send_event(self, event: dict[str, Any]) -> None:
        if not self.event_subscribers:
            return
        payload = json.dumps({"type": "event", "data": event}, default=str)
        await self._broadcast(list(self.event_subscribers), payload, channel=("events",))

    async def _broadcast(self, subs: list[WebSocket], payload: str, channel) -> None:
        dead: list[WebSocket] = []
        for ws in subs:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        if not dead:
            return
        async with self._lock:
            if channel[0] == "stream":
                cam_id = channel[1]
                bucket = self.stream_subscribers.get(cam_id, [])
                for ws in dead:
                    if ws in bucket:
                        bucket.remove(ws)
            else:
                for ws in dead:
                    if ws in self.event_subscribers:
                        self.event_subscribers.remove(ws)


manager = ConnectionManager()
