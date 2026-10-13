from contextvars import ContextVar, Token


_request_id_context: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)


def set_request_id(request_id: str) -> Token[str | None]:
    """
    Store the request identifier in the current execution context.

    Args:
        request_id: Unique identifier assigned to the HTTP request.

    Returns:
        Token used to restore the previous context value.
    """

    return _request_id_context.set(request_id)


def get_request_id() -> str | None:
    """
    Return the request identifier for the current execution context.

    Returns:
        Current request identifier, or None outside an HTTP request.
    """

    return _request_id_context.get()


def reset_request_id(token: Token[str | None]) -> None:
    """
    Restore the previous request identifier context.

    Args:
        token: Context token returned by set_request_id.
    """

    _request_id_context.reset(token)