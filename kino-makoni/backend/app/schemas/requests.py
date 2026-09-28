"""So'rov tanasi (request body) shakllari."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DeviceAuthRequest(BaseModel):
    device_id: str = Field(min_length=1, max_length=200)
    platform: str = Field(default="ios", max_length=20)
    app_version: str | None = Field(default=None, max_length=30)


class PlaybackRequest(BaseModel):
    title_id: int
    episode_id: int | None = None


class ProgressRequest(BaseModel):
    title_id: int
    episode_id: int | None = None
    position_sec: int = Field(ge=0)
    duration_sec: int | None = Field(default=None, ge=0)
