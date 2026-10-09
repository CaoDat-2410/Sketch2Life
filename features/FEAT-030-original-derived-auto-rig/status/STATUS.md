# FEAT-030 status

Status: IN_PROGRESS
Updated: 2026-10-08

## Local sprite-cycle runtime preview — 2026-10-02

- Enabled `motion.walker-avian.v1` and `motion.walker-corgi.v2` in the explicit, default-off local/test preview catalog after exact provenance/hash and alpha-cycle QA. `motion.flyer-songbird.v2` remains blocked by excessive centroid drift; the other candidates did not pass the current conservative preview screen.
- Added the server-side local/test gate and kept production manifest rights/runtime flags unchanged. Found the existing Pixi show planner was disabled, so restarted the local backend with that planner enabled; image-flow use will invoke the configured AI planner, while readiness checks did not submit images. Metro now resolves the mobile app as root and the pnpm-linked shared renderer; backend health and Android bundle both returned HTTP 200.
- Verification: 22 focused backend tests, Ruff, 57 renderer tests, renderer typecheck/demo build, and mobile UI check passed. Full Android image-to-Pixi visible animation was not run; device playback acceptance is still pending.
- Evidence: `../../FEAT-028-pixi-topic-asset-library/evidence/notes/MOTION_CYCLE_LOCAL_PREVIEW_ACTIVATION_20261002.md`. No commit/push performed.

- The approved revision-4 SAM2.1 worker and integrated quality workstream are implemented locally;
  multimask candidates are bounded and filtered by existing prompt/area constraints.
- Synthetic metric/selector benchmark is reproducible independently of pytest. Its analytic masks
  are not human-reviewed drawings and do not establish SAM accuracy. The current constructed run
  improves region/boundary metrics but loses thin detail unless the feature is explicitly anchored.
- Full backend suite: 1,650 passed, 10 skipped. Local BE/Metro/emulator connectivity is verified,
  but no fresh visual playback with live SAM was performed.
- Still pending: reviewed held-out references, owner/reviewer-approved quality thresholds, L4 latency
  and VRAM with Qwen resident, Android visual acceptance, and the existing model ADR gate. Live SAM
  activation remains disabled/gated.
- Evidence: `evidence/notes/SAM21_BENCHMARK_RUNABILITY_20260930.md`.
- Pixi follow-up: the repeated `MASK_BACKGROUND_RECONSTRUCTION_FAILED` was isolated from successful
  HTTP 200 artifact reads to local paper-donor reconstruction. Added same-image credible-paper
  seeding for dense outlines, strictly within the verified mask. Renderer suite 49, typecheck/build,
  and mobile typecheck/UI-copy validation pass; rebuilt page/bundle return HTTP 200. Fresh Android
  visual acceptance remains pending. See `evidence/notes/PIXI_MASK_BACKGROUND_RECONSTRUCTION_FIX_FOLLOWUP_20260930.md`.

- SAM 2.1 prompt/refinement follow-up plan revision 1 is owner-approved and implementation is in
  locally implemented. It reuses current multimask selection, adds target-grounded point prompts,
  connected-component/boundary tie-breaks, and one bounded mask-input refinement for at most one
  subject plus one eligible part per source image. No fine-tuning or model call has been run.
  Held-out quality review, L4 latency/VRAM measurement, and Android visual acceptance remain open.
  See
  `plan/SAM21_PROMPT_REFINEMENT_FOLLOWUP_20260930.md` and
  `evidence/notes/SAM21_PROMPT_REFINEMENT_BASELINE_20260930.md` and
  `evidence/notes/SAM21_PROMPT_REFINEMENT_IMPLEMENTATION_20260930.md`.

## Approved Pixi sprite show plan — implementation in progress (2026-10-01)

- Revision 4 of `plan/PIXI_SPRITE_SHOW_AND_AI_MOTION_MATCHING_20261001.md` records all four owner
  choices: visual beats only (narration/captions deferred), companion characters allowed, a bounded
  image/crop permitted in the one post-Gate-B planner call, and visible typed failure with no
  automatic retry or substitute show. It retains gap-driven sprite coverage across supported
  behavior classes and the owner's visual approval of 144 frames; rights clearance/runtime remain
  pending.
- Plan revision 4 was explicitly approved; the exact pre-approval hash, branch and scope are recorded
  in `approvals/TASK_APPROVAL.md`. Implementation is authorized on `codex/pixi-ai-show-20261001`.
  FEAT-028 rights/runtime eligibility and live provider/Android gates remain separate constraints.

- Offline implementation is in place on `codex/pixi-ai-show-20261001`: additive versioned show
  contracts, one bounded post-Gate-B planner adapter (disabled by default), deterministic validator/
  compiler, capability-bound sprite reads, and mobile-to-Pixi V3 bridge. V1/V2 contracts remain
  unchanged; failures are visible and preserve the original with no automatic retry/fallback.
