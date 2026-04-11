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

### Backend and data model

| Task                                        | Progress | Notes |
| ------------------------------------------- | -------- | ----- |
| Persistent settings entity and storage      |          |       |
| Durable sources entity with policy fields   |          |       |
| Canonical channel identity persistence      |          |       |
| Source refresh runs entity                  |          |       |
| Video/item entity with dedup-safe identity  |          |       |
| Transcript entity and metadata storage      |          |       |
| Articles entity                             |          |       |
| Article versions entity                     |          |       |
| Collections entity                          |          |       |
| Jobs entity                                 |          |       |
| Job items entity                            |          |       |
| Logs/events entity                          |          |       |
| Reading progress entity                     |          |       |
| Practical schema only, no speculative bloat |          |       |
| Alembic migrations created                  |          |       |
| Migrations apply cleanly                    |          |       |

### Source model and source policy

| Task                                           | Progress | Notes |
| ---------------------------------------------- | -------- | ----- |
| Add YouTube channel as source                  |          |       |
| Edit source                                    |          |       |
| Pause source                                   |          |       |
| Resume source                                  |          |       |
| Archive source                                 |          |       |
| Persist source URL                             |          |       |
| Resolve and persist canonical channel identity |          |       |
| Persist source title and metadata              |          |       |
| Persist enabled/paused/archived state          |          |       |
| Persist refresh cadence                        |          |       |
| Persist discovery mode                         |          |       |
| Persist max videos policy                      |          |       |
| Persist rolling time-window policy             |          |       |
| Persist minimum duration filter                |          |       |
| Persist skip shorts policy                     |          |       |
| Persist skip livestreams policy                |          |       |
| Persist transcript strategy                    |          |       |
| Persist transcription fallback strategy        |          |       |
| Persist prompt/article generation preset       |          |       |
| Persist destination collection or shelf        |          |       |
| Persist deduplication policy                   |          |       |
| Persist retry policy                           |          |       |
| Support manual reprocess for selected items    |          |       |

### Discovery and refresh pipeline

| Task                                           | Progress | Notes |
| ---------------------------------------------- | -------- | ----- |
| Normalize and resolve source before refresh    |          |       |
| Fetch source metadata during refresh           |          |       |
| Discover latest N videos                       |          |       |
| Discover all videos since last successful scan |          |       |
| Discover videos within rolling window          |          |       |
| Apply minimum duration filter                  |          |       |
| Apply skip shorts filter                       |          |       |
| Apply skip livestreams filter                  |          |       |
| Compare discovered items against known items   |          |       |
| Create new items only when eligible            |          |       |
| Safely suppress duplicates                     |          |       |
| Enqueue new eligible items for processing      |          |       |
| Record refresh logs and status                 |          |       |
| Force refresh / run-now action                 |          |       |

### Scheduling and retry behavior

| Task                               | Progress | Notes |
| ---------------------------------- | -------- | ----- |
| Global refresh enabled/disabled    |          |       |
| Global default cadence             |          |       |
| Per-source cadence override        |          |       |
| Hourly refresh support             |          |       |
| Next scheduled run tracking        |          |       |
| Last successful run tracking       |          |       |
| Missed-run handling                |          |       |
| Backoff after repeated failure     |          |       |
| Concurrency cap                    |          |       |
| Retry intervals/backoff settings   |          |       |
| Scheduler runs automatically       |          |       |
| Scheduler status visible in UI/API |          |       |

### Item lifecycle and processing states

| Task                                  | Progress | Notes |
| ------------------------------------- | -------- | ----- |
| Persist discovered state              |          |       |
| Persist filtered_out state            |          |       |
| Persist queued state                  |          |       |
| Persist metadata_fetched state        |          |       |
| Persist transcript_searching state    |          |       |
| Persist transcript_found state        |          |       |
| Persist transcript_unavailable state  |          |       |
| Persist audio_downloaded state        |          |       |
| Persist transcription_started state   |          |       |
| Persist transcription_completed state |          |       |
| Persist generation_started state      |          |       |
| Persist generation_completed state    |          |       |
| Persist published state               |          |       |
| Persist failed state                  |          |       |
| Persist retry_pending state           |          |       |
| Persist skipped_duplicate state       |          |       |
| Persist skipped_by_policy state       |          |       |
| All transitions visible in API        |          |       |
| All transitions visible in UI         |          |       |

