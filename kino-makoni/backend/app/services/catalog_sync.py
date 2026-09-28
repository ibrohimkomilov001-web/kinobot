"""Bot katalogini (kino-makon) o'z bazamizga sinxronlash.

`BotCatalogSource` — bot bazasidan o'qish protokoli. `PgBotCatalogSource`
haqiqiy amalga oshirish (asyncpg, FAQAT O'QISH tranzaksiya) — botga hech
qachon yozilmaydi. `FakeBotCatalogSource` — testlar uchun xotiradagi soxta
manba.

Har bir `sync_once` chaqiruvi TO'LIQ sinxronizatsiya: movies/serials/
seasons/episodes upsert qilinadi, botda yo'qolganlar soft-delete qilinadi.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol

import asyncpg
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import media_urls
from app.core.config import Settings
from app.models.episode import Episode
from app.models.season import Season
from app.models.title import Title, TitleGenre
from app.services import tmdb
from app.services.genres import parse_genres
from app.services.text_clean import extract_description
from app.services.translit import normalize_title

logger = logging.getLogger("kino_makoni.catalog_sync")


# ===================== Bot qatorlari (dataclasslar) =====================


@dataclass
class BotMovie:
    id: int
    code: int
    title: str
    caption: str | None
    base_msg_id: int | None
    year: int | None
    genre: str | None
    quality: str | None
    language: str | None
    duration: int | None
    is_premium: bool
    views: int
    created_at: datetime


@dataclass
class BotSerial:
    id: int
    code: int
    title: str
    caption: str | None
    year: int | None
    genre: str | None
    is_premium: bool
    views: int
    created_at: datetime


@dataclass
class BotSeason:
    id: int
    serial_id: int
    number: int
    title: str | None


@dataclass
class BotEpisode:
    id: int
    season_id: int
    number: int
    title: str | None
    base_msg_id: int | None


@dataclass
class BotCatalog:
    movies: list[BotMovie] = field(default_factory=list)
    serials: list[BotSerial] = field(default_factory=list)
    seasons: list[BotSeason] = field(default_factory=list)
    episodes: list[BotEpisode] = field(default_factory=list)


class BotCatalogSource(Protocol):
    async def fetch_catalog(self) -> BotCatalog: ...


class PgBotCatalogSource:
    """Bot bazasidan FAQAT O'QISH — asyncpg, read-only tranzaksiya ichida."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    async def fetch_catalog(self) -> BotCatalog:
        conn = await asyncpg.connect(self._dsn)
        try:
            async with conn.transaction(readonly=True):
                movie_rows = await conn.fetch(
                    'SELECT id, code, title, caption, "baseMsgId", year, genre, quality, '
                    'language, duration, "isPremium", views, "createdAt" FROM movies'
                )
                serial_rows = await conn.fetch(
                    'SELECT id, code, title, caption, year, genre, "isPremium", views, '
                    '"createdAt" FROM serials'
                )
                season_rows = await conn.fetch('SELECT id, "serialId", number, title FROM seasons')
                episode_rows = await conn.fetch(
                    'SELECT id, "seasonId", number, title, "baseMsgId" FROM episodes'
                )
        finally:
            await conn.close()

        return BotCatalog(
            movies=[
                BotMovie(
                    id=r["id"],
                    code=r["code"],
                    title=r["title"],
                    caption=r["caption"],
                    base_msg_id=r["baseMsgId"],
                    year=r["year"],
                    genre=r["genre"],
                    quality=r["quality"],
                    language=r["language"],
                    duration=r["duration"],
                    is_premium=r["isPremium"],
                    views=r["views"],
                    created_at=r["createdAt"],
                )
                for r in movie_rows
            ],
            serials=[
                BotSerial(
                    id=r["id"],
                    code=r["code"],
                    title=r["title"],
                    caption=r["caption"],
                    year=r["year"],
                    genre=r["genre"],
                    is_premium=r["isPremium"],
                    views=r["views"],
                    created_at=r["createdAt"],
                )
                for r in serial_rows
            ],
            seasons=[
                BotSeason(id=r["id"], serial_id=r["serialId"], number=r["number"], title=r["title"])
                for r in season_rows
            ],
            episodes=[
                BotEpisode(
                    id=r["id"],
                    season_id=r["seasonId"],
                    number=r["number"],
                    title=r["title"],
                    base_msg_id=r["baseMsgId"],
                )
                for r in episode_rows
            ],
        )


class FakeBotCatalogSource:
    """Testlar uchun xotiradagi soxta manba."""

    def __init__(self, catalog: BotCatalog | None = None) -> None:
        self.catalog = catalog or BotCatalog()

    async def fetch_catalog(self) -> BotCatalog:
        return self.catalog


# ===================== Sinxronizatsiya holati (/health uchun) =====================


@dataclass
class SyncStatus:
    last_synced_at: datetime | None = None
    last_error: str | None = None


sync_status = SyncStatus()


