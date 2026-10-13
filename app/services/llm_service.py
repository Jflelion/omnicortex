from app.ai.llm import LLMService


_service = LLMService()


def generate_answer(prompt: str) -> str:
    """
    Temporary compatibility layer.

    This function preserves the current public API while the
    application is migrated to the new AI architecture.
    """

    response = _service.generate(prompt)

    return response.text