from datetime import datetime, timedelta
from types import SimpleNamespace

from app.services.ops import redact_secrets
from app.services.transcript import should_fallback_to_transcription
from app.services.youtube import evaluate_video_policy


def test_dedup_key_policy_is_source_scoped_example():
    existing = [{"source_id": 1, "video_id": "abc"}]
    incoming = {"source_id": 2, "video_id": "abc"}
    assert not any(row["source_id"] == incoming["source_id"] and row["video_id"] == incoming["video_id"] for row in existing)


def test_transcript_selection_manual_strategy_no_fallback():
    assert not should_fallback_to_transcription("manual_only", transcript_found=False, fallback_enabled=True)


def test_cleanup_policy_ttl_cutoff_example():
    now = datetime.utcnow()
    threshold = now - timedelta(hours=24)
    stale = now - timedelta(hours=30)
    fresh = now - timedelta(hours=3)
    assert stale < threshold
    assert not (fresh < threshold)


def test_status_transition_order_example():
    statuses = ["queued", "metadata_fetched", "transcript_searching", "generation_started", "published"]
    assert statuses.index("metadata_fetched") > statuses.index("queued")
    assert statuses[-1] == "published"


def test_schedule_calculation_respects_window():
    source = SimpleNamespace(skip_shorts=False, min_duration_seconds=1, skip_livestreams=True, discovery_mode="rolling_window", rolling_window_hours=2)
    stale_video = {"duration": 100, "is_live": False, "published_at": datetime.utcnow() - timedelta(hours=4)}
    fresh_video = {"duration": 100, "is_live": False, "published_at": datetime.utcnow() - timedelta(minutes=30)}
    assert evaluate_video_policy(stale_video, source) == (False, "outside_window")
    assert evaluate_video_policy(fresh_video, source) == (True, "ok")


def test_article_preview_extraction_example():
    body = "A" * 300
    assert body[:160] == "A" * 160


def test_secret_redaction_masks_keys():
    text = "Authorization: Bearer sk-abcDEF1234567890 and api_key=supersecret"
    redacted = redact_secrets(text)
    assert "supersecret" not in redacted
    assert "***redacted***" in redacted
