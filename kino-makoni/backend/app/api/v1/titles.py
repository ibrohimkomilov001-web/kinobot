"""`GET /v1/titles`, `GET /v1/titles/{id}`."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Depends, Query
from sqlalchemy import ColumnElement, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.errors import raise_error
from app.db.session import get_session
from app.models.favorite import Favorite
from app.models.progress import WatchProgress
from app.models.season import Season
from app.models.title import Title, TitleGenre
from app.models.user import User
from app.schemas.common import EpisodeOut, ProgressInfo, SeasonOut, TitleDetail, TitlesResponse
from app.services.cursor import decode_cursor, encode_cursor
from app.services.presenters import title_to_card

router = APIRouter(tags=["titles"])

_SORT_ORDERS: dict[str, Callable[[], tuple[ColumnElement, ...]]] = {
    "new": lambda: (Title.bot_created_at.desc(), Title.id.desc()),
    "popular": lambda: (Title.views.desc(), Title.id.desc()),
    "year": lambda: (Title.year.desc(), Title.id.desc()),
}


@router.get("/titles", response_model=TitlesResponse)
async def list_titles(
    kind: str | None = Query(default=None, pattern="^(movie|serial)$"),
    genre: str | None = Query(default=None),
    sort: str = Query(default="new", pattern="^(new|popular|year)$"),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=24, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_current_user),
) -> TitlesResponse:
    offset = decode_cursor(cursor)
    stmt = select(Title).where(Title.is_deleted.is_(False))
    if kind:
        stmt = stmt.where(Title.kind == kind)
    if genre:
        stmt = stmt.join(TitleGenre, TitleGenre.title_id == Title.id).where(
            TitleGenre.slug == genre
        )

    stmt = stmt.order_by(*_SORT_ORDERS[sort]()).offset(offset).limit(limit + 1)
    rows = (await session.execute(stmt)).scalars().all()

    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = encode_cursor(offset + limit) if has_more else None
    return TitlesResponse(items=[title_to_card(t) for t in rows], next_cursor=next_cursor)


@router.get("/titles/{title_id}", response_model=TitleDetail)
async def get_title(
    title_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> TitleDetail:
    stmt = select(Title).where(Title.id == title_id, Title.is_deleted.is_(False))
    title = (await session.execute(stmt)).scalar_one_or_none()
    if title is None:
        raise_error(404, "not_found", "Kino topilmadi")

    is_favorite = (
        await session.execute(
            select(Favorite.id).where(Favorite.user_id == user.id, Favorite.title_id == title_id)
        )
    ).first() is not None

    latest_progress = (
        await session.execute(
            select(WatchProgress)
            .where(WatchProgress.user_id == user.id, WatchProgress.title_id == title_id)
            .order_by(WatchProgress.updated_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    progress = (
        ProgressInfo(
            episode_id=latest_progress.episode_id,
            position_sec=latest_progress.position_sec,
            duration_sec=latest_progress.duration_sec,
        )
        if latest_progress
        else None
    )

    seasons_out: list[SeasonOut] = []
    if title.kind == "serial":
        seasons = (
            (
                await session.execute(
                    select(Season)
                    .where(Season.title_id == title_id)
                    .order_by(Season.number)
                    .options(selectinload(Season.episodes))
                )
            )
            .scalars()
            .all()
        )
        episode_ids = [ep.id for season in seasons for ep in season.episodes]
        progress_by_episode: dict[int, int] = {}
        if episode_ids:
            rows = (
                await session.execute(
                    select(WatchProgress).where(
                        WatchProgress.user_id == user.id, WatchProgress.episode_id.in_(episode_ids)
                    )
                )
            ).scalars()
            progress_by_episode = {
                row.episode_id: row.position_sec for row in rows if row.episode_id
            }

        for season in seasons:
            episodes_out = [
                EpisodeOut(
                    id=ep.id,
                    number=ep.number,
                    title=ep.episode_title,
                    duration_sec=None,
                    is_available=ep.is_available,
                    progress_sec=progress_by_episode.get(ep.id, 0),
                )
                for ep in sorted(season.episodes, key=lambda e: e.number)
            ]
            seasons_out.append(
                SeasonOut(
                    id=season.id,
                    number=season.number,
                    title=season.season_title,
                    episodes=episodes_out,
                )
            )

    card = title_to_card(title)
    return TitleDetail(
        **card.model_dump(),
        code=title.code,
        description=title.description,
        language=title.language,
        views=title.views,
        is_favorite=is_favorite,
        is_available=title.is_available,
        progress=progress,
        seasons=seasons_out,
    )
