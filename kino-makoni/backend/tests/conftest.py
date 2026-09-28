"""Umumiy test fixture'lari — har bir test alohida vaqtinchalik SQLite bazada ishlaydi."""

from __future__ import annotations

import contextlib
import os
import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("SECRET_KEY", "test-secret-key-please-32-characters-min!!")
os.environ.setdefault("PREMIUM_ENFORCED", "true")
os.environ.setdefault("BOT_DATABASE_URL", "")
os.environ.setdefault("TG_BASE_CHANNEL_ID", "-1001234567890")


async def _configure_db(db_url: str) -> None:
    """DATABASE_URL'ni o'rnatib, sozlamalar keshini va engine'ni qayta yaratadi."""
    os.environ["DATABASE_URL"] = db_url

    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.db import session as db_session

    await db_session.reset_engine()

    from app import models  # noqa: F401 — metadata'ga ro'yxatdan o'tkazish uchun
    from app.db.base import Base

    engine = db_session.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(autouse=True)
def _reset_sync_status():
    """`sync_status` modul darajasida global — testlar orasida tozalanadi."""
    from app.services.catalog_sync import sync_status

    sync_status.last_synced_at = None
    sync_status.last_error = None
    yield
    sync_status.last_synced_at = None
    sync_status.last_error = None


@pytest_asyncio.fixture
async def _db() -> AsyncIterator[str]:
    """Testga xos vaqtinchalik SQLite fayl — jadvallar yaratilgan holda."""
    db_path = f"/tmp/kino_makoni_test_{uuid.uuid4().hex}.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    await _configure_db(db_url)
    yield db_url

    from app.db import session as db_session

    await db_session.reset_engine()
    with contextlib.suppress(FileNotFoundError):
        os.remove(db_path)


@pytest_asyncio.fixture
async def session_factory(_db: str):
    """Ochiq turadigan sessiyasiz — har safar `factory()` bilan yangi sessiya."""
    from app.db.session import get_session_factory

    return get_session_factory()


@pytest_asyncio.fixture
async def app_client(_db: str) -> AsyncIterator[AsyncClient]:
    """Sozlangan bazaga ulangan FastAPI ilova uchun HTTP client."""
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def auth_headers(app_client: AsyncClient) -> dict[str, str]:
    """Yangi qurilma uchun access token olib, Authorization header qaytaradi."""
    resp = await app_client.post(
        "/v1/auth/device",
        json={"device_id": f"device-{uuid.uuid4().hex}", "platform": "ios", "app_version": "1.0.0"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
