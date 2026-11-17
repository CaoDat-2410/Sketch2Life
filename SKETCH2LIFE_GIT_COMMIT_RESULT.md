# Sketch2Life — Git commit result

Date: 2026-10-09 (Asia/Ho_Chi_Minh). Repository: the current `Sketch2Life` checkout. Branch: `codex/feat-018-contract-plan`. Initial HEAD: `c80ef1f6b6d7d33da54eb26a9ad036283aa381fb`. Four **local** commits were created; no push, merge, deploy, paid inference, feature expansion, or Milestone 3 work was performed. This result file is deliberately **untracked**: it needs the actual fourth SHA and a fifth commit was not authorized.

## Commits and exact file inventory

1. `9bd25f0d71ffcc45ac1d1b84964396144da8ad35` — `feat(story-video): add gated V2 world registry and scene-state prototype` (10 files):
   - `backend/src/sketch2life/contracts/schemas/story_world_v2.py`
   - `backend/src/sketch2life/application/services/story_world_errors.py`
   - `backend/src/sketch2life/application/services/story_world_model.py`
   - `backend/src/sketch2life/application/services/story_video_planner.py`
   - `backend/src/sketch2life/infrastructure/media/scene_state_composer.py`
   - `backend/src/sketch2life/application/services/story_video_pipeline.py`
   - `backend/src/sketch2life/infrastructure/config/settings.py`
   - `backend/src/sketch2life/interfaces/http/app.py`
   - `tools/story_world_v2_fixture.py`
   - `backend/tests/unit/test_story_world_v2.py`
2. `923af91daeb9cdd6b0af13c14a6758868339f7ca` — `test(story-video): validate V2 continuity across family and ocean drawings` (2 files):
   - `tools/story_world_v2_ocean_fixture.py`
   - `backend/tests/unit/test_story_world_v2_multidrawing.py`
3. `61182d3c8a556528ead12f6decf9c9e34159add2` — `feat(story-video): add offline source-pixel drawing pilot behind V2 boundary` (7 files):
   - `backend/src/sketch2life/contracts/schemas/story_strokes_v2.py`
   - `backend/src/sketch2life/application/ports/story_world_v2_ports.py`
   - `backend/src/sketch2life/application/services/story_draw_schedule_v2.py`
   - `backend/src/sketch2life/infrastructure/media/object_stroke_engine_v2.py`
   - `backend/src/sketch2life/infrastructure/media/whiteboard_renderer_v2.py`
   - `tools/story_whiteboard_v2_pilot.py`
   - `backend/tests/unit/test_whiteboard_v2_engine.py`

   Commit body explicitly records: `EXPERIMENTAL`, `VISUAL_QA_NOT_PASSED`, no approved full-story V2 video, HTTP endpoint, or LightningAI runtime acceptance.

4. `93668ffdaa7f2890fe9498596c670006a87eba4a` — `docs(story-video): record V2 milestone evidence and acceptance limits` (14 files):
   - `SKETCH2LIFE_GIT_COMMIT_PLAN.md`
   - `features/FEAT-030-whiteboard-story-video/CONTEXT.md`
   - `features/FEAT-030-whiteboard-story-video/DECISIONS.md`
   - `features/FEAT-030-whiteboard-story-video/approvals/TASK_APPROVAL.md`
   - `features/FEAT-030-whiteboard-story-video/evidence/README.md`
   - `features/FEAT-030-whiteboard-story-video/evidence/SKETCH2LIFE_MILESTONE1_RESULT.md`
   - `features/FEAT-030-whiteboard-story-video/evidence/SKETCH2LIFE_MILESTONE1_5_RESULT.md`
   - `features/FEAT-030-whiteboard-story-video/evidence/SKETCH2LIFE_MILESTONE2_RESULT.md`
   - `features/FEAT-030-whiteboard-story-video/evidence/milestone1-v2-contact-sheet.png`
   - `features/FEAT-030-whiteboard-story-video/evidence/milestone1_5-fixture-a-family-contact-sheet.png`
   - `features/FEAT-030-whiteboard-story-video/evidence/milestone1_5-fixture-b-ocean-png-contact-sheet.png`
   - `features/FEAT-030-whiteboard-story-video/evidence/milestone1_5-fixture-b-ocean-jpeg-contact-sheet.png`
   - `features/FEAT-030-whiteboard-story-video/plan/PLAN.md`
   - `features/FEAT-030-whiteboard-story-video/status/STATUS.md`

## Checks immediately before each commit

| Commit | Test command and observed result | Staged diff gate |
|---|---|---|
| 1 | `backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_story_world_v2.py backend/tests/unit/test_story_video_planner.py backend/tests/unit/test_whiteboard_mvp_renderer.py backend/tests/unit/test_whiteboard_stroke_extraction.py backend/tests/contract/test_story_video_file_api.py` → **72 passed**, 0 failed, 74.15 s | Exactly 10 approved paths, 1009 insertions/3 deletions; full text diff reviewed; `git diff --cached --check` clean. |
| 2 | `backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_story_world_v2_multidrawing.py backend/tests/unit/test_story_video_planner.py backend/tests/contract/test_story_video_file_api.py` → **48 passed**, 0 failed, 55.13 s | Exactly 2 approved paths, 321 insertions; full text diff reviewed; whitespace check clean. |
| 3 | `backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_whiteboard_v2_engine.py backend/tests/unit/test_story_video_planner.py backend/tests/unit/test_whiteboard_mvp_renderer.py backend/tests/unit/test_whiteboard_stroke_extraction.py backend/tests/contract/test_story_video_file_api.py` → **69 passed**, 0 failed, 74.83 s. The engine tests decode synthetic pilot MP4s; no real/Lightning video was run. | Exactly 7 approved paths, 866 insertions; full text diff reviewed; whitespace check clean. Commit body preserves experimental/failed-QA labels. |
| 4 | `backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_story_world_v2.py::test_v2_feature_flag_off_does_not_call_any_provider backend/tests/unit/test_story_world_v2.py::test_flag_on_does_not_silently_replace_v1_run backend/tests/unit/test_story_video_planner.py backend/tests/contract/test_story_video_file_api.py` → **30 passed**, 0 failed, 53.70 s. Repository security: `REPOSITORY_SECURITY_VALID`, 1,651 publishable files scanned. | Exactly 14 approved paths, 521 text insertions and 4 small PNGs; full text diff and all 4 images reviewed; whitespace check clean. Three Markdown relative links checked, zero broken. |