- Image-processing part proposals require visible connected-color evidence inside the verified
  subject mask; uniform silhouettes return no parts. Full backend suite reached 100%; workspace
  typecheck/tests/build and focused Ruff passed. See
  `evidence/notes/PIXI_SHOW_IMPLEMENTATION_20261001.md`.
- Additive planning update: the owner visually approved all 28 frames in seven FEAT-028 motion
  concept sheets on 2026-10-01; this is not rights, crop/pivot, catalog, or runtime approval. A
  subject-family/behavior-class registry addendum now includes required motion-sprite coverage for
  every supported non-static behavior and is APPROVED FOR IMPLEMENTATION at
  `plan/PIXIJ_SUBJECT_BEHAVIOR_CLASS_REGISTRY_REV5_DRAFT_20261001.md`. Owner confirmed full current
  taxonomy coverage plus a reviewed extension path, multiple capabilities selected per beat, and
  plants/environment/effect motion, and one or more reusable cycles per compatible behavior class
  with variants where needed. Approved revision 4 remains unchanged. At approval time implementation
  had not started; current progress is recorded below.
- Exact pre-approval revision-5 plan SHA-256 and post-approval hash are recorded in
  `approvals/TASK_APPROVAL.md`.

## Subject/behavior registry and motion-cycle coverage — implementation in progress (2026-10-01)

- Implemented an isolated domain registry with 29 behavior classes, separate semantic family / rig
  archetype / action primitive fields, multi-capability topic profiles, static/unknown outcomes, and
  deterministic compatibility/readiness checks. All 144 current FEAT-028 catalog topic IDs map to a
  reviewed profile; morphology corrections distinguish mollusks, insects, aquatic mammals, and
  flying reptiles. People now carry character-motion capabilities instead of being mislabeled static.
- Every behavior class has at least one cycle ID. The FEAT-028 provenance manifest covers all 37
  four-pose cycles (seven previously visually approved sheets plus 30 newly generated sheets).
  The new 30-sheet batch is awaiting owner visual review. Nothing was added to the asset catalog or
  runtime; every behavior remains runtime-ineligible pending rights, crop/pivot/loop QA, catalog,
  renderer, and contract/provider gates.
- Validation: focused registry tests (7 passed), Ruff, formatting, PNG dimensions/RGBA and asset
  hashes pass. The focused tests also prove exact catalog-topic coverage, class-to-cycle provenance,
  closed unknown handling, and that no behavior is runtime-selectable.
- No live AI/provider request, Android run, contract mutation, asset promotion, or commit/push was
  performed. Evidence: `evidence/notes/BEHAVIOR_REGISTRY_IMPLEMENTATION_20261001.md`.
- FEAT-028 gap audit found only static one-pose catalog frames. Seven four-pose motion sheets have
  visual approval for all 28 frames; the additional 30 four-pose sheets remain pending owner visual
  review. None is crop/pivot/loop-verified, catalogued, rights-cleared, or runtime-referenced.
  Existing 144 catalog visual approvals and the 28 approved motion frames do not clear rights.
- Still gated: caregiver subject-reconfirmation round-trip, motion-frame technical/provenance and rights
  for new sprite drafts, external-provider privacy/retention, live Qwen single-call validation,
  Lightning L4 latency/VRAM, and fresh Android playback. No live model request or Android run was
  performed. Runtime planner remains disabled.

## Sprite-cycle Pixi integration — offline implementation verified (2026-10-02)

- Owner visually approved the 30-sheet/120-frame expansion; all 37 cycle sheets now have visual
  approval. Hash-matched copies are in FEAT-028 `assets/approved/`; generated originals are preserved.
- Added additive Python envelope V2 / renderer command V4 cycle contracts and capability-bound PNG
  frame reads; the Pixi demo selects frames from the existing playback clock, with bounded placement,
  safe cycle logs, and cleanup on failures. V1/V2/V3 contracts remain unchanged.
- Independent rights, crop/pivot/loop QA, catalog, formal renderer, and runtime gates remain closed.
  The demo build/tests do not establish cleared rights or Android acceptance; no live cycle can play.
- Verification: complete backend suite passed; workspace tests passed (57 renderer + 7 mobile tests),
  workspace typecheck passed; `apps/ui-mobile` bridge/context TypeScript check also passed. Renderer
  demo build passed, focused Ruff passed. Repository security
  validation passed after replacing a local machine path in the related evidence note. See
  `evidence/notes/SPRITE_CYCLE_PIXI_INTEGRATION_20261002.md`.
- Global harness validation remains blocked by missing evidence subdirectories in FEAT-026, FEAT-033,
  and FEAT-034; FEAT-028 and FEAT-030 have no missing harness paths. These out-of-scope feature paths
  were left untouched.

## FEAT-035 integration follow-up — 2026-10-03

- Added the additive subject-only Pixi V3 path so an empty rights-cleared companion shortlist no
  longer invalidates an otherwise valid subject show. Essential subject/rig checks and the sprite
  cycle/read gates remain intact; no PIXI_V2 downgrade or asset promotion was introduced.
