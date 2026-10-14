"""
Shared HTTP call to the Gemini API with retries and useful error logs.

The free tier fails often and transiently (429 rate limit, 503 overloaded),
so both the LLM and the embedding clients go through ``post_gemini``:

- Retries 429/500/503 and network errors with a short backoff, honouring
  the ``retryDelay`` Google sends, unless that delay is too long to wait
  inside a request.
- Logs the HTTP status and Google's error message (never the API key), so
  the real cause is visible in the server logs.
- Raises ``AIRateLimitError`` for quota errors and
  ``AIServiceUnavailableError`` for everything else.
"""

import re
import time
from typing import Any

import requests

from app.core.config import settings
from app.core.exceptions import AIRateLimitError, AIServiceUnavailableError
from app.observability.logger import get_logger


logger = get_logger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta"

RETRYABLE_STATUS_CODES = {429, 500, 503}

# Base backoff between attempts: 1s, 2s, 4s...
BACKOFF_SECONDS = 1.0

# Longer suggested waits are not worth holding the HTTP request open for.
MAX_RETRY_WAIT_SECONDS = 8.0


def post_gemini(
    url: str,
    payload: dict[str, Any],
    timeout: float,
    unavailable_message: str
) -> requests.Response:
    """
    POST to the Gemini API, retrying transient failures.

    Args:
        url: Full Gemini endpoint URL.
        payload: JSON body.
        timeout: Per-attempt timeout in seconds.
        unavailable_message: Message for the raised exception.

    Raises:
        AIRateLimitError: The quota is exhausted (HTTP 429).
        AIServiceUnavailableError: Any other provider failure.
    """

    attempts = settings.GEMINI_MAX_RETRIES + 1

    for attempt in range(1, attempts + 1):
        try:
            response = requests.post(
                url,
                headers={"x-goog-api-key": settings.GEMINI_API_KEY or ""},
                json=payload,
                timeout=timeout,
            )

            response.raise_for_status()

            return response

        except requests.HTTPError as error:
            status_code, reason, retry_after = _describe_http_error(error)

            logger.warning(
                "Gemini API error: status=%s attempt=%s/%s reason=%s",
                status_code,
                attempt,
                attempts,
                reason,
            )

            retryable = status_code in RETRYABLE_STATUS_CODES
            last_error: Exception = error

        except (requests.ConnectionError, requests.Timeout) as error:
            logger.warning(
                "Gemini API unreachable: %s attempt=%s/%s",
                type(error).__name__,
                attempt,
                attempts,
            )

            status_code = None
            retry_after = None
            retryable = True
            last_error = error

        except requests.RequestException as error:
            logger.warning("Gemini API request failed: %s", type(error).__name__)

            status_code = None
            retry_after = None
            retryable = False
            last_error = error

        wait = (
            retry_after
            if retry_after is not None
            else BACKOFF_SECONDS * 2 ** (attempt - 1)
        )

        if not retryable or attempt == attempts or wait > MAX_RETRY_WAIT_SECONDS:
            break

        time.sleep(wait)

    if status_code == 429:
        raise AIRateLimitError(
            "The AI provider's free quota is exhausted"
        ) from last_error

    raise AIServiceUnavailableError(unavailable_message) from last_error


def _describe_http_error(
    error: requests.HTTPError
) -> tuple[int | None, str, float | None]:
    """
    Extract status code, Google's error message and suggested retry delay.
    """

    response = error.response

    if response is None:
        return None, str(error), None

    status_code = response.status_code
    reason = response.reason or ""
    retry_after: float | None = None

    try:
        body = response.json().get("error", {})
        reason = f"{body.get('status', '')}: {body.get('message', '')}"[:300]

        for detail in body.get("details", []):
            delay = detail.get("retryDelay")

            if isinstance(delay, str):
                match = re.fullmatch(r"(\d+(?:\.\d+)?)s", delay)

                if match:
                    retry_after = float(match.group(1))

    except (ValueError, AttributeError):
        pass

    header = response.headers.get("Retry-After")

    if retry_after is None and header and header.isdigit():
        retry_after = float(header)

    return status_code, reason, retry_after
