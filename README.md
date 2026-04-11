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

---

## Progress Table (Current status)

| Area                                                                       | Status | What is implemented | What is not implemented / partial | Progress | Notes |
| -------------------------------------------------------------------------- | ------ | ------------------- | --------------------------------- | -------- | ----- |
| Source creation and persistent source policy model                         |        |                     |                                   |          |       |
| Source editing, pause/resume/archive, and run-now controls                 |        |                     |                                   |          |       |
| Source URL normalization and canonical channel resolution                  |        |                     |                                   |          |       |
| Per-source metadata, identity, and destination shelf/collection assignment |        |                     |                                   |          |       |
| Discovery mode: latest N videos                                            |        |                     |                                   |          |       |
| Discovery mode: all videos since last successful scan                      |        |                     |                                   |          |       |
| Discovery mode: rolling time window                                        |        |                     |                                   |          |       |
| Discovery filters: minimum duration                                        |        |                     |                                   |          |       |
| Discovery filters: skip shorts                                             |        |                     |                                   |          |       |
| Discovery filters: skip livestreams if identifiable                        |        |                     |                                   |          |       |
| Manual reprocess of selected discovered items                              |        |                     |                                   |          |       |
| Refresh scheduler: global enable/disable                                   |        |                     |                                   |          |       |
| Refresh scheduler: global default cadence                                  |        |                     |                                   |          |       |
| Refresh scheduler: per-source cadence override                             |        |                     |                                   |          |       |
| Refresh scheduler: hourly refresh support                                  |        |                     |                                   |          |       |
| Refresh scheduler: next scheduled run visibility                           |        |                     |                                   |          |       |
| Refresh scheduler: last successful run visibility                          |        |                     |                                   |          |       |
| Refresh scheduler: missed-run handling                                     |        |                     |                                   |          |       |
| Refresh scheduler: backoff after repeated failure                          |        |                     |                                   |          |       |
| Refresh run persistence and audit logs                                     |        |                     |                                   |          |       |
| Refresh pipeline: fetch source metadata                                    |        |                     |                                   |          |       |
| Refresh pipeline: discover eligible videos by policy                       |        |                     |                                   |          |       |
| Refresh pipeline: compare against known videos                             |        |                     |                                   |          |       |
| Refresh pipeline: create new items only when appropriate                   |        |                     |                                   |          |       |
| Refresh pipeline: enqueue processing for new eligible items                |        |                     |                                   |          |       |
| Refresh pipeline: duplicate-safe behavior / idempotency                    |        |                     |                                   |          |       |
| Durable item lifecycle state model                                         |        |                     |                                   |          |       |
| Per-item status visibility in API                                          |        |                     |                                   |          |       |
| Per-item status visibility in UI                                           |        |                     |                                   |          |       |
| Transcript strategy: manual transcript only                                |        |                     |                                   |          |       |
| Transcript strategy: prefer manual then auto transcript                    |        |                     |                                   |          |       |
| Transcript strategy: allow auto transcript                                 |        |                     |                                   |          |       |
| Transcript strategy: force local transcription                             |        |                     |                                   |          |       |
| Transcript strategy: transcript first then audio fallback                  |        |                     |                                   |          |       |
| Transcript strategy: disable fallback                                      |        |                     |                                   |          |       |
| Preferred transcript languages support                                     |        |                     |                                   |          |       |
| Transcript retrieval from available upstream sources                       |        |                     |                                   |          |       |
| Audio download fallback path                                               |        |                     |                                   |          |       |
| Faster-Whisper CPU transcription fallback                                  |        |                     |                                   |          |       |
| Transcript persistence and transcript metadata recording                   |        |                     |                                   |          |       |
| Audio cleanup after successful processing (default true)                   |        |                     |                                   |          |       |
| Optional retention of failed-job audio only                                |        |                     |                                   |          |       |
| Generation provider abstraction                                            |        |                     |                                   |          |       |
| OpenAI generation provider support                                         |        |                     |                                   |          |       |
| LM Studio OpenAI-compatible provider support                               |        |                     |                                   |          |       |
| Persistent generation settings                                             |        |                     |                                   |          |       |
| Global default prompt template                                             |        |                     |                                   |          |       |
| Optional per-source prompt override                                        |        |                     |                                   |          |       |
| Prompt preview / resolved prompt inspection                                |        |                     |                                   |          |       |
| Test prompt against sample transcript                                      |        |                     |                                   |          |       |
| Stored prompt snapshot on each article version                             |        |                     |                                   |          |       |
| Article modes: concise article                                             |        |                     |                                   |          |       |
| Article modes: detailed article                                            |        |                     |                                   |          |       |
| Article modes: study notes                                                 |        |                     |                                   |          |       |
| Article modes: executive brief                                             |        |                     |                                   |          |       |
| Article modes: tutorial reconstruction                                     |        |                     |                                   |          |       |
| Article generation with filler removal and substance preservation          |        |                     |                                   |          |       |
| Article versioning on regeneration                                         |        |                     |                                   |          |       |
| Library: bookshelf/grid/list views                                         |        |                     |                                   |          |       |
| Library: grouping by source                                                |        |                     |                                   |          |       |
| Library: unread filters                                                    |        |                     |                                   |          |       |
| Library: search by title/body/source                                       |        |                     |                                   |          |       |
| Library: sorting by import time/publish time/source/title                  |        |                     |                                   |          |       |
| Library: YouTube thumbnails and preview snippets                           |        |                     |                                   |          |       |
| Library: transcript source badges                                          |        |                     |                                   |          |       |
| Reader: polished ebook-like reading experience                             |        |                     |                                   |          |       |
| Reader: light/dark/sepia themes                                            |        |                     |                                   |          |       |
| Reader: serif/sans font modes                                              |        |                     |                                   |          |       |
| Reader: adjustable font size                                               |        |                     |                                   |          |       |
| Reader: adjustable line width                                              |        |                     |                                   |          |       |
| Reader: estimated reading time                                             |        |                     |                                   |          |       |
| Reader: heading navigation                                                 |        |                     |                                   |          |       |
| Reader: source metadata display                                            |        |                     |                                   |          |       |
| Reader: transcript access panel/tab                                        |        |                     |                                   |          |       |
| Reader: article version switcher                                           |        |                     |                                   |          |       |
| Reader: mark read/unread                                                   |        |                     |                                   |          |       |
| Reader: export and copy actions                                            |        |                     |                                   |          |       |
| Collections: create/edit/delete                                            |        |                     |                                   |          |       |
| Collections: add/remove articles                                           |        |                     |                                   |          |       |
| Collections: collection detail and filtering                               |        |                     |                                   |          |       |
| Home page functionality                                                    |        |                     |                                   |          |       |
| Sources page functionality                                                 |        |                     |                                   |          |       |
| Source Detail page functionality                                           |        |                     |                                   |          |       |
| Jobs page functionality                                                    |        |                     |                                   |          |       |
| Library page functionality                                                 |        |                     |                                   |          |       |
| Collections page functionality                                             |        |                     |                                   |          |       |
| Article Reader page functionality                                          |        |                     |                                   |          |       |
| Settings page functionality                                                |        |                     |                                   |          |       |
| Diagnostics page functionality                                             |        |                     |                                   |          |       |
| Logs page functionality                                                    |        |                     |                                   |          |       |
| Settings: General                                                          |        |                     |                                   |          |       |
| Settings: Sources defaults                                                 |        |                     |                                   |          |       |
| Settings: Transcript/Transcription                                         |        |                     |                                   |          |       |
| Settings: Generation                                                       |        |                     |                                   |          |       |
| Settings: Reader                                                           |        |                     |                                   |          |       |
| Settings: Scheduling                                                       |        |                     |                                   |          |       |
| Settings: Storage                                                          |        |                     |                                   |          |       |
| Settings: Advanced                                                         |        |                     |                                   |          |       |
| Durable backend persistence and real database                              |        |                     |                                   |          |       |
| Alembic migrations                                                         |        |                     |                                   |          |       |
| Background workers for long-running tasks                                  |        |                     |                                   |          |       |
| Queue-backed processing isolation                                          |        |                     |                                   |          |       |
| Jobs list/detail/retry/cancel API support                                  |        |                     |                                   |          |       |
| Failure isolation per video/item                                           |        |                     |                                   |          |       |
| Replayability / retry failed items                                         |        |                     |                                   |          |       |
| Structured logging                                                         |        |                     |                                   |          |       |
| Secret redaction in logs and frontend payloads                             |        |                     |                                   |          |       |
| Diagnostics: DB connectivity                                               |        |                     |                                   |          |       |
| Diagnostics: queue/scheduler health                                        |        |                     |                                   |          |       |
| Diagnostics: storage writability                                           |        |                     |                                   |          |       |
| Diagnostics: FFmpeg availability                                           |        |                     |                                   |          |       |
| Diagnostics: yt-dlp availability/version                                   |        |                     |                                   |          |       |
| Diagnostics: transcript dependency health                                  |        |                     |                                   |          |       |
| Diagnostics: Faster-Whisper availability                                   |        |                     |                                   |          |       |
| Diagnostics: OpenAI connectivity                                           |        |                     |                                   |          |       |
| Diagnostics: LM Studio connectivity                                        |        |                     |                                   |          |       |
| Logs viewer: filtering/searching/severity/linked context                   |        |                     |                                   |          |       |
| REST API: settings CRUD                                                    |        |                     |                                   |          |       |
| REST API: source CRUD and source actions                                   |        |                     |                                   |          |       |
| REST API: source refresh trigger                                           |        |                     |                                   |          |       |
| REST API: item detail                                                      |        |                     |                                   |          |       |
| REST API: transcript detail/retry                                          |        |                     |                                   |          |       |
| REST API: article list/detail/regenerate/export                            |        |                     |                                   |          |       |
| REST API: collections CRUD                                                 |        |                     |                                   |          |       |
| REST API: diagnostics                                                      |        |                     |                                   |          |       |
| REST API: logs                                                             |        |                     |                                   |          |       |
| REST API: health endpoints                                                 |        |                     |                                   |          |       |
| Unit tests required by spec                                                |        |                     |                                   |          |       |
| Integration tests required by spec                                         |        |                     |                                   |          |       |
| End-to-end Playwright tests required by spec                               |        |                     |                                   |          |       |
| Failure-path automated tests required by spec                              |        |                     |                                   |          |       |
| Docker Compose local stack                                                 |        |                     |                                   |          |       |
| Backend Dockerfile                                                         |        |                     |                                   |          |       |
| Frontend Dockerfile                                                        |        |                     |                                   |          |       |
| .env.example                                                               |        |                     |                                   |          |       |
| Migration commands and startup/run path                                    |        |                     |                                   |          |       |
| Seed or smoke-test fixtures                                                |        |                     |                                   |          |       |
| Full-stack local startup success                                           |        |                     |                                   |          |       |
| Clean migration application                                                |        |                     |                                   |          |       |
| No-placeholder core flow compliance                                        |        |                     |                                   |          |       |


