"""Password hashing (argon2 via pwdlib) and JWT access tokens (PyJWT)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

_password_hash = PasswordHash.recommended()  # Argon2, pwdlib's current recommendation

TOKEN_TYPE = "access"  # noqa: S105 - a JWT "typ" claim value, not a credential


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _password_hash.verify(password, password_hash)


class InvalidTokenError(ValueError):
    """The token is malformed, expired, or not one this service issued."""


@dataclass(frozen=True)
class TokenPayload:
    user_id: uuid.UUID
    expires_at: datetime


def create_access_token(user_id: uuid.UUID) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.jwt_access_ttl_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": TOKEN_TYPE,
        "iat": now,
        "exp": expires_at,
    }
    return jwt.encode(
        payload, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> TokenPayload:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key.get_secret_value(), algorithms=[settings.jwt_algorithm]
        )
    except jwt.PyJWTError as error:
        raise InvalidTokenError(str(error)) from error

    if payload.get("type") != TOKEN_TYPE:
        raise InvalidTokenError("Not an access token")
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as error:
        raise InvalidTokenError("Token subject is not a valid user id") from error

    return TokenPayload(user_id=user_id, expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC))
