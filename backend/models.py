from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CameraCreate(BaseModel):
    name: str
    stream_url: str
    context: str
    threshold: float = 0.7


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    stream_url: Optional[str] = None
    context: Optional[str] = None
    threshold: Optional[float] = None
    status: Optional[str] = None


class CameraResponse(BaseModel):
    id: str
    name: str
    stream_url: str
    context: str
    threshold: float
    status: str
    created_at: datetime


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
