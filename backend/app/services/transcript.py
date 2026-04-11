from __future__ import annotations

import os
import subprocess
import tempfile
import time
from urllib.parse import parse_qs, urlparse

from faster_whisper import WhisperModel
from youtube_transcript_api import YouTubeTranscriptApi


def select_transcript_strategy(source) -> str:
    return source.transcript_strategy


def should_fallback_to_transcription(strategy: str, transcript_found: bool, fallback_enabled: bool) -> bool:
    normalized = (strategy or "").lower()
    if normalized == "force_local_transcription":
        return True
    if normalized in {"disable_fallback", "manual_only", "prefer_manual_then_auto", "auto_only"}:
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


def fetch_transcript(video_url: str, languages: list[str], strategy: str = "transcript_first") -> tuple[str, str]:
    video_id = _extract_video_id(video_url)
    language_order = languages or ["en"]

    normalized = (strategy or "").lower()
    fetched = YouTubeTranscriptApi().list(video_id)
    transcript_obj = None
    if normalized in {"manual_only", "prefer_manual_then_auto"}:
        transcript_obj = fetched.find_manually_created_transcript(language_order)
    elif normalized == "auto_only":
        transcript_obj = fetched.find_generated_transcript(language_order)
    else:
        transcript_obj = fetched.find_transcript(language_order)

    snippets = transcript_obj.fetch()
    text = "\n".join(part.text.strip() for part in snippets if part.text.strip())
    if not text:
        return "", "youtube_transcript"
    return text, "youtube_transcript"


def transcribe_audio_locally(
    video_url: str,
    yt_dlp_command: str = "yt-dlp",
    ffmpeg_command: str = "ffmpeg",
    retain_audio_on_failure: bool = False,
    retention_dir: str = "./tmp/failed_audio",
) -> tuple[str, dict]:
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
        normalized_path = os.path.join(temp_dir, "audio.normalized.wav")
        subprocess.run(
            [
                ffmpeg_command,
                "-y",
                "-i",
                mp3_path,
                "-ar",
                "16000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                normalized_path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        started = time.time()
        model = WhisperModel("base", device="cpu", compute_type="int8")
        try:
            segments, _ = model.transcribe(normalized_path)
            transcript = "\n".join(segment.text.strip() for segment in segments if segment.text.strip())
            elapsed = int(time.time() - started)
            return transcript, {"transcription_seconds": elapsed, "audio_retained_path": ""}
        except Exception:
            if retain_audio_on_failure:
                os.makedirs(retention_dir, exist_ok=True)
                retained = os.path.join(retention_dir, f"{video_id_from_url(video_url)}.wav")
                with open(normalized_path, "rb") as src, open(retained, "wb") as dest:
                    dest.write(src.read())
            else:
                retained = ""
            raise RuntimeError(f"Local transcription failed. retained_audio={retained}")


def video_id_from_url(video_url: str) -> str:
    return _extract_video_id(video_url)
