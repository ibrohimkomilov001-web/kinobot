"""Telegram MTProto orqali video stream (HTTP Range bilan).

Tashqi interfeys (app/main.py shularni ishlatadi):
- router — /v1/stream/{token}/{filename}, /v1/thumb/{token}/poster.jpg
- start() / stop() — lifespan'da MTProto klientni ulash/uzish
- is_connected() — /health uchun
"""

from app.streaming.router import router
from app.streaming.service import is_connected, start, stop

__all__ = ["is_connected", "router", "start", "stop"]
