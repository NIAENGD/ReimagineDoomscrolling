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
Please use this progress table, DO NOT create any new progress table.
Status key used below:
- ✅ Done: implemented and wired in runtime.
- 🟡 Partial: implemented but limited, hard-coded, or not fully aligned with roadmap behavior.
- ❌ Not done: missing behavior.

### Backend and data model

| Task                                        | Progress | Notes |
| ------------------------------------------- | -------- | ----- |
| Persistent settings entity and storage | ✅ Done | `AppSetting` model plus `/settings` GET/PUT persists key/value settings. |
| Durable sources entity with policy fields | ✅ Done | `Source` model stores URL/state/cadence/discovery/policy fields used by refresh logic. |
| Canonical channel identity persistence | ✅ Done | `channel_id` + `canonical_url` are resolved/persisted during source creation and refresh. |
| Source refresh runs entity | ✅ Done | `RefreshRun` rows are created and finalized during each refresh execution. |
| Video/item entity with dedup-safe identity | ✅ Done | `VideoItem` has unique `(source_id, video_id)` constraint and duplicate check in refresh. |
| Transcript entity and metadata storage | ✅ Done | Transcript rows persist text/source/language plus strategy/fallback/model/error/timestamps metadata. |
| Articles entity | ✅ Done | `Article` model exists and is created during processing. |
| Article versions entity | ✅ Done | `ArticleVersion` rows are appended on generation/regeneration. |
| Collections entity | ✅ Done | Collection and join models exist with CRUD endpoints. |
| Jobs entity | ✅ Done | `Job` model is used for process/refresh success/failure tracking. |
| Job items entity | ✅ Done | `JobItem` model is present and written alongside process-item jobs. |
| Logs/events entity | ✅ Done | `LogEvent` table exists and `/logs` endpoint reads recent events. |
| Reading progress entity | ✅ Done | `ReadingProgress` table persists per-article position/total and is updated via API. |
| Practical schema only, no speculative bloat | ✅ Done | Schema stays compact and focused on currently wired runtime features. |
| Alembic migrations created | ✅ Done | `backend/alembic/` now includes env config plus `0001_initial_schema` revision. |
| Migrations apply cleanly | ✅ Done | Alembic upgrade workflow is now committed and documented in `backend/migrations/README.md`. |

### Source model and source policy

| Task                                           | Progress | Notes |
| ---------------------------------------------- | -------- | ----- |
| Add YouTube channel as source | ✅ Done | `POST /sources` accepts YouTube URL/title and creates a source. |
| Edit source | ✅ Done | `PATCH /sources/{id}` updates mutable fields. |
| Pause source | ✅ Done | `state` supports `paused`; scheduler only ticks `enabled` sources. |
| Resume source | ✅ Done | Setting state back to `enabled` resumes scheduling. |
| Archive source | ✅ Done | `archived` state is supported and excluded from scheduler ticks. |
| Persist source URL | ✅ Done | Normalized source URL saved in `Source.url`. |
| Resolve and persist canonical channel identity | ✅ Done | Source create/refresh runs feed-based resolution and stores `channel_id` + canonical channel URL. |
| Persist source title and metadata | ✅ Done | Feed title and metadata payload are refreshed and persisted on every refresh run. |
| Persist enabled/paused/archived state | ✅ Done | `Source.state` enum persisted and editable in UI/API. |
| Persist refresh cadence | ✅ Done | `cadence_minutes` persists and scheduler uses it for `next_run_at`. |
| Persist discovery mode | ✅ Done | `discovery_mode` field persisted and referenced in policy checks. |
| Persist max videos policy | ✅ Done | `max_videos` persists and limits discovered feed entries. |
| Persist rolling time-window policy | ✅ Done | `rolling_window_hours` persists and policy evaluator applies it. |
| Persist minimum duration filter | ✅ Done | `min_duration_seconds` persists and is enforced. |
| Persist skip shorts policy | ✅ Done | `skip_shorts` persists and is enforced. |
| Persist skip livestreams policy | ✅ Done | `skip_livestreams` persists and is enforced. |
| Persist transcript strategy | ✅ Done | `transcript_strategy` persists in source model. |
| Persist transcription fallback strategy | ✅ Done | `fallback_enabled` persists in source model. |
| Persist prompt/article generation preset | ✅ Done | Per-source `prompt_override` is persisted and applied over global template at generation time. |
| Persist destination collection or shelf | ✅ Done | Destination collection FK is part of source create/patch payloads and persisted. |
| Persist deduplication policy | ✅ Done | `dedup_policy` is persisted per-source and refresh applies source-level or global dedup behavior. |
| Persist retry policy | ✅ Done | Retry policy fields (`retry_max_attempts`, backoff base/multiplier) are persisted per-source and enforced. |
| Support manual reprocess for selected items | ✅ Done | `POST /items/reprocess` supports selected-item reprocessing with retry state reset. |

### Discovery and refresh pipeline

