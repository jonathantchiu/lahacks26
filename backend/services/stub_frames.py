"""Placeholder frame source until Sartaj's stream_manager.py lands.

Emits a tiny 1x1 JPEG plus a frame counter so the frontend can render
something immediately.  Replace the call site in routers/websocket.py
with the real stream queue when ready.
"""
import base64
import time

# 1x1 black JPEG, base64-encoded.
_PLACEHOLDER_JPEG_B64 = (
    "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEB"
    "AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEB/9sAQwEBAQEBAQEBAQEBAQEB"
    "AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEB/8AA"
    "EQgAAQABAwEiAAIRAQMRAf/EAB8AAAEFAQEBAQEBAAAAAAAAAAABAgMEBQYHCAkKC//EALUQ"
    "AAIBAwMCBAMFBQQEAAABfQECAwAEEQUSITFBBhNRYQcicRQygZGhCCNCscEVUtHwJDNicoIJ"
    "ChYXGBkaJSYnKCkqNDU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6g4SF"
    "hoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV1tfY2drh4uPk"
    "5ebn6Onq8fLz9PX29/j5+v/aAAwDAQACEQMRAD8A/v8AKAP/2Q=="
)


def placeholder_jpeg_b64() -> str:
    return _PLACEHOLDER_JPEG_B64


def now_ts() -> float:
    return time.time()
