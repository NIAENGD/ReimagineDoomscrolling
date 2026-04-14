from fastapi.testclient import TestClient

from app.main import app


def test_update_settings_and_diagnostics_and_logs_flow(monkeypatch):
    with TestClient(app) as client:
        put = client.put('/api/settings', json={'scheduler_enabled': False, 'openai_api_key': 'sk-test-secret'})
        assert put.status_code == 200

        diag = client.get('/api/diagnostics')
        assert diag.status_code == 200
        payload = diag.json()
        assert 'storage' in payload
        assert 'yt_dlp' in payload and 'version' in payload['yt_dlp']
        assert 'openai_connectivity' in payload

        # Seed logs with a secret-looking string and verify redaction on output.
        from app.db.session import SessionLocal
        from app.models.entities import LogEvent

        db = SessionLocal()
        try:
            db.add(LogEvent(severity='INFO', context='ctx', message='api_key=my-very-secret-token'))
            db.commit()
        finally:
            db.close()

        logs = client.get('/api/logs?q=redacted')
        assert logs.status_code == 200
        assert any('***redacted***' in row['message'] for row in logs.json())


def test_source_refresh_deduplicates_and_records_status_timeline(monkeypatch):
    from app.services import pipeline

    def fake_discover(_source):
        return [
            {'video_id': 'vid-1', 'url': 'https://www.youtube.com/watch?v=vid-1', 'title': 'One', 'duration': 300, 'is_live': False},
            {'video_id': 'vid-1', 'url': 'https://www.youtube.com/watch?v=vid-1', 'title': 'One duplicate', 'duration': 300, 'is_live': False},
        ]

    monkeypatch.setattr(pipeline, 'discover_videos', fake_discover)
    monkeypatch.setattr(pipeline, 'resolve_source_identity', lambda _url: {'normalized_url': 'https://www.youtube.com/channel/xyz', 'canonical_url': 'https://www.youtube.com/channel/xyz', 'channel_id': 'xyz', 'title': 'XYZ'})
    monkeypatch.setattr(pipeline, 'fetch_transcript', lambda *_args, **_kwargs: ('hello world', 'youtube_transcript'))
    monkeypatch.setattr(pipeline, 'generate_article', lambda *_args, **_kwargs: 'Generated body\nd}[/"One"%x^#')

    with TestClient(app) as client:
        s = client.post('/api/sources', json={'url': 'https://youtube.com/channel/xyz', 'title': 'XYZ', 'max_videos': 2})
        assert s.status_code == 200
        sid = s.json()['id']

        rr = client.post(f'/api/sources/{sid}/refresh')
        assert rr.status_code == 200

        lib = client.get('/api/library')
        assert lib.status_code == 200
        assert len(lib.json()) == 1

        item_id = lib.json()[0]['video_item_id']
        timeline = client.get(f'/api/items/{item_id}/timeline')
        assert timeline.status_code == 200
        assert len(timeline.json()) >= 3


def test_create_source_triggers_initial_refresh(monkeypatch):
    from app.api import routes

    calls: list[int] = []

    monkeypatch.setattr(
        routes,
        "resolve_source_identity",
        lambda url: {
            "normalized_url": url,
            "canonical_url": "https://www.youtube.com/channel/UCTESTCHANNEL",
            "channel_id": "UCTESTCHANNEL",
            "title": "Economics Explained",
            "last_discovered_count": 0,
        },
    )
    monkeypatch.setattr(routes, "refresh_source", lambda _db, source_id: calls.append(source_id))

    with TestClient(app) as client:
        created = client.post(
            "/api/sources",
            json={"url": "https://www.youtube.com/@EconomicsExplained", "title": "Economics Explained"},
        )
        assert created.status_code == 200
        source_id = created.json()["id"]
        assert calls == [source_id]
