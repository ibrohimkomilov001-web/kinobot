"""Umumiy FastAPI dependency'lari — joriy foydalanuvchi (JWT)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.errors import raise_error
from app.db.session import get_session
from app.models.user import User

__all__ = ["get_current_user", "get_session"]


async def get_current_user(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise_error(401, "unauthorized", "Avtorizatsiya talab qilinadi")
    token = authorization.split(" ", 1)[1].strip()
    try:
        user_id = security.decode_access_token(token)
    except security.InvalidTokenError:
        raise_error(401, "unauthorized", "Token yaroqsiz yoki muddati o'tgan")

    user = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise_error(401, "unauthorized", "Foydalanuvchi topilmadi")
    user.last_seen_at = datetime.now(UTC)
    return user
