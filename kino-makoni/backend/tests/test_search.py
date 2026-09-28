"""`/v1/search` — kirill/lotin farqsiz, kod bo'yicha ham."""

from datetime import UTC, datetime

from httpx import AsyncClient

from app.core.config import get_settings
from app.services.catalog_sync import BotCatalog, BotMovie, FakeBotCatalogSource, sync_once

NOW = datetime(2026, 1, 1, tzinfo=UTC)


async def _seed(session_factory, *movies: BotMovie) -> None:
    await sync_once(
        session_factory, FakeBotCatalogSource(BotCatalog(movies=list(movies))), get_settings()
    )


def _movie(bot_id: int, code: int, title: str) -> BotMovie:
    return BotMovie(
        id=bot_id,
        code=code,
        title=title,
        caption=None,
        base_msg_id=500 + bot_id,
        year=2020,
        genre=None,
        quality=None,
        language=None,
        duration=None,
        is_premium=False,
        views=1,
        created_at=NOW,
    )


async def test_search_by_latin_title(app_client: AsyncClient, session_factory, auth_headers):
    await _seed(session_factory, _movie(1, 1001, "Bo'ychechak"))
    resp = await app_client.get("/v1/search", params={"q": "boychechak"}, headers=auth_headers)
    assert resp.status_code == 200
    titles = [t["title"] for t in resp.json()["items"]]
    assert "Bo'ychechak" in titles


async def test_search_cyrillic_matches_latin_title(
    app_client: AsyncClient, session_factory, auth_headers
):
    await _seed(session_factory, _movie(1, 1001, "Bo'ychechak"))
    resp = await app_client.get("/v1/search", params={"q": "Бойчечак"}, headers=auth_headers)
    assert resp.status_code == 200
    titles = [t["title"] for t in resp.json()["items"]]
    assert "Bo'ychechak" in titles


async def test_search_by_code(app_client: AsyncClient, session_factory, auth_headers):
    await _seed(session_factory, _movie(1, 4242, "Har xil nom"))
    resp = await app_client.get("/v1/search", params={"q": "4242"}, headers=auth_headers)
    assert resp.status_code == 200
    titles = [t["title"] for t in resp.json()["items"]]
    assert "Har xil nom" in titles


async def test_search_empty_query_is_422(app_client: AsyncClient, auth_headers):
    resp = await app_client.get("/v1/search", params={"q": ""}, headers=auth_headers)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


async def test_search_excludes_deleted(app_client: AsyncClient, session_factory, auth_headers):
    await _seed(session_factory, _movie(1, 1001, "O'chirilgan kino"))
    # botda kino yo'qoladi — soft-delete
    await sync_once(session_factory, FakeBotCatalogSource(BotCatalog(movies=[])), get_settings())

    resp = await app_client.get("/v1/search", params={"q": "ochirilgan"}, headers=auth_headers)
    assert resp.json()["items"] == []
