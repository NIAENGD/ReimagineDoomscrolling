import json
import os
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, render_template
import subprocess
import tempfile
import openai

app = Flask(__name__)

DATA_DIR = Path("data")
ARTICLES_DIR = DATA_DIR / "articles"
INDEX_FILE = DATA_DIR / "index.json"
ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
if not INDEX_FILE.exists():
    INDEX_FILE.write_text("[]", encoding="utf-8")

# Default prompts ---------------------------------------------------------
SCORING_PROMPT = """You are an impartial video-analysis engine.

INPUT
———
{{transcript}}

TASK
———
1. **Pre-processing**
   • Remove or ignore all segments that are clearly promotional, sponsored, or ad-read in nature.
   • Evaluate only the substantive, non-advertisement content.

2. **Scoring (0-100, decimals allowed)**
   Apply the *strict* rubric below to each dimension.
   • A typical, average-quality video transcript scores < 30.
   • Only truly exceptional work reaches > 60.
   • Nobody scores 100.
   • Score each dimension independently; do not calculate or output any totals.

   | Dimension (JSON key) | 0 – 19 (Poor) | 20 – 39 (Weak) | 40 – 59 (Fair) | 60 – 79 (Strong) | 80 – 100 (Exceptional) |
   |----------------------|---------------|----------------|----------------|------------------|------------------------|
   | **logic**            | Incoherent, contradictory, or overtly misleading | Frequent gaps or fallacies | Generally coherent but with some leaps or ambiguities | Clear, sequential, few minor issues | Crystal-clear, airtight, zero misleading cues |
   | **depth**            | Surface-level, anecdotal | Minimal background/context | Moderately deep; some causal links | Thorough causal & systemic analysis | Multi-layer, root-cause & systemic depth |
   | **insight**          | Trivial or common knowledge | Few minor takeaways | Some new angles, limited originality | Several fresh, actionable insights | Breakthrough, paradigm-shifting insights |
   | **expression**       | Robotic or disjointed | Stiff, monotonous | Mostly natural; occasional dull moments | Engaging, vivid narration | Highly vivid, memorable storytelling |
   | **inspiration**      | None; flat | Slightly motivating | Moderately inspiring | Strongly motivating | Profoundly energising & empowering |
   | **overallQuality**   | Holistically synthesize the above (but do not average them mechanically); apply the same 0-100 scale |

3. **Blind-Spots & Challenges**
   Craft one concise sentence (≤ 35 words) flagging any major bias, commercial tilt, feasibility gaps, risk omissions, or likely misinterpretations the audience might overlook. Be specific, rational, and avoid clichés.

OUTPUT
———
Return only the following JSON (no commentary):

{"logic":<float>,"depth":<float>,"insight":<float>,"expression":<float>,"inspiration":<float>,"overallQuality":<float>,"blindSpots":""}
"""

REWRITE_PROMPT = (
    "以原作者视角，忠实呈现视频中的观点、思路、结构和情绪，不加任何旁人评价或个人观点。"\
    "标题/小标题分明，段落清晰；语言优美自然，贴合原风格。"\
    "原汁原味还原引用、比喻、故事、幽默等表现手法；保持视频作者的个性（如讽刺、深情等）。"\
    "开头简要介绍视频内容，结尾收束主要结论或号召；绝不提及‘视频’，直接以文章形式呈现。"\
    "切记！这并不是一个TLDR，或是总结，而是完整的文稿。"\
    "切记！这不是一个总结，你需要输出尽量还原原视频的长度。"
)

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
    """Score a transcript using the SCORING_PROMPT via OpenAI ChatCompletion."""
    prompt = SCORING_PROMPT.replace("{{transcript}}", transcript)
    try:
        resp = openai.ChatCompletion.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        txt = resp.choices[0].message.content.strip()
        return json.loads(txt)
    except Exception:
        return {}


def rewrite_article(transcript: str) -> str:
    """Rewrite transcript as an article in Chinese using REWRITE_PROMPT."""
    prompt = REWRITE_PROMPT + "\n\n" + transcript
    try:
        resp = openai.ChatCompletion.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
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
    return render_template(
        "article.html",
        title=v.get("title", v.get("url")),
        score=v.get("score", {}),
        article=data["article"],
    )




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
