import asyncio
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI

from app.core.config import Settings
from app.streaming import router as streaming_router
from app.streaming import service
from app.streaming.cache import TTLCache
from app.streaming.errors import Busy, FileRefExpired, MediaNotFound, StreamBroken
from app.streaming.ranges import ByteRange
from app.streaming.streamer import Streamer
from tests.streaming.conftest import CHANNEL, CHUNK, stream_token
from tests.streaming.fakes import FakeBackend, pattern_bytes

DATA = pattern_bytes(10 * CHUNK + 777, seed=9)


def make_streamer(backend: FakeBackend, **kw: Any) -> Streamer:
    kw.setdefault("flood_min_sleep_sec", 0.01)
    return Streamer(backend, channel_id=CHANNEL, chunk_size=CHUNK, **kw)


async def read_all(streamer: Streamer, msg: int, start: int, end: int) -> bytes:
    media = await streamer.get_media(msg)
    stream = streamer.open_stream(msg, media, ByteRange(start, end))
    try:
        await stream.prefetch()
        return b"".join([c async for c in stream])
    finally:
        await stream.aclose()


async def test_file_reference_refresh_mid_stream() -> None:
    backend = FakeBackend(expire_after_requests=3)
    backend.add(1, DATA)
    streamer = make_streamer(backend)
    body = await read_all(streamer, 1, 100, len(DATA) - 1)
    assert body == DATA[100:]
    assert backend.fetch_calls == 2  # xabar bir marta qayta olindi
    offsets = [off for off, _ in backend.requests]
    assert offsets == [i * CHUNK for i in range(len(offsets))]  # takror/bo'shliq yo'q
    assert backend.open_iterators == 0


async def test_file_reference_refresh_gives_up_without_progress() -> None:
    backend = FakeBackend(expire_after_requests=0)
    backend.add(1, DATA)
    streamer = make_streamer(backend)
    media = await streamer.get_media(1)
    stale = media

    async def stale_fetch(msg_id: int) -> Any:
        backend.fetch_calls += 1
        return stale  # yangilangan xabar ham eski ref qaytaradi

    backend.fetch_media = stale_fetch  # type: ignore[method-assign]
    stream = streamer.open_stream(1, media, ByteRange(0, 10))
    with pytest.raises(FileRefExpired):
        await stream.prefetch()
    await stream.aclose()
    assert backend.open_iterators == 0


async def test_document_changed_on_refresh() -> None:
    backend = FakeBackend(expire_after_requests=1)
    f = backend.add(1, DATA)
    streamer = make_streamer(backend)
    media = await streamer.get_media(1)
    f.doc_id = 999  # xabar tahrirlanib video almashgan
    stream = streamer.open_stream(1, media, ByteRange(0, len(DATA) - 1))
    await stream.prefetch()
    with pytest.raises(StreamBroken):
        async for _ in stream:
            pass
    await stream.aclose()
    assert backend.open_iterators == 0


async def test_short_flood_wait_is_retried() -> None:
    backend = FakeBackend(flood_once=0)
    backend.add(1, DATA)
    streamer = make_streamer(backend)
    assert await read_all(streamer, 1, 0, len(DATA) - 1) == DATA


async def test_short_flood_on_metadata_is_retried() -> None:
    backend = FakeBackend(flood_on_fetch=0)
    backend.add(1, DATA)
    streamer = make_streamer(backend)
    assert (await streamer.get_media(1)).size == len(DATA)
    assert backend.fetch_calls == 2


async def test_get_media_singleflight_and_not_found() -> None:
    backend = FakeBackend()
    backend.add(1, DATA)
    streamer = make_streamer(backend)
    results = await asyncio.gather(*(streamer.get_media(1) for _ in range(10)))
    assert {r.doc_id for r in results} == {1000}
    assert backend.fetch_calls == 1
    with pytest.raises(MediaNotFound):
        await streamer.get_media(2)
    with pytest.raises(MediaNotFound):
        await streamer.get_media(0)


async def test_parallel_limit_busy() -> None:
    backend = FakeBackend(delay=0.3)
    backend.add(1, DATA)
    streamer = make_streamer(backend, max_parallel=1, queue_wait_sec=0.05)
    media = await streamer.get_media(1)
    first = streamer.open_stream(1, media, ByteRange(0, 10))
    second = streamer.open_stream(1, media, ByteRange(0, 10))
    task = asyncio.create_task(first.prefetch())
    await asyncio.sleep(0.05)
    with pytest.raises(Busy):
        await second.prefetch()
    await task
    await first.aclose()
    await second.aclose()
    assert backend.open_iterators == 0


async def test_close_after_prefetch_stops_download() -> None:
    backend = FakeBackend()
    backend.add(1, DATA)
    streamer = make_streamer(backend)
    media = await streamer.get_media(1)
    stream = streamer.open_stream(1, media, ByteRange(0, len(DATA) - 1))
    await stream.prefetch()
    assert backend.open_iterators == 1
    await stream.aclose()
    await stream.aclose()  # idempotent
    assert backend.open_iterators == 0
    assert len(backend.requests) == 1


