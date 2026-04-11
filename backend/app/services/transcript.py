from __future__ import annotations

import os
import subprocess
import tempfile
from urllib.parse import parse_qs, urlparse

from faster_whisper import WhisperModel
from youtube_transcript_api import YouTubeTranscriptApi


def select_transcript_strategy(source) -> str:
    return source.transcript_strategy


def should_fallback_to_transcription(strategy: str, transcript_found: bool, fallback_enabled: bool) -> bool:
    if strategy == "force_local_transcription":
        return True
    if strategy == "disable_fallback":
        return False
    return not transcript_found and fallback_enabled


def _extract_video_id(video_url: str) -> str:
    parsed = urlparse(video_url)
    if parsed.netloc.endswith("youtu.be"):
        return parsed.path.lstrip("/")
    query = parse_qs(parsed.query)
    if "v" in query and query["v"]:
        return query["v"][0]
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2 and parts[0] in {"embed", "shorts"}:
        return parts[1]
    raise ValueError("Unable to parse YouTube video id from URL")


def fetch_transcript(video_url: str, languages: list[str]) -> tuple[str, str]:
    video_id = _extract_video_id(video_url)
    language_order = languages or ["en"]

    snippets = YouTubeTranscriptApi().fetch(video_id, languages=language_order)
    text = "\n".join(part.text.strip() for part in snippets if part.text.strip())
    if not text:
        return "", "youtube_transcript"
    return text, "youtube_transcript"


def transcribe_audio_locally(video_url: str, yt_dlp_command: str = "yt-dlp") -> str:
    with tempfile.TemporaryDirectory(prefix="reimagine_transcribe_") as temp_dir:
        audio_path = os.path.join(temp_dir, "audio.%(ext)s")
        cmd = [
            yt_dlp_command,
            "-f",
            "bestaudio/best",
            "-x",
            "--audio-format",
            "mp3",
            "-o",
            audio_path,
            video_url,
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)

        mp3_path = os.path.join(temp_dir, "audio.mp3")
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(mp3_path)
        transcript = "\n".join(segment.text.strip() for segment in segments if segment.text.strip())
        return transcript
