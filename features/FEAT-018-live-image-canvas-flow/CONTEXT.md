# FEAT-018 live image and canvas context

- Status: P1 complete; D3/P2-T1 closed for owner-approved offline Cohorts A+B; P2-T2 contract
  boundary and bounded offline implementation complete; approved local Android image-only UI/API
  integration is implemented and offline-tested; emulator and owner-run live acceptance remain
  pending
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
