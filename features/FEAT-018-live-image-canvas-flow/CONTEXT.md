# FEAT-018 live image and canvas context

- Status: P1 complete; D3/P2-T1 closed for owner-approved offline Cohorts A+B; P2-T2 contract
  boundary and bounded offline implementation complete; the approved staged topic/Pixi/video-
  placeholder/outdoor-activity flow is implemented, offline-tested, Android-built and boot-smoked;
  owner-run live Lightning flow and full orientation/control acceptance remain pending
- Plan revision: 2 with approved P2-T1 D2/D3-R2 and P2-T2 offline addenda
- Owner: shared integration allocation pending contract freeze approval
- Goal: run a synthetic/non-child JPG/PNG through backend admission and the owner-triggered Lightning
  Vision V2 path, Gate A, adult-entered one-anchor/one-objective ExperienceSpec/P1/Gate B, whole-image
  Pixi reveal, P4 fallback, caregiver handoff, session gallery and feedback.
- Data policy: non-sensitive test image only; no child/personal data, production data, or provider credential in Git/mobile/evidence.
- Dependencies: FEAT-003 `VisionUnderstandingResultV2` and local Qwen adapter boundary, FEAT-015 fixture contracts, FEAT-016 runtime/session contracts, FEAT-004 PixiJS/GSAP renderer plan, ADR-0006 allocation rules. FEAT-017's remote HTTPS path is not used by P2-T2.
- Contract authority: `plan/CONTRACT_FREEZE.md`.
- Pilot: 20 golden activities for full device/integration flow; 100 MVP activities for offline catalog/reference validation.

## Current state

The 2026-09-23 staged story-intro increment is implemented under the approved
`PIXI_STORY_INTRO_TOPIC_DIRECTIONS_FLOW_PLAN.md`. Backend understanding now returns at most three
source-linked Vietnamese topic directions and retains the one-changed-direction re-query boundary.
Gate B remains the immutable ExperienceSpec approval. After approval, the mobile app opens a
dedicated landscape Pixi intro with timeline controls and synchronized captions, then an explicit
landscape main-video placeholder, restores portrait, creates the existing handoff and opens the
outdoor activity. The renderer uses the original source image only and emits four bounded beats;
no video or provider generation was added. Android x86_64 build/install and initial portrait boot
passed. Evidence is recorded in
`evidence/notes/PIXI_STORY_INTRO_TOPIC_DIRECTIONS_IMPLEMENTATION_20260923.md`; the complete live
flow remains an owner-run synthetic-image check because Codex did not spend Lightning credits.

P2 research round 1 is complete as documentation only (2026-09-09). Working research
and handoff notes remain local-only; publish selected completed P2 records after
owner review through the evidence index. See
`plan/P2_OFFLINE_FIRST_PLAN.md` (P2-R1, awaiting owner review). The proposal separates
offline work from later FEAT-003 producer connections and full live acceptance.
The owner reports Phase 8 executed with insufficient quality. A new untracked Phase 8
report appeared during final verification and records `QUALITY_NOT_READY`, with both
passes schema-valid 8/8 but below quality thresholds; its hash and provenance are in
the local research report. No FEAT-003 state, report or approval was changed by this research.

The repository has a fixture UI and backend-only live P2 route. The approved P1 slice is now implemented offline: the reviewed catalog is loaded through a typed template adapter, adult context and hard eligibility rules run before fit scoring, and the fixture-only ExperienceSpec compiler locks anchor/objective/template/spec identity at Gate B. PixiJS/GSAP runtime/bridge, approved asset pack, live media consumers and gallery journey remain downstream work and are still pending their own approval.

The D3-R2 harness review found and fixed only evaluation-boundary issues: non-blocking stdin
submission so a child that does not read its pipe still reaches the parent timeout; clean-worktree
validation now rejects untracked files; aggregation recomputes timing status instead of trusting a
spoofed field; child output locks the environment envelope; and missing source digests are allowed
only for the bounded byte-budget rejection. These changes do not alter D2 admission behavior.

