"""Smoke test for stream_manager.

Spins up an in-process HTTP server that serves a real JPEG, registers
that as a camera with a `.jpg` URL (auto-routed to the http_jpeg
transport), subscribes via WS, and verifies real frames arrive.
"""
import asyncio
import base64
import json
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx
import websockets

BASE_HTTP = "http://127.0.0.1:8000"
BASE_WS = "ws://127.0.0.1:8000"

# A real, valid 8x8 red JPEG (~600 bytes after base64-decode).
SAMPLE_JPEG_HEX = (
    "ffd8ffe000104a46494600010100000100010000ffdb004300080606070605080707"
    "0709090808080a0e090b0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a"
    "0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0affc4"
    "001f0000010501010101010100000000000000000102030405060708090a0bffc400"
    "b5100002010303020403050504040000017d01020300041105122131410613516107"
    "227114328191a1082342b1c11552d1f02433627282090a161718191a25262728292a"
    "3435363738393a434445464748494a535455565758595a636465666768696a737475"
    "767778797a838485868788898a92939495969798999aa2a3a4a5a6a7a8a9aab2b3b4"
    "b5b6b7b8b9bac2c3c4c5c6c7c8c9cad2d3d4d5d6d7d8d9dae1e2e3e4e5e6e7e8e9ea"
    "f1f2f3f4f5f6f7f8f9faffda000c03010002110311003f00f7e8a28a00ffd9"
)
SAMPLE_JPEG = bytes.fromhex(SAMPLE_JPEG_HEX)


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(SAMPLE_JPEG)))
        self.end_headers()
        self.wfile.write(SAMPLE_JPEG)

    def log_message(self, *_):
        pass


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


async def main() -> int:
    port = _free_port()
    server = HTTPServer(("127.0.0.1", port), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    snapshot_url = f"http://127.0.0.1:{port}/cam.jpg"
    print(f"local snapshot server: {snapshot_url}")

    async with httpx.AsyncClient(base_url=BASE_HTTP, timeout=30.0) as client:
        cam = (
            await client.post(
                "/cameras",
                json={
                    "name": "Local Snapshot",
                    "stream_url": snapshot_url,
                    "context": "test",
                },
            )
        ).json()
        cam_id = cam["id"]
        print(f"created camera id={cam_id}")

        await asyncio.sleep(2.0)

        health = (await client.get("/health")).json()
        assert cam_id in health["active_streams"], "stream did not start"

        async with websockets.connect(f"{BASE_WS}/ws/stream/{cam_id}") as ws:
            real = 0
            for _ in range(8):
                raw = await asyncio.wait_for(ws.recv(), timeout=10.0)
                msg = json.loads(raw)
                if msg.get("type") != "frame":
                    continue
                jpeg = base64.b64decode(msg["jpeg_b64"])
                if jpeg == SAMPLE_JPEG:
                    real += 1
                    if real >= 2:
                        break
            print(f"real frames matching sample: {real}")
            assert real >= 2, f"expected >=2 real frames, got {real}"

        await client.delete(f"/cameras/{cam_id}")
        await asyncio.sleep(0.5)
        health = (await client.get("/health")).json()
        assert cam_id not in health["active_streams"], "stream did not stop"

    server.shutdown()
    print("OK: stream_manager smoke test passed")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
