import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from services.connection_manager import manager
from services.stream_manager import stream_manager
from services.stub_frames import now_ts, placeholder_jpeg_b64

router = APIRouter()

STUB_FRAME_INTERVAL_S = 1.0


@router.websocket("/ws/stream/{camera_id}")
async def stream_websocket(websocket: WebSocket, camera_id: str):
    """Live frame feed for a single camera.

    If a real stream is active in stream_manager, frames flow through
    ConnectionManager.send_frame and we just hold the socket open.
    Otherwise (no camera registered, or stream still reconnecting),
    we emit a stub placeholder so the frontend can render *something*.
    """
    await manager.subscribe_stream(camera_id, websocket)
    try:
        while True:
            if camera_id in stream_manager.streams:
                await websocket.receive_text()
            else:
                await manager.send_frame(camera_id, placeholder_jpeg_b64(), now_ts())
                await asyncio.sleep(STUB_FRAME_INTERVAL_S)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await manager.unsubscribe_stream(camera_id, websocket)


@router.websocket("/ws/events")
async def events_websocket(websocket: WebSocket):
    """Global event feed.  Sends a JSON message per notable event."""
    await manager.subscribe_events(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await manager.unsubscribe_events(websocket)


@router.post("/test/fire-event")
async def fire_test_event(camera_id: str = "test-cam", description: str = "Test event"):
    """Dev-only: broadcast a fake event to all /ws/events subscribers."""
    if not manager.event_subscribers:
        raise HTTPException(409, "No /ws/events subscribers connected")
    await manager.send_event(
        {
            "id": "test",
            "camera_id": camera_id,
            "camera_name": "Stub Camera",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "confidence": 0.92,
            "description": description,
            "thumbnail": None,
            "audio_url": None,
            "solana_tx": None,
        }
    )
    return {"broadcast": True, "subscribers": len(manager.event_subscribers)}