Formal Cohort A execution completed at commit `c77230ca1593d5cd31098b5e58f3ff2a13d18a63` with
320 forward and 320 reverse samples. The sanitized metrics artifact and independent verification
report were owner-approved on 2026-09-11 and are indexed under `evidence/README.md`. This closes
D3/P2-T1 for the synthetic Cohort A scope at that time. Formal Cohort B was subsequently executed
and independently verified; the combined closure is recorded below.

## P2 image admission (D1) — 2026-09-10

An isolated image admission and decoding design was accepted and published
(`evidence/P2_IMAGE_DECODE_DESIGN_20260910.md`, `EV-018-P2-DECODE-DESIGN-01`), conditional on
preserving the existing FEAT-003 image-research path. The follow-on D1 specification is now
complete and published as revision 2 (`evidence/P2_IMAGE_ADMISSION_SPEC_20260910.md`,
`EV-018-P2-D1-SPEC-01`): exact admission outcomes, bounded snapshot flow, a measured PyAV
decoder profile, a FEAT-018-local fixture manifest design, and an implementation acceptance
checklist. The specification is additive to FEAT-018 and changes no FEAT-003 default,
validator, inspector, contract, policy, prompt, model profile, fixture, scoring rule,
benchmark runner or historical evidence.

The owner subsequently approved U1 (`av==18.1.0` in a new optional `image-admission` extra
in `backend/pyproject.toml`) and the isolated D2 scope, recorded in `approvals/TASK_APPROVAL.md`
"Approved P2-T1 D2 scope addendum — 2026-09-10". **D2 implementation and its deterministic
tests are reviewed and accepted** (`evidence/notes/P2_D2_IMPLEMENTATION_20260910.md`,
`EV-018-P2-D2-IMPL-01`): 58 focused tests passed; the full 900-test backend collection reported
895 passed and 5 skipped, together with clean lint, type and repository validators. **D3
**D3-R2 performance/memory evaluation is implemented, formally executed and independently
verified for offline Cohort A+B.** The fresh-process protocol, bounded I/O/cleanup, Win32 native
reads, conservative [L,U] classification, deterministic 16-profile manifest and aggregation are
covered by the D3 test suite. D3/P2-T1 is closed for the owner-approved offline Cohort A+B scope;
D2/D3 remain additive to FEAT-018 only. FEAT-003 and all provider/mobile/public-contract
integration remain unchanged and separately gated.
## Canonical P2 integration — 2026-09-11

The approved canonical P2 branch `origin/feature/feat018-p2-image-validation` was merged into `codex/feat-018-contract-plan` as merge commit `627260c`, after carrying the P2 integration approval addendum. The merge includes the reviewed D2 image-admission implementation, deterministic media validation, P2 offline fixtures and related evidence. The other P2 branches remain research references. D3 measurement, FEAT-003 producer connection, live provider execution, mobile/public-schema integration, P3/P4 implementation and production work remain pending.

## P3/P4 offline integration — 2026-09-11

The approved P3 renderer branch `origin/plan/person-3-art-animation-poc` was merged as `2851bb6`. It contributes the closed Motion DSL, PixiJS/GSAP browser player, source-art provenance loader, butterfly fixture/demo, validation, fallback and benchmark support. The approved latest P4 branch `origin/feat-018-person-4-media-integration` was merged as `77745c4`, followed by its replay entrypoint update `ccd1ea5` in merge commit `da1a369`. It contributes versioned learning-media contracts, cache-first resolver, safe fallback, replay fixtures and sanitized evidence. These are offline/scoped integrations; live provider execution, Android/mobile wiring, production assets and production deployment remain pending.


## P1 strict continuity polish — 2026-09-11

The approved P1-only polish is implemented in the application compiler. `P1_STRICT_CONTINUITY_V1` now hard-gates exact primary-anchor label/tag and semantic-kind compatibility, objective membership, downstream identity continuity and the immutable spec hash before Gate B approval. Bridge wording is child-facing and derived from the selected anchor and objective title while its versioned references remain locked to the same template.

