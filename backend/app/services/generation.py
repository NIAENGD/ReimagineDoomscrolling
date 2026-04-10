from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import settings


@dataclass
class ProviderConfig:
    provider: str
    model: str
    temperature: float = 0.2


def render_prompt(template: str, transcript: str, mode: str) -> str:
    return template.replace("{{transcript}}", transcript).replace("{{mode}}", mode)


def _chat_completion(base_url: str, api_key: str, model: str, prompt: str, temperature: float) -> str:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": "You convert transcripts into polished reading articles."},
            {"role": "user", "content": prompt},
        ],
    }

    with httpx.Client(timeout=60.0) as client:
        response = client.post(f"{base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()

    body = response.json()
    return body["choices"][0]["message"]["content"].strip()


def generate_article(transcript: str, prompt: str, cfg: ProviderConfig) -> str:
    if not transcript.strip():
        return ""

    provider = (cfg.provider or "openai").lower()
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when provider is openai")
        return _chat_completion(
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
            model=cfg.model,
            prompt=prompt,
            temperature=cfg.temperature,
        )

    if provider in {"lmstudio", "openai_compatible"}:
        return _chat_completion(
            base_url=settings.lmstudio_base_url,
            api_key="",
            model=cfg.model,
            prompt=prompt,
            temperature=cfg.temperature,
        )

    raise ValueError(f"Unsupported generation provider: {cfg.provider}")
