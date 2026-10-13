import requests

from app.ai.llm.models import LLMResponse


OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:3b"


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

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "30m",
                "options": {
                    "num_predict": 120,
                },
            },
            timeout=300,
        )

        response.raise_for_status()

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