The feature-local fixture set covers the butterfly fold-and-print pass, unrelated sorting rejection, unsupported anchor kind, unrelated objective, ambiguous selection, bridge drift, media-plan drift and spec-hash drift. The catalog audit confirms 20 non-production golden templates with non-empty anchor labels, supported kinds and known objective references. No P2/P3/P4 code, contract version, provider, mobile or production scope changed.

Validation evidence: `evidence/metrics/P1_STRICT_CONTINUITY_20260911.json` and `evidence/notes/P1_STRICT_CONTINUITY_IMPLEMENTATION_20260911.md`.


## P1 catalog and Gate integrity polish — 2026-09-11

The approved follow-on P1 integrity plan is implemented. The golden catalog adapter now removes objective IDs and broad area taxonomy values from `supported_anchor_labels`, normalizes and de-duplicates labels, and fails closed when meaningful labels or objective titles are missing. The compiler rejects duplicate template IDs, validates injected objective titles, enforces optional selected activity/objective refs when supplied, routes compilation through the same Gate B approval path, and independently verifies deterministic `spec_id` and `spec_sha256`.

The contract versions remain unchanged and no P2/P3/P4/shared/mobile source changed. The expanded P1 suite covers catalog hygiene, all optional context ref mismatch/partial cases, Gate B re-checks, duplicate registration, spec ID drift and downstream consumer compatibility. Evidence: `evidence/metrics/P1_CATALOG_GATE_INTEGRITY_20260911.json` and `evidence/notes/P1_CATALOG_GATE_INTEGRITY_IMPLEMENTATION_20260911.md`.

## P1 online-model compatibility tests — 2026-09-11

The approved compatibility addendum is implemented as an offline boundary suite. Provider-shaped Qwen3-VL-8B-Instruct and Whisper large-v3-turbo payloads pass through the existing structured adapters, preserve source hashes and provenance, and feed the existing adult-confirmed `SemanticAnchorSetV1` into the butterfly P1 compiler and Gate B. Malformed, prohibited, unknown, timeout, retry, empty-entity, low-confidence and unrelated-model cases fail closed. No live provider, model download, token, raw media or downstream source change was used.

Evidence: `evidence/metrics/P1_ONLINE_MODEL_COMPATIBILITY_20260911.json` and `evidence/notes/P1_ONLINE_MODEL_COMPATIBILITY_IMPLEMENTATION_20260911.md`.
## D3/P2-T1 closure - 2026-09-12

Formal Cohort B completed with 24 samples from eight owner-approved images, three fresh-process
repeats per image, all admitted and within the approved timing and memory targets. Independent
verification reproduced every published data value with zero discrepancies and accepted the result as
`PASS WITH FINDINGS`. D3/P2-T1 is closed for the offline Cohort A+B evaluation scope. The three
verification findings remain follow-up work before a future formal run relies on the same cleanliness
safeguard. Provider, mobile, Gate A, public-contract and shared-integration scopes remain separately
gated.

## P2-T2 contract and offline implementation approval - 2026-09-12

The owner approved FEAT-018 consumption of FEAT-003's typed `VisionUnderstandingResultV2` and
local `qwen_vision.py` adapter boundary. FEAT-003 ownership is unchanged and its schemas, runtime,
profiles, dependencies, benchmarks, fixtures and evidence may not be modified. FEAT-017's flat V1
contract and remote HTTPS `LightningVisionAdapter` are excluded from P2-T2.

FEAT-018 owns a separate `RawUnderstandingResultV1` with typed observation groups, confidence
bounded to `0..1`, required source SHA-256, typed failures, preserved ambiguity/conflicts and
`gate_a_required=true`. The approved implementation slice is offline-only and limited to the exact
schema, port, mapper, unit/contract tests and one sanitized feature-local evidence note listed in
`approvals/TASK_APPROVAL.md`. Live Lightning/GPU execution, model-weight download, provider/network
calls, mobile, Gate A UI, P1 eligibility, P3/P4 and shared integration remain separately gated.

