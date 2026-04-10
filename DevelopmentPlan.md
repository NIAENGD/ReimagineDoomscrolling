Build a complete, production-style, full-stack web application that continuously converts YouTube content into an ebook-like personal reading library. This is not a demo, not a prototype, not a mockup, not a partial proof of concept, and not a scaffold for later repair. It must be implemented as a complete app in one run, with the core product working end to end on first delivery, including tests, migrations, background jobs, scheduling, cleanup, operational visibility, and a polished multi-page UI. Do not leave critical features as placeholders. Do not rely on future cleanup runs to fix broken architecture or incomplete flows.

The product goal is simple: the user subscribes to YouTube channels, the system checks them on a schedule, discovers new videos, retrieves or generates transcripts, transforms the content into high-quality reading artifacts using a configurable LLM provider, and publishes those artifacts into a polished bookshelf and reader experience so the user can consume the substance of long videos through reading instead of watching filler-heavy content.

Mandatory dependency verification rule: before writing any integration against any external package, framework, API, CLI tool, local model server, or library, always search for and verify the current official documentation, release behavior, endpoint shape, flags, and compatibility details for the exact dependency being used. Never rely on stale memory for package APIs. This is mandatory, especially for YouTube transcript packages, yt-dlp, Faster-Whisper, FastAPI ecosystem packages, schedulers, frontend libraries, OpenAI API integration, and LM Studio OpenAI-compatible endpoints. If current upstream behavior differs from prior assumptions, implement against current upstream behavior.

Product scope:

This app is a continuous personal reading platform, not a one-off summarizer. It must support persistent sources, recurring refresh, transcript retrieval, audio-transcription fallback, article generation, library organization, and a real reading experience. The source model must be durable and policy-driven. Do not hardcode “top 10 videos.” Video count and discovery behavior must be configurable globally and overrideable per source.

Version 1 should focus on YouTube channels as the fully supported source type. However, architect the source model cleanly so playlists and manual video lists can be added later without schema collapse or rewrites.

Core requirements:

The app must be a real server-hosted web application with:

* persistent backend
* real database
* background workers
* recurring scheduler
* storage cleanup
* structured logs
* multi-page frontend
* durable settings
* complete tests

The system must allow the user to:

* add YouTube channels as sources
* configure how many videos to ingest and how to discover them
* configure refresh cadence, including hourly refresh
* automatically detect and process new videos
* fetch transcripts when available
* fall back to local CPU transcription using Faster-Whisper when transcripts are unavailable
* generate article-style outputs using either OpenAI or LM Studio
* browse generated content in a bookshelf/library
* read articles in a polished ebook-like reader
* regenerate articles with versioning
* search, filter, and organize articles
* see full per-item processing status
* retry failures
* automatically delete downloaded audio after successful processing by default

Source policy model:

A source is not just a URL. A source is a persistent ingestion policy. Each source must include:

* source URL
* canonical channel identity
* title and metadata
* enabled/paused/archived state
* refresh cadence
* discovery mode
* max videos or time-window policy
* transcript strategy
* transcription fallback strategy
* prompt/article generation preset
* destination collection or shelf
* deduplication policy
* retry policy

Discovery behavior must be configurable. At minimum support:

* latest N videos
* all videos since last successful scan
* videos within rolling window
* minimum duration filter
* skip shorts
* skip livestreams if identifiable
* manual reprocess selected items

Refresh behavior:

Implement a scheduler subsystem with:

* global refresh enabled/disabled
* global default cadence
* per-source cadence override
* hourly refresh support
* run-now action
* pause/resume source
* next scheduled run
* last successful run
* missed-run handling
* backoff after repeated failure

A source refresh must:

1. normalize and resolve the source
2. fetch source metadata
3. discover eligible videos according to source policy
4. compare against already known videos
5. create new items only when appropriate
6. enqueue processing for new eligible items
7. avoid duplicates safely
8. record refresh logs and status

Item lifecycle:

Each discovered video must have explicit lifecycle states. At minimum:

* discovered
* filtered_out
* queued
* metadata_fetched
* transcript_searching
* transcript_found
* transcript_unavailable
* audio_downloaded
* transcription_started
* transcription_completed
* generation_started
* generation_completed
* published
* failed
* retry_pending
* skipped_duplicate
* skipped_by_policy

All transitions must be persisted and visible in API and UI.

Transcript and transcription pipeline:

Implement a transcript-first pipeline with policy controls. Support:

