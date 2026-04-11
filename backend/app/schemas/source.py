from datetime import datetime

from pydantic import BaseModel, Field


class SourceCreate(BaseModel):
    url: str
    title: str = ""
    cadence_minutes: int = Field(default=60, ge=5, le=24 * 60)
    discovery_mode: str = "latest_n"
    max_videos: int = Field(default=10, ge=1, le=200)


class SourcePatch(BaseModel):
    title: str | None = None
    state: str | None = None
    cadence_minutes: int | None = Field(default=None, ge=5, le=24 * 60)
    discovery_mode: str | None = None
    max_videos: int | None = Field(default=None, ge=1, le=200)
    rolling_window_hours: int | None = Field(default=None, ge=1, le=24 * 14)
    skip_shorts: bool | None = None
    min_duration_seconds: int | None = Field(default=None, ge=0, le=60 * 60 * 8)
    skip_livestreams: bool | None = None
    transcript_strategy: str | None = None
    fallback_enabled: bool | None = None
    prompt_override: str | None = None


class SourceOut(SourceCreate):
    id: int
    state: str
    next_run_at: datetime | None = None
    last_success_at: datetime | None = None

    class Config:
        from_attributes = True
