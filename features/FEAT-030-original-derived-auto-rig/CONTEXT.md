# FEAT-030 Original-derived auto-rig context

- Status: REVISION_3_PART_AWARE_BASELINE_IMPLEMENTED; REVISION_4_SAM21_WORKER_IMPLEMENTATION_IN_PROGRESS; QWEN_SINGLE_PASS_AND_SAM_PROMPT_FIX_IMPLEMENTED; SAM2_SUCCESS_MASK_HANDOFF_FIX_IMPLEMENTED_LOCALLY; PIXI_STARTUP_BRIDGE_REPLAY_IMPLEMENTED_LOCALLY; NO_AUTOMATIC_V2_TO_V1_FALLBACK_AND_GATE_B_PRELOAD_IMPLEMENTED_LOCALLY; HIGH_PIGMENT_AND_MASK_QUALITY_CHANGES_IMPLEMENTED_OFFLINE; PIXI_SHOW_V1_OFFLINE_BRIDGE_IMPLEMENTED; PIXI_SHOW_RUNTIME_DISABLED; MOTION_SPRITE_VISUAL_APPROVED_RIGHTS_AND_TECHNICAL_REVIEW_PENDING; SUBJECT_BEHAVIOR_REGISTRY_REVISION_5_IN_PROGRESS; ANDROID_VISUAL_RETEST_AND_LIVE_L4_BENCHMARK_PENDING.
- Owner: Project owner; auto-rig revision 4 and Pixi sprite-show plan revision 4 are approved for implementation. Live activation remains gated by separate asset-rights, privacy/retention, L4, contract, and Android evidence.
- Goal: turn a validated subject from the child's immutable drawing into a bounded, explainable PixiJS 2D rig so the drawing visibly moves while remaining recognizably the child's work.
- Scope: target selection, spatial grounding, segmentation, original-derived masks/textures, mesh and skeleton generation, skin weights, rig validation, bounded motion profiles, asynchronous preparation, Renderer V2 loading, PixiJS CPU skinning, deterministic fallback, provenance, metrics, and golden-scene evidence.
- Non-goals: generative redrawing; replacing the original; any extra Qwen inference outside the single bounded post-Gate-B multimodal show-planning request approved by plan revision 4; AI video generation; changing Gate A or Gate B authority; letting the renderer or mobile app call model providers; inventing actions unsupported by the drawing and learning objective; removing Renderer V1 compatibility.
- Dependencies: FEAT-003 canonical understanding, FEAT-004 art player invariants, FEAT-005/018 supervised flow and Gate B, FEAT-028 approved supplemental assets, FEAT-029 master SRS, `docs/governance/FRONTEND_ASSET_GATE.md`, and the repository approval/evidence policies.
- Risks: poor masks on children's drawings, GPU contention with Qwen, long preparation time, bridge payload size, background holes/ghosting, unstable mesh topology, unsafe or semantically invented motion, and derived artifacts being mistaken for approved creative assets.

## Owner brief

The requested direction is an automatic 2D rig pipeline:

`OriginalDrawing + CanonicalUnderstanding + Gate B`

→ target selection → localization → segmentation → mask cleanup → archetype → keypoints/skeleton → mesh → bones → weights → validation → motion profile → `RiggedArtworkPackageV1` → `VisualAnimationPlanV2` → `RendererLoadCommandV2` → PixiJS mesh deformation.

The original drawing remains immutable. Every mask, crop, texture, mesh, rig, and background patch is a derived artifact with a source hash and derivation record. A rigging failure must never fail the supervised session.

## Current product boundary

- Gate A remains the semantic authority for the selected subject and learning direction.
- Gate B remains the authority for the activity/experience to be shown.
- The auto-rig pipeline may derive geometry; it must not independently reinterpret the story or select another subject.
- The mobile app receives only backend-issued launch contracts and short-lived capabilities. Provider credentials and internal endpoints remain backend-only.
- Renderer V1 remains available until V2 quality, latency, stability, and rollback evidence are accepted.