## P2-T2 offline implementation closure - 2026-09-12

The owner approved the completed offline P2-T2 implementation at commit
`11468d3a5a327697a491f09251a3210987337da0`. The change adds the mandatory ASR correlation guard
before `RawUnderstandingResultV1` construction and regression coverage for matching and mismatched
ASR results. Focused tests (17) and the related vision/Qwen/ASR sweep (801 passed, 5 skipped) passed;
ruff, mypy, repository validators and `git diff --check` were clean. The independent verification
report found no blocker and confirms the published contract/data scope is unchanged.

P2-T2 offline is complete. Live Lightning/GPU/model execution, provider/network calls, P2-T3 through
P2-T5, mobile, Gate A UI, P1 eligibility, P3/P4 and shared integration remain separately gated.

## Shared Android/backend integration addendum — 2026-09-18

- The project owner approved shared integration addendum revision 2 in
  `plan/UI_MOBILE_LIGHTNING_ANDROID_DEMO_PLAN_REV2_DETAILED.md` and recorded the exact approval/hash
  in `approvals/TASK_APPROVAL.md`.
- Approved demo target: Android Emulator, image-only non-child synthetic/test image sent through the
  backend to Lightning Vision, Gate A/P1/Gate B, PixiJS original-art canvas, P4 cache/fallback,
  handoff, session gallery and feedback. No audio capture/upload/ASR and no video.
- The current run remains unauthenticated and in-memory. Implementation must use application ports
  with in-memory/temp adapters so future identity and durable-store adapters can be added without
  changing domain contracts. Later sign-in/save is not implemented by this approval.
- Future boundary follows ADR-0005: Firebase Authentication only, backend token verification through
  provider-neutral `IdentityTokenVerifier`/`VerifiedPrincipal`, PostgreSQL/S3-compatible backend-owned
  persistence; Firebase Storage/Firestore/Realtime Database remain forbidden.
- ADR-0005 now has a narrow FEAT-018 owner-approved image-only development exception. The owner
  reports ~25 existing credits and authorizes up to 25 total, no top-up; the owner will manually
  run live requests and Codex must never do so. No automatic provider retry; only admitted synthetic/
  non-child images; result must satisfy the FEAT-003 V2 boundary and Gate A remains mandatory.
  FEAT-016 state order, retake invalidation,
  P1 completed-activity context, Gate-A/B wire schemas and version adapters have been reconciled and
  verified in the M1 evidence record. The versioned session API and Expo Android workflow are now
  connected; offline fake-provider verification is complete. The app's user-triggered live lane is
  enabled under the ADR-0005 25-credit ceiling, but the owner still needs to build/run the emulator
  and personally initiate any provider request.

## Optional narration integration closure — 2026-09-21

- The owner-approved correction supersedes the earlier image-only UI note for this demo: image
  remains mandatory, while narration now has explicit `NONE`, typed `TEXT`, and recorded `AUDIO`
  choices on the reachable BaoVC Capture screen.
- Typed narration is sent directly in `MobileWorkflowCommandV1` as `TEXT_TYPED`; it does not invoke
  ASR or TTS. Recorded audio is stored as a process-local artifact and is sent to the backend-owned
  Lightning `/v1/asr` route only after the user taps the explicit analysis action.
- The same Lightning deployment now serves `/health`, `/v2/vision`, and `/v1/asr`. The server loads
  faster-whisper lazily, validates source identity/hash, and returns the existing strict Phase-A ASR
  contract. Audio failure blocks before Vision and does not silently continue.
- Settings now load `backend/.env` deterministically even when Uvicorn starts from the repository
  root. Mobile still contains no Lightning endpoint/token and no durable auth/save implementation.
- Video remains excluded. Live provider calls were not made by Codex; the owner manually triggers
  smoke requests under the approved approximately 25-credit ceiling.
- Asset review is approved as work, not as a blanket visual approval: FEAT-028's 144 frames remain
  `REVIEW_PENDING` until each frame and its rights are reviewed and the owner records decisions.
