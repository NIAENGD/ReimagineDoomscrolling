from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import AppSetting, Article, ArticleVersion, Collection, Job, LogEvent, Source, VideoItem
from app.schemas.source import SourceCreate, SourceOut
from app.services.pipeline import refresh_source
from app.services.youtube import normalize_source_url

router = APIRouter()
DEFAULT_APP_SETTINGS = {
    "ffmpeg_path": "",
    "yt_dlp_path": "",
    "openai_api_key": "",
    "openai_base_url": "https://api.openai.com/v1",
    "lmstudio_base_url": "http://localhost:1234/v1",
}


@router.get('/health')
def health():
    return {"status": "ok"}


@router.get('/settings')
def get_settings(db: Session = Depends(get_db)):
    rows = db.execute(select(AppSetting)).scalars().all()
    saved = {r.key: r.value for r in rows}
    return {**DEFAULT_APP_SETTINGS, **saved}


@router.put('/settings')
def put_settings(payload: dict, db: Session = Depends(get_db)):
    for k, v in payload.items():
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
    src = Source(url=normalized, title=body.title or normalized, cadence_minutes=body.cadence_minutes, discovery_mode=body.discovery_mode, max_videos=body.max_videos)
    db.add(src)
    db.commit()
    db.refresh(src)
    return src


@router.post('/sources/{source_id}/refresh')
def refresh(source_id: int, db: Session = Depends(get_db)):
    refresh_source(db, source_id)
    return {"queued": True}


@router.patch('/sources/{source_id}')
def patch_source(source_id: int, body: dict, db: Session = Depends(get_db)):
    src = db.get(Source, source_id)
    if not src:
        raise HTTPException(404)
    for key, value in body.items():
        if hasattr(src, key):
            setattr(src, key, value)
    db.commit()
    return {"saved": True}


@router.get('/jobs')
def list_jobs(db: Session = Depends(get_db)):
    return db.execute(select(Job).order_by(Job.created_at.desc())).scalars().all()


@router.post('/jobs/{job_id}/retry')
def retry_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404)
    job.status = 'retry_pending'
    db.commit()
    return {"retried": True}


@router.get('/library')
def library(q: str = '', db: Session = Depends(get_db)):
    stmt = select(Article, VideoItem).join(VideoItem, Article.video_item_id == VideoItem.id)
    rows = db.execute(stmt).all()
    out = []
    for art, item in rows:
        if q and q.lower() not in item.title.lower():
            continue
        ver = db.execute(select(ArticleVersion).where(ArticleVersion.article_id == art.id, ArticleVersion.version == art.latest_version)).scalar_one_or_none()
        out.append({"article_id": art.id, "title": item.title, "version": art.latest_version, "body_preview": (ver.body[:160] if ver else ''), "video_item_id": item.id})
    return out


@router.get('/articles/{article_id}')
def article_detail(article_id: int, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404)
    versions = db.execute(select(ArticleVersion).where(ArticleVersion.article_id == article_id).order_by(ArticleVersion.version.desc())).scalars().all()
    item = db.get(VideoItem, article.video_item_id)
    return {"id": article.id, "title": item.title if item else '', "latest_version": article.latest_version, "versions": [{"version": v.version, "body": v.body, "prompt_snapshot": v.prompt_snapshot} for v in versions]}


@router.post('/articles/{article_id}/regenerate')
def regenerate(article_id: int, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404)
    item = db.get(VideoItem, article.video_item_id)
    if not item:
        raise HTTPException(404, "video item not found")
    from app.services.pipeline import process_video_item
    process_video_item(db, item.id)
    return {"regenerated": True}


@router.get('/collections')
def collections(db: Session = Depends(get_db)):
    return db.execute(select(Collection)).scalars().all()


@router.post('/collections')
def create_collection(body: dict, db: Session = Depends(get_db)):
    col = Collection(name=body['name'])
    db.add(col)
    db.commit()
    db.refresh(col)
    return col


@router.get('/diagnostics')
def diagnostics():
    import shutil
    from app.db.session import SessionLocal

    ffmpeg_detected = False
    yt_dlp_detected = False
    ffmpeg_command = "ffmpeg"
    yt_dlp_command = "yt-dlp"

    db = SessionLocal()
    try:
        rows = db.execute(select(AppSetting).where(AppSetting.key.in_(["ffmpeg_path", "yt_dlp_path"]))).scalars().all()
        settings_map = {row.key: row.value.strip() for row in rows}
        ffmpeg_command = settings_map.get("ffmpeg_path") or ffmpeg_command
        yt_dlp_command = settings_map.get("yt_dlp_path") or yt_dlp_command
    finally:
        db.close()

    ffmpeg_detected = bool(shutil.which(ffmpeg_command) or (ffmpeg_command and shutil.which("ffmpeg")))
    yt_dlp_detected = bool(shutil.which(yt_dlp_command) or (yt_dlp_command and shutil.which("yt-dlp")))

    return {
        'ffmpeg': ffmpeg_detected,
        'ffmpeg_command': ffmpeg_command,
        'yt_dlp': yt_dlp_detected,
        'yt_dlp_command': yt_dlp_command,
        'faster_whisper': True,
        'db': True,
        'queue': True,
    }


@router.get('/logs')
def logs(db: Session = Depends(get_db)):
    return db.execute(select(LogEvent).order_by(LogEvent.created_at.desc()).limit(200)).scalars().all()