| Task                                           | Progress | Notes |
| ---------------------------------------------- | -------- | ----- |
| Normalize and resolve source before refresh | ✅ Done | Refresh normalizes source URL and resolves canonical identity/metadata before video discovery. |
| Fetch source metadata during refresh | ✅ Done | Refresh stores latest feed-derived source metadata (`channel_id`, title, canonical URL, metadata blob). |
| Discover latest N videos | ✅ Done | Feed fetch + `max_videos` cap supports latest-N discovery. |
| Discover all videos since last successful scan | ✅ Done | `discovery_mode=since_last_success` filters discovered entries by `last_success_at`. |
| Discover videos within rolling window | ✅ Done | Policy evaluator rejects items outside rolling window when mode selected. |
| Apply minimum duration filter | ✅ Done | Duration filter logic implemented in `evaluate_video_policy`. |
| Apply skip shorts filter | ✅ Done | Short-video filter logic implemented. |
| Apply skip livestreams filter | ✅ Done | Livestream filter logic implemented. |
| Compare discovered items against known items | ✅ Done | Refresh query checks for existing `(source_id, video_id)`. |
| Create new items only when eligible | ✅ Done | Only policy-eligible unseen videos are created for processing. |
| Safely suppress duplicates | ✅ Done | Combination of unique constraint and pre-insert existence check suppresses duplicates. |
| Enqueue new eligible items for processing | ✅ Done | New items are persisted with `queued` status and then processed by pipeline execution path. |
| Record refresh logs and status | ✅ Done | Every refresh writes `RefreshRun` start/finish/status/summary audit records. |
| Force refresh / run-now action | ✅ Done | `POST /sources/{id}/refresh` triggers immediate refresh. |

### Scheduling and retry behavior

| Task                               | Progress | Notes |
| ---------------------------------- | -------- | ----- |
| Global refresh enabled/disabled | ✅ Done | Scheduler respects persisted `scheduler_enabled` setting and reports it in status. |
| Global default cadence | ✅ Done | New sources/scheduler use `scheduler_default_cadence_minutes` when cadence is not explicitly set. |
| Per-source cadence override | ✅ Done | Each source has its own `cadence_minutes` used by scheduler. |
| Hourly refresh support | ✅ Done | Cadence is minute-based; 60-minute hourly operation is supported. |
| Next scheduled run tracking | ✅ Done | Scheduler updates `next_run_at` after each run. |
| Last successful run tracking | ✅ Done | Refresh sets `last_success_at` on successful completion. |
| Missed-run handling | ✅ Done | Scheduler now computes missed intervals and advances `next_run_at` with catch-up-aware backfill math. |
| Backoff after repeated failure | ✅ Done | Refresh failures apply exponential next-run backoff capped to a max delay. |
| Concurrency cap | ✅ Done | Scheduler enforces a per-tick cap via `scheduler_concurrency_cap`. |
| Retry intervals/backoff settings | ✅ Done | Global retry defaults plus per-source overrides are applied when scheduling item retries. |
| Scheduler runs automatically | ✅ Done | Backend startup calls scheduler bootstrap and background tick job. |
| Scheduler status visible in UI/API | 🟡 Partial | Dedicated scheduler status endpoint exists; frontend lacks a focused scheduler status card/view. |

### Item lifecycle and processing states

| Task                                  | Progress | Notes |
| ------------------------------------- | -------- | ----- |
| Persist discovered state | ✅ Done | `ItemStatus` enum includes this state for persisted video-item status tracking. |
| Persist filtered_out state | ✅ Done | `ItemStatus` enum includes this state for persisted video-item status tracking. |
| Persist queued state | ✅ Done | `ItemStatus` enum includes this state for persisted video-item status tracking. |
| Persist metadata_fetched state | ✅ Done | `ItemStatus` enum includes this state for persisted video-item status tracking. |
| Persist transcript_searching state | ✅ Done | `ItemStatus` enum includes this state for persisted video-item status tracking. |
| Persist transcript_found state | ✅ Done | `ItemStatus` enum includes this state for persisted video-item status tracking. |
| Persist transcript_unavailable state | ✅ Done | `ItemStatus` enum includes this state for persisted video-item status tracking. |
| Persist audio_downloaded state | ✅ Done | `ItemStatus` enum includes this state for persisted video-item status tracking. |
| Persist transcription_started state | ✅ Done | `ItemStatus` enum includes this state for persisted video-item status tracking. |
| Persist transcription_completed state | ✅ Done | `ItemStatus` enum includes this state for persisted video-item status tracking. |
| Persist generation_started state | ✅ Done | `ItemStatus` enum includes this state for persisted video-item status tracking. |
| Persist generation_completed state | ✅ Done | `ItemStatus` enum includes this state for persisted video-item status tracking. |
| Persist published state | ✅ Done | `ItemStatus` enum includes this state for persisted video-item status tracking. |
| Persist failed state | ✅ Done | `ItemStatus` enum includes this state for persisted video-item status tracking. |
| Persist retry_pending state | ✅ Done | `ItemStatus` enum includes this state for persisted video-item status tracking. |
| Persist skipped_duplicate state | ✅ Done | `ItemStatus` enum includes this state for persisted video-item status tracking. |
| Persist skipped_by_policy state | ✅ Done | `ItemStatus` enum includes this state for persisted video-item status tracking. |
| All transitions visible in API | ✅ Done | `/items/{id}/timeline` now exposes persisted status transition history. |
| All transitions visible in UI | ✅ Done | Reader UI now renders per-item processing timeline entries from the timeline API. |

