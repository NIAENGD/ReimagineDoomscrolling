# ReimagineDoomscrolling

ReimagineDoomscrolling is a local-first Chrome extension + Python helper server that turns your YouTube home feed into a **quality-filtered reading workflow**:

1. Collect videos from your feed.
2. Pull subtitles (or run Whisper fallback when subtitles are missing).
3. Send transcripts to ChatGPT for strict scoring + long-form rewriting.
4. Store and browse results in a filterable dashboard.

See [docs/overview.md](docs/overview.md) for the higher-level design.

## What is now functional

- Local helper API with health check, transcript fetching, Whisper fallback, article persistence, and simple metrics.
- Cleaner subtitle extraction from VTT tracks.
- Extension control panel with server/login status, progress log, and prompt editing.
- Automated side-by-side YouTube + ChatGPT popup windows.
- Results dashboard with search, status filtering, score/date sorting, and compact stats cards.
- Article detail page with score table and like/dislike watch actions.

## Quick start

Install dependencies and run the helper server. It expects these CLIs on your `PATH`:

- `yt-dlp`
- `whisper` (from `openai-whisper`)
- `ffmpeg`

```bash
pip install -r requirements.txt
pip install yt-dlp openai-whisper
python server.py
```

The server runs at `http://localhost:5001`.

Then load the Chrome extension:

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** and select `extension/`
4. Open the extension popup and click **Open tabs**, then **Start run**

## API summary

- `GET /api/health` – server status
- `POST /api/subtitles` – transcript/title for a YouTube URL
- `POST /api/article` – upsert generated result
- `GET /api/articles` – list results
- `GET /api/article/<id>` – full item
- `GET /api/stats` – aggregate counts

## Packaging

Use:

```bash
python package.py
```

It writes a zip to `dist/`.

## Notes

- This is still an experimental automation-heavy project.
- ChatGPT UI automation can break when the web UI changes.
- If you have an existing `articles.db`, it will continue to work; new timestamp columns are added only for fresh databases.
