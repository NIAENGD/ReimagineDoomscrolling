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
| Migrations apply cleanly | 🟡 Partial | Alembic files exist, but runtime startup still relies on `Base.metadata.create_all` rather than running `alembic upgrade`. |

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
| Apply minimum duration filter | 🟡 Partial | Filter logic exists, but Atom discovery currently sets duration to `0`, so this policy cannot use real YouTube durations yet. |
| Apply skip shorts filter | 🟡 Partial | Shorts logic exists, but current discovery payload lacks accurate duration metadata from YouTube feed responses. |
| Apply skip livestreams filter | 🟡 Partial | Livestream filter exists, but discovered feed items currently default `is_live=False`, so live detection is effectively missing. |
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
| Bookshelf/grid/list views | 🟡 Partial | Grid + list views now exist; dedicated bookshelf-style rendering is still absent. |
| Grouping by source | ✅ Done | Library API and UI both support group-by-source mode. |
| Unread filters | ✅ Done | Library UI now supports read/unread filter controls. |
| Search by title | ✅ Done | Library search filters by video title. |
| Search by body | ✅ Done | Library query now matches latest article body text as well as title/description. |
| Search by source | ✅ Done | Source filter control is available on Library page and wired to API. |
| Sort by import time | ✅ Done | Library API supports `sort_by=import_time` default behavior. |
| Sort by publish time | ✅ Done | Library frontend exposes sort controls, including publish-time sorting. |
| Sort by source | ✅ Done | Library frontend exposes source sort option. |
| Sort by title | ✅ Done | Library frontend exposes title sort option. |
| YouTube thumbnails displayed | 🟡 Partial | UI renders thumbnails, but default discovery currently does not populate thumbnail URLs from feed entries. |
| Preview snippets | ✅ Done | Library payload includes body preview snippet. |
| Transcript source badges | ✅ Done | Library cards display transcript source badge values. |
| Polished reader page | ✅ Done | Reader now includes metadata, transcript tab, copy/read actions, estimate, heading list, and persisted progress syncing. |
| Clean typography | ✅ Done | Custom CSS provides readable typography and spacing baseline. |
| Light theme | ✅ Done | Reader supports light theme mode via persisted settings. |
| Dark theme | ✅ Done | Dark theme is the shipped default. |
| Sepia theme | ✅ Done | Reader supports sepia theme mode via persisted settings. |
| Serif font mode | ✅ Done | Reader supports serif font family mode via persisted settings. |
| Sans font mode | ✅ Done | Default sans stack is used globally. |
| Adjustable font size | ✅ Done | Reader consumes persisted font-size setting for rendering. |
| Adjustable line width | ✅ Done | Reader consumes persisted line-width setting for rendering. |
| Estimated reading time | ✅ Done | Reader computes and displays estimated reading time. |
| Heading navigation | 🟡 Partial | Reader displays extracted heading outline, but no in-article anchor jumps yet. |
| Source metadata in reader | ✅ Done | Reader now renders source title/url metadata. |
| Transcript tab or panel | ✅ Done | Reader includes transcript tab alongside article view. |
| Article version switcher | ✅ Done | Reader has version dropdown bound to available versions. |
| Mark as read | ✅ Done | Reader and Library now provide mark-read controls wired to API. |
| Mark as unread | ✅ Done | Reader and Library now provide mark-unread controls wired to API. |
| Export action | 🟡 Partial | Backend export endpoint exists, but reader/library UI does not expose an export control yet. |
| Copy action | ✅ Done | Reader includes copy-to-clipboard action for article text. |
| Related source articles if implemented | ❌ Not done | No related-article recommendations are generated/rendered. |
| Reading progress persistence | ✅ Done | Reader now auto-syncs scroll position to progress API. |

### Collections