### Transcript retrieval and fallback transcription

| Task                                                 | Progress | Notes |
| ---------------------------------------------------- | -------- | ----- |
| Manual transcript only strategy                      |          |       |
| Prefer manual then auto transcript strategy          |          |       |
| Allow auto transcript strategy                       |          |       |
| Force local transcription strategy                   |          |       |
| Transcript-first then audio fallback strategy        |          |       |
| Disable fallback strategy                            |          |       |
| Preferred transcript languages                       |          |       |
| Retrieve transcript when available                   |          |       |
| Download audio when fallback is needed               |          |       |
| Normalize extracted audio as needed                  |          |       |
| Run Faster-Whisper on CPU                            |          |       |
| Persist transcript text                              |          |       |
| Persist transcription metadata                       |          |       |
| Delete downloaded audio after success by default     |          |       |
| Retain failed-job audio only when explicitly enabled |          |       |
| Retry transcript/transcription failures              |          |       |

### Article generation and provider abstraction

| Task                                                        | Progress | Notes |
| ----------------------------------------------------------- | -------- | ----- |
| Provider abstraction implemented                            |          |       |
| OpenAI provider support                                     |          |       |
| LM Studio OpenAI-compatible provider support                |          |       |
| Persistent provider selection                               |          |       |
| Persistent model name                                       |          |       |
| Persistent API key or base URL                              |          |       |
| Persistent timeout                                          |          |       |
| Persistent temperature                                      |          |       |
| Persistent max tokens                                       |          |       |
| Persistent article mode                                     |          |       |
| Persistent global prompt template                           |          |       |
| Optional per-source prompt override                         |          |       |
| Prompt preview / resolved prompt inspection                 |          |       |
| Test prompt against sample transcript                       |          |       |
| Store prompt snapshot on every generated article version    |          |       |
| Concise article mode                                        |          |       |
| Detailed article mode                                       |          |       |
| Study notes mode                                            |          |       |
| Executive brief mode                                        |          |       |
| Tutorial reconstruction mode                                |          |       |
| Regenerate article creates new version, not overwrite       |          |       |
| Generation avoids unsupported invention as much as feasible |          |       |

### Library, reader, and reading experience

| Task                                   | Progress | Notes |
| -------------------------------------- | -------- | ----- |
| Articles appear in library             |          |       |
| Bookshelf/grid/list views              |          |       |
| Grouping by source                     |          |       |
| Unread filters                         |          |       |
| Search by title                        |          |       |
| Search by body                         |          |       |
| Search by source                       |          |       |
| Sort by import time                    |          |       |
| Sort by publish time                   |          |       |
| Sort by source                         |          |       |
| Sort by title                          |          |       |
| YouTube thumbnails displayed           |          |       |
| Preview snippets                       |          |       |
| Transcript source badges               |          |       |
| Polished reader page                   |          |       |
| Clean typography                       |          |       |
| Light theme                            |          |       |
| Dark theme                             |          |       |
| Sepia theme                            |          |       |
| Serif font mode                        |          |       |
| Sans font mode                         |          |       |
| Adjustable font size                   |          |       |
| Adjustable line width                  |          |       |
| Estimated reading time                 |          |       |
| Heading navigation                     |          |       |
| Source metadata in reader              |          |       |
| Transcript tab or panel                |          |       |
| Article version switcher               |          |       |
| Mark as read                           |          |       |
| Mark as unread                         |          |       |
| Export action                          |          |       |
| Copy action                            |          |       |
| Related source articles if implemented |          |       |
| Reading progress persistence           |          |       |

### Collections

| Task                           | Progress | Notes |
| ------------------------------ | -------- | ----- |
| Create collection              |          |       |
| Edit collection                |          |       |
| Delete collection              |          |       |
| Collection detail page         |          |       |
| Add article to collection      |          |       |
| Remove article from collection |          |       |
| Filter library by collection   |          |       |

### Pages and frontend coverage

