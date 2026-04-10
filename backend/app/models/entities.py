import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SourceState(str, enum.Enum):
    enabled = "enabled"
    paused = "paused"
    archived = "archived"


class ItemStatus(str, enum.Enum):
    discovered = "discovered"
    filtered_out = "filtered_out"
    queued = "queued"
    metadata_fetched = "metadata_fetched"
    transcript_searching = "transcript_searching"
    transcript_found = "transcript_found"
    transcript_unavailable = "transcript_unavailable"
    audio_downloaded = "audio_downloaded"
    transcription_started = "transcription_started"
    transcription_completed = "transcription_completed"
    generation_started = "generation_started"
    generation_completed = "generation_completed"
    published = "published"
    failed = "failed"
    retry_pending = "retry_pending"
    skipped_duplicate = "skipped_duplicate"
    skipped_by_policy = "skipped_by_policy"


class AppSetting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(500), unique=True)
    channel_id: Mapped[str] = mapped_column(String(255), default="")
    title: Mapped[str] = mapped_column(String(255), default="")
    state: Mapped[SourceState] = mapped_column(Enum(SourceState), default=SourceState.enabled)
    cadence_minutes: Mapped[int] = mapped_column(Integer, default=60)
    discovery_mode: Mapped[str] = mapped_column(String(50), default="latest_n")
    max_videos: Mapped[int] = mapped_column(Integer, default=10)
    rolling_window_hours: Mapped[int] = mapped_column(Integer, default=72)
    skip_shorts: Mapped[bool] = mapped_column(Boolean, default=True)
    min_duration_seconds: Mapped[int] = mapped_column(Integer, default=180)
    skip_livestreams: Mapped[bool] = mapped_column(Boolean, default=True)
    transcript_strategy: Mapped[str] = mapped_column(String(50), default="transcript_first")
    fallback_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    prompt_override: Mapped[str] = mapped_column(Text, default="")
    destination_collection_id: Mapped[int | None] = mapped_column(ForeignKey("collections.id"), nullable=True)
    last_scan_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)


class RefreshRun(Base):
    __tablename__ = "refresh_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="running")
    summary: Mapped[str] = mapped_column(Text, default="")


class VideoItem(Base):
    __tablename__ = "video_items"
    __table_args__ = (UniqueConstraint("source_id", "video_id", name="uq_source_video"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    video_id: Mapped[str] = mapped_column(String(50))
    url: Mapped[str] = mapped_column(String(500))
    title: Mapped[str] = mapped_column(String(500), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    thumbnail_url: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[ItemStatus] = mapped_column(Enum(ItemStatus), default=ItemStatus.discovered)
    status_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Transcript(Base):
    __tablename__ = "transcripts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_item_id: Mapped[int] = mapped_column(ForeignKey("video_items.id"), unique=True)
    language: Mapped[str] = mapped_column(String(20), default="en")
    source: Mapped[str] = mapped_column(String(30), default="manual")
    text: Mapped[str] = mapped_column(Text, default="")


class Article(Base):
    __tablename__ = "articles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_item_id: Mapped[int] = mapped_column(ForeignKey("video_items.id"), unique=True)
    title: Mapped[str] = mapped_column(String(500), default="")
    latest_version: Mapped[int] = mapped_column(Integer, default=1)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)


class ArticleVersion(Base):
    __tablename__ = "article_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"))
    version: Mapped[int] = mapped_column(Integer)
    mode: Mapped[str] = mapped_column(String(50), default="detailed")
    prompt_snapshot: Mapped[str] = mapped_column(Text, default="")
    body: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Collection(Base):
    __tablename__ = "collections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)


class CollectionArticle(Base):
    __tablename__ = "collection_articles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collection_id: Mapped[int] = mapped_column(ForeignKey("collections.id"))
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"))


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="queued")
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    video_item_id: Mapped[int | None] = mapped_column(ForeignKey("video_items.id"), nullable=True)
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LogEvent(Base):
    __tablename__ = "log_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    severity: Mapped[str] = mapped_column(String(20), default="INFO")
    context: Mapped[str] = mapped_column(String(100), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
