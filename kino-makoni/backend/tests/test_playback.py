"""`POST /v1/playback` — premium/unavailable/episode validatsiyasi."""

from datetime import UTC, datetime

from httpx import AsyncClient

from app.core.config import get_settings
from app.services.catalog_sync import (
    BotCatalog,
    BotEpisode,
    BotMovie,
    BotSeason,
    BotSerial,
    FakeBotCatalogSource,
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
        genre=None,
        quality=None,
        language=None,
        duration=10000,
        is_premium=False,
        views=1,
        created_at=NOW,
    )
    base.update(overrides)
    return BotMovie(**base)


async def _seed(session_factory, catalog: BotCatalog) -> None:
    await sync_once(session_factory, FakeBotCatalogSource(catalog), get_settings())


async def _first_title(app_client: AsyncClient, headers: dict, kind: str | None = None) -> dict:
    params = {"kind": kind} if kind else {}
    resp = await app_client.get("/v1/titles", params=params, headers=headers)
    return resp.json()["items"][0]


async def test_playback_movie_happy_path(app_client: AsyncClient, session_factory, auth_headers):
    await _seed(session_factory, BotCatalog(movies=[_movie(1)]))
    title = await _first_title(app_client, auth_headers)

    resp = await app_client.post(
        "/v1/playback", json={"title_id": title["id"], "episode_id": None}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["stream_url"].startswith("http")
    assert "/v1/stream/" in body["stream_url"]
    assert body["resume_position_sec"] == 0
    assert body["expires_at"].endswith("Z")


async def test_playback_resumes_from_progress(
    app_client: AsyncClient, session_factory, auth_headers
):
    await _seed(session_factory, BotCatalog(movies=[_movie(1)]))
    title = await _first_title(app_client, auth_headers)

    await app_client.put(
        "/v1/me/progress",
        json={
            "title_id": title["id"],
            "episode_id": None,
            "position_sec": 4242,
            "duration_sec": 10000,
        },
        headers=auth_headers,
    )
    resp = await app_client.post(
        "/v1/playback", json={"title_id": title["id"], "episode_id": None}, headers=auth_headers
    )
    assert resp.json()["resume_position_sec"] == 4242


async def test_playback_premium_required(app_client: AsyncClient, session_factory, auth_headers):
    await _seed(session_factory, BotCatalog(movies=[_movie(1, is_premium=True)]))
    title = await _first_title(app_client, auth_headers)

    resp = await app_client.post(
        "/v1/playback", json={"title_id": title["id"]}, headers=auth_headers
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "premium_required"


async def test_playback_unavailable_movie(app_client: AsyncClient, session_factory, auth_headers):
    await _seed(session_factory, BotCatalog(movies=[_movie(1, base_msg_id=None)]))
    title = await _first_title(app_client, auth_headers)

    resp = await app_client.post(
        "/v1/playback", json={"title_id": title["id"]}, headers=auth_headers
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "unavailable"


async def test_playback_not_found(app_client: AsyncClient, auth_headers):
    resp = await app_client.post("/v1/playback", json={"title_id": 999999}, headers=auth_headers)
    assert resp.status_code == 404


async def test_playback_serial_requires_episode_id(
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
    await _seed(session_factory, catalog)
    title = await _first_title(app_client, auth_headers, kind="serial")

    resp = await app_client.post(
        "/v1/playback", json={"title_id": title["id"]}, headers=auth_headers
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


async def test_playback_serial_episode_must_belong_to_title(
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
            ),
            BotSerial(
                id=2,
                code=9002,
                title="Serial 2",
                caption=None,
                year=2022,
                genre=None,
                is_premium=False,
                views=1,
                created_at=NOW,
            ),
        ],
        seasons=[
            BotSeason(id=10, serial_id=1, number=1, title=None),
            BotSeason(id=20, serial_id=2, number=1, title=None),
        ],
        episodes=[
            BotEpisode(id=100, season_id=10, number=1, title=None, base_msg_id=700),
            BotEpisode(id=200, season_id=20, number=1, title=None, base_msg_id=800),
        ],
    )
    await _seed(session_factory, catalog)

    resp = await app_client.get("/v1/titles", params={"kind": "serial"}, headers=auth_headers)
    titles = {t["title"]: t["id"] for t in resp.json()["items"]}
    detail = await app_client.get(f"/v1/titles/{titles['Serial 1']}", headers=auth_headers)
    foreign_episode_detail = await app_client.get(
        f"/v1/titles/{titles['Serial 2']}", headers=auth_headers
    )
    foreign_episode_id = foreign_episode_detail.json()["seasons"][0]["episodes"][0]["id"]

    play = await app_client.post(
        "/v1/playback",
        json={"title_id": titles["Serial 1"], "episode_id": foreign_episode_id},
        headers=auth_headers,
    )
    assert play.status_code == 422
    assert play.json()["error"]["code"] == "validation_error"

    own_episode_id = detail.json()["seasons"][0]["episodes"][0]["id"]
    play_ok = await app_client.post(
        "/v1/playback",
        json={"title_id": titles["Serial 1"], "episode_id": own_episode_id},
        headers=auth_headers,
    )
    assert play_ok.status_code == 200


async def test_playback_serial_episode_unavailable(
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
        episodes=[BotEpisode(id=100, season_id=10, number=1, title=None, base_msg_id=None)],
    )
    await _seed(session_factory, catalog)
    title = await _first_title(app_client, auth_headers, kind="serial")
    detail = await app_client.get(f"/v1/titles/{title['id']}", headers=auth_headers)
    episode_id = detail.json()["seasons"][0]["episodes"][0]["id"]

    resp = await app_client.post(
        "/v1/playback",
        json={"title_id": title["id"], "episode_id": episode_id},
        headers=auth_headers,
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "unavailable"
