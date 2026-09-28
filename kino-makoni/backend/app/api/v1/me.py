"""`GET /v1/me`, sevimlilar, `GET /v1/me/continue`, `PUT /v1/me/progress`."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import raise_error
from app.db.session import get_session
from app.models.favorite import Favorite
from app.models.progress import WatchProgress
from app.models.title import Title
from app.models.user import User
from app.schemas.common import ContinueResponse, FavoritesResponse, MeResponse
from app.schemas.requests import ProgressRequest
from app.services.presenters import build_continue_items, title_to_card

router = APIRouter(tags=["me"])


@router.get("/me", response_model=MeResponse)
async def get_me(user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(id=user.id, created_at=user.created_at)


@router.get("/me/favorites", response_model=FavoritesResponse)
async def list_favorites(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> FavoritesResponse:
    stmt = (
        select(Title)
        .join(Favorite, Favorite.title_id == Title.id)
        .where(Favorite.user_id == user.id, Title.is_deleted.is_(False))
        .order_by(Favorite.created_at.desc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    return FavoritesResponse(items=[title_to_card(t) for t in rows])


@router.put("/me/favorites/{title_id}", status_code=204)
async def add_favorite(
    title_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> Response:
    exists = (
        await session.execute(
            select(Title.id).where(Title.id == title_id, Title.is_deleted.is_(False))
        )
    ).first()
    if exists is None:
        raise_error(404, "not_found", "Kino topilmadi")

    already = (
        await session.execute(
            select(Favorite.id).where(Favorite.user_id == user.id, Favorite.title_id == title_id)
        )
    ).first()
    if already is None:
        session.add(Favorite(user_id=user.id, title_id=title_id, created_at=datetime.now(UTC)))
    return Response(status_code=204)


@router.delete("/me/favorites/{title_id}", status_code=204)
async def remove_favorite(
    title_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> Response:
    await session.execute(
        delete(Favorite).where(Favorite.user_id == user.id, Favorite.title_id == title_id)
    )
    return Response(status_code=204)


@router.get("/me/continue", response_model=ContinueResponse)
async def get_continue(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> ContinueResponse:
    items = await build_continue_items(session, user.id, limit=20)
    return ContinueResponse(items=items)


@router.put("/me/progress", status_code=204)
async def put_progress(
    body: ProgressRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> Response:
    title = (
        await session.execute(
            select(Title).where(Title.id == body.title_id, Title.is_deleted.is_(False))
        )
    ).scalar_one_or_none()
    if title is None:
        raise_error(404, "not_found", "Kino topilmadi")

    key = body.episode_id or 0
    finished = bool(body.duration_sec) and body.position_sec >= 0.92 * body.duration_sec
    now = datetime.now(UTC)

    progress = (
        await session.execute(
            select(WatchProgress).where(
                WatchProgress.user_id == user.id,
                WatchProgress.title_id == body.title_id,
                WatchProgress.episode_key == key,
            )
        )
    ).scalar_one_or_none()

    if progress is None:
        session.add(
            WatchProgress(
                user_id=user.id,
                title_id=body.title_id,
                episode_id=body.episode_id,
                episode_key=key,
                position_sec=body.position_sec,
                duration_sec=body.duration_sec,
                finished=finished,
                updated_at=now,
            )
        )
    else:
        progress.episode_id = body.episode_id
        progress.position_sec = body.position_sec
        progress.duration_sec = body.duration_sec
        progress.finished = finished
        progress.updated_at = now

    return Response(status_code=204)
