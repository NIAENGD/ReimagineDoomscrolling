from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, get_db
from app.models.entities import (
    AppSetting,
    Article,
    ArticleVersion,
    ItemStatus,
    Collection,
    CollectionArticle,
    ItemStatusTransition,
    Job,
    JobItem,
    LogEvent,
    ReadingProgress,
    RefreshRun,
    Source,
    SourceState,
    Transcript,
    VideoItem,
)
from app.schemas.common import (
    CollectionCreate,
    DeletedResponse,
    MarkReadPayload,
    QueuedResponse,
    ReadingProgressPayload,
    SavedResponse,
    SettingsPatch,
)
from app.schemas.source import SourceActionResponse, SourceCreate, SourceOut, SourcePatch
from app.services.diagnostics import (
    check_binary,
    check_db,
    check_faster_whisper,
    check_lmstudio_connectivity,
    check_openai_connectivity,
    check_storage_writable,
)
from app.services.generation import ProviderConfig, generate_article, render_prompt
from app.services.ops import redact_secrets
from app.services.pipeline import process_video_item, refresh_source
from app.services.youtube import normalize_source_url, resolve_source_identity
from app.workers.scheduler import scheduler_status

router = APIRouter()


def _refresh_source_in_background(source_id: int):
    db = SessionLocal()
    try:
        refresh_source(db, source_id)
    finally:
        db.close()

DEFAULT_APP_SETTINGS = {
    "ffmpeg_path": "",
    "yt_dlp_path": "",
    "openai_api_key": "",
    "openai_base_url": "https://api.openai.com/v1",
    "lmstudio_base_url": "http://localhost:1234/v1",
    "scheduler_enabled": "true",
    "scheduler_default_cadence_minutes": "10",
    "scheduler_concurrency_cap": "2",
    "retry_default_max_attempts": "2",
    "retry_default_backoff_minutes": "10",
    "retry_default_backoff_multiplier": "2",
    "generation_provider": "openai",
    "generation_model": "gpt-4.1-mini",
    "generation_temperature": "0.2",
    "generation_timeout_seconds": "300",
    "generation_max_tokens": "30000",
    "generation_metadata_max_tokens": "4096",
    "global_prompt_template": "Convert the transcript into a polished article.\n\n{{transcript}}",
    "title_prompt_template": "Generate a video title that is concise and clear.",
    "score_prompt_template": "Video Rating: [Select from the list, briefly explain the reason for each in one sentence] Logic: Confused, Misleading, Clear; Depth: Explanation, Cause, Deeper Level, Lower Level; Insight: Superficial, Deeper Level, Lower Level; Expression: Stiff, Natural, Vivid; Inspiration: Neutral, Inspirational, Strongly Motivating; Overall Quality Score: [0-100, extremely strict scoring. Mediocre videos will not exceed 30, excellent videos may reach 80, and no video will reach 100.]",
    "title_identifier_a": "d}",
    "title_identifier_b": "[/",
    "title_identifier_c": "%x",
    "title_identifier_d": "^#",
    "title_output_language": "English",
    "transcript_languages": "en",
    "retain_failed_audio": "false",
    "delete_audio_after_success": "true",
    "temp_cleanup_ttl_hours": "24",
    "transcript_retention_days": "0",
    "thumbnail_cache_ttl_days": "0",
    "log_retention_days": "30",
    "debug_logging": "false",
    "timezone": "UTC",
    "ui_theme_default": "dark",
    "source_default_discovery_mode": "latest_n",
    "source_default_max_videos": "10",
    "source_default_rolling_window_hours": "72",
    "source_default_skip_shorts": "true",
    "source_default_min_duration_seconds": "180",
    "source_default_dedup_policy": "source_video_id",
    "whisper_model_size": "base",
    "transcription_cpu_threads": "4",
    "transcription_language_hint": "",
    "reader_default_theme": "dark",
    "reader_font_family": "sans",
    "reader_font_size": "17",
    "reader_line_width": "72",
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


@router.get('/settings/schema')
def settings_schema():
    return {
        "general": ["timezone", "ui_theme_default"],
        "sources": [
            "source_default_discovery_mode",
            "source_default_max_videos",
            "source_default_rolling_window_hours",
            "source_default_skip_shorts",
            "source_default_min_duration_seconds",
            "source_default_dedup_policy",
        ],
        "transcript": [
            "transcript_languages",
            "whisper_model_size",
            "transcription_cpu_threads",
            "transcription_language_hint",
            "retain_failed_audio",
            "delete_audio_after_success",
        ],
        "generation": [
            "generation_provider",
            "generation_model",
            "generation_temperature",
            "generation_timeout_seconds",
            "generation_max_tokens",
            "generation_metadata_max_tokens",
            "openai_api_key",
            "openai_base_url",
            "lmstudio_base_url",
            "global_prompt_template",
            "title_prompt_template",
            "score_prompt_template",
            "title_identifier_a",
            "title_identifier_b",
            "title_identifier_c",
            "title_identifier_d",
            "title_output_language",
        ],
        "scheduling": [
            "scheduler_enabled",
            "scheduler_default_cadence_minutes",
            "scheduler_concurrency_cap",
            "retry_default_max_attempts",
            "retry_default_backoff_minutes",
            "retry_default_backoff_multiplier",
        ],
        "storage": [
            "temp_cleanup_ttl_hours",
            "transcript_retention_days",
            "thumbnail_cache_ttl_days",
            "log_retention_days",
        ],
        "advanced": ["ffmpeg_path", "yt_dlp_path", "debug_logging"],
    }


@router.put('/settings', response_model=SavedResponse)
def put_settings(payload: SettingsPatch, db: Session = Depends(get_db)):
    for k, v in payload.model_dump(exclude_none=True).items():
        db.merge(AppSetting(key=k, value=str(v)))
    db.commit()
    return {"saved": True}


@router.delete('/settings/{key}', response_model=DeletedResponse)
def delete_setting(key: str, db: Session = Depends(get_db)):
    row = db.get(AppSetting, key)
    if not row:
        raise HTTPException(404, "setting not found")
    db.delete(row)
    db.commit()
    return {"deleted": True}


@router.get('/sources', response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)):
    return db.execute(select(Source)).scalars().all()


