from __future__ import annotations

import os
import subprocess
import tempfile
import time
from urllib.parse import parse_qs, urlparse

from faster_whisper import WhisperModel


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


def transcribe_audio_locally(
    video_url: str,
    yt_dlp_command: str = "yt-dlp",
    ffmpeg_command: str = "ffmpeg",
    retain_audio_on_failure: bool = False,
    retention_dir: str = "./tmp/failed_audio",
    delete_audio_after_success: bool = True,
) -> tuple[str, dict]:
    with tempfile.TemporaryDirectory(prefix="reimagine_transcribe_") as temp_dir:
        audio_path = os.path.join(temp_dir, "audio.%(ext)s")
        yt_dlp_attempts = [
            [
                yt_dlp_command,
                "--no-playlist",
                "-f",
                "bestaudio/best",
                "-x",
                "--audio-format",
                "mp3",
                "-o",
                audio_path,
                video_url,
            ],
            [
                yt_dlp_command,
                "--no-playlist",
                "--extractor-args",
                "youtube:player_client=android,web",
                "-f",
                "bestaudio/best",
                "-x",
                "--audio-format",
                "mp3",
                "-o",
                audio_path,
                video_url,
            ],
        ]
        yt_dlp_error = ""
        for cmd in yt_dlp_attempts:
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                yt_dlp_error = ""
                break
            except subprocess.CalledProcessError as exc:
                stderr = (exc.stderr or "").strip()
                stdout = (exc.stdout or "").strip()
                output = stderr or stdout or str(exc)
                yt_dlp_error = output[-1200:]
        if yt_dlp_error:
            raise RuntimeError(f"yt-dlp failed after {len(yt_dlp_attempts)} attempts: {yt_dlp_error}")
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
            retained = ""
            if not delete_audio_after_success:
                persist_dir = os.path.join(retention_dir, "successful")
                os.makedirs(persist_dir, exist_ok=True)
                retained = os.path.join(persist_dir, f"{video_id_from_url(video_url)}.wav")
                with open(normalized_path, "rb") as src, open(retained, "wb") as dest:
                    dest.write(src.read())
            return transcript, {"transcription_seconds": elapsed, "audio_retained_path": retained}
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