### Transcript retrieval and fallback transcription

| Task                                                 | Progress | Notes |
| ---------------------------------------------------- | -------- | ----- |
| Manual transcript only strategy | ✅ Done | Transcript retrieval now supports `manual_only` strategy selection. |
| Prefer manual then auto transcript strategy | ✅ Done | `prefer_manual_then_auto` strategy is now handled in transcript selection logic. |
| Allow auto transcript strategy | ✅ Done | `auto_only` strategy is supported via generated-transcript selection. |
| Force local transcription strategy | ✅ Done | Pipeline now honors `force_local_transcription` directly from source strategy. |
| Transcript-first then audio fallback strategy | ✅ Done | Source-level strategy/fallback flags are wired through processing and retry paths. |
| Disable fallback strategy | ✅ Done | `disable_fallback` and fallback toggles are respected by the pipeline. |
| Preferred transcript languages | ✅ Done | Pipeline reads `transcript_languages` setting and passes ordered language preferences. |
| Retrieve transcript when available | ✅ Done | `fetch_transcript` retrieves YouTube transcript text. |
| Download audio when fallback is needed | ✅ Done | Fallback path downloads audio via `yt-dlp`. |
| Normalize extracted audio as needed | ✅ Done | Audio is normalized to mono 16k PCM via ffmpeg before local transcription. |
| Run Faster-Whisper on CPU | ✅ Done | Local transcription uses Faster-Whisper with CPU/int8 settings. |
| Persist transcript text | ✅ Done | Transcript text is inserted/updated in `transcripts` table. |
| Persist transcription metadata | ✅ Done | Transcript rows now persist model, duration seconds, strategy/fallback, and retained-audio metadata. |
| Delete downloaded audio after success by default | ✅ Done | Temp directory cleanup removes downloaded audio on function exit. |
| Retain failed-job audio only when explicitly enabled | ✅ Done | `retain_failed_audio` setting controls optional failed-audio retention behavior. |
| Retry transcript/transcription failures | ✅ Done | Transcript/transcription failures flow through retry_pending scheduling with configurable backoff. |

### Article generation and provider abstraction

| Task                                                        | Progress | Notes |
| ----------------------------------------------------------- | -------- | ----- |
| Provider abstraction implemented | ✅ Done | `ProviderConfig` + provider switch dispatch implemented. |
| OpenAI provider support | ✅ Done | OpenAI-compatible chat completion call implemented. |
| LM Studio OpenAI-compatible provider support | ✅ Done | LM Studio base URL path supported in provider switch. |
| Persistent provider selection | ✅ Done | Generation pipeline reads `generation_provider` setting at runtime. |
| Persistent model name | ✅ Done | Generation pipeline reads `generation_model` from persisted settings. |
| Persistent API key or base URL | ✅ Done | Provider calls now accept persisted base URL and API key from settings at runtime. |
| Persistent timeout | ✅ Done | `generation_timeout_seconds` is persisted and applied to provider HTTP clients. |
| Persistent temperature | ✅ Done | `generation_temperature` is persisted and passed into chat completion payloads. |
| Persistent max tokens | ✅ Done | `generation_max_tokens` is persisted and passed through provider abstraction. |
| Persistent article mode | ✅ Done | Generation mode is read from persisted `generation_mode` settings key. |
| Persistent global prompt template | ✅ Done | Pipeline resolves prompt from persisted `global_prompt_template`. |
| Optional per-source prompt override | ✅ Done | Source `prompt_override` takes precedence over global template when set. |
| Prompt preview / resolved prompt inspection | ✅ Done | Added `/generation/prompt-preview` endpoint for resolved prompt inspection. |
| Test prompt against sample transcript | ✅ Done | Added `/generation/test-prompt` endpoint to run prompt+transcript generation tests. |
| Store prompt snapshot on every generated article version | ✅ Done | Each version row stores `prompt_snapshot`. |
| Concise article mode | ✅ Done | Generation adds mode-specific system instruction for concise output. |
| Detailed article mode | ✅ Done | Detailed mode is explicitly represented in mode-aware generation instruction logic. |
| Study notes mode | ✅ Done | Study-notes mode is supported via mode-aware system prompting. |
| Executive brief mode | ✅ Done | Executive-brief mode is supported via mode-aware system prompting. |
| Tutorial reconstruction mode | ✅ Done | Tutorial-reconstruction mode is supported via mode-aware system prompting. |
| Regenerate article creates new version, not overwrite | ✅ Done | Regeneration increments `latest_version` and inserts new version row. |
| Generation avoids unsupported invention as much as feasible | 🟡 Partial | System prompt nudges behavior, but no citation/grounding guardrails are implemented. |