---

## Function Inventory (Categorized)

### 1) Backend — Service Layer

#### Discovery / Source policy (`backend/app/services/youtube.py`)
- `normalize_source_url(url)`
- `evaluate_video_policy(video, source)`
- `_feed_url_from_source_url(source_url)`
- `_parse_atom_entries(feed_xml)`
- `discover_videos(source)`

#### Transcript / Transcription (`backend/app/services/transcript.py`)
- `select_transcript_strategy(source)`
- `should_fallback_to_transcription(strategy, transcript_found, fallback_enabled)`
- `_extract_video_id(video_url)`
- `fetch_transcript(video_url, languages)`
- `transcribe_audio_locally(video_url, yt_dlp_command='yt-dlp')`

#### Article generation (`backend/app/services/generation.py`)
- `render_prompt(template, transcript, mode)`
- `_chat_completion(base_url, api_key, model, prompt, temperature)`
- `generate_article(transcript, prompt, cfg)`

#### Pipeline orchestration (`backend/app/services/pipeline.py`)
- `refresh_source(db, source_id)`
- `process_video_item(db, item_id)`

### 2) Backend — API and runtime

#### API routes (`backend/app/api/routes.py`)
- `health()`
- `get_settings(...)`
- `put_settings(...)`
- `list_sources(...)`
- `create_source(...)`
- `refresh(...)`
- `patch_source(...)`
- `list_jobs(...)`
- `retry_job(...)`
- `library(...)`
- `article_detail(...)`
- `regenerate(...)`
- `collections(...)`
- `create_collection(...)`
- `diagnostics()`
- `logs(...)`

