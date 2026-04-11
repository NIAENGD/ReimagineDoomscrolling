from types import SimpleNamespace

import pytest

from app.services.generation import ProviderConfig, generate_article, render_prompt
from app.services.transcript import should_fallback_to_transcription
from app.services.youtube import evaluate_video_policy, normalize_source_url, resolve_source_identity


def test_resolve_source_identity_supports_handle_urls(monkeypatch):
    channel_id = "UCabcdefghijklmnopqrstuvwxyz123456"

    class FakeResponse:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            return None

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url):
            if "feeds/videos.xml" in url:
                return FakeResponse(f"""<?xml version='1.0' encoding='UTF-8'?><feed xmlns='http://www.w3.org/2005/Atom' xmlns:yt='http://www.youtube.com/xml/schemas/2015'><title>My Channel</title><yt:channelId>{channel_id}</yt:channelId><entry><yt:videoId>abc123</yt:videoId><title>Video</title><published>Wed, 01 Jan 2025 00:00:00 GMT</published></entry></feed>""")
            return FakeResponse(f'<html><script>"externalId":"{channel_id}"</script></html>')

    monkeypatch.setattr("app.services.youtube.httpx.Client", FakeClient)
    resolved = resolve_source_identity("https://www.youtube.com/@myhandle")
    assert resolved["channel_id"] == channel_id
    assert resolved["canonical_url"] == f"https://www.youtube.com/channel/{channel_id}"


def test_normalize_url():
    assert normalize_source_url('https://youtube.com/channel/abc?x=1') == 'https://www.youtube.com/channel/abc'


def test_policy_eval_short_filtered():
    source = SimpleNamespace(skip_shorts=True, min_duration_seconds=30, skip_livestreams=True, discovery_mode='latest_n', rolling_window_hours=72)
    allowed, reason = evaluate_video_policy({'duration': 40, 'is_live': False}, source)
    assert not allowed and reason == 'short'


def test_fallback_logic():
    assert should_fallback_to_transcription('transcript_first', False, True)
    assert not should_fallback_to_transcription('disable_fallback', False, True)


def test_prompt_and_generation_provider_validation():
    prompt = render_prompt('Mode={{mode}}\n{{transcript}}', 'abc', 'study')
    with pytest.raises(ValueError):
        generate_article('abc', prompt, ProviderConfig(provider='unsupported-provider', model='x'))