* manual transcript only
* prefer manual then auto transcript
* allow auto transcript
* force local transcription
* transcript first then audio fallback
* disable fallback
* preferred transcript languages

If transcript retrieval fails and fallback is enabled:

* download audio
* extract and normalize as needed
* run Faster-Whisper on CPU
* persist transcript text
* record transcription metadata
* delete downloaded audio after success by default
* optionally retain failed-job audio only if explicitly enabled

Article generation:

Implement a provider abstraction supporting:

* OpenAI
* LM Studio using OpenAI-compatible endpoint

Support persistent generation settings:

* provider selection
* model name
* API key or base URL
* timeout
* temperature
* max tokens
* article mode
* prompt template

Prompting should be simple but complete. Do not overbuild exotic prompt-management UIs normal users will never touch. Support:

* one global default prompt template
* optional per-source prompt override
* prompt preview/resolved prompt inspection
* test prompt against a sample transcript
* stored prompt snapshot on every generated article version

Support useful article modes such as:

* concise article
* detailed article
* study notes
* executive brief
* tutorial reconstruction

The generation system must remove filler while preserving substance. It must not invent unsupported claims.

Reader and library experience:

This is a core product requirement. The app should feel like a reading product, not an admin dashboard. The article reader must support:

* clean typography
* light/dark/sepia themes
* serif/sans font modes
* adjustable font size
* adjustable line width
* estimated reading time
* heading navigation
* source metadata
* transcript access
* article version switcher
* mark as read/unread
* export and copy actions

The library must be first-class and support:

* bookshelf/grid/list views
* grouping by source
* unread filters
* search by title/body/source
* sorting by import time, publish time, source, title
* YouTube thumbnails
* preview snippets
* transcript source badges

Collections should exist, but keep them simple:

* create collection
* add/remove articles
* filter by collection

Pages:

Implement these pages and make all of them functional:

1. Home
   Show:

* continue reading
* latest articles
* unread count
* active sources
* recent jobs
* failed items
* scheduler status

2. Sources
   Support:

* add source
* edit source
* pause/resume/archive
* force refresh
* source stats and status

3. Source Detail
   Show:

* source metadata
* effective rules
* latest refreshes
* discovered videos
* per-item statuses
* source-level overrides
* reprocess selected items

4. Jobs
   Show:

* all jobs
* filters by source/date/status
* job detail
* per-item logs/errors

5. Library
   Support:

* search
* filters
* grouping
* shelf/grid/list
* open reader

6. Collections
   Support:

* create/edit/delete collections
* collection detail
* add/remove articles

7. Article Reader
   Support:

* polished reading view
* typography/theme controls
* metadata
* transcript tab or panel
* version switching
* export/copy
* related source articles if feasible

8. Settings
   Split logically into:

* General
* Sources
* Transcript/Transcription
* Generation
* Reader
* Scheduling
* Storage
* Advanced

9. Diagnostics
   Show:

* DB connectivity
* queue/scheduler health
* storage writability
* FFmpeg availability
* yt-dlp availability/version
* transcript dependency health
* Faster-Whisper availability
* OpenAI connectivity
* LM Studio connectivity

10. Logs
    Support:

* filtering
* searching
* severity
* linked context

Settings scope:

Implement strong but practical settings. Exclude obscure controls normal users will not touch. Include:

General:

* timezone
* UI theme default

Sources:

* default discovery mode
* default video cap
* rolling time window
* skip shorts default
* minimum duration default
* duplicate handling

Transcript/Transcription:

* preferred languages
* transcript-first toggle
* fallback enabled toggle
* Faster-Whisper model size
* CPU threads
* language hint optional
* delete audio after success default true
* retain failed audio only optional

Generation:

* provider
* model
* API key or base URL
* timeout
* temperature
* max tokens
* article mode default
* global prompt template
* per-source override allowed

Reader:

* default theme
* font family
* font size
* line width

Scheduling:

* global refresh enabled
* default cadence
* concurrency cap
* retry intervals/backoff

Storage:

* temp cleanup TTL
* transcript retention policy
* thumbnail cache policy
* log retention

Advanced:

* debug logging
* test provider connection
* test transcription pipeline

Architecture:

Use a Python backend and modern TypeScript frontend. Recommended baseline:

* FastAPI backend
* SQLAlchemy 2.x
* Alembic
* PostgreSQL
* Redis
* Celery plus scheduler support such as Celery Beat or APScheduler
* Next.js with TypeScript
* Tailwind CSS
* React Query or equivalent
* pytest
* Playwright

