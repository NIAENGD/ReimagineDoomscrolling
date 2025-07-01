import json
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
import subprocess
import tempfile

app = Flask(__name__)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

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


@app.route("/articles/<int:aid>")
def get_article(aid: int):
    p = DATA_DIR / f"article-{aid}.json"
    if not p.exists():
        return jsonify({"error": "not found"}), 404
    return send_from_directory(p.parent, p.name)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
