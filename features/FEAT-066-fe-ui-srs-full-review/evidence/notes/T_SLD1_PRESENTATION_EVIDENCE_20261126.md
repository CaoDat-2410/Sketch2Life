# T-SLD1 Teacher presentation backend evidence

Date: 2026-11-25
Scope: Phase E E1, backend only
Approval: Owner approval recorded in the task instruction on 2026-11-25, including the provisional DDL parent.
Verification state: **NOT VERIFIED**. Tests were authored but not run, as instructed.

## Requirement basis

Implemented against the FEAT-063 v2.7-draft working SRS: FR-T-19 through FR-T-22, BR-43/44, AC-35, AT-16 and FR-AI-14. Routes and DDL remain new proposals (TD-new); this work does not imply formal SRS approval.

## Delivered

- Added occurrence-scoped presentations, immutable slide revisions, server-side READY transitions, plan pinning and derived stale-source responses.
- Aggregate and revision GET validators hash the complete JSON response, including freshness, presentability and slide media state; command `If-Match` validators remain strong revision numbers.
- Added upload-purpose support for JPEG/PNG/WebP presentation images. Attachment checks the completed upload scope, clean scan, checksum, content signature and bounded image decode; the original remains the stored source.
- Image bytes are read and decoded before the command takes occurrence, presentation and draft locks. The locked transaction rechecks completed-upload metadata, and repeated handles are decoded once per request.
- Added parse-only HTTPS YouTube/Vimeo URL handling. The backend stores a provider and video ID and never resolves or fetches the supplied URL.
- Added a provider-neutral SVG drafter port, deterministic local fake and review lifecycle. The fake produces four paths classified for manual authoring. Runtime composition sets the drafter to `None`; tests inject the fake after app creation, and production requests fail closed with `PROVIDER_UNAVAILABLE`. Sanitization readiness, schema validation, rendering, provenance, license allowlisting and the 20-per-24-hour local cap are applied before persistence. The port requires a finite timeout and maps typed provider unavailability to 503. No Billing quota table is used.
- Added migration `20261126_sl_0001` with provisional parent `20261125_nt_0003`, immutable-row triggers, bounded JSONB checks and the `PRESENTATION_IMAGE` upload-purpose check. Re-linking is deferred to the approved squash step.
- Added nine route operations, five bounded request paths, OpenAPI catalog entries, ORM mirrors, receipt-race handling and audit events. The E1 DDL graph test is relative to this migration's parent; shared graph and catalog pin reconciliation is deferred to the Phase E squash.
- Added domain, DDL, port and route-contract tests. Synthetic PostgreSQL tests now cover receipt PK-race rollback counts, stale READY and repin, superseding READY, image purpose/scope/checksum/cache/image serving, catalog visibility and staleness, SVG draft decisions/attachment/cap race, archived or suspended writes, downgrade refusal and immutability triggers. Integration coverage uses the existing disposable test harness and contains no real child data.

## Safety and limits

- New presentation tables and receipts store no child, roster, profile or drawing references. Slide and alt text remain Teacher-provided free text and are not scanned for names (OPEN-5).
- Image safety beyond type, size, signature, malware-scan state and decode bounds remains a Teacher review at READY (OPEN-6).
- AI generation is a local injected fake in tests only. No provider or network call was made.
- PLAN_ACTIVITIES seeding applies the existing 200-character title and 2,000-character description caps by truncating the copied text; the source plan remains unchanged.
- Combined-worktree route, catalog and migration graph count pins remain for the Phase E squash reconciliation; no E3-only absolute values were added to E1's graph test.
- No database, Docker, Alembic command, PostgreSQL client, test runner or protected port was used.
- No plan, status, approval or TASK_APPROVAL record was edited. No stage, stash, commit, push or branch switch was performed.
- The migration parent is provisional. The final chain re-link remains part of the separately approved squash workflow.

## Verification record

- Source and allowlisted-file review: performed manually.
- Ruff and mypy: NOT VERIFIED; neither command/module is available in the current Python environment. Targeted line-length scan found no remaining E501 lines in the reviewed E1 files.
- Unit tests: NOT VERIFIED; not run.
- Contract tests: NOT VERIFIED; not run.
- Synthetic PostgreSQL tests: NOT VERIFIED; not run.
- Repository security validator: NOT RUN; no commit or push was requested.