Data model:

At minimum implement durable entities for:

* settings
* sources
* source refresh runs
* videos/items
* transcripts
* articles
* article versions
* collections
* jobs
* job items
* logs/events
* reading progress

Keep schema practical. Do not bloat it with speculative entities that have no UI or operational value in version 1.

API requirements:

Implement real REST API support for:

* settings CRUD
* source CRUD and source actions
* source refresh trigger
* jobs list/detail/retry/cancel
* item detail
* transcript detail/retry
* article list/detail/regenerate/export
* collections CRUD
* diagnostics
* logs
* health endpoints

Operational rules:

Implement strong idempotency. Repeated refreshes must not create uncontrolled duplicates.

Implement failure isolation. One failed video must not fail the full source.

Implement replayability. Failed items must be retryable.

Implement article versioning. Regeneration must create a new article version rather than silently overwriting.

Implement structured logging.

Implement cleanup discipline. Temporary audio files must be deleted after successful processing by default.

Implement secret redaction. API keys must never appear in logs or frontend payloads.

Implement no-placeholder core flow rule. These features must work in version 1:

* source creation
* refresh discovery
* transcript retrieval
* fallback transcription
* article generation
* library
* article reader
* settings persistence
* scheduler
* retries
* cleanup
* diagnostics
* tests

Testing requirements:

Tests are required in the first implementation pass.

Unit tests must cover:

* source URL normalization
* source policy evaluation
* deduplication
* transcript selection
* fallback decision logic
* prompt rendering
* provider abstraction
* cleanup policy
* status transitions
* schedule calculation
* article preview extraction

Integration tests must cover:

* create/update settings
* add source
* run refresh
* discover videos
* transcript success path
* transcript failure plus audio fallback
* successful article generation
* article regeneration versioning
* duplicate suppression
* audio cleanup after success
* retry failed item
* diagnostics behavior

Use mocks/fakes for:

* OpenAI
* LM Studio
* transcript package calls
* yt-dlp
* Faster-Whisper
* YouTube metadata/discovery

End-to-end tests with Playwright must cover:

* save settings
* add source
* force refresh
* observe job progress
* open library
* read article
* switch reader settings
* view transcript
* view diagnostics
* regenerate article version

Include failure-path tests for:

* invalid source URL
* transcript unavailable
* yt-dlp failure
* ffmpeg unavailable
* transcription failure
* OpenAI auth failure
* LM Studio connection failure
* malformed model response
* duplicate refresh request

A developer must be able to start the full stack locally with one primary command path and run the full test suite with another.

Implementation quality requirements:

Write this as production-grade application code, not tutorial code.

Use typed schemas and clear interfaces.

Use clear separation of concerns.

Use migrations.

Do not rely on frontend-only state for durable data.

Do not block API requests on long-running work.

Do not hardcode a single provider.

Do not assume dependency behavior without searching current upstream docs first.

Do not leave TODOs in any primary flow.

Recommended implementation order:

1. project scaffolding and infra
2. DB schema and migrations
3. settings and provider config
4. source model and CRUD
5. refresh discovery pipeline
6. transcript retrieval
7. audio download and fallback transcription
8. article generation
9. library and reader
10. scheduler
11. cleanup and diagnostics
12. collections and polish
13. tests
14. final validation

Acceptance criteria:

The app is complete only if all of the following are true:

* full stack starts successfully
* migrations apply cleanly
* frontend pages are navigable and functional
* sources can be added and edited
* refresh can discover videos according to policy
* scheduled refresh works, including hourly refresh
* transcript retrieval works when available
* fallback transcription works when transcripts are unavailable and fallback is enabled
* audio files are deleted after successful processing by default
* article generation works through OpenAI and LM Studio
* articles appear in the library
* reader page is polished and usable
* statuses are visible
* failures are retryable
* logs and diagnostics are useful
* automated tests run successfully
* no primary page is a dead placeholder
* no critical flow requires a second implementation run to become operational

Final instruction:

Build this as a complete, durable, self-hostable personal reading platform for YouTube-derived knowledge. The user should feel like they are subscribing to channels and receiving a continuously updated personal ebook library, not running one-off summarization jobs. Optimize for completeness, reliability, clean data flow, polished reading UX, and first-pass usability. Before integrating any dependency, always search current upstream documentation and implement against current behavior, not memory.