## Source and authority

- Direct owner request and the supplied auto-rig proposal define the desired direction for this feature.
- `feat-029-master-srs`, `sketch2life-workflow`, and accepted feature records are requirement baselines, not implementation approval.
- Exact segmentation, grounding, and geometry libraries remain candidates until an ADR records benchmark evidence. The handbook explicitly does not freeze providers without evaluation.

## Auto-rig implementation revision 4 boundary

The approved implementation now includes the typed SAM 2.1 worker contract, a lazy process-scoped
Lightning runtime, a backend-only adapter, deterministic bounded box proposal, mask provenance,
and safe typed fallback. The SAM2 dependency/checkpoint is not installed or downloaded by the
repository change. Live activation remains opt-in via `SKETCH2LIFE_LIGHTNING_SAM21_ENABLED=true`
until the L4 benchmark and deployment ADR evidence are recorded.

## Owner closure — 2026-09-25

- Spatial grounding and segmentation may begin after Gate A to hide latency. Gate B is still required before the final motion/experience plan is compiled or presented.
- Coverage must address the full range of children's drawing topics. This means all initially identified archetype families plus deterministic `generic_organic`, `rigid`, and `unknown` handling; it does not permit fabricated semantics or guarantee a bespoke skeleton for every possible object.
- Auto-rig may run as a separate worker/service on the same Lightning L4 host. Because Qwen currently lazy-loads when used, implementation must measure combined VRAM and coordinate GPU work rather than assuming both models can run concurrently without limits.
- Lightning `/v2/vision` keeps bounded repair disabled by default so one live request performs at most one Qwen inference; repair remains an explicit benchmark opt-in through `SKETCH2LIFE_LIGHTNING_VISION_BOUNDED_REPAIR=true`.
- The same live route enables in-memory structural normalization separately, so common Qwen JSON shape drift is canonicalized without starting a second model attempt.
- Lightning runtime logging is explicitly INFO-level so typed vision outcomes are visible even when the worker returns HTTP 200; greedy generation removes unused sampling fields to avoid misleading Transformers warnings.
- The Lightning worker also emits a sanitized stdout completion line, and the mobile client preserves closed, parent-facing workflow messages instead of collapsing them into a generic image-read error.
- The backend SAM2 adapter now creates a bounded box from clustered colored ink before calling `/v2/rig/segment`; blank or invalid images still fail closed. Pillow is a runtime dependency because prompt extraction occurs in the backend process.
- The 2026-09-27 Lightning evidence confirms Qwen is single-pass and successful while SAM2 returns typed `MODEL_UNAVAILABLE`. The worker now resolves standard checkpoint/config locations from `SAM2_MODEL_DIR` and logs a closed private diagnostic reason without exposing provider details to mobile; live SAM2 activation still requires the private runtime dependency/checkpoint setup.
- The 2026-09-27 SAM2-success runtime fix added a separate short-lived mask capability and verified source/package/mask hashes and dimensions. Its initial subject-cutout path used neutral-corner checks and automatic V1 recovery; the corner gate and V2-to-V1 recovery were superseded by owner-approved D-030-25/D-030-27 on 2026-09-29.
- The 2026-09-28 emulator retest disproved the earlier Pixi-init-stall hypothesis: WebGL/Pixi became ready, but no source/package/mask request followed. The startup bridge now caches one validated launch and replays that exact message after Pixi readiness; renderer-side handling deduplicates it, and native timeout copy distinguishes handshake, Pixi initialization, and post-ready loading. Unit/type/build checks pass. Full post-fix artifact-flow verification is pending because the configured image workflow may invoke live Lightning inference.
- Metadata-only part proposals no longer promote a package to `FULL_AUTO_RIG`; the current package/renderer path does not yet deliver independent part masks to PixiJS.
- The approved 2026-09-28 part-motion restoration is implemented locally and passes focused offline checks. It carries bounded part-mask capabilities and source provenance from SAM2.1 through the renderer command. The worker encodes the image once and attempts role-specific SAM prompts; a rejected part prompt does not discard a valid subject mask. If fewer than two quality-checked model parts survive, deterministic archetype-anchored image processing partitions only pixels already inside the subject mask; unsupported/generic shapes remain lower-tier.
- `FULL_AUTO_RIG` now reaches separate source-derived Pixi sprite textures for every validated part (not rectangular butterfly crops). The whole-subject fallback keeps fixed framing and may only use small translations; V2 zoom/rotation and the post-completion infinite idle were removed. The default plan is 20 seconds, semantic tracks end at 14.4 seconds, and the remaining 5.6 seconds holds neutral.
- Whole-drawing and V2 canvases now use aspect-preserving contain-fit with a 12% margin, avoiding the natural-pixel-scale crop when the renderer enters the original-art fallback. Backend auto-rig logs identify whether validated part masks came from SAM2.1 or image processing, or why a partition was unavailable.
- The 2026-09-29 Android console trace `Renderer V2 package could not start. PART_MASKS_REQUIRED` identified a consumer regression: the WebView fetched subject masks for `CUTOUT_MICRO_MOTION` but then rejected every package that was not `FULL_AUTO_RIG`. The approved follow-up now passes a validated subject-only cutout to the existing Pixi player while keeping independent-mask gates strict for full rigs. Renderer tests (43), typecheck and demo build pass; backend was restarted and serves the rebuilt page/bundle. A fresh owner-run Android flow is still required for visual/live-SAM acceptance; restart cleared the previous in-memory demo session.
- The 2026-09-29 emulator logcat then identified `MASK_BACKGROUND_PATCH_UNSAFE`: four image corners were assumed to be uniform neutral paper. The approved follow-up replaces that gate with verified-mask-bounded inpainting, removes automatic classic/V1 recovery from V2 startup errors, shows preparation progress at Gate A/Gate B/Pixi, pre-prepares the launch after Gate B, and allows 90 seconds after handshake. Renderer tests (43), renderer/UI TypeScript checks, UI-copy validation and demo build pass. Backend health is 200 and the current build serves `mobile-CMtWg0Zp.js` without restart. Android was not force-reloaded and no live model was called; visual playback and separate WebGL texture warnings remain pending owner-flow retest.
- The owner-provided 2026-09-29 playback screenshot shows pale radial patches around a high-pigment butterfly cutout. Initial diagnosis identified possible saturated-color donors and absent mask-boundary metrics, without attributing the issue to SAM alone. The approved integrated follow-up rejects cutouts without credible neutral donors, confines reconstruction to the verified subject mask, and evaluates prompt-consistent candidate selection using synthetic masks. See the implementation record and the 2026-09-30 bounded donor-radius regression below; real drawing/source-mask inspection remains pending.
- Focused offline checks pass for synthetic butterfly, bird, flower, tree, fish and biped partitions, package/capability handoff, renderer part sprite/keyframe/rest behavior, and the legacy fixed-camera fallback. No live Lightning/SAM/Qwen request or Android visual smoke was performed; real-drawing mask quality, background seam quality and L4 latency remain unverified.
- The SAM 2.1 quality audit is implemented as bounded multimask prompt-consistency selection and synthetic metric/benchmark tooling. The benchmark uses generated masks only and does not invoke SAM; measured results are a selector/plumbing comparison, not model accuracy, held-out quality, or L4 performance. See `evidence/notes/INTEGRATED_MASK_AND_CUTOUT_QUALITY_20260929.md`.
- 2026-09-30 follow-up decoupled synthetic archetype masks from the pytest module so the benchmark can run in a NumPy-capable workspace runtime without pytest. The synthetic comparison again shows improved region/boundary metrics but reduced thin-detail recall (0.639); an explicit positive point preserves a grounded thin feature in a bounded candidate test. These are synthetic selector checks only. Full backend suite passes; reviewed drawing references, live SAM/L4 budget and Android visual acceptance remain open. See `evidence/notes/SAM21_BENCHMARK_RUNABILITY_20260930.md`.

