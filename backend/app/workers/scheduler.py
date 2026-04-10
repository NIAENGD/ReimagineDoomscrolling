from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.entities import Source, SourceState
from app.services.pipeline import refresh_source

scheduler = BackgroundScheduler()


def tick_sources():
    db = SessionLocal()
    try:
        sources = db.execute(select(Source).where(Source.state == SourceState.enabled)).scalars().all()
        now = datetime.utcnow()
        for src in sources:
            if not src.next_run_at or src.next_run_at <= now:
                refresh_source(db, src.id)
                src.next_run_at = now + timedelta(minutes=src.cadence_minutes)
        db.commit()
    finally:
        db.close()


def start_scheduler():
    if scheduler.get_jobs():
        return
    scheduler.add_job(tick_sources, 'interval', minutes=5, id='source_tick')
    scheduler.start()
