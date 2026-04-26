"""Event pipeline orchestrator.

Triggered when the classifier flags a notable frame.  Runs:
  1. reasoning(frames, context)   -> text description
  2. narration(text)              -> audio bytes
  3. cloudinary upload (frames + audio) in parallel
  4. mongo insert (events collection)
  5. solana_logger(event_hash)    -> tx signature
  6. broadcast over /ws/events

All external dependencies are pluggable callables registered on the
pipeline.  Defaults are safe stubs so the chain runs without sponsor
APIs configured — useful for local dev and as fallbacks if a sponsor
service is rate-limited or down.
"""
import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional

from bson import ObjectId

from database import cameras_collection, events_collection
from services.cloudinary_upload import upload_audio, upload_frames
from services.connection_manager import manager

logger = logging.getLogger(__name__)

ReasoningFn = Callable[[list[bytes], str], Awaitable[str]]
NarrationFn = Callable[[str], Awaitable[Optional[bytes]]]
SolanaFn = Callable[[str, str, int], Awaitable[Optional[str]]]


async def _stub_reasoning(frames: list[bytes], context: str) -> str:
    return f"Notable activity detected. Context: {context}"


async def _stub_narration(text: str) -> Optional[bytes]:
    return None


async def _stub_solana(event_hash: str, camera_id: str, ts: int) -> Optional[str]:
    return None


class EventPipeline:
    def __init__(self) -> None:
        self.reasoning: ReasoningFn = _stub_reasoning
        self.narration: NarrationFn = _stub_narration
        self.solana_logger: SolanaFn = _stub_solana

    def set_reasoning(self, fn: ReasoningFn) -> None:
        self.reasoning = fn

    def set_narration(self, fn: NarrationFn) -> None:
        self.narration = fn

    def set_solana_logger(self, fn: SolanaFn) -> None:
        self.solana_logger = fn

    async def run(
        self,
        *,
        camera_id: str,
        frames: list[bytes],
        confidence: float,
        context_override: Optional[str] = None,
    ) -> dict[str, Any]:
        ts = datetime.now(timezone.utc)

        camera = await self._load_camera(camera_id)
        context = context_override if context_override is not None else (camera.get("context", "") if camera else "")
        camera_name = camera.get("name") if camera else None

        description = await self._safe_call(
            self.reasoning(frames, context),
            fallback=f"Notable activity detected at {camera_name or camera_id}",
            label="reasoning",
        )

        audio_bytes = await self._safe_call(
            self.narration(description),
            fallback=None,
            label="narration",
        )

        audio_url = await upload_audio(audio_bytes) if audio_bytes else None
        logger.info("pipeline audio_url=%s (bytes=%d)", audio_url, len(audio_bytes) if audio_bytes else 0)

        sampled_frames = self._sample_frames(frames, max_frames=8)
        frame_urls = await upload_frames(sampled_frames) if sampled_frames else []
        thumbnail = frame_urls[0] if frame_urls else None

        doc = {
            "camera_id": camera_id,
            "camera_name": camera_name,
            "timestamp": ts,
            "confidence": confidence,
            "description": description,
            "frames": frame_urls,
            "thumbnail": thumbnail,
            "audio_url": audio_url,
            "solana_tx": None,
            "context_used": context,
        }
        result = await events_collection.insert_one(doc)
        doc["_id"] = result.inserted_id

        event_hash = self._hash_event(doc)
        solana_tx = await self._safe_call(
            self.solana_logger(event_hash, camera_id, int(ts.timestamp())),
            fallback=None,
            label="solana",
        )
        if solana_tx:
            await events_collection.update_one(
                {"_id": result.inserted_id}, {"$set": {"solana_tx": solana_tx}}
            )
            doc["solana_tx"] = solana_tx

        await manager.send_event(self._serialize(doc))
        return doc

    async def _load_camera(self, camera_id: str) -> Optional[dict]:
        try:
            return await cameras_collection.find_one({"_id": ObjectId(camera_id)})
        except Exception:
            return None

    @staticmethod
    async def _safe_call(coro, *, fallback, label: str):
        try:
            return await coro
        except Exception:
            logger.exception("%s failed; using fallback", label)
            return fallback

    @staticmethod
    def _sample_frames(frames: list[bytes], max_frames: int) -> list[bytes]:
        if len(frames) <= max_frames:
            return frames
        step = max(1, len(frames) // max_frames)
        return frames[::step][:max_frames]

    @staticmethod
    def _hash_event(doc: dict[str, Any]) -> str:
        payload = json.dumps(
            {
                "camera_id": doc["camera_id"],
                "timestamp": doc["timestamp"].isoformat(),
                "description": doc["description"],
                "confidence": doc["confidence"],
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    @staticmethod
    def _serialize(doc: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(doc["_id"]),
            "camera_id": doc["camera_id"],
            "camera_name": doc.get("camera_name"),
            "timestamp": doc["timestamp"].isoformat(),
            "confidence": doc["confidence"],
            "description": doc["description"],
            "frames": doc.get("frames", []),
            "thumbnail": doc.get("thumbnail"),
            "audio_url": doc.get("audio_url"),
            "solana_tx": doc.get("solana_tx"),
            "context_used": doc.get("context_used"),
        }


pipeline = EventPipeline()
