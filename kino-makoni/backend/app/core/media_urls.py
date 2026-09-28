"""Stream va thumbnail URL'larini yasash — YAGONA joy (docs/API.md)."""

from datetime import UTC, datetime

from app.core import signing
from app.core.config import get_settings


def telegram_stream_url(channel_id: int, msg_id: int) -> tuple[str, datetime]:
    """Kanal xabaridagi video uchun vaqtinchalik stream URL va muddati."""
    s = get_settings()
    token = signing.sign(
        {"v": 1, "src": "tg", "ch": channel_id, "msg": msg_id},
        ttl_sec=s.playback_url_ttl_sec,
    )
    expires_at = datetime.fromtimestamp(signing.verify(token)["exp"], tz=UTC)
    return f"{s.stream_base_url}/v1/stream/{token}/video.mp4", expires_at


def telegram_thumb_url(channel_id: int, msg_id: int) -> str:
    """Video thumbnail'i uchun muddatsiz URL (kesh qilinadi)."""
    token = signing.sign({"v": 1, "src": "tg-thumb", "ch": channel_id, "msg": msg_id})
    return f"{get_settings().api_base_url}/v1/thumb/{token}/poster.jpg"
