"""Katalog sinxronizatsiyasi — soxta bot manbasi bilan (FakeBotCatalogSource)."""

from datetime import UTC, datetime

from sqlalchemy import select

from app.core.config import get_settings
from app.models.episode import Episode
from app.models.season import Season
from app.models.title import Title, TitleGenre
from app.services.catalog_sync import (
    BotCatalog,
    BotEpisode,
    BotMovie,
    BotSeason,
    BotSerial,
    FakeBotCatalogSource,
    sync_once,
    sync_status,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _movie(**overrides) -> BotMovie:
    base = dict(
        id=1,
        code=1001,
        title="Bo'ychechak",
        caption=None,
        base_msg_id=555,
        year=2020,
        genre="Jangari, Drama",
        quality="1080p",
        language="O'zbek tilida",
        duration=6000,
        is_premium=False,
        views=10,
        created_at=NOW,
    )
    base.update(overrides)
    return BotMovie(**base)


def _serial(**overrides) -> BotSerial:
    base = dict(
        id=1,
        code=2001,
        title="Test Serial",
        caption=None,
        year=2021,
        genre="Komediya",
        is_premium=False,
        views=5,
        created_at=NOW,
    )
    base.update(overrides)
    return BotSerial(**base)


async def _get_title(session_factory, kind: str, bot_id: int) -> Title:
    async with session_factory() as session:
        stmt = select(Title).where(Title.kind == kind, Title.bot_id == bot_id)
        return (await session.execute(stmt)).scalar_one()


async def test_upsert_movie_basic_fields(session_factory):
    settings = get_settings()
    source = FakeBotCatalogSource(BotCatalog(movies=[_movie()]))
    await sync_once(session_factory, source, settings)

    title = await _get_title(session_factory, "movie", 1)
    assert title.code == 1001
    assert title.title == "Bo'ychechak"
    assert title.title_norm == "boychechak"
    assert title.year == 2020
    assert title.genres == ["Jangari", "Drama"]
    assert title.quality == "1080p"
    assert title.language == "O'zbek tilida"
    assert title.duration_sec == 6000
    assert title.is_available is True  # base_msg_id bor + channel sozlangan
    assert title.tg_channel_id == settings.tg_base_channel_id
    assert title.tg_msg_id == 555
    assert title.is_deleted is False
    assert title.poster_url is not None  # telegram_thumb_url fallback
    assert sync_status.last_synced_at is not None


async def test_title_genres_table_populated_for_filtering(session_factory):
    settings = get_settings()
    source = FakeBotCatalogSource(BotCatalog(movies=[_movie(genre="Jangari va Drama")]))
    await sync_once(session_factory, source, settings)

    async with session_factory() as session:
        title = await _get_title(session_factory, "movie", 1)
        rows = (
            (await session.execute(select(TitleGenre).where(TitleGenre.title_id == title.id)))
            .scalars()
            .all()
        )
    slugs = sorted(r.slug for r in rows)
    assert slugs == ["drama", "jangari"]


async def test_update_existing_movie_on_second_sync(session_factory):
    settings = get_settings()
    source = FakeBotCatalogSource(BotCatalog(movies=[_movie(views=10)]))
    await sync_once(session_factory, source, settings)

    source.catalog = BotCatalog(movies=[_movie(views=999, title="Yangi nom")])
    await sync_once(session_factory, source, settings)

    title = await _get_title(session_factory, "movie", 1)
    assert title.views == 999
    assert title.title == "Yangi nom"

    # bitta bot_id — bitta yozuv (dublikat yaratilmagan)
    async with session_factory() as session:
        count = len(
            (await session.execute(select(Title).where(Title.kind == "movie"))).scalars().all()
        )
    assert count == 1


async def test_movie_disappearing_soft_deletes(session_factory):
    settings = get_settings()
    source = FakeBotCatalogSource(BotCatalog(movies=[_movie()]))
    await sync_once(session_factory, source, settings)

    source.catalog = BotCatalog(movies=[])  # botda kino o'chirilgan
    await sync_once(session_factory, source, settings)

    title = await _get_title(session_factory, "movie", 1)
    assert title.is_deleted is True
    assert title.is_available is False


async def test_movie_without_base_msg_id_is_unavailable(session_factory):
    settings = get_settings()
    source = FakeBotCatalogSource(BotCatalog(movies=[_movie(base_msg_id=None)]))
    await sync_once(session_factory, source, settings)

    title = await _get_title(session_factory, "movie", 1)
    assert title.is_available is False
    assert title.poster_url is None  # thumb fallback ham yo'q (msg yo'q)


async def test_serial_seasons_and_episodes_sync(session_factory):
    settings = get_settings()
    catalog = BotCatalog(
        serials=[_serial()],
        seasons=[BotSeason(id=10, serial_id=1, number=1, title=None)],
        episodes=[
            BotEpisode(id=100, season_id=10, number=1, title=None, base_msg_id=700),
            BotEpisode(id=101, season_id=10, number=2, title=None, base_msg_id=None),
        ],
    )
    await sync_once(session_factory, FakeBotCatalogSource(catalog), settings)

    title = await _get_title(session_factory, "serial", 1)
    assert title.duration_sec is None
    assert title.quality is None
    assert title.tg_msg_id is None  # serialning o'ziniki emas
    assert title.poster_url is not None  # birinchi qism thumb fallback
    assert title.is_available is True  # kamida 1-qism mavjud

    async with session_factory() as session:
        season = (
            await session.execute(select(Season).where(Season.title_id == title.id))
        ).scalar_one()
        episodes = (
            (await session.execute(select(Episode).where(Episode.season_id == season.id)))
            .scalars()
            .all()
        )
    episodes_by_number = {e.number: e for e in episodes}
    assert episodes_by_number[1].is_available is True
    assert episodes_by_number[2].is_available is False  # base_msg_id yo'q


async def test_serial_episode_removed_from_bot_is_cleaned_up(session_factory):
    settings = get_settings()
    catalog = BotCatalog(
        serials=[_serial()],
        seasons=[BotSeason(id=10, serial_id=1, number=1, title=None)],
        episodes=[
            BotEpisode(id=100, season_id=10, number=1, title=None, base_msg_id=700),
            BotEpisode(id=101, season_id=10, number=2, title=None, base_msg_id=701),
        ],
    )
    source = FakeBotCatalogSource(catalog)
    await sync_once(session_factory, source, settings)

    # 2-qism botdan o'chirildi
    catalog.episodes = [BotEpisode(id=100, season_id=10, number=1, title=None, base_msg_id=700)]
    await sync_once(session_factory, source, settings)

    title = await _get_title(session_factory, "serial", 1)
    async with session_factory() as session:
        season = (
            await session.execute(select(Season).where(Season.title_id == title.id))
        ).scalar_one()
        episodes = (
            (await session.execute(select(Episode).where(Episode.season_id == season.id)))
            .scalars()
            .all()
        )
    assert [e.number for e in episodes] == [1]


async def test_no_base_channel_configured_means_unavailable(session_factory, monkeypatch):
    monkeypatch.setenv("TG_BASE_CHANNEL_ID", "0")
    get_settings.cache_clear()
    settings = get_settings()
    try:
        source = FakeBotCatalogSource(BotCatalog(movies=[_movie()]))
        await sync_once(session_factory, source, settings)
        title = await _get_title(session_factory, "movie", 1)
        assert title.is_available is False
        assert title.tg_channel_id is None
    finally:
        monkeypatch.setenv("TG_BASE_CHANNEL_ID", "-1001234567890")
        get_settings.cache_clear()


# ===================== Tavsif (description) chiqarish =====================


async def test_description_extraction_drops_noise_lines(session_factory):
    caption = (
        "#kino #1234\n"
        "🎭 Janri: Jangari, Drama\n"
        "📀 Sifat: 1080p\n"
        "🗣 Til: O'zbek tilida\n"
        "\n"
        "Bu ajoyib kino haqiqiy voqealar asosida suratga olingan.\n"
        "🔥🔥🔥\n"
        "@kino_makon_channel\n"
        "https://t.me/kino_makon_channel\n"
    )
    settings = get_settings()
    source = FakeBotCatalogSource(BotCatalog(movies=[_movie(caption=caption)]))
    await sync_once(session_factory, source, settings)

    title = await _get_title(session_factory, "movie", 1)
    assert title.description == "Bu ajoyib kino haqiqiy voqealar asosida suratga olingan."


async def test_description_extraction_returns_none_when_nothing_left(session_factory):
    caption = "#kino #1234\nJanri: Drama\n@kanal\nhttps://t.me/kanal\n👍👍"
    settings = get_settings()
    source = FakeBotCatalogSource(BotCatalog(movies=[_movie(caption=caption)]))
    await sync_once(session_factory, source, settings)

    title = await _get_title(session_factory, "movie", 1)
    assert title.description is None


async def test_description_extraction_html_tags_stripped(session_factory):
    caption = "<b>Bu kino</b> haqida &amp; qiziqarli tarix."
    settings = get_settings()
    source = FakeBotCatalogSource(BotCatalog(movies=[_movie(caption=caption)]))
    await sync_once(session_factory, source, settings)

    title = await _get_title(session_factory, "movie", 1)
    assert title.description == "Bu kino haqida & qiziqarli tarix."


def test_description_drops_inline_mention_and_title_repeat():
    from app.services.text_clean import extract_description

    caption = (
        "🎬 <b>Qasoskorlar: Final</b>\n\n"
        "Qahramonlar so'nggi jangga otlanadi.\n"
        "👉 @kinomakonbot"
    )
    assert extract_description(caption, "Qasoskorlar: Final") == (
        "Qahramonlar so'nggi jangga otlanadi."
    )
    # E-mail mention hisoblanmaydi
    assert extract_description("Yozing: info@mail.uz", None) == "Yozing: info@mail.uz"
