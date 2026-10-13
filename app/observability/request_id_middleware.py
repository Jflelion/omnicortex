from time import perf_counter
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.observability.logger import get_logger
from app.observability.request_context import (
    reset_request_id,
    set_request_id,
)


logger = get_logger(__name__)


class RequestIdMiddleware:
    """
    Assign and propagate a unique identifier for every HTTP request.

    The middleware accepts an existing X-Request-ID header when provided by
    the client. Otherwise, it generates a new identifier. The value is stored
    in the current execution context and returned in the response headers.
    """

    def __init__(self, app: ASGIApp) -> None:
        """
        Initialize the middleware.

        Args:
            app: Wrapped ASGI application.
        """

        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """
        Process an incoming ASGI request.

        Args:
            scope: ASGI connection information.
            receive: ASGI receive callable.
            send: ASGI send callable.
        """

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)

        incoming_request_id = headers.get("x-request-id")
        request_id = (
            incoming_request_id.strip()
            if incoming_request_id
            else uuid4().hex[:12]
        )

        token = set_request_id(request_id)
        started_at = perf_counter()
        status_code = 500

        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")

        logger.info(
            "request_id=%s method=%s path=%s event=request_started",
            request_id,
            method,
            path,
        )

        async def send_with_request_id(message: Message) -> None:
            """
            Add the request identifier to the HTTP response.
            """

            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]

                response_headers = MutableHeaders(scope=message)
                response_headers["X-Request-ID"] = request_id

            await send(message)

        try:
            await self.app(
                scope,
                receive,
                send_with_request_id,
            )

        except Exception:
            logger.exception(
                (
                    "request_id=%s method=%s path=%s "
                    "event=request_failed"
                ),
                request_id,
                method,
                path,
            )
            raise

        finally:
            elapsed_ms = (
                perf_counter() - started_at
            ) * 1000

            logger.info(
                (
                    "request_id=%s method=%s path=%s "
                    "status_code=%s elapsed_ms=%.2f "
                    "event=request_finished"
                ),
                request_id,
                method,
                path,
                status_code,
                elapsed_ms,
            )

            reset_request_id(token)