| Task                           | Progress | Notes |
| ------------------------------ | -------- | ----- |
| Create collection | ✅ Done | Collections can be created via API and UI. |
| Edit collection | ✅ Done | Collection rename API and UI are now implemented. |
| Delete collection | ✅ Done | Collection delete API and UI are now implemented. |
| Collection detail page | ✅ Done | Dedicated collection detail route/page now exists. |
| Add article to collection | ✅ Done | Library cards can add articles to collections through API. |
| Remove article from collection | ✅ Done | Collection detail page supports removing article assignments. |
| Filter library by collection | ✅ Done | Library includes collection filter control wired to API. |

### Pages and frontend coverage

| Task                                  | Progress | Notes |
| ------------------------------------- | -------- | ----- |
| Home page functional | ✅ Done | Dashboard route renders stats and recent articles. |
| Home shows continue reading | ✅ Done | Home now surfaces a continue-reading card from saved reading progress. |
| Home shows latest articles | ✅ Done | Home lists recent articles with links to reader. |
| Home shows unread count | ✅ Done | Home stat cards now include unread article count. |
| Home shows active sources | ✅ Done | Home stat cards now include active source count. |
| Home shows recent jobs | ✅ Done | Home now renders a recent jobs list. |
| Home shows failed items | 🟡 Partial | Failed job count card exists, but not failed item drill-down. |
| Home shows scheduler status | ✅ Done | Home now shows scheduler enabled status card. |
| Sources page functional | ✅ Done | Sources page supports add/list/edit and refresh actions. |
| Source Detail page functional | ✅ Done | Source detail route/page is now available with run-now action. |
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
| General: timezone | ✅ Done | Timezone setting is now exposed/persisted in settings flow. |
| General: UI theme default | ✅ Done | UI theme default is now exposed/persisted in settings flow. |
| Sources: default discovery mode | ✅ Done | Global default discovery mode is exposed in settings and applied to new sources. |
| Sources: default video cap | ✅ Done | Global default max-video cap is exposed in settings and applied to new sources. |
| Sources: rolling time window | ✅ Done | Global default rolling-window setting is exposed and applied to new sources. |
| Sources: skip shorts default | ✅ Done | Global skip-shorts default is exposed and applied to new sources. |
| Sources: minimum duration default | ✅ Done | Global minimum-duration default is exposed and applied to new sources. |
| Sources: duplicate handling | ✅ Done | Global default dedup policy is exposed and applied to new sources. |
| Transcript: preferred languages | ✅ Done | `transcript_languages` setting is consumed by processing when fetching transcripts. |
| Transcript: transcript-first toggle | ✅ Done | Transcript-first toggle is now exposed/persisted in settings flow. |
| Transcript: fallback enabled toggle | ✅ Done | Fallback-enabled toggle is now exposed/persisted in settings flow. |
| Transcript: Faster-Whisper model size | ✅ Done | Whisper model size is now exposed/persisted in settings flow. |
| Transcript: CPU threads | ✅ Done | CPU thread setting is now exposed/persisted in settings flow. |
| Transcript: optional language hint | ✅ Done | Optional transcription language hint is now exposed/persisted in settings flow. |
| Transcript: delete audio after success default true | ✅ Done | `delete_audio_after_success` is now a persisted setting consumed by local transcription flow. |
| Transcript: retain failed audio only optional | ✅ Done | `retain_failed_audio` now controls whether failed transcription audio is retained. |
| Generation: local and cloud provider | ✅ Done | Runtime provider selection is loaded from persisted generation settings. |
| Generation: model | ✅ Done | Persisted model setting is consumed in generation pipeline. |
| Generation: API key or base URL | ✅ Done | Runtime generation now accepts persisted API key/base URL values without requiring env-only key configuration. |
| Generation: timeout | ✅ Done | Persisted timeout setting is wired to generation provider requests. |
| Generation: temperature | ✅ Done | Persisted temperature setting is wired to generation provider requests. |
| Generation: max tokens | ✅ Done | Persisted max-token setting is wired to provider request payloads. |
| Generation: article mode default | ✅ Done | Generation mode default is persisted and consumed from settings. |
| Generation: global prompt template | ✅ Done | Global prompt template is persisted and used when source override is empty. |
| Generation: per-source override allowed | ✅ Done | Per-source prompt overrides are consumed in generation pipeline. |
| Reader: default theme | ✅ Done | Reader default theme is now configurable/persisted in settings and used in reader UI. |
| Reader: font family | ✅ Done | Reader font-family setting is now configurable/persisted and applied in UI. |
| Reader: font size | ✅ Done | Reader font-size setting is now configurable/persisted and applied in UI. |
| Reader: line width | ✅ Done | Reader line-width setting is now configurable/persisted and applied in UI. |
| Scheduling: global refresh enabled | ✅ Done | Scheduler reads persisted `scheduler_enabled` toggle before running ticks. |
| Scheduling: default cadence | ✅ Done | Default cadence setting is persisted, visible via scheduler status, and applied for sources missing cadence. |
| Scheduling: concurrency cap | ✅ Done | Configurable `scheduler_concurrency_cap` is enforced during scheduler ticks. |
| Scheduling: retry intervals/backoff | ✅ Done | Retry attempts and backoff settings are persisted and consumed by processing retry scheduling. |
| Storage: temp cleanup TTL | ✅ Done | Scheduler now enforces temp failed-audio cleanup using `temp_cleanup_ttl_hours`. |
| Storage: transcript retention policy | ✅ Done | Scheduler retention pass now supports transcript cleanup via `transcript_retention_days`. |
| Storage: thumbnail cache policy | ✅ Done | Scheduler retention pass now supports thumbnail cache eviction via `thumbnail_cache_ttl_days`. |
| Storage: log retention | ✅ Done | Scheduler retention pass now enforces log retention using `log_retention_days`. |
| Advanced: debug logging | ✅ Done | `debug_logging` advanced setting is now persisted and available in settings schema/configuration. |
| Advanced: test provider connection | ✅ Done | Settings flow includes `POST /generation/test-prompt` to validate provider/path configuration quickly. |
| Advanced: test transcription pipeline | ✅ Done | Transcript retry endpoint and persisted transcript settings allow end-to-end transcription pipeline checks. |
| Settings persistence works end to end | ✅ Done | Settings families are persisted and consumed by source creation, scheduler, processing, and generation runtime logic. |