| Task                                  | Progress | Notes |
| ------------------------------------- | -------- | ----- |
| Home page functional                  |          |       |
| Home shows continue reading           |          |       |
| Home shows latest articles            |          |       |
| Home shows unread count               |          |       |
| Home shows active sources             |          |       |
| Home shows recent jobs                |          |       |
| Home shows failed items               |          |       |
| Home shows scheduler status           |          |       |
| Sources page functional               |          |       |
| Source Detail page functional         |          |       |
| Jobs page functional                  |          |       |
| Library page functional               |          |       |
| Collections page functional           |          |       |
| Article Reader page functional        |          |       |
| Settings page functional              |          |       |
| Diagnostics page functional           |          |       |
| Logs page functional                  |          |       |
| No primary page is a dead placeholder |          |       |
| Multi-page frontend implemented       |          |       |

### Settings coverage

| Task                                                | Progress | Notes |
| --------------------------------------------------- | -------- | ----- |
| General: timezone                                   |          |       |
| General: UI theme default                           |          |       |
| Sources: default discovery mode                     |          |       |
| Sources: default video cap                          |          |       |
| Sources: rolling time window                        |          |       |
| Sources: skip shorts default                        |          |       |
| Sources: minimum duration default                   |          |       |
| Sources: duplicate handling                         |          |       |
| Transcript: preferred languages                     |          |       |
| Transcript: transcript-first toggle                 |          |       |
| Transcript: fallback enabled toggle                 |          |       |
| Transcript: Faster-Whisper model size               |          |       |
| Transcript: CPU threads                             |          |       |
| Transcript: optional language hint                  |          |       |
| Transcript: delete audio after success default true |          |       |
| Transcript: retain failed audio only optional       |          |       |
| Generation: local and cloud provider                |          |       |
| Generation: model                                   |          |       |
| Generation: API key or base URL                     |          |       |
| Generation: timeout                                 |          |       |
| Generation: temperature                             |          |       |
| Generation: max tokens                              |          |       |
| Generation: article mode default                    |          |       |
| Generation: global prompt template                  |          |       |
| Generation: per-source override allowed             |          |       |
| Reader: default theme                               |          |       |
| Reader: font family                                 |          |       |
| Reader: font size                                   |          |       |
| Reader: line width                                  |          |       |
| Scheduling: global refresh enabled                  |          |       |
| Scheduling: default cadence                         |          |       |
| Scheduling: concurrency cap                         |          |       |
| Scheduling: retry intervals/backoff                 |          |       |
| Storage: temp cleanup TTL                           |          |       |
| Storage: transcript retention policy                |          |       |
| Storage: thumbnail cache policy                     |          |       |
| Storage: log retention                              |          |       |
| Advanced: debug logging                             |          |       |
| Advanced: test provider connection                  |          |       |
| Advanced: test transcription pipeline               |          |       |
| Settings persistence works end to end               |          |       |

### API surface

| Task                           | Progress | Notes |
| ------------------------------ | -------- | ----- |
| Settings CRUD API              |          |       |
| Source CRUD API                |          |       |
| Source action APIs             |          |       |
| Source refresh trigger API     |          |       |
| Jobs list API                  |          |       |
| Jobs detail API                |          |       |
| Jobs retry API                 |          |       |
| Jobs cancel API                |          |       |
| Item detail API                |          |       |
| Transcript detail API          |          |       |
| Transcript retry API           |          |       |
| Article list API               |          |       |
| Article detail API             |          |       |
| Article regenerate API         |          |       |
| Article export API             |          |       |
| Collections CRUD API           |          |       |
| Diagnostics API                |          |       |
| Logs API                       |          |       |
| Health endpoints               |          |       |
| Typed request/response schemas |          |       |

### Diagnostics, logs, and operational visibility

| Task                                    | Progress | Notes |
| --------------------------------------- | -------- | ----- |
| DB connectivity diagnostic              |          |       |
| Queue/scheduler health diagnostic       |          |       |
| Storage writability diagnostic          |          |       |
| FFmpeg availability diagnostic          |          |       |
| yt-dlp availability/version diagnostic  |          |       |
| Transcript dependency health diagnostic |          |       |
| Faster-Whisper availability diagnostic  |          |       |
| OpenAI connectivity diagnostic          |          |       |
| LM Studio connectivity diagnostic       |          |       |
| Structured logging implemented          |          |       |
| Log filtering                           |          |       |
| Log searching                           |          |       |
| Log severity filtering                  |          |       |
| Linked log context                      |          |       |
| Secret redaction in logs                |          |       |

