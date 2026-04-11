from datetime import datetime, timedelta

from sqlalchemy import select

from app.models.entities import (
    AppSetting,
    Article,
    ArticleVersion,
    ItemStatus,
    Job,
    JobItem,
    ReadingProgress,
    RefreshRun,
    Source,
    Transcript,
    VideoItem,
)
from app.services.generation import ProviderConfig, generate_article, render_prompt
from app.services.transcript import fetch_transcript, should_fallback_to_transcription, transcribe_audio_locally
from app.services.youtube import discover_videos, evaluate_video_policy, normalize_source_url, resolve_source_identity


def _get_setting(db, key: str, default: str = "") -> str:
    row = db.execute(select(AppSetting).where(AppSetting.key == key)).scalar_one_or_none()
    return row.value if row and row.value is not None else default


def refresh_source(db, source_id: int):
    source = db.get(Source, source_id)
    if not source:
        return
    run = RefreshRun(source_id=source_id, status="running", summary="")
    db.add(run)
    db.flush()

    fetched_count = 0
    filtered_count = 0
    enqueued_count = 0
    duplicate_count = 0
    failed_count = 0

    try:
        source.url = normalize_source_url(source.url)
        try:
            resolved = resolve_source_identity(source.url)
            source.channel_id = resolved.get("channel_id", source.channel_id)
            source.canonical_url = resolved.get("canonical_url", source.canonical_url)
            if resolved.get("title"):
                source.title = resolved["title"]
            source.metadata_json = str(resolved)
        except Exception:
            pass
        videos = discover_videos(source)
        fetched_count = len(videos)
    except Exception as exc:
        db.add(Job(type="refresh_source", status="failed", source_id=source_id, error=str(exc)))
        source.failure_count += 1
        source.last_scan_at = datetime.utcnow()
        source.next_run_at = datetime.utcnow() + timedelta(minutes=min(240, max(10, source.cadence_minutes * (2 ** source.failure_count))))
        run.status = "failed"
        run.finished_at = datetime.utcnow()
        run.summary = f"error={exc}"
        db.commit()
        return

    for raw in videos:
        allowed, reason = evaluate_video_policy(raw, source)
        if not allowed:
            filtered_count += 1
            item = VideoItem(
                source_id=source_id,
                video_id=raw["video_id"],
                url=raw["url"],
                title=raw["title"],
                status=ItemStatus.skipped_by_policy,
                status_message=reason,
            )
            db.merge(item)
            continue
        exists_stmt = select(VideoItem).where(VideoItem.video_id == raw["video_id"])
        if source.dedup_policy == "source_video_id":
            exists_stmt = exists_stmt.where(VideoItem.source_id == source_id)
        exists = db.execute(exists_stmt).scalar_one_or_none()
        if exists:
            duplicate_count += 1
            continue
        item = VideoItem(source_id=source_id, video_id=raw["video_id"], url=raw["url"], title=raw["title"], status=ItemStatus.queued)
        db.add(item)
        db.flush()
        enqueued_count += 1
        try:
            process_video_item(db, item.id)
        except Exception:
            failed_count += 1

    source.last_scan_at = datetime.utcnow()
    source.last_success_at = datetime.utcnow()
    source.failure_count = 0
    source.next_run_at = datetime.utcnow() + timedelta(minutes=source.cadence_minutes)
    run.status = "done"
    run.finished_at = datetime.utcnow()
    run.summary = (
        f"fetched={fetched_count};filtered={filtered_count};"
        f"enqueued={enqueued_count};duplicates={duplicate_count};failed={failed_count}"
    )
    db.commit()