- The Shared Integration Addendum Rev 2 plan hash was refreshed after narrowing the media lane to
  image-only; the corrected hash and timestamp are in `approvals/TASK_APPROVAL.md`.

## BaoVC UI and runtime verification — 2026-09-21

- The Android client was corrected to restore and retain BaoVC's original React Native UI shell;
  the earlier green standalone demo screen is no longer the mounted app entry.
- Real client wiring now lives in `apps/ui-mobile/src/context/AppContext.tsx` and reuses the
  versioned client in `apps/ui-mobile/src/demo/api.ts` as a transport adapter. The visible flow is
  `CREATE_SESSION -> image admission -> explicit RUN_UNDERSTANDING -> Gate A -> P1 context/filter
  -> ExperienceSpec -> Gate B -> renderer launch/handoff -> feedback`.
- The UI renders the selected source image, backend analysis claims and backend-selected activity;
  PixiJS is opened after handoff with the source-only renderer contract. No video, provider token or
  durable save was added to mobile. The later narration addendum below owns the optional microphone
  and ASR behavior.
- Verification on this worktree: `pnpm --dir apps/ui-mobile exec tsc --noEmit` passed; the six-test
  backend contract file `backend/tests/contract/test_live_image_demo_api.py` passed using the
  repository backend virtualenv; the running local API returned `ADMITTED` for the approved
  synthetic fixture upload. The owner remains responsible for manually triggering the Lightning
  request on the emulator under the 25-credit ceiling.

## Live VLM schema-output remediation — 2026-09-22

- The approved FEAT-018 live `/v2/vision` route now reuses FEAT-027's bounded Qwen payload
  normalizer and FEAT-003's closed mapping diagnostics. It performs at most one internal repair
  generation after the first output fails mapping/schema validation; it does not widen the V2
  contract or enable client/unbounded retries.
- Repair prompts contain the canonical JSON instructions and closed diagnostic tokens only. Raw
  model output, image bytes, narration, credentials, child data and raw exception text are not
  logged, persisted, returned or committed.
- Local tests, Ruff, compile checks, architecture validation, repository security validation and
  diff checks passed. Mypy was attempted but blocked by the workstation's Windows Application
  Control policy loading a Python DLL; this is an environment limitation, not a reported code
  failure. Owner-run Lightning smoke remains pending and is limited to synthetic/non-child images
  under the existing approximately 25-credit ceiling.

## Topic quality and T2 activity matching — 2026-09-22

- The owner-approved plan `plan/TOPIC_AND_T2_ACTIVITY_MATCHING_FIX_PLAN.md` is implemented. The
  backend now ranks image claims deterministically, demotes scenery/background labels, composes a
  bounded Vietnamese topic from grounded claims, and preserves raw labels, claim IDs, confidence,
  source identity and reviewed semantic tags through Gate A.
- The existing reviewed semantic activity catalog is injected through `SemanticCatalogPort` into the
  supervised workflow. Exact P1 matches keep their existing path; raw English/alias/concept-family
  labels resolve through the reviewed catalog, with one age-safe baseline fallback labeled as an
  expanded recommendation. Existing age, material, readiness, supervision, safety, Gate B and
  activity/template/objective identity checks remain authoritative.
- The generic workflow-result payload exposes optional topic/recommendation metadata without
  widening `P1ContextOptionsV1` or changing FEAT-003. The BaoVC T2 screen clears stale state,
  waits for the real backend chain, labels fallback provenance, and no longer presents the
  hardcoded butterfly card/icon as a backend result. The initial claim selection is primary-only.
- Focused contract, semantic catalog, ranking, Ruff, mypy and mobile TypeScript checks passed. The
  repository-wide backend collection was attempted but fixture setup was blocked by Windows access
  denial for the pytest temp/cache directories. No Lightning request was made by Codex; owner-run
  Android/Lightning smoke remains pending under the existing approximately 25-credit ceiling.
- Evidence: `evidence/notes/TOPIC_AND_T2_ACTIVITY_MATCHING_IMPLEMENTATION_20260922.md`.

