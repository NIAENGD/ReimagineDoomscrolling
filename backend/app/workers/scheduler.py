from datetime import datetime, timedelta
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.entities import AppSetting, ItemStatus, LogEvent, Source, SourceState, Transcript, VideoItem
from app.services.ops import log_event
from app.services.pipeline import process_video_item, refresh_source

scheduler = BackgroundScheduler()


def _bool_setting(db, key: str, default: bool) -> bool:
    row = db.execute(select(AppSetting).where(AppSetting.key == key)).scalar_one_or_none()
    if not row:
        return default
    return str(row.value).lower() in {"1", "true", "yes", "on"}


def _int_setting(db, key: str, default: int) -> int:
    row = db.execute(select(AppSetting).where(AppSetting.key == key)).scalar_one_or_none()
    if not row or not str(row.value).strip():
        return default
    try:
        return int(row.value)
    except ValueError:
        return default


def tick_sources():
    db = SessionLocal()
    try:
        if not _bool_setting(db, "scheduler_enabled", True):
            log_event(db, "INFO", "scheduler.tick", "Scheduler tick skipped because scheduler is disabled")
            db.commit()
            return

        cap = max(1, _int_setting(db, "scheduler_concurrency_cap", 2))
        sources = db.execute(select(Source).where(Source.state == SourceState.enabled)).scalars().all()
        now = datetime.utcnow()

        default_cadence = max(5, _int_setting(db, "scheduler_default_cadence_minutes", 10))
        processed = 0
        for src in sources:
            if processed >= cap:
                break
            cadence = max(5, src.cadence_minutes or default_cadence)
            if not src.cadence_minutes:
                src.cadence_minutes = cadence
            if not src.next_run_at:
                src.next_run_at = now
            if src.next_run_at <= now:
                log_event(db, "INFO", "scheduler.refresh", "Refreshing source from scheduler", source_id=src.id)
                refresh_source(db, src.id)
                missed_intervals = max(1, int((now - src.next_run_at).total_seconds() // (cadence * 60)) + 1)
                src.next_run_at = src.next_run_at + timedelta(minutes=cadence * missed_intervals)
                processed += 1

        retry_items = db.execute(
            select(VideoItem).where(
                VideoItem.status == ItemStatus.retry_pending,
                VideoItem.next_retry_at.is_not(None),
                VideoItem.next_retry_at <= now,
            ).limit(cap)
        ).scalars().all()
        for item in retry_items:
            log_event(db, "INFO", "scheduler.retry", "Retrying failed item", source_id=item.source_id, item_id=item.id)
            process_video_item(db, item.id)
        _run_retention_cleanup(db)
        db.commit()
    finally:
        db.close()


def scheduler_status() -> dict:
    db = SessionLocal()
    try:
        enabled = _bool_setting(db, "scheduler_enabled", True)
        cap = _int_setting(db, "scheduler_concurrency_cap", 2)
        default_cadence = _int_setting(db, "scheduler_default_cadence_minutes", 10)
        return {
            "running": scheduler.running,
            "enabled": enabled,
            "concurrency_cap": cap,
            "default_cadence_minutes": default_cadence,
            "job_count": len(scheduler.get_jobs()),
        }
    finally:
        db.close()


def start_scheduler():
    if scheduler.get_jobs():
        return
    scheduler.add_job(tick_sources, 'interval', minutes=5, id='source_tick')
    scheduler.start()


def _run_retention_cleanup(db):
    now = datetime.utcnow()

    log_retention_days = max(1, _int_setting(db, "log_retention_days", 30))
    db.query(LogEvent).filter(LogEvent.created_at < now - timedelta(days=log_retention_days)).delete()

    transcript_retention_days = _int_setting(db, "transcript_retention_days", 0)
    if transcript_retention_days > 0:
        db.query(Transcript).filter(Transcript.updated_at < now - timedelta(days=transcript_retention_days)).delete()

    thumbnail_cache_ttl_days = _int_setting(db, "thumbnail_cache_ttl_days", 0)
    if thumbnail_cache_ttl_days > 0:
        stale_items = db.execute(
            select(VideoItem).where(
                VideoItem.updated_at < now - timedelta(days=thumbnail_cache_ttl_days),
                VideoItem.thumbnail_url != "",
            )
        ).scalars().all()
        for item in stale_items:
            item.thumbnail_url = ""

    temp_cleanup_ttl_hours = max(1, _int_setting(db, "temp_cleanup_ttl_hours", 24))
    failed_audio_dir = Path("./tmp/failed_audio")
    if failed_audio_dir.exists():
        threshold = now - timedelta(hours=temp_cleanup_ttl_hours)
        for file_path in failed_audio_dir.rglob("*"):
            if not file_path.is_file():
                continue
            modified = datetime.utcfromtimestamp(file_path.stat().st_mtime)
            if modified < threshold:
                file_path.unlink(missing_ok=True)
