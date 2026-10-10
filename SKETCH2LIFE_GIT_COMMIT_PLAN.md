# Sketch2Life — Git Change Review & Commit Plan

Date: 2026-10-09 (Asia/Ho_Chi_Minh). This is the original pre-commit plan/snapshot; its counts and HEAD below describe that time, not the post-approval Git state. Owner subsequently approved the four local commit groups and chose to keep all 15 Milestone 2 pilot exports outside Git. Execution details and actual SHAs belong in `SKETCH2LIFE_GIT_COMMIT_RESULT.md`.

## 1. Git snapshot and provenance

- Repository: the current `Sketch2Life` Git root. The separate local audit/review export directory is **not** this Git repository and is excluded from this plan.
- Branch: `codex/feat-018-contract-plan`; HEAD: `c80ef1f6b6d7d33da54eb26a9ad036283aa381fb`; upstream `origin/codex/feat-018-contract-plan`, currently `+0/-0`. Do not infer who updated the remote since the earlier M1 snapshot.
- Before creating this plan: **13 tracked modified, 41 untracked, 0 staged**, 54 paths total. After creating this report: 42 untracked / 55 total. No deleted/renamed files in `git status`.
- V2 core files were produced across M1 plus small M1.5 hardening; ocean validation files in M1.5; stroke engine/renderer files in M2. All are AI-created in this task sequence and remain **uncommitted**. FEAT-030 governance/docs additions for revisions 8–10 are also AI-authored on top of pre-existing tracked documents.
- Three tracked V1 edits were already present **before M1**: `backend/src/sketch2life/infrastructure/media/whiteboard_stroke_extraction.py`, `backend/tests/unit/test_whiteboard_mvp_renderer.py`, `backend/tests/unit/test_whiteboard_stroke_extraction.py`. Their exact author/approval cannot be established from current Git status; treat as user-owned and keep out of these commits. Do not overwrite or reset them.
- Four untracked `assets/generated/whiteboard-hand-marker-v{1,2}.{png,provenance.md}` existed before M1. Their provenance describes Codex-generated visual drafts, **not approved** for renderer use or Git inclusion. They are AI-generated but not M1–M2 deliverables and remain excluded.
- Fifteen files under `evidence/milestone2-pilots/` are AI-generated experimental outputs from M2. They are not production assets. MP4s are small (about 20–43 KB each), but size alone is not approval to commit temporary media. Keep all fifteen out pending explicit artifact-policy choice.

## 2. Proposed commit order (conditional; no staging yet)

### Commit 1 — V2 world/state prototype core

Message: `feat(story-video): add gated V2 world registry and scene-state prototype`

Exact files (**10**):

1. `backend/src/sketch2life/contracts/schemas/story_world_v2.py`
2. `backend/src/sketch2life/application/services/story_world_errors.py`
3. `backend/src/sketch2life/application/services/story_world_model.py`
4. `backend/src/sketch2life/application/services/story_video_planner.py`
5. `backend/src/sketch2life/infrastructure/media/scene_state_composer.py`
6. `backend/src/sketch2life/application/services/story_video_pipeline.py`
7. `backend/src/sketch2life/infrastructure/config/settings.py`
8. `backend/src/sketch2life/interfaces/http/app.py`
9. `tools/story_world_v2_fixture.py`
10. `backend/tests/unit/test_story_world_v2.py`

Rationale: schema/error/registry/planner/composer and the explicit default-OFF integration must land together so no intermediate commit has unresolved imports. Fixture A and its tests are included so this commit is reviewable and testable. The current registry already includes M1.5 mask-digest hardening; it is intentionally kept with its dependent fixture/test rather than surgically split into a fragile hunk. V1 `.run()` remains V1.

Current-worktree check: `pytest ... test_story_world_v2.py test_story_video_planner.py` → **37 passed**. Before commit, re-run after staging only these paths, check flag OFF and V1 job/contract tests. The current 37-pass result does **not** prove an isolated staged tree yet.

### Commit 2 — independent second drawing and codec validation

Message: `test(story-video): validate V2 continuity across family and ocean drawings`

Exact files (**2**):

1. `tools/story_world_v2_ocean_fixture.py`
2. `backend/tests/unit/test_story_world_v2_multidrawing.py`

