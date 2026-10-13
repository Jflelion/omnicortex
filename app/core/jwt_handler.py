from typing import Any

from jwt import decode as jwt_decode
from jwt import encode as jwt_encode


def encode_jwt(
    payload: dict[str, Any],
    secret_key: str,
    algorithm: str
) -> str:
    token = jwt_encode(
        payload=payload,
        key=secret_key,
        algorithm=algorithm
    )

    if isinstance(token, str):
        return token

    return bytes(token).decode("utf-8")


def decode_jwt(
    token: str,
    secret_key: str,
    algorithms: list[str]
) -> dict[str, Any]:
    payload = jwt_decode(
        jwt=token,
        key=secret_key,
        algorithms=algorithms
    )

    return payload