All commands ran against the working tree containing later untracked V2 files, not a detached export of each staged tree. Import/diff inspection found no dependency from Commit 1 into later groups; Commit 2 depends on 1, and Commit 3 depends on 1–2. HEAD, branch, index and relevant path status were rechecked before each stage/commit; the approved staged files did not drift during their test runs. No conflicting editor change was observed. This does **not** prove that no other task existed, because no cross-task ownership API was available. No file outside the exact approved list was staged. `git add .`, `git add -A`, amend, rebase and reset were not used.

## Artifact policy, links and security

- The 15 original pilot files remain untracked at `features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots/` and were not deleted or modified. Copies are at `D:/Codex/Sketch2Life/milestone2_artifact_backup_2026-10-09/`, outside this Git repository. `SHA256_MANIFEST.md` there lists every filename, byte count and SHA-256. Independent verification: **15 entries, 0 source/backup hash mismatches**. The backup directory contains 16 files including the manifest.
- The Milestone 2 report's six broken relative links to excluded MP4/contact sheets were replaced by plain filenames plus the external backup/manifest location and reproduction command. Metrics (family/ocean MAE etc.), `VISUAL_QA_NOT_PASSED`, `SOURCE_IMAGE_FIDELITY_PARTIAL`, `LIGHTNINGAI_NOT_TESTED`, and `FULL_STORY_VIDEO_NOT_IMPLEMENTED` were retained. Three remaining relative links in the staged review Markdown were checked and exist (the Milestone 1.5 contact sheets).
- All four committed contact sheets were visually inspected: generated synthetic family/ocean art only, no real child image or private content visible. Sizes: 5,053; 5,053; 6,555; and 33,172 bytes. The repository security validator passed before Commit 4. No `.env`, credential, approved/private user asset, or large MP4 was staged.

## V1/V2 state and remaining files

- `Settings.story_render_v2_enabled` and `StoryVideoPipeline(... story_render_v2_enabled=...)` both default to `False`; the explicit V2 prototype rejects calls with `V2_DISABLED` when OFF. Tests verify V1 `.run()` is still the V1 path even if the flag is ON. The existing app passes the flag into pipeline construction but exposes no V2 HTTP upload route. No feature flag was enabled by these commits.
- Final HEAD: `93668ffdaa7f2890fe9498596c670006a87eba4a`; branch is **ahead 4** of `origin/codex/feat-018-contract-plan`. Index is empty. The only tracked worktree modifications are the three preserved pre-existing V1 files:
  - `backend/src/sketch2life/infrastructure/media/whiteboard_stroke_extraction.py`
  - `backend/tests/unit/test_whiteboard_mvp_renderer.py`
  - `backend/tests/unit/test_whiteboard_stroke_extraction.py`
- The four unapproved hand-asset drafts are still untracked, unchanged: `assets/generated/whiteboard-hand-marker-v1.png`, `assets/generated/whiteboard-hand-marker-v1.provenance.md`, `assets/generated/whiteboard-hand-marker-v2.png`, `assets/generated/whiteboard-hand-marker-v2.provenance.md`.
- The 15 untracked pilot originals are, for each prefix `family`, `ocean-png`, `ocean-jpeg`: `<prefix>-draw-schedule.json`, `<prefix>-metrics.json`, `<prefix>-strokes.json`, `<prefix>-v2-0-25-50-75-100.png`, `<prefix>-v2-pilot.mp4`, all under `features/FEAT-030-whiteboard-story-video/evidence/milestone2-pilots/`.
- This `SKETCH2LIFE_GIT_COMMIT_RESULT.md` is one additional untracked file by design. Thus the post-report worktree has 3 modified tracked + 20 preserved untracked artifacts/drafts + 1 new untracked report; no staged changes. The original 22 held files remain uncommitted.

## Open blockers / limits

- V2 visual QA is **not passed**: the pilot reveal remains stiff, and background preservation is partial for the ocean fixtures. Do not treat the commits as product-quality whiteboard acceptance.
- No server-verified adult event/mask approval, durable source-asset store, real image upload-to-V2, complete 40–60-second narrated V2 story, or LightningAI runtime acceptance exists.
- The earlier broad unit/contract run excluded 86 Vision V3 tests because fixture images were missing; a prior unfiltered run had nine related failures. This commit task reran focused suites, not the entire repository. Do not report the repository as fully green.
- The external artifact backup is local to this machine and is not shared by cloning Git. Reviewers need access to that directory or must regenerate synthetic pilots from the documented CLI. The local result report remains uncommitted until separately approved.
