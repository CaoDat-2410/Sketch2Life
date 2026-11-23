# FEAT-083 — AI backend port under Phase A

## Goal

Port the AI backend pieces of CaoDat's branch `origin/codex/parent-modal-e2e-20261123` (commit `77635688`) into the backend integration line without duplicating or breaking goal v4 Phase A.

## Why

The source branch adds Modal workloads (Qwen3.8-FP8, LTX worker), a Modal client, an SVG guide engine and catalog, and Parent topic suggestions. The same commit also contains its own activity-selection and video-generation designs that duplicate Phase A routes and tables and collide with Phase A migrations. The owner decided that Phase A wins and the AI part is plugged in beneath it.

## Product authority

Only the FEAT-063 canonical working SRS named in `docs/context/SRS_AUTHORITY.md` at the base commit. SRS Rev70–Rev73 on the source branch is not adopted here.

## Source check

A read-only check of the source branch was done on 2026-11-23 (local note `tmp/ai-parent-modal-check/AI_PARENT_MODAL_CHECK_20261123.md`, not committed). Main findings: route and migration collisions with Phase A, 13 merge conflicts, the `parent_svg_guide` layering violation, and committed `.pytest-*` directories with absolute-path symlinks.

## Boundaries

See `plan/PLAN.md`. No mobile, no SRS, no activity-selection or video-candidate port, no real provider calls.

## Related

- FEAT-063 (SRS authority, Phase A backend), FEAT-081 (Parent mobile), FEAT-082 (source branch's Qwen3.8 story-quality feature; not present on this line).

## Implementation in progress (2026-11-23)

Scoped source files have been copied, but integration is incomplete. The existing
sketch-guide route remains unchanged because the acceptance criteria restrict route
changes to added SVG catalog and topic routes, while the imported SVG API tests
expect that existing route to be replaced. The builder injection, OpenAPI catalog,
and full comparison checks remain open. Do not treat this work as ready to merge.

## Amendment 1 continuation

Amendment 1 approval and plan SHA-256 F9354BEFF35D1A34A70C5457C5846007ECCDD905DC78323D18562B4DBF073D80 were verified. The previous route-scope question is resolved. The sketch-guide route, composition-root builders, topic gate, OpenAPI catalogue, and migration head/count tests were updated. The implementation remains incomplete because the imported story and activity worker contracts introduce integration regressions; see the continuation evidence.

## Amendments 2 and 3 (2026-11-23)

The Modal Story v1 and Parent activity contracts and model pin are restored. Topic-subject workers and independent visual-plan/image-guide modules remain additive. The owner approved the two narrowly scoped existing test updates listed in `evidence/AMENDMENT_3_20261123.md`. Full backend comparison is in progress; the local environment lacks `cairosvg`, `lmformatenforcer` and `imageio`.

## Closeout (2026-11-23)

The Amendment 3 implementation and reviewer comparison are complete with environment limitations. The final type-check comparison found no new real type errors; the only new normal-mode mypy finding is the unavailable `cairosvg` import in the Modal image-guide helper. No `cairosvg` import/reference exists under `backend/src`. See `evidence/notes/FINAL_REPORT_20261123.md` for the final file manifest, exact existing test edits, verification counts, and outstanding checks. The task is `COMPLETE_WITH_LIMITATIONS`.