### API surface

| Task                           | Progress | Notes |
| ------------------------------ | -------- | ----- |
| Settings CRUD API | ✅ Done | GET/PUT plus settings schema and key delete endpoint are implemented with typed payloads. |
| Source CRUD API | ✅ Done | Create/list/patch/delete source endpoints are implemented. |
| Source action APIs | ✅ Done | Refresh plus dedicated pause/resume/archive endpoints are implemented. |
| Source refresh trigger API | ✅ Done | Run-now source refresh endpoint is implemented. |
| Jobs list API | ✅ Done | `GET /jobs` returns recent jobs. |
| Jobs detail API | ✅ Done | `GET /jobs/{id}` returns individual job details. |
| Jobs retry API | ✅ Done | `POST /jobs/{id}/retry` marks retry pending. |
| Jobs cancel API | ✅ Done | `POST /jobs/{id}/cancel` updates job state to cancelled. |
| Item detail API | ✅ Done | `GET /items/{id}` endpoint returns a video item record. |
| Transcript detail API | ✅ Done | `GET /transcripts/{item_id}` returns transcript details for an item. |
| Transcript retry API | ✅ Done | `POST /transcripts/{item_id}/retry` retriggers processing. |
| Article list API | ✅ Done | `GET /library` functions as article listing API. |
| Article detail API | ✅ Done | `GET /articles/{id}` returns article + versions. |
| Article regenerate API | ✅ Done | `POST /articles/{id}/regenerate` triggers new version generation. |
| Article export API | ✅ Done | `GET /articles/{id}/export` supports markdown/txt/json output. |
| Collections CRUD API | ✅ Done | Collection create/list/get/update/delete endpoints are implemented. |
| Diagnostics API | ✅ Done | `GET /diagnostics` returns runtime checks. |
| Logs API | ✅ Done | `GET /logs` returns recent structured log rows. |
| Health endpoints | ✅ Done | `GET /health` endpoint returns OK. |
| Typed request/response schemas | ✅ Done | Expanded typed schemas now cover settings/source actions and common saved/deleted responses. |

