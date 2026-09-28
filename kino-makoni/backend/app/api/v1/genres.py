"""`GET /v1/genres`."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models.title import Title, TitleGenre
from app.models.user import User
from app.schemas.common import GenreOut, GenresResponse

router = APIRouter(tags=["genres"])


@router.get("/genres", response_model=GenresResponse)
async def list_genres(
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_current_user),
) -> GenresResponse:
    stmt = (
        select(TitleGenre.slug, TitleGenre.name, func.count(TitleGenre.id))
        .join(Title, Title.id == TitleGenre.title_id)
        .where(Title.is_deleted.is_(False))
        .group_by(TitleGenre.slug, TitleGenre.name)
        .order_by(func.count(TitleGenre.id).desc(), TitleGenre.name)
    )
    rows = (await session.execute(stmt)).all()
    return GenresResponse(
        items=[GenreOut(slug=slug, name=name, count=count) for slug, name, count in rows]
    )
