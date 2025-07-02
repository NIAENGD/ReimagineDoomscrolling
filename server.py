import json
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, render_template
import subprocess
import tempfile

app = Flask(__name__)

DATA_DIR = Path("data")
ARTICLES_DIR = DATA_DIR / "articles"
INDEX_FILE = DATA_DIR / "index.json"
ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
if not INDEX_FILE.exists():
    INDEX_FILE.write_text("[]", encoding="utf-8")

# --- helpers --------------------------------------------------------------

def whisper_transcribe(audio_path: Path) -> str:
    """Transcribe audio using local whisper command."""
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


def score_transcript(transcript: str) -> dict:
    """Placeholder scoring using ChatGPT or similar."""
    # This is a stub implementation. Integrate with an LLM as needed.
    return {
        "逻辑": "清晰",
        "深度": "阐述",
        "见解": "深层",
        "表达": "自然",
        "启发性": "有启发",
        "综合质量分": 50,
    }


def rewrite_article(transcript: str) -> str:
    """Placeholder rewriting using ChatGPT or similar."""
    return transcript


def process_url(url: str) -> dict:
    """Fetch transcript, score it and save result."""
    transcript = fetch_subtitles(url)
    if not transcript:
        with tempfile.TemporaryDirectory() as td:
            audio_path = Path(td) / "audio"
            subprocess.run([
                "yt-dlp",
                "-f",
                "bestaudio",
                "-o",
                str(audio_path),
                url,
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            audio_file = audio_path.with_suffix(".webm")
            if audio_file.exists():
                transcript = whisper_transcribe(audio_file)
    score = score_transcript(transcript)
    article = rewrite_article(transcript)
    idx = load_index()
    vid = len(idx) + 1
    idx.append({"id": vid, "url": url, "title": "", "score": score})
    save_index(idx)
    (ARTICLES_DIR / f"{vid}.json").write_text(
        json.dumps({"article": article, "transcript": transcript}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"id": vid, "score": score, "article": article}


def fetch_subtitles(url: str) -> str:
    """Try to download subtitles with yt-dlp and return text."""
    with tempfile.TemporaryDirectory() as td:
        outtmpl = Path(td) / "%(id)s"
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-auto-sub",
            "--sub-lang",
            "en",
            "-o",
            str(outtmpl),
            url,
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        vtt_files = list(Path(td).glob("*.vtt"))
        if vtt_files:
            return vtt_files[0].read_text("utf-8")
    return ""


def load_index():
    return json.loads(INDEX_FILE.read_text("utf-8"))


def save_index(data):
    INDEX_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# --- API endpoints -------------------------------------------------------

@app.route("/api/transcribe", methods=["POST"])
def api_transcribe():
    if "file" not in request.files:
        return jsonify({"error": "no file"}), 400
    f = request.files["file"]
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        f.save(tmp.name)
        txt = whisper_transcribe(Path(tmp.name))
    return jsonify({"transcript": txt})


@app.route("/api/process", methods=["POST"])
def api_process():
    data = request.get_json(force=True)
    transcript = data.get("transcript")
    if not transcript:
        return jsonify({"error": "missing transcript"}), 400
    score = score_transcript(transcript)
    article = rewrite_article(transcript)
    fid = len(list(DATA_DIR.glob("article-*.json"))) + 1
    outfile = DATA_DIR / f"article-{fid}.json"
    outfile.write_text(json.dumps({"score": score, "article": article}, ensure_ascii=False, indent=2))
    return jsonify({"id": fid, "score": score, "article": article})


@app.route("/api/fetch", methods=["POST"])
def api_fetch():
    data = request.get_json(force=True)
    url = data.get("url")
    if not url:
        return jsonify({"error": "missing url"}), 400
    result = process_url(url)
    return jsonify(result)


@app.route("/")
def index():
    idx = load_index()
    return render_template("index.html", videos=idx)


@app.route("/article/<int:aid>")
def article_page(aid: int):
    idx = load_index()
    v = next((i for i in idx if i["id"] == aid), None)
    if not v:
        return "Not found", 404
    p = ARTICLES_DIR / f"{aid}.json"
    data = json.loads(p.read_text("utf-8"))
    return render_template("article.html", title=v.get("title", v.get("url")), article=data["article"])




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