Depends on Commit 1's family fixture and V2 contracts. Current-worktree check: `pytest ... test_story_world_v2_multidrawing.py` → **20 passed**. PNG/JPEG, IDs, source pixels, mask failure paths and two-scene continuity are exercised. Repeat after the staged diff is reviewed.

### Commit 3 — isolated experimental V2 drawing pilot

Message: `feat(story-video): add offline source-pixel drawing pilot behind V2 boundary`

Exact files (**7**):

1. `backend/src/sketch2life/contracts/schemas/story_strokes_v2.py`
2. `backend/src/sketch2life/application/ports/story_world_v2_ports.py`
3. `backend/src/sketch2life/application/services/story_draw_schedule_v2.py`
4. `backend/src/sketch2life/infrastructure/media/object_stroke_engine_v2.py`
5. `backend/src/sketch2life/infrastructure/media/whiteboard_renderer_v2.py`
6. `tools/story_whiteboard_v2_pilot.py`
7. `backend/tests/unit/test_whiteboard_v2_engine.py`

Depends on Commits 1–2: the pilot CLI imports both fixtures, and the extractor uses the V2 registry. The port was drafted in M1.5, then its `ObjectAwareStrokePort` signature was adapted to the implemented M2 extractor; commit its **current coherent version** here, not half of the file in Commit 2. Current-worktree check: `pytest ... test_whiteboard_v2_engine.py` → **9 passed**; A/B/JPEG pilots decoded, with final raw frames matching the canonical composer target. **Visual QA failed**; this commit must be explicitly described as experimental, not a product-quality renderer. Do not commit if another task is still editing any of these seven files—confirm ownership and recheck diff/hashes immediately before staging.

### Commit 4 — governance, reports and small review images (artifact choice approved)

Message: `docs(story-video): record V2 milestone evidence and acceptance limits`

Proposed files (**14**, including this plan):

1. `features/FEAT-030-whiteboard-story-video/CONTEXT.md`
2. `features/FEAT-030-whiteboard-story-video/DECISIONS.md`
3. `features/FEAT-030-whiteboard-story-video/approvals/TASK_APPROVAL.md`
4. `features/FEAT-030-whiteboard-story-video/evidence/README.md`
5. `features/FEAT-030-whiteboard-story-video/plan/PLAN.md`
6. `features/FEAT-030-whiteboard-story-video/status/STATUS.md`
7. `features/FEAT-030-whiteboard-story-video/evidence/SKETCH2LIFE_MILESTONE1_RESULT.md`
8. `features/FEAT-030-whiteboard-story-video/evidence/SKETCH2LIFE_MILESTONE1_5_RESULT.md`
9. `features/FEAT-030-whiteboard-story-video/evidence/SKETCH2LIFE_MILESTONE2_RESULT.md`
10. `features/FEAT-030-whiteboard-story-video/evidence/milestone1-v2-contact-sheet.png`
11. `features/FEAT-030-whiteboard-story-video/evidence/milestone1_5-fixture-a-family-contact-sheet.png`
12. `features/FEAT-030-whiteboard-story-video/evidence/milestone1_5-fixture-b-ocean-png-contact-sheet.png`
13. `features/FEAT-030-whiteboard-story-video/evidence/milestone1_5-fixture-b-ocean-jpeg-contact-sheet.png`
14. `SKETCH2LIFE_GIT_COMMIT_PLAN.md`

These are text review records plus four small PNG contact sheets. The owner selected the outside-Git policy for all fifteen Milestone 2 pilot files. Before Commit 4, revise the M2 report to remove broken artifact links while retaining filenames/metrics; create and verify an external SHA-256 backup without deleting originals. Do not stage the pilot folder. Review the four proposed M1/M1.5 PNGs for privacy/size before inclusion. The reports must continue to say M2 `VISUAL_QA_NOT_PASSED` and Lightning not tested. Documentation tests: link/path review, `git diff --check`, repository security validator; no runtime claim from docs alone.

## 3. Explicit hold/exclusion inventory

The following **22 pre-plan paths** stay uncommitted in this plan:

**Pre-existing V1 worktree edits (3):**

