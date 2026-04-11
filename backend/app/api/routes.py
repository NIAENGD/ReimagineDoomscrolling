from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import (
    AppSetting,
    Article,
    ArticleVersion,
    ItemStatus,
    Collection,
    Job,
    LogEvent,
    ReadingProgress,
    Source,
    VideoItem,
)
from app.schemas.common import CollectionCreate, MarkReadPayload, ReadingProgressPayload, SettingsPatch
from app.schemas.source import SourceCreate, SourceOut, SourcePatch
from app.services.pipeline import process_video_item, refresh_source
from app.services.youtube import normalize_source_url, resolve_source_identity
from app.workers.scheduler import scheduler_status

router = APIRouter()
DEFAULT_APP_SETTINGS = {
    "ffmpeg_path": "",
    "yt_dlp_path": "",
    "openai_api_key": "",
    "openai_base_url": "https://api.openai.com/v1",
    "lmstudio_base_url": "http://localhost:1234/v1",
    "scheduler_enabled": "true",
    "scheduler_default_cadence_minutes": "60",
    "scheduler_concurrency_cap": "2",
    "generation_provider": "openai",
    "generation_model": "gpt-4.1-mini",
    "generation_mode": "detailed",
    "global_prompt_template": "Convert to {{mode}} article\n{{transcript}}",
    "transcript_languages": "en",
}
SECRET_KEYS = {"openai_api_key"}


@router.get('/health')
def health():
    return {"status": "ok"}


@router.get('/settings')
def get_settings(db: Session = Depends(get_db)):
    rows = db.execute(select(AppSetting)).scalars().all()
    saved = {r.key: r.value for r in rows}
    merged = {**DEFAULT_APP_SETTINGS, **saved}
    for k in SECRET_KEYS:
        if k in merged and merged[k]:
            merged[k] = "***redacted***"
    return merged


@router.put('/settings')
def put_settings(payload: SettingsPatch, db: Session = Depends(get_db)):
    for k, v in payload.model_dump(exclude_none=True).items():
        db.merge(AppSetting(key=k, value=str(v)))
    db.commit()
    return {"saved": True}


@router.get('/sources', response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)):
    return db.execute(select(Source)).scalars().all()


@router.post('/sources', response_model=SourceOut)
def create_source(body: SourceCreate, db: Session = Depends(get_db)):
    try:
        normalized = normalize_source_url(body.url)
    except ValueError as e:
        raise HTTPException(400, str(e))

    existing = db.execute(select(Source).where(Source.url == normalized)).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "source already exists")

    resolved = {}
    try:
        resolved = resolve_source_identity(normalized)
    except Exception:
        resolved = {"normalized_url": normalized, "canonical_url": normalized, "channel_id": "", "title": ""}

    src = Source(
        url=resolved.get("normalized_url", normalized),
        canonical_url=resolved.get("canonical_url", normalized),
        channel_id=resolved.get("channel_id", ""),
        title=body.title or resolved.get("title") or normalized,
        cadence_minutes=body.cadence_minutes,
        discovery_mode=body.discovery_mode,
        max_videos=body.max_videos,
        rolling_window_hours=body.rolling_window_hours,
        skip_shorts=body.skip_shorts,
        min_duration_seconds=body.min_duration_seconds,
        skip_livestreams=body.skip_livestreams,
        transcript_strategy=body.transcript_strategy,
        fallback_enabled=body.fallback_enabled,
        prompt_override=body.prompt_override,
        destination_collection_id=body.destination_collection_id,
        dedup_policy=body.dedup_policy,
        retry_max_attempts=body.retry_max_attempts,
        retry_backoff_minutes=body.retry_backoff_minutes,
        retry_backoff_multiplier=body.retry_backoff_multiplier,
    )
    db.add(src)
    db.commit()
    db.refresh(src)
    return src


@router.post('/sources/{source_id}/refresh')
def refresh(source_id: int, db: Session = Depends(get_db)):
    refresh_source(db, source_id)
    return {"queued": True}


@router.patch('/sources/{source_id}')
def patch_source(source_id: int, body: SourcePatch, db: Session = Depends(get_db)):
    src = db.get(Source, source_id)
    if not src:
        raise HTTPException(404)
    for key, value in body.model_dump(exclude_none=True).items():
        if hasattr(src, key):
            setattr(src, key, value)
    db.commit()
    return {"saved": True}


@router.get('/jobs')
def list_jobs(db: Session = Depends(get_db)):
    return db.execute(select(Job).order_by(Job.created_at.desc())).scalars().all()


@router.get('/jobs/{job_id}')
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404)
    return job


@router.post('/jobs/{job_id}/retry')
def retry_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404)
    job.status = 'retry_pending'
    if job.video_item_id:
        process_video_item(db, job.video_item_id)
    db.commit()
    return {"retried": True}


@router.post('/items/reprocess')
def reprocess_items(item_ids: list[int], db: Session = Depends(get_db)):
    processed = 0
    for item_id in item_ids:
        item = db.get(VideoItem, item_id)
        if not item:
            continue
        item.retry_count = 0
        item.next_retry_at = None
        item.status = ItemStatus.queued
        process_video_item(db, item_id)
        processed += 1
    return {"processed": processed}


@router.get('/items/{item_id}')
def item_detail(item_id: int, db: Session = Depends(get_db)):
    item = db.get(VideoItem, item_id)
    if not item:
        raise HTTPException(404)
    return item


@router.get('/transcripts/{item_id}')
def transcript_detail(item_id: int, db: Session = Depends(get_db)):
    from app.models.entities import Transcript

    tr = db.execute(select(Transcript).where(Transcript.video_item_id == item_id)).scalar_one_or_none()
    if not tr:
        raise HTTPException(404)
    return tr


