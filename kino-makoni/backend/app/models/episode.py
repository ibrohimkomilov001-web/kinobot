"""Serial qismi."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.season import Season


class Episode(Base):
    __tablename__ = "episodes"
    __table_args__ = (UniqueConstraint("season_id", "bot_id", name="uq_episodes_season_bot_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    season_id: Mapped[int] = mapped_column(
        ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    bot_id: Mapped[int] = mapped_column(Integer, nullable=False)  # bot bazasidagi Episode.id
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    episode_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tg_msg_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    season: Mapped[Season] = relationship(back_populates="episodes")
