import logging
import os
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)

try:
    import torch
    from torchvision import models, transforms
    from PIL import Image
except Exception:  # pragma: no cover - optional runtime dependency
    torch = None
    models = None
    transforms = None
    Image = None

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover - optional runtime dependency
    YOLO = None


@dataclass
class ClassificationResult:
    notable_confidence: float
    person_boxes: list[tuple[int, int, int, int]]


class ClassifierService:
    """Runs YOLO person detection and ResNet notable scoring."""

    def __init__(
        self,
        *,
        resnet_model_path: str | None = None,
        yolo_model_name: str = "yolov8n.pt",
        yolo_confidence: float = 0.25,
    ) -> None:
        self.yolo_confidence = yolo_confidence
        self.device = "cpu"
        self._yolo: Any | None = None
        self._resnet = None
        self._transform = None

        self._init_yolo(yolo_model_name)
        self._init_resnet(resnet_model_path)

    def classify(self, frame_bgr: np.ndarray) -> ClassificationResult:
        boxes = self._detect_people(frame_bgr)
        notable_conf = self._score_notable(frame_bgr)
        return ClassificationResult(notable_confidence=notable_conf, person_boxes=boxes)

    def _init_yolo(self, model_name: str) -> None:
        if YOLO is None:
            logger.warning("Ultralytics not installed; person detection disabled")
            return
        try:
            self._yolo = YOLO(model_name)
            logger.info("YOLO initialized with model=%s", model_name)
        except Exception:
            logger.exception("Failed to initialize YOLO; person detection disabled")
            self._yolo = None

    def _init_resnet(self, model_path: str | None) -> None:
        if torch is None or models is None or transforms is None:
            logger.warning("Torch/torchvision not installed; notable scoring disabled")
            return

        model_path = model_path or os.getenv("RESNET_MODEL_PATH")
        if not model_path:
            logger.warning("RESNET_MODEL_PATH not set; notable scoring disabled")
            return

        if not os.path.exists(model_path):
            logger.warning("ResNet model path not found: %s", model_path)
            return

        try:
            model = models.resnet18(weights=None)
            model.fc = torch.nn.Linear(model.fc.in_features, 2)
            state = torch.load(model_path, map_location="cpu")
            model.load_state_dict(state)
            model.eval()

            self._resnet = model
            self._transform = transforms.Compose(
                [
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225],
                    ),
                ]
            )
            logger.info("ResNet classifier initialized from %s", model_path)
        except Exception:
            logger.exception("Failed to initialize ResNet; notable scoring disabled")
            self._resnet = None
            self._transform = None

    def _detect_people(self, frame_bgr: np.ndarray) -> list[tuple[int, int, int, int]]:
        if self._yolo is None:
            return []

        try:
            results = self._yolo.predict(
                source=frame_bgr,
                conf=self.yolo_confidence,
                verbose=False,
                classes=[0],  # person class
            )
            if not results:
                return []
            boxes_xyxy = results[0].boxes.xyxy.cpu().numpy() if results[0].boxes is not None else []
            h, w = frame_bgr.shape[:2]
            out: list[tuple[int, int, int, int]] = []
            for box in boxes_xyxy:
                x1, y1, x2, y2 = [int(v) for v in box.tolist()]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                if x2 > x1 and y2 > y1:
                    out.append((x1, y1, x2, y2))
            return out
        except Exception:
            logger.exception("YOLO inference failed")
            return []

    def _score_notable(self, frame_bgr: np.ndarray) -> float:
        if self._resnet is None or self._transform is None or Image is None or torch is None:
            return 0.0
        try:
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            tensor = self._transform(pil_img).unsqueeze(0)
            with torch.no_grad():
                logits = self._resnet(tensor)
                probs = torch.softmax(logits, dim=1)
            return float(probs[0, 1].item())
        except Exception:
            logger.exception("ResNet inference failed")
            return 0.0