## Integrated mask/cutout implementation — 2026-09-29

- Runtime requests the bounded SAM multimask output and selects only candidates consistent with the
  adult/worker prompt geometry, positive/negative points, box and area limits.
- The offline synthetic benchmark covers nine archetypes. Prompt checks reduce false inclusion and
  improve synthetic boundary metrics but reduce thin-detail recall; this trade-off blocks any claim
  of proven real-mask accuracy.
- Renderer donor selection no longer seeds paper reconstruction from saturated crayon pixels;
  absent credible local paper donors yields a typed failure, and pixels outside the verified mask
  remain untouched.
- Targeted runtime/metric tests, 7 cutout tests, and Python lint pass. Android visual retest, real
  SAM/L4 benchmark, mask-to-anatomy reference review and WebGL acceptance remain pending.

## Bounded paper-donor regression — 2026-09-30

A synthetic high-pigment outline reproduced `MASK_BACKGROUND_RECONSTRUCTION_FAILED`: the verified
mask had nearby neutral paper, but the previous five-pixel donor radius could not reach it. The
renderer now searches up to 12 pixels for credible local low-chroma/light paper, still rejects
saturated donors, preserves outside-mask pixels exactly, and still fails closed when no paper donor
exists within the bound. All 48 renderer tests, renderer typecheck/build, and mobile typecheck/copy
checks pass. No model/provider call or user image was used. Android visual/live-SAM retest remains
pending. See [E-030-FIX-013](evidence/notes/PIXI_MASK_BACKGROUND_RECONSTRUCTION_FIX_20260930.md).

