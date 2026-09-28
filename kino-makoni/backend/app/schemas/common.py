"""Javob obyektlari — docs/API.md dagi shakllarga aniq mos (snake_case)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, Field, PlainSerializer


def _iso_z(value: datetime) -> str:
    """ISO-8601 UTC, "+00:00" o'rniga "Z" (docs/API.md talabi)."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


IsoDateTime = Annotated[datetime, PlainSerializer(_iso_z, return_type=str)]


class TitleCard(BaseModel):
    id: int
    kind: str
    title: str
    year: int | None = None
    genres: list[str] = Field(default_factory=list)
    poster_url: str | None = None
    backdrop_url: str | None = None
    is_premium: bool
    quality: str | None = None
    duration_sec: int | None = None


class ProgressInfo(BaseModel):
    episode_id: int | None = None
    position_sec: int
    duration_sec: int | None = None


class EpisodeOut(BaseModel):
    id: int
    number: int
    title: str | None = None
    duration_sec: int | None = None
    is_available: bool
    progress_sec: int


class SeasonOut(BaseModel):
    id: int
    number: int
    title: str | None = None
    episodes: list[EpisodeOut] = Field(default_factory=list)


class TitleDetail(TitleCard):
    code: int
    description: str | None = None
    language: str | None = None
    views: int
    is_favorite: bool
    is_available: bool
    progress: ProgressInfo | None = None
    seasons: list[SeasonOut] = Field(default_factory=list)


class ContinueItem(BaseModel):
    title: TitleCard
    episode_id: int | None = None
    episode_label: str | None = None
    position_sec: int
    duration_sec: int | None = None
    updated_at: IsoDateTime


class GenreOut(BaseModel):
    slug: str
    name: str
    count: int


class HomeSection(BaseModel):
    id: str
    title: str
    style: str
    items: list[TitleCard]
    continue_items: list[ContinueItem] | None = None


class HomeResponse(BaseModel):
    sections: list[HomeSection]


class TitlesResponse(BaseModel):
    items: list[TitleCard]
    next_cursor: str | None = None


class GenresResponse(BaseModel):
    items: list[GenreOut]


class SearchResponse(BaseModel):
    items: list[TitleCard]


class PlaybackResponse(BaseModel):
    stream_url: str
    expires_at: IsoDateTime
    resume_position_sec: int


class MeResponse(BaseModel):
    id: int
    created_at: IsoDateTime


class FavoritesResponse(BaseModel):
    items: list[TitleCard]


class ContinueResponse(BaseModel):
    items: list[ContinueItem]


class DeviceAuthUser(BaseModel):
    id: int
    created_at: IsoDateTime


class DeviceAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: DeviceAuthUser
