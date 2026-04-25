"""Cloudinary upload helpers.

If Cloudinary env vars are not set, falls back to returning sentinel
URLs so the pipeline still completes during local development.  Set
CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
in .env to enable real uploads.
"""
import asyncio
import io
import logging
import os
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

_configured: Optional[bool] = None


def _is_configured() -> bool:
    global _configured
    if _configured is not None:
        return _configured
    name = os.getenv("CLOUDINARY_CLOUD_NAME")
    key = os.getenv("CLOUDINARY_API_KEY")
    secret = os.getenv("CLOUDINARY_API_SECRET")
    if not (name and key and secret):
        logger.warning("Cloudinary not configured; uploads will return stub URLs")
        _configured = False
        return False
    try:
        import cloudinary  # type: ignore

        cloudinary.config(cloud_name=name, api_key=key, api_secret=secret, secure=True)
        _configured = True
        return True
    except Exception:
        logger.exception("Failed to configure Cloudinary; falling back to stub URLs")
        _configured = False
        return False


def _stub_url(prefix: str, ext: str) -> str:
    return f"https://stub.local/{prefix}/{uuid.uuid4().hex}.{ext}"


def _upload_sync(data: bytes, *, resource_type: str, folder: str, ext: str) -> str:
    import cloudinary.uploader  # type: ignore

    public_id = f"{folder}/{uuid.uuid4().hex}"
    result = cloudinary.uploader.upload(
        io.BytesIO(data),
        resource_type=resource_type,
        public_id=public_id,
        format=ext,
        overwrite=False,
    )
    return result["secure_url"]


async def upload_image(data: bytes, folder: str = "frames", ext: str = "jpg") -> str:
    if not _is_configured():
        return _stub_url(folder, ext)
    return await asyncio.to_thread(
        _upload_sync, data, resource_type="image", folder=folder, ext=ext
    )


async def upload_audio(data: bytes, folder: str = "narration", ext: str = "mp3") -> str:
    if not _is_configured():
        return _stub_url(folder, ext)
    return await asyncio.to_thread(
        _upload_sync, data, resource_type="video", folder=folder, ext=ext
    )


async def upload_frames(frames: list[bytes]) -> list[str]:
    return await asyncio.gather(*(upload_image(f) for f in frames))
