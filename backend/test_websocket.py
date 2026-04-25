"""Smoke test for the WebSocket endpoints.

Connects to /ws/stream/<id> and /ws/events, fires a test event via
HTTP POST, and verifies messages arrive on both channels.
"""
import asyncio
import json
import sys

import httpx
import websockets

BASE_HTTP = "http://127.0.0.1:8000"
BASE_WS = "ws://127.0.0.1:8000"


async def listen_stream(camera_id: str, n: int) -> list[dict]:
    msgs: list[dict] = []
    async with websockets.connect(f"{BASE_WS}/ws/stream/{camera_id}") as ws:
        for _ in range(n):
            raw = await asyncio.wait_for(ws.recv(), timeout=3.0)
            msgs.append(json.loads(raw))
    return msgs


async def listen_events(n: int) -> list[dict]:
    msgs: list[dict] = []
    async with websockets.connect(f"{BASE_WS}/ws/events") as ws:
        for _ in range(n):
            raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
            msgs.append(json.loads(raw))
    return msgs


async def fire_event() -> dict:
    # Wait briefly so the events socket subscribes before we fire.
    await asyncio.sleep(1.0)
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BASE_HTTP}/test/fire-event",
            params={"camera_id": "stub", "description": "Hello from smoke test"},
        )
        r.raise_for_status()
        return r.json()


async def main() -> int:
    stream_task = asyncio.create_task(listen_stream("stub", n=2))
    events_task = asyncio.create_task(listen_events(n=1))
    fire_task = asyncio.create_task(fire_event())

    stream_msgs, event_msgs, fire_result = await asyncio.gather(
        stream_task, events_task, fire_task
    )

    print(f"fire result: {fire_result}")
    print(f"stream frames received: {len(stream_msgs)}")
    assert len(stream_msgs) == 2, "expected 2 frames"
    assert stream_msgs[0]["type"] == "frame"
    assert stream_msgs[0]["camera_id"] == "stub"
    assert stream_msgs[0]["jpeg_b64"]
    print(f"  frame[0] keys: {list(stream_msgs[0].keys())}")

    print(f"events received: {len(event_msgs)}")
    assert len(event_msgs) == 1, "expected 1 event"
    assert event_msgs[0]["type"] == "event"
    assert event_msgs[0]["data"]["camera_id"] == "stub"
    print(f"  event[0]: {event_msgs[0]['data']['description']}")

    print("OK: WebSocket smoke test passed")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
