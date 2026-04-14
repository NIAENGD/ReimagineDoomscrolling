from pydantic import BaseModel, Field


class Message(BaseModel):
    message: str


class SettingsPatch(BaseModel):
    ffmpeg_path: str | None = None
    yt_dlp_path: str | None = None
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    lmstudio_base_url: str | None = None
    generation_provider: str | None = None
    generation_model: str | None = None
    scheduler_enabled: bool | None = None
    scheduler_default_cadence_minutes: int | None = Field(default=None, ge=5, le=24 * 60)
    scheduler_concurrency_cap: int | None = Field(default=None, ge=1, le=16)
    retry_default_max_attempts: int | None = Field(default=None, ge=0, le=10)
    retry_default_backoff_minutes: int | None = Field(default=None, ge=1, le=240)
    retry_default_backoff_multiplier: int | None = Field(default=None, ge=1, le=8)
    generation_temperature: float | None = Field(default=None, ge=0, le=2)
    generation_timeout_seconds: int | None = Field(default=None, ge=5, le=300)
    generation_max_tokens: int | None = Field(default=None, ge=64, le=30000)
    global_prompt_template: str | None = None
    retain_failed_audio: bool | None = None
    delete_audio_after_success: bool | None = None
    temp_cleanup_ttl_hours: int | None = Field(default=None, ge=1, le=24 * 30)
    transcript_retention_days: int | None = Field(default=None, ge=0, le=3650)
    thumbnail_cache_ttl_days: int | None = Field(default=None, ge=0, le=3650)
    log_retention_days: int | None = Field(default=None, ge=1, le=3650)
    debug_logging: bool | None = None
    timezone: str | None = None
    ui_theme_default: str | None = None
    source_default_discovery_mode: str | None = None
    source_default_max_videos: int | None = Field(default=None, ge=1, le=200)
    source_default_rolling_window_hours: int | None = Field(default=None, ge=1, le=24 * 30)
    source_default_skip_shorts: bool | None = None
    source_default_min_duration_seconds: int | None = Field(default=None, ge=0, le=60 * 60 * 24)
    source_default_dedup_policy: str | None = None
    transcript_first: bool | None = None
    transcript_fallback_enabled: bool | None = None
    whisper_model_size: str | None = None
    transcription_cpu_threads: int | None = Field(default=None, ge=1, le=64)
    transcription_language_hint: str | None = None
    reader_default_theme: str | None = None
    reader_font_family: str | None = None
    reader_font_size: int | None = Field(default=None, ge=12, le=30)
    reader_line_width: int | None = Field(default=None, ge=45, le=120)


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class MarkReadPayload(BaseModel):
    is_read: bool


class ReadingProgressPayload(BaseModel):
    position: int = Field(ge=0)
    total: int = Field(ge=0)


class SavedResponse(BaseModel):
    saved: bool


class DeletedResponse(BaseModel):
    deleted: bool


class QueuedResponse(BaseModel):
    queued: bool