### Cleanup, reliability, and operational rules

| Task                                                           | Progress | Notes |
| -------------------------------------------------------------- | -------- | ----- |
| Strong idempotency on repeated refreshes                       |          |       |
| Repeated refreshes do not create uncontrolled duplicates       |          |       |
| Failure isolation per video/item                               |          |       |
| Failed items are retryable                                     |          |       |
| Replayability of failed items                                  |          |       |
| Article versioning instead of silent overwrite                 |          |       |
| Temporary audio deleted after successful processing by default |          |       |
| Optional failed-audio retention policy                         |          |       |
| Temp cleanup TTL enforcement                                   |          |       |
| Transcript retention policy enforcement                        |          |       |
| Thumbnail cache policy enforcement                             |          |       |
| Log retention enforcement                                      |          |       |
| API keys never exposed in frontend payloads                    |          |       |
| Long-running work moved off request thread                     |          |       |

### Testing

| Task                                                | Progress | Notes |
| --------------------------------------------------- | -------- | ----- |
| Unit: source URL normalization                      |          |       |
| Unit: source policy evaluation                      |          |       |
| Unit: deduplication                                 |          |       |
| Unit: transcript selection                          |          |       |
| Unit: fallback decision logic                       |          |       |
| Unit: prompt rendering                              |          |       |
| Unit: provider abstraction                          |          |       |
| Unit: cleanup policy                                |          |       |
| Unit: status transitions                            |          |       |
| Unit: schedule calculation                          |          |       |
| Unit: article preview extraction                    |          |       |
| Integration: create settings                        |          |       |
| Integration: update settings                        |          |       |
| Integration: add source                             |          |       |
| Integration: run refresh                            |          |       |
| Integration: discover videos                        |          |       |
| Integration: transcript success path                |          |       |
| Integration: transcript failure plus audio fallback |          |       |
| Integration: successful article generation          |          |       |
| Integration: article regeneration versioning        |          |       |
| Integration: duplicate suppression                  |          |       |
| Integration: audio cleanup after success            |          |       |
| Integration: retry failed item                      |          |       |
| Integration: diagnostics behavior                   |          |       |
| E2E: save settings                                  |          |       |
| E2E: add source                                     |          |       |
| E2E: force refresh                                  |          |       |
| E2E: observe job progress                           |          |       |
| E2E: open library                                   |          |       |
| E2E: read article                                   |          |       |
| E2E: switch reader settings                         |          |       |
| E2E: view transcript                                |          |       |
| E2E: view diagnostics                               |          |       |
| E2E: regenerate article version                     |          |       |
| Failure-path: invalid source URL                    |          |       |
| Failure-path: transcript unavailable                |          |       |
| Failure-path: yt-dlp failure                        |          |       |
| Failure-path: ffmpeg unavailable                    |          |       |
| Failure-path: transcription failure                 |          |       |
| Failure-path: OpenAI auth failure                   |          |       |
| Failure-path: LM Studio connection failure          |          |       |
| Failure-path: malformed model response              |          |       |
| Failure-path: duplicate refresh request             |          |       |
| Mocks/fakes for OpenAI                              |          |       |
| Mocks/fakes for LM Studio                           |          |       |
| Mocks/fakes for transcript package calls            |          |       |
| Mocks/fakes for yt-dlp                              |          |       |
| Mocks/fakes for Faster-Whisper                      |          |       |
| Mocks/fakes for YouTube metadata/discovery          |          |       |

### Deployment and local developer experience

| Task                                                         | Progress | Notes |
| ------------------------------------------------------------ | -------- | ----- |
| docker-compose provided                                      |          |       |
| Backend Dockerfile provided                                  |          |       |
| Frontend Dockerfile provided                                 |          |       |
| .env.example provided                                        |          |       |
| Migration commands documented                                |          |       |
| Seed or smoke-test fixtures provided                         |          |       |
| Startup script or Makefile provided                          |          |       |
| Full stack starts successfully with one primary command path |          |       |
| Full test suite runs with another command path               |          |       |
| Self-hostable local deployment path works                    |          |       |

### Acceptance criteria checklist