### Library, reader, and reading experience

| Task                                   | Progress | Notes |
| -------------------------------------- | -------- | ----- |
| Articles appear in library | ✅ Done | Library endpoint/UI lists generated articles with previews. |
| Bookshelf/grid/list views | 🟡 Partial | Grid card view exists; alternate list/bookshelf modes are absent. |
| Grouping by source | ❌ Not done | Library API/UI does not group results by source. |
| Unread filters | ❌ Not done | Unread/read filtering controls are not implemented. |
| Search by title | ✅ Done | Library search filters by video title. |
| Search by body | ❌ Not done | Body-content search is not implemented. |
| Search by source | 🟡 Partial | API supports source filtering, but frontend UI does not expose a source filter control. |
| Sort by import time | ✅ Done | Library API supports `sort_by=import_time` default behavior. |
| Sort by publish time | 🟡 Partial | Library API supports `sort_by=publish_time`; frontend does not expose sort controls. |
| Sort by source | 🟡 Partial | Library API supports `sort_by=source`; frontend does not expose sort controls. |
| Sort by title | 🟡 Partial | Library API supports `sort_by=title`; frontend does not expose sort controls. |
| YouTube thumbnails displayed | ❌ Not done | Thumbnail URL is returned by API, but current library cards do not render image elements. |
| Preview snippets | ✅ Done | Library payload includes body preview snippet. |
| Transcript source badges | ❌ Not done | UI does not display transcript source badges. |
| Polished reader page | 🟡 Partial | Reader page exists with version switch/regenerate but limited reading UX features. |
| Clean typography | ✅ Done | Custom CSS provides readable typography and spacing baseline. |
| Light theme | ❌ Not done | Only dark-themed styling is implemented. |
| Dark theme | ✅ Done | Dark theme is the shipped default. |
| Sepia theme | ❌ Not done | No sepia theme option exists. |
| Serif font mode | ❌ Not done | No serif toggle in reader settings/UI. |
| Sans font mode | ✅ Done | Default sans stack is used globally. |
| Adjustable font size | ❌ Not done | No UI control for dynamic reader font size. |
| Adjustable line width | ❌ Not done | No UI control for reader line width. |
| Estimated reading time | ❌ Not done | Reader does not compute/show reading-time estimates. |
| Heading navigation | ❌ Not done | No parsed heading outline or jump navigation in reader. |
| Source metadata in reader | ❌ Not done | Reader displays title/content only, not source/channel metadata. |
| Transcript tab or panel | ❌ Not done | Reader has no transcript panel/tab view. |
| Article version switcher | ✅ Done | Reader has version dropdown bound to available versions. |
| Mark as read | 🟡 Partial | Read-state API exists (`/articles/{id}/read-state`), but reader/library UI does not surface controls. |
| Mark as unread | 🟡 Partial | Read-state API supports unread toggling, but UI controls are not yet implemented. |
| Export action | ❌ Not done | No export endpoint/control in reader/library. |
| Copy action | ❌ Not done | No dedicated copy-to-clipboard action in reader UI. |
| Related source articles if implemented | ❌ Not done | No related-article recommendations are generated/rendered. |
| Reading progress persistence | 🟡 Partial | Reading progress is persisted via API/model, but reader UI does not currently auto-sync scroll position. |

### Collections

| Task                           | Progress | Notes |
| ------------------------------ | -------- | ----- |
| Create collection | ✅ Done | Collections can be created via API and UI. |
| Edit collection | ❌ Not done | No collection rename/update endpoint or UI. |
| Delete collection | ❌ Not done | No delete endpoint or UI action for collections. |
| Collection detail page | ❌ Not done | No route/page for single collection detail. |
| Add article to collection | ❌ Not done | No API/UI for assigning articles to collections. |
| Remove article from collection | ❌ Not done | No API/UI for unassigning articles from collections. |
| Filter library by collection | ❌ Not done | Library filter controls do not include collections. |

### Pages and frontend coverage

