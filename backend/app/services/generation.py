from dataclasses import dataclass


@dataclass
class ProviderConfig:
    provider: str
    model: str
    temperature: float = 0.2


def render_prompt(template: str, transcript: str, mode: str) -> str:
    return template.replace("{{transcript}}", transcript).replace("{{mode}}", mode)


def generate_article(transcript: str, prompt: str, cfg: ProviderConfig) -> str:
    header = f"# {cfg.provider}:{cfg.model}\n"
    return header + prompt[:200] + "\n\n" + transcript[:1500]
