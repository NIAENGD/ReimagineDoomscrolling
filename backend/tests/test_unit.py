from types import SimpleNamespace

from app.services.generation import ProviderConfig, generate_article, render_prompt
from app.services.transcript import should_fallback_to_transcription
from app.services.youtube import evaluate_video_policy, normalize_source_url


def test_normalize_url():
    assert normalize_source_url('https://youtube.com/channel/abc?x=1') == 'https://www.youtube.com/channel/abc'


def test_policy_eval_short_filtered():
    source = SimpleNamespace(skip_shorts=True, min_duration_seconds=30, skip_livestreams=True, discovery_mode='latest_n', rolling_window_hours=72)
    allowed, reason = evaluate_video_policy({'duration': 40, 'is_live': False}, source)
    assert not allowed and reason == 'short'


def test_fallback_logic():
    assert should_fallback_to_transcription('transcript_first', False, True)
    assert not should_fallback_to_transcription('disable_fallback', False, True)


def test_prompt_and_provider():
    prompt = render_prompt('Mode={{mode}}\n{{transcript}}', 'abc', 'study')
    out = generate_article('abc', prompt, ProviderConfig(provider='openai', model='x'))
    assert 'openai:x' in out