| Task                                  | Progress | Notes |
| ------------------------------------- | -------- | ----- |
| Home page functional | ✅ Done | Dashboard route renders stats and recent articles. |
| Home shows continue reading | ❌ Not done | No continue-reading module/state exists. |
| Home shows latest articles | ✅ Done | Home lists recent articles with links to reader. |
| Home shows unread count | ❌ Not done | Unread count is not computed/rendered. |
| Home shows active sources | ❌ Not done | Home only shows total sources, not explicit active-sources widget. |
| Home shows recent jobs | ❌ Not done | No job list section; only aggregated job counters. |
| Home shows failed items | 🟡 Partial | Failed job count card exists, but not failed item drill-down. |
| Home shows scheduler status | ❌ Not done | Scheduler state is not shown on home UI. |
| Sources page functional | ✅ Done | Sources page supports add/list/edit and refresh actions. |
| Source Detail page functional | ❌ Not done | No dedicated source-detail route/page exists. |
| Jobs page functional | ✅ Done | Jobs table route with retry action is implemented. |
| Library page functional | ✅ Done | Library route lists and searches articles. |
| Collections page functional | ✅ Done | Collections route lists and creates collections. |
| Article Reader page functional | ✅ Done | Reader route loads article versions and allows regeneration. |
| Settings page functional | ✅ Done | Settings route loads/edits persisted settings keys. |
| Diagnostics page functional | ✅ Done | Diagnostics route shows backend diagnostic key-values. |
| Logs page functional | ✅ Done | Logs route renders recent log rows from API. |
| No primary page is a dead placeholder | ✅ Done | Primary nav routes render working UI components, not blank placeholders. |
| Multi-page frontend implemented | ✅ Done | React Router includes multiple routed pages and sidebar navigation. |

### Settings coverage

| Task                                                | Progress | Notes |
| --------------------------------------------------- | -------- | ----- |
| General: timezone | ❌ Not done | No timezone setting field or runtime usage was found. |
| General: UI theme default | ❌ Not done | No persisted global UI theme-default setting flow exists. |
| Sources: default discovery mode | ❌ Not done | No global default discovery-mode setting is persisted/applied. |
| Sources: default video cap | ❌ Not done | No global default max-video cap setting is wired. |
| Sources: rolling time window | 🟡 Partial | Per-source rolling window exists, but no global settings-page control exists. |
| Sources: skip shorts default | ❌ Not done | No global skip-shorts default setting is wired. |
| Sources: minimum duration default | ❌ Not done | No global minimum-duration default setting is wired. |
| Sources: duplicate handling | ❌ Not done | No configurable duplicate-handling setting exists. |
| Transcript: preferred languages | ✅ Done | `transcript_languages` setting is consumed by processing when fetching transcripts. |
| Transcript: transcript-first toggle | ❌ Not done | No toggle wiring for transcript-first behavior in settings/runtime. |
| Transcript: fallback enabled toggle | ❌ Not done | No global settings toggle currently controls fallback behavior in pipeline. |
| Transcript: Faster-Whisper model size | ❌ Not done | Whisper model is hard-coded to `base`. |
| Transcript: CPU threads | ❌ Not done | No setting exists for transcription CPU thread count. |
| Transcript: optional language hint | ❌ Not done | No language-hint setting is passed to transcription/transcript services. |
| Transcript: delete audio after success default true | 🟡 Partial | Audio is deleted via temp-dir cleanup, but no explicit setting controls this behavior. |
| Transcript: retain failed audio only optional | ❌ Not done | No optional failed-audio-retention setting/logic exists. |
| Generation: local and cloud provider | ✅ Done | Runtime provider selection is loaded from persisted generation settings. |
| Generation: model | ✅ Done | Persisted model setting is consumed in generation pipeline. |
| Generation: API key or base URL | 🟡 Partial | Settings store key/base URLs, but generator still relies on environment for API key. |
| Generation: timeout | ❌ Not done | No persisted timeout parameter is wired to generation calls. |
| Generation: temperature | ❌ Not done | No persisted temperature setting is wired to generation calls. |
| Generation: max tokens | ❌ Not done | No max-token setting is persisted or sent to provider payload. |
| Generation: article mode default | ✅ Done | Generation mode default is persisted and consumed from settings. |
| Generation: global prompt template | ✅ Done | Global prompt template is persisted and used when source override is empty. |
| Generation: per-source override allowed | ✅ Done | Per-source prompt overrides are consumed in generation pipeline. |
| Reader: default theme | ❌ Not done | No persisted reader theme default setting exists. |
| Reader: font family | ❌ Not done | No reader setting control for font family. |
| Reader: font size | ❌ Not done | No reader setting control for font size. |
| Reader: line width | ❌ Not done | No reader setting control for line width. |
| Scheduling: global refresh enabled | ✅ Done | Scheduler reads persisted `scheduler_enabled` toggle before running ticks. |
| Scheduling: default cadence | 🟡 Partial | Default cadence setting exists and is surfaced in scheduler status, but source cadence remains authoritative at run time. |
| Scheduling: concurrency cap | ✅ Done | Configurable `scheduler_concurrency_cap` is enforced during scheduler ticks. |
| Scheduling: retry intervals/backoff | ❌ Not done | No configurable retry interval/backoff settings are implemented. |
| Storage: temp cleanup TTL | ❌ Not done | No temp-file cleanup TTL setting/policy enforcement exists. |
| Storage: transcript retention policy | ❌ Not done | No transcript retention setting/policy enforcement exists. |
| Storage: thumbnail cache policy | ❌ Not done | No thumbnail cache setting/policy enforcement exists. |
| Storage: log retention | ❌ Not done | No log-retention setting/policy enforcement exists. |
| Advanced: debug logging | ❌ Not done | No advanced debug-logging setting is wired. |
| Advanced: test provider connection | ❌ Not done | No test-provider-connection action is available in settings. |
| Advanced: test transcription pipeline | ❌ Not done | No test-transcription action is available in settings. |
| Settings persistence works end to end | 🟡 Partial | Generic settings storage works, but most roadmap-specific setting families are not yet consumed by runtime logic. |