| Task                                                                                  | Progress | Notes |
| ------------------------------------------------------------------------------------- | -------- | ----- |
| Full stack starts successfully                                                        |          |       |
| Migrations apply cleanly                                                              |          |       |
| Frontend pages are navigable and functional                                           |          |       |
| Sources can be added and edited                                                       |          |       |
| Refresh can discover videos according to policy                                       |          |       |
| Scheduled refresh works, including hourly refresh                                     |          |       |
| Transcript retrieval works when available                                             |          |       |
| Fallback transcription works when transcripts are unavailable and fallback is enabled |          |       |
| Audio files are deleted after successful processing by default                        |          |       |
| Article generation works through OpenAI                                               |          |       |
| Article generation works through LM Studio                                            |          |       |
| Articles appear in the library                                                        |          |       |
| Reader page is polished and usable                                                    |          |       |
| Statuses are visible                                                                  |          |       |
| Failures are retryable                                                                |          |       |
| Logs and diagnostics are useful                                                       |          |       |
| Automated tests run successfully                                                      |          |       |
| No primary page is a dead placeholder                                                 |          |       |
| No critical flow requires a second implementation run to become operational           |          |       |


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

## Deep Analysis: Function-by-Function Status (Done vs Not Done)

Status key used below:
- **✅ Done**: implemented and wired in runtime.
- **🟡 Partial**: implemented but limited, hard-coded, or not fully aligned with roadmap behavior.
- **❌ Not done**: missing behavior expected by roadmap/acceptance intent.

### A) Backend — Service Layer

| Function | Status | Evidence-based notes |
| --- | --- | --- |
| `normalize_source_url(url)` | 🟡 Partial | Validates YouTube URLs and normalizes `/channel/...` + handle URLs, but does not fully resolve canonical channel identity (`channel_id` is not resolved from handle/custom URLs). |
| `evaluate_video_policy(video, source)` | 🟡 Partial | Enforces shorts/min-duration/livestream/window filters, but depends on discovery payload fields that are currently sparse (duration/is_live defaults). |
| `_feed_url_from_source_url(source_url)` | 🟡 Partial | Supports `/channel/`, `/@handle`, and `channel_id` query. Unsupported formats fail (playlist/custom URL patterns not covered). |
| `_parse_atom_entries(feed_xml)` | 🟡 Partial | Parses Atom entries correctly, but sets `duration=0` and `is_live=False` for all entries, constraining policy accuracy. |
| `discover_videos(source)` | ✅ Done | Fetches Atom feed, parses entries, and returns `max_videos` bounded list with graceful failure handling. |
| `select_transcript_strategy(source)` | 🟡 Partial | Returns stored strategy directly, but strategy is not fully enforced end-to-end in pipeline runtime. |
| `should_fallback_to_transcription(...)` | ✅ Done | Implements decision logic for force/disable/default fallback behavior. |
| `_extract_video_id(video_url)` | ✅ Done | Handles `youtu.be`, watch query `v=`, and embed/shorts path formats. |
| `fetch_transcript(video_url, languages)` | ✅ Done | Retrieves transcript text via `youtube-transcript-api` and returns normalized joined transcript output. |
| `transcribe_audio_locally(video_url, yt_dlp_command)` | ✅ Done | Downloads audio with `yt-dlp`, transcribes using Faster-Whisper CPU model, returns transcript text. |
| `render_prompt(template, transcript, mode)` | ✅ Done | Deterministic template interpolation for mode + transcript placeholders. |
| `_chat_completion(...)` | ✅ Done | Calls OpenAI-compatible `/chat/completions` endpoint and extracts assistant content. |
| `generate_article(transcript, prompt, cfg)` | 🟡 Partial | Supports OpenAI + LM Studio-compatible routing, but relies on global settings and has minimal provider error taxonomy/config depth. |
| `refresh_source(db, source_id)` | 🟡 Partial | Discovers videos, applies policy, dedups, queues/processes items, updates scan timestamps; lacks richer refresh-run accounting and lock/backoff semantics. |
| `process_video_item(db, item_id)` | 🟡 Partial | Runs transcript/fallback/generation/versioning path; currently hard-codes strategy (`transcript_first`), language (`en`), provider/model, and prompt template instead of persisted per-source/per-settings policy. |

