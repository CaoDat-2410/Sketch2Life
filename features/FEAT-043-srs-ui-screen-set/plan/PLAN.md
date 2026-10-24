# SRS-based Child, Teacher and Admin UI images

- Status: APPROVED
- Plan revision: 1
- Implementation status: DONE
- Date: 2026-10-10, Asia/Saigon

## Goal

Deliver separate, coherent UI mockup images for all34 SRSv3.1 screen responsibilities in three role folders, with9 essential supplementary states (43images total), matching current Sketch2Life styling and current scope.

## Scope

Child C01–C10 plus C03b/C04b/C07b; Teacher T01–T14 plus adult loginT00 and T07b/T09b/T09c; Admin A01–A10 plus adult loginA00 and partial deletionA08b. Sources B14/B19/B20/B23/B24 and current mobile theme. UX details remain proposals. Only generated raster design artifacts, documentation and provenance; no runtime implementation, tech-stack lock, visual approval promotion or Git publication requested.

## Steps

1. Read source register/context/SRS/governance and audit three role screen catalogs independently.
2. Record this plan and direct task approval before image production; keep original pending code untouched.
3. Prepare inventory, shared style and exact per-screen Vietnamese prompts. Generate one built-in imagegen output per screen/state, copy unchanged PNG into assets/generated/{child-app,teacher-app,admin-app}.
4. Inspect each output for legibility, one-screen composition, required actions/state guards and product consistency; revise concrete defects without overwriting approved art.
5. Record prompts, references, generator/time/output SHA/dimensions and review status in feature-local manifests; verify43 unique outputs covering34main IDs.
6. Deliver folder links plus a local gallery and coverage/provenance report; leave visual review pending and runtime assets unchanged.

## Acceptance criteria

- AC01: 34main SRS screen IDs covered exactly once across Child10/Teacher14/Admin10.
- AC02: nine named additional variants delivered; each screen/state is its own PNG, not a collage.
- AC03: current palette/design family, Vietnamese labels, Android tablet Child and desktop Teacher/Admin layouts consistent.
- AC04: consent/admission/turn, per-Sketch review, video waiting/failure choice, recovery/attribution, scoped administration/privacy/retention match SRS; no removed legacy scope features.
- AC05: every PNG has source/prompt/tool/time/hash/dimensions/provenance and reviewer QA; REVIEW_PENDING until actual visual approval.
- AC06: images in three role folders; browsable gallery and manifest; original eight pending runtime files and canonical SRS unchanged.

## Risks and verification

Generated typography may drift; inspect actual PNGs and revise material text/action defects. Samples synthetic only; no real QR/token or child data. UX/advanced tool/provider policies not frozen by pictures. Read-only dimensions/hash/coverage validator and repository harness/security at completion; no runtime test or device acceptance claims.

## Evidence

Feature-local artifacts/SCREEN_INVENTORY.json and DESIGN_SYSTEM.md; assets/prompts and manifests; evidence/notes/visual QA and metrics/coverage. Preserve built-in originals by unchanged copying. No generated image is referenced by app code.

## Completion checkpoint

43 selected PNGs delivered: Child13, Teacher18, Admin12; all34 main SRS IDs plus9 supplementary states. Local gallery, offline-gallery ZIP, complete prompt history and per-image manifests are generated. Final delivery checks verify distinct hashes, source preservation and unchanged pending runtime files. Scope/revision/acceptance remain as approved; only implementation status and this completion checkpoint were added after approval. Visual review remains REVIEW_PENDING.