@router.post('/sources', response_model=SourceOut)
def create_source(body: SourceCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
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

    default_cadence_row = db.execute(select(AppSetting).where(AppSetting.key == "scheduler_default_cadence_minutes")).scalar_one_or_none()
    default_cadence = int(default_cadence_row.value) if default_cadence_row and str(default_cadence_row.value).isdigit() else 10
    cadence = body.cadence_minutes or default_cadence
    default_discovery_mode = db.execute(select(AppSetting).where(AppSetting.key == "source_default_discovery_mode")).scalar_one_or_none()
    default_max_videos = db.execute(select(AppSetting).where(AppSetting.key == "source_default_max_videos")).scalar_one_or_none()
    default_window = db.execute(select(AppSetting).where(AppSetting.key == "source_default_rolling_window_hours")).scalar_one_or_none()
    default_skip_shorts = db.execute(select(AppSetting).where(AppSetting.key == "source_default_skip_shorts")).scalar_one_or_none()
    default_min_duration = db.execute(select(AppSetting).where(AppSetting.key == "source_default_min_duration_seconds")).scalar_one_or_none()
    default_dedup_policy = db.execute(select(AppSetting).where(AppSetting.key == "source_default_dedup_policy")).scalar_one_or_none()
    max_videos = body.max_videos
    if max_videos is None and default_max_videos and str(default_max_videos.value).isdigit():
        max_videos = int(default_max_videos.value)
    rolling_window_hours = body.rolling_window_hours
    if rolling_window_hours is None and default_window and str(default_window.value).isdigit():
        rolling_window_hours = int(default_window.value)
    min_duration_seconds = body.min_duration_seconds
    if min_duration_seconds is None and default_min_duration and str(default_min_duration.value).isdigit():
        min_duration_seconds = int(default_min_duration.value)
    skip_shorts = body.skip_shorts
    if skip_shorts is None and default_skip_shorts:
        skip_shorts = str(default_skip_shorts.value).lower() in {"1", "true", "yes", "on"}

    src = Source(
        url=resolved.get("normalized_url", normalized),
        canonical_url=resolved.get("canonical_url", normalized),
        channel_id=resolved.get("channel_id", ""),
        title=body.title or resolved.get("title") or normalized,
        cadence_minutes=cadence,
        discovery_mode=body.discovery_mode or (default_discovery_mode.value if default_discovery_mode else "latest_n"),
        max_videos=max_videos if max_videos is not None else 10,
        rolling_window_hours=rolling_window_hours if rolling_window_hours is not None else 72,
        skip_shorts=True if skip_shorts is None else skip_shorts,
        min_duration_seconds=min_duration_seconds if min_duration_seconds is not None else 180,
        skip_livestreams=body.skip_livestreams,
        transcript_strategy=body.transcript_strategy,
        fallback_enabled=body.fallback_enabled,
        prompt_override=body.prompt_override,
        destination_collection_id=body.destination_collection_id,
        dedup_policy=body.dedup_policy or (default_dedup_policy.value if default_dedup_policy else "source_video_id"),
        retry_max_attempts=body.retry_max_attempts,
        retry_backoff_minutes=body.retry_backoff_minutes,
        retry_backoff_multiplier=body.retry_backoff_multiplier,
    )
    db.add(src)
    db.commit()
    db.refresh(src)
    background_tasks.add_task(_refresh_source_in_background, src.id)
    return src


@router.post('/sources/{source_id}/refresh')
def refresh(source_id: int, db: Session = Depends(get_db)) -> QueuedResponse:
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


@router.delete('/sources/{source_id}', response_model=DeletedResponse)
def delete_source(source_id: int, db: Session = Depends(get_db)):
    src = db.get(Source, source_id)
    if not src:
        raise HTTPException(404)
    source_job_ids = [
        row[0]
        for row in db.execute(select(Job.id).where(Job.source_id == source_id)).all()
    ]
    video_ids = [row[0] for row in db.execute(select(VideoItem.id).where(VideoItem.source_id == source_id)).all()]
    video_job_ids = [
        row[0]
        for row in db.execute(select(Job.id).where(Job.video_item_id.in_(video_ids))).all()
    ] if video_ids else []
    job_ids = list({*source_job_ids, *video_job_ids})
    article_ids = [row[0] for row in db.execute(select(Article.id).where(Article.video_item_id.in_(video_ids))).all()] if video_ids else []
    if article_ids:
        db.query(CollectionArticle).filter(CollectionArticle.article_id.in_(article_ids)).delete(synchronize_session=False)
        db.query(ReadingProgress).filter(ReadingProgress.article_id.in_(article_ids)).delete(synchronize_session=False)
        db.query(ArticleVersion).filter(ArticleVersion.article_id.in_(article_ids)).delete(synchronize_session=False)
        db.query(Article).filter(Article.id.in_(article_ids)).delete(synchronize_session=False)
    if job_ids:
        db.query(JobItem).filter(JobItem.job_id.in_(job_ids)).delete(synchronize_session=False)
    if video_ids:
        db.query(JobItem).filter(JobItem.video_item_id.in_(video_ids)).delete(synchronize_session=False)
        db.query(ItemStatusTransition).filter(ItemStatusTransition.video_item_id.in_(video_ids)).delete(synchronize_session=False)
        db.query(Transcript).filter(Transcript.video_item_id.in_(video_ids)).delete(synchronize_session=False)
        db.query(Job).filter(Job.video_item_id.in_(video_ids)).delete(synchronize_session=False)
        db.query(VideoItem).filter(VideoItem.id.in_(video_ids)).delete(synchronize_session=False)
    db.query(RefreshRun).filter(RefreshRun.source_id == source_id).delete(synchronize_session=False)
    db.query(Job).filter(Job.source_id == source_id).delete()
    db.delete(src)
    db.commit()
    return {"deleted": True}


def _set_source_state(source_id: int, state: SourceState, db: Session) -> SourceActionResponse:
    src = db.get(Source, source_id)
    if not src:
        raise HTTPException(404)
    src.state = state
    db.commit()
    return SourceActionResponse(id=src.id, state=src.state.value if hasattr(src.state, "value") else str(src.state))


@router.post('/sources/{source_id}/pause', response_model=SourceActionResponse)
def pause_source(source_id: int, db: Session = Depends(get_db)):
    return _set_source_state(source_id, SourceState.paused, db)


@router.post('/sources/{source_id}/resume', response_model=SourceActionResponse)
def resume_source(source_id: int, db: Session = Depends(get_db)):
    return _set_source_state(source_id, SourceState.enabled, db)


@router.post('/sources/{source_id}/archive', response_model=SourceActionResponse)
def archive_source(source_id: int, db: Session = Depends(get_db)):
    return _set_source_state(source_id, SourceState.archived, db)


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


@router.post('/jobs/{job_id}/cancel', response_model=SavedResponse)
def cancel_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404)
    job.status = "cancelled"
    db.commit()
    return {"saved": True}


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