@pytest.mark.parametrize("phase", ["during_fetch", "during_send"])
async def test_client_disconnect_stops_telegram_download(backend: FakeBackend, phase: str) -> None:
    """Haqiqiy ASGI oqimi (uvicorn kabi spec 2.3): mijoz oqim o'rtasida uziladi.

    during_fetch — uzilish Telegram bo'lagini kutayotganda;
    during_send — javob yuborish to'xtab qolganda (TCP backpressure): generator
    yield'da osilib qoladi, uni faqat TelegramStreamResponse yopadi.
    """
    backend.add(5, DATA)
    backend.delay = 0.05
    streamer = make_streamer(backend)
    service.install(streamer)
    app = FastAPI()
    app.include_router(streaming_router)

    disconnect = asyncio.Event()
    sent: list[dict[str, Any]] = []
    request_sent = False
    bodies = 0

    async def receive() -> dict[str, Any]:
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await disconnect.wait()
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        nonlocal bodies
        sent.append(message)
        if message["type"] == "http.response.body" and message.get("body"):
            bodies += 1
            if phase == "during_fetch":
                disconnect.set()
            elif bodies == 2:
                disconnect.set()
                await asyncio.Event().wait()  # mijoz o'qimayapti — send abadiy kutadi

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": f"/v1/stream/{stream_token(5)}/video.mp4",
        "raw_path": b"",
        "root_path": "",
        "query_string": b"",
        "headers": [(b"host", b"test")],
        "client": ("127.0.0.1", 1234),
        "server": ("test", 80),
    }
    tasks_before = asyncio.all_tasks()
    try:
        await asyncio.wait_for(app(scope, receive, send), timeout=5)
    finally:
        service.install(None)

    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 200
    assert backend.open_iterators == 0  # Telegram iteratori yopildi
    total_chunks = len(DATA) // CHUNK + 1
    await asyncio.sleep(0.2)
    assert len(backend.requests) < total_chunks  # yuklash to'xtadi
    requests_after = len(backend.requests)
    await asyncio.sleep(0.2)
    assert len(backend.requests) == requests_after
    leaked = asyncio.all_tasks() - tasks_before
    assert not leaked, leaked


def test_ttl_cache_expiry_and_lru() -> None:
    now = [0.0]
    cache: TTLCache[int, str] = TTLCache(2, 10.0, clock=lambda: now[0])
    cache.set(1, "a")
    cache.set(2, "b")
    assert cache.get(1) == "a"  # 1 endi eng yangi
    cache.set(3, "c")  # 2 chiqariladi
    assert cache.get(2) is None and cache.get(1) == "a" and cache.get(3) == "c"
    now[0] = 11.0
    assert cache.get(1) is None and len(cache) == 1


def test_chunk_size_normalized() -> None:
    streamer = Streamer(FakeBackend(), channel_id=CHANNEL, chunk_size=1_000_000)
    assert streamer.chunk_size == 512 * 1024


# ---------- service: start/stop/is_connected ----------


def _settings(tmp_path: Path, **kw: Any) -> Settings:
    base: dict[str, Any] = {
        "tg_api_id": 1,
        "tg_api_hash": "hash",
        "tg_helper_bot_token": "123:abc",
        "tg_base_channel_id": CHANNEL,
        "tg_session_dir": str(tmp_path),
    }
    base.update(kw)
    return Settings(_env_file=None, **base)


async def test_start_disabled_stays_disconnected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(service, "get_settings", lambda: _settings(tmp_path, tg_api_id=0))
    created: list[object] = []
    monkeypatch.setattr(service, "_create_backend", lambda s: created.append(s))
    await service.start()
    assert service.current() is None
    assert service.is_connected() is False
    assert created == []
    assert "Telegram sozlanmagan" in caplog.text
    await service.stop()


async def test_start_stop_with_backend(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = FakeBackend()
    monkeypatch.setattr(service, "get_settings", lambda: _settings(tmp_path))
    monkeypatch.setattr(service, "_create_backend", lambda s: fake)
    try:
        await service.start()
        assert fake.started
        assert service.is_connected() is True
        streamer = service.current()
        assert streamer is not None and streamer.channel_id == CHANNEL
        fake.ready = False
        assert service.is_connected() is False
    finally:
        await service.stop()
    assert fake.closed
    assert service.current() is None


async def test_start_never_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def boom(settings: Settings) -> FakeBackend:
        raise RuntimeError("boom")

    monkeypatch.setattr(service, "get_settings", lambda: _settings(tmp_path))
    monkeypatch.setattr(service, "_create_backend", boom)
    await service.start()
    assert service.current() is None
