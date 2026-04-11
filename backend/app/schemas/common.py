from pydantic import BaseModel, Field


class Message(BaseModel):
    message: str


class SettingsPatch(BaseModel):
    ffmpeg_path: str | None = None
    yt_dlp_path: str | None = None
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    lmstudio_base_url: str | None = None
    scheduler_enabled: bool | None = None
    scheduler_default_cadence_minutes: int | None = Field(default=None, ge=5, le=24 * 60)
    scheduler_concurrency_cap: int | None = Field(default=None, ge=1, le=16)


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class MarkReadPayload(BaseModel):
    is_read: bool


class ReadingProgressPayload(BaseModel):
    position: int = Field(ge=0)
    total: int = Field(ge=0)
