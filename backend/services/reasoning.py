import logging
import os

import google.generativeai as genai

logger = logging.getLogger(__name__)


class ReasoningService:
    """Builds concise event summaries with Gemini."""

    def __init__(self, model_name: str = "gemini-1.5-flash") -> None:
        self.model_name = model_name
        self._model = None

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
        if not api_key:
            logger.warning("Gemini API key missing; reasoning will use fallback text")
            return
        try:
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(model_name)
            logger.info("Gemini reasoning initialized with model=%s", model_name)
        except Exception:
            logger.exception("Failed to initialize Gemini; reasoning will use fallback text")

    async def analyze_event(self, frames: list[bytes], context: str) -> str:
        if not frames or self._model is None:
            return self._fallback(context)

        try:
            sampled = self._sample_frames(frames, max_frames=6)
            parts = [{"mime_type": "image/jpeg", "data": f} for f in sampled]
            prompt = (
                "You are a security analyst. Describe what happened in <=40 words, mention who/what, "
                "and tie it to the camera context. Keep it direct and alarm-friendly.\n"
                f"Camera context: {context or 'General monitoring'}"
            )
            response = await self._model.generate_content_async([prompt, *parts])
            text = (response.text or "").strip()
            return text if text else self._fallback(context)
        except Exception:
            logger.exception("Gemini reasoning call failed")
            return self._fallback(context)

    @staticmethod
    def _sample_frames(frames: list[bytes], max_frames: int) -> list[bytes]:
        if len(frames) <= max_frames:
            return frames
        step = max(1, len(frames) // max_frames)
        sampled = frames[::step][:max_frames]
        return sampled

    @staticmethod
    def _fallback(context: str) -> str:
        if context:
            return f"Notable activity detected. Watch context: {context}."
        return "Notable activity detected."
