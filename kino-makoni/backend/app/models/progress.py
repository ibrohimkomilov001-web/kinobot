"""Ko'rish progressi (kino uchun ham, serial qismi uchun ham).

`episode_key` — NULL bilan unikallik muammosini oldini olish uchun:
kino yoki "umumiy" yozuv uchun 0, aks holda episode_id bilan bir xil qiymat.
Postgres/SQLite'ning ikkalasida ham NULL ustunlar unique cheklovda "teng emas"
hisoblanadi, shuning uchun NULL o'rniga doim 0 ishlatiladi.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WatchProgress(Base):
    __tablename__ = "watch_progress"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "title_id", "episode_key", name="uq_watch_progress_user_title_episode"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title_id: Mapped[int] = mapped_column(
        ForeignKey("titles.id", ondelete="CASCADE"), nullable=False
    )
    episode_id: Mapped[int | None] = mapped_column(
        ForeignKey("episodes.id", ondelete="CASCADE"), nullable=True
    )
    episode_key: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    position_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    finished: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
