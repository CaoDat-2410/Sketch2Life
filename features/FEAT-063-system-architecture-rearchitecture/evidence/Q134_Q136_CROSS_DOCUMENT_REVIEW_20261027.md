# EV-063-10 - Q134-Q136 integration and static cross-document review

Date: 2026-10-27
Feature: FEAT-063
Scope: Documentation-only reconciliation after owner answers Q134-Q136 and the SRS v1.6 review. This evidence does not authorize implementation.

## Decisions applied

- Q134: A run's mutable current owner and active-run uniqueness field are distinct from immutable creator provenance. `DRAFT` participates in adult-wait closeout; closeout releases the current-owner lock at 168 hours. Teacher reassignment uses a durable BE1/Story transfer. Emergency organization-admin force-close is explicit, reasoned, metadata-only and audited; it grants no media access and does not release accepted quota or a successful sample claim.
- Q135: Add `core.upload_sessions` and `core.upload_parts`. Each application chunk is at most 4 MiB and stored as a separate object by `PutObject`; backend validation checks part continuity and hashes, assembles within bounded resources, then writes the final asset with one `PutObject`. The S3 Multipart Upload API is not used. Counts are 42 new, 93 active and 128 physical including 35 read-only legacy tables.
- Q136: At 144 hours, create one in-app reminder and attempt push best-effort; also attempt email only if the current Parent/Teacher owner has a verified email. Inbox remains authoritative and delivery failure does not change run state.

## Static document checks

- SRS v1.7 and `DATA_TABLE_REGISTER.md` both state 51 retained/refactored + 42 new = 93 active; 93 + 35 legacy = 128 physical. Five test fixtures remain excluded.
- The register contains logical dictionary entries for 42 new target tables, including both Core upload entities.
- SRS FR/NFR traceability has eight columns, including priority; BR traceability has six columns. Every BR-01 through BR-41 is represented once. FR/NFR IDs are checked against their catalogues.
- The upload design keeps session/part receipts out of `core_asset_metadata`; rate limits separate control, chunk and status requests; MinIO SDK behavior remains a synthetic POC gate.
- Proposed ADR-0021, CONTEXT, DECISIONS, plan, approval and STATUS record the same Q134-Q136 decisions and current table counts. D-68 is marked superseded by D-71.
- `TASK_APPROVAL.md` points to plan revision 16 and its current SHA-256. The plan remains documentation-only and waits for owner review of both Markdown baselines.

## Execution boundary

Only static Markdown inspection and consistency checks were used. No product tests/builds, code changes, database, provider, Modal, payment, migration, benchmark, deployment or real-child data were used. No final diagram or PDF was created.
