import time

import requests

from app.ai.gemini_http import GEMINI_API_URL, post_gemini
from app.ai.llm.models import LLMResponse
from app.core.config import settings
from app.core.exceptions import AIServiceUnavailableError
from app.observability.logger import get_logger


logger = get_logger(__name__)


BLOCKED_TEXT = "No puedo responder a esa solicitud."


class GeminiClient:
    """
    Client for Gemini's generateContent API, used for the public demo
    (``LLM_PROVIDER=gemini``). Mirrors OllamaClient: any provider failure
    (network, quota, invalid key) becomes AIServiceUnavailableError; see
    app.ai.gemini_http for retries and logging.
    """

    def generate(
        self,
        prompt: str,
    ) -> LLMResponse:
        started = time.perf_counter_ns()

        response = self._post_with_fallback(prompt)

        data = response.json()

        candidate = (data.get("candidates") or [{}])[0]

        # A blocked prompt returns no candidates, only promptFeedback.
        text = "".join(
            part.get("text", "")
            for part in candidate.get("content", {}).get("parts", [])
            if not part.get("thought")
        ).strip() or BLOCKED_TEXT

        usage = data.get("usageMetadata", {})

        return LLMResponse(
            text=text,
            model=data.get("modelVersion", ""),
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

    def _post_with_fallback(
        self,
        prompt: str,
    ) -> requests.Response:
        """
        Try the primary model and then each fallback. Preview models are
        often overloaded (503); another model usually still answers.
        """

        models = settings.gemini_llm_models
        last_error: AIServiceUnavailableError | None = None

        for model in models:
            try:
                return post_gemini(
                    f"{GEMINI_API_URL}/models/{model}:generateContent",
                    {
                        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "maxOutputTokens": settings.GEMINI_MAX_TOKENS,
                        },
                    },
                    timeout=settings.LLM_TIMEOUT_SECONDS,
                    unavailable_message="Language model service is unavailable",
                )

            except AIServiceUnavailableError as error:
                last_error = error

                if model != models[-1]:
                    logger.warning(
                        "Gemini model %s failed (%s); falling back to the next model",
                        model,
                        error,
                    )

        assert last_error is not None

        raise last_error
