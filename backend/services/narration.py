import asyncio
import logging
import os

from elevenlabs.client import ElevenLabs

logger = logging.getLogger(__name__)


class NarrationService:
    """Generates short narration audio with ElevenLabs."""

    def __init__(self, voice_id: str | None = None) -> None:
        self.voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", "CwhRBWXzGAHq8TQ4Fs17")
        self._client = None
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            logger.warning("ElevenLabs API key missing; narration disabled")
            return
        try:
            self._client = ElevenLabs(api_key=api_key)
        except Exception:
            logger.exception("Failed to initialize ElevenLabs client")

    async def narrate(self, text: str) -> bytes | None:
        if not text or self._client is None:
            return None
        try:
            return await asyncio.to_thread(self._synthesize_sync, text)
        except Exception:
            logger.exception("ElevenLabs synthesis failed")
            return None

    def _synthesize_sync(self, text: str) -> bytes | None:
        logger.info("ElevenLabs synthesizing %d chars with voice=%s", len(text), self.voice_id)
        audio_stream = self._client.text_to_speech.convert(
            voice_id=self.voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
            text=text,
        )
        chunks: list[bytes] = []
        for chunk in audio_stream:
            if isinstance(chunk, bytes):
                chunks.append(chunk)
        result = b"".join(chunks) if chunks else None
        logger.info("ElevenLabs returned %d bytes", len(result) if result else 0)
        return result
