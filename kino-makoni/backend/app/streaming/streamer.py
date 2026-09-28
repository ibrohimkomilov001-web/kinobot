"""Stream orkestratori: metama'lumot keshi, Range bo'yicha yuklash, thumbnail.

Telegram'ga faqat MediaBackend orqali murojaat qiladi (testda soxtasi ulanadi).
"""

import asyncio
import logging
import os
from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TypeVar

import anyio

from app.streaming.backend import MediaBackend, MediaInfo, marked_channel_id
from app.streaming.cache import TTLCache
from app.streaming.errors import (
    BackendUnavailable,
    Busy,
    FileRefExpired,
    FloodWait,
    MediaNotFound,
    StreamBroken,
)
from app.streaming.ranges import ByteRange, normalize_request_size, plan_chunks

log = logging.getLogger("app.streaming")

T = TypeVar("T")

_CLEANUP_WAIT_SEC = 5.0


async def close_quietly(agen: object) -> None:
    """Async iterator'ni yopadi (bekor qilish paytida ham) — xatolar yutiladi."""
    aclose = getattr(agen, "aclose", None)
    if aclose is None:
        return
    with anyio.move_on_after(_CLEANUP_WAIT_SEC, shield=True):
        try:
            await aclose()
        except Exception:  # yopishdagi xato javobni buzmasin
            log.debug("iterator yopilmadi", exc_info=True)