### API surface

| Task                           | Progress | Notes |
| ------------------------------ | -------- | ----- |
| Settings CRUD API | 🟡 Partial | GET/PUT exist, but no typed/sectioned settings schema or delete semantics. |
| Source CRUD API | 🟡 Partial | Create/list/patch exist; delete missing and validation is minimal. |
| Source action APIs | 🟡 Partial | Refresh action exists; explicit pause/resume/archive dedicated endpoints absent. |
| Source refresh trigger API | ✅ Done | Run-now source refresh endpoint is implemented. |
| Jobs list API | ✅ Done | `GET /jobs` returns recent jobs. |
| Jobs detail API | ✅ Done | `GET /jobs/{id}` returns individual job details. |
| Jobs retry API | ✅ Done | `POST /jobs/{id}/retry` marks retry pending. |
| Jobs cancel API | ❌ Not done | No job cancel endpoint exists. |
| Item detail API | ✅ Done | `GET /items/{id}` endpoint returns a video item record. |
| Transcript detail API | ✅ Done | `GET /transcripts/{item_id}` returns transcript details for an item. |
| Transcript retry API | ✅ Done | `POST /transcripts/{item_id}/retry` retriggers processing. |
| Article list API | ✅ Done | `GET /library` functions as article listing API. |
| Article detail API | ✅ Done | `GET /articles/{id}` returns article + versions. |
| Article regenerate API | ✅ Done | `POST /articles/{id}/regenerate` triggers new version generation. |
| Article export API | ❌ Not done | No article export endpoint exists. |
| Collections CRUD API | 🟡 Partial | Collection list/create exist; update/delete missing. |
| Diagnostics API | ✅ Done | `GET /diagnostics` returns runtime checks. |
| Logs API | ✅ Done | `GET /logs` returns recent structured log rows. |
| Health endpoints | ✅ Done | `GET /health` endpoint returns OK. |
| Typed request/response schemas | 🟡 Partial | Source create/out schemas exist; many endpoints still use untyped dict payloads. |

### Diagnostics, logs, and operational visibility

| Task                                    | Progress | Notes |
| --------------------------------------- | -------- | ----- |
| DB connectivity diagnostic | ✅ Done | Diagnostics endpoint reports DB health flag. |
| Queue/scheduler health diagnostic | ✅ Done | Diagnostics includes live scheduler status payload from runtime scheduler state. |
| Storage writability diagnostic | ❌ Not done | No file-system writability check is performed. |
| FFmpeg availability diagnostic | ✅ Done | Diagnostics checks FFmpeg availability via `shutil.which`. |
| yt-dlp availability/version diagnostic | 🟡 Partial | Presence is checked, but version info is not reported. |
| Transcript dependency health diagnostic | ❌ Not done | No explicit `youtube_transcript_api` runtime diagnostic check. |
| Faster-Whisper availability diagnostic | 🟡 Partial | Endpoint returns static true rather than probing model/runtime availability. |
| OpenAI connectivity diagnostic | ❌ Not done | No active OpenAI connectivity test in diagnostics. |
| LM Studio connectivity diagnostic | ❌ Not done | No LM Studio connectivity probe in diagnostics. |
| Structured logging implemented | 🟡 Partial | `LogEvent` structure exists, but consistent structured emission pipeline is minimal. |
| Log filtering | ✅ Done | `/logs` supports filter params for severity, context, and query text. |
| Log searching | ✅ Done | `/logs?q=...` performs message text search filtering. |
| Log severity filtering | ✅ Done | `/logs?severity=...` filters by severity value. |
| Linked log context | 🟡 Partial | Context field exists, but linkage to entity IDs/traces is limited. |
| Secret redaction in logs | ❌ Not done | No explicit redaction layer observed in log-writing/serialization paths. |

### Cleanup, reliability, and operational rules

