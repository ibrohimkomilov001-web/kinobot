"""Stream modulining hayot sikli: start/stop/is_connected (app/main.py lifespan)."""

import logging
from pathlib import Path

from app.core.config import Settings, get_settings
from app.streaming.backend import MediaBackend
from app.streaming.streamer import Streamer

log = logging.getLogger("app.streaming")

_streamer: Streamer | None = None


def _create_backend(settings: Settings) -> MediaBackend:
    # Telethon importi shu yerda — testlar uni almashtira oladi
    from app.streaming.telegram import TelethonBackend

    return TelethonBackend(settings)


def build_streamer(settings: Settings, backend: MediaBackend) -> Streamer:
    return Streamer(
        backend,
        channel_id=settings.tg_base_channel_id,
        chunk_size=settings.tg_chunk_size,
        thumb_dir=Path(settings.tg_session_dir) / "thumbs",
    )


async def start() -> None:
    """Hech qachon xato otmaydi: Telegram sozlanmagan/ulanmasa endpointlar 503 beradi."""
    global _streamer
    if _streamer is not None:
        return
    try:
        settings = get_settings()
        if not settings.telegram_enabled:
            log.warning(
                "Telegram sozlanmagan (TG_API_ID, TG_API_HASH, TG_HELPER_BOT_TOKEN, "
                "TG_BASE_CHANNEL_ID) — /v1/stream va /v1/thumb 503 qaytaradi"
            )
            return
        streamer = build_streamer(settings, _create_backend(settings))
        streamer.start()  # fonda ulanadi, qayta urinishlar backoff bilan
    except Exception:
        log.exception("Stream modulini ishga tushirib bo'lmadi")
        return
    _streamer = streamer


async def stop() -> None:
    global _streamer
    streamer, _streamer = _streamer, None
    if streamer is None:
        return
    try:
        await streamer.aclose()
    except Exception:
        log.exception("Stream modulini to'xtatishda xato")


def is_connected() -> bool:
    return _streamer is not None and _streamer.is_connected()


def current() -> Streamer | None:
    return _streamer


def install(streamer: Streamer | None) -> None:
    """Tayyor Streamer'ni o'rnatadi (testlar va maxsus ishga tushirish uchun)."""
    global _streamer
    _streamer = streamer
