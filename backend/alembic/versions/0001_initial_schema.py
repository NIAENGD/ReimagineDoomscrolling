"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-04-11
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "settings",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "collections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
    )
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("url", sa.String(length=500), nullable=False, unique=True),
        sa.Column("channel_id", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("canonical_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("title", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default=""),
        sa.Column("state", sa.Enum("enabled", "paused", "archived", name="sourcestate"), nullable=False),
        sa.Column("cadence_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("discovery_mode", sa.String(length=50), nullable=False, server_default="latest_n"),
        sa.Column("max_videos", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("rolling_window_hours", sa.Integer(), nullable=False, server_default="72"),
        sa.Column("skip_shorts", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("min_duration_seconds", sa.Integer(), nullable=False, server_default="180"),
        sa.Column("skip_livestreams", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("transcript_strategy", sa.String(length=50), nullable=False, server_default="transcript_first"),
        sa.Column("fallback_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("prompt_override", sa.Text(), nullable=False, server_default=""),
        sa.Column("destination_collection_id", sa.Integer(), nullable=True),
        sa.Column("dedup_policy", sa.String(length=50), nullable=False, server_default="source_video_id"),
        sa.Column("retry_max_attempts", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("retry_backoff_minutes", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("retry_backoff_multiplier", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("last_scan_at", sa.DateTime(), nullable=True),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.Column("next_run_at", sa.DateTime(), nullable=True),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["destination_collection_id"], ["collections.id"]),
    )
    op.create_table(
        "refresh_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="running"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
    )
    op.create_table(
        "video_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("video_id", sa.String(length=50), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("thumbnail_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("status", sa.Enum(
            "discovered", "filtered_out", "queued", "metadata_fetched", "transcript_searching", "transcript_found",
            "transcript_unavailable", "audio_downloaded", "transcription_started", "transcription_completed",
            "generation_started", "generation_completed", "published", "failed", "retry_pending", "skipped_duplicate",
            "skipped_by_policy", name="itemstatus"
        ), nullable=False),
        sa.Column("status_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_retry_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("source_id", "video_id", name="uq_source_video"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
    )
    op.create_table(
        "transcripts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("video_item_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("language", sa.String(length=20), nullable=False, server_default="en"),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="manual"),
        sa.Column("strategy", sa.String(length=50), nullable=False, server_default="transcript_first"),
        sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("transcription_model", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(["video_item_id"], ["video_items.id"]),
    )
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("video_item_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("title", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("latest_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["video_item_id"], ["video_items.id"]),
    )
    op.create_table(
        "article_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=50), nullable=False, server_default="detailed"),
        sa.Column("prompt_snapshot", sa.Text(), nullable=False, server_default=""),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"]),
    )
    op.create_table(
        "collection_articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("collection_id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"]),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"]),
    )
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("video_item_id", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.ForeignKeyConstraint(["video_item_id"], ["video_items.id"]),
    )
    op.create_table(
        "job_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("video_item_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("error", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.ForeignKeyConstraint(["video_item_id"], ["video_items.id"]),
    )
    op.create_table(
        "reading_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("article_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"]),
    )
    op.create_table(
        "log_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="INFO"),
        sa.Column("context", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("log_events")
    op.drop_table("reading_progress")
    op.drop_table("job_items")
    op.drop_table("jobs")
    op.drop_table("collection_articles")
    op.drop_table("article_versions")
    op.drop_table("articles")
    op.drop_table("transcripts")
    op.drop_table("video_items")
    op.drop_table("refresh_runs")
    op.drop_table("sources")
    op.drop_table("collections")
    op.drop_table("settings")
