from fastapi.testclient import TestClient

from app.main import app


def test_settings_source_refresh_completes_without_placeholder_failures():
    with TestClient(app) as client:
        r = client.put('/api/settings', json={'provider': 'openai'})
        assert r.status_code == 200

        s = client.post('/api/sources', json={'url': 'https://youtube.com/channel/abc', 'title': 'ABC', 'max_videos': 2})
        assert s.status_code == 200
        sid = s.json()['id']

        rr = client.post(f'/api/sources/{sid}/refresh')
        assert rr.status_code == 200

        lib = client.get('/api/library')
        assert lib.status_code == 200

        jobs = client.get('/api/jobs')
        assert jobs.status_code == 200
        assert not any(job['status'] == 'failed' and job['type'] == 'refresh_source' for job in jobs.json())
