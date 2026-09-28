"""Qidiruv — kirill/lotin farqsiz, kod bo'yicha ham (docs/API.md).

Tartib: 1) `q` butunlay raqamdan iborat bo'lsa — kod bo'yicha aniq moslik;
2) `title_norm`da ichki moslik (normalize_title orqali, kirill/lotin farqsiz);
3) hech narsa topilmasa va Postgres bo'lsa — pg_trgm similarity fallback.
"""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.title import Title
from app.services.translit import normalize_title


async def search_titles(session: AsyncSession, q: str, limit: int) -> list[Title]:
    q = q.strip()
    seen: set[int] = set()
    results: list[Title] = []

    def _add(rows: list[Title]) -> None:
        for row in rows:
            if row.id not in seen:
                seen.add(row.id)
                results.append(row)

    if q.isdigit():
        stmt = (
            select(Title)
            .where(Title.code == int(q), Title.is_deleted.is_(False))
            .order_by(Title.views.desc())
            .limit(limit)
        )
        _add(list((await session.execute(stmt)).scalars().all()))

    norm = normalize_title(q)
    if norm and len(results) < limit:
        stmt = (
            select(Title)
            .where(Title.title_norm.contains(norm), Title.is_deleted.is_(False))
            .order_by(Title.views.desc())
            .limit(limit)
        )
        _add(list((await session.execute(stmt)).scalars().all()))

    if not results and session.bind is not None and session.bind.dialect.name == "postgresql":
        term = norm or q
        rows = (
            await session.execute(
                text(
                    "SELECT id FROM titles WHERE is_deleted = false "
                    "AND lower(title_norm) % lower(:term) "
                    "ORDER BY similarity(lower(title_norm), lower(:term)) DESC LIMIT :lim"
                ),
                {"term": term, "lim": limit},
            )
        ).all()
        ids = [r[0] for r in rows]
        if ids:
            by_id = {
                t.id: t
                for t in (await session.execute(select(Title).where(Title.id.in_(ids)))).scalars()
            }
            _add([by_id[i] for i in ids if i in by_id])

    return results[:limit]
