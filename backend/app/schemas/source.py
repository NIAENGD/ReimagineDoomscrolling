from datetime import datetime

from pydantic import BaseModel, Field


class SourceCreate(BaseModel):
    url: str
    title: str = ""
    cadence_minutes: int = Field(default=60, ge=5, le=24 * 60)
    discovery_mode: str = "latest_n"
    max_videos: int = Field(default=10, ge=1, le=200)
    rolling_window_hours: int = Field(default=72, ge=1, le=24 * 14)
    skip_shorts: bool = True
    min_duration_seconds: int = Field(default=180, ge=0, le=60 * 60 * 8)
    skip_livestreams: bool = True
    transcript_strategy: str = "transcript_first"
    fallback_enabled: bool = True
    prompt_override: str = ""
    destination_collection_id: int | None = None
    dedup_policy: str = "source_video_id"
    retry_max_attempts: int = Field(default=2, ge=0, le=10)
    retry_backoff_minutes: int = Field(default=10, ge=1, le=240)
    retry_backoff_multiplier: int = Field(default=2, ge=1, le=8)


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
    destination_collection_id: int | None = None
    dedup_policy: str | None = None
    retry_max_attempts: int | None = Field(default=None, ge=0, le=10)
    retry_backoff_minutes: int | None = Field(default=None, ge=1, le=240)
    retry_backoff_multiplier: int | None = Field(default=None, ge=1, le=8)


class SourceOut(SourceCreate):
    id: int
    channel_id: str = ""
    canonical_url: str = ""
    state: str
    next_run_at: datetime | None = None
    last_success_at: datetime | None = None

    class Config:
        from_attributes = True
