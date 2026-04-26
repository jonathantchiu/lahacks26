import asyncio
import logging
import time
from dataclasses import dataclass

import cv2
import numpy as np

from database import cameras_collection
from services.classifier import ClassifierService
from services.event_pipeline import pipeline
from services.face_service import FaceService
from services.stream_manager import stream_manager

logger = logging.getLogger(__name__)


@dataclass
class _CameraState:
    last_event_ts: float = 0.0
    last_frame_hash: int = 0
    thresholds_cache_ts: float = 0.0
    threshold: float = 0.7
    context: str = ""


class DetectionMonitor:
    """Polls live streams and triggers event pipeline on notable frames."""

    def __init__(
        self,
        classifier: ClassifierService,
        face_service: FaceService,
        *,
        loop_interval_s: float = 1.0,
        event_cooldown_s: float = 20.0,
    ) -> None:
        self.classifier = classifier
        self.face_service = face_service
        self.loop_interval_s = loop_interval_s
        self.event_cooldown_s = event_cooldown_s
        self._state: dict[str, _CameraState] = {}
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Detection monitor started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except Exception:
                pass
        logger.info("Detection monitor stopped")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                for camera_id in list(stream_manager.streams.keys()):
                    await self._process_camera(camera_id)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Detection monitor loop error")
            await asyncio.sleep(self.loop_interval_s)

    async def _process_camera(self, camera_id: str) -> None:
        jpeg = stream_manager.get_latest_frame(camera_id)
        if not jpeg:
            return

        state = self._state.setdefault(camera_id, _CameraState())
        frame_hash = hash(jpeg[:256])
        if frame_hash == state.last_frame_hash:
            return
        state.last_frame_hash = frame_hash

        frame = cv2.imdecode(np.frombuffer(jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            return

        await self._refresh_camera_settings(camera_id, state)
        result = self.classifier.classify(frame)
        if result.notable_confidence < state.threshold:
            return

        now = time.time()
        if now - state.last_event_ts < self.event_cooldown_s:
            return
        state.last_event_ts = now

        matches = await self.face_service.identify_people(frame, result.person_boxes)
        if matches:
            names = ", ".join(sorted({m.name for m in matches}))
            context = f"{state.context} Known/seen people: {names}".strip()
        else:
            context = state.context

        frames = stream_manager.get_buffer_window(camera_id, before_s=8, after_s=0)
        if not frames:
            frames = [jpeg]
        await pipeline.run(camera_id=camera_id, frames=frames, confidence=result.notable_confidence, context_override=context)

    async def _refresh_camera_settings(self, camera_id: str, state: _CameraState) -> None:
        now = time.time()
        if now - state.thresholds_cache_ts < 5:
            return
        doc = await cameras_collection.find_one({"_id": self._maybe_object_id(camera_id)})
        if doc:
            state.threshold = float(doc.get("threshold", 0.7))
            state.context = str(doc.get("context", ""))
        state.thresholds_cache_ts = now

    @staticmethod
    def _maybe_object_id(camera_id: str):
        try:
            from bson import ObjectId

            return ObjectId(camera_id)
        except Exception:
            return camera_id
