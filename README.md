# ReimagineDoomscrolling v2

A self-hosted, full-stack YouTube-to-reading pipeline with persistent sources, scheduled refreshes, transcript/transcription fallback, article generation, and library/reader UX.

## Stack
- Backend: FastAPI + SQLAlchemy + APScheduler + Celery-compatible architecture
- Frontend: React + TypeScript + Vite + React Query
- Storage: SQL database (SQLite default, PostgreSQL via `DATABASE_URL`)
- Queue/Scheduler: job tables + scheduler tick loop (Redis/Celery dependencies included)

## One-click Windows startup
Use `run_app.bat` and choose:
1) bootstrap dependencies,
4) run backend + frontend,
6) open the detailed development plan manager.

No manual command entry is required after launching the batch menu.

For planning workflow on Windows, you can also run `manage_dev_plan.bat` directly.

## API Pages
- Home
- Sources
- Jobs
- Library
- Collections
- Reader
- Settings
- Diagnostics
- Logs

## Testing
Use `run_app.bat` option 5, or run:
- `pytest backend/tests -q`
- `npm test` in `frontend/`

## Implemented integrations
- `discover_videos`: YouTube channel discovery through the public Atom feed.
- `fetch_transcript`: subtitle retrieval via `youtube-transcript-api`.
- `transcribe_audio_locally`: local fallback with `yt-dlp` + `faster-whisper`.
- `generate_article`: OpenAI-compatible chat completion support for OpenAI and LM Studio.

