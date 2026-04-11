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

## Progress Table (Current Repository Snapshot)

| Area | Status | What is implemented | What is not implemented / partial | Notes |
|---|---|---|---|---|
| Backend data model | 🟡 Mostly done | Rich entities exist for sources, items, transcripts, articles/versions, collections, jobs, logs, refresh runs. | Some modeled concepts are not fully wired in runtime logic (e.g., refresh run accounting fields are not fully exercised). | Good schema foundation for future hardening. |
| Backend API routes | 🟡 Functional baseline | Core endpoints exist for settings, sources, refresh, jobs, library, reader, collections, diagnostics, logs. | Several mutation endpoints use permissive `dict` payloads instead of strict schemas; limited validation and invariant checks. | Works for fast iteration but contract stability is medium. |
| Discovery pipeline | 🟡 Partially real | Real YouTube Atom feed parsing and policy filtering path exists. | Discovery only supports certain URL forms; duration/live metadata from Atom path remains minimal (`duration=0`, `is_live=False` placeholders). | Enough for first-pass ingestion, not robust ranking-quality discovery yet. |
| Transcript/transcription | 🟡 Core path implemented | Transcript API fetch + local Whisper fallback exists with `yt-dlp` download. | Strategy handling is simplified in pipeline call sites; error categorization and policy-specific fallback behaviors are still thin. | Practical baseline, missing advanced reliability controls. |
| Generation provider layer | 🟡 Core path implemented | Provider abstraction supports OpenAI and LM Studio/OpenAI-compatible endpoint. | Prompt management/version policy sophistication is limited; no token budgeting/safety controls yet. | Good initial abstraction point. |
| Scheduler/jobs/retry | 🟡 Basic implementation | APScheduler source tick and `next_run_at` updates exist; jobs are recorded on item processing attempts. | No full retry state machine/backoff orchestration; retry endpoint only marks status. | Observability exists but execution semantics are still lightweight. |
| Frontend web app | 🟡 Feature baseline | Multi-page SPA supports dashboard, source CRUD-lite, jobs list/retry, library, reader version switch, settings, diagnostics, logs, collections. | Advanced UX from plan (rich source policy editor, reader polish options, deep filters/sorts) is not complete. | Useful operator UI is in place. |
| Browser extension workflow | 🟢 Implemented (parallel path) | End-to-end automation scripts exist for collecting links, prompting ChatGPT, and viewing results pages. | Heavily dependent on DOM/cookie assumptions and local helper server endpoints; brittle against site UI changes. | Still valuable as experimental/legacy execution path. |
| Test coverage | 🟡 Foundational | Unit tests + one integration test exist for key service behavior and API flow sanity. | Coverage depth is still modest vs roadmap goals; frontend component tests are limited. | Baseline guardrails exist. |
| Security/config hardening | 🔴 Not done enough | Config and diagnostics primitives exist. | CORS/config hardening, auth modes, and stricter deployment safeguards remain roadmap items. | Biggest production-readiness gap. |

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

### 4) Browser Extension (automation path)

#### Popup controller (`extension/popup.js`)
- `addLog(text)`
- `checkLogin()`
- `checkServer()`
- `refreshStatus()`

#### Background orchestration (`extension/background.js`)
- `log(msg)`
- `setStatus(status, progress)`
- `persistArticle(a)`
- `parseJsonObject(text)`
- `startProcessing()`
- `openPopup(url, opts)`
- `waitTabComplete(tabId)`
- `ensureChatGPTReady()`
- `openTabs()`
- `collectLinks(tabId, count)`
- `fetchTranscript(url)`
- `fetchTitle(url)`
- `processTranscript(transcript, title)`
- `runChatPrompt(prompt)`
- `watchAndReact(url, like)`
- `cleanupTabs()`

#### Results UI (`extension/results.js`)
- `statusText(v)`
- `fmtDate(iso)`
- `renderStats(articles)`
- `renderRows(articles)`
- `applyFilters()`

#### ChatGPT page content script (`extension/chatgpt.js`)
- `waitFor(selector, root, timeout)`
- `waitAssistantReplyInternal()`
- `getComposer()`
- `dispatchEnter(node)`
- `dispatchInputLikeEvents(el)`
- `sleep(ms)`
- `sendPromptInternal(promptText)`

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
