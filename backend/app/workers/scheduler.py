from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.entities import AppSetting, ItemStatus, Source, SourceState, VideoItem
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
            return

        cap = max(1, _int_setting(db, "scheduler_concurrency_cap", 2))
        sources = db.execute(select(Source).where(Source.state == SourceState.enabled)).scalars().all()
        now = datetime.utcnow()

        default_cadence = max(5, _int_setting(db, "scheduler_default_cadence_minutes", 60))
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
            process_video_item(db, item.id)
        db.commit()
    finally:
        db.close()


def scheduler_status() -> dict:
    db = SessionLocal()
    try:
        enabled = _bool_setting(db, "scheduler_enabled", True)
        cap = _int_setting(db, "scheduler_concurrency_cap", 2)
        default_cadence = _int_setting(db, "scheduler_default_cadence_minutes", 60)
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
