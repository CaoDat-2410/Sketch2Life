# FEAT-084 fix and verification — 2026-11-24

## Fix

`ParentApi` now normalizes drawing-subject exclusions with trim and whitespace collapse, drops values outside 2–80 Unicode code points, then keeps the last 24. The caller no longer applies an earlier 24-value window. This follows the FEAT-083 `exclude_subjects` rule in `parent_topic_suggestions.py` and prevents 81–120 character `guide_subject` values from causing a 422. No backend change was made.

New tests in `parentApiI2Contract.test.ts`:

- `normalizes drawing-subject exclusions and sends only backend-supported lengths`
- `applies the 24-item drawing-subject exclusion window after filtering`

## FEAT-083 contract audit

Read-only sources: `backend/src/sketch2life/interfaces/http/routers/parent_topic_suggestions.py`, `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`, `backend/src/sketch2life/contracts/schemas/parent_topic_suggestions.py`, and `backend/src/sketch2life/contracts/schemas/svg_engine.py`.

- `GET /topics/suggestions`: `draft_id` is a UUID; `exclude_set_ids` is capped at 16 and uses `pts_` set IDs. Mobile sends the matching query names and caps the exclusion window at 16.
- `GET /topics/{topic_id}/drawing-subject-suggestions`: `topic_id` is 2–48 lowercase slug characters; `draft_id` is a UUID; `topic` is 2–120 characters; `exclude_set_ids` is capped at 16; `exclude_subjects` is capped at 24, with each normalized value 2–80 characters. The overlength/raw-whitespace mismatch was the only request mismatch found and is fixed.
- `POST /topics/custom-subject-validation`: mobile sends `topic_id`, `topic`, and `subject`; the Pydantic request bounds are 2–48, 2–120, and 2–120 respectively. Field names and response fields match.
- `POST /ai/sketch-guides`: mobile sends the versioned contract, `topic`, optional trimmed `intended_subject`, and `difficulty: beginner`. FEAT-083 accepts topic length 2–120, intended subject length 2–160, and difficulty `beginner` or `simple`. The source-draft response fields, literals, and nullability match the mobile type and runtime guide check.

The topic-set, subject-set, custom-validation, and SVG source-draft response types match the Pydantic wire fields. No other request or response wire-shape mismatch was found. The API relies on FEAT-083 for validation of direct invalid IDs/text; normal callers use generated UUIDs, server-issued set IDs/topic slugs, and 120-character UI fields.

## Verification

- Vitest: **20 files / 241 tests passed**. The previous FEAT-084 baseline was 18 files / 228 tests; the pre-fix AIPORT2 run was 20 / 239.
- UI copy: **UI_COPY_AND_RECOVERY_VALID**.
- Typecheck: **111 existing errors**, all under `packages/art-renderer` due to unavailable `zod`; **0 outside** that package, matching the baseline record.
- Harness, repository security, architecture, and `git diff --check`: **passed**.
- No network install or baseline worktree was used. Temporary dependency junctions were removed; both dependency targets remained present with their original top-level entry counts.

## Scope and verdict

Changed files are within `apps/ui-mobile` and `features/FEAT-084-ai-mobile-port`. No web, billing, backend, or Modal file changed. No approval, plan, or SRS file changed. No files outside the approved scope changed.

**Verdict: PASS WITH NOTES.** Typecheck retains the 111 recorded baseline errors under `packages/art-renderer`; there are zero errors outside it. Safe to commit as one commit on top of `06c8490d`, subject to the owner’s decision. No commit or push was made.
