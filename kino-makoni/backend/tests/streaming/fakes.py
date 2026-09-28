"""Soxta Telegram backend: xotiradagi baytlar + MTProto upload.getFile cheklovlari."""

import asyncio
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field

from app.streaming.backend import MediaInfo, ThumbInfo
from app.streaming.errors import BackendUnavailable, FileRefExpired, FloodWait

MIB = 1024 * 1024


class ConstraintViolation(AssertionError):
    """Streamer MTProto cheklovini buzdi."""


def check_get_file(offset: int, limit: int, size: int) -> None:
    """upload.getFile (precise=False) qoidalari — buzilsa xato."""
    if offset % 4096:
        raise ConstraintViolation(f"offset {offset} 4096 ga karrali emas")
    if limit <= 0 or limit % 4096:
        raise ConstraintViolation(f"limit {limit} 4096 ga karrali emas")
    if MIB % limit:
        raise ConstraintViolation(f"1 MiB limit {limit} ga bo'linmaydi")
    if limit > 512 * 1024:
        raise ConstraintViolation(f"limit {limit} > 512 KiB")
    if offset // MIB != (offset + limit - 1) // MIB:
        raise ConstraintViolation(f"so'rov {offset}+{limit} 1 MiB chegarasini kesadi")
    if offset >= size:
        raise ConstraintViolation(f"offset {offset} fayl hajmidan ({size}) tashqarida")


_BLOCK = bytes((i * 131 + (i >> 8) * 7) & 0xFF for i in range(65521))  # tub uzunlik


def pattern_bytes(size: int, seed: int = 0) -> bytes:
    """Deterministik baytlar: 4096/64K chegaralarida takrorlanmaydi (bo'lak siljishi sezilsin)."""
    shift = seed % len(_BLOCK)
    block = _BLOCK[shift:] + _BLOCK[:shift]
    return (block * (size // len(block) + 1))[:size]


@dataclass
class FakeFile:
    data: bytes
    mime: str | None = "video/mp4"
    thumb: bytes | None = None
    doc_id: int = 1000


@dataclass
class FakeBackend:
    files: dict[int, FakeFile] = field(default_factory=dict)
    ready: bool = True
    delay: float = 0.0  # har bir bo'lak oldidan kutish (uzilish testlari uchun)
    requests: list[tuple[int, int]] = field(default_factory=list)
    fetch_calls: int = 0
    thumb_calls: int = 0
    open_iterators: int = 0
    closed_iterators: int = 0
    ref_version: int = 1  # joriy file_reference; eskisi bilan so'rov → FileRefExpired
    expire_after_requests: int | None = None  # N-so'rovdan keyin ref eskiradi
    flood_once: int | None = None  # birinchi getFile'da FloodWait(seconds)
    flood_on_fetch: int | None = None
    fail_unavailable: bool = False
    started: bool = False
    closed: bool = False

    def add(self, msg_id: int, data: bytes, **kw: object) -> FakeFile:
        f = FakeFile(data, **kw)  # type: ignore[arg-type]
        self.files[msg_id] = f
        return f

    # ----- MediaBackend -----

    def start(self) -> None:
        self.started = True

    async def close(self) -> None:
        self.closed = True

    def is_ready(self) -> bool:
        return self.ready

    async def wait_ready(self, wait_sec: float) -> bool:
        return self.ready

    def _media(self, msg_id: int, f: FakeFile) -> MediaInfo:
        thumb = ThumbInfo("m", len(f.thumb), 320, 180) if f.thumb else None
        return MediaInfo(
            msg_id=msg_id,
            doc_id=f.doc_id,
            access_hash=42,
            file_reference=f"ref{self.ref_version}".encode(),
            dc_id=2,
            size=len(f.data),
            mime_type=f.mime,
            thumb=thumb,
        )

    async def fetch_media(self, msg_id: int) -> MediaInfo | None:
        self.fetch_calls += 1
        await asyncio.sleep(0)
        if self.flood_on_fetch is not None:
            seconds, self.flood_on_fetch = self.flood_on_fetch, None
            raise FloodWait(seconds)
        f = self.files.get(msg_id)
        return self._media(msg_id, f) if f else None

    def _check_ref(self, media: MediaInfo) -> None:
        if media.file_reference != f"ref{self.ref_version}".encode():
            raise FileRefExpired("eski file_reference")

    async def iter_chunks(
        self, media: MediaInfo, offset: int, request_size: int, count: int
    ) -> AsyncGenerator[bytes, None]:
        self.open_iterators += 1
        try:
            f = self.files[media.msg_id]
            for i in range(count):
                off = offset + i * request_size
                check_get_file(off, request_size, len(f.data))
                if self.delay:
                    await asyncio.sleep(self.delay)
                else:
                    await asyncio.sleep(0)
                if self.fail_unavailable:
                    raise BackendUnavailable("soxta uzilish")
                if self.flood_once is not None:
                    seconds, self.flood_once = self.flood_once, None
                    raise FloodWait(seconds)
                if (
                    self.expire_after_requests is not None
                    and len(self.requests) >= self.expire_after_requests
                ):
                    self.expire_after_requests = None
                    self.ref_version += 1
                self._check_ref(media)
                self.requests.append((off, request_size))
                chunk = f.data[off : off + request_size]
                yield chunk
                if len(chunk) < request_size:
                    return
        finally:
            self.open_iterators -= 1
            self.closed_iterators += 1

    async def download_thumb(self, media: MediaInfo) -> bytes | None:
        self.thumb_calls += 1
        self._check_ref(media)
        f = self.files.get(media.msg_id)
        return f.thumb if f else None
