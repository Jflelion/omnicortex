class AIServiceUnavailableError(Exception):
    """
    Raised when an external AI provider (Ollama) cannot be reached,
    times out, or returns an error response.
    """
