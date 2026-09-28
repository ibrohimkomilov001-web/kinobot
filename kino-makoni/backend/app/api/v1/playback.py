"""`POST /v1/playback`."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core import media_urls
from app.core.config import get_settings
from app.core.errors import raise_error
from app.db.session import get_session
from app.models.episode import Episode
from app.models.progress import WatchProgress
from app.models.season import Season
from app.models.title import Title
from app.models.user import User
from app.schemas.common import PlaybackResponse
from app.schemas.requests import PlaybackRequest

router = APIRouter(tags=["playback"])


@router.post("/playback", response_model=PlaybackResponse)
async def playback(
    body: PlaybackRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> PlaybackResponse:
    settings = get_settings()
    title = (
        await session.execute(
            select(Title).where(Title.id == body.title_id, Title.is_deleted.is_(False))
        )
    ).scalar_one_or_none()
    if title is None:
        raise_error(404, "not_found", "Kino topilmadi")

    if settings.premium_enforced and title.is_premium:
        raise_error(403, "premium_required", "Bu kontent uchun premium obuna kerak")

    channel_id = title.tg_channel_id
    episode_id: int | None = None

    if title.kind == "serial":
        if body.episode_id is None:
            raise_error(422, "validation_error", "Serial uchun episode_id majburiy")
        episode = (
            await session.execute(
                select(Episode)
                .join(Season, Season.id == Episode.season_id)
                .where(Episode.id == body.episode_id, Season.title_id == title.id)
            )
        ).scalar_one_or_none()
        if episode is None:
            raise_error(422, "validation_error", "Qism ushbu serialga tegishli emas")
        if not episode.is_available or channel_id is None:
            raise_error(409, "unavailable", "Bu qism hozircha mavjud emas")
        msg_id = episode.tg_msg_id
        episode_id = episode.id
    else:
        if not title.is_available or channel_id is None or title.tg_msg_id is None:
            raise_error(409, "unavailable", "Bu kino hozircha mavjud emas")
        msg_id = title.tg_msg_id

    stream_url, expires_at = media_urls.telegram_stream_url(channel_id, msg_id)

    key = episode_id or 0
    progress = (
        await session.execute(
            select(WatchProgress).where(
                WatchProgress.user_id == user.id,
                WatchProgress.title_id == title.id,
                WatchProgress.episode_key == key,
            )
        )
    ).scalar_one_or_none()
    resume_position = progress.position_sec if progress and not progress.finished else 0

    return PlaybackResponse(
        stream_url=stream_url, expires_at=expires_at, resume_position_sec=resume_position
    )
