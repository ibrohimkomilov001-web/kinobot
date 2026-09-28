"""Kino Makoni API — FastAPI kirish nuqtasi."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import streaming
from app.api.v1 import router as v1_router
from app.core.config import Settings, get_settings
from app.core.errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.db.session import get_session_factory
from app.services.catalog_sync import PgBotCatalogSource, sync_once, sync_status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kino_makoni")


async def _catalog_sync_loop(settings: Settings) -> None:
    """Botni faqat o'qish orqali katalogni doimiy sinxronlab turadi."""
    source = PgBotCatalogSource(settings.bot_database_url)
    while True:
        try:
            await sync_once(get_session_factory(), source, settings)
            logger.info("Katalog sinxronizatsiyasi muvaffaqiyatli")
        except Exception:  # fon jarayoni hech qachon o'lmasligi kerak
            logger.exception("Katalog sinxronizatsiyasi muvaffaqiyatsiz bo'ldi")
        await asyncio.sleep(settings.catalog_sync_interval_sec)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    tasks: list[asyncio.Task] = []
    if settings.bot_database_url:
        tasks.append(asyncio.create_task(_catalog_sync_loop(settings)))
    else:
        logger.warning("BOT_DATABASE_URL bo'sh — katalog sinxronizatsiyasi ishga tushmaydi")

    await streaming.start()
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        for task in tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task
        await streaming.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Kino Makoni API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins or ["*"],
        allow_credentials=bool(settings.cors_origins),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(v1_router)
    app.include_router(streaming.router)

    @app.get("/health")
    async def health() -> dict:
        db_ok = True
        try:
            factory = get_session_factory()
            async with factory() as session:
                await session.execute(text("SELECT 1"))
        except Exception:  # health hech qachon 500 bermasligi kerak
            db_ok = False

        synced_at = sync_status.last_synced_at
        return {
            "status": "ok" if db_ok else "error",
            "db": db_ok,
            "telegram": streaming.is_connected(),
            "catalog_synced_at": (
                synced_at.isoformat(timespec="seconds").replace("+00:00", "Z")
                if synced_at
                else None
            ),
        }

    return app


app = create_app()
