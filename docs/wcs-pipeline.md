# WCS pipeline — end-to-end architecture

This document describes the West Coast Swing data pipeline from raw audio recording to the published wiki. It names each stage, the repository that runs it, and what each stage produces. It covers how the pieces fit together. Each repository documents its own stages:

- the substrate, its write and read surfaces and the operator workflows are in [`api-kaianolevine-com`'s `docs/wcs-pipeline.md`](https://github.com/mini-app-polis/api-kaianolevine-com/blob/main/docs/wcs-pipeline.md);
- the wiki's passes, worker and renderer are in [`wiki-curator-cog`'s `docs/PIPELINE.md`](https://github.com/mini-app-polis/wiki-curator-cog/blob/main/docs/PIPELINE.md), and its page spec is in [`docs/PAGES.md`](https://github.com/mini-app-polis/wiki-curator-cog/blob/main/docs/PAGES.md).

The pipeline spans these repositories:

- **`watcher-cog`** polls Google Drive for new files and signals downstream.
- **`transcription-cog`** is the ingest pipeline. It transcribes audio, runs LLM extraction and registers the source through the API.
- **`api-kaianolevine-com`** owns the substrate (Postgres), runs the Composition Service and exposes the read, write and admin endpoints.
- **`wiki-curator-cog`** is the wiki. It has LLM passes that link, fold and write prose over the canonical graph (the API holds their state), a Lambda worker that runs them for each composed source, and a deterministic renderer into markdown.
- **`website-astro-wcs`** is the SSR site that shows per-lesson notes and the operator admin pages.
- **`wcs-wiki`** is the markdown projection of the canonical entity graph, browsable in Obsidian and on GitHub.

The ADRs behind this pipeline:

- **`api-kaianolevine-com` ADR-0002**: the WCS entity substrate.
- **`api-kaianolevine-com` ADR-0003**: versioned extractions and corrections.
- **`api-kaianolevine-com` ADR-0004**: the rebuild from scratch that produced the current substrate.
- **`api-kaianolevine-com` ADR-0006**: operator direct edits on canonical state.
- **`wiki-curator-cog` ADR-0002**: the curator repurposed as a renderer over canonical entities.
- **`wiki-curator-cog` ADR-0005 / ADR-0006**: the self-generating wiki, and its state, jobs and worker in this pipeline.

---

## Pipeline overview

```
[lesson] → [audio file in Drive]
              │
              │ filename: YYYY-MM-DD instructors > students/org - Topic
              │ (filename-authoritative metadata)
              ▼
       watcher-cog (polls Drive)
              │
              │ POST /v1/transcription/runs → SQS (one job per file)
              ▼
       transcription-cog.process_transcript (Lambda worker)
       ┌────────────────────────────────────────────────┐
       │ 1. parse filename → ParsedFilename             │
       │ 2. read transcript text                        │
       │ 3. POST /v1/wcs/transcripts → wcs_transcripts  │
       │    (idempotent on drive_file_id)               │
       │ 4. LLM extraction call → extraction dict       │
       │ 5. POST /v1/wcs/sources                        │
       │    ├─ creates/updates wcs_sources              │
       │    ├─ writes wcs_source_extractions (active)   │
       │    └─ runs Composition Service synchronously   │
       │ 6. archive Drive file                          │
       └────────────────────────────────────────────────┘
              │
              ▼
       api-kaianolevine-com substrate
       (canonical-layer rows committed)
              │
              ├──────────────────┬──────────────────┬─────────────────┐
              ▼                  ▼                  ▼                 ▼
       wiki worker        website notes UI    admin portal       Q&A agent
       (wiki-curator-     (website-astro-     (in website-       (reads legacy
        cog, Lambda)       wcs /notes/*)       astro-wcs           tables today)
              │                                 /admin/*)
              ▼
       page documents stored by the API
              │
              ▼ render (by hand)
       wcs-wiki repo
       (markdown export)
```

The forward flow (input to canonical) runs through the cogs and the API. Operator edits and corrections are written straight to the API. Corrections take effect when the source is recomposed; direct edits take effect immediately.

---

## Stages

### 1. Recording

A lesson, class or workshop is recorded. The result is an **audio file** in the configured Google Drive folder. The filename follows this convention:

```
YYYY-MM-DD instructors > students/org - Topic
```

Examples:

- `2026-05-15 Kaiano > Sarah - Anchor step quality`
- `2026-03-12 Robert Royston > Kaiano, Libby - Whip variations`
- `2025-09-08 Kaiano - Beginner WCS week 1`

The filename is **authoritative** for who taught (`instructors`), who attended (`students`), the organization or context, the session date and the topic. The LLM downstream never re-infers these fields from the transcript; the filename is the source of truth.

The cog skips a filename that doesn't parse cleanly, logs a Sentry warning, and does not ingest the file.

### 2. Drive watch (`watcher-cog`)

`watcher-cog` polls the configured WCS notes folder on a schedule. For each file it finds, it calls `POST /v1/transcription/runs`. The API claims the file and puts one job per file on `transcription-cog`'s SQS queue. `watcher-cog` itself is generic: it watches several folders for several cogs and has nothing WCS-specific in it.

### 3. Ingest (`transcription-cog`)

`transcription-cog`'s Lambda worker runs `process_transcript` once for each queued file. Jobs run one at a time, set by the queue consumer's concurrency setting. For each file it does the following:

1. **Parse the filename.** `filename_parser.parse_filename(name)` returns a `ParsedFilename` with `session_date`, `session_type`, `instructors`, `students`, `organization` and `title`. If parsing fails, the file is skipped.
2. **Read the transcript.** It reads the audio file from Drive and transcribes it to plain text. A transcript shorter than the configured minimum is skipped with the reason `transcript_too_short`.
3. **Store the transcript.** It calls `POST /v1/wcs/transcripts`, which is idempotent on `drive_file_id`. From that point the transcript is immutable.
4. **Extract.** It makes one LLM call over the transcript text and the parsed filename metadata. The result is a structured dict of attributions, definitions, relations, drill purposes, technique requirements and references.
5. **Store the source.** It calls `POST /v1/wcs/sources`. In that one synchronous call the API stores the extraction as the source's active version and runs the Composition Service. When the call returns, the source's canonical rows are committed. There is no eventual consistency. When `flags.wcs.wiki_jobs_enabled` is on, the API then queues a wiki `link` job for the source.
6. **Archive.** It moves the Drive file to the processed-files folder. This is the last step. If it fails, the source is already ingested and queryable, but the file may have to be moved by hand.

Steps 3 and 5 are the API's. What they write, and the substrate they write it to, are described in the API's [`docs/wcs-pipeline.md`](https://github.com/mini-app-polis/api-kaianolevine-com/blob/main/docs/wcs-pipeline.md).

---

## Consumers

### Website (`website-astro-wcs`)

The SSR Astro site at `wcs.kaianolevine.com` reads the API's caller-scoped endpoints and authenticates with a Clerk session JWT. Its pages:

- `/notes` lists the visible sources.
- `/notes/[id]` shows one source in detail.
- `/admin/notes` and `/admin/notes/[id]` manage source visibility and metadata, using the admin-scoped endpoints.
- `/admin/*` (future) will be the operator admin portal for corrections, additions, direct edits and gap discovery, per the API's ADR-0002 deferred work.

### Wiki worker (`wiki-curator-cog` ADR-0006)

A Lambda behind `wiki-curator-jobs.fifo` runs one job at a time.

- A `link` job links one source's statements and names its follow-on jobs: `consolidate` for its new entities, `generate` for the pages it touched, and, after each `generate`, a `materialise` that stores the changed pages' documents in the API.
- The worker posts follow-on jobs back to the API.
- Each job reads the export and the curator's state from the API and writes back what it changed.
- Every pass is watermarked, so a repeated job makes no model call.

### Wiki repo (`wcs-wiki`)

`wcs-wiki` is a local markdown export of the stored page documents. It is written by `python -m wiki_curator_cog.main render` and committed by hand, if at all. The Railway renderer that once cloned, rendered and pushed it is retired. The repo is not an edit surface, because a render overwrites the derived pages. Corrections go in as notes, through the same ingestion as lessons (`wiki-curator-cog` ADR-0005).

### Q&A agent

A retrieval-based agent sits behind `POST /v1/wcs/ask` on the API and is shown at `wcs.kaianolevine.com/notes/ask`. It still reads the legacy notes and transcript tables, not the canonical layer; moving it onto canonical state is future work.

---

## Boundaries

These are out of scope for the pipeline as a whole, and are named so future work knows where the edges are:

- **Inter-cog direct DB access.** Every cog is an API client. The substrate is owned by `api-kaianolevine-com`.
- **Operator UI in `wcs-wiki`.** The wiki is read-only for operators. Edits go to the API.
- **Transcript editing, retroactive re-extraction and in-place extraction edits.** These are the API's rules. See its `docs/wcs-pipeline.md`.

---

## Where the code is

- The ingest cog: `transcription-cog/src/transcription_cog/flow.py`, function `process_transcript`.
- The Composition Service: `api-kaianolevine-com/src/kaianolevine_api/services/wcs_composition.py`.
- The wiki worker and renderer: `wiki-curator-cog/src/wiki_curator_cog/` (`render.py` for the markdown).
- The website notes UI: `website-astro-wcs/src/pages/notes/`.
- ADRs: `api-kaianolevine-com/docs/decisions/` and `wiki-curator-cog/docs/decisions/`.
