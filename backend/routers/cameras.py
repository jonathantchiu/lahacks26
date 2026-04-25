from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException

from database import cameras_collection
from models import CameraCreate, CameraResponse, CameraUpdate
from services.stream_manager import stream_manager

router = APIRouter(prefix="/cameras", tags=["cameras"])


def _to_response(doc) -> CameraResponse:
    return CameraResponse(
        id=str(doc["_id"]),
        name=doc["name"],
        stream_url=doc["stream_url"],
        context=doc["context"],
        threshold=doc["threshold"],
        status=doc["status"],
        created_at=doc["created_at"],
    )


def _parse_id(camera_id: str) -> ObjectId:
    try:
        return ObjectId(camera_id)
    except (InvalidId, TypeError):
        raise HTTPException(400, "Invalid camera id")


@router.post("", response_model=CameraResponse, status_code=201)
async def create_camera(camera: CameraCreate):
    doc = {
        **camera.model_dump(),
        "status": "active",
        "created_at": datetime.now(timezone.utc),
    }
    result = await cameras_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    await stream_manager.start_camera(str(result.inserted_id), camera.stream_url)
    return _to_response(doc)


@router.get("", response_model=list[CameraResponse])
async def list_cameras():
    return [_to_response(doc) async for doc in cameras_collection.find()]


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(camera_id: str):
    doc = await cameras_collection.find_one({"_id": _parse_id(camera_id)})
    if not doc:
        raise HTTPException(404, "Camera not found")
    return _to_response(doc)


@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(camera_id: str, update: CameraUpdate):
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(400, "No fields to update")
    doc = await cameras_collection.find_one_and_update(
        {"_id": _parse_id(camera_id)},
        {"$set": update_data},
        return_document=True,
    )
    if not doc:
        raise HTTPException(404, "Camera not found")
    if "stream_url" in update_data:
        await stream_manager.start_camera(camera_id, doc["stream_url"])
    return _to_response(doc)


@router.delete("/{camera_id}")
async def delete_camera(camera_id: str):
    result = await cameras_collection.delete_one({"_id": _parse_id(camera_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Camera not found")
    await stream_manager.stop_camera(camera_id)
    return {"deleted": True}