## Progressive Qwen multimodal response — implementation 2026-09-22

- The approved plan `plan/PROGRESSIVE_QWEN_MULTIMODAL_RESPONSE_PLAN.md` is implemented without
  widening the frozen Vision V2 or MobileWorkflow envelope. A valid-but-empty Qwen result now gets
  one semantic repair opportunity in the Lightning adapter; if it remains empty, the application
  returns `BLOCKED_NO_GROUNDED_CLAIMS`, keeps the session out of Gate A, and the UI shows a retry
  message instead of `0 Thực thể`.
- The backend now emits a sanitized `understanding_progress` projection with stage history,
  image/narration/fused claim IDs, conflict records, repair/attempt counters, Gate-A readiness and
  a deterministic Vietnamese topic normally bounded to 10–18 words. A read-only progress endpoint
  is available for polling; the current provider call remains terminal/synchronous and never emits
  partial model JSON.
- Image and ASR/typed-text evidence remain separate. Reviewed aliases can produce a derived fused
  claim with source references; unsupported disagreement is preserved as a closed conflict. Typed
  text does not receive fabricated numeric confidence.
- Choosing a different primary direction in BaoVC sends one explicit `REQUERY_UNDERSTANDING` command
  using the admitted image and stored narration input. The backend rechecks the image, records a
  new direction revision, retains the prior valid proposal if the re-query fails, and rejects a
  second changed-direction re-query in the demo.
- Verification passed: full backend test collection (`pytest -q backend/tests`, with repository
  root on `PYTHONPATH`, 6 existing skips), focused Qwen/live contract tests, Ruff, mypy on changed
  backend modules, mobile TypeScript, compile, diff checks and repository security validation. No
  Lightning/model request was made by Codex; owner-run smoke remains pending under the approved
  approximately 25-credit ceiling.

## Activity suggestion strict-fit/UI recovery diagnosis — 2026-09-22

- A real Android session reached `CANDIDATES_READY` but `PREPARE_EXPERIENCE` returned a typed
  `BLOCKED` envelope with `ANCHOR_TEMPLATE_MISMATCH` and `FIT_BELOW_THRESHOLD`. The selected
  `ACT-0029` candidate came from loose token overlap, while the unchanged strict continuity gate
  correctly rejected it before ExperienceSpec creation.
- HTTP access logs showed `200 OK` because blocked workflow outcomes use the versioned response
  envelope; the UI hid the closed reasons behind a generic ExperienceSpec message and could start
  a duplicate chain before React busy state re-rendered.
- The approved repair is documented in
  `plan/ACTIVITY_SUGGESTION_STRICT_FIT_UI_RECOVERY_PLAN.md`; implementation was authorized by the
  owner on 2026-09-22. It aligns
  option discovery with strict compilation, tries the next reviewed eligible candidate, preserves
  exact identity, adds an atomic UI request lock, reopens existing results, and retains failures
  without showing a mock activity. No provider call is required or authorized for this repair.
- Implementation is complete. Direct options and semantic candidates now share the compiler's
  strict fit policy before exposure; ranked semantic resolution continues to the next reviewed
  candidate after rejection. BaoVC preserves valid state, synchronously locks the activity request,
  reopens prepared results without network calls, and maps closed P1/fit reasons to safe Vietnamese
  guidance. The butterfly/ACT-0029 regression and Gate-A-to-ExperienceSpec identity continuity are
  covered by unit and HTTP contract tests. Verification evidence is in
  `evidence/notes/ACTIVITY_SUGGESTION_STRICT_FIT_UI_RECOVERY_IMPLEMENTATION_20260922.md`.

## Vision/topic/catalog/Pixi/child-UX follow-up — 2026-09-22

- Status: `APPROVED — IN_PROGRESS`; mandatory Phase 0 read-only UI audit completed with checkpoint
  `UI_AUDIT_COMPLETE — NO CODE CHANGED`. Application/runtime implementation may now start.
