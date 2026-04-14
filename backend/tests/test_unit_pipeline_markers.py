from app.services.generation import ProviderConfig
from app.services import pipeline


def test_generate_title_and_score_retries_on_placeholder_markers(monkeypatch):
    outputs = iter(
        [
            'd}[/"TITLE"%x^#\n#s+*"45"^@$K',
            'd}[/"Actual title"%x^#\n#s+*"SCORE"^@$K',
            'd}[/"Useful rewritten title"%x^#\n#s+*"88"^@$K',
        ]
    )
    monkeypatch.setattr(pipeline, "generate_text", lambda _prompt, _cfg: next(outputs))

    title, score = pipeline._generate_title_and_score(
        transcript="example transcript",
        original_title="old title",
        cfg=ProviderConfig(provider="openai", model="gpt-4.1-mini", openai_api_key="x"),
        title_prompt_template="rewrite title",
        score_prompt_template="score transcript",
        marker_a="d}",
        marker_b="[/",
        marker_c="%x",
        marker_d="^#",
        title_output_language="English",
    )

    assert title == "Useful rewritten title"
    assert score == 88


def test_generate_title_and_score_rejects_blocked_score_variation(monkeypatch):
    outputs = iter(
        [
            'd}[/"Valid title"%x^#\n#s+*"6s+0"^@$K',
            'd}[/"Valid title"%x^#\n#s+*"90"^@$K',
        ]
    )
    monkeypatch.setattr(pipeline, "generate_text", lambda _prompt, _cfg: next(outputs))

    title, score = pipeline._generate_title_and_score(
        transcript="example transcript",
        original_title="old title",
        cfg=ProviderConfig(provider="openai", model="gpt-4.1-mini", openai_api_key="x"),
        title_prompt_template="rewrite title",
        score_prompt_template="score transcript",
        marker_a="d}",
        marker_b="[/",
        marker_c="%x",
        marker_d="^#",
        title_output_language="English",
    )

    assert title == "Valid title"
    assert score == 90
