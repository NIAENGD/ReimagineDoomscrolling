from __future__ import annotations

from dataclasses import dataclass

import httpx
import re

from app.core.config import settings


@dataclass
class ProviderConfig:
    provider: str
    model: str
    temperature: float = 0.2
    timeout_seconds: float = 60.0
    max_tokens: int = 1200
    openai_api_key: str = ""
    openai_base_url: str = ""
    lmstudio_base_url: str = ""


def render_prompt(template: str, transcript: str, mode: str) -> str:
    return template.replace("{{transcript}}", transcript).replace("{{mode}}", mode)


def _mode_instruction(prompt: str) -> str:
    lower = prompt.lower()
    if "concise" in lower:
        return "Write a concise article with short sections and minimal repetition."
    if "study_notes" in lower:
        return "Write study notes with headings, bullet points, and key takeaways."
    if "executive_brief" in lower:
        return "Write an executive brief with decisions, risks, and next actions."
    if "tutorial_reconstruction" in lower:
        return "Write a tutorial reconstruction with ordered steps and prerequisites."
    return "Write a detailed article with clear structure and examples."


def _chat_completion(base_url: str, api_key: str, model: str, prompt: str, temperature: float, timeout_seconds: float, max_tokens: int) -> str:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You convert transcripts into polished reading articles. "
                    "Return only the final article body. Do not include reasoning, chain-of-thought, thinking process, "
                    "analysis notes, scratchpad text, or XML tags like <think>. "
                    f"{_mode_instruction(prompt)}"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
    }

    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.post(f"{base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()

    body = response.json()
    raw = body["choices"][0]["message"]["content"].strip()
    return _strip_reasoning_artifacts(raw)


def generate_text(prompt: str, cfg: ProviderConfig) -> str:
    provider = (cfg.provider or "openai").lower()
    if provider in {"none", "raw", "raw_transcript"}:
        raise ValueError("Text generation is unavailable when provider is raw")

    if provider == "openai":
        if not (cfg.openai_api_key or settings.openai_api_key):
            raise ValueError("OPENAI_API_KEY is required when provider is openai")
        return _chat_completion(
            base_url=cfg.openai_base_url or settings.openai_base_url,
            api_key=cfg.openai_api_key or settings.openai_api_key,
            model=cfg.model,
            prompt=prompt,
            temperature=cfg.temperature,
            timeout_seconds=cfg.timeout_seconds,
            max_tokens=cfg.max_tokens,
        )

    if provider in {"lmstudio", "openai_compatible"}:
        return _chat_completion(
            base_url=cfg.lmstudio_base_url or settings.lmstudio_base_url,
            api_key="",
            model=cfg.model,
            prompt=prompt,
            temperature=cfg.temperature,
            timeout_seconds=cfg.timeout_seconds,
            max_tokens=cfg.max_tokens,
        )

    raise ValueError(f"Unsupported generation provider: {cfg.provider}")


def _strip_reasoning_artifacts(text: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"```(?:thinking|reasoning)[\s\S]*?```", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _clean_raw_transcript(transcript: str) -> str:
    lines = []
    for raw_line in transcript.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^\[?\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\]?\s*[-–—]?\s*", "", line)
        line = re.sub(r"^\d+\s*$", "", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def generate_article(transcript: str, prompt: str, cfg: ProviderConfig) -> str:
    if not transcript.strip():
        return ""

    provider = (cfg.provider or "openai").lower()
    if provider in {"none", "raw", "raw_transcript"}:
        return _clean_raw_transcript(transcript)

    return generate_text(prompt, cfg)
