"""Imzolangan tokenlar — stream va thumbnail URL'lari uchun.

Format: base64url(json) + "." + base64url(HMAC-SHA256). AVPlayer header
yubora olmaydi, shuning uchun ruxsat URL'ning o'zida bo'ladi.
"""

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from app.core.config import get_settings


class InvalidToken(Exception):
    """Token soxta, buzilgan yoki muddati o'tgan."""


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64d(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _key() -> bytes:
    # JWT kalitidan ajratilgan kalit — bitta sirr ikki joyda to'g'ridan-to'g'ri ishlatilmaydi
    return hashlib.sha256((get_settings().secret_key + ":media-url").encode()).digest()


def sign(payload: dict[str, Any], ttl_sec: int | None = None) -> str:
    body = dict(payload)
    if ttl_sec is not None:
        body["exp"] = int(time.time()) + ttl_sec
    raw = json.dumps(body, separators=(",", ":"), sort_keys=True).encode()
    mac = hmac.new(_key(), raw, hashlib.sha256).digest()
    return f"{_b64e(raw)}.{_b64e(mac)}"


def verify(token: str) -> dict[str, Any]:
    try:
        raw_b64, mac_b64 = token.split(".", 1)
        raw = _b64d(raw_b64)
        mac = _b64d(mac_b64)
    except (ValueError, TypeError) as e:
        raise InvalidToken("format") from e
    expected = hmac.new(_key(), raw, hashlib.sha256).digest()
    if not hmac.compare_digest(mac, expected):
        raise InvalidToken("signature")
    try:
        payload = json.loads(raw)
    except ValueError as e:
        raise InvalidToken("json") from e
    if not isinstance(payload, dict):
        raise InvalidToken("json")
    exp = payload.get("exp")
    if exp is not None and int(exp) < int(time.time()):
        raise InvalidToken("expired")
    return payload
