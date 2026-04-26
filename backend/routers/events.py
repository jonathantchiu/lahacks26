from datetime import datetime
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query

import base64

from fastapi.responses import Response
from pydantic import BaseModel

from database import events_collection
from models import EventResponse
from services.event_pipeline import pipeline
from services.stub_frames import placeholder_jpeg_b64

router = APIRouter(prefix="/events", tags=["events"])

_narration_service = None

def _get_narration():
    global _narration_service
    if _narration_service is None:
        from services.narration import NarrationService
        _narration_service = NarrationService()
    return _narration_service


class NarrateRequest(BaseModel):
    text: str


def _to_response(doc) -> EventResponse:
    return EventResponse(
        id=str(doc["_id"]),
        camera_id=doc.get("camera_id", ""),
        camera_name=doc.get("camera_name"),
        timestamp=doc["timestamp"],
        confidence=doc["confidence"],
        description=doc["description"],
        frames=doc.get("frames", []),
        thumbnail=doc.get("thumbnail"),
        audio_url=doc.get("audio_url"),
        solana_tx=doc.get("solana_tx"),
        context_used=doc.get("context_used"),
    )


@router.get("", response_model=list[EventResponse])
async def list_events(
    camera_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_confidence: Optional[float] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    query: dict = {}
    if camera_id:
        query["camera_id"] = camera_id
    if min_confidence is not None:
        query["confidence"] = {"$gte": min_confidence}
    if start_date or end_date:
        ts: dict = {}
        if start_date:
            ts["$gte"] = start_date
        if end_date:
            ts["$lte"] = end_date
        query["timestamp"] = ts

    cursor = (
        events_collection.find(query)
        .sort("timestamp", -1)
        .skip(offset)
        .limit(limit)
    )
    return [_to_response(doc) async for doc in cursor]


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: str):
    try:
        oid = ObjectId(event_id)
    except (InvalidId, TypeError):
        raise HTTPException(400, "Invalid event id")
    doc = await events_collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(404, "Event not found")
    return _to_response(doc)


@router.delete("/{event_id}", status_code=204)
async def delete_event(event_id: str):
    try:
        oid = ObjectId(event_id)
    except (InvalidId, TypeError):
        raise HTTPException(400, "Invalid event id")
    result = await events_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(404, "Event not found")


@router.post("/narrate")
async def narrate_text(body: NarrateRequest):
    """Synthesize narration audio from text and return mp3 bytes."""
    svc = _get_narration()
    audio = await svc.narrate(body.text)
    if not audio:
        raise HTTPException(503, "Narration service unavailable")
    return Response(content=audio, media_type="audio/mpeg")


@router.post("/test/trigger", response_model=EventResponse, status_code=201)
async def trigger_test_event(camera_id: str, confidence: float = 0.9):
    """Dev-only: run the full event pipeline with a single stub frame."""
    stub_frame = base64.b64decode(placeholder_jpeg_b64())
    doc = await pipeline.run(
        camera_id=camera_id,
        frames=[stub_frame],
        confidence=confidence,
    )
    return _to_response(doc)