@router.post('/transcripts/{item_id}/retry')
def transcript_retry(item_id: int, db: Session = Depends(get_db)):
    process_video_item(db, item_id)
    return {"retried": True}


@router.get('/library')
def library(
    q: str = '',
    source: str = '',
    read_state: str = '',
    sort_by: str = Query(default='import_time', pattern='^(import_time|title|source|publish_time)$'),
    db: Session = Depends(get_db),
):
    stmt = select(Article, VideoItem, Source).join(VideoItem, Article.video_item_id == VideoItem.id).join(Source, VideoItem.source_id == Source.id)
    rows = db.execute(stmt).all()
    out = []
    for art, item, src in rows:
        if q and q.lower() not in item.title.lower() and q.lower() not in (item.description or '').lower():
            continue
        if source and source.lower() not in src.title.lower():
            continue
        if read_state == 'read' and not art.is_read:
            continue
        if read_state == 'unread' and art.is_read:
            continue
        ver = db.execute(select(ArticleVersion).where(ArticleVersion.article_id == art.id, ArticleVersion.version == art.latest_version)).scalar_one_or_none()
        out.append({
            "article_id": art.id,
            "title": item.title,
            "source_title": src.title,
            "thumbnail_url": item.thumbnail_url,
            "is_read": art.is_read,
            "version": art.latest_version,
            "body_preview": (ver.body[:160] if ver else ''),
            "video_item_id": item.id,
            "published_at": item.published_at.isoformat() if item.published_at else None,
        })

    if sort_by == 'title':
        out.sort(key=lambda x: x['title'].lower())
    elif sort_by == 'source':
        out.sort(key=lambda x: x['source_title'].lower())
    elif sort_by == 'publish_time':
        out.sort(key=lambda x: x['published_at'] or '', reverse=True)
    return out


@router.get('/articles/{article_id}')
def article_detail(article_id: int, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404)
    versions = db.execute(select(ArticleVersion).where(ArticleVersion.article_id == article_id).order_by(ArticleVersion.version.desc())).scalars().all()
    item = db.get(VideoItem, article.video_item_id)
    progress = db.execute(select(ReadingProgress).where(ReadingProgress.article_id == article_id)).scalar_one_or_none()
    return {
        "id": article.id,
        "title": item.title if item else '',
        "latest_version": article.latest_version,
        "is_read": article.is_read,
        "reading_progress": {"position": progress.position, "total": progress.total} if progress else {"position": 0, "total": 0},
        "versions": [{"version": v.version, "body": v.body, "prompt_snapshot": v.prompt_snapshot, "mode": v.mode} for v in versions],
    }


@router.post('/articles/{article_id}/regenerate')
def regenerate(article_id: int, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404)
    item = db.get(VideoItem, article.video_item_id)
    if not item:
        raise HTTPException(404, "video item not found")
    process_video_item(db, item.id)
    return {"regenerated": True}


@router.post('/articles/{article_id}/read-state')
def mark_read_state(article_id: int, payload: MarkReadPayload, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404)
    article.is_read = payload.is_read
    db.commit()
    return {"saved": True}


@router.post('/articles/{article_id}/progress')
def upsert_reading_progress(article_id: int, payload: ReadingProgressPayload, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404)
    progress = db.execute(select(ReadingProgress).where(ReadingProgress.article_id == article_id)).scalar_one_or_none()
    if not progress:
        progress = ReadingProgress(article_id=article_id, position=payload.position, total=payload.total)
        db.add(progress)
    else:
        progress.position = payload.position
        progress.total = payload.total
    db.commit()
    return {"saved": True}


@router.get('/collections')
def collections(db: Session = Depends(get_db)):
    return db.execute(select(Collection)).scalars().all()


@router.post('/collections')
def create_collection(body: CollectionCreate, db: Session = Depends(get_db)):
    col = Collection(name=body.name)
    db.add(col)
    db.commit()
    db.refresh(col)
    return col


@router.get('/diagnostics')
def diagnostics(db: Session = Depends(get_db)):
    import shutil

    ffmpeg_command = "ffmpeg"
    yt_dlp_command = "yt-dlp"

    rows = db.execute(select(AppSetting).where(AppSetting.key.in_(["ffmpeg_path", "yt_dlp_path"]))).scalars().all()
    settings_map = {row.key: row.value.strip() for row in rows}
    ffmpeg_command = settings_map.get("ffmpeg_path") or ffmpeg_command
    yt_dlp_command = settings_map.get("yt_dlp_path") or yt_dlp_command

    ffmpeg_detected = bool(shutil.which(ffmpeg_command) or shutil.which("ffmpeg"))
    yt_dlp_path = shutil.which(yt_dlp_command) or shutil.which("yt-dlp")
    yt_dlp_detected = bool(yt_dlp_path)

    return {
        'ffmpeg': ffmpeg_detected,
        'ffmpeg_command': ffmpeg_command,
        'yt_dlp': yt_dlp_detected,
        'yt_dlp_command': yt_dlp_command,
        'yt_dlp_path': yt_dlp_path or '',
        'faster_whisper': True,
        'db': True,
        'scheduler': scheduler_status(),
    }


@router.get('/scheduler/status')
def get_scheduler_status():
    return scheduler_status()


@router.get('/logs')
def logs(
    severity: str = '',
    context: str = '',
    q: str = '',
    db: Session = Depends(get_db),
):
    rows = db.execute(select(LogEvent).order_by(LogEvent.created_at.desc()).limit(500)).scalars().all()
    out = []
    for row in rows:
        if severity and row.severity.lower() != severity.lower():
            continue
        if context and context.lower() not in row.context.lower():
            continue
        if q and q.lower() not in row.message.lower():
            continue
        out.append(row)
    return out
