from fastapi.testclient import TestClient

from app.main import app


def test_settings_source_refresh_library_flow():
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
        assert len(lib.json()) >= 1

        aid = lib.json()[0]['article_id']
        regen = client.post(f'/api/articles/{aid}/regenerate')
        assert regen.status_code == 200

        detail = client.get(f'/api/articles/{aid}')
        assert detail.status_code == 200
        assert len(detail.json()['versions']) >= 1
