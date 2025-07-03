"""Minimal helper server for transcription tasks."""

import json
import subprocess
import tempfile
from pathlib import Path

from flask import Flask, jsonify, request
import sqlite3
import pyautogui
import pygetwindow as gw
import time

pyautogui.FAILSAFE = False

# Default Whisper settings
WHISPER_MODEL = "small"
WHISPER_LANGUAGE = "en"

app = Flask(__name__)

# Path for local database
DB_PATH = Path("articles.db")

# Directory for temporary downloads
TMP_BASE = Path(tempfile.gettempdir()) / "yt_tmp"
TMP_BASE.mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    """Ensure the SQLite database exists with the required table."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                title TEXT,
                score TEXT,
                article TEXT,
                transcript TEXT,
                liked INTEGER DEFAULT 0,
                disliked INTEGER DEFAULT 0
            )
            """
        )


def fetch_subtitles(url: str, lang: str = WHISPER_LANGUAGE) -> str:
    """Return subtitles text for the given YouTube URL if available."""
    with tempfile.TemporaryDirectory(dir=TMP_BASE) as td:
        out = Path(td) / "%(id)s"
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-auto-sub",
            "--sub-lang",
            lang,
            "-o",
            str(out),
            url,
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        vtt_files = list(Path(td).glob("*.vtt"))
        if vtt_files:
            return vtt_files[0].read_text("utf-8")
    return ""


def whisper_transcribe(
    audio_path: Path,
    model: str = WHISPER_MODEL,
    language: str = WHISPER_LANGUAGE,
) -> str:
    """Transcribe audio using the local Whisper CLI."""
    out_dir = audio_path.parent
    cmd = [
        "whisper",
        str(audio_path),
        "--model",
        model,
        "--language",
        language,
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

    transcript = fetch_subtitles(url, WHISPER_LANGUAGE)
    if not transcript:
        with tempfile.TemporaryDirectory(dir=TMP_BASE) as td:
            audio = Path(td) / "audio"
            subprocess.run(
                [
                    "yt-dlp",
                    "-f",
                    "worstaudio",
                    "-o",
                    str(audio),
                    url,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            audio_file = audio.with_suffix(".webm")
            if audio_file.exists():
                transcript = whisper_transcribe(audio_file, WHISPER_MODEL, WHISPER_LANGUAGE)

    return jsonify({"transcript": transcript})


@app.route("/api/click", methods=["POST"])
def api_click() -> jsonify:
    """Simulate a mouse click at the provided screen coordinates."""
    data = request.get_json(force=True) or {}
    x = data.get("x")
    y = data.get("y")
    if x is None or y is None:
        return jsonify({"error": "missing coordinates"}), 400
    pyautogui.click(x, y)
    time.sleep(0.1)
    return jsonify({"status": "ok"})


@app.route("/api/type", methods=["POST"])
def api_type() -> jsonify:
    """Type the given text using the keyboard."""
    data = request.get_json(force=True) or {}
    text = data.get("text", "")
    pyautogui.write(text, interval=0.02)
    return jsonify({"status": "ok"})


@app.route("/api/arrange", methods=["POST"])
def api_arrange() -> jsonify:
    """Arrange YouTube and ChatGPT windows side by side."""
    data = request.get_json(force=True) or {}
    yt_title = data.get("youtube_title", "YouTube")
    gpt_title = data.get("chatgpt_title", "ChatGPT")

    width, height = pyautogui.size()
    half = width // 2

    for w in gw.getWindowsWithTitle(yt_title):
        try:
            w.moveTo(0, 0)
            w.resizeTo(half, height)
            break
        except Exception:
            continue

    for w in gw.getWindowsWithTitle(gpt_title):
        try:
            w.moveTo(half, 0)
            w.resizeTo(width - half, height)
            break
        except Exception:
            continue

    return jsonify({"status": "ok"})


@app.route("/api/article", methods=["POST"])
def api_article() -> jsonify:
    """Persist a processed article and return its ID."""
    data = request.get_json(force=True) or {}
    url = data.get("url")
    if not url:
        return jsonify({"error": "missing url"}), 400

    title = data.get("title", "")
    score = json.dumps(data.get("score") or {})
    article_text = data.get("article", "")
    transcript = data.get("transcript", "")
    liked = int(bool(data.get("liked")))
    disliked = int(bool(data.get("disliked")))

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO articles (url, title, score, article, transcript, liked, disliked)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                title=excluded.title,
                score=excluded.score,
                article=excluded.article,
                transcript=excluded.transcript,
                liked=excluded.liked,
                disliked=excluded.disliked
            """,
            (url, title, score, article_text, transcript, liked, disliked),
        )
        row = conn.execute("SELECT id FROM articles WHERE url=?", (url,)).fetchone()
    return jsonify({"id": row[0]})


@app.route("/api/articles")
def api_articles() -> jsonify:
    """Return list of stored articles."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, url, title, score, liked, disliked FROM articles"
        ).fetchall()
    articles = []
    for r in rows:
        score = json.loads(r["score"] or "{}")
        articles.append(
            {
                "id": r["id"],
                "url": r["url"],
                "title": r["title"],
                "score": score,
                "liked": bool(r["liked"]),
                "disliked": bool(r["disliked"]),
            }
        )
    return jsonify({"articles": articles})


@app.route("/api/article/<int:aid>")
def api_get_article(aid: int) -> jsonify:
    """Return a single stored article."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM articles WHERE id=?", (aid,)).fetchone()
    if not row:
        return jsonify({"error": "not found"}), 404
    article = {
        "id": row["id"],
        "url": row["url"],
        "title": row["title"],
        "score": json.loads(row["score"] or "{}"),
        "article": row["article"],
        "transcript": row["transcript"],
        "liked": bool(row["liked"]),
        "disliked": bool(row["disliked"]),
    }
    return jsonify(article)


@app.route("/")
def root():
    return "YT helper server running"

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Local helper server")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="interface to bind (default 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5001,
        help="port to use (default 5001)",
    )
    parser.add_argument(
        "--whisper-model",
        default=WHISPER_MODEL,
        help="Whisper model size (default small)",
    )
    parser.add_argument(
        "--whisper-language",
        default=WHISPER_LANGUAGE,
        help="Language code for Whisper and subtitles (default en)",
    )

    args = parser.parse_args()

    WHISPER_MODEL = args.whisper_model
    WHISPER_LANGUAGE = args.whisper_language

    init_db()

    app.run(host=args.host, port=args.port)
