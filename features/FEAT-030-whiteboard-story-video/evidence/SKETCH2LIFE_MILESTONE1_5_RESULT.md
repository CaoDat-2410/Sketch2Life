# Sketch2Life — Milestone 1.5 result (2026-10-09)

## Verdict

**PARTIAL overall; bounded local Milestone-1.5 validation PASS.** Two synthetic drawings exercise the same V2 world/registry/planner/still composer with PNG and JPEG. No real adult approval, actual upload, LightningAI run, animation or full V2 video exists. No inference, GPU, paid API, commit, push or deploy was used.

Baseline before edits: branch `codex/feat-018-contract-plan`, HEAD `c80ef1f6b6d7d33da54eb26a9ad036283aa381fb`. Milestone-1 files were already modified/untracked. Pre-existing user edits to `whiteboard_stroke_extraction.py`, `test_whiteboard_mvp_renderer.py`, `test_whiteboard_stroke_extraction.py`, and `assets/` were not touched. Revision-9 plan and approval were recorded before code edits.

## Actual fixes and changed files

| File | Milestone-1.5 change |
|---|---|
| `backend/src/sketch2life/application/services/story_world_model.py` | Bind each manual mask to its reviewed digest; absent/changed digest -> `NEEDS_MASK_REVIEW` |
| `backend/src/sketch2life/application/services/story_video_pipeline.py` | Explicit `approval_verification=UNVERIFIED_PROTOTYPE` result marker |
| `backend/src/sketch2life/application/ports/story_world_v2_ports.py` | Future-only approval, segmentation, storage, strokes, motion and new-asset interfaces |
| `tools/story_world_v2_fixture.py` | Family fixture A now supplies mask digests |
| `tools/story_world_v2_ocean_fixture.py` | Independent ocean fixture B, source PNG/JPEG and contact-sheet generator |
| `backend/tests/unit/test_story_world_v2_multidrawing.py` | Multi-drawing, codec, pixel, continuity, mask, approval, asset, action and flag tests |
| `features/FEAT-030-whiteboard-story-video/plan/PLAN.md`, `approvals/TASK_APPROVAL.md` | Scope/owner approval before implementation |
| `features/FEAT-030-whiteboard-story-video/CONTEXT.md`, `DECISIONS.md`, `status/STATUS.md`, `evidence/README.md` | Review records and evidence index |
| `features/FEAT-030-whiteboard-story-video/evidence/SKETCH2LIFE_MILESTONE1_5_RESULT.md` | This report |
| `features/FEAT-030-whiteboard-story-video/evidence/milestone1_5-fixture-a-family-contact-sheet.png`, `milestone1_5-fixture-b-ocean-png-contact-sheet.png`, `milestone1_5-fixture-b-ocean-jpeg-contact-sheet.png` | Separate two-scene still contact sheets |

The V2 world schema, planner and composer are reused, not replaced. No V1 route, Gate A/B evaluator, provider or media renderer was edited in this milestone. **Caller-supplied** mask bytes and digest still cannot authenticate who reviewed identity; the new comparison catches accidental substitution only. A wrongly hand-labelled mask could still pass.

## Fixture and error evidence

Fixture A is a 600×360 synthetic family/house/garden PNG with 6 source IDs. Fixture B is an independent 480×320 synthetic ocean drawing (2 fish, turtle, kelp, coral) with 5 source IDs, exported as PNG and JPEG. Both use four explicitly reviewed-fixture text/event segments of 10 seconds, the same registry, planner and composer, continuous state IDs, and first-two-scene stills that differ. Tests compare every masked cutout pixel to the **decoded** source pixel including its color and alpha. JPEG preservation means exact decoded JPEG pixels, not pre-compression pixels; the cutout is lossless PNG thereafter. Test verifies object IDs and source/mask/asset SHA-256 hashes.

Both ocean codecs test missing, wrong-size, non-binary, overlapping, duplicate-identity and swapped masks -> `NEEDS_MASK_REVIEW`; missing/tampered cutout -> `SOURCE_ASSET_MISMATCH`; unapproved event -> `NEEDS_APPROVAL`; unknown action -> `UNSUPPORTED_ACTION`; default-OFF flag -> `V2_DISABLED`. Existing V2 tests also check quote/fact mismatch, stale script hash and flag-ON `.run()` still using V1. No silent V1 fallback or finished-video claim.