- Owner emulator evidence shows four remaining integration-quality problems: English and duplicate
  labels can escape the live Qwen result into the Vietnamese UI; topic composition remains raw and
  overly generic; the real HTTP runtime still loads the baseline/legacy activity catalog and can
  present an unrelated age-safe activity with template/material/safety IDs; and a valid backend
  Pixi launch is rejected by the strict TypeScript bridge because Python sends optional values as
  explicit `null`.
- The full reachable BaoVC flow also renders expected failures as inline red technical text and
  mixes child instructions with backend, Gate, ExperienceSpec, catalog and protocol terminology.
- The proposed repair is documented in
  `plan/VISION_TOPIC_ACTIVITY_CATALOG_PIXI_CHILD_UX_PLAN.md`. It introduces a single shared vision
  repair budget, grounded Vietnamese normalization/topic composition, V2 expansion catalog runtime
  wiring, at most three strict-fit prioritized activity cards with adult selection, an app-level
  friendly error modal, a full child-facing copy/accessibility pass, and canonical Pixi transport
  serialization verified across Python and the actual TypeScript schema.
- Before any implementation, the revised plan requires a complete read-only audit of every
  reachable BaoVC screen and important loading/error/navigation state. The audit must produce a
  prioritized feature-local finding matrix and an explicit `UI_AUDIT_COMPLETE — NO CODE CHANGED`
  checkpoint; the already-observed UI, activity and Pixi defects remain mandatory scope.
- The audit is complete at base commit `f98958f6690e6d233ca79d8be1defec56fdd85be` on Android Emulator
  1080x2424/density 420. It found 25 bounded issues covering truthfulness, topic/activity continuity,
  Pixi transport, modal errors, stale notices, hard-coded butterfly preview/feedback, native chrome,
  keyboard/accessibility and child-facing copy. The prioritized matrix is recorded in
  `evidence/notes/FULL_UI_READ_ONLY_AUDIT_20260922.md`; no implementation/runtime code changed during
  the audit and no scope expansion is required.
- Boundaries remain synthetic/non-child demo inputs, process-local state, future auth/save seams,
  original-art preservation, no video, no credential in mobile/Git, no unrelated FEAT-026 changes,
  and no Codex-triggered Lightning request.

## Vision/topic/activity/catalog/Pixi/child-UX implementation closure — 2026-09-23

- The approved plan `plan/VISION_TOPIC_ACTIVITY_CATALOG_PIXI_CHILD_UX_PLAN.md` is implemented for
  the offline/API/UI scope. Phase 0's read-only audit remains recorded in
  `evidence/notes/FULL_UI_READ_ONLY_AUDIT_20260922.md` and was completed before source changes.
- The HTTP composition root now loads the curated V2 semantic catalog. The bird/branch path returns
  up to three prioritized strict-fit reviewed activities with Vietnamese display metadata; age-only
  unrelated activities are not exposed. Choosing a different offered card reruns the selected
  downstream P1/ExperienceSpec path without rerunning Qwen while Gate A is unchanged.
- Topic rendering now ranks specific visual evidence, translates covered English labels, removes
  duplicates/aggregate labels and composes a grounded Vietnamese sentence. The Qwen live adapter
  shares one bounded semantic-quality repair budget with schema repair, so a request can still make
  at most two model generations.
- BaoVC now presents concise child-friendly copy, uses a global friendly error modal, hides raw
  activity/provider/contract diagnostics, and keeps adult details in the activity flow. The Pixi
  bridge omits nullable optional fields and preserves the original drawing when playback fails.
- Verification evidence is recorded in
  `evidence/notes/VISION_TOPIC_ACTIVITY_CATALOG_PIXI_CHILD_UX_IMPLEMENTATION_20260923.md`.
  Offline tests, TypeScript, renderer tests, architecture validation and repository security
  validation passed. No live Lightning request, video path, auth flow or durable persistence was
  added; the future auth/save seam remains process-local and adapter-based.
