"""`GET /v1/search`."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import raise_error
from app.db.session import get_session
from app.models.user import User
from app.schemas.common import SearchResponse
from app.services.presenters import title_to_card
from app.services.search import search_titles

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(default=..., min_length=1),
    limit: int = Query(default=20, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_current_user),
) -> SearchResponse:
    if not q.strip():
        raise_error(422, "validation_error", "Qidiruv so'zi bo'sh bo'lishi mumkin emas")
    results = await search_titles(session, q, limit)
    return SearchResponse(items=[title_to_card(t) for t in results])
