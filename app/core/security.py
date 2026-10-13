from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any
from app.core.config import settings
from passlib.context import CryptContext

from app.core.jwt_handler import decode_jwt, encode_jwt


settings.SECRET_KEY
settings.ALGORITHM
settings.ACCESS_TOKEN_EXPIRE_MINUTES


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


def create_access_token(
    data: Mapping[str, Any]
) -> str:
    to_encode = dict(data)

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return encode_jwt(
        payload=to_encode,
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def decode_access_token(
    token: str
) -> dict[str, Any] | None:
    try:
        return decode_jwt(
            token=token,
            secret_key=settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

    except Exception:
        return None