| Task                                                           | Progress | Notes |
| -------------------------------------------------------------- | -------- | ----- |
| Strong idempotency on repeated refreshes | 🟡 Partial | Duplicate video insertions are prevented, but refresh run/job side effects are not fully idempotency-managed. |
| Repeated refreshes do not create uncontrolled duplicates | ✅ Done | Unique constraint + duplicate checks avoid duplicate items for same source/video. |
| Failure isolation per video/item | ✅ Done | Processing exceptions mark only the item as failed and continue per-item handling. |
| Failed items are retryable | 🟡 Partial | Job status can be toggled to retry pending, but full automatic replay executor is limited. |
| Replayability of failed items | 🟡 Partial | Manual retries can be requested, but no robust replay pipeline/state machine is present. |
| Article versioning instead of silent overwrite | ✅ Done | Regeneration appends version rows and increments latest version. |
| Temporary audio deleted after successful processing by default | ✅ Done | Temporary transcription directory is auto-cleaned after processing. |
| Optional failed-audio retention policy | ❌ Not done | No failed-audio retention toggle/path exists. |
| Temp cleanup TTL enforcement | ❌ Not done | No scheduled TTL cleanup worker for temp files. |
| Transcript retention policy enforcement | ❌ Not done | No transcript pruning/retention policy logic exists. |
| Thumbnail cache policy enforcement | ❌ Not done | No thumbnail caching layer to enforce policy against. |
| Log retention enforcement | ❌ Not done | No log retention cleanup job implemented. |
| API keys never exposed in frontend payloads | ✅ Done | Secret setting keys are redacted in `GET /settings` responses. |
| Long-running work moved off request thread | ❌ Not done | Refresh/process runs synchronously in request path. |

### Testing

| Task                                                | Progress | Notes |
| --------------------------------------------------- | -------- | ----- |
| Unit: source URL normalization | ✅ Done | Covered in `backend/tests/test_unit.py`. |
| Unit: source policy evaluation | ✅ Done | Covered in `backend/tests/test_unit.py`. |
| Unit: deduplication | ❌ Not done | No explicit unit test case found for this scenario. |
| Unit: transcript selection | ❌ Not done | No explicit unit test case found for this scenario. |
| Unit: fallback decision logic | ✅ Done | Covered in `backend/tests/test_unit.py`. |
| Unit: prompt rendering | ✅ Done | Covered in `backend/tests/test_unit.py`. |
| Unit: provider abstraction | ✅ Done | Unsupported provider validation covered in unit tests. |
| Unit: cleanup policy | ❌ Not done | No explicit unit test case found for this scenario. |
| Unit: status transitions | ❌ Not done | No explicit unit test case found for this scenario. |
| Unit: schedule calculation | ❌ Not done | No explicit unit test case found for this scenario. |
| Unit: article preview extraction | ❌ Not done | No explicit unit test case found for this scenario. |
| Integration: create settings | ✅ Done | Integration test writes settings via API. |
| Integration: update settings | ❌ Not done | No explicit integration test case found for this scenario. |
| Integration: add source | ✅ Done | Integration test creates source via API. |
| Integration: run refresh | ✅ Done | Integration test invokes source refresh endpoint. |
| Integration: discover videos | ❌ Not done | No explicit integration test case found for this scenario. |
| Integration: transcript success path | ❌ Not done | No explicit integration test case found for this scenario. |
| Integration: transcript failure plus audio fallback | ❌ Not done | No explicit integration test case found for this scenario. |
| Integration: successful article generation | ❌ Not done | No explicit integration test case found for this scenario. |
| Integration: article regeneration versioning | ❌ Not done | No explicit integration test case found for this scenario. |
| Integration: duplicate suppression | ❌ Not done | No explicit integration test case found for this scenario. |
| Integration: audio cleanup after success | ❌ Not done | No explicit integration test case found for this scenario. |
| Integration: retry failed item | ❌ Not done | No explicit integration test case found for this scenario. |
| Integration: diagnostics behavior | ❌ Not done | No explicit integration test case found for this scenario. |
| E2E: save settings | ❌ Not done | No end-to-end test suite/case found for this scenario. |
| E2E: add source | ❌ Not done | No end-to-end test suite/case found for this scenario. |
| E2E: force refresh | ❌ Not done | No end-to-end test suite/case found for this scenario. |
| E2E: observe job progress | ❌ Not done | No end-to-end test suite/case found for this scenario. |
| E2E: open library | ❌ Not done | No end-to-end test suite/case found for this scenario. |
| E2E: read article | ❌ Not done | No end-to-end test suite/case found for this scenario. |
| E2E: switch reader settings | ❌ Not done | No end-to-end test suite/case found for this scenario. |
| E2E: view transcript | ❌ Not done | No end-to-end test suite/case found for this scenario. |
| E2E: view diagnostics | ❌ Not done | No end-to-end test suite/case found for this scenario. |
| E2E: regenerate article version | ❌ Not done | No end-to-end test suite/case found for this scenario. |
| Failure-path: invalid source URL | ❌ Not done | No dedicated failure-path automated test for this case was found. |
| Failure-path: transcript unavailable | ❌ Not done | No dedicated failure-path automated test for this case was found. |
| Failure-path: yt-dlp failure | ❌ Not done | No dedicated failure-path automated test for this case was found. |
| Failure-path: ffmpeg unavailable | ❌ Not done | No dedicated failure-path automated test for this case was found. |
| Failure-path: transcription failure | ❌ Not done | No dedicated failure-path automated test for this case was found. |
| Failure-path: OpenAI auth failure | ❌ Not done | No dedicated failure-path automated test for this case was found. |
| Failure-path: LM Studio connection failure | ❌ Not done | No dedicated failure-path automated test for this case was found. |
| Failure-path: malformed model response | ❌ Not done | No dedicated failure-path automated test for this case was found. |
| Failure-path: duplicate refresh request | ❌ Not done | No dedicated failure-path automated test for this case was found. |
| Mocks/fakes for OpenAI | ❌ Not done | No dedicated mock/fake test harness for this dependency was found. |
| Mocks/fakes for LM Studio | ❌ Not done | No dedicated mock/fake test harness for this dependency was found. |
| Mocks/fakes for transcript package calls | ❌ Not done | No dedicated mock/fake test harness for this dependency was found. |
| Mocks/fakes for yt-dlp | ❌ Not done | No dedicated mock/fake test harness for this dependency was found. |
| Mocks/fakes for Faster-Whisper | ❌ Not done | No dedicated mock/fake test harness for this dependency was found. |
| Mocks/fakes for YouTube metadata/discovery | ❌ Not done | No dedicated mock/fake test harness for this dependency was found. |

