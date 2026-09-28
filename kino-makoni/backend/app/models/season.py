"""Serial sezoni."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.episode import Episode
    from app.models.title import Title


class Season(Base):
    __tablename__ = "seasons"
    __table_args__ = (UniqueConstraint("title_id", "bot_id", name="uq_seasons_title_bot_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title_id: Mapped[int] = mapped_column(
        ForeignKey("titles.id", ondelete="CASCADE"), nullable=False
    )
    bot_id: Mapped[int] = mapped_column(Integer, nullable=False)  # bot bazasidagi Season.id
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    # "title" nomi Title bilan bog'liq relationship bilan to'qnashmasligi uchun
    season_title: Mapped[str | None] = mapped_column(String(200), nullable=True)

    parent_title: Mapped[Title] = relationship(back_populates="seasons")
    episodes: Mapped[list[Episode]] = relationship(
        back_populates="season", cascade="all, delete-orphan", passive_deletes=True
    )
