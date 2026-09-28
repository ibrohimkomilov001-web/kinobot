"""Sevimlilar (idempotent), progress + continue + tugallanish mantiqi."""

from datetime import UTC, datetime

from httpx import AsyncClient

from app.core.config import get_settings
from app.services.catalog_sync import BotCatalog, BotMovie, FakeBotCatalogSource, sync_once

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _movie(bot_id: int) -> BotMovie:
    return BotMovie(
        id=bot_id,
        code=1000 + bot_id,
        title=f"Kino {bot_id}",
        caption=None,
        base_msg_id=500 + bot_id,
        year=2020,
        genre=None,
        quality=None,
        language=None,
        duration=10000,
        is_premium=False,
        views=1,
        created_at=NOW,
    )


async def _seed(session_factory, *movies: BotMovie) -> None:
    await sync_once(
        session_factory, FakeBotCatalogSource(BotCatalog(movies=list(movies))), get_settings()
    )


async def _first_title_id(app_client: AsyncClient, headers: dict) -> int:
    resp = await app_client.get("/v1/titles", headers=headers)
    return resp.json()["items"][0]["id"]


async def test_favorite_put_get_delete_idempotent(
    app_client: AsyncClient, session_factory, auth_headers
):
    await _seed(session_factory, _movie(1))
    title_id = await _first_title_id(app_client, auth_headers)

    put1 = await app_client.put(f"/v1/me/favorites/{title_id}", headers=auth_headers)
    assert put1.status_code == 204
    put2 = await app_client.put(f"/v1/me/favorites/{title_id}", headers=auth_headers)  # idempotent
    assert put2.status_code == 204

    listed = await app_client.get("/v1/me/favorites", headers=auth_headers)
    assert len(listed.json()["items"]) == 1

    del1 = await app_client.delete(f"/v1/me/favorites/{title_id}", headers=auth_headers)
    assert del1.status_code == 204
    del2 = await app_client.delete(
        f"/v1/me/favorites/{title_id}", headers=auth_headers
    )  # idempotent
    assert del2.status_code == 204

    listed2 = await app_client.get("/v1/me/favorites", headers=auth_headers)
    assert listed2.json()["items"] == []


async def test_favorite_unknown_title_is_404(app_client: AsyncClient, auth_headers):
    resp = await app_client.put("/v1/me/favorites/999999", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


async def test_progress_update_and_continue_list(
    app_client: AsyncClient, session_factory, auth_headers
):
    await _seed(session_factory, _movie(1))
    title_id = await _first_title_id(app_client, auth_headers)

    resp = await app_client.put(
        "/v1/me/progress",
        json={
            "title_id": title_id,
            "episode_id": None,
            "position_sec": 1000,
            "duration_sec": 10000,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 204

    cont = await app_client.get("/v1/me/continue", headers=auth_headers)
    items = cont.json()["items"]
    assert len(items) == 1
    assert items[0]["title"]["id"] == title_id
    assert items[0]["position_sec"] == 1000


async def test_progress_marks_finished_at_92_percent(
    app_client: AsyncClient, session_factory, auth_headers
):
    await _seed(session_factory, _movie(1))
    title_id = await _first_title_id(app_client, auth_headers)

    await app_client.put(
        "/v1/me/progress",
        json={
            "title_id": title_id,
            "episode_id": None,
            "position_sec": 9300,
            "duration_sec": 10000,
        },
        headers=auth_headers,
    )

    cont = await app_client.get("/v1/me/continue", headers=auth_headers)
    assert cont.json()["items"] == []  # tugallangan — continue'dan chiqadi

    detail = await app_client.get(f"/v1/titles/{title_id}", headers=auth_headers)
    assert detail.json()["progress"]["position_sec"] == 9300


async def test_progress_update_is_upsert_not_duplicate(
    app_client: AsyncClient, session_factory, auth_headers
):
    await _seed(session_factory, _movie(1))
    title_id = await _first_title_id(app_client, auth_headers)

    for pos in (100, 200, 300):
        await app_client.put(
            "/v1/me/progress",
            json={
                "title_id": title_id,
                "episode_id": None,
                "position_sec": pos,
                "duration_sec": 10000,
            },
            headers=auth_headers,
        )

    cont = await app_client.get("/v1/me/continue", headers=auth_headers)
    items = cont.json()["items"]
    assert len(items) == 1
    assert items[0]["position_sec"] == 300


async def test_progress_unknown_title_is_404(app_client: AsyncClient, auth_headers):
    resp = await app_client.put(
        "/v1/me/progress",
        json={"title_id": 999999, "episode_id": None, "position_sec": 1, "duration_sec": 10},
        headers=auth_headers,
    )
    assert resp.status_code == 404
