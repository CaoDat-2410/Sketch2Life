# FEAT-020 Semantic Activity Remediation Decisions

**Status:** APPROVED FOR IMPLEMENTATION — VALIDATED

**Date:** 2026-09-13

These decisions were provided by the project owner after reviewing the semantic
activity remediation plan. They update the plan scope; they do not by themselves
authorize implementation.

## DEC-020-09 — Hybrid curated semantic eligibility

The system will use a hybrid semantic engine. A reviewed concept graph,
activity-anchor profile and deterministic hard-rule validator define eligibility.
AI/embedding assistance may normalize observations, suggest concepts and rank
already eligible candidates, but it may not invent activity IDs or bypass catalog,
age, readiness, prerequisite, material, supervision or safety rules.

## DEC-020-10 — Safe fallback with bounded AI suggestions

Each age band must have a reviewed safe fallback tier. When an exact or alias
match is unavailable, the workflow may select a fallback only when its explicit
profile and all hard rules pass. AI may suggest fallback candidates, but the
selection remains deterministic, auditable and visible as SAFE_FALLBACK, never as
an exact match.

## DEC-020-11 — Full 100-activity catalog scope

The remediation covers the full planned 100-activity catalog, including activity
content, semantic profiles, progression, materials, safety, duration, fallback
coverage, review evidence and validation. The current 20 activities are the
migration pilot; the remaining 80 are not eligible until they pass the same
validators.

## DEC-020-12 — Test-only partial age matrix

The backend test/demo matrix may return PARTIAL_SUCCESS when some requested age
bands are ready and others are unavailable. The result must explicitly list ready
and unavailable bands with terminal statuses and blocking reasons. This policy is
test/demo-only; a future real child session remains fail-closed for its selected
age band.
## Implementation approval

The project owner approved implementation of this remediation in the current task on 2026-09-13. The implementation must remain within this feature scope: no UI, no runtime PixiJS generation, no video generation, no fixture substitution, and no production relaxation of fail-closed age-band behavior.