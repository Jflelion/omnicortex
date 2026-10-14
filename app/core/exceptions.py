class AIServiceUnavailableError(Exception):
    """
    Raised when an external AI provider (Ollama or Gemini) cannot be
    reached, times out, or returns an error response.
    """


class AIRateLimitError(AIServiceUnavailableError):
    """
    Raised when the AI provider rejects the request because the quota
    is exhausted (e.g. Gemini free tier, HTTP 429).
    """
