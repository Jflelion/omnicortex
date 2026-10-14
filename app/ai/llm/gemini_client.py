import time

import requests

from app.ai.llm.models import LLMResponse
from app.core.config import settings
from app.core.exceptions import AIServiceUnavailableError
from app.observability.logger import get_logger


logger = get_logger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta"

BLOCKED_TEXT = "No puedo responder a esa solicitud."


class GeminiClient:
    """
    Client for Gemini's generateContent API, used for the public demo
    (``LLM_PROVIDER=gemini``). Mirrors OllamaClient: any provider failure
    (network, quota, invalid key) becomes AIServiceUnavailableError (503).
    """

    def generate(
        self,
        prompt: str,
    ) -> LLMResponse:
        started = time.perf_counter_ns()

        try:
            response = requests.post(
                f"{GEMINI_API_URL}/models/{settings.GEMINI_LLM_MODEL}:generateContent",
                headers={"x-goog-api-key": settings.GEMINI_API_KEY or ""},
                json={
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "maxOutputTokens": settings.GEMINI_MAX_TOKENS,
                    },
                },
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )

            response.raise_for_status()

        except requests.RequestException as error:
            logger.warning("Gemini API unavailable: %s", type(error).__name__)

            raise AIServiceUnavailableError(
                "Language model service is unavailable"
            ) from error

        data = response.json()

        candidate = (data.get("candidates") or [{}])[0]

        # A blocked prompt returns no candidates, only promptFeedback.
        text = "".join(
            part.get("text", "")
            for part in candidate.get("content", {}).get("parts", [])
        ).strip() or BLOCKED_TEXT

        usage = data.get("usageMetadata", {})

        return LLMResponse(
            text=text,
            model=data.get("modelVersion", settings.GEMINI_LLM_MODEL),
            done_reason=candidate.get(
                "finishReason",
                data.get("promptFeedback", {}).get("blockReason", ""),
            ),
            total_duration_ns=time.perf_counter_ns() - started,
            load_duration_ns=0,
            prompt_eval_duration_ns=0,
            eval_duration_ns=0,
            prompt_eval_count=usage.get("promptTokenCount", 0),
            eval_count=usage.get("candidatesTokenCount", 0),
        )
