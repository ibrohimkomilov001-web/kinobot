from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from app.core import signing
from app.streaming import router as streaming_router
from app.streaming import service
from app.streaming.streamer import Streamer
from tests.streaming.fakes import FakeBackend

CHANNEL = -1001234567890
CHUNK = 64 * 1024  # kichik bo'lak — ko'p bo'lakli yo'llar tez test qilinadi


def stream_token(msg: int, *, ch: int = CHANNEL, src: str = "tg", ttl: int = 3600) -> str:
    return signing.sign({"v": 1, "src": src, "ch": ch, "msg": msg}, ttl_sec=ttl)


def thumb_token(msg: int, *, ch: int = CHANNEL, src: str = "tg-thumb") -> str:
    return signing.sign({"v": 1, "src": src, "ch": ch, "msg": msg})


@pytest.fixture
def backend() -> FakeBackend:
    return FakeBackend()


@pytest.fixture
def streamer(backend: FakeBackend, tmp_path: Path) -> Iterator[Streamer]:
    s = Streamer(
        backend,
        channel_id=CHANNEL,
        chunk_size=CHUNK,
        thumb_dir=tmp_path / "thumbs",
        queue_wait_sec=2.0,
        chunk_wait_sec=5.0,
    )
    service.install(s)
    yield s
    service.install(None)


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(streaming_router)
    return application


@pytest.fixture
async def client(app: FastAPI, streamer: Streamer) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