def _read_file(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


class ByteStream:
    """Bitta HTTP javob tanasi. prefetch() birinchi bo'lakni oldindan oladi —
    shunda Telegram xatolari sarlavhalar yuborilmasdan HTTP status bo'lib qaytadi."""

    def __init__(self, gen: AsyncGenerator[bytes, None]) -> None:
        self._gen = gen
        self._pending: bytes | None = None
        self._closed = False

    async def prefetch(self) -> None:
        try:
            self._pending = await anext(self._gen)
        except StopAsyncIteration:
            self._pending = b""

    def __aiter__(self) -> AsyncIterator[bytes]:
        return self

    async def __anext__(self) -> bytes:
        if self._pending is not None:
            data, self._pending = self._pending, None
            if data:
                return data
        if self._closed:
            raise StopAsyncIteration
        return await anext(self._gen)

    async def aclose(self) -> None:
        """Idempotent: Telegram yuklashini to'xtatadi, resurslarni qaytaradi."""
        if self._closed:
            return
        self._closed = True
        self._pending = None
        await close_quietly(self._gen)


class Streamer:
    def __init__(
        self,
        backend: MediaBackend,
        *,
        channel_id: int,
        chunk_size: int = 512 * 1024,
        max_parallel: int = 16,
        queue_wait_sec: float = 15.0,
        chunk_wait_sec: float = 60.0,
        ready_wait_sec: float = 5.0,
        meta_ttl_sec: float = 30 * 60,
        meta_max: int = 2048,
        thumb_dir: Path | None = None,
        thumb_mem_max: int = 256,
        short_flood_sec: int = 10,
        flood_retries: int = 3,
        flood_min_sleep_sec: float = 1.0,
    ) -> None:
        self._backend = backend
        self._channel_id = marked_channel_id(channel_id)
        self._chunk_size = normalize_request_size(chunk_size)
        if self._chunk_size != chunk_size:
            log.warning(
                "TG_CHUNK_SIZE=%s MTProto'ga mos emas — %s ishlatiladi",
                chunk_size,
                self._chunk_size,
            )
        # Parallel upload.getFile so'rovlari soni (ochiq HTTP oqimlar emas: AVPlayer
        # buferi to'lganda oqim kutib turadi va slot band qilmaydi).
        self._slots = asyncio.Semaphore(max_parallel)
        self._queue_wait_sec = queue_wait_sec
        self._chunk_wait_sec = chunk_wait_sec
        self._ready_wait_sec = ready_wait_sec
        self._meta: TTLCache[int, MediaInfo] = TTLCache(meta_max, meta_ttl_sec)
        self._inflight: dict[int, asyncio.Task[MediaInfo]] = {}
        self._thumb_dir = thumb_dir
        self._thumbs: TTLCache[int, bytes] = TTLCache(thumb_mem_max, 24 * 3600)
        self._short_flood_sec = short_flood_sec
        self._flood_retries = flood_retries
        self._flood_min_sleep_sec = flood_min_sleep_sec

    # ---------- holat ----------

    @property
    def channel_id(self) -> int:
        return self._channel_id

    @property
    def chunk_size(self) -> int:
        return self._chunk_size

    @property
    def backend(self) -> MediaBackend:
        return self._backend

    def accepts_channel(self, channel_id: object) -> bool:
        if not isinstance(channel_id, int) or isinstance(channel_id, bool):
            return False
        return marked_channel_id(channel_id) == self._channel_id

    def is_connected(self) -> bool:
        return self._backend.is_ready()

    async def ensure_ready(self) -> None:
        if self._backend.is_ready():
            return
        if not await self._backend.wait_ready(self._ready_wait_sec):
            raise BackendUnavailable("Telegram ulanmagan")

    def start(self) -> None:
        self._backend.start()

    async def aclose(self) -> None:
        tasks = list(self._inflight.values())
        self._inflight.clear()
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        await self._backend.close()

    # ---------- umumiy yordamchilar ----------

    @asynccontextmanager
    async def _slot(self) -> AsyncIterator[None]:
        try:
            async with asyncio.timeout(self._queue_wait_sec):
                await self._slots.acquire()
        except TimeoutError:
            raise Busy("parallel so'rovlar limiti to'lgan") from None
        try:
            yield
        finally:
            self._slots.release()

    async def _with_flood_retry(self, fn: Callable[[], Awaitable[T]]) -> T:
        """Qisqa FLOOD_WAIT'da kutib qayta urinadi; uzuni FloodWait bo'lib chiqadi."""
        attempt = 0
        while True:
            try:
                return await fn()
            except FloodWait as e:
                if e.seconds > self._short_flood_sec or attempt >= self._flood_retries:
                    raise
                attempt += 1
                log.info("FLOOD_WAIT %ss — kutib qayta urinamiz", e.seconds)
                await asyncio.sleep(max(e.seconds, self._flood_min_sleep_sec))

    # ---------- metama'lumot ----------

    async def get_media(self, msg_id: int, *, refresh: bool = False) -> MediaInfo:
        """Kanal xabaridagi video. Kesh (LRU+TTL) va bir vaqtdagi so'rovlarni birlashtirish."""
        if msg_id <= 0:
            raise MediaNotFound(f"msg {msg_id}")
        if refresh:
            self._meta.pop(msg_id)
        else:
            cached = self._meta.get(msg_id)
            if cached is not None:
                return cached
        task = self._inflight.get(msg_id)
        if task is None:
            task = asyncio.get_running_loop().create_task(
                self._load_media(msg_id), name=f"tg-media-{msg_id}"
            )
            self._inflight[msg_id] = task
            task.add_done_callback(lambda t, key=msg_id: self._forget(key, t))
        # shield: bitta mijoz uzilsa ham boshqalar kutayotgan yuklash davom etadi
        return await asyncio.shield(task)

    def _forget(self, msg_id: int, task: asyncio.Task[MediaInfo]) -> None:
        if self._inflight.get(msg_id) is task:
            del self._inflight[msg_id]
        if not task.cancelled():
            task.exception()  # "exception was never retrieved" ogohlantirishiga qarshi

    async def _load_media(self, msg_id: int) -> MediaInfo:
        await self.ensure_ready()

        async def fetch() -> MediaInfo | None:
            async with self._slot():
                return await self._backend.fetch_media(msg_id)

        media = await self._with_flood_retry(fetch)
        if media is None:
            raise MediaNotFound(f"msg {msg_id}: video yo'q")
        self._meta.set(msg_id, media)
        return media

    # ---------- video oqimi ----------

    def open_stream(self, msg_id: int, media: MediaInfo, byte_range: ByteRange) -> ByteStream:
        return ByteStream(self._generate(msg_id, media, byte_range.start, byte_range.end))

    async def _next_chunk(self, chunks: AsyncGenerator[bytes, None]) -> bytes | None:
        async with self._slot():
            try:
                async with asyncio.timeout(self._chunk_wait_sec):
                    return await anext(chunks, None)
            except TimeoutError:
                raise BackendUnavailable("Telegram bo'lakni o'z vaqtida bermadi") from None

    async def _generate(
        self, msg_id: int, media: MediaInfo, start: int, end: int
    ) -> AsyncGenerator[bytes, None]:
        plan = plan_chunks(start, end, self._chunk_size)
        index = 0
        can_refresh = True
        floods_left = self._flood_retries
        while index < plan.count:
            chunks = self._backend.iter_chunks(
                media, plan.offset(index), plan.request_size, plan.count - index
            )
            try:
                while index < plan.count:
                    raw = await self._next_chunk(chunks)
                    if raw is None:
                        raise StreamBroken(f"msg {msg_id}: fayl kutilganidan qisqa")
                    try:
                        piece = plan.trim(index, raw)
                    except ValueError as e:
                        raise StreamBroken(f"msg {msg_id}: {e}") from None
                    index += 1
                    can_refresh = True
                    yield piece
            except FileRefExpired:
                if not can_refresh:
                    raise
                can_refresh = False
                log.info("msg %s: file_reference eskirgan — xabar qayta olinadi", msg_id)
                fresh = await self.get_media(msg_id, refresh=True)
                if (fresh.doc_id, fresh.size) != (media.doc_id, media.size):
                    raise StreamBroken(f"msg {msg_id}: xabardagi video almashgan") from None
                media = fresh
            except FloodWait as e:
                if e.seconds > self._short_flood_sec or floods_left <= 0:
                    raise
                floods_left -= 1
                log.info("msg %s: FLOOD_WAIT %ss — kutib davom etamiz", msg_id, e.seconds)
                await asyncio.sleep(max(e.seconds, self._flood_min_sleep_sec))
            finally:
                # mijoz uzilsa ham (CancelledError/GeneratorExit) Telegram yuklashi to'xtaydi
                await close_quietly(chunks)

    # ---------- thumbnail ----------

    def thumb_path(self, channel_id: int, msg_id: int) -> Path | None:
        if self._thumb_dir is None:
            return None
        return self._thumb_dir / f"{marked_channel_id(channel_id)}_{msg_id}.jpg"

    async def get_thumb(self, channel_id: int, msg_id: int) -> bytes:
        cached = self._thumbs.get(msg_id)
        if cached is not None:
            return cached
        path = self.thumb_path(channel_id, msg_id)
        if path is not None:
            data = await asyncio.to_thread(_read_file, path)
            if data:
                self._thumbs.set(msg_id, data)
                return data

        media = await self.get_media(msg_id)
        if media.thumb is None:
            raise MediaNotFound(f"msg {msg_id}: thumbnail yo'q")
        data = await self._download_thumb(msg_id, media)
        if not data:
            raise MediaNotFound(f"msg {msg_id}: thumbnail bo'sh")

        self._thumbs.set(msg_id, data)
        if path is not None:
            try:
                await asyncio.to_thread(_write_atomic, path, data)
            except OSError:
                log.warning("thumbnail diskka yozilmadi: %s", path, exc_info=True)
        return data

    async def _download_thumb(self, msg_id: int, media: MediaInfo) -> bytes | None:
        current = media

        async def download() -> bytes | None:
            async with self._slot():
                return await self._backend.download_thumb(current)

        try:
            return await self._with_flood_retry(download)
        except FileRefExpired:
            current = await self.get_media(msg_id, refresh=True)
            try:
                return await self._with_flood_retry(download)
            except FileRefExpired:
                raise StreamBroken(f"msg {msg_id}: file_reference yangilanmadi") from None
