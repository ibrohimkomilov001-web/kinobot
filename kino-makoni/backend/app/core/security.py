"""JWT access token — HS256, sub=user_id (docs/API.md)."""

from __future__ import annotations

import time

import jwt

from app.core.config import get_settings

ALGORITHM = "HS256"


class InvalidTokenError(Exception):
    """Token yaroqsiz, buzilgan yoki muddati o'tgan."""


def create_access_token(user_id: int) -> tuple[str, int]:
    """JWT va uning amal qilish muddatini (soniyada) qaytaradi."""
    settings = get_settings()
    ttl_sec = settings.access_token_ttl_days * 24 * 3600
    now = int(time.time())
    payload = {"sub": str(user_id), "iat": now, "exp": now + ttl_sec}
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    return token, ttl_sec


def decode_access_token(token: str) -> int:
    """Token ichidagi user_id'ni qaytaradi; yaroqsiz bo'lsa InvalidTokenError."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc
    sub = payload.get("sub")
    try:
        return int(sub)
    except (TypeError, ValueError) as exc:
        raise InvalidTokenError("sub noto'g'ri") from exc