### Diagnostics, logs, and operational visibility

| Task                                    | Progress | Notes |
| --------------------------------------- | -------- | ----- |
| DB connectivity diagnostic | ✅ Done | Diagnostics endpoint reports DB health flag. |
| Queue/scheduler health diagnostic | ✅ Done | Diagnostics includes live scheduler status payload from runtime scheduler state. |
| Storage writability diagnostic | ✅ Done | Diagnostics now performs a writable probe against `./tmp` and reports path/error details. |
| FFmpeg availability diagnostic | ✅ Done | Diagnostics checks FFmpeg availability via `shutil.which`. |
| yt-dlp availability/version diagnostic | ✅ Done | Diagnostics now reports resolved command path and `--version` output when available. |
| Transcript dependency health diagnostic | ✅ Done | Diagnostics now imports/probes `youtube_transcript_api` and returns dependency health + version where possible. |
| Faster-Whisper availability diagnostic | ✅ Done | Diagnostics now performs runtime module/class availability checks for Faster-Whisper and reports package version when available. |
| OpenAI connectivity diagnostic | ✅ Done | Diagnostics now probes OpenAI-compatible `/models` with configured base URL/key and returns status metadata. |
| LM Studio connectivity diagnostic | ✅ Done | Diagnostics now probes LM Studio `/models` endpoint and reports connectivity status metadata. |
| Structured logging implemented | ✅ Done | Pipeline and scheduler now emit structured `LogEvent` entries with consistent context and severity. |
| Log filtering | ✅ Done | `/logs` supports filter params for severity, context, and query text. |
| Log searching | ✅ Done | `/logs?q=...` performs message text search filtering. |
| Log severity filtering | ✅ Done | `/logs?severity=...` filters by severity value. |
| Linked log context | ✅ Done | Logging helper now appends source/item identifiers in context strings for easier traceability. |
| Secret redaction in logs | ✅ Done | Redaction helper now masks common API key/token patterns in persisted and API-returned log content. |

### Cleanup, reliability, and operational rules

| Task                                                           | Progress | Notes |
| -------------------------------------------------------------- | -------- | ----- |
| Strong idempotency on repeated refreshes | ✅ Done | Refresh loop now tracks duplicate IDs within a run and guards against duplicate DB insertion/update paths. |
| Repeated refreshes do not create uncontrolled duplicates | ✅ Done | Unique constraint + duplicate checks avoid duplicate items for same source/video. |
| Failure isolation per video/item | ✅ Done | Processing exceptions mark only the item as failed and continue per-item handling. |
| Failed items are retryable | ✅ Done | Failed/retry-pending items are retried by scheduler when `next_retry_at` is due and can also be manually retried. |
| Replayability of failed items | ✅ Done | Retry metadata (`retry_count`, `next_retry_at`, backoff settings) and manual/API reprocessing endpoints provide replay flow. |
| Article versioning instead of silent overwrite | ✅ Done | Regeneration appends version rows and increments latest version. |
| Temporary audio deleted after successful processing by default | ✅ Done | Temporary transcription directory is auto-cleaned after processing. |
| Optional failed-audio retention policy | ✅ Done | Local transcription now supports retain-on-failure behavior and persists retained file path metadata. |
| Temp cleanup TTL enforcement | ✅ Done | Scheduler retention worker prunes stale files in `./tmp/failed_audio` based on `temp_cleanup_ttl_hours`. |
| Transcript retention policy enforcement | ✅ Done | Scheduler retention worker prunes transcript rows by `transcript_retention_days`. |
| Thumbnail cache policy enforcement | ✅ Done | Scheduler retention worker clears stale thumbnail URLs by configured cache TTL. |
| Log retention enforcement | ✅ Done | Scheduler retention worker deletes old log rows according to `log_retention_days`. |
| API keys never exposed in frontend payloads | ✅ Done | Secret setting keys are redacted in `GET /settings` responses. |
| Long-running work moved off request thread | ❌ Not done | Refresh/process runs synchronously in request path. |

