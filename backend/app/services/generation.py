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
    return ""


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
                    "以原作者视角，忠实呈现视频中的观点、思路、结构和情绪，不加任何旁人评价或个人观点。标题/小标题分明，段落清晰；语言优美自然，贴合原风格。原汁原味还原引用、比喻、故事、幽默等表现手法；保持视频作者的个性（如讽刺、深情等）。开头简要介绍视频内容，结尾收束主要结论或号召；绝不提及“视频”，直接以文章形式呈现。切记！这并不是一个TLDR，或是总结，而是完整的文稿。切记！必须使用中文回答。切记！这不是一个总结，你需要输出尽量还原原视频的长度，不要缩短任何地方。 "
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
