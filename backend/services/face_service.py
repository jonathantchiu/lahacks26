import logging
import math
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

from database import db

logger = logging.getLogger(__name__)

try:
    import face_recognition
except Exception:  # pragma: no cover - optional runtime dependency
    face_recognition = None


@dataclass
class FaceMatch:
    name: str
    similarity: float
    face_box: tuple[int, int, int, int]


class FaceService:
    """Matches faces against stored embeddings in MongoDB."""

    def __init__(self, *, similarity_threshold: float = 0.6) -> None:
        self.similarity_threshold = similarity_threshold
        self.collection = db.people
        self._unknown_counter = 0

    async def identify_people(
        self,
        frame_bgr: np.ndarray,
        person_boxes: list[tuple[int, int, int, int]],
    ) -> list[FaceMatch]:
        if face_recognition is None:
            return []

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results: list[FaceMatch] = []

        for box in person_boxes:
            x1, y1, x2, y2 = box
            crop = rgb[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            try:
                encodings = face_recognition.face_encodings(crop)
            except Exception:
                logger.exception("face_recognition encoding failed")
                continue

            if not encodings:
                continue

            embedding = encodings[0].tolist()
            best = await self._nearest_embedding(embedding)
            if best and best["similarity"] >= self.similarity_threshold:
                results.append(
                    FaceMatch(
                        name=best["name"],
                        similarity=best["similarity"],
                        face_box=box,
                    )
                )
                continue

            self._unknown_counter += 1
            unknown_name = f"unknown_person_{self._unknown_counter}"
            await self.collection.insert_one({"name": unknown_name, "embedding": embedding})
            results.append(
                FaceMatch(name=unknown_name, similarity=0.0, face_box=box)
            )

        return results

    async def register_person(self, name: str, frame_bgr: np.ndarray) -> bool:
        if face_recognition is None:
            return False
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb)
        if not encodings:
            return False
        await self.collection.update_one(
            {"name": name},
            {"$set": {"embedding": encodings[0].tolist()}},
            upsert=True,
        )
        return True

    async def _nearest_embedding(self, query: list[float]) -> dict[str, Any] | None:
        best_doc = None
        best_similarity = -1.0

        async for doc in self.collection.find({}, {"name": 1, "embedding": 1}):
            emb = doc.get("embedding")
            if not emb:
                continue
            similarity = self._cosine_similarity(query, emb)
            if similarity > best_similarity:
                best_similarity = similarity
                best_doc = {"name": doc.get("name", "unknown"), "similarity": similarity}

        return best_doc

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if len(a) != len(b) or not a:
            return -1.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0.0 or nb == 0.0:
            return -1.0
        return dot / (na * nb)