The owner then reported the same error again. Sanitized backend logs confirmed renderer page, source,
package and all four masks were served successfully; the failure remained inside Pixi cutout
reconstruction. E-030-FIX-014 supersedes the 12-pixel-only recovery: local donors remain preferred,
with a deterministic estimate from at least eight credible unmasked paper pixels as a same-image
fallback when nearby pixels are all pigment. Inpainting still writes only inside the verified mask,
preserves outside pixels/source bytes, and fails closed if the unmasked image has no credible paper
samples. Renderer tests (49), typecheck/build, mobile typecheck/UI-copy checks pass; backend served
the rebuilt page/bundle with HTTP 200. Fresh Android visual acceptance remains pending because this
shell has no accessible `adb`/Android SDK path. No provider call or image was used in the fix.

## SAM 2.1 prompt-refinement follow-up — 2026-09-30

- A new revision-1 plan was approved by the owner at 2026-09-30 23:17 Asia/Saigon; implementation
  is implemented locally at
  `plan/SAM21_PROMPT_REFINEMENT_FOLLOWUP_20260930.md`.
- Existing multimask output/selection is already implemented. The reviewed gaps are target-grounded
  positive/negative point generation and a bounded use of SAM's iterative mask input; prior
  synthetic selector results also warn that thin-detail recall can fall without explicit anchors.
- The proposal keeps SAM 2.1 and the current checkpoint path, excludes fine-tuning, and caps any
  refinement at two extra predictions per source image. No fine-tuning or model call is included.
- Local implementation now reuses a target-keyed normalized region when present, seeds SAM from
  actual ink/paper evidence, filters part seeds against the accepted subject silhouette, and keeps
  one iterative mask-input pass per subject and first eligible part. Candidate ranking uses SAM's
  score with small prompt-fit, 8-connected-component, and source-boundary tie-breaks. Focused and
  full backend tests, Ruff, and Python compilation pass. Real SAM/L4 quality and Android review are
  still activation gates; see
  `evidence/notes/SAM21_PROMPT_REFINEMENT_IMPLEMENTATION_20260930.md`.

## Pixi sprite show / AI motion matching proposal — 2026-10-01

