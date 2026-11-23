# FEAT-083 decisions

## D-083-01 — Phase A wins over the source branch (2026-11-23)

Where the source branch and the integration line implement the same behaviour (Parent activity selection, `POST /v1/story-runs/{id}/video-generations`, the `ck_story_receipt_operation` change), the integration line's Phase A design stays. The AI part is ported beneath it. Consequence: the source branch's activity-suggestion/selection tables and routes and its video-candidate route are not ported.

## D-083-02 — Scope limited to four AI pieces (2026-11-23)

Port only Modal workloads, the Modal client with story contracts, the SVG engine and catalog, and Parent topic suggestions. Mobile screens, registration completion, SRS Rev70–Rev73 and source-branch evidence are separate decisions.

## D-083-03 — Feature id (2026-11-23)

The source branch already uses FEAT-082 for its Qwen3.8 story-quality work. This port uses FEAT-083 to avoid an id collision on the integration line.

## Open

- OPEN-1: owner decision on SRS Rev70–Rev73 and the records pinned to the current SRS hash.
- OPEN-2: how the AI-generated activity set and the LTX worker attach to the Phase A routes (follow-up task).
- OPEN-3: online PostgreSQL migration check needs a password-free access path to the `frc08` container.

## D-083-04 � Tentative migration parent (2026-11-23)

The ported SVG migration currently follows `20261123_rv_0001`, the current
Phase A Story chain head. Alembic reports 15 down-only heads and 10
resolution-aware heads after this change. Online migration validation remains
NOT RUN; the choice is provisional until the complete port is verified.

## D-083-05 - Replace the legacy sketch-guides route (2026-11-23)

The legacy AI route `POST /api/parent/v1/ai/sketch-guides` is replaced by the catalog-first SVG guide route from the source commit. It is not a Phase A route, and the imported SVG API tests require the replacement. The request/response contract changes and an unknown topic returns 404 (no AI fallback); the mobile client is adapted in the follow-up mobile task. Recorded in plan Amendment 1 and approval Amendment 1.

## D-083-06 - Narrow the Modal scope (2026-11-23)

The wholesale Modal port changed the existing Parent activity worker contract and the Story v1 worker input, which broke contract tests that pass on the integration line. Only additive Modal changes are ported; the Qwen3.8 story/activity move, the v3 story input and ADR-0024 are deferred (follows OPEN-2). Recorded in plan Amendment 2 and approval Amendment 2.

## D-083-07 - Allow minimal test edits for the replaced route (2026-11-23)

The two existing tests that assert the legacy `sketch-guides` behaviour (route surface, provider gate) are updated to the approved catalog-first behaviour, and only those assertions. Recorded in plan Amendment 3 and approval Amendment 3.

## D-083-05 � Additive Modal scope and sketch-guide test update (2026-11-23)

Amendment 2 retains the integration line's Story v1 and Parent activity worker contracts and model pin. The topic-subject workers are added using that existing model; story image-guide and visual-plan modules are retained independently. The Qwen3.8 story/activity change, the v3 input and ADR-0024 remain deferred. Amendment 3 permits only the two existing route-surface and provider-gate test updates identified in the feature evidence. The user-visible sketch-guide route remains catalog-first as approved by Amendment 1.

## Closeout note (2026-11-23)

No product-scope or owner decisions changed during closeout. The Amendment 3 plan hash remains B1D2AF0BE53DC56927E15F27FE77CDC3EB41A30772A4FF640BB4848F9861CCBB. Verification limits and the completed file/test inventory are recorded in evidence/notes/FINAL_REPORT_20261123.md; online PostgreSQL validation and dependency-blocked CairoSVG/Modal checks remain open limitations.
