from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CameraCreate(BaseModel):
    name: str
    stream_url: str
    context: str
    threshold: float = 0.7
    # For file-based streams only: only allow detection events after this offset (seconds) in the media timeline.
    demo_alert_after_video_sec: Optional[float] = None


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    stream_url: Optional[str] = None
    context: Optional[str] = None
    threshold: Optional[float] = None
    status: Optional[str] = None
    demo_alert_after_video_sec: Optional[float] = None


class CameraResponse(BaseModel):
    id: str
    name: str
    stream_url: str
    context: str
    threshold: float
    status: str
    created_at: datetime
    demo_alert_after_video_sec: Optional[float] = None


class EventResponse(BaseModel):
    id: str
    camera_id: str
    camera_name: Optional[str] = None
    timestamp: datetime
    confidence: float
    description: str
    frames: list[str] = []
    thumbnail: Optional[str] = None
    audio_url: Optional[str] = None
    solana_tx: Optional[str] = None
    context_used: Optional[str] = None


class EventQuery(BaseModel):
    camera_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_confidence: Optional[float] = None
    limit: int = 50
    offset: int = 0