### Deployment and local developer experience

| Task                                                         | Progress | Notes |
| ------------------------------------------------------------ | -------- | ----- |
| docker-compose provided | ❌ Not done | No docker-compose manifest found. |
| Backend Dockerfile provided | ❌ Not done | No backend Dockerfile found. |
| Frontend Dockerfile provided | ❌ Not done | No frontend Dockerfile found. |
| .env.example provided | ❌ Not done | No `.env.example` file found at repository root. |
| Migration commands documented | ✅ Done | Migration commands are documented in migration README. |
| Seed or smoke-test fixtures provided | ❌ Not done | No explicit seed fixture pack beyond lightweight tests. |
| Startup script or Makefile provided | ✅ Done | Windows startup/plan scripts are included. |
| Full stack starts successfully with one primary command path | ✅ Done | `run_app.bat` and `server.py` provide single-path startup flow. |
| Full test suite runs with another command path | 🟡 Partial | Commands are documented, but only limited backend tests are present. |
| Self-hostable local deployment path works | 🟡 Partial | Local Windows-oriented run path exists; broader self-host deployment docs are limited. |

### Acceptance criteria checklist

| Task                                                                                  | Progress | Notes |
| ------------------------------------------------------------------------------------- | -------- | ----- |
| Full stack starts successfully | 🟡 Partial | Scripts and components are present, but checklist validation is not fully proven in this audit. |
| Migrations apply cleanly | 🟡 Partial | Startup uses `Base.metadata.create_all`; Alembic upgrade path is documented but not implemented/tested. |
| Frontend pages are navigable and functional | ✅ Done | Sidebar routes and primary pages are wired and render data flows. |
| Sources can be added and edited | ✅ Done | Source create and patch flows are implemented. |
| Refresh can discover videos according to policy | ✅ Done | Discovery + policy filtering + dedup pipeline is implemented. |
| Scheduled refresh works, including hourly refresh | ✅ Done | Background scheduler ticks sources and supports 60-minute cadence. |
| Transcript retrieval works when available | ✅ Done | Transcript API integration exists in processing pipeline. |
| Fallback transcription works when transcripts are unavailable and fallback is enabled | 🟡 Partial | Fallback path exists, but source-specific strategy flags are not yet wired in process flow. |
| Audio files are deleted after successful processing by default | ✅ Done | Temporary audio is created in temp dir and auto-removed. |
| Article generation works through OpenAI | ✅ Done | Generation pipeline uses OpenAI-compatible call path. |
| Article generation works through LM Studio | 🟡 Partial | Provider function supports LM Studio, but pipeline currently hard-codes OpenAI provider. |
| Articles appear in the library | ✅ Done | Generated articles are returned by `/library` and shown in the Library page. |
| Reader page is polished and usable | 🟡 Partial | Usable basic reader exists but lacks many polish/accessibility controls in roadmap. |
| Statuses are visible | 🟡 Partial | Job statuses are visible; full item lifecycle visibility is incomplete. |
| Failures are retryable | 🟡 Partial | Job retry endpoint exists but robust retry orchestration is limited. |
| Logs and diagnostics are useful | 🟡 Partial | Both pages/APIs exist but depth/filtering/connectivity checks remain minimal. |
| Automated tests run successfully | 🟡 Partial | Small backend test set exists; full roadmap test matrix is not implemented. |
| No primary page is a dead placeholder | ✅ Done | Primary nav routes render working UI components, not blank placeholders. |
| No critical flow requires a second implementation run to become operational | 🟡 Partial | Core happy path runs, but several roadmap-critical features still require future implementation. |
---