- The owner requested reviewed sprite reuse, bounded image-processing part separation when SAM lacks
  usable parts, and AI classification/planning that can select from a sprite list and create a
  content-bearing PixiJS show.
- The owner visually approved all 144 existing FEAT-028 catalog v2.0.0 frames on 2026-10-01; exact
  catalog hash and review scope are recorded in FEAT-028 `assets/REVIEW.md`. Rights remain pending,
  so none is runtime-eligible or promoted to approved/applied.
- The current catalog sprites are static single-pose frames, not walk/flight cycles. Any additions
  are gap-driven and need separate per-frame review; no need to expand all 144 by default.
- Code inspection found the existing deterministic part splitter assigns nearest-anchor regions
  with constant `0.7` confidence. The revision-2 plan treats this as an untrusted baseline, not
  anatomical evidence; image-processing proposals must earn acceptance through held-out metrics.
- The proposed AI output is a structured, backend-validated visual show plan using confirmed subject
  and Gate-B experience, verified rig capability, and approved sprite IDs. It is not arbitrary code
  or generated replacement art. The owner resolved the product questions for revision 4: visual
  beats only for now; distinct companion characters permitted; one bounded source crop may be sent
  to the planner without overriding Gate A/B; and failures show an error with no automatic retry or
  substitute show.
- Planning artifact: `plan/PIXI_SPRITE_SHOW_AND_AI_MOTION_MATCHING_20261001.md` revision 4. Sprite
  gaps are assessed across the supported behavior registry; walker/flyer are representative
  starting cases, not the only intended subject types. Exact-plan approval is recorded, and
  implementation is authorized on `codex/pixi-ai-show-20261001`. ADR/contract review, image-provider
  privacy/retention review, and asset rights/runtime eligibility remain gates for their respective
  integrations. No model call or asset promotion has occurred.

## Subject behavior registry addendum — draft — 2026-10-01

- The owner requested a comprehensive, explicit class registry for supported animals, people,
  plants, objects, vehicles, and other subjects (e.g. walker/flyer/swimmer), and approved the visual
  appearance of all 28 frames in seven FEAT-028 motion concept sheets.
- Approved plan: `plan/PIXIJ_SUBJECT_BEHAVIOR_CLASS_REGISTRY_REV5_DRAFT_20261001.md` (revision 5).
  It separates
  semantic subject families, structural rig archetypes, behavior classes, and action primitives;
  AI may select only from a deterministic, evidence-backed registry.
- Revision 5 is approved for implementation by the owner. The exact pre-approval hash and
  status-only post-approval hash are recorded in `approvals/TASK_APPROVAL.md`. Approved plan
  revision 4 and its hash remain untouched. The seven motion sheets remain in FEAT-028
  `assets/generated/`; visual approval does not imply rights, technical QA, catalog, or runtime approval.
- Revision-5 exact pre-approval SHA-256: `11C2DABC405D0C8C3C57768CD97A4277A34F63B97CD22DF984F3D0FE09FA32FD`.
- Owner clarified the coverage boundary (all current Gate-A/FEAT-028 topics plus a reviewed
  extension path), approved multi-capability subjects with behavior chosen per beat, and included
  plants/environment/effect motion. The owner also requested motion sprites for all supported
  non-static behaviors, with one or more reusable cycles per compatible behavior class and variants
  where needed. `STILL`/`UNKNOWN` are safe no-motion outcomes. The owner approved the exact revision;
  implementation is underway. See
  `evidence/notes/BEHAVIOR_REGISTRY_IMPLEMENTATION_20261001.md`. New sprite candidates remain gated
  on separate visual review, rights/provenance and technical/runtime checks.

## Pixi show implementation — offline bridge; runtime gated — 2026-10-01

- Implemented additive `PixiShowPlanV1` / `PixiRendererShowEnvelopeV1` backend and TypeScript
  contracts, deterministic compiler, one-call Lightning planner adapter, bounded source crop,
  rights-filtered asset capability service, and V3 renderer bridge. Frozen V1/V2 contracts remain
  unchanged. Backend and Lightning planner flags default off; no live model/provider request was
  made. A planner failure preserves the original and is surfaced as a typed error without automatic
  retry, V1 fallback, or a substitute show.
