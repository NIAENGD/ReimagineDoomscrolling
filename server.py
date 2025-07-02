"""Minimal helper server for transcription tasks."""

import json
import subprocess
import tempfile
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

# Directory for temporary downloads
TMP_BASE = Path(tempfile.gettempdir()) / "yt_tmp"
TMP_BASE.mkdir(parents=True, exist_ok=True)


def fetch_subtitles(url: str) -> str:
    """Return subtitles text for the given YouTube URL if available."""
    with tempfile.TemporaryDirectory(dir=TMP_BASE) as td:
        out = Path(td) / "%(id)s"
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-auto-sub",
            "--sub-lang",
            "en",
            "-o",
            str(out),
            url,
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        vtt_files = list(Path(td).glob("*.vtt"))
        if vtt_files:
            return vtt_files[0].read_text("utf-8")
    return ""


def whisper_transcribe(audio_path: Path) -> str:
    """Transcribe audio using the local Whisper CLI."""
    out_dir = audio_path.parent
    cmd = [
        "whisper",
        str(audio_path),
        "--model",
        "small",
        "--language",
        "en",
        "--output-format",
        "txt",
        "--output_dir",
        str(out_dir),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    txt_file = audio_path.with_suffix(".txt")
    if txt_file.exists():
        return txt_file.read_text("utf-8")
    return ""


@app.route("/api/subtitles", methods=["POST"])
def api_subtitles() -> jsonify:
    """Return a transcript for the requested YouTube URL."""
    data = request.get_json(force=True) or {}
    url = data.get("url")
    if not url:
        return jsonify({"error": "missing url"}), 400

    transcript = fetch_subtitles(url)
    if not transcript:
        with tempfile.TemporaryDirectory(dir=TMP_BASE) as td:
            audio = Path(td) / "audio"
            subprocess.run(
                [
                    "yt-dlp",
                    "-f",
                    "bestaudio",
                    "-o",
                    str(audio),
                    url,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            audio_file = audio.with_suffix(".webm")
            if audio_file.exists():
                transcript = whisper_transcribe(audio_file)

    return jsonify({"transcript": transcript})


@app.route("/")
def root():
    return "YT helper server running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
