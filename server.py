"""Local helper server for transcript fetching, whisper fallback, and article storage."""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import pyautogui
import pygetwindow as gw
import pyperclip
from flask import Flask, jsonify, request

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


VTT_TIMESTAMP_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}\.\d{3}")


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a subprocess command and capture text output without raising."""
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def clean_vtt(raw_vtt: str) -> str:
    """Strip WEBVTT metadata/timestamps and dedupe repeated caption lines."""
    cleaned: list[str] = []
    seen_recent: list[str] = []

    for line in raw_vtt.splitlines():
        line = line.strip()
        if (
            not line
            or line.startswith("WEBVTT")
            or line.startswith("Kind:")
            or line.startswith("Language:")
            or line.startswith("NOTE")
            or VTT_TIMESTAMP_RE.match(line)
            or line.isdigit()
        ):
            continue

        # Remove inline timestamp tags like <00:00:02.000>
        line = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", "", line).strip()
        if not line:
            continue

        # Keep output readable by avoiding immediate repeated lines.
        if line in seen_recent:
            continue

        cleaned.append(line)
        seen_recent.append(line)
        if len(seen_recent) > 6:
            seen_recent.pop(0)

    return "\n".join(cleaned).strip()


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
                disliked INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(articles)").fetchall()
        }
        if "created_at" not in cols:
            conn.execute("ALTER TABLE articles ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP")
        if "updated_at" not in cols:
            conn.execute("ALTER TABLE articles ADD COLUMN updated_at TEXT DEFAULT CURRENT_TIMESTAMP")


def fetch_video_metadata(url: str) -> dict[str, Any]:
    """Fetch video metadata (title, id...) via yt-dlp JSON."""
    result = run_cmd(["yt-dlp", "--dump-single-json", "--skip-download", url])
    if result.returncode != 0 or not result.stdout.strip():
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def fetch_subtitles(url: str, lang: str = WHISPER_LANGUAGE) -> str:
    """Return cleaned subtitles for the given YouTube URL if available."""
    with tempfile.TemporaryDirectory(dir=TMP_BASE) as td:
        out = Path(td) / "%(id)s"
        run_cmd(
            [
                "yt-dlp",
                "--skip-download",
                "--write-auto-sub",
                "--sub-lang",
                lang,
                "-o",
                str(out),
                url,
            ]
        )
        vtt_files = list(Path(td).glob("*.vtt"))
        if vtt_files:
            return clean_vtt(vtt_files[0].read_text("utf-8", errors="ignore"))
    return ""


def whisper_transcribe(
    audio_path: Path,
    model: str = WHISPER_MODEL,
    language: str = WHISPER_LANGUAGE,
) -> str:
    """Transcribe audio using the local Whisper CLI."""
    out_dir = audio_path.parent
    run_cmd(
        [
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
    )
    txt_file = audio_path.with_suffix(".txt")
    if txt_file.exists():
        return txt_file.read_text("utf-8", errors="ignore").strip()
    return ""


@app.route("/api/health")
def api_health() -> Any:
    """Simple server health endpoint."""
    return jsonify({"status": "ok", "db": str(DB_PATH.resolve())})


@app.route("/api/subtitles", methods=["POST"])
def api_subtitles() -> Any:
    """Return transcript + title for requested YouTube URL."""
    data = request.get_json(force=True) or {}
    url = data.get("url")
    if not url:
        return jsonify({"error": "missing url"}), 400

    metadata = fetch_video_metadata(url)
    title = metadata.get("title") or ""

    transcript = fetch_subtitles(url, WHISPER_LANGUAGE)
    source = "subtitles"

    if not transcript:
        with tempfile.TemporaryDirectory(dir=TMP_BASE) as td:
            audio = Path(td) / "audio"
            run_cmd(["yt-dlp", "-f", "worstaudio", "-o", str(audio), url])
            candidates = list(Path(td).glob("audio.*"))
            audio_file = candidates[0] if candidates else None
            if audio_file:
                transcript = whisper_transcribe(audio_file, WHISPER_MODEL, WHISPER_LANGUAGE)
                source = "whisper"

    return jsonify({"transcript": transcript, "title": title, "source": source})


@app.route("/api/click", methods=["POST"])
def api_click() -> Any:
    """Simulate a mouse click at the provided screen coordinates."""
    data = request.get_json(force=True) or {}
    x = data.get("x")
    y = data.get("y")
    if x is None or y is None:
        return jsonify({"error": "missing coordinates"}), 400
    try:
        x = int(round(float(x)))
        y = int(round(float(y)))
    except (ValueError, TypeError):
        return jsonify({"error": "invalid coordinates"}), 400
    pyautogui.moveTo(x, y)
    pyautogui.click()
    time.sleep(0.1)
    return jsonify({"status": "ok"})


@app.route("/api/type", methods=["POST"])
def api_type() -> Any:
    """Paste the given text via clipboard for faster input."""
    data = request.get_json(force=True) or {}
    text = data.get("text", "")
    if text:
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
    return jsonify({"status": "ok"})


@app.route("/api/arrange", methods=["POST"])
def api_arrange() -> Any:
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
def api_article() -> Any:
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
            INSERT INTO articles (url, title, score, article, transcript, liked, disliked, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(url) DO UPDATE SET
                title=excluded.title,
                score=excluded.score,
                article=excluded.article,
                transcript=excluded.transcript,
                liked=excluded.liked,
                disliked=excluded.disliked,
                updated_at=CURRENT_TIMESTAMP
            """,
            (url, title, score, article_text, transcript, liked, disliked),
        )
        row = conn.execute("SELECT id FROM articles WHERE url=?", (url,)).fetchone()
    return jsonify({"id": row[0]})


@app.route("/api/articles")
def api_articles() -> Any:
    """Return list of stored articles sorted by last update desc."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, url, title, score, liked, disliked, updated_at
            FROM articles
            ORDER BY datetime(updated_at) DESC, id DESC
            """
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
                "updatedAt": r["updated_at"],
            }
        )
    return jsonify({"articles": articles})


@app.route("/api/article/<int:aid>")
def api_get_article(aid: int) -> Any:
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
        "updatedAt": row["updated_at"],
    }
    return jsonify(article)


@app.route("/api/stats")
def api_stats() -> Any:
    """Return basic aggregate metrics for the dashboard."""
    with sqlite3.connect(DB_PATH) as conn:
        total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        liked = conn.execute("SELECT COUNT(*) FROM articles WHERE liked=1").fetchone()[0]
        disliked = conn.execute("SELECT COUNT(*) FROM articles WHERE disliked=1").fetchone()[0]
    return jsonify({"total": total, "liked": liked, "disliked": disliked})


if __name__ == "__main__":
    init_db()
    app.run(port=5001)