- Full backend tests and focused Pixi regressions pass; this establishes contract/service behavior,
  not a successful live drawing or Android visual acceptance. See
  `../../FEAT-035-branch-review-remediation/evidence/notes/implementation-progress-20261003.md`.

## Adaptive original-art rendering — implementation in progress — 2026-10-08

- Owner choices recorded: attempt both background extraction and part separation; prefer full rig when masks validate; otherwise use a verified subject cutout in a scene matching the child's selected topic; let AI choose among supported strategies; reuse the existing single post-Gate-B planner call.
- Review found that the current planner chooses behavior/assets/beats but does not return an explicit renderer strategy or scene-theme choice. Candidate descriptors are text-only, so style-fit assessment needs bounded candidate previews or an equivalent reviewed visual signal.
- Additive plan: `plan/PIXI_ADAPTIVE_ART_AND_TOPIC_SCENE_20261008.md`, revision 1, approved against pre-approval SHA-256 `FC634C8899AB4B4FC618AF8311BDBD9C7391CC0C952C2F24AF60EC33D12428EF`; owner approval recorded 2026-10-08 22:20 Asia/Saigon. Offline implementation and focused verification are complete; external acceptance gates remain open. No live-provider request or asset promotion is included.
- Existing FEAT-028 rights/runtime, FEAT-030 provider/privacy/L4, and Android visual acceptance gates remain closed.

## Adaptive original-art rendering — local implementation — 2026-10-08

- Implemented the additive planner strategy/theme contract and bounded ephemeral candidate previews in the existing single post-Gate-B request. The planner can choose only a validated full rig, a verified cutout with a topic scene, cutout micro-motion, or static source, with backend-allowlisted asset IDs.
- Reused the verified source-cutout/background reconstruction path. Pixi now loads an eligible scene theme behind the drawing and freezes subject translation for `STATIC_SOURCE`; the original remains the lead image.
- Added regression coverage for incomplete part-mask coverage: masks covering only part of the verified subject are rejected before a full rig is emitted. Clean part-mask, same-color silhouette, cutout, contract, planner, and renderer cases are also covered with synthetic data.
- Local checks: the combined focused planner/catalog/worker/settings/auto-rig/part-mask backend suite passed (108); Ruff, renderer typecheck, renderer Vitest (67), and mobile typecheck passed.
- The full backend suite had one unrelated FEAT-020 semantic-personalization test failure involving the repository's current age-band policy; five tests were skipped. No change was made to that workstream.
- No live provider request, real child image, asset promotion, production activation, or Android visual acceptance occurred. FEAT-028 rights/runtime, privacy/retention, L4/ADR, and Android acceptance gates remain open.
- Detailed record: `evidence/notes/ADAPTIVE_ART_AND_TOPIC_SCENE_IMPLEMENTATION_20261008.md`.

## Pixi planner timeout and invalid output — 2026-10-09

- Approved follow-up plan: `plan/PIXI_SHOW_TIMEOUT_AND_OUTPUT_VALIDITY_FIX_20261009.md` (revision 1; plan hash and owner approval are recorded in `approvals/TASK_APPROVAL.md`).
- Evidence received: UI surfaced `REQUEST_TIMEOUT`; Lightning later logged `/v4/pixi/show-plan` as `MODEL_OUTPUT_INVALID` with HTTP 502.
- Local implementation is complete within the approved scope. Python source compilation and `git diff --check` passed; tests and live model inference were not run. Feature-local evidence: `evidence/notes/PIXI_SHOW_TIMEOUT_AND_OUTPUT_VALIDITY_FIX_20261009.md`.
- Deployment and live acceptance remain outstanding: update the Lightning checkout, restart Uvicorn, then inspect the next synthetic-image attempt for the new stage-specific failure code or a successful show plan.

## Pixi schema-invalid prompt follow-up — 2026-10-09

- Runtime evidence: owner confirmed commit `c74831e` was pulled and Uvicorn restarted; `/v4/pixi/show-plan` still returned HTTP 502 with `MODEL_SCHEMA_INVALID`.
- Source review found a prompt contradiction: the model was told to provide allowlisted asset IDs and later told not to output any asset IDs. The follow-up plan was approved by the owner request to check and fix this 502.
- Local implementation is complete: removed that contradiction, made ID array/null shapes explicit, and added sanitized bounded schema field/type diagnostics. `py_compile` and `git diff --check` passed; tests and live inference were not run.
- New runtime acceptance requires deploying this patch, restarting Uvicorn, and confirming a successful plan or a safe `schema_issues` field path in the next synthetic request.

## Pixi root-validator failure follow-up — 2026-10-09

- Runtime evidence after `b3a7798`: HTTP 502 with `MODEL_SCHEMA_INVALID schema_issues=root:value_error`.
- Local fix clarifies the final still interval and selected-ID uniqueness; logs map known root validator messages to fixed reason codes without logging those messages. Python compilation and `git diff --check` passed; tests and live inference were not run.
- Runtime acceptance requires deployment of this commit and one synthetic-image request. Unknown root failures remain safely classified without content.
