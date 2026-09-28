"""Kino/serial katalogi — bot bazasidan sinxronlanadigan yagona jadval.

`kind` bo'yicha bitta jadvalda kino ham, serial ham saqlanadi (bot_id — bot
bazasidagi asl ID, kind+bot_id bo'yicha unikal). Janrlar ikki ko'rinishda:
`genres` — ko'rsatish uchun tartiblangan nomlar ro'yxati (JSON), `TitleGenre`
— filtrlash uchun alohida jadval (SQLite'da ham, Postgres'da ham ishlaydi).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.season import Season


class Title(Base):
    __tablename__ = "titles"
    __table_args__ = (
        UniqueConstraint("kind", "bot_id", name="uq_titles_kind_bot_id"),
        Index("ix_titles_title_norm", "title_norm"),
        Index("ix_titles_kind_deleted", "kind", "is_deleted"),
        Index("ix_titles_views", "views"),
        Index("ix_titles_bot_created_at", "bot_created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)  # "movie" | "serial"
    bot_id: Mapped[int] = mapped_column(Integer, nullable=False)  # bot bazasidagi Movie/Serial.id
    code: Mapped[int] = mapped_column(Integer, nullable=False)  # bot kodi (ko'rsatish uchun)

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    title_norm: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    genres: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    quality: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language: Mapped[str | None] = mapped_column(String(60), nullable=True)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_premium: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    tg_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tg_msg_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    poster_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    backdrop_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tmdb_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    bot_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    seasons: Mapped[list[Season]] = relationship(
        back_populates="parent_title", cascade="all, delete-orphan", passive_deletes=True
    )


class TitleGenre(Base):
    """Janr bo'yicha filtrlash uchun (title_id, slug) juftliklari."""

    __tablename__ = "title_genres"
    __table_args__ = (
        UniqueConstraint("title_id", "slug", name="uq_title_genres_title_slug"),
        Index("ix_title_genres_slug", "slug"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title_id: Mapped[int] = mapped_column(
        ForeignKey("titles.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
