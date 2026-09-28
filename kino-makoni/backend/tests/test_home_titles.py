"""`/v1/home`, `/v1/titles`, `/v1/titles/{id}`, `/v1/genres`."""

from datetime import UTC, datetime

from httpx import AsyncClient

from app.core.config import get_settings
from app.services.catalog_sync import (
    BotCatalog,
    BotEpisode,
    BotMovie,
    BotSeason,
    BotSerial,
    sync_once,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _movie(bot_id: int, **overrides) -> BotMovie:
    base = dict(
        id=bot_id,
        code=1000 + bot_id,
        title=f"Kino {bot_id}",
        caption=None,
        base_msg_id=500 + bot_id,
        year=2020,
        genre="Jangari",
        quality="1080p",
        language="O'zbek tilida",
        duration=6000,
        is_premium=False,
        views=bot_id,
        created_at=NOW,
    )
    base.update(overrides)
    return BotMovie(**base)


async def _seed_catalog(session_factory, catalog: BotCatalog) -> None:
    from app.services.catalog_sync import FakeBotCatalogSource

    await sync_once(session_factory, FakeBotCatalogSource(catalog), get_settings())


async def test_titles_pagination(app_client: AsyncClient, session_factory, auth_headers):
    movies = [_movie(i, views=i) for i in range(1, 6)]
    await _seed_catalog(session_factory, BotCatalog(movies=movies))

    resp = await app_client.get(
        "/v1/titles", params={"limit": 2, "sort": "popular"}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["items"][0]["title"] == "Kino 5"  # eng ko'p ko'rilgan birinchi
    assert body["next_cursor"] is not None

    resp2 = await app_client.get(
        "/v1/titles",
        params={"limit": 2, "sort": "popular", "cursor": body["next_cursor"]},
        headers=auth_headers,
    )
    body2 = resp2.json()
    assert len(body2["items"]) == 2
    assert body2["items"][0]["title"] == "Kino 3"

    seen_titles = {
        body["items"][0]["title"],
        body["items"][1]["title"],
        body2["items"][0]["title"],
        body2["items"][1]["title"],
    }
    assert "Kino 5" in seen_titles and "Kino 4" in seen_titles


async def test_titles_last_page_has_no_next_cursor(
    app_client: AsyncClient, session_factory, auth_headers
):
    await _seed_catalog(session_factory, BotCatalog(movies=[_movie(1)]))
    resp = await app_client.get("/v1/titles", params={"limit": 24}, headers=auth_headers)
    assert resp.json()["next_cursor"] is None


async def test_titles_genre_filter(app_client: AsyncClient, session_factory, auth_headers):
    await _seed_catalog(
        session_factory,
        BotCatalog(movies=[_movie(1, genre="Jangari"), _movie(2, genre="Komediya")]),
    )
    resp = await app_client.get("/v1/titles", params={"genre": "jangari"}, headers=auth_headers)
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["title"] == "Kino 1"


async def test_titles_kind_filter(app_client: AsyncClient, session_factory, auth_headers):
    await _seed_catalog(
        session_factory,
        BotCatalog(
            movies=[_movie(1)],
            serials=[
                BotSerial(
                    id=1,
                    code=9001,
                    title="Serial 1",
                    caption=None,
                    year=2022,
                    genre=None,
                    is_premium=False,
                    views=1,
                    created_at=NOW,
                )
            ],
        ),
    )
    resp = await app_client.get("/v1/titles", params={"kind": "serial"}, headers=auth_headers)
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["kind"] == "serial"


async def test_title_detail_not_found(app_client: AsyncClient, auth_headers):
    resp = await app_client.get("/v1/titles/999999", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


async def test_title_detail_movie_shape(app_client: AsyncClient, session_factory, auth_headers):
    await _seed_catalog(session_factory, BotCatalog(movies=[_movie(1)]))
    resp = await app_client.get("/v1/titles", headers=auth_headers)
    title_id = resp.json()["items"][0]["id"]

    detail = await app_client.get(f"/v1/titles/{title_id}", headers=auth_headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["code"] == 1001
    assert body["is_favorite"] is False
    assert body["is_available"] is True
    assert body["progress"] is None
    assert body["seasons"] == []


async def test_title_detail_serial_with_seasons_and_progress(
    app_client: AsyncClient, session_factory, auth_headers
):
    catalog = BotCatalog(
        serials=[
            BotSerial(
                id=1,
                code=9001,
                title="Serial 1",
                caption=None,
                year=2022,
                genre=None,
                is_premium=False,
                views=1,
                created_at=NOW,
            )
        ],
        seasons=[BotSeason(id=10, serial_id=1, number=1, title=None)],
        episodes=[BotEpisode(id=100, season_id=10, number=1, title=None, base_msg_id=700)],
    )
    await _seed_catalog(session_factory, catalog)

    resp = await app_client.get("/v1/titles", params={"kind": "serial"}, headers=auth_headers)
    title_id = resp.json()["items"][0]["id"]

    detail = await app_client.get(f"/v1/titles/{title_id}", headers=auth_headers)
    body = detail.json()
    assert len(body["seasons"]) == 1
    assert body["seasons"][0]["number"] == 1
    episode = body["seasons"][0]["episodes"][0]
    assert episode["number"] == 1
    assert episode["is_available"] is True
    assert episode["progress_sec"] == 0


async def test_genres_endpoint_counts(app_client: AsyncClient, session_factory, auth_headers):
    await _seed_catalog(
        session_factory,
        BotCatalog(
            movies=[
                _movie(1, genre="Jangari"),
                _movie(2, genre="Jangari"),
                _movie(3, genre="Drama"),
            ]
        ),
    )
    resp = await app_client.get("/v1/genres", headers=auth_headers)
    body = {item["slug"]: item["count"] for item in resp.json()["items"]}
    assert body["jangari"] == 2
    assert body["drama"] == 1


async def test_home_sections_present(app_client: AsyncClient, session_factory, auth_headers):
    await _seed_catalog(session_factory, BotCatalog(movies=[_movie(i) for i in range(1, 4)]))
    resp = await app_client.get("/v1/home", headers=auth_headers)
    assert resp.status_code == 200
    sections = {s["id"]: s for s in resp.json()["sections"]}
    assert "new" in sections
    assert "popular" in sections
    assert "hero" in sections  # poster mavjud (thumb fallback)
    assert "continue" not in sections  # progress yo'q
