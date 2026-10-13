import requests

from app.core.config import settings
from app.core.exceptions import AIServiceUnavailableError
from app.ai.llm.models import LLMResponse


class OllamaClient:
    """
    Client responsible for communicating with Ollama.

    This class encapsulates every HTTP interaction with the Ollama API.
    The rest of the application should never call requests.post()
    directly.
    """

    def generate(
        self,
        prompt: str,
    ) -> LLMResponse:
        """
        Generate a completion from the configured language model.

        Args:
            prompt: Prompt sent to the language model.

        Returns:
            Normalized LLMResponse.
        """

        try:
            response = requests.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "keep_alive": settings.OLLAMA_KEEP_ALIVE,
                    "options": {
                        "num_predict": settings.LLM_MAX_TOKENS,
                    },
                },
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )

            response.raise_for_status()

        except requests.RequestException as error:
            raise AIServiceUnavailableError(
                "Language model service is unavailable"
            ) from error

        data = response.json()

        return LLMResponse(
            text=data["response"],
            model=data["model"],
            done_reason=data.get("done_reason", ""),
            total_duration_ns=data.get(
                "total_duration",
                0,
            ),
            load_duration_ns=data.get(
                "load_duration",
                0,
            ),
            prompt_eval_duration_ns=data.get(
                "prompt_eval_duration",
                0,
            ),
            eval_duration_ns=data.get(
                "eval_duration",
                0,
            ),
            prompt_eval_count=data.get(
                "prompt_eval_count",
                0,
            ),
            eval_count=data.get(
                "eval_count",
                0,
            ),
        )