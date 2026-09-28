"""`POST /v1/auth/device` — qurilma bo'yicha anonim autentifikatsiya."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.db.session import get_session
from app.models.user import User
from app.schemas.common import DeviceAuthResponse, DeviceAuthUser
from app.schemas.requests import DeviceAuthRequest

router = APIRouter(tags=["auth"])


@router.post("/auth/device", response_model=DeviceAuthResponse)
async def auth_device(
    body: DeviceAuthRequest, session: AsyncSession = Depends(get_session)
) -> DeviceAuthResponse:
    stmt = select(User).where(User.device_id == body.device_id)
    user = (await session.execute(stmt)).scalar_one_or_none()
    now = datetime.now(UTC)

    if user is None:
        user = User(
            device_id=body.device_id,
            platform=body.platform,
            app_version=body.app_version,
            created_at=now,
            last_seen_at=now,
        )
        session.add(user)
    else:
        user.platform = body.platform
        user.app_version = body.app_version
        user.last_seen_at = now

    await session.flush()
    token, ttl_sec = security.create_access_token(user.id)
    return DeviceAuthResponse(
        access_token=token,
        expires_in=ttl_sec,
        user=DeviceAuthUser(id=user.id, created_at=user.created_at),
    )
