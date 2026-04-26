import logging
import os
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover - optional dependency
    YOLO = None


@dataclass
class OverlayResult:
    jpeg: bytes
    boxes_xyxy: list[list[float]]
    caption: str


class StreamYoloOverlay:
    """Cheap YOLO overlay for websocket previews (person class only)."""

    def __init__(self) -> None:
        self.enabled = os.getenv("STREAM_YOLO_OVERLAY", "1") not in ("0", "false", "False")
        self.every_n = max(1, int(os.getenv("STREAM_YOLO_EVERY_N", "2")))
        self.conf = float(os.getenv("STREAM_YOLO_CONF", "0.25"))
        self._model: Any | None = None

        if not self.enabled:
            return
        if YOLO is None:
            logger.warning("Ultralytics missing; stream overlays disabled")
            self.enabled = False
            return
        try:
            self._model = YOLO(os.getenv("STREAM_YOLO_MODEL", "yolov8n.pt"))
        except Exception:
            logger.exception("Failed to init YOLO overlay model; disabling overlays")
            self.enabled = False

    def annotate_bgr(self, frame_bgr: np.ndarray, *, frame_index: int) -> OverlayResult:
        boxes: list[list[float]] = []
        caption = "YOLO overlay off"

        if not self.enabled or self._model is None:
            ok, buf = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 60])
            return OverlayResult(jpeg=buf.tobytes() if ok else b"", boxes=boxes, caption=caption)

        run = frame_index % self.every_n == 0
        if run:
            try:
                results = self._model.predict(
                    source=frame_bgr,
                    conf=self.conf,
                    verbose=False,
                    classes=[0],
                )
                if results and results[0].boxes is not None:
                    xyxy = results[0].boxes.xyxy.cpu().numpy()
                    for row in xyxy:
                        x1, y1, x2, y2 = [float(v) for v in row.tolist()]
                        boxes.append([x1, y1, x2, y2])
            except Exception:
                logger.exception("YOLO overlay inference failed")

        h, w = frame_bgr.shape[:2]
        out = frame_bgr
        for box in boxes:
            x1, y1, x2, y2 = [int(v) for v in box]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w - 1, x2), min(h - 1, y2)
            cv2.rectangle(out, (x1, y1), (x2, y2), (0, 255, 0), 2)

        ok, buf = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 60])
        caption = f"YOLOv8n | persons={len(boxes)} | conf≥{self.conf:.2f} | every {self.every_n} frames"
        return OverlayResult(jpeg=buf.tobytes() if ok else b"", boxes=boxes, caption=caption)


stream_overlay = StreamYoloOverlay()