### Testing

Primary integration scenarios now use the RealLifeLore channel URL (`https://www.youtube.com/@RealLifeLore`) with deterministic monkeypatched discovery/transcript/generation paths for stable test execution.

| Task                                                | Progress | Notes |
| --------------------------------------------------- | -------- | ----- |
| Unit: source URL normalization | ✅ Done | Covered in `backend/tests/test_unit.py`. |
| Unit: source policy evaluation | ✅ Done | Covered in `backend/tests/test_unit.py`. |
| Unit: deduplication | ✅ Done | Added unit-level coverage for source-scoped dedup behavior and duplicate suppression logic. |
| Unit: transcript selection | ✅ Done | Added tests for transcript strategy/fallback decision behavior. |
| Unit: fallback decision logic | ✅ Done | Covered in `backend/tests/test_unit.py`. |
| Unit: prompt rendering | ✅ Done | Covered in `backend/tests/test_unit.py`. |
| Unit: provider abstraction | ✅ Done | Unsupported provider validation covered in unit tests. |
| Unit: cleanup policy | ✅ Done | Added deterministic unit checks for TTL-style cleanup cutoff behavior. |
| Unit: status transitions | ✅ Done | Added tests validating expected processing status progression order. |
| Unit: schedule calculation | ✅ Done | Added policy/schedule unit checks for rolling-window inclusion and exclusion outcomes. |
| Unit: article preview extraction | ✅ Done | Added explicit unit check for article preview truncation behavior. |
| Integration: create settings | ✅ Done | Integration test writes settings via API. |
| Integration: update settings | ✅ Done | Added integration coverage for writing/updating settings and validating persisted behavior via API. |
| Integration: add source | ✅ Done | Integration test creates source via API. |
| Integration: run refresh | ✅ Done | Integration test invokes source refresh endpoint. |
| Integration: discover videos | ✅ Done | Added integration tests that monkeypatch discovery for the RealLifeLore source and assert discovered items appear in library output. |
| Integration: transcript success path | ✅ Done | Added integration coverage for successful transcript fetch, transcript persistence, and published status transitions. |
| Integration: transcript failure plus audio fallback | ✅ Done | Added integration coverage that forces transcript failure, exercises local transcription fallback, and validates fallback metadata. |
| Integration: successful article generation | ✅ Done | Added integration tests that verify article generation output is persisted for discovered RealLifeLore items. |
| Integration: article regeneration versioning | ✅ Done | Added integration test that regenerates an article and asserts version increments/history growth. |
| Integration: duplicate suppression | ✅ Done | Added integration test that refreshes duplicate feed entries and verifies single library item output. |
| Integration: audio cleanup after success | ✅ Done | Added fallback integration coverage that asserts `delete_audio_after_success` is enabled for successful local transcription calls. |
| Integration: retry failed item | ✅ Done | Added integration test that fails processing once, retries the failed job, and verifies a successful transcript/article outcome. |
| Integration: diagnostics behavior | ✅ Done | Added integration test coverage for diagnostics payload structure and key runtime checks. |
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
| Failure-path: invalid source URL | ✅ Done | Added integration test that submits a non-YouTube URL and verifies API rejection. |
| Failure-path: transcript unavailable | ✅ Done | Added integration test that forces transcript fetch failure before fallback handling. |
| Failure-path: yt-dlp failure | ✅ Done | Added integration test that simulates yt-dlp/local transcription failure and verifies failed job + retry flow. |
| Failure-path: ffmpeg unavailable | ❌ Not done | No dedicated failure-path automated test for this case was found. |
| Failure-path: transcription failure | ❌ Not done | No dedicated failure-path automated test for this case was found. |
| Failure-path: OpenAI auth failure | ✅ Done | Added integration test that forces generation provider auth failure and verifies failed job capture. |
| Failure-path: LM Studio connection failure | ✅ Done | Added integration test that forces LM Studio provider connectivity failure and verifies failed job capture. |
| Failure-path: malformed model response | ✅ Done | Added integration test that forces malformed model response exceptions and verifies failure handling. |
| Failure-path: duplicate refresh request | ✅ Done | Added integration coverage that exercises duplicate discovery entries and validates suppression behavior. |
| Mocks/fakes for OpenAI | ✅ Done | Integration tests now monkeypatch generation calls to deterministic fake outputs. |
| Mocks/fakes for LM Studio | 🟡 Partial | OpenAI-compatible generation path is mockable; dedicated LM Studio-specific fixture matrix is still limited. |
| Mocks/fakes for transcript package calls | ✅ Done | Integration tests monkeypatch transcript-fetch path with deterministic responses. |
| Mocks/fakes for yt-dlp | 🟡 Partial | Local transcription path remains external-process based; test harness primarily targets transcript-first/mocked processing flows. |
| Mocks/fakes for Faster-Whisper | 🟡 Partial | Runtime diagnostics now probe dependency availability, but transcription model execution is not fully mocked in all failure matrix tests. |
| Mocks/fakes for YouTube metadata/discovery | ✅ Done | Integration tests monkeypatch discovery and identity resolution for deterministic source refresh coverage. |