@router.get('/items/{item_id}/timeline')
def item_timeline(item_id: int, db: Session = Depends(get_db)):
    from app.models.entities import ItemStatusTransition

    return db.execute(
        select(ItemStatusTransition)
        .where(ItemStatusTransition.video_item_id == item_id)
        .order_by(ItemStatusTransition.created_at.asc())
    ).scalars().all()


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


@router.post('/generation/prompt-preview')
def generation_prompt_preview(payload: dict, db: Session = Depends(get_db)):
    template_setting = db.execute(select(AppSetting).where(AppSetting.key == "global_prompt_template")).scalar_one_or_none()
    template = payload.get("template") or (template_setting.value if template_setting else DEFAULT_APP_SETTINGS["global_prompt_template"])
    transcript = payload.get("transcript", "")
    return {"prompt": render_prompt(template, transcript, "")}


@router.post('/generation/test-prompt')
def generation_test_prompt(payload: dict, db: Session = Depends(get_db)):
    transcript = payload.get("transcript", "")
    if not transcript.strip():
        raise HTTPException(400, "transcript is required")
    template = payload.get("template") or DEFAULT_APP_SETTINGS["global_prompt_template"]
    prompt = render_prompt(template, transcript, "")
    rows = db.execute(select(AppSetting)).scalars().all()
    settings_map = {r.key: r.value for r in rows}
    body = generate_article(
        transcript,
        prompt,
        ProviderConfig(
            provider=settings_map.get("generation_provider", "openai"),
            model=settings_map.get("generation_model", "gpt-4.1-mini"),
            temperature=float(settings_map.get("generation_temperature", "0.2")),
            timeout_seconds=float(settings_map.get("generation_timeout_seconds", "300")),
            max_tokens=int(settings_map.get("generation_max_tokens", "30000")),
            openai_api_key=settings_map.get("openai_api_key", ""),
            openai_base_url=settings_map.get("openai_base_url", ""),
            lmstudio_base_url=settings_map.get("lmstudio_base_url", ""),
        ),
    )
    return {"prompt": prompt, "body": body}


