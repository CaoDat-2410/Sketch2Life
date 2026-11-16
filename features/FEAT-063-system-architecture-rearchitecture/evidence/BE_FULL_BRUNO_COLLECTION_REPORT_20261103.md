# Full BE Bruno collection — implementation report

Date: 2026-11-03<br>
Status: **COLLECTION TASK COMPLETE — COVERAGE, BRUNO PARSE, AND LIMITED SAFE SMOKE PASS; DB-BACKED ROUTES NOT RUN**<br>
Approved plan: `plan/BE_FULL_BRUNO_COLLECTION_PLAN_20261103.md`<br>
Approved plan SHA-256: `4488A7B739FDCC80246AFB590DDFC229B6DCB37FEB9600C5B9501B160E5E80ED`

## Scope and source

Milestone 1 review round 3 was already recorded as **ACCEPTED** for the synthetic local demo before this separate artifact task began. The collection was generated from the current backend working tree on `feature/feat063-be-foundation`, HEAD `c4edf51fd5af69a327d6776625cf387447f4ec59`. Pre-existing local source/test edits were preserved; this task did not modify runtime source, tests, migrations, FEAT-064, or the existing StoryRun-lite collection.

The source is `application.state.runtime_openapi_schema` populated by the combined/classroom/demo app factories. It is the full internal runtime schema, not the FE/SRS `/openapi.json` projection. Generation disables dotenv loading, sets the AI provider to disabled, and does not enter the ASGI lifespan, connect to a database, start a server, or call an external service. Optional groups were separately measured by profile.

## Reconciled operation inventory

- Full runtime union: **136 mounted operations across 122 paths**, including 11 StoryRun-lite main-demo operations and three optional local-storage operations.
- Combined default: **122**; combined with StoryRun-lite: **133**; combined with local storage: **125**; classroom: **57**; demo: **35**.
- The historical Rev31 inventory has 135 declarations: 121 unconditional combined routes, three optional local storage operations, and 11 unmounted candidates. The current default runtime has one more operation than the historical unconditional count: `GET /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/pilot-profiles`, present in current runtime but absent from the static Rev31 catalog. The three storage routes remain optional, and all 11 unmounted candidates remain excluded from requests. This yields the current union of 136 without counting candidates as runnable.
- Coverage CSV: **147 rows** — 136 mounted request mappings plus 11 `unmounted-candidate` rows with no request file.
- Runtime schema operations all have unique operation IDs. The request bodies include 60 JSON and four multipart operations; examples were omitted from the exported schema, and body values are schema-shaped placeholders.
- The default Bruno environment points only to `http://127.0.0.1:8000`; the bearer token and IDs are placeholders. Mutating, query-style POST, and provider-capable requests are visibly labeled. The collection does not seed records or provide identity credentials.

## Validation results

- Generator: **PASS** — 136 operations / 122 paths, profile counts as listed above.
- Local operation-to-request and safety validator: **PASS** — 136/136 method-path pairs, no duplicates or omissions, 11 candidates excluded, loopback base URL, placeholder auth/environment, and no absolute machine paths or non-loopback URLs in artifacts.
- Ruff check: **PASS**. Ruff format check: **PASS**. The initial cache-backed Ruff check could not create `.ruff_cache`; the same checks were rerun with `--no-cache` and passed.
- Bruno parser: **PASS** — Bruno CLI 4.3.0, installed from the existing npm cache with offline mode, generated collection documentation for all environments using `bru docs generate --all-envs --no-git-link`; exit code 0, output 130,861 bytes. All 136 request names appear in that output. This parser operation sent no HTTP requests. `bru --help` exposes no separate list command.
- Parsed request inventory: **136/136 names present** in the CLI-generated documentation; the local coverage validator independently verified 136/136 method-path mappings.
- Bruno MCP request listing: **NOT AVAILABLE** — its configured discovery exposes only the existing StoryRun-lite collection and rejects the new path. The local coverage validator independently enumerates and verifies all 136 request files.
- Existing StoryRun-lite Bruno collection: **PRESERVED** — no file in that directory was edited for this task; all six files recorded in the Milestone 1 closeout hash manifest still match byte-for-byte.
- Mypy 1.20.2 on the two artifact scripts: **NO VERDICT** — mypy returned an internal error before reporting diagnostics.
- Safe Bruno loopback smoke: **PASS, 3/3 HTTP requests** — `GET /health` → 200; synthetic process-local `POST /v1/sessions` → 201; `GET /v1/sessions/{session_id}` → 200. CLI output reported 0 tests and 0 assertions; statuses were checked directly from CLI and Uvicorn output. Server bound only to `127.0.0.1:18080`, StoryRun-lite DB-backed routes were disabled, AI provider was disabled, and both database URLs were unset. The synthetic session existed only in process memory and disappeared when the server stopped.
- DB-backed BE1/Lesson Library reads and the StoryRun-lite flow: **NOT RUN** — no task-owned database or test identity was used. The StoryRun flow's DB-backed prerequisites were not enabled. Modal/GPU/provider calls: **0**.
- Harness: **PASS** (`HARNESS_VALID`, approval and asset gates enabled).
- Repository security: **PASS** (6,374 files scanned; no absolute machine paths).
- Architecture validator: **PASS**.
- `git diff --check`: **PASS**; only Git's CRLF normalization warnings were printed.

## Deliverables and boundaries

- `artifacts/be-full/openapi.runtime.json`
- `artifacts/be-full/API_COVERAGE.csv`
- `artifacts/be-full/bruno/` — one request for each mounted operation, with loopback-only `local` environment
- `artifacts/be-full/README.md`

The three documented loopback requests were the only API requests sent. No database operation or Modal/provider call was made. The owner later authorized a separate local collection commit with generator/validator scripts excluded; no push or merge is part of this closeout. The temporary API server stopped cleanly and port 18080 has no listener. Milestone 1 remains accepted for its synthetic local scope; Milestone 2 is not started. Collection parsing and the limited smoke are verified; DB-backed BE1/Lesson Library runtime coverage and the conditional StoryRun-lite flow remain unrun. Bruno MCP discovery/listing for the new directory and GUI import were not verified.

Supplemental snapshot: `.claude/handoff/snapshots/BE_FULL_BRUNO_COLLECTION_20261103_COMMIT_FINAL/`.

Sanitized CLI and loopback smoke transcript: `evidence/BE_FULL_BRUNO_VALIDATION_20261103.log`.