- The planner is wired only after Gate B and is constrained by the adult-confirmed Gate-A subject,
  selected activity/objective, verified rig tier/part roles, exact renderer duration, candidate
  allowlist, bounded crop, and deterministic motion templates. Pixi receives selected short-lived
  PNG capabilities and validates hashes/bytes. Static sprites cannot claim articulated action.
- Part-image processing proposes only visible connected color regions inside the verified subject
  mask. A uniform silhouette yields no parts; role anchors only label evidenced regions. Synthetic
  checks prove parent containment and no overlap; they do not establish real-drawing anatomy.
- FEAT-028 inventory audit: 144 catalog frames across 24 topic families are single-pose entries;
  none is an animation-ready locomotion cycle. Metadata roles: 69 `SUBJECT`, 51 `PROP`, 18
  `ENVIRONMENT`, 6 `EFFECT`. Walker/flyer are the first demonstrated animation gaps; two four-pose
  draft sheets are stored in FEAT-028 `assets/generated/` and remain unreviewed, uncatalogued, and
  runtime-ineligible. Existing 144-frame visual approval is distinct from rights clearance.
- Verification: full backend suite reached 100%; `pnpm -r typecheck`, `pnpm -r test`, renderer demo
  build, focused Ruff, and Python syntax checks passed. Repository security validation passed after
  deleting task-created pytest scratch directories. Android playback, rights-cleared sprite
  composition, live Qwen behavior/subject classification, privacy/retention review, and L4
  latency/VRAM remain unverified. Details: `evidence/notes/PIXI_SHOW_IMPLEMENTATION_20261001.md`.

## Local sprite-cycle preview activation — 2026-10-02

Under the separate owner-approved local activation plan, the backend now has a default-off preview
gate limited to local/test environments. The exact-hash applied catalog exposes only the avian
walker and corgi walker cycles; the production manifest and rights/runtime gates are unchanged.
The app-root Metro startup/root-resolution issue was also fixed and its Android bundle now serves
successfully. Backend focused tests, renderer tests/typecheck/build, and mobile check pass. A full
image-to-visible-Pixi playback has not yet been verified on the emulator; do not treat this as
Android acceptance or production activation. See
`../../FEAT-028-pixi-topic-asset-library/evidence/notes/MOTION_CYCLE_LOCAL_PREVIEW_ACTIVATION_20261002.md`.

## Sprite-cycle renderer sidecar — 2026-10-02

The owner visually approved the new 30-sheet/120-frame sprite batch. The additive V4 Pixi renderer
sidecar is implemented offline: it accepts gated frame capabilities, checks content hashes, and
syncs animation to the existing show clock. Backend, renderer, mobile, build, typecheck, Ruff, and
repository security checks passed. Visual approval is not runtime approval: rights/provenance,
crop/pivot/loop QA, catalog registration, formal renderer verification, and Android acceptance remain
open, so the checked-in manifest still rejects runtime use. Details: `evidence/notes/SPRITE_CYCLE_PIXI_INTEGRATION_20261002.md`.

## Owner direction — adaptive original-art rendering — 2026-10-08

- The owner wants both background removal and body-part separation, preferring independent part motion when validated masks support it.
- If the whole subject cannot be split into reliable parts, use the validated original-subject cutout in a Pixi scene selected to fit the child's chosen topic. The owner allows AI to choose among supported rendering strategies and selected reuse of the existing single post-Gate-B planner request.
- The planner currently selects behavior/assets/beats but has no explicit rendering-strategy/theme field; current candidate data is text metadata without visual previews. The approved additive contract and candidate-preview approach is recorded in `plan/PIXI_ADAPTIVE_ART_AND_TOPIC_SCENE_20261008.md` (pre-approval SHA-256 recorded in the approval ledger).
- Gate A/B authority, immutable source/provenance, FEAT-028 asset rights/runtime eligibility, and no-live-provider boundaries remain in force.

