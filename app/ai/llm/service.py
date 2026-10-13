from app.ai.llm.client import OllamaClient
from app.ai.llm.models import LLMResponse


class LLMService:
    """
    High-level language model service.

    This service contains business logic related to language models.
    It delegates provider-specific communication to an LLM client.
    """

    def __init__(self) -> None:
        self._client = OllamaClient()

    def generate(
        self,
        prompt: str,
    ) -> LLMResponse:
        """
        Generate a response from the configured LLM.

        Args:
            prompt: Prompt sent to the language model.

        Returns:
            Normalized language model response.
        """

        return self._client.generate(prompt)