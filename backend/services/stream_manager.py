"""StreamManager: opens camera URLs, samples frames, broadcasts.

Two transports:
  - cv2: cv2.VideoCapture for RTSP, HTTP MJPEG, MP4, or webcam index.
         Works for most real IP cameras and RTSP feeds on Linux.
  - http_jpeg: polls a URL at FRAME_INTERVAL_S, expects a JPEG body.
         Works for snapshot endpoints and is portable across all
         platforms (macOS opencv wheels can't open https video).

Auto-picks http_jpeg when the URL ends in .jpg/.jpeg, otherwise cv2.

Public surface (start_camera / stop_camera / get_buffer_window) is the
same shape Sartaj's classifier callback will plug into.
"""
import asyncio
import base64
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import cv2
import httpx
import numpy as np

from services.connection_manager import manager
from services.stream_overlay import stream_overlay

logger = logging.getLogger(__name__)

FRAME_INTERVAL_S = 0.5
BUFFER_SECONDS = 60
JPEG_QUALITY = 60
RECONNECT_BACKOFF_S = [1.0, 2.0, 5.0, 10.0]


@dataclass
class _Stream:
    camera_id: str
    url: str
    task: Optional[asyncio.Task] = None
    buffer: deque[tuple[float, bytes, Optional[float]]] = field(
        default_factory=lambda: deque(maxlen=BUFFER_SECONDS)
    )


def _pick_transport(url: str) -> str:
    lo = url.lower().split("?")[0]
    if lo.endswith(".jpg") or lo.endswith(".jpeg") or "snapshot" in lo:
        return "http_jpeg"
    return "cv2"


class StreamManager:
    def __init__(self) -> None:
        self.streams: dict[str, _Stream] = {}
        self._overlay_ticks: dict[str, int] = {}

    async def start_camera(self, camera_id: str, url: str) -> None:
        if camera_id in self.streams:
            await self.stop_camera(camera_id)
        stream = _Stream(camera_id=camera_id, url=url)
        transport = _pick_transport(url)
        runner = self._run_http_jpeg if transport == "http_jpeg" else self._run_cv2
        stream.task = asyncio.create_task(runner(stream))
        self.streams[camera_id] = stream
        logger.info(
            "started stream camera_id=%s transport=%s url=%s",
            camera_id,
            transport,
            url,
        )

    async def stop_camera(self, camera_id: str) -> None:
        stream = self.streams.pop(camera_id, None)
        if stream is None:
            return
        if stream.task:
            stream.task.cancel()
            try:
                await stream.task
            except (asyncio.CancelledError, Exception):
                pass
        logger.info("stopped stream camera_id=%s", camera_id)

    async def stop_all(self) -> None:
        for cid in list(self.streams.keys()):
            await self.stop_camera(cid)

    def get_latest_frame(self, camera_id: str) -> Optional[bytes]:
        stream = self.streams.get(camera_id)
        if stream and stream.buffer:
            return stream.buffer[-1][1]
        return None

    def get_latest_video_pos_msec(self, camera_id: str) -> Optional[float]:
        stream = self.streams.get(camera_id)
        if not stream or not stream.buffer:
            return None
        return stream.buffer[-1][2]

    def get_buffer_window(
        self, camera_id: str, before_s: int = 10, after_s: int = 0
    ) -> list[bytes]:
        stream = self.streams.get(camera_id)
        if not stream or not stream.buffer:
            return []
        now = time.time()
        lo = now - before_s
        hi = now + after_s
        return [jpeg for ts, jpeg, _pos in stream.buffer if lo <= ts <= hi]

    async def _publish(
        self, stream: _Stream, frame_bgr: np.ndarray, video_pos_msec: Optional[float] = None
    ) -> None:
        ts = time.time()
        tick = self._overlay_ticks.get(stream.camera_id, 0) + 1
        self._overlay_ticks[stream.camera_id] = tick

        overlay = await asyncio.to_thread(
            stream_overlay.annotate_bgr, frame_bgr, frame_index=tick
        )
        jpeg = overlay.jpeg
        stream.buffer.append((ts, jpeg, video_pos_msec))
        b64 = base64.b64encode(jpeg).decode("ascii")
        await manager.send_frame(
            stream.camera_id,
            b64,
            ts,
            caption=overlay.caption,
            boxes_xyxy=overlay.boxes_xyxy,
        )

    # cv2 transport -------------------------------------------------

    async def _run_cv2(self, stream: _Stream) -> None:
        attempt = 0
        while True:
            cap = await asyncio.to_thread(self._open_cv2, stream.url)
            if cap is None or not cap.isOpened():
                if cap is not None:
                    cap.release()
                delay = RECONNECT_BACKOFF_S[min(attempt, len(RECONNECT_BACKOFF_S) - 1)]
                logger.warning(
                    "cv2 open failed camera_id=%s; retrying in %.1fs",
                    stream.camera_id,
                    delay,
                )
                attempt += 1
                await asyncio.sleep(delay)
                continue
            attempt = 0
            try:
                while True:
                    frame, pos_msec = await asyncio.to_thread(self._grab_frame_cv2, cap)
                    if frame is None:
                        break
                    await self._publish(stream, frame, video_pos_msec=pos_msec)
                    await asyncio.sleep(FRAME_INTERVAL_S)
            except asyncio.CancelledError:
                cap.release()
                raise
            except Exception:
                logger.exception("cv2 loop error camera_id=%s", stream.camera_id)
            finally:
                cap.release()

    @staticmethod
    def _open_cv2(url: str):
        try:
            try:
                idx = int(url)
                cap = cv2.VideoCapture(idx)
            except ValueError:
                cap = cv2.VideoCapture(url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return cap
        except Exception:
            logger.exception("cv2.VideoCapture failed for %s", url)
            return None

    @staticmethod
    def _grab_frame_cv2(cap) -> tuple[Optional[np.ndarray], Optional[float]]:
        for _ in range(5):
            if not cap.grab():
                break
        ok, frame = cap.retrieve()
        if not ok or frame is None:
            ok, frame = cap.read()
        if not ok or frame is None or not isinstance(frame, np.ndarray):
            return None, None
        raw = cap.get(cv2.CAP_PROP_POS_MSEC)
        if raw is None or float(raw) < 0.0:
            pos_msec = None
        else:
            pos_msec = float(raw)
        return frame, pos_msec

    # http_jpeg transport -------------------------------------------

    async def _run_http_jpeg(self, stream: _Stream) -> None:
        attempt = 0
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            while True:
                try:
                    r = await client.get(stream.url)
                    if r.status_code != 200 or not r.content:
                        raise RuntimeError(f"status={r.status_code}")
                    frame = cv2.imdecode(
                        np.frombuffer(r.content, dtype=np.uint8), cv2.IMREAD_COLOR
                    )
                    if frame is None:
                        raise RuntimeError("jpeg decode failed")
                    await self._publish(stream, frame, video_pos_msec=None)
                    attempt = 0
                    await asyncio.sleep(FRAME_INTERVAL_S)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    delay = RECONNECT_BACKOFF_S[min(attempt, len(RECONNECT_BACKOFF_S) - 1)]
                    logger.warning(
                        "http_jpeg fetch failed camera_id=%s err=%s; retry in %.1fs",
                        stream.camera_id,
                        e,
                        delay,
                    )
                    attempt += 1
                    await asyncio.sleep(delay)


stream_manager = StreamManager()
