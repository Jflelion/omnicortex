import time

import anthropic

from app.ai.llm.models import LLMResponse
from app.core.config import settings
from app.core.exceptions import AIServiceUnavailableError
from app.observability.logger import get_logger


logger = get_logger(__name__)

REFUSAL_TEXT = "No puedo responder a esa solicitud."


class AnthropicClient:
    """
    Client for Claude through the Anthropic API, used for the public demo
    (``LLM_PROVIDER=anthropic``). Mirrors OllamaClient: provider errors that
    make the service unusable become AIServiceUnavailableError (HTTP 503).
    """

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )

    def generate(
        self,
        prompt: str,
    ) -> LLMResponse:
        started = time.perf_counter_ns()

        try:
            response = self._client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=settings.ANTHROPIC_MAX_TOKENS,
                # Short, grounded answers: low effort keeps latency and
                # cost down.
                output_config={"effort": settings.ANTHROPIC_EFFORT},
                messages=[{"role": "user", "content": prompt}],
            )

        except (
            anthropic.APIConnectionError,
            anthropic.RateLimitError,
            anthropic.AuthenticationError,
            anthropic.PermissionDeniedError,
            anthropic.InternalServerError,
        ) as error:
            logger.warning("Anthropic API unavailable: %s", type(error).__name__)

            raise AIServiceUnavailableError(
                "Language model service is unavailable"
            ) from error

        if response.stop_reason == "refusal":
            text = REFUSAL_TEXT
        else:
            text = "".join(
                block.text
                for block in response.content
                if block.type == "text"
            ).strip()

        return LLMResponse(
            text=text,
            model=response.model,
            done_reason=response.stop_reason or "",
            total_duration_ns=time.perf_counter_ns() - started,
            load_duration_ns=0,
            prompt_eval_duration_ns=0,
            eval_duration_ns=0,
            prompt_eval_count=response.usage.input_tokens,
            eval_count=response.usage.output_tokens,
        )
