from datetime import datetime, timedelta
import re

from sqlalchemy import select

from app.models.entities import (
    AppSetting,
    Article,
    ArticleVersion,
    ItemStatus,
    ItemStatusTransition,
    Job,
    JobItem,
    ReadingProgress,
    RefreshRun,
    Source,
    Transcript,
    VideoItem,
)
from app.services.generation import ProviderConfig, generate_article, generate_text, render_prompt
from app.services.ops import log_event
from app.services.transcript import fetch_transcript, should_fallback_to_transcription, transcribe_audio_locally
from app.services.youtube import discover_videos, evaluate_video_policy, normalize_source_url, resolve_source_identity


def _get_setting(db, key: str, default: str = "") -> str:
    row = db.execute(select(AppSetting).where(AppSetting.key == key)).scalar_one_or_none()
    return row.value if row and row.value is not None else default


def _set_item_status(db, item: VideoItem, to_status: ItemStatus, message: str = ""):
    from_status = item.status.value if item.status else ""
    item.status = to_status
    if message:
        item.status_message = message
    db.add(
        ItemStatusTransition(
            video_item_id=item.id,
            from_status=from_status,
            to_status=to_status.value,
            message=message,
        )
    )


def _extract_single_marker(text: str, pattern: str) -> str:
    matches = re.findall(pattern, text, flags=re.DOTALL)
    if len(matches) != 1:
        return ""
    return matches[0].strip()


def _is_placeholder_value(value: str, placeholder: str) -> bool:
    return value.strip().strip('"').casefold() == placeholder.strip().strip('"').casefold()


