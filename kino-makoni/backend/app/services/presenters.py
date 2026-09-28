"""ORM obyektlarini API javob shakllariga aylantirish."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.episode import Episode
from app.models.progress import WatchProgress
from app.models.season import Season
from app.models.title import Title
from app.schemas.common import ContinueItem, TitleCard


def title_to_card(t: Title) -> TitleCard:
    return TitleCard(
        id=t.id,
        kind=t.kind,
        title=t.title,
        year=t.year,
        genres=list(t.genres or []),
        poster_url=t.poster_url,
        backdrop_url=t.backdrop_url,
        is_premium=t.is_premium,
        quality=t.quality,
        duration_sec=t.duration_sec,
    )


async def build_continue_items(
    session: AsyncSession, user_id: int, limit: int
) -> list[ContinueItem]:
    """Tugallanmagan ko'rishlar ro'yxati — oxirgi yangilangani birinchi."""
    stmt = (
        select(WatchProgress, Title)
        .join(Title, Title.id == WatchProgress.title_id)
        .where(
            WatchProgress.user_id == user_id,
            WatchProgress.finished.is_(False),
            Title.is_deleted.is_(False),
        )
        .order_by(WatchProgress.updated_at.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()

    items: list[ContinueItem] = []
    for progress, title in rows:
        episode_label = None
        if progress.episode_id is not None:
            ep_stmt = (
                select(Episode, Season)
                .join(Season, Season.id == Episode.season_id)
                .where(Episode.id == progress.episode_id)
            )
            ep_row = (await session.execute(ep_stmt)).first()
            if ep_row is not None:
                episode, season = ep_row
                episode_label = f"{season.number}-fasl, {episode.number}-qism"
        items.append(
            ContinueItem(
                title=title_to_card(title),
                episode_id=progress.episode_id,
                episode_label=episode_label,
                position_sec=progress.position_sec,
                duration_sec=progress.duration_sec,
                updated_at=progress.updated_at,
            )
        )
    return items