### Deployment and local developer experience

| Task                                                         | Progress | Notes |
| ------------------------------------------------------------ | -------- | ----- |
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
| Migrations apply cleanly | 🟡 Partial | Startup still uses `Base.metadata.create_all`; Alembic migrations are present but not the active boot path. |
| Frontend pages are navigable and functional | ✅ Done | Sidebar routes and primary pages are wired and render data flows. |
| Sources can be added and edited | ✅ Done | Source create and patch flows are implemented. |
| Refresh can discover videos according to policy | 🟡 Partial | Pipeline exists, but feed-derived items currently miss duration/live metadata, limiting enforcement fidelity for related policies. |
| Scheduled refresh works, including hourly refresh | ✅ Done | Background scheduler ticks sources and supports 60-minute cadence. |
| Transcript retrieval works when available | ✅ Done | Transcript API integration exists in processing pipeline. |
| Fallback transcription works when transcripts are unavailable and fallback is enabled | ✅ Done | Pipeline uses per-source strategy and fallback flags, and calls local transcription when transcript retrieval fails/strategy requires fallback. |
| Audio files are deleted after successful processing by default | ✅ Done | Temporary audio is created in temp dir and auto-removed. |
| Article generation works through OpenAI | ✅ Done | Generation pipeline uses OpenAI-compatible call path. |
| Article generation works through LM Studio | ✅ Done | Pipeline reads persisted `generation_provider` and dispatches to LM Studio via OpenAI-compatible endpoint when selected. |
| Articles appear in the library | ✅ Done | Generated articles are returned by `/library` and shown in the Library page. |
| Reader page is polished and usable | ✅ Done | Reader includes version switching, transcript tab, copy/read controls, heading list, and persisted progress synchronization. |
| Statuses are visible | ✅ Done | Job list plus item timeline API/UI expose processing lifecycle state transitions. |
| Failures are retryable | ✅ Done | Failed/retry-pending items can be retried via scheduler timing, jobs retry endpoint, transcript retry endpoint, and manual reprocess API. |
| Logs and diagnostics are useful | ✅ Done | Diagnostics include dependency/connectivity probes and logs support severity/context/query filtering with redaction. |
| Automated tests run successfully | 🟡 Partial | Small backend test set exists; full roadmap test matrix is not implemented. |
| No primary page is a dead placeholder | ✅ Done | Primary nav routes render working UI components, not blank placeholders. |
| No critical flow requires a second implementation run to become operational | 🟡 Partial | Core flows exist, but default source policy + feed metadata gaps (duration/live/thumbnail) still require manual tuning for smooth first-run behavior. |
---
