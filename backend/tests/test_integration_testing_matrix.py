from fastapi.testclient import TestClient

from app.main import app

REAL_LIFE_LORE_URL = "https://www.youtube.com/@RealLifeLore"


def _create_source(client: TestClient, suffix: str = "") -> int:
    response = client.post(
        "/api/sources",
        json={
            "url": f"{REAL_LIFE_LORE_URL}{suffix}",
            "title": "RealLifeLore",
            "max_videos": 5,
            "retry_max_attempts": 1,
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_integration_real_life_lore_refresh_discovery_and_generation(monkeypatch):
    from app.services import pipeline

    monkeypatch.setattr(
        pipeline,
        "resolve_source_identity",
        lambda _url: {
            "normalized_url": REAL_LIFE_LORE_URL,
            "canonical_url": "https://www.youtube.com/channel/UCP5tjEmvPItGyLhmjdwP7Ww",
            "channel_id": "UCP5tjEmvPItGyLhmjdwP7Ww",
            "title": "RealLifeLore",
        },
    )
    monkeypatch.setattr(
        pipeline,
        "discover_videos",
        lambda _source: [
            {
                "video_id": "rll-1",
                "url": "https://www.youtube.com/watch?v=rll-1",
                "title": "How Geography Shapes War",
                "duration": 900,
                "is_live": False,
            },
            {
                "video_id": "rll-2",
                "url": "https://www.youtube.com/watch?v=rll-2",
                "title": "The Hidden Cost of Islands",
                "duration": 840,
                "is_live": False,
            },
        ],
    )
    monkeypatch.setattr(pipeline, "fetch_transcript", lambda *_args, **_kwargs: ("Transcript text", "youtube_transcript"))
    monkeypatch.setattr(
        pipeline,
        "generate_article",
        lambda *_args, **_kwargs: 'Generated article body\nd}[/"Geography and Island Economics"%x^#',
    )

    with TestClient(app) as client:
        source_id = _create_source(client)

        refresh = client.post(f"/api/sources/{source_id}/refresh")
        assert refresh.status_code == 200

        library = client.get("/api/library")
        assert library.status_code == 200
        assert len(library.json()) >= 2

        item_id = library.json()[0]["video_item_id"]
        transcript = client.get(f"/api/transcripts/{item_id}")
        assert transcript.status_code == 200
        assert transcript.json()["source"] == "youtube_transcript"

        timeline = client.get(f"/api/items/{item_id}/timeline")
        assert timeline.status_code == 200
        statuses = [step["to_status"] for step in timeline.json()]
        assert "transcript_found" in statuses
        assert "generation_completed" in statuses
        assert "published" in statuses


def test_integration_transcript_fallback_retry_and_regeneration(monkeypatch):
    from app.services import pipeline

    monkeypatch.setattr(
        pipeline,
        "resolve_source_identity",
        lambda _url: {
            "normalized_url": REAL_LIFE_LORE_URL,
            "canonical_url": "https://www.youtube.com/channel/UCP5tjEmvPItGyLhmjdwP7Ww",
            "channel_id": "UCP5tjEmvPItGyLhmjdwP7Ww",
            "title": "RealLifeLore",
        },
    )
    monkeypatch.setattr(
        pipeline,
        "discover_videos",
        lambda _source: [
            {
                "video_id": "rll-fallback-1",
                "url": "https://www.youtube.com/watch?v=rll-fallback-1",
                "title": "Fallback Path",
                "duration": 700,
                "is_live": False,
            }
        ],
    )

    calls = {"transcribe": 0, "generate": 0}

    def fake_fetch(*_args, **_kwargs):
        raise RuntimeError("transcript unavailable")

    def fake_transcribe(*_args, **kwargs):
        calls["transcribe"] += 1
        assert kwargs.get("delete_audio_after_success") is True
        if calls["transcribe"] == 1:
            raise RuntimeError("yt-dlp failed")
        return "Fallback transcript", {"transcription_seconds": 1, "audio_retained_path": ""}

    def fake_generate(*_args, **_kwargs):
        calls["generate"] += 1
        return f'Generated v{calls["generate"]}\n' + 'd}[/"Fallback Path"%x^#'

    monkeypatch.setattr(pipeline, "fetch_transcript", fake_fetch)
    monkeypatch.setattr(pipeline, "transcribe_audio_locally", fake_transcribe)
    monkeypatch.setattr(pipeline, "generate_article", fake_generate)

    with TestClient(app) as client:
        source_id = _create_source(client, "/fallback")

        refresh = client.post(f"/api/sources/{source_id}/refresh")
        assert refresh.status_code == 200

        jobs = client.get("/api/jobs")
        assert jobs.status_code == 200
        failed_job = next(job for job in jobs.json() if job["status"] == "failed" and "yt-dlp failed" in (job.get("error") or ""))
        item_id = failed_job["video_item_id"]

        retry = client.post(f"/api/jobs/{failed_job['id']}/retry")
        assert retry.status_code == 200

        library = client.get("/api/library")
        assert library.status_code == 200
        article_id = library.json()[0]["article_id"]

        transcript = client.get(f"/api/transcripts/{item_id}")
        assert transcript.status_code == 200
        assert transcript.json()["source"] == "local_transcription"
        assert transcript.json()["fallback_used"] is True

        regenerated = client.post(f"/api/articles/{article_id}/regenerate")
        assert regenerated.status_code == 200

        detail = client.get(f"/api/articles/{article_id}")
        assert detail.status_code == 200
        assert detail.json()["latest_version"] >= 2
        assert len(detail.json()["versions"]) >= 2


def test_failure_paths_invalid_source_and_generation_provider_errors(monkeypatch):
    from app.services import pipeline

    with TestClient(app) as client:
        invalid = client.post("/api/sources", json={"url": "https://example.com/not-youtube", "title": "Bad"})
        assert invalid.status_code == 400

        client.put(
            "/api/settings",
            json={
                "generation_provider": "openai",
                "openai_api_key": "sk-invalid",
            },
        )

        monkeypatch.setattr(
            pipeline,
            "resolve_source_identity",
            lambda _url: {
                "normalized_url": REAL_LIFE_LORE_URL,
                "canonical_url": "https://www.youtube.com/channel/UCP5tjEmvPItGyLhmjdwP7Ww",
                "channel_id": "UCP5tjEmvPItGyLhmjdwP7Ww",
                "title": "RealLifeLore",
            },
        )
        monkeypatch.setattr(
            pipeline,
            "discover_videos",
            lambda _source: [
                {
                    "video_id": "rll-openai-fail",
                    "url": "https://www.youtube.com/watch?v=rll-openai-fail",
                    "title": "Provider Failure",
                    "duration": 901,
                    "is_live": False,
                }
            ],
        )
        monkeypatch.setattr(pipeline, "fetch_transcript", lambda *_args, **_kwargs: ("text", "youtube_transcript"))
        monkeypatch.setattr(pipeline, "generate_article", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("openai auth failure")))

        source_id = _create_source(client, "/provider-openai")
        refresh = client.post(f"/api/sources/{source_id}/refresh")
        assert refresh.status_code == 200

        jobs = client.get("/api/jobs")
        assert jobs.status_code == 200
        assert any(job["status"] == "failed" and "openai auth failure" in (job.get("error") or "") for job in jobs.json())

        client.put("/api/settings", json={"generation_provider": "lmstudio"})
        monkeypatch.setattr(pipeline, "generate_article", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("lm studio connection failure")))

        source_id_lm = _create_source(client, "/provider-lm")
        refresh_lm = client.post(f"/api/sources/{source_id_lm}/refresh")
        assert refresh_lm.status_code == 200

        jobs_after_lm = client.get("/api/jobs")
        assert jobs_after_lm.status_code == 200
        assert any(job["status"] == "failed" and "lm studio connection failure" in (job.get("error") or "") for job in jobs_after_lm.json())

        monkeypatch.setattr(pipeline, "generate_article", lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("malformed model response")))
        source_id_malformed = _create_source(client, "/provider-malformed")
        refresh_bad_shape = client.post(f"/api/sources/{source_id_malformed}/refresh")
        assert refresh_bad_shape.status_code == 200

        jobs_after_shape = client.get("/api/jobs")
        assert jobs_after_shape.status_code == 200
        assert any(job["status"] == "failed" and "malformed model response" in (job.get("error") or "") for job in jobs_after_shape.json())