### B) Backend — API and Runtime

| Function | Status | Evidence-based notes |
| --- | --- | --- |
| `health()` | ✅ Done | Returns simple service health payload. |
| `get_settings(...)` | ✅ Done | Returns persisted settings merged with defaults. |
| `put_settings(...)` | ✅ Done | Upserts arbitrary key/value settings. |
| `list_sources(...)` | ✅ Done | Lists persisted sources via ORM query. |
| `create_source(...)` | 🟡 Partial | Creates source with normalization and basic fields, but does not resolve/persist canonical channel identity metadata. |
| `refresh(...)` | ✅ Done | Triggers source refresh pipeline entrypoint. |
| `patch_source(...)` | ✅ Done | Generic source patch for mutable model fields. |
| `list_jobs(...)` | ✅ Done | Returns jobs sorted newest-first. |
| `retry_job(...)` | 🟡 Partial | Marks job as `retry_pending` only; no worker-side retry execution mechanism implemented here. |
| `library(...)` | 🟡 Partial | Returns article list with title search and preview, but not richer filtering/sorting/grouping described in roadmap. |
| `article_detail(...)` | ✅ Done | Returns article and version history payload for reader view. |
| `regenerate(...)` | ✅ Done | Reuses processing pipeline for version regeneration path. |
| `collections(...)` | ✅ Done | Lists collections. |
| `create_collection(...)` | 🟡 Partial | Supports creation only; edit/delete/detail association flows absent in routes. |
| `diagnostics()` | 🟡 Partial | Includes db/queue/ffmpeg/yt-dlp/faster-whisper style checks, but several values are optimistic constants (e.g., queue/db true path). |
| `logs(...)` | ✅ Done | Returns latest log events. |
| `tick_sources()` | ✅ Done | Scheduler tick processes due enabled sources and advances `next_run_at`. |
| `start_scheduler()` | ✅ Done | Prevents duplicate scheduler jobs and starts periodic ticking. |
| `get_db()` | ✅ Done | Standard session-yield dependency with proper close semantics. |
| `startup()` | 🟡 Partial | Bootstraps schema and scheduler for local use, but migration-first production flow is not enforced. |

### C) Frontend (React SPA)

| Function | Status | Evidence-based notes |
| --- | --- | --- |
| `Page(...)` | ✅ Done | Shared page container for route views. |
| `StatCard(...)` | ✅ Done | Shared metric card component. |
| `Layout()` | ✅ Done | Multi-page navigation and route wiring implemented. |
| `Home()` | 🟡 Partial | Displays high-level dashboard + recent articles, but omits deeper “continue reading/scheduler health/unread” roadmap depth. |
| `Sources()` | ✅ Done | Add/list/edit source controls and manual refresh action present. |
| `Jobs()` | ✅ Done | Job table with retry action for failed jobs. |
| `Library()` | 🟡 Partial | Title search and reader link available, but advanced filters/sorts/grouping are not implemented. |
| `Reader()` | 🟡 Partial | Version switch + regenerate present, but lacks richer reader ergonomics (themes, typography controls, transcript panel, progress tracking). |
| `Settings()` | 🟡 Partial | Generic key/value settings editor works; domain-specific grouped settings UX from roadmap not implemented. |
| `Diagnostics()` | ✅ Done | Diagnostics payload visualized in UI. |
| `Logs()` | 🟡 Partial | Basic log listing implemented, but no searching/filtering/severity drill-down controls. |
| `Collections()` | 🟡 Partial | Create + list implemented, but edit/delete/detail/article assignment flows missing. |

### D) Progress table interpretation (based on current code)

- The codebase is **strongest in baseline end-to-end wiring** (source creation, refresh invocation, transcript/transcription path, article generation, library/reader views). 
- It is **partially complete in policy richness and operational hardening** (canonical identity resolution, strategy matrix completeness, retry/backoff semantics, and observability depth).
- It is **incomplete in advanced UX and full roadmap surface area** (reader personalization, advanced filtering, comprehensive collections workflows, and broad settings coverage).

### Practical conclusion

Current state is a **working prototype with meaningful real functionality**, not a fully roadmap-complete v1. The remaining gap is mostly in **hardening + completeness**, not initial scaffolding.
