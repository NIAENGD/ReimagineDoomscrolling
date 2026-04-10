from datetime import datetime

from sqlalchemy import select

from app.models.entities import Article, ArticleVersion, ItemStatus, Job, Source, Transcript, VideoItem
from app.services.generation import ProviderConfig, generate_article, render_prompt
from app.services.transcript import fetch_transcript, should_fallback_to_transcription, transcribe_audio_locally
from app.services.youtube import discover_videos, evaluate_video_policy


def refresh_source(db, source_id: int):
    source = db.get(Source, source_id)
    try:
        videos = discover_videos(source)
    except NotImplementedError as exc:
        db.add(Job(type="refresh_source", status="failed", source_id=source_id, error=str(exc)))
        source.failure_count += 1
        source.last_scan_at = datetime.utcnow()
        db.commit()
        return

    for raw in videos:
        allowed, reason = evaluate_video_policy(raw, source)
        if not allowed:
            item = VideoItem(source_id=source_id, video_id=raw["video_id"], url=raw["url"], title=raw["title"], status=ItemStatus.skipped_by_policy, status_message=reason)
            db.merge(item)
            continue
        exists = db.execute(select(VideoItem).where(VideoItem.source_id == source_id, VideoItem.video_id == raw["video_id"])).scalar_one_or_none()
        if exists:
            continue
        item = VideoItem(source_id=source_id, video_id=raw["video_id"], url=raw["url"], title=raw["title"], status=ItemStatus.queued)
        db.add(item)
        db.flush()
        process_video_item(db, item.id)
    source.last_scan_at = datetime.utcnow()
    source.last_success_at = datetime.utcnow()
    db.commit()


def process_video_item(db, item_id: int):
    item = db.get(VideoItem, item_id)

    try:
        item.status = ItemStatus.transcript_searching
        text, source_kind = fetch_transcript(item.url, ["en"])

        if not text and should_fallback_to_transcription("transcript_first", False, True):
            item.status = ItemStatus.transcription_started
            text = transcribe_audio_locally(item.url)
            source_kind = "local_transcription"
            item.status = ItemStatus.transcription_completed
        else:
            item.status = ItemStatus.transcript_found

        transcript = db.execute(select(Transcript).where(Transcript.video_item_id == item.id)).scalar_one_or_none()
        if transcript:
            transcript.text = text
            transcript.source = source_kind
        else:
            db.add(Transcript(video_item_id=item.id, text=text, source=source_kind))

        item.status = ItemStatus.generation_started
        prompt = render_prompt("Convert to {{mode}} article\n{{transcript}}", text, "detailed")
        body = generate_article(text, prompt, ProviderConfig(provider="openai", model="gpt-4.1-mini"))

        article = db.execute(select(Article).where(Article.video_item_id == item.id)).scalar_one_or_none()
        if not article:
            article = Article(video_item_id=item.id, title=item.title)
            db.add(article)
            db.flush()
            version_num = 1
        else:
            version_num = article.latest_version + 1
            article.latest_version = version_num

        db.add(ArticleVersion(article_id=article.id, version=version_num, mode="detailed", prompt_snapshot=prompt, body=body))
        item.status = ItemStatus.published
        db.add(Job(type="process_item", status="done", video_item_id=item.id, source_id=item.source_id))
    except NotImplementedError as exc:
        item.status = ItemStatus.failed
        item.status_message = str(exc)
        db.add(Job(type="process_item", status="failed", video_item_id=item.id, source_id=item.source_id, error=str(exc)))

    db.commit()
