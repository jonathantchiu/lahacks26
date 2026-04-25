"""End-to-end smoke test for the event pipeline.

1. Creates a camera via REST
2. Subscribes to /ws/events
3. Fires POST /events/test/trigger (runs reasoning -> upload -> mongo
   -> solana -> WS broadcast with stubbed external services)
4. Asserts event landed in Mongo via GET /events?camera_id=...
5. Asserts WS broadcast received
6. Cleans up
"""
import asyncio
import json
import sys

import httpx
import websockets

BASE_HTTP = "http://127.0.0.1:8000"
BASE_WS = "ws://127.0.0.1:8000"


async def listen_one_event() -> dict:
    async with websockets.connect(f"{BASE_WS}/ws/events") as ws:
        raw = await asyncio.wait_for(ws.recv(), timeout=10.0)
        return json.loads(raw)


async def main() -> int:
    async with httpx.AsyncClient(base_url=BASE_HTTP, timeout=30.0) as client:
        cam = (
            await client.post(
                "/cameras",
                json={
                    "name": "Pipeline Test Cam",
                    "stream_url": "http://example.com/stream",
                    "context": "watch for test events",
                },
            )
        ).json()
        cam_id = cam["id"]
        print(f"created camera id={cam_id}")

        listener = asyncio.create_task(listen_one_event())
        await asyncio.sleep(1.0)  # let WS subscribe

        trigger_resp = await client.post(
            "/events/test/trigger", params={"camera_id": cam_id, "confidence": 0.91}
        )
        trigger_resp.raise_for_status()
        triggered = trigger_resp.json()
        print(f"pipeline ran: event id={triggered['id']}")
        assert triggered["camera_id"] == cam_id
        assert triggered["description"]
        assert triggered["frames"], "expected at least one frame URL"

        ws_msg = await listener
        print(f"WS broadcast received: type={ws_msg['type']}")
        assert ws_msg["type"] == "event"
        assert ws_msg["data"]["id"] == triggered["id"]

        listed = (
            await client.get(
                "/events", params={"camera_id": cam_id, "min_confidence": 0.9}
            )
        ).json()
        print(f"GET /events returned {len(listed)} event(s) for this camera")
        assert any(e["id"] == triggered["id"] for e in listed)

        single = (await client.get(f"/events/{triggered['id']}")).json()
        assert single["id"] == triggered["id"]

        await client.delete(f"/cameras/{cam_id}")
        print("cleaned up camera")

    print("OK: pipeline smoke test passed")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