#### Scheduler (`backend/app/workers/scheduler.py`)
- `tick_sources()`
- `start_scheduler()`

#### DB/session and app lifecycle
- `get_db()` (`backend/app/db/session.py`)
- `startup()` (`backend/app/main.py`)

### 3) Frontend (React SPA)

#### Layout/shared UI (`frontend/src/main.tsx`)
- `Page(...)`
- `StatCard(...)`
- `Layout()`

#### Page-level feature modules (`frontend/src/main.tsx`)
- `Home()`
- `Sources()`
- `Jobs()`
- `Library()`
- `Reader()`
- `Settings()`
- `Diagnostics()`
- `Logs()`
- `Collections()`

---

## Deep Analysis: What Is Done vs Not Done (with Notes)

### A) Core architecture status
- **Done:** A real full-stack baseline exists with persistent database entities, route coverage for main UX pages, and a working ingest → transcript → generation pipeline.
- **Not done:** Production-grade robustness (strict schemas, state-machine-grade retry semantics, richer observability, stronger auth/security defaults) is not fully implemented.
- **Note:** This repo is best described as **feature-complete for a serious prototype**, not fully hardened for production.

### B) Ingestion and source handling
- **Done:** Real Atom feed ingestion is integrated, policy filters are applied, duplicates are prevented by source/video identity constraints.
- **Not done:** URL normalization and channel identity resolution are still partial relative to the roadmap. Feed metadata limitations keep policy richness constrained (e.g., shorts/live inference quality).
- **Note:** Works for many channels, but coverage consistency depends on feed format details.

