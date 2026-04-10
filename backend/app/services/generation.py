from dataclasses import dataclass


@dataclass
class ProviderConfig:
    provider: str
    model: str
    temperature: float = 0.2


def render_prompt(template: str, transcript: str, mode: str) -> str:
    return template.replace("{{transcript}}", transcript).replace("{{mode}}", mode)


def generate_article(_transcript: str, _prompt: str, _cfg: ProviderConfig) -> str:
    raise NotImplementedError(
        "generate_article is a required integration point and still a placeholder. "
        "Implement provider API calls (OpenAI/LM Studio/etc.) before publishing articles."
    )
