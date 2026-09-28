"""Telegram bilan ishlash interfeysi (testlarda soxta backend ulanadi).

Streamer faqat shu interfeysni biladi; Telethon tafsilotlari telegram.py'da.
"""

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Protocol

_CHANNEL_MARK = 10**12  # Bot API/Telethon: -100XXXXXXXXXX = -(10^12 + XXXXXXXXXX)


def marked_channel_id(channel_id: int) -> int:
    """Kanal id'ni "-100..." ko'rinishiga keltiradi (musbat xom id ham qabul qilinadi)."""
    return channel_id if channel_id < 0 else -(_CHANNEL_MARK + channel_id)


def bare_channel_id(channel_id: int) -> int:
    """-1001234567890 → 1234567890 (MTProto'dagi haqiqiy id)."""
    if channel_id > 0:
        return channel_id
    raw = -channel_id
    if raw <= _CHANNEL_MARK:
        raise ValueError(f"{channel_id} kanal id emas (-100 bilan boshlanishi kerak)")
    return raw - _CHANNEL_MARK


@dataclass(frozen=True, slots=True)
class ThumbInfo:
    """Hujjatning eng katta JPEG thumbnail'i."""

    type: str  # PhotoSize.type ("m", "x", ...) — yuklash uchun thumb_size
    size: int
    width: int = 0
    height: int = 0
    inline: bytes | None = None  # PhotoCachedSize: baytlar xabarning o'zida


@dataclass(frozen=True, slots=True)
class MediaInfo:
    """Kanal xabaridagi video hujjat metama'lumoti (yuklash uchun yetarli)."""

    msg_id: int
    doc_id: int
    access_hash: int
    file_reference: bytes
    dc_id: int
    size: int
    mime_type: str | None = None
    duration: float | None = None
    width: int | None = None
    height: int | None = None
    file_name: str | None = None
    supports_streaming: bool = False
    caption: str = ""
    thumb: ThumbInfo | None = None


class MediaBackend(Protocol):
    """Telegram'ga kirish. Xatolar app.streaming.errors turlarida bo'lishi kerak."""

    def start(self) -> None:
        """Fonda ulanishni boshlaydi (bloklamaydi, xato otmaydi)."""

    async def close(self) -> None:
        """Ulanishni to'xtatadi."""

    def is_ready(self) -> bool:
        """Ulangan, bot kirgan va kanal aniqlangan."""

    async def wait_ready(self, wait_sec: float) -> bool:
        """Tayyor bo'lishini `wait_sec` gacha kutadi."""

    async def fetch_media(self, msg_id: int) -> MediaInfo | None:
        """Baza kanal xabarini olib video metama'lumotini qaytaradi (video yo'q → None)."""

    def iter_chunks(
        self, media: MediaInfo, offset: int, request_size: int, count: int
    ) -> AsyncGenerator[bytes, None]:
        """upload.getFile(offset + i*request_size, request_size) natijalari, i < count.

        Oxirgi bo'lak fayl oxirida qisqaroq bo'lishi mumkin. Chaqiruvchi aclose() qiladi.
        """

    async def download_thumb(self, media: MediaInfo) -> bytes | None:
        """media.thumb baytlarini yuklaydi (yo'q bo'lsa None)."""