def process_video_item(db, item_id: int):
    item = db.get(VideoItem, item_id)
    if not item:
        return
    source = db.get(Source, item.source_id)

    try:
        item.status = ItemStatus.transcript_searching
        language_pref = _get_setting(db, "transcript_languages", "en")
        languages = [lang.strip() for lang in language_pref.split(",") if lang.strip()] or ["en"]
        text, source_kind = fetch_transcript(item.url, languages)

        strategy = source.transcript_strategy if source else "transcript_first"
        fallback_enabled = source.fallback_enabled if source else True
        fallback_used = False

        if not text and should_fallback_to_transcription(strategy, False, fallback_enabled):
            item.status = ItemStatus.transcription_started
            yt_dlp_command = _get_setting(db, "yt_dlp_path", "yt-dlp").strip() or "yt-dlp"
            text = transcribe_audio_locally(item.url, yt_dlp_command=yt_dlp_command)
            source_kind = "local_transcription"
            fallback_used = True
            item.status = ItemStatus.transcription_completed
        elif text:
            item.status = ItemStatus.transcript_found
        else:
            item.status = ItemStatus.transcript_unavailable

        transcript = db.execute(select(Transcript).where(Transcript.video_item_id == item.id)).scalar_one_or_none()
        if transcript:
            transcript.text = text
            transcript.source = source_kind
            transcript.language = languages[0]
            transcript.strategy = strategy
            transcript.fallback_used = fallback_used
            transcript.transcription_model = "faster-whisper-base-cpu-int8" if fallback_used else ""
            transcript.error_message = ""
            transcript.fetched_at = datetime.utcnow()
        else:
            db.add(
                Transcript(
                    video_item_id=item.id,
                    text=text,
                    source=source_kind,
                    language=languages[0],
                    strategy=strategy,
                    fallback_used=fallback_used,
                    transcription_model="faster-whisper-base-cpu-int8" if fallback_used else "",
                    fetched_at=datetime.utcnow(),
                )
            )

        item.status = ItemStatus.generation_started
        provider_name = _get_setting(db, "generation_provider", "openai")
        model_name = _get_setting(db, "generation_model", "gpt-4.1-mini")
        mode_name = _get_setting(db, "generation_mode", "detailed")
        global_template = _get_setting(db, "global_prompt_template", "Convert to {{mode}} article\n{{transcript}}")
        prompt_template = source.prompt_override if source and source.prompt_override else global_template
        prompt = render_prompt(prompt_template, text, mode_name)
        body = generate_article(text, prompt, ProviderConfig(provider=provider_name, model=model_name))

        article = db.execute(select(Article).where(Article.video_item_id == item.id)).scalar_one_or_none()
        if not article:
            article = Article(video_item_id=item.id, title=item.title, latest_version=1)
            db.add(article)
            db.flush()
            db.add(ReadingProgress(article_id=article.id, position=0, total=0))
            version_num = 1
        else:
            version_num = article.latest_version + 1
            article.latest_version = version_num

        db.add(ArticleVersion(article_id=article.id, version=version_num, mode=mode_name, prompt_snapshot=prompt, body=body))
        item.status = ItemStatus.published

        job = Job(type="process_item", status="done", video_item_id=item.id, source_id=item.source_id)
        db.add(job)
        db.flush()
        db.add(JobItem(job_id=job.id, video_item_id=item.id, status="done"))
    except Exception as exc:
        max_attempts = max(0, source.retry_max_attempts if source else 0)
        item.retry_count = (item.retry_count or 0) + 1
        if item.retry_count <= max_attempts:
            base = max(1, source.retry_backoff_minutes if source else 10)
            mul = max(1, source.retry_backoff_multiplier if source else 2)
            item.status = ItemStatus.retry_pending
            item.next_retry_at = datetime.utcnow() + timedelta(minutes=base * (mul ** max(0, item.retry_count - 1)))
        else:
            item.status = ItemStatus.failed
        item.status_message = str(exc)
        transcript = db.execute(select(Transcript).where(Transcript.video_item_id == item.id)).scalar_one_or_none()
        if transcript:
            transcript.error_message = str(exc)
        job = Job(type="process_item", status="failed", video_item_id=item.id, source_id=item.source_id, error=str(exc))
        db.add(job)
        db.flush()
        db.add(JobItem(job_id=job.id, video_item_id=item.id, status="failed", error=str(exc)))
        db.commit()
        raise

    db.commit()
