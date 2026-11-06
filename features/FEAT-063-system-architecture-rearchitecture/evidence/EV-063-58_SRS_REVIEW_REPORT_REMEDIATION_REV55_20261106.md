# EV-063-58 — SRS review report remediation (Plan Rev55)

**Completed:** 2026-11-07 (Asia/Saigon)
**Feature:** FEAT-063 — system architecture rearchitecture
**Branch:** `docs/feat063-v25-report-remediation-20261106`
**Source base:** `1431ef81972b71303fd4a7909748fd3005769a3c` (`dev` at worktree creation)
**Plan:** `plan/PLAN_REV55_SRS_REPORT_REMEDIATION_20261106.md`
**Approval:** owner’s direct request, recorded in root and FEAT-063 approval registers before edits.
**Final plan SHA-256:** `FE9A7717E5D4A1573FAD5B86F02C82455769CFC3125C67FC221C2F66B671001E`.

## Source reviewed

- Owner-provided, read-only document: `Sketch2Life_Bao_cao_hop_nhat_Fix_1_luot_v2_5.docx` (supplied from Downloads; not copied into the repository).
- The report was reviewed as an 8-page DOCX with 363 paragraphs and 5 tables. It contains 16 contradiction/alignment findings (M-01–M-16), 20 missing-specification findings (D-01–D-20), and 13 open questions (Q-01–Q-13).
- Canonical working source at task start: FEAT-063 SRS v2.5-draft and its Data Table Register companion. Current output is v2.6-draft; both remain unsigned.
- Supporting evidence: FEAT-063 context/source/status/decision records, approved plan and repository source at the recorded base commit. Older SRS copies were treated as historical.

## Work completed

- Added `artifacts/REPORT_REMEDIATION_CROSSWALK_REV55_20261106.md` with an explicit disposition for all 49 report items. Supported contradictions were corrected; evidence-limited details and unresolved owner choices remain OPEN or NOT SPECIFIED.
- Added `artifacts/ARCHITECTURE_DETAIL_CATALOG_REV55_20261106.md` for logical role/scope, relationships and lineage, state/admission/retry behavior, target API workflows, screen coverage, domain ports, and package dependencies.
- Updated the canonical SRS and Data Table Register to v2.6-draft. Reconciled Parent activity ordering, exact lesson-version references, Q159 roles, permission scope, API/workflow traces, state transitions, job target kinds, age/count narrative, logical versus physical table identifiers, and historical versus local database observations.
- Cross-checked the related UI review’s Teacher Sketch Deck concern against BR-42/Q167: the mandatory-step claim is stale; the current SRS already makes Deck generation opt-in per session, with readiness required before presentation only when enabled.
- Updated the canonical authority pointer, AGENTS instructions, FEAT-063 source/context/status/decision records, task plan, approvals, and evidence pointers. Added a source-only §32.7 snapshot for the recorded `dev` source base.
- Kept open questions open, including quota-pool precedence/prices, exceptional media access, sample eligibility, role aliasing, invitation acceptance/expiry, Parent history period, age-band details and handling legacy ages 121–155, and exact physical DDL.

## Source snapshot boundary

The source-only review records that the main FastAPI composition does not mount `ai_jobs`, while StoryRun-lite is a separate app using in-process `BackgroundTasks`. Source presence is not treated as proof of API availability, durable jobs, end-to-end AI behavior, database migration, or production readiness. No current OpenAPI, runtime, DB, provider, or Modal result was regenerated for this documentation task.

## Validation

- `git diff --check`: passed; no whitespace errors (Git emitted only line-ending normalization warnings for two existing documents).
- Crosswalk item count: passed, 49 unique IDs (M=16, D=20, Q=13). Version/authority pointers and Rev55 cross-artifact links were checked; supporting files and SRS anchor `srs-32-7` exist.
- Markdown whitespace scan for the Rev55 outputs and `git diff --check`: passed.
- Product tests/API tests/database/migrations/Modal/provider/deployment/security validation: not run. No product code or runtime configuration changed; no commit or push was requested.

## Changed files

- Root: `AGENTS.md`, `docs/context/SRS_AUTHORITY.md`, `approvals/TASK_APPROVAL.md`.
- FEAT-063: canonical SRS, Data Table Register, context, source register, decisions, status, approvals, Rev55 plan, this evidence, crosswalk and architecture detail catalog.