## Adaptive original-art rendering — implementation update — 2026-10-08

- The approved additive contract is implemented locally: planner request V3 carries the selected topic and bounded transient candidate previews; plan V3 returns one supported renderer strategy and an optional allowlisted scene-theme asset. The existing post-Gate-B planner request remains the only AI call.
- Verified part motion remains preferred. The auto-rig validator rejects partial part masks that do not meet the existing parent-containment and coverage bar; the valid subject mask can then use the approved cutout/topic-scene path. The source artwork is immutable and remains the primary subject.
- Renderer envelope V4 and command V6 are additive; older Pixi contracts remain supported. Theme art is capability/hash checked and rendered behind the cutout. Static-source mode disables subject translation.
- Candidate previews are generated transiently from approved/applied, runtime-eligible catalog assets and are excluded from logs and evidence. The worker builds one contact sheet for the existing planner inference; no second inference, new dependency/model, or live provider request was made.
- Local verification and remaining gates are recorded in `evidence/notes/ADAPTIVE_ART_AND_TOPIC_SCENE_IMPLEMENTATION_20261008.md`.

## Pixi planner timeout and invalid output — 2026-10-09

- Owner-approved follow-up: `plan/PIXI_SHOW_TIMEOUT_AND_OUTPUT_VALIDITY_FIX_20261009.md`.
- The mobile renderer-preparation call currently aborts at its generic 30-second deadline while the bounded Lightning/Qwen planner can take up to 120 seconds. Lightning logs also report `MODEL_OUTPUT_INVALID`/HTTP 502; the current server log intentionally does not reveal whether parsing, schema validation, or deterministic asset validation failed.
- The approved fix is limited to the mobile deadline and V4 prompt/closed parser diagnostics. No additional planner call, retry, fallback, contract change, or real-child-data test is authorized.
- Local implementation is complete: only renderer preparation now waits up to 150 seconds; the V4 prompt follows the closed schema; one optional outer JSON fence is unwrapped; and failures receive sanitized stage-specific log codes. Static Python compilation and `git diff --check` passed; tests and live model inference were not run.
- Feature-local evidence: `evidence/notes/PIXI_SHOW_TIMEOUT_AND_OUTPUT_VALIDITY_FIX_20261009.md`. The remote Lightning checkout still needs this change and a Uvicorn restart before live acceptance can confirm the new diagnostics.

## Pixi schema-invalid follow-up — 2026-10-09

- Owner confirmed Lightning had pulled and restarted `c74831e`; the next `/v4/pixi/show-plan` request still returned HTTP 502 with `MODEL_SCHEMA_INVALID` after activity ranking succeeded.
- Source review found the V4 prompt asked for eligible asset IDs and later prohibited all asset IDs. The follow-up plan also makes JSON array/null types explicit and adds a bounded schema-path/error-type summary that excludes values and messages.
- Local implementation and static verification: `evidence/notes/PIXI_SCHEMA_INVALID_PROMPT_CONTRADICTION_FIX_20261009.md`. The newest patch needs to be deployed and the synthetic request repeated before runtime acceptance.

## Pixi root-validator failure follow-up — 2026-10-09

- After deploying and restarting `b3a7798`, the owner reported `MODEL_SCHEMA_INVALID schema_issues=root:value_error`.
- The root validator can reject duplicate selected IDs, a non-SETTLE final beat, an insufficient still tail, overlapping/out-of-order beats, or supplemental asset references. The prompt did not directly state the final beat's `endSeconds <= durationSeconds - 2` or uniqueness of `selectedAssetIds`.
- The approved follow-up makes these constraints explicit and maps known validator messages to fixed safe diagnostic codes. Evidence: `evidence/notes/PIXI_ROOT_VALIDATOR_DIAGNOSTICS_AND_CONSTRAINTS_20261009.md`.
