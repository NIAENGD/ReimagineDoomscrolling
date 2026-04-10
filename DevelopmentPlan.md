# ReimagineDoomscrolling — Detailed Development Plan (Execution-Ready)

## 1) Purpose and Planning Principles

This plan defines how to evolve the current repository from a **working foundation** into a stable, production-grade personal YouTube-to-reading platform.

Guiding principles:
- Preserve current functionality while hardening architecture.
- Ship in vertical slices (backend + frontend + tests + ops) rather than isolated layers.
- Enforce measurable acceptance criteria for every milestone.
- Keep the workflow Windows-friendly via batch-driven developer operations.

---

## 2) Current-State Review (Repository-Wide)

### 2.1 What already exists and is valuable

- Full-stack baseline is present:
  - FastAPI backend with SQLAlchemy models and API routes.
  - React + TypeScript frontend with multi-page SPA sections (Home, Sources, Jobs, Library, Reader, Settings, Diagnostics, Logs, Collections).
  - APScheduler tick loop for recurring source processing.
- Data model includes many target concepts:
  - Sources, video items, transcripts, articles + versions, collections, jobs, logs, app settings.
  - Lifecycle/status enum already captures rich item processing states.
- Basic end-to-end integration flow exists:
  - Source creation → refresh → item processing → transcript/generation → article visible in library.
- Existing Windows operational scripts:
  - `run_app.bat` provides menu-driven bootstrap/run/test actions.
  - `run_server.cmd` provides direct backend launch.

### 2.2 Major gaps that must be closed

- Service layer is mostly stubbed/mock behavior:
  - YouTube discovery returns generated mock items, not real channel ingestion.
  - Transcript retrieval and local transcription are placeholders.
  - Article generation is local string formatting, not provider API execution.
- Scheduler/queue reliability needs hardening:
  - Single in-process scheduler, limited concurrency control, no robust retry/backoff policy persistence.
- API contracts are permissive in places:
  - Several endpoints accept `dict` payloads instead of strict schema validation.
- Security and config maturity needs improvement:
  - CORS currently wide-open (`*`).
  - Provider key storage/settings handling needs separation and safer operational defaults.
- Frontend UX is functional but not fully “reader-product polished”:
  - Reader theming/typography controls and richer filtering/sorting/metadata interactions need expansion.
- Operational diagnostics and observability are minimal:
  - No deep health checks, queue lag, run history analytics, or structured error reporting pipeline.

### 2.3 Constraints and compatibility goals

- Keep SQLite-first local development experience.
- Maintain Windows-first operation path with `.bat` tooling.
- Keep architecture compatible with PostgreSQL and external queue adoption later.

---

## 3) Target Product Definition (v1.0)

By v1.0, the platform should reliably provide:

1. **Durable source management** with policy-based refresh/discovery controls.
2. **Real ingestion pipeline** from YouTube channel data to published article.
3. **Transcript-first strategy** with optional local audio transcription fallback.
4. **Provider abstraction** supporting OpenAI and LM Studio OpenAI-compatible endpoints.
5. **Readable library experience** with article versioning and strong retrieval UX.
6. **Job and run transparency** (status, logs, retries, backoff, diagnostics).
7. **Automated test gate** across unit + integration + frontend checks.
8. **Windows-managed developer workflow** through `run_app.bat` + `manage_dev_plan.bat`.

---

## 4) Architecture Workstreams

## Workstream A — Backend API and Data Contracts

### A1. Schema hardening
- Replace generic `dict` API payloads with explicit Pydantic schemas for settings patches, source updates, job retries, collections create/update, and regenerate options.
- Add API response models for all read endpoints to ensure stable frontend contracts.

### A2. Validation and invariants
- Validate cadence bounds, discovery mode options, and policy constraints.
- Add uniqueness and state transition guards (e.g., invalid lifecycle jumps).

### A3. Error model standardization
- Add common error response schema with code, message, context, trace ID.

**Acceptance criteria**
- Invalid source/update payloads rejected with deterministic 4xx responses.
- API docs include all request/response shapes with examples.

---

## Workstream B — YouTube Discovery and Refresh Reliability

### B1. Real source normalization and identity resolution
- Normalize URL types (`@handle`, `/channel/`, `/c/`, `/user/`) into canonical source identity.
- Persist canonical identity fields and metadata refresh strategy.

### B2. Real video discovery implementation
- Replace mocked discovery with real extraction path.
- Apply policy filters consistently:
  - latest-N, rolling window, since-last-success,
  - shorts/livestream exclusions,
  - min duration.

### B3. Refresh run accounting
- Persist refresh run records with summary statistics:
  - fetched count, filtered count, enqueued count, duplicate count, failed count.

**Acceptance criteria**
- Re-running refresh does not duplicate items.
- Refresh run table explains outcomes for every source run.

---

## Workstream C — Transcript + Transcription Pipeline

### C1. Transcript retrieval strategy implementation
- Implement transcript retrieval policy modes:
  - manual only,
  - prefer manual + auto,
  - allow auto,
  - force local transcription,
  - disable fallback.

### C2. Audio fallback implementation
- On eligible failures, download audio + run local transcription + persist transcript metadata.
- Ensure cleanup policy is configurable and defaults to delete successful temp artifacts.

### C3. Fault categorization
- Track reasons: transcript unavailable, geo restricted, audio download failed, model runtime error, timeout.

**Acceptance criteria**
- Transcript source is always explicit (`manual`, `auto`, `local_transcription`).
- Failed steps generate actionable retry messages.

---

## Workstream D — Generation Provider Layer