@router.get('/library')
def library(
    q: str = '',
    source: str = '',
    read_state: str = '',
    collection_id: int | None = None,
    group_by_source: bool = False,
    sort_by: str = Query(default='import_time', pattern='^(import_time|title|source|publish_time)$'),
    db: Session = Depends(get_db),
):
    stmt = select(Article, VideoItem, Source).join(VideoItem, Article.video_item_id == VideoItem.id).join(Source, VideoItem.source_id == Source.id)
    rows = db.execute(stmt).all()
    out = []
    for art, item, src in rows:
        ver = db.execute(select(ArticleVersion).where(ArticleVersion.article_id == art.id, ArticleVersion.version == art.latest_version)).scalar_one_or_none()
        body_text = (ver.body if ver else '') or ''
        if q and q.lower() not in item.title.lower() and q.lower() not in (item.description or '').lower() and q.lower() not in body_text.lower():
            continue
        if source and source.lower() not in src.title.lower():
            continue
        if read_state == 'read' and not art.is_read:
            continue
        if read_state == 'unread' and art.is_read:
            continue
        if collection_id is not None:
            link = db.execute(
                select(CollectionArticle).where(
                    CollectionArticle.article_id == art.id,
                    CollectionArticle.collection_id == collection_id,
                )
            ).scalar_one_or_none()
            if not link:
                continue
        progress = db.execute(select(ReadingProgress).where(ReadingProgress.article_id == art.id)).scalar_one_or_none()
        transcript = db.execute(select(Transcript).where(Transcript.video_item_id == item.id)).scalar_one_or_none()
        article_collections = db.execute(
            select(Collection.id, Collection.name)
            .join(CollectionArticle, CollectionArticle.collection_id == Collection.id)
            .where(CollectionArticle.article_id == art.id)
        ).all()
        out.append({
            "article_id": art.id,
            "title": art.ai_title or item.title,
            "original_title": item.title,
            "source_title": src.title,
            "source_id": src.id,
            "thumbnail_url": item.thumbnail_url or f"https://i.ytimg.com/vi/{item.video_id}/hqdefault.jpg",
            "is_read": art.is_read,
            "version": art.latest_version,
            "body_preview": (ver.body[:160] if ver else ''),
            "video_item_id": item.id,
            "video_id": item.video_id,
            "video_url": item.url,
            "published_at": item.published_at.isoformat() if item.published_at else None,
            "transcript_source": transcript.source if transcript else "",
            "video_category": art.ai_video_category,
            "quality_score": art.ai_quality_score,
            "quality_report": art.ai_quality_report,
            "collections": [{"id": c_id, "name": c_name} for c_id, c_name in article_collections],
            "reading_progress": {"position": progress.position, "total": progress.total} if progress else {"position": 0, "total": 0},
        })

    if sort_by == 'title':
        out.sort(key=lambda x: x['title'].lower())
    elif sort_by == 'source':
        out.sort(key=lambda x: x['source_title'].lower())
    elif sort_by == 'publish_time':
        out.sort(key=lambda x: x['published_at'] or '', reverse=True)
    if group_by_source:
        grouped: dict[str, list[dict]] = {}
        for entry in out:
            grouped.setdefault(entry["source_title"] or "Unknown source", []).append(entry)
        return [{"source_title": key, "items": value} for key, value in grouped.items()]
    return out


