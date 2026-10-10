# Butterfly refinement — Revision 24

Status: CANDIDATE_READY_FOR_REVIEW. Concept only approved; final artwork, paths and duration remain pending. VISUAL_QA_NOT_PASSED. No MP4, TTS, inference, remote upload or production changes.

## Artwork and paths

One locally authored candidate, native 256 x 184 RGBA, slightly asymmetric curved orange/cyan wings, antialiased at 4x and procedural paper/pencil texture. Palette is source-derived; butterfly pixels are NEW_LOCAL_AUTHORED_PENCIL_ART_NOT_SOURCE_OBJECT_OR_AI, not recovered source pixels. Original image, master masks and earlier assets are unchanged.

| Phase | Paths | Standard duration estimate |
| --- | ---: | ---: |
| OUTLINE | 7 | 2.849 s |
| DETAIL | 9 | 2.255 s |
| COLOR | 5 | 9.172 s |
| Total including pen travel | 21 | 14.277 s |

Five closed outlines cover four wings/body; two open outlines cover antennae. Details contain curved wing markings. Coloring follows component contour/inward spiral trajectories with opposite winding directions, not horizontal scan rows. Spatial brush masks clip each path to its component, preserving candidate pigment/texture; no global opacity fade or whole-region reveal. Ink is separate from pigment, so OUTLINE does not expose color.

20 pen lifts; zero zero-length paths. Standard placement: 77 x 55 source pixels; smaller: 56 x 40 at the same garden center. Smaller estimate: 11.399 s. Pacing uses existing 24 FPS, ink 180 px/s, color 300 px/s, pen-up 600 px/s, minimum 4 down/2 up frames. These are path estimates, not observed natural drawing or measured narration. Butterfly alone nearly fills 15 s; the full family slice remains infeasible under previously measured unsimplified paths. No speed/quality thresholds were relaxed.

Initial candidate-v2 output left 33 antialias fringe pigment pixels uncovered. A perimeter brush traversal was added to each same component COLOR path before inward coloring. Final review output covers 20,251/20,251 pigment pixels (100%); completed RGBA exactly equals candidate, without a final-frame replacement. Initial output is retained.

## Review artifacts outside Git

Directory: D:/Codex/Sketch2Life/butterfly_refinement_2026-10-09/review-final/

- [Candidate](D:/Codex/Sketch2Life/butterfly_refinement_2026-10-09/review-final/butterfly-candidate-preview.png)
- [Old versus refined](D:/Codex/Sketch2Life/butterfly_refinement_2026-10-09/review-final/original-candidate-vs-refined.png)
- [Two placement sizes](D:/Codex/Sketch2Life/butterfly_refinement_2026-10-09/review-final/placement-size-comparison.png)
- [Timed clean stages](D:/Codex/Sketch2Life/butterfly_refinement_2026-10-09/review-final/progress-0-25-50-75-100-clean.png)
- [Stages with actual traveled path and tip](D:/Codex/Sketch2Life/butterfly_refinement_2026-10-09/review-final/progress-0-25-50-75-100-pen-paths.png)
- [Phase paths](D:/Codex/Sketch2Life/butterfly_refinement_2026-10-09/review-final/draw-path-contact-sheet.png)
- candidate-paths.json: full path points, component and phase identities.
- pen-timeline-standard.json / pen-timeline-smaller.json: travel and down/up timings.
- progress-tip-traces.json: sampled tip state and geometry.
- outline/detail/color-phase-mask.png: phase coverage.
- candidate-manifest-and-diagnostics.json: provenance, recipe, metrics and SHA-256.
- artifact-sha256.json: original generation outputs; final handoff manifest additionally covers later debug sheet.

0/25/50/75/100% means elapsed estimated timeline, NOT pixel coverage. Debug annotations are not part of clean artwork. New candidate PNG SHA-256: c70031dadfc17b7ca8aa85254e29ae689da8d25869ac7b12787be1c93698ef4b.

## Actual validation

From repository root:

```text
backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_butterfly_candidate_refinement.py backend/tests/unit/test_whiteboard_slice_feasibility.py backend/tests/unit/test_whiteboard_mvp_renderer.py backend/tests/unit/test_whiteboard_stroke_extraction.py
72 passed in 19.10s
backend/.venv/Scripts/python.exe -m ruff check tools/refine_butterfly_candidate.py backend/tests/unit/test_butterfly_candidate_refinement.py
All checks passed!
MYPYPATH=backend/src backend/.venv/Scripts/python.exe -m mypy --follow-imports=silent tools/refine_butterfly_candidate.py
Success: no issues found in 1 source file
backend/.venv/Scripts/python.exe tools/validate_repository_security.py
REPOSITORY_SECURITY_VALID; publishable_files_scanned=1679 (final post-documentation scan)
git diff --check: PASS
```

Includes 17 new candidate tests, existing path feasibility and selected V1 renderer/extraction tests. First selected run was 71 PASS/1 FAIL due a floating-point exact-bound assertion; assertion fixed with 1e-9 arithmetic tolerance, not a drawing quality/pacing change. Final run has no skips/deselections. Full repository, Vision V3, LightningAI, audio and moving-video Visual QA were not run. Mypy scope is one tool with local backend import resolution, not repository-wide type acceptance.

Before/after HEAD: 93668ffdaa7f2890fe9498596c670006a87eba4a, branch codex/feat-018-contract-plan; index empty. All 330 preexisting Python files byte-unchanged. Source/manifest SHA unchanged; all nine mask digests rechecked with zero failures. V1 remains default; story_render_v2_enabled remains False. No existing engine or rig implementation was edited. Private final-handoff-verification.json includes SHA-256 entries for all 35 review-final files, including the additional pen-path debug sheet.

## Files changed in this task

- tools/refine_butterfly_candidate.py: isolated local candidate, phase masks, paths, timed spatial brush previews and diagnostics.
- backend/tests/unit/test_butterfly_candidate_refinement.py: candidate/path/coverage/pen/immutability tests.
- features/FEAT-030-whiteboard-story-video/approvals/TASK_APPROVAL.md: concept-only scope.
- features/FEAT-030-whiteboard-story-video/plan/PLAN.md: bounded execution record.
- features/FEAT-030-whiteboard-story-video/CONTEXT.md: current state.
- features/FEAT-030-whiteboard-story-video/DECISIONS.md: review gate and measured limits.
- features/FEAT-030-whiteboard-story-video/status/STATUS.md: result and stop.
- features/FEAT-030-whiteboard-story-video/evidence/README.md: evidence index.
- features/FEAT-030-whiteboard-story-video/evidence/SKETCH2LIFE_BUTTERFLY_REFINEMENT_RESULT.md: this report.

Existing unrelated worktree edits remain owned by earlier tasks/user and were not reset, staged or committed.

## Limitations and next gate

Static inspection supports smoother silhouette and separate ink/color phases, not VideoScribe-equivalent natural animation. Contour spirals can still look mechanically regular; temporary inner white gaps are expected during coloring. Pencil grain and vein clarity at smaller size need owner review. Coverage/final fidelity do not prove visually pleasing temporal brush motion. No butterfly movement was implemented.

Owner must approve artwork, size, paths and duration before slice rendering. Full-scene source stroke fragmentation and timing remain separate blockers; this task does not resolve them. Stop here; no Golden Story, rig changes, production endpoint, commit, push or deploy.
