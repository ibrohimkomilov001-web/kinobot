"""`GET /v1/home` — asosiy sahifa bo'limlari."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models.title import Title, TitleGenre
from app.models.user import User
from app.schemas.common import HomeResponse, HomeSection
from app.services.presenters import build_continue_items, title_to_card

router = APIRouter(tags=["home"])

ROW_LIMIT = 12
HERO_LIMIT = 6
HERO_CANDIDATE_POOL = 60
CONTINUE_HOME_LIMIT = 10
GENRE_ROW_LIMIT = 6


@router.get("/home", response_model=HomeResponse)
async def get_home(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> HomeResponse:
    not_deleted = Title.is_deleted.is_(False)
    sections: list[HomeSection] = []

    # hero: so'ngi qo'shilganlar orasida eng ko'p ko'rilgan, rasm bor bo'lganlar
    recent_stmt = (
        select(Title)
        .where(not_deleted)
        .order_by(Title.bot_created_at.desc(), Title.id.desc())
        .limit(HERO_CANDIDATE_POOL)
    )
    recent = (await session.execute(recent_stmt)).scalars().all()
    hero_candidates = sorted(
        (t for t in recent if t.poster_url or t.backdrop_url),
        key=lambda t: t.views,
        reverse=True,
    )
    if hero_candidates:
        sections.append(
            HomeSection(
                id="hero",
                title="Tavsiya",
                style="hero",
                items=[title_to_card(t) for t in hero_candidates[:HERO_LIMIT]],
            )
        )

    # continue: foydalanuvchining tugallanmagan ko'rishlari
    continue_items = await build_continue_items(session, user.id, limit=CONTINUE_HOME_LIMIT)
    if continue_items:
        sections.append(
            HomeSection(
                id="continue",
                title="Davom ettirish",
                style="continue",
                items=[],
                continue_items=continue_items,
            )
        )

    # new
    new_stmt = (
        select(Title)
        .where(not_deleted)
        .order_by(Title.bot_created_at.desc(), Title.id.desc())
        .limit(ROW_LIMIT)
    )
    new_items = (await session.execute(new_stmt)).scalars().all()
    if new_items:
        sections.append(
            HomeSection(
                id="new",
                title="Yangi qo'shilganlar",
                style="row",
                items=[title_to_card(t) for t in new_items],
            )
        )

    # popular
    popular_stmt = (
        select(Title)
        .where(not_deleted)
        .order_by(Title.views.desc(), Title.id.desc())
        .limit(ROW_LIMIT)
    )
    popular_items = (await session.execute(popular_stmt)).scalars().all()
    if popular_items:
        sections.append(
            HomeSection(
                id="popular",
                title="Ko'p ko'rilganlar",
                style="row",
                items=[title_to_card(t) for t in popular_items],
            )
        )

    # serials
    serials_stmt = (
        select(Title)
        .where(not_deleted, Title.kind == "serial")
        .order_by(Title.views.desc(), Title.id.desc())
        .limit(ROW_LIMIT)
    )
    serial_items = (await session.execute(serials_stmt)).scalars().all()
    if serial_items:
        sections.append(
            HomeSection(
                id="serials",
                title="Seriallar",
                style="row",
                items=[title_to_card(t) for t in serial_items],
            )
        )

    # eng katta janrlardan boshlab, har biri uchun bitta qator (max 6 ta)
    genre_count_stmt = (
        select(TitleGenre.slug, func.max(TitleGenre.name), func.count(TitleGenre.id))
        .join(Title, Title.id == TitleGenre.title_id)
        .where(not_deleted)
        .group_by(TitleGenre.slug)
        .order_by(func.count(TitleGenre.id).desc())
        .limit(GENRE_ROW_LIMIT)
    )
    genre_rows = (await session.execute(genre_count_stmt)).all()
    for slug, name, _count in genre_rows:
        stmt = (
            select(Title)
            .join(TitleGenre, TitleGenre.title_id == Title.id)
            .where(not_deleted, TitleGenre.slug == slug)
            .order_by(Title.views.desc(), Title.id.desc())
            .limit(ROW_LIMIT)
        )
        items = (await session.execute(stmt)).scalars().all()
        if items:
            sections.append(
                HomeSection(
                    id=f"genre:{slug}",
                    title=name,
                    style="row",
                    items=[title_to_card(t) for t in items],
                )
            )

    return HomeResponse(sections=sections)