### C) Transcript strategy and fallback
- **Done:** Subtitle retrieval + local transcription fallback path is operational.
- **Not done:** Runtime path currently uses simplified strategy/fallback choices in processing flow; nuanced strategy matrix from plan is only partially represented.
- **Note:** High practical utility already, but behavior under edge-failure scenarios could be made more explainable.

### D) Article generation
- **Done:** Provider switching exists between OpenAI and LM Studio-compatible endpoints via a centralized generation helper.
- **Not done:** Prompt lifecycle controls (preset catalogs, source-level override governance, strict snapshots/metadata conventions, refusal/error taxonomy) are still thin.
- **Note:** Integration is usable now, but prompt and quality governance need a second iteration.

### E) Frontend and operator UX
- **Done:** All core operator pages are present and wired to backend routes.
- **Not done:** Advanced UX promised in roadmap (deeper library filtering, richer reader personalization, stronger diagnostics/log drill-down, comprehensive policy editor) is incomplete.
- **Note:** Current UI favors direct operational control over polished end-user reading experience.

### F) Scheduler, jobs, and reliability controls
- **Done:** Scheduled ticking and basic job records exist; failures are captured.
- **Not done:** Robust retry/backoff semantics, run accounting, and deterministic lock/lease protections are limited.
- **Note:** Acceptable for single-instance/local usage; scaling reliability needs more engineering.

### G) Testing and quality gate
- **Done:** Basic unit and integration tests are present and aligned with current behavior.
- **Not done:** Broad regression suite for edge cases and frontend behavior remains below roadmap target.
- **Note:** Good start, but not enough to claim high confidence under rapid refactoring.

### H) Security and deployment maturity
- **Done:** Config settings and diagnostics endpoints exist.
- **Not done:** Hard security boundaries and deployment-grade defaults are not complete.
- **Note:** Treat current system as a **local/self-hosted trusted environment** unless hardened further.

---

## Practical Conclusion

Overall, the project has moved beyond idea-stage: it already delivers a meaningful and usable end-to-end pipeline. The biggest remaining work is **hardening and reliability**, not initial feature creation. If development resumes, prioritize:
1. strict API contracts,
2. retry/backoff and refresh-run accounting,
3. richer transcript strategy execution,
4. frontend usability upgrades,
5. security/config hardening.

That sequence gives the highest impact-to-effort ratio for reaching a stable v1.0.
