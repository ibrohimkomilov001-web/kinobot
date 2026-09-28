"""Opaque pagination kursori — {"o": offset} ning base64url(JSON) kodlanishi.

docs/API.md namunasi (limit=24, birinchi sahifa) "eyJvIjoyNH0" ni beradi, bu
`base64url(json.dumps({"o":24}))` bilan bir xil — implementatsiya shu bilan
mos.
"""

from __future__ import annotations

import base64
import json


def encode_cursor(offset: int) -> str:
    raw = json.dumps({"o": offset}, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def decode_cursor(cursor: str | None) -> int:
    """Noto'g'ri/soxta kursor — 0 (birinchi sahifa) qaytaradi, xato otmaydi."""
    if not cursor:
        return 0
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        data = json.loads(raw)
        offset = int(data.get("o", 0))
        return offset if offset > 0 else 0
    except (ValueError, TypeError, KeyError, UnicodeDecodeError):
        return 0
