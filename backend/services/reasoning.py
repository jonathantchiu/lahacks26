import logging
import os

import google.generativeai as genai

logger = logging.getLogger(__name__)


class ReasoningService:
    """Builds concise event summaries with Gemini."""

    def __init__(self, model_name: str = "gemma-4-26b-a4b-it") -> None:
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
                "Output ONLY a single short alert sentence, nothing else. No thinking, no reasoning, no bullet points, no markdown.\n"
                "You are a security camera analyst. Write one alert sentence (max 20 words) describing what you see in these frames.\n"
                "Mention what is happening and tie it to the camera context.\n"
                f"Camera context: {context or 'General monitoring'}\n"
                "Example output: ALERT: Two vehicles detected traveling northbound on Highway 101 during peak hours."
            )
            response = await self._model.generate_content_async([prompt, *parts])
            text = (response.text or "").strip()
            if text:
                first_line = text.split("\n")[0].strip()
                if first_line.startswith("*") or first_line.startswith("-"):
                    first_line = first_line.lstrip("*- ").strip()
                return first_line
            return self._fallback(context)
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