def _contains_blocked_marker(text: str, marker_start: str, marker_end: str, blocked_literal: str) -> bool:
    escaped_start = re.escape(marker_start)
    escaped_end = re.escape(marker_end)
    pattern = f"{escaped_start}\\\"([^\\\"]+)\\\"{escaped_end}"
    matches = re.findall(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not matches:
        return False
    return any(_is_placeholder_value(value, blocked_literal) for value in matches)


def _generate_title_and_score(
    transcript: str,
    original_title: str,
    cfg: ProviderConfig,
    title_prompt_template: str,
    score_prompt_template: str,
    marker_a: str,
    marker_b: str,
    marker_c: str,
    marker_d: str,
    title_output_language: str,
) -> tuple[str, int]:
    score_marker_start = "#s+*"
    score_marker_end = "^@$K"
    prompt = (
        f"{title_prompt_template}\n"
        f"{score_prompt_template}\n\n"
        f"Write the rewritten title in {title_output_language}.\n"
        f"1) After analysis, output title in this format: {marker_a}{marker_b}\"TITLE_TEXT\"{marker_c}{marker_d}\n"
        f"2) After analysis, output title in this format: {score_marker_start}\"0-100_INTEGER\"{score_marker_end}\n"
        f"Only output results in the described format with surrounding string identifications when you finish. Don't mention them in thinking proccess.\n"
        f"Original title:\n{original_title}\n\nTranscript:\n{transcript}"
    )
    title_escaped = [re.escape(s) for s in [marker_a, marker_b, marker_c, marker_d]]
    title_pattern = f"{title_escaped[0]}{title_escaped[1]}\\\"([^\\\"]+)\\\"{title_escaped[2]}{title_escaped[3]}"
    score_pattern = f"{re.escape(score_marker_start)}\\\"(\\d{{1,3}})\\\"{re.escape(score_marker_end)}"
    for _ in range(3):
        output = generate_text(prompt, cfg)
        title = _extract_single_marker(output, title_pattern)
        if not title or _is_placeholder_value(title, "TITLE"):
            continue
        if _contains_blocked_marker(output, score_marker_start, score_marker_end, "SCORE"):
            continue
        if _contains_blocked_marker(output, score_marker_start, score_marker_end, "6s+0"):
            continue
        score_raw = _extract_single_marker(output, score_pattern)
        if not score_raw:
            continue
        return title, max(0, min(100, int(score_raw)))
    raise ValueError("Could not produce a uniquely marked AI title and score after 3 attempts")


def refresh_source(db, source_id: int):
    source = db.get(Source, source_id)
    if not source:
        return
    run = RefreshRun(source_id=source_id, status="running", summary="")
    db.add(run)
    db.commit()
    db.refresh(run)

    fetched_count = 0
    filtered_count = 0
    enqueued_count = 0
    duplicate_count = 0
    failed_count = 0
    seen_video_ids: set[str] = set()

    try:
        log_event(db, "INFO", "refresh_source.start", "Starting source refresh", source_id=source_id)
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
        log_event(db, "ERROR", "refresh_source.error", f"Refresh failed: {exc}", source_id=source_id)
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
        if raw["video_id"] in seen_video_ids:
            duplicate_count += 1
            continue
        seen_video_ids.add(raw["video_id"])
        existing_for_video = db.execute(
            select(VideoItem).where(
                VideoItem.video_id == raw["video_id"],
                VideoItem.source_id == source_id,
            )
        ).scalar_one_or_none()
        allowed, reason = evaluate_video_policy(raw, source)
        if not allowed:
            filtered_count += 1
            if existing_for_video:
                existing_for_video.status = ItemStatus.skipped_by_policy
                existing_for_video.status_message = reason
            else:
                item = VideoItem(
                    source_id=source_id,
                    video_id=raw["video_id"],
                    url=raw["url"],
                    title=raw["title"],
                    thumbnail_url=f"https://i.ytimg.com/vi/{raw['video_id']}/hqdefault.jpg",
                    duration_seconds=int(raw.get("duration", 0) or 0),
                    status=ItemStatus.skipped_by_policy,
                    status_message=reason,
                )
                db.add(item)
            continue
        dedup_policy = (source.dedup_policy or "source_video_id").strip()
        if dedup_policy == "source_video_id":
            exists = existing_for_video
        elif dedup_policy == "title_source":
            exists = db.execute(
                select(VideoItem).where(
                    VideoItem.source_id == source_id,
                    VideoItem.title == raw["title"],
                )
            ).scalar_one_or_none()
        else:
            exists = db.execute(
                select(VideoItem).where(
                    VideoItem.source_id == source_id,
                    VideoItem.video_id == raw["video_id"],
                )
            ).scalar_one_or_none()
        if exists:
            duplicate_count += 1
            continue
        item = VideoItem(
            source_id=source_id,
            video_id=raw["video_id"],
            url=raw["url"],
            title=raw["title"],
            thumbnail_url=f"https://i.ytimg.com/vi/{raw['video_id']}/hqdefault.jpg",
            duration_seconds=int(raw.get("duration", 0) or 0),
            status=ItemStatus.queued,
        )
        db.add(item)
        db.flush()
        _set_item_status(db, item, ItemStatus.queued)
        db.commit()
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
    log_event(
        db,
        "INFO",
        "refresh_source.done",
        f"Refresh complete fetched={fetched_count} filtered={filtered_count} enqueued={enqueued_count} duplicates={duplicate_count} failed={failed_count}",
        source_id=source_id,
    )
    db.commit()


def process_video_item(db, item_id: int):
    item = db.get(VideoItem, item_id)
    if not item:
        return
    source = db.get(Source, item.source_id)

    try:
        log_event(db, "INFO", "process_item.start", "Starting item processing", source_id=item.source_id, item_id=item.id)
        _set_item_status(db, item, ItemStatus.metadata_fetched)
        _set_item_status(db, item, ItemStatus.transcript_searching)

        language_pref = _get_setting(db, "transcript_languages", "en")
        languages = [lang.strip() for lang in language_pref.split(",") if lang.strip()] or ["en"]

        strategy = source.transcript_strategy if source else "transcript_first"
        fallback_enabled = source.fallback_enabled if source else True
        text = ""
        source_kind = "youtube_transcript"
        fallback_used = False
        transcribe_meta = {"transcription_seconds": 0, "audio_retained_path": ""}

        if strategy != "force_local_transcription":
            try:
                text, source_kind = fetch_transcript(item.url, languages, strategy=strategy)
            except Exception:
                text = ""

        if not text and should_fallback_to_transcription(strategy, False, fallback_enabled):
            _set_item_status(db, item, ItemStatus.audio_downloaded)
            _set_item_status(db, item, ItemStatus.transcription_started)
            yt_dlp_command = _get_setting(db, "yt_dlp_path", "yt-dlp").strip() or "yt-dlp"
            ffmpeg_command = _get_setting(db, "ffmpeg_path", "ffmpeg").strip() or "ffmpeg"
            retain_failed = _get_setting(db, "retain_failed_audio", "false").lower() in {"1", "true", "yes", "on"}
            delete_audio_after_success = _get_setting(db, "delete_audio_after_success", "true").lower() in {"1", "true", "yes", "on"}
            text, transcribe_meta = transcribe_audio_locally(
                item.url,
                yt_dlp_command=yt_dlp_command,
                ffmpeg_command=ffmpeg_command,
                retain_audio_on_failure=retain_failed,
                delete_audio_after_success=delete_audio_after_success,
            )
            source_kind = "local_transcription"
            fallback_used = True
            _set_item_status(db, item, ItemStatus.transcription_completed)
        elif text:
            _set_item_status(db, item, ItemStatus.transcript_found)
        else:
            _set_item_status(db, item, ItemStatus.transcript_unavailable)

        transcript = db.execute(select(Transcript).where(Transcript.video_item_id == item.id)).scalar_one_or_none()
        if transcript:
            transcript.text = text
            transcript.source = source_kind
            transcript.language = languages[0]
            transcript.strategy = strategy
            transcript.fallback_used = fallback_used
            transcript.transcription_model = "faster-whisper-base-cpu-int8" if fallback_used else ""
            transcript.transcription_seconds = int(transcribe_meta.get("transcription_seconds", 0))
            transcript.audio_retained_path = transcribe_meta.get("audio_retained_path", "")
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
                    transcription_seconds=int(transcribe_meta.get("transcription_seconds", 0)),
                    audio_retained_path=transcribe_meta.get("audio_retained_path", ""),
                    fetched_at=datetime.utcnow(),
                )
            )

        _set_item_status(db, item, ItemStatus.generation_started)
        provider_name = _get_setting(db, "generation_provider", "openai")
        model_name = _get_setting(db, "generation_model", "gpt-4.1-mini")
        global_template = _get_setting(db, "global_prompt_template", "Convert the transcript into a polished article.\n\n{{transcript}}")
        timeout_seconds = float(_get_setting(db, "generation_timeout_seconds", "300"))
        temperature = float(_get_setting(db, "generation_temperature", "0.2"))
        max_tokens = int(_get_setting(db, "generation_max_tokens", "30000"))
        metadata_max_tokens = int(_get_setting(db, "generation_metadata_max_tokens", "512"))
        prompt_template = source.prompt_override if source and source.prompt_override else global_template
        title_prompt_template = _get_setting(
            db,
            "title_prompt_template",
            "Rewrite the video title into a descriptive, non-clickbait title that matches the transcript.",
        )
        score_prompt_template = _get_setting(
            db,
            "score_prompt_template",
            "Evaluate this video transcript with strict scoring and concise rationale.",
        )
        marker_a = _get_setting(db, "title_identifier_a", "d}")
        marker_b = _get_setting(db, "title_identifier_b", "[/")
        marker_c = _get_setting(db, "title_identifier_c", "%x")
        marker_d = _get_setting(db, "title_identifier_d", "^#")
        title_output_language = _get_setting(db, "title_output_language", "English")
        cfg = ProviderConfig(
            provider=provider_name,
            model=model_name,
            temperature=temperature,
            timeout_seconds=timeout_seconds,
            max_tokens=max_tokens,
            openai_api_key=_get_setting(db, "openai_api_key", ""),
            openai_base_url=_get_setting(db, "openai_base_url", ""),
            lmstudio_base_url=_get_setting(db, "lmstudio_base_url", ""),
        )
        metadata_cfg = ProviderConfig(
            provider=provider_name,
            model=model_name,
            temperature=temperature,
            timeout_seconds=timeout_seconds,
            max_tokens=metadata_max_tokens,
            openai_api_key=_get_setting(db, "openai_api_key", ""),
            openai_base_url=_get_setting(db, "openai_base_url", ""),
            lmstudio_base_url=_get_setting(db, "lmstudio_base_url", ""),
        )
        ai_title = item.title
        quality_report = ""
        quality_category = ""
        quality_score = 0
        if provider_name.lower() not in {"none", "raw", "raw_transcript"}:
            try:
                ai_title, quality_score = _generate_title_and_score(
                    text,
                    item.title,
                    metadata_cfg,
                    title_prompt_template,
                    score_prompt_template,
                    marker_a,
                    marker_b,
                    marker_c,
                    marker_d,
                    title_output_language,
                )
            except Exception as exc:
                log_event(db, "WARNING", "process_item.ai_title_score", f"AI title/score fallback: {exc}", source_id=item.source_id, item_id=item.id)
                ai_title = item.title
                quality_report, quality_category, quality_score = "", "", 0
        prompt = render_prompt(prompt_template, text, "")
        body = generate_article(text, prompt, cfg)

        article = db.execute(select(Article).where(Article.video_item_id == item.id)).scalar_one_or_none()
        if not article:
            article = Article(
                video_item_id=item.id,
                title=item.title,
                ai_title=ai_title,
                ai_video_category=quality_category,
                ai_quality_score=quality_score,
                ai_quality_report=quality_report,
                latest_version=1,
            )
            db.add(article)
            db.flush()
            db.add(ReadingProgress(article_id=article.id, position=0, total=0))
            version_num = 1
        else:
            version_num = article.latest_version + 1
            article.latest_version = version_num
            article.ai_title = ai_title
            article.ai_video_category = quality_category
            article.ai_quality_score = quality_score
            article.ai_quality_report = quality_report

        db.add(ArticleVersion(article_id=article.id, version=version_num, mode="default", prompt_snapshot=prompt, body=body))
        _set_item_status(db, item, ItemStatus.generation_completed)
        _set_item_status(db, item, ItemStatus.published)

        job = Job(type="process_item", status="done", video_item_id=item.id, source_id=item.source_id)
        db.add(job)
        db.flush()
        db.add(JobItem(job_id=job.id, video_item_id=item.id, status="done"))
        log_event(db, "INFO", "process_item.done", "Item processed successfully", source_id=item.source_id, item_id=item.id)
    except Exception as exc:
        global_attempts = int(_get_setting(db, "retry_default_max_attempts", "2"))
        global_base = int(_get_setting(db, "retry_default_backoff_minutes", "10"))
        global_mul = int(_get_setting(db, "retry_default_backoff_multiplier", "2"))
        max_attempts = max(0, source.retry_max_attempts if source else global_attempts)
        item.retry_count = (item.retry_count or 0) + 1
        if item.retry_count <= max_attempts:
            base = max(1, source.retry_backoff_minutes if source else global_base)
            mul = max(1, source.retry_backoff_multiplier if source else global_mul)
            _set_item_status(db, item, ItemStatus.retry_pending, str(exc))
            item.next_retry_at = datetime.utcnow() + timedelta(minutes=base * (mul ** max(0, item.retry_count - 1)))
        else:
            _set_item_status(db, item, ItemStatus.failed, str(exc))
        transcript = db.execute(select(Transcript).where(Transcript.video_item_id == item.id)).scalar_one_or_none()
        if transcript:
            transcript.error_message = str(exc)
        job = Job(type="process_item", status="failed", video_item_id=item.id, source_id=item.source_id, error=str(exc))
        db.add(job)
        db.flush()
        db.add(JobItem(job_id=job.id, video_item_id=item.id, status="failed", error=str(exc)))
        log_event(db, "ERROR", "process_item.error", f"Item processing failed: {exc}", source_id=item.source_id, item_id=item.id)
        db.commit()
        raise

    db.commit()