- [Fixture A family contact sheet](milestone1_5-fixture-a-family-contact-sheet.png)
- [Fixture B ocean PNG contact sheet](milestone1_5-fixture-b-ocean-png-contact-sheet.png)
- [Fixture B ocean JPEG contact sheet](milestone1_5-fixture-b-ocean-jpeg-contact-sheet.png)

These are simple synthetic stills, **not** the requested whiteboard aesthetic or animation.

## Actual checks

| Check | Result |
|---|---|
| Focused V2 + related V1 unit/contract (command below) | **85 passed, 0 failed**, 55.08 s |
| Broad backend unit/contract with 4 Vision V3 groups excluded (command below) | **1,690 passed, 5 skipped, 86 deselected, 0 failed**, 176.00 s |
| Ruff on 11 V2/fixture/test Python files | `All checks passed!` |
| Mypy on 7 V2/V1 source files | `Success: no issues found` |
| Mypy on ocean fixture separately | `Success: no issues found` with `--disable-error-code import-untyped`; editable local package lacks `py.typed` when checked standalone. An initial mixed tools+tests invocation failed due duplicate module discovery and was rerun separately. |
| Repository security | `REPOSITORY_SECURITY_VALID`, 1,628 publishable files scanned |
| Compatibility/whitespace | `git diff --check` exit 0; `story_render_v2_enabled=False`; no V2 HTTP route; V1 focused tests pass |

```text
backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_story_world_v2.py backend/tests/unit/test_story_world_v2_multidrawing.py backend/tests/unit/test_story_video_planner.py backend/tests/unit/test_story_video_media_smoke.py backend/tests/unit/test_story_video_demo.py backend/tests/unit/test_story_video_job_input_gate.py backend/tests/contract/test_story_video_file_api.py
backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit backend/tests/contract -k 'not vision_v3_quality_fixtures and not vision_v3_mapping_fixtures and not vision_v3_quality_benchmark and not vision_v3_quality_execution'
```

The 86 deselected tests are in four Vision V3 fixture/mapping/benchmark/execution name groups. The prior Milestone-1 unfiltered attempt had **9 failures** due missing `features/FEAT-003-multimodal-understanding/fixtures/vision-v3-quality/images/v3q-fixture-01.png`; `Test-Path` remained `False` here. They were not fixed or rerun unfiltered. Five other tests were skipped by pytest. **Do not report all repository tests PASS.**

## Gate A/B and future approval contract

`StoryVideoJobService.create_or_replay` admits **V1** only after live session snapshot, server-stored Gate A/B evidence, session-owned source artifact and package/script hashes. Gate B approves an experience spec, not exact story events. Direct V2 `run_v2_prototype` does not invoke the job service; its event `review_ref` and source `identity_review_ref` are caller strings, not proof of adult approval. Structural event links to segment, approved fact/confirmed anchor IDs and exact quote are checked; `NEEDS_APPROVAL` blocks. No V2 HTTP endpoint was opened.

Future `ServerApprovalVerificationPort` must retrieve a **server-owned immutable** review record, not accept one as caller JSON, bound to active session/version, package hash, exact script hash, source hash, every event ID and per-object reviewed mask digest, reviewer identity, record digest and revocation status. The existing Gate A/B source/spec/anchor evidence and a separate exact adult script/content review must also be required. `ServerApprovalSnapshotV2` is a design contract only; no verifier implementation or authorization claim exists.

## Milestone-2 interfaces only; Lightning readiness

`SourceObjectSegmentationPort` proposes masks for review; `DurableAssetStoragePort` persists byte-verified session-scoped assets; `ObjectAwareStrokePort` describes per-object drawing/color reveal; `SceneMotionTransitionPort` describes supported action/transition execution; `ApprovedNewAssetGenerationPort` proposes candidates after approval. None is implemented. Current `SourceAssetRegistry` keeps byte arrays behind `memory:` refs; they are not restart-safe or Lightning-ready. A new PNG/JPEG with no manual mask fails `NEEDS_MASK_REVIEW`. There is no automatic identity discovery, mask correction UI, durable retention/privacy policy, object-aware pen stroke, articulated action, synchronization, scene transition, audio assembly or V2 MP4.

Before real upload-to-V2: server-verified adult event/mask approval, permitted real drawings, reliable reviewed masks across art types, durable hashed storage/access control, reviewed new-object flow, motion/stroke engines, V2 media/job route and separate LightningAI real-runtime fidelity/continuity/video acceptance. **Stop for Architect/owner review; do not start Milestone 2.**