- Final acceptance-gap closure added friendly recovery actions, original-art Pixi fallback/retry,
  collapsed adult guidance, keyboard avoidance, broader accessibility state, truthful process-local
  feedback copy, a mobile UI copy guard, a non-primary activity/no-Vision-rerun contract test and a
  TypeScript source-only renderer launch test. The focused and full backend suites, mobile and
  renderer TypeScript/tests, Ruff, mypy, architecture and security checks pass. The only harness
  finding remains the unrelated user-owned FEAT-026 directory structure.

## Pixi story-intro and staged media flow — 2026-09-23

- Status: `APPROVED — IMPLEMENTATION AUTHORIZED`; implementation is in progress.
- Owner emulator review confirms the current Pixi surface is not an effective animation: the live
  path supplies one whole-image reveal, the player has no seek/pause/progress controls, and the
  WebView is embedded at the end of the portrait activity-detail page. Topic choices also remain
  too close to raw claims and can collapse unknown labels into generic Vietnamese text.
- The owner confirmed the target order: Gate B keeps its exact ExperienceSpec approval meaning,
  followed by a landscape Pixi presentation-style opening from the original drawing, a landscape
  placeholder for the future main video, portrait outdoor activity instructions, then feedback.
- The owner also confirmed at most three complete grounded Vietnamese topic directions; selecting
  a different direction uses the existing bounded one-time re-query. Loading must communicate real
  stages so model/renderer work is not mistaken for a frozen app.
- Detailed scope, contracts, flow, acceptance criteria, risk controls and verification are in
  `plan/PIXI_STORY_INTRO_TOPIC_DIRECTIONS_FLOW_PLAN.md`. No runtime code may change until the owner
  approves that exact plan and its hash is recorded.

## Pixi-only exploration implementation authorization — 2026-09-23

- Status: `APPROVED — IMPLEMENTATION AUTHORIZED` on branch
  `codex/feat-018-pixi-exploration`.
- The owner approved implementation of
  `plan/PERSONALIZED_DRAWING_EXPLORATION_TAP_25D_PLAN.md` for subject-only Vietnamese labels,
  `SceneExplorationPlanV1`, bounded localization/cut-outs, tap-to-discover, 2.5D rendering,
  mobile flow, tests and feature-local evidence.
- Whiteboard MP4 generation, TTS, video worker/encoder, video playback and video READY/retry are
  explicitly excluded from this branch and are owned by another implementation task. This branch
  preserves only the existing video placeholder/handoff seam.
- Existing Gate A, Gate B, ExperienceSpec identity, original-art preservation, auth/save seams,
  synthetic/non-child demo boundary and no-Codex-Lightning-call rule remain unchanged. FEAT-003
  contracts and unrelated FEAT-026 files remain out of scope.

## Pixi-only exploration implementation — 2026-09-23

- Implemented on `codex/feat-018-pixi-exploration`. `SubjectCandidateSetV1` now projects at most
  three confirmed concrete entities into short Vietnamese labels with image/narration coverage,
  confidence bands and source claim references. `SceneExplorationPlanV1` adds bounded reveal,
  focus, relation and learning-bridge beats without changing the Qwen/FEAT-003 contract.
- Added `SceneFocusPlanV1` and explicit normalized source-region provenance. A region is accepted
  only when an approved localizer supplies a bounded region plus extraction version/confidence;
  absent or invalid localization produces `FALLBACK_REQUIRED` and keeps the whole original image.
  No fake bounding boxes, generated replacement artwork or supplemental assets are introduced.
- PixiJS now accepts source-derived crop layers, applies the crop in the WebView, supports GSAP
  motion for multiple source-preserving objects, and emits bounded `FOCUS_CHANGED` and
  `DISCOVERED_ENTITY` events. BaoVC shows child-friendly discovery chips and handles those events
  without exposing technical error codes.
- The video placeholder/handoff remains unchanged. MP4/TTS/worker/encoder/playback/READY/retry,
  auth, durable persistence, FEAT-003 and live Lightning calls remain excluded from this branch.
- Verification is recorded in
  `evidence/notes/PERSONALIZED_DRAWING_EXPLORATION_IMPLEMENTATION_20260923.md`.