# ===================== Asosiy sinxronizatsiya =====================


async def sync_once(
    session_factory: async_sessionmaker[AsyncSession],
    source: BotCatalogSource,
    settings: Settings,
    http_client: httpx.AsyncClient | None = None,
) -> None:
    """Botdan bitta to'liq katalog o'qib, bazamizga upsert/soft-delete qiladi."""
    catalog = await source.fetch_catalog()
    channel_id = settings.tg_base_channel_id or None
    channel_configured = channel_id is not None

    first_ep_msg = _first_available_episode_msg(catalog)

    should_enrich = bool(settings.tmdb_api_key)
    owns_client = http_client is None and should_enrich
    client = (
        http_client
        if http_client is not None
        else (httpx.AsyncClient(timeout=10.0) if should_enrich else None)
    )

    try:
        async with session_factory() as session:
            await _sync_movies(
                session, catalog.movies, channel_id, channel_configured, client, settings
            )
            await _sync_serials(
                session,
                catalog.serials,
                channel_id,
                channel_configured,
                first_ep_msg,
                client,
                settings,
            )
            await _sync_seasons_episodes(
                session, catalog.seasons, catalog.episodes, channel_configured
            )
            await _soft_delete_missing(session, "movie", {m.id for m in catalog.movies})
            await _soft_delete_missing(session, "serial", {s.id for s in catalog.serials})
            await session.commit()
        sync_status.last_synced_at = datetime.now(UTC)
        sync_status.last_error = None
    except Exception as exc:  # holatni belgilab qayta ko'taramiz
        sync_status.last_error = str(exc)
        raise
    finally:
        if owns_client and client is not None:
            await client.aclose()


def _first_available_episode_msg(catalog: BotCatalog) -> dict[int, int]:
    """Har bir serial uchun eng birinchi mavjud qism xabar ID'si (poster fallback)."""
    season_serial = {s.id: s.serial_id for s in catalog.seasons}
    season_number = {s.id: s.number for s in catalog.seasons}
    by_serial: dict[int, list[BotEpisode]] = {}
    for ep in catalog.episodes:
        serial_id = season_serial.get(ep.season_id)
        if serial_id is None:
            continue
        by_serial.setdefault(serial_id, []).append(ep)

    result: dict[int, int] = {}
    for serial_id, eps in by_serial.items():
        available = [e for e in eps if e.base_msg_id]
        if not available:
            continue
        available.sort(key=lambda e: (season_number.get(e.season_id, 0), e.number))
        result[serial_id] = available[0].base_msg_id  # type: ignore[assignment]
    return result


async def _get_or_create_title(session: AsyncSession, kind: str, bot_id: int) -> Title:
    stmt = select(Title).where(Title.kind == kind, Title.bot_id == bot_id)
    title = (await session.execute(stmt)).scalar_one_or_none()
    if title is None:
        title = Title(kind=kind, bot_id=bot_id)
        session.add(title)
    return title


async def _apply_enrichment(
    title: Title, client: httpx.AsyncClient | None, settings: Settings, name: str, year: int | None
) -> None:
    if client is None or title.tmdb_id is not None:
        return
    enriched = await tmdb.enrich(client, settings.tmdb_api_key, name, year)
    if enriched:
        title.poster_url = title.poster_url or enriched.get("poster_url")
        title.backdrop_url = title.backdrop_url or enriched.get("backdrop_url")
        title.tmdb_id = enriched.get("tmdb_id") or title.tmdb_id


async def _sync_movies(
    session: AsyncSession,
    movies: list[BotMovie],
    channel_id: int | None,
    channel_configured: bool,
    client: httpx.AsyncClient | None,
    settings: Settings,
) -> None:
    for m in movies:
        title = await _get_or_create_title(session, "movie", m.id)
        is_available = channel_configured and m.base_msg_id is not None
        genres = parse_genres(m.genre)

        title.code = m.code
        title.title = m.title
        title.title_norm = normalize_title(m.title)
        title.year = m.year
        title.genres = [name for name, _slug in genres]
        title.quality = m.quality
        title.language = m.language
        title.duration_sec = m.duration
        title.description = extract_description(m.caption)
        title.is_premium = m.is_premium
        title.views = m.views
        title.tg_channel_id = channel_id
        title.tg_msg_id = m.base_msg_id
        title.is_available = is_available
        title.is_deleted = False
        title.bot_created_at = m.created_at
        title.synced_at = datetime.now(UTC)

        await _apply_enrichment(title, client, settings, m.title, m.year)

        if is_available and channel_id is not None:
            thumb = media_urls.telegram_thumb_url(channel_id, m.base_msg_id)  # type: ignore[arg-type]
            title.poster_url = title.poster_url or thumb
            title.backdrop_url = title.backdrop_url or thumb

        await session.flush()
        await _sync_title_genres(session, title.id, genres)