### D1. Provider abstraction maturity
- Implement provider client interface with:
  - OpenAI API (official endpoint pattern),
  - LM Studio base URL compatibility mode.

### D2. Prompt and mode management
- Store global prompt template, per-source override, and mode presets.
- Persist prompt snapshots in every article version.

### D3. Safety and quality controls
- Add truncation/token budgeting and generation timeout handling.
- Distinguish model refusal/content errors from transport errors.

**Acceptance criteria**
- Regeneration creates deterministic new article version metadata.
- Provider switch does not require code changes.

---

## Workstream E — Frontend Experience and Usability

### E1. Source policy editor upgrades
- Add full policy controls in Sources page (mode, cadence, filters, fallback strategy).

### E2. Library ergonomics
- Expand filtering and sorting with source, read state, date window, collection.
- Improve result cards with thumbnails, status badges, and transcript source tags.

### E3. Reader polish
- Add reader controls:
  - theme (light/dark/sepia),
  - typography mode,
  - font size and width,
  - version switcher and metadata panel.

### E4. Diagnostics and logs UX
- Display health checks with actionable hints.
- Support log filter by severity/context/source/job.

**Acceptance criteria**
- Primary tasks (discover → read → regenerate → organize) are executable without API tools.

---

## Workstream F — Scheduler, Jobs, Retry, and Backoff

### F1. Scheduling logic hardening
- Introduce deterministic scheduling windows and source-level lock/lease protection.

### F2. Retry system
- Implement structured retry state machine with capped exponential backoff.

### F3. Job visibility
- Persist queue timing and duration fields for troubleshooting.

**Acceptance criteria**
- Repeated failures do not create thrash loops.
- Next run times and retry timers are explainable via API/UI.

---

## Workstream G — Testing, QA, and Release Discipline

### G1. Backend tests
- Unit tests for policy evaluation, state transitions, provider behavior, fallback decision logic.
- Integration tests for source lifecycle and regeneration/versioning.

### G2. Frontend tests
- Add component tests for source editing, library filtering, and reader controls.
- Add API contract tests for key view models.

### G3. End-to-end test script
- Add scriptable smoke flow:
  - create source,
  - run refresh,
  - confirm article publish,
  - regenerate,
  - verify versions.

**Acceptance criteria**
- CI-local test gate has no flaky default path.

---

## Workstream H — Operations, Security, and Configuration

### H1. Configuration model
- Separate local defaults from deployment-time secrets.
- Add environment templates and strict validation.

### H2. Security baseline
- Restrict CORS by configured origins.
- Add optional API auth mode for non-local deployments.

### H3. Observability
- Structured logs with source ID, video ID, job ID correlation keys.
- Add `/health` and `/ready` distinction and deeper diagnostics.

**Acceptance criteria**
- Misconfiguration errors are surfaced clearly at startup.

---

## 5) Milestone Timeline (Suggested)

## Milestone 1 — Foundation Hardening (1–2 weeks)
- API schema hardening.
- Validation/error standardization.
- Scheduler/job visibility improvements.
- Baseline regression tests.

## Milestone 2 — Real Ingestion Path (2–3 weeks)
- Real discovery implementation.
- Transcript strategy implementation.
- Fallback transcription integration.

## Milestone 3 — Generation and Reader UX (2 weeks)
- Real provider integration.
- Prompt/mode persistence.
- Reader controls + library enhancements.

## Milestone 4 — Reliability and Release (1–2 weeks)
- Retry/backoff completion.
- Diagnostics/log UX finalization.
- Performance pass + release checklist.

---

## 6) Definition of Done (Per Feature)

A feature is done only when all are true:
- Backend logic implemented with schema + validation.
- Frontend interaction implemented and usable.
- Unit/integration tests updated.
- Logs and diagnostics cover failure paths.
- Windows batch workflow includes how to run/verify it.
- Documentation updated.

---

## 7) Risk Register and Mitigation

1. **Dependency/API drift risk**
   - Mitigation: verify official docs before each integration change.
2. **Pipeline brittleness risk**
   - Mitigation: strict state transitions + retry classes + run history.
3. **Performance bottlenecks on local CPU transcription**
   - Mitigation: queue caps, timeout controls, optional skip policy.
4. **User trust risk due to silent failures**
   - Mitigation: explicit status reasons in UI and logs.

---

## 8) Windows-Managed Development Operations (.bat Required)

This repository should be operated primarily through batch scripts on Windows.

### Required scripts
- `run_app.bat` — app lifecycle (bootstrap/run/test).
- `manage_dev_plan.bat` — planning lifecycle (open plan, verify key files, run review checks, write status reports).

### Batch-first policy
- New contributors should not need to memorize backend/frontend command chains.
- Every recurring operational task should be reachable from a `.bat` menu option.

---

## 9) Development Review Cadence

Use a weekly cycle:
- Monday: scope lock and task assignment.
- Midweek: integration checkpoint (pipeline + UI + tests).
- Friday: plan review using `manage_dev_plan.bat`, publish status report, update milestone burndown.

---

## 10) Immediate Next Actions (Priority Ordered)

1. Implement strict request/response schemas for all mutable API endpoints.
2. Replace mock video discovery with real source fetch path.
3. Implement transcript strategy matrix and fallback execution.
4. Add provider clients and robust generation error handling.
5. Expand frontend policy controls and reader personalization.
6. Introduce richer retry/backoff visibility in Jobs + Logs.
7. Increase automated test coverage to guard full lifecycle behavior.
8. Keep all of the above executable and reviewable from Windows `.bat` workflows.