- `backend/src/sketch2life/infrastructure/media/whiteboard_stroke_extraction.py`
- `backend/tests/unit/test_whiteboard_mvp_renderer.py`
- `backend/tests/unit/test_whiteboard_stroke_extraction.py`

**Unapproved hand drafts (4):**

- `assets/generated/whiteboard-hand-marker-v1.png`
- `assets/generated/whiteboard-hand-marker-v1.provenance.md`
- `assets/generated/whiteboard-hand-marker-v2.png`
- `assets/generated/whiteboard-hand-marker-v2.provenance.md`

**Experimental M2 exports (15):**

- `features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots/family-draw-schedule.json`
- `features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots/family-metrics.json`
- `features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots/family-strokes.json`
- `features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots/family-v2-0-25-50-75-100.png`
- `features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots/family-v2-pilot.mp4`
- `features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots/ocean-jpeg-draw-schedule.json`
- `features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots/ocean-jpeg-metrics.json`
- `features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots/ocean-jpeg-strokes.json`
- `features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots/ocean-jpeg-v2-0-25-50-75-100.png`
- `features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots/ocean-jpeg-v2-pilot.mp4`
- `features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots/ocean-png-draw-schedule.json`
- `features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots/ocean-png-metrics.json`
- `features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots/ocean-png-strokes.json`
- `features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots/ocean-png-v2-0-25-50-75-100.png`
- `features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots/ocean-png-v2-pilot.mp4`

No `.env`, credentials, real child media or approved visual assets were identified in the proposed candidate lists. That is a scoped inspection, not a guarantee about future files. After adding this plan, the repo-security validator returned `REPOSITORY_SECURITY_VALID` (1,651 publishable files scanned) and `git diff --check` passed on the current worktree. `story_render_v2_enabled` is still `False` in settings/pipeline, and no V2 HTTP upload route appears in the inspected story-video router.

## 4. Test evidence and pre-commit gates

- Current combined post-M2 evidence: focused V1/V2 group **101 passed**; broad `backend/tests/unit backend/tests/contract` with four missing-fixture Vision V3 groups excluded **1,699 passed, 5 skipped, 86 deselected**. The previous unfiltered M1 attempt had nine Vision V3 failures due missing `features/FEAT-003-multimodal-understanding/fixtures/vision-v3-quality/images/v3q-fixture-01.png`; do **not** call the entire repository green. Ruff/Mypy/security passed in the M2 review. None of these tests proves visual acceptance or a real Lightning run.
- This planning turn's scoped read-only checks: core + V1 planner **37 passed**; ocean multi-drawing **20 passed**; experimental engine **9 passed**. These ran against the **combined dirty worktree**, not isolated commit trees.
- After explicit owner approval, for *each* commit: recheck branch/HEAD/status and absence of concurrent edits; stage **only** the exact listed paths (never `git add .` / `git add -A`); inspect `git diff --cached --name-status`, `git diff --cached --check` and full staged diff; verify no held file/secret/media slipped in; run its focused tests plus V1 regression/contract tests appropriate to imports; commit locally only if green. For Commit 3 also decode MP4 in a temp/output directory and retain the `VISUAL_QA_NOT_PASSED` label. For Commit 4 first resolve the artifact-link blocker and run security validation again. Do not amend, rebase or reset existing commits.
- Recheck `SKETCH2LIFE_STORY_RENDER_V2_ENABLED` defaults OFF and existing V1 `.run()` remains the production path. A code commit is **not** authorization to expose V2 in HTTP, run paid inference, push, merge or deploy.

## 5. Owner decisions (resolved after this plan)

1. Approve or change the four commit boundaries/messages above.
2. Choose M2 artifact policy for documentation: recommended keep all fifteen pilot exports local/untracked and adjust the report links; or explicitly approve a named minimal subset to commit. No artifact will be staged by default.
3. Confirm no concurrent task is still changing M2 engine files when local commit work begins. The three pre-existing V1 edits and four hand drafts remain untouched unless separately requested/approved.

**Historical stop point:** this plan originally awaited review/approval; the owner later authorized four local commits, subject to per-commit gates. This plan does not itself record their outcome.