async def _sync_serials(
    session: AsyncSession,
    serials: list[BotSerial],
    channel_id: int | None,
    channel_configured: bool,
    first_ep_msg: dict[int, int],
    client: httpx.AsyncClient | None,
    settings: Settings,
) -> None:
    for s in serials:
        title = await _get_or_create_title(session, "serial", s.id)
        ep_msg = first_ep_msg.get(s.id)
        is_available = channel_configured and ep_msg is not None
        genres = parse_genres(s.genre)

        title.code = s.code
        title.title = s.title
        title.title_norm = normalize_title(s.title)
        title.year = s.year
        title.genres = [name for name, _slug in genres]
        title.quality = None
        title.language = None
        title.duration_sec = None
        title.description = extract_description(s.caption)
        title.is_premium = s.is_premium
        title.views = s.views
        title.tg_channel_id = channel_id
        title.tg_msg_id = None  # serial'ning o'ziniki emas — birinchi qism ishlatiladi
        title.is_available = is_available
        title.is_deleted = False
        title.bot_created_at = s.created_at
        title.synced_at = datetime.now(UTC)

        await _apply_enrichment(title, client, settings, s.title, s.year)

        if ep_msg is not None and channel_id is not None:
            thumb = media_urls.telegram_thumb_url(channel_id, ep_msg)
            title.poster_url = title.poster_url or thumb
            title.backdrop_url = title.backdrop_url or thumb

        await session.flush()
        await _sync_title_genres(session, title.id, genres)


async def _sync_title_genres(
    session: AsyncSession, title_id: int, genres: list[tuple[str, str]]
) -> None:
    existing_rows = (
        (await session.execute(select(TitleGenre).where(TitleGenre.title_id == title_id)))
        .scalars()
        .all()
    )
    existing = {row.slug: row for row in existing_rows}
    wanted = dict((slug, name) for name, slug in genres)

    for slug, row in existing.items():
        if slug not in wanted:
            await session.delete(row)
    for slug, name in wanted.items():
        if slug in existing:
            existing[slug].name = name
        else:
            session.add(TitleGenre(title_id=title_id, slug=slug, name=name))


async def _sync_seasons_episodes(
    session: AsyncSession,
    seasons: list[BotSeason],
    episodes: list[BotEpisode],
    channel_configured: bool,
) -> None:
    serial_title_ids = {
        bot_id: title_id
        for bot_id, title_id in (
            await session.execute(select(Title.bot_id, Title.id).where(Title.kind == "serial"))
        ).all()
    }

    season_pk: dict[int, int] = {}
    seen_seasons: dict[int, set[int]] = {}
    for s in seasons:
        title_id = serial_title_ids.get(s.serial_id)
        if title_id is None:
            continue  # serial o'zi yo'q bo'lib qolgan (keyingi sinxronizatsiyada soft-delete)
        stmt = select(Season).where(Season.title_id == title_id, Season.bot_id == s.id)
        season = (await session.execute(stmt)).scalar_one_or_none()
        if season is None:
            season = Season(title_id=title_id, bot_id=s.id)
            session.add(season)
        season.number = s.number
        season.season_title = s.title
        await session.flush()
        season_pk[s.id] = season.id
        seen_seasons.setdefault(title_id, set()).add(s.id)

    seen_episodes: dict[int, set[int]] = {}
    for e in episodes:
        season_id = season_pk.get(e.season_id)
        if season_id is None:
            continue
        stmt = select(Episode).where(Episode.season_id == season_id, Episode.bot_id == e.id)
        episode = (await session.execute(stmt)).scalar_one_or_none()
        if episode is None:
            episode = Episode(season_id=season_id, bot_id=e.id)
            session.add(episode)
        episode.number = e.number
        episode.episode_title = e.title
        episode.tg_msg_id = e.base_msg_id
        episode.is_available = channel_configured and e.base_msg_id is not None
        seen_episodes.setdefault(season_id, set()).add(e.id)
    await session.flush()

    # Botdan o'chirilgan sezon/qismlarni tozalash
    for title_id in serial_title_ids.values():
        kept = seen_seasons.get(title_id, set())
        rows = (
            (await session.execute(select(Season).where(Season.title_id == title_id)))
            .scalars()
            .all()
        )
        for row in rows:
            if row.bot_id not in kept:
                await session.delete(row)

    for season_id in season_pk.values():
        kept = seen_episodes.get(season_id, set())
        rows = (
            (await session.execute(select(Episode).where(Episode.season_id == season_id)))
            .scalars()
            .all()
        )
        for row in rows:
            if row.bot_id not in kept:
                await session.delete(row)


async def _soft_delete_missing(session: AsyncSession, kind: str, present_bot_ids: set[int]) -> None:
    stmt = select(Title).where(Title.kind == kind, Title.is_deleted.is_(False))
    rows = (await session.execute(stmt)).scalars().all()
    for row in rows:
        if row.bot_id not in present_bot_ids:
            row.is_deleted = True
            row.is_available = False