@router.get('/articles/{article_id}')
def article_detail(article_id: int, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404)
    versions = db.execute(select(ArticleVersion).where(ArticleVersion.article_id == article_id).order_by(ArticleVersion.version.desc())).scalars().all()
    item = db.get(VideoItem, article.video_item_id)
    source = db.get(Source, item.source_id) if item else None
    progress = db.execute(select(ReadingProgress).where(ReadingProgress.article_id == article_id)).scalar_one_or_none()
    return {
        "id": article.id,
        "video_item_id": article.video_item_id,
        "title": article.ai_title or (item.title if item else ''),
        "original_title": item.title if item else "",
        "video_category": article.ai_video_category,
        "quality_score": article.ai_quality_score,
        "quality_report": article.ai_quality_report,
        "latest_version": article.latest_version,
        "is_read": article.is_read,
        "source_title": source.title if source else "",
        "source_url": source.url if source else "",
        "channel_id": source.channel_id if source else "",
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


@router.get('/articles/{article_id}/export')
def export_article(article_id: int, format: str = Query(default="markdown", pattern="^(markdown|txt|json)$"), db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404)
    item = db.get(VideoItem, article.video_item_id)
    version = db.execute(
        select(ArticleVersion).where(
            ArticleVersion.article_id == article_id,
            ArticleVersion.version == article.latest_version,
        )
    ).scalar_one_or_none()
    if not version:
        raise HTTPException(404, "article version not found")
    title = item.title if item else f"Article {article_id}"
    if format == "json":
        return {"article_id": article_id, "title": title, "version": article.latest_version, "body": version.body}
    if format == "txt":
        return Response(content=f"{title}\n\n{version.body}", media_type="text/plain")
    return Response(content=f"# {title}\n\n{version.body}", media_type="text/markdown")


@router.post('/articles/{article_id}/read-state')
def mark_read_state(article_id: int, payload: MarkReadPayload, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(404)
    if payload.is_read:
        video_item_id = article.video_item_id
        db.query(CollectionArticle).filter(CollectionArticle.article_id == article_id).delete(synchronize_session=False)
        db.query(ReadingProgress).filter(ReadingProgress.article_id == article_id).delete(synchronize_session=False)
        db.query(ArticleVersion).filter(ArticleVersion.article_id == article_id).delete(synchronize_session=False)
        db.query(Article).filter(Article.id == article_id).delete(synchronize_session=False)
        # Keep the VideoItem row so future refreshes deduplicate by source+video_id and do not fetch again.
        db.query(Transcript).filter(Transcript.video_item_id == video_item_id).delete(synchronize_session=False)
        db.query(ItemStatusTransition).filter(ItemStatusTransition.video_item_id == video_item_id).delete(synchronize_session=False)
        db.query(JobItem).filter(JobItem.video_item_id == video_item_id).delete(synchronize_session=False)
        db.query(Job).filter(Job.video_item_id == video_item_id).delete(synchronize_session=False)
        video_item = db.get(VideoItem, video_item_id)
        if video_item:
            video_item.status = ItemStatus.skipped_by_policy
            video_item.status_message = "Marked read and removed by user"
        db.commit()
        return {"saved": True, "deleted": True}
    article.is_read = payload.is_read
    db.commit()
    return {"saved": True, "deleted": False}


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


@router.get('/collections/{collection_id}')
def collection_detail(collection_id: int, db: Session = Depends(get_db)):
    col = db.get(Collection, collection_id)
    if not col:
        raise HTTPException(404)
    rows = db.execute(
        select(Article.id, VideoItem.title)
        .join(CollectionArticle, CollectionArticle.article_id == Article.id)
        .join(VideoItem, VideoItem.id == Article.video_item_id)
        .where(CollectionArticle.collection_id == collection_id)
    ).all()
    return {"id": col.id, "name": col.name, "articles": [{"article_id": article_id, "title": title} for article_id, title in rows]}


@router.patch('/collections/{collection_id}')
def update_collection(collection_id: int, body: CollectionCreate, db: Session = Depends(get_db)):
    col = db.get(Collection, collection_id)
    if not col:
        raise HTTPException(404)
    col.name = body.name
    db.commit()
    return {"saved": True}


@router.delete('/collections/{collection_id}')
def delete_collection(collection_id: int, db: Session = Depends(get_db)):
    col = db.get(Collection, collection_id)
    if not col:
        raise HTTPException(404)
    db.query(CollectionArticle).filter(CollectionArticle.collection_id == collection_id).delete()
    db.delete(col)
    db.commit()
    return {"deleted": True}


@router.post('/collections/{collection_id}/articles/{article_id}')
def add_collection_article(collection_id: int, article_id: int, db: Session = Depends(get_db)):
    col = db.get(Collection, collection_id)
    article = db.get(Article, article_id)
    if not col or not article:
        raise HTTPException(404)
    exists = db.execute(
        select(CollectionArticle).where(
            CollectionArticle.collection_id == collection_id,
            CollectionArticle.article_id == article_id,
        )
    ).scalar_one_or_none()
    if not exists:
        db.add(CollectionArticle(collection_id=collection_id, article_id=article_id))
        db.commit()
    return {"saved": True}


@router.delete('/collections/{collection_id}/articles/{article_id}')
def remove_collection_article(collection_id: int, article_id: int, db: Session = Depends(get_db)):
    db.query(CollectionArticle).filter(
        CollectionArticle.collection_id == collection_id,
        CollectionArticle.article_id == article_id,
    ).delete()
    db.commit()
    return {"deleted": True}


@router.get('/diagnostics')
def diagnostics(db: Session = Depends(get_db)):
    ffmpeg_command = "ffmpeg"
    yt_dlp_command = "yt-dlp"
    rows = db.execute(
        select(AppSetting).where(
            AppSetting.key.in_(["ffmpeg_path", "yt_dlp_path", "openai_api_key", "openai_base_url", "lmstudio_base_url"])
        )
    ).scalars().all()
    settings_map = {row.key: row.value.strip() for row in rows}
    ffmpeg_command = settings_map.get("ffmpeg_path") or ffmpeg_command
    yt_dlp_command = settings_map.get("yt_dlp_path") or yt_dlp_command
    openai_base_url = settings_map.get("openai_base_url") or DEFAULT_APP_SETTINGS["openai_base_url"]
    lmstudio_base_url = settings_map.get("lmstudio_base_url") or DEFAULT_APP_SETTINGS["lmstudio_base_url"]
    openai_api_key = settings_map.get("openai_api_key", "")
    ffmpeg_status = check_binary(ffmpeg_command, fallback="ffmpeg")
    yt_dlp_status = check_binary(yt_dlp_command, fallback="yt-dlp")

    return {
        'db': check_db(db),
        'storage': check_storage_writable("./tmp"),
        'ffmpeg': ffmpeg_status,
        'yt_dlp': yt_dlp_status,
        'faster_whisper': check_faster_whisper(),
        'openai_connectivity': check_openai_connectivity(openai_base_url, openai_api_key),
        'lmstudio_connectivity': check_lmstudio_connectivity(lmstudio_base_url),
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
    source_id: int | None = None,
    db: Session = Depends(get_db),
):
    rows = db.execute(select(LogEvent).order_by(LogEvent.created_at.desc()).limit(500)).scalars().all()
    out = []
    for row in rows:
        sanitized_context = redact_secrets(row.context or "")
        sanitized_message = redact_secrets(row.message or "")
        if severity and row.severity.lower() != severity.lower():
            continue
        if context and context.lower() not in sanitized_context.lower():
            continue
        if source_id is not None and f"source_id={source_id}" not in sanitized_context:
            continue
        if q and q.lower() not in sanitized_message.lower():
            continue
        row.context = sanitized_context
        row.message = sanitized_message
        out.append(row)
    return out
