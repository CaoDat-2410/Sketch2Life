# Task approval

- Status: APPROVED for the historical slices below plus the Shared Integration Addendum Rev 2 and
  the narrow live-test authorization recorded in ADR-0005 on 2026-09-18. The owner may manually run
  synthetic-image Lightning tests up to the existing 25-credit total ceiling; Codex must not send
  live requests. Authentication and durable saving remain future seams only.
- Approver: Project owner direct instruction in the current conversation
- Plan revision: 2
- Requested scope: FEAT-018 revision 2 P1 implementation slice only: catalog promotion/provenance, Activity Template Library, adult context and deterministic eligibility, semantic-anchor to objective/template selection, ExperienceSpec compilation and fit validation, Gate B identity/version locking, catalog/pilot harness and feature-local evidence.
- Explicit exclusions: production API/cloud, Runpod, Android release, real child/personal data,
  mobile provider credentials, provider auto-retries, top-ups/purchases, and durable saving.

## Shared Android / Lightning / Pixi non-video integration addendum — 2026-09-18

- Approver: Project owner direct instruction in the current conversation (“duyệt, nhớ làm sao để sau này có thể nối vs auth flow, để sau này có thể lưu lại”).
- Approved artifact: `plan/UI_MOBILE_LIGHTNING_ANDROID_DEMO_PLAN_REV2_DETAILED.md`, Shared Integration Addendum Rev 2.
- Plan SHA-256 (image-only scope correction): `fa0f2e597fd56b221e5ef8f2b97d9f390d6206aaf9fc36bedb57b7ca3205af33`.
- Approved at: 2026-09-18 20:29:32 Asia/Ho_Chi_Minh (2026-09-18 13:29:32 UTC).
- Approved scope: local Android Emulator journey with image-only non-child synthetic/test image upload through the backend; Gate A, adult-entered fictional P1 context, exact Gate B/ExperienceSpec, PixiJS original-art canvas, per-frame asset/rights review and approved-only selection, P4 cache/fallback, activity handoff, session gallery and feedback. No microphone permission, audio capture/upload, or ASR call. No video.
- Future readiness requirement: current session/job/artifact use cases use application ports with in-memory/temp adapters. Preserve the existing provider-neutral verified-principal boundary and design a later explicit authenticated save/ownership contract; do not implement Firebase sign-in, persistent storage, or a save endpoint in this demo. Firebase data products are forbidden; future persistence follows backend-owned PostgreSQL/S3-compatible architecture.
- Boundaries: no real child media, mobile provider credentials, automatic persistence, commits/pushes, or blanket asset approval. All 144 FEAT-028 frames remain pending until individually visually reviewed and rights-cleared. Asset approval is separate from task-plan approval.
- Provider gate: the separate ADR-0005 FEAT-018 addendum authorizes only owner-initiated local
  synthetic-image Vision V2 requests against the existing balance, capped at 25 credits total.
  Owner monitors the provider balance; stop if cost or remaining balance is unclear. No Codex live
  calls, background/inferred calls, automatic retries, or public/shared-network deployment.
- Acceptance: exact HTTP/domain contract compatibility and corrected FEAT-016 state order; full emulator non-video flow when provider gate is cleared; honest typed no-match/fallback; no silent fixtures, no video; auth/save seams covered by adapter-boundary tests without durable writes.
- Scope/hash correction recorded 2026-09-18 21:10 Asia/Ho_Chi_Minh (14:10 UTC): the previously approved optional narration lane is removed to match the user's image-only demo requirement. This narrows scope; all approved objectives otherwise remain unchanged. The hash above identifies the corrected addendum.

## Live Lightning test authorization — 2026-09-18

- The owner clarified that approximately 25 Lightning credits are currently available and requested
  a live-test path, to be run personally. This confirmation is recorded in the ADR-0005 FEAT-018
  addendum; it does not authorize Codex to invoke Lightning.
- Hard aggregate ceiling: at most 25 credits from the existing balance for this synthetic-image
  demo; no purchase/top-up. The owner checks the provider's actual balance and cost before each
  manual run and stops if either is uncertain.
- Runtime remains one explicit user-triggered Vision request per action, with no inferred call and
  no automatic retry. Only admitted synthetic/non-child PNG/JPEG images up to the frozen 5 MB cap.
- Android emulator build and a real provider request remain operator-run acceptance checks; all
  agent-side verification uses fake/offline providers.

## Approved P1 scope addendum — 2026-09-09

The project owner approved FEAT-018 plan revision 2 for the P1 implementation slice described above. This approval covers the P1 task IDs `FEAT018-P1-E1` through `FEAT018-P1-E5` and the original P1 catalog/context/Gate-B/harness tasks in `PERSON_1_DOMAIN.md`.

Approved P1 acceptance boundary:

- versioned 100-MVP and 20-golden catalog promotion with provenance and the ACT-0004 migration;
- curated `ActivityTemplateV1` records with objective, anchor, age, material, supervision and safety rules;
- adult-provided `P1ContextV1` and deterministic hard eligibility rules;
- `SemanticAnchorSetV1` to one `LearningFocusV1` and one compatible activity template;
- immutable `ExperienceSpecV1` compilation and proposed `ActivityFitEvaluationV1` policy;
- Gate B approval of exact activity, objective, template and spec versions;
- 100-MVP offline validation, 20-golden pilot fixtures and redacted feature-local evidence.

This approval does not authorize P2 model changes, P3 renderer implementation, P4 provider/media implementation, shared mobile/backend/gallery integration, live provider execution, production API/cloud work, Android release, or real child/personal data. The proposed revision-2 contracts remain subject to the shared contract-freeze rules; P1 may implement only its approved domain slice and its fixture-local contract adapters.

## Implementation record — 2026-09-09
- P1 fixture-only implementation completed on `codex/p1-feat018-task-plan`.
- Evidence: `evidence/metrics/P1_ENGINE_VALIDATION_20260909.json` and `evidence/notes/P1_ENGINE_IMPLEMENTATION_20260909.md`.
- Downstream P2/P3/P4/shared/live/production scope remains unimplemented and separately gated.

## P2 integration addendum — 2026-09-11

- Approver: Project owner direct instruction in the current conversation.
- Approved scope: merge `origin/feature/feat018-p2-image-validation` as the canonical FEAT-018 P2 integration branch and connect its frozen P2 contracts to the approved integration branch. Treat the other P2 branches as research references only.
- Validation scope: offline contract compatibility, deterministic fixtures, repository validators, and relevant P2/integration tests.
- Explicit exclusions remain: live provider execution, production API/cloud, Android release, real child/personal data, mobile provider credentials, and P3/P4 implementation.
- Merge acceptance: no unresolved conflicts; P2 producers remain compatible with `VisionUnderstandingResultV1`, contract freeze, Gate A handoff, and existing P1 fixture adapters; evidence is stored under this feature.

## P3/P4 integration addendum — 2026-09-11

- Approver: Project owner direct instruction in the current conversation.
- Approved scope: merge the approved offline P3 renderer implementation from `origin/plan/person-3-art-animation-poc` and the latest approved offline P4 media integration from `origin/feat-018-person-4-media-integration` into `codex/feat-018-contract-plan`.
- Validation scope: package typechecks/tests, deterministic renderer/media fixtures, cache/fallback replay, contract compatibility and repository validators.
- Explicit exclusions remain: live provider execution, production API/cloud, Android release, real child/personal data, mobile provider credentials, and production asset publication.
- Other P4/P3 research or POC branches remain references only unless separately approved.

## P1 strict continuity polish addendum — 2026-09-11

- Approver: Project owner direct instruction in the current conversation ("ok, chốt plan, implement").
- Approved scope: implement `plan/P1_STRICT_CONTINUITY_POLISH_PLAN.md` in the P1 domain/compiler slice only: exact anchor label/kind compatibility, hard fit rejection before score threshold, bridge/media/activity identity defense-in-depth, policy metadata, fixture tests, and feature-local evidence.
- Validation scope: targeted P1 unit and fixture tests, the full offline Python/TypeScript test suites, repository security and contract/harness validators.
- Explicit exclusions: P2/P3/P4 code changes, shared/mobile integration, contract version changes, live provider execution, production API/cloud work, Android release, provider credentials, and real child/personal data.


## P1 catalog and Gate integrity polish approval — 2026-09-11

- Approver: Project owner direct instruction in the current conversation ("approve").
- Approved scope: implement `plan/P1_CATALOG_GATE_INTEGRITY_POLISH_PLAN.md`: catalog anchor-label hygiene, optional P1 context identity locks, one Gate B approval path, template/spec integrity fail-fast checks, fixture regression tests and feature-local evidence.
- Validation scope: targeted P1 tests, full offline Python/TypeScript suites, catalog/harness/architecture/security validators.
- Explicit exclusions: P2/P3/P4 code changes, shared/mobile/API changes, contract version changes, live providers, production/cloud, Android release, provider credentials and real child/personal data.

## P1 online-model compatibility test addendum — 2026-09-11

- Approver: Project owner direct instruction in the current conversation ("thêm nhiều test vào, đảm bảo là nếu có lên trên onl model là vẫn sài đc").
- Approved scope: implement `plan/P1_ONLINE_MODEL_COMPATIBILITY_TEST_PLAN.md` with provider-shaped ASR/VLM adapter fixtures and model-output-to-P1 handoff tests.
- Validation scope: offline injected clients/transports, contract round-trips, P1 Gate A/Gate B continuity, full offline suites and repository validators.
- Explicit exclusions: live provider/model execution, model downloads, provider credentials, production API/cloud, Android release, mobile/shared changes, contract version changes and real child/personal data.

This approval does not authorize D3 performance/memory evaluation, Qwen/ASR integration, mobile
transport, any public-contract migration, or any FEAT-003 connection. FEAT-003 contracts,
validation, adapters, inspector, prompts, profiles, fixtures, benchmarks, scoring, and historical
evidence remain fully excluded and unchanged. P2-T1 is not complete after D2 alone; D3 evaluation
and its separately reviewed evidence remain outstanding. The later D3-R2 addendum below separately
authorizes only that evaluation scope; it does not retroactively expand D2.

## Approved P2-T1 D3-R2 evaluation addendum — 2026-09-10

The project owner directly approved
`plan/P2_D3_IMAGE_ADMISSION_EVALUATION_PLAN.md` revision D3-R2 and its recommended decisions
D3-U1 through D3-U6. This approval authorizes only the offline image-admission evaluation harness,
deterministic Cohort A fixtures/execution, optional Cohort B preparation subject to the source gate,
and sanitized draft evidence described in that plan.

Approved measurement boundary:

- one fresh subprocess per sample, using the current interpreter and bounded stdin/stdout/stderr;
- 5-second observational target classified only from `admission_elapsed_ms` around the committed
  D2 `Feat018ImageAdmission.admit()` call;
- 256-MiB observational target classified only from the approved native-working-set bracket
  `[L,U]`: `U <= target` is `WITHIN_TARGET`, `L > target` is `EXCEEDS_TARGET`, otherwise
  `INCONCLUSIVE`;
- Windows native measurement through stdlib `ctypes` and `PROCESS_MEMORY_COUNTERS_EX`, with raw
  peak/current/private values diagnostic only and no peak-to-peak classification;
- Cohort A uses 20 fresh-process repeats per homogeneous profile and dependency-free nearest-rank
  p95; Cohort B is limited to eight non-sensitive owner-reviewed images and three repeats each;
- completed sanitized JSON/Markdown requires owner review before evidence indexing or D3/P2-T1
  completion.

Cohort B execution is not yet source-approved: the owner must visually review the actual four JPEG
and four PNG candidates against the plan's exclusion list before they are hashed or executed. Until
then, implementation and Cohort A work may proceed, but Cohort B must stop at its source gate.

This approval does not authorize a production timeout/worker, dependency change, D2 behavior or
policy change, Qwen/ASR work, mobile transport, Gate A/shared integration, public-contract
migration, or any FEAT-003 edit/connection. It does not mark D3 or P2-T1 complete and does not
authorize push or PR creation.

## Owner approval and Cohort A closure - 2026-09-11

The project owner approved Formal Cohort A at commit
`c77230ca1593d5cd31098b5e58f3ff2a13d18a63`, authorized publication/indexing of the sanitized
metrics JSON and both verification reports, and closed D3/P2-T1 for the synthetic Cohort A scope
only. Cohort B remains unapproved. The approved artifacts are indexed in `evidence/README.md`; no
provider, mobile, FEAT-003 or shared-integration work is authorized by this closure.

## Owner approval and Cohort B source admission - 2026-09-12

The project owner approved the exact local B01-B08 candidate set for FEAT-018 D3-R2 Cohort B:
four JPEG files and four PNG files, as recorded in the local git-ignored candidate manifest under
`tmp/feat018-cohort-b-input-20260912/`. The manifest sets `owner_reviewed=true` and preserves the
per-file SHA-256 values. This addendum authorizes only the offline Cohort B evaluation described by
D3-R2; raw images remain local and no provider, Qwen, Whisper, mobile, FEAT-003, or shared-
integration work is authorized.

## Owner approval and offline D3/P2-T1 closure - 2026-09-12

The project owner approved the Formal Cohort B execution and its independent verification with
verdict `PASS WITH FINDINGS`. The owner confirmed 24/24 samples, eight images with three fresh-
process repeats each, all `ADMITTED` and `WITHIN_TARGET`, zero data discrepancies, and the corrected
B08 manifest digest. The sanitized Cohort B execution report, metrics and independent verification
report may be indexed. D3/P2-T1 is closed for the offline Cohort A+B evaluation scope. The three
verification findings remain follow-up work and do not require a Cohort B rerun. This closure does
not authorize provider, mobile, Gate A, public-contract or shared-integration work.

## Approved P2-T2 contract and offline implementation addendum — 2026-09-12

The project owner approves FEAT-018 P2-T2 offline implementation after the FEAT-003 cross-feature
consumption addendum recorded in the corresponding FEAT-003 approval file.

Approved architecture and contract boundary:

- FEAT-018 consumes FEAT-003 `VisionUnderstandingResultV2` through the approved typed boundary in
  `vision_v2.py` and `qwen_vision.py`.
- FEAT-018 owns and freezes a separate `RawUnderstandingResultV1`; it is not an alias of FEAT-017's
  flat `understanding.py` V1, FEAT-003 Phase A V1, or FEAT-003 V2.
- `RawUnderstandingResultV1` uses typed observation groups, confidence values bounded to `0..1`,
  a required source-image SHA-256, typed failures, preserved uncertainty/conflicts, and
  `gate_a_required=true`. It cannot make eligibility, personality, readiness, activity, objective,
  Gate B, or safety decisions from media.
- Mapping preserves provenance and ambiguity and rejects source/session mismatch, malformed or
  prohibited output, extra fields, stale versions, and oversized output.

Approved FEAT-018 file scope:

- `backend/src/sketch2life/contracts/schemas/raw_understanding.py`
- `backend/src/sketch2life/application/ports/raw_understanding.py`
- `backend/src/sketch2life/application/services/raw_understanding_mapper.py`
- `backend/tests/unit/test_raw_understanding.py`
- `backend/tests/contract/test_raw_understanding_contract.py`
- one feature-local sanitized contract/evidence note under
  `features/FEAT-018-live-image-canvas-flow/evidence/notes/`

No unlisted file may be changed without renewed approval. In particular, FEAT-003, FEAT-017,
`vision_v2.py`, `qwen_vision.py`, mobile, Gate A UI, P1 eligibility, P3/P4, shared integration,
published D3 evidence, and canonical contract history are excluded from the implementation slice.

Offline-only gate: approved work may use typed fake fixtures and injected runners without network,
model weights, provider calls, GPU, or Lightning execution. Live Lightning execution, model-weight
download, and any provider/network call remain separately gated and require a later explicit
execution approval with fixture, budget, redaction, and evidence requirements.

Approved at: 2026-09-12, project owner direct instruction in the current conversation.

## FEAT-018 live-vision demo budget clarification — 2026-09-18

- The project owner clarified that approximately 25 Lightning credits are currently available and
  sufficient for testing. The approved FEAT-018 image-only demo ceiling is no more than 25 existing
  credits total; no purchase/top-up is authorized.
- The project owner will personally initiate live provider requests. Codex must not send live
  provider requests. Integration must require an explicit user action, make no automatic inference
  retry, and use only admitted synthetic/non-child images. The owner monitors credits outside this
  repository; if remaining balance or per-call cost is unclear, execution stops.
- This clarification narrows execution to the FEAT-018 dev-only image path under the ADR-0005
  addendum. It does not authorize ASR/audio, video, real child data, model downloads, or production
  inference. Provider output must validate as FEAT-003 V2 and map to FEAT-018 Raw V1; existing
  fixture-only/flat-V1 routes do not satisfy live acceptance.

## Owner approval and P2-T2 offline closure — 2026-09-12

The project owner approves the completed FEAT-018 P2-T2 offline implementation at commit
`11468d3a5a327697a491f09251a3210987337da0` (`fix(feat018): validate ASR correlation before mapping`).
Independent verification reported no blocker: the mapper now rejects supplied ASR results with a
mismatched correlation ID before Raw construction, while absent, matching-success and matching-
failure cases remain valid. Focused tests (17), related tests (801 passed, 5 skipped), ruff, mypy,
all repository validators and `git diff --check` passed. No model/GPU/Lightning/provider/network
execution occurred. This approval closes P2-T2 offline only; live execution and P2-T3 through P2-T5,
mobile, Gate A, P1 eligibility, P3/P4 and shared integration remain separately gated.

## Approved full workflow debug and narration-input addendum — 2026-09-21

- Approver: Project owner direct instruction in the current conversation: “thêm cái đó vào đi,
  đó là chỉnh sửa mới để phù hợp, sau khi thêm vào thì implement”.
- Approved plan: `plan/UI_BACKEND_FULL_WORKFLOW_ASR_DEBUG_PLAN.md`.
- Plan SHA-256 at approval: `CA9E4137061E37600B7C42976BE5AD0E18EDEA6DD700ACE001722F8B78365E63`.
- Approved behavior: image is mandatory; narration is optional and can be absent, recorded audio,
  or typed text. Typed text is passed directly as transcript context with explicit `TEXT_TYPED`
  provenance and is not converted to speech or sent through ASR. Recorded audio uses
  `faster-whisper` in the Lightning environment with Vietnamese auto-detection as the initial
  behavior.
- Approved implementation scope: reconcile versioned contracts; add backend audio/text ingress and
  orchestration; add backend-only ASR provider path; add a reachable BaoVC narration UI with a text
  fallback; remove silent mock/video success from the live route; add contract, backend, frontend,
  emulator and sanitized observability verification.
- Preserved boundaries: synthetic/non-child image only, Android Emulator demo, process-local state,
  future auth/save seam, no video generation/player in the live workflow, no provider credentials
  in mobile, and no automatic Lightning retry.
- Live execution boundary: Codex must not trigger Lightning or ASR provider calls. The owner alone
  performs the approved live smoke tests after offline/API/UI wiring is verified, within the
  existing approximately 25-credit ceiling.

## Implementation closure for the approved addendum — 2026-09-21

- The approved scope is implemented in the backend, Lightning service adapter, BaoVC Capture UI and
  Android native permission manifest. The plan's implementation-result section was appended after
  execution; the resulting plan SHA-256 is `BE6A2D754D686C1E403FD08B5BC2371847B424704106983CB6F03ED91C1EC545`.
- Offline verification passed: mobile TypeScript, focused image/narration/ASR adapter tests, the
  full backend contract/unit collection (5 existing skips), `git diff --check`, and repository
  security validation. No live provider call was made.
- The owner still controls live smoke execution and credit usage. No approval is implied for video,
  real child data, mobile credentials, durable storage, or automatic provider retries.

## Owner approval — live VLM schema-output remediation — 2026-09-22

- Approver: project owner direct instruction in the current conversation: “approve and implement”.
- Approved plan: `features/FEAT-018-live-image-canvas-flow/plan/LIVE_VISION_SCHEMA_REMEDIATION_PLAN.md`.
- Plan SHA-256 at approval: `F4EE8D7967243F5E91D5E6CA84812DDDC4689F03BCA49BDFBFF9C416DD9F1B99`.
- Scope: connect the already-approved FEAT-027 bounded VLM normalizer (`3565c94`) and the existing
  private schema-path diagnostics (`b9a8a07`) to the FEAT-018 Lightning `/v2/vision` live demo path;
  add one internal schema-repair generation at most; preserve the FEAT-003 V2 boundary and
  fail-closed validation.
- Approved behavior: the live route may perform at most two provider generations for one explicit
  user request, only when the first response fails output mapping/schema validation. This supersedes
  the earlier “no automatic provider retry” wording only for this bounded internal schema-repair
  transition; it does not authorize client retries, unbounded retries, ASR/video calls, production
  inference, or Codex-triggered Lightning requests.
- Privacy boundary: no raw model output, prompt, image bytes, narration, credentials, child data or
  raw exception text may be logged, persisted, committed or returned. Only closed diagnostics,
  attempt/repair state and existing provenance may be recorded.
- Contract boundary: no schema widening or version change is approved by this entry. Any necessary
  V2 contract migration requires a new approval. Existing strict adapter/test behavior remains
  unchanged outside the explicitly wired live demo construction.
- Verification boundary: owner manually runs Lightning smoke tests under the existing approximately
  25-credit ceiling after offline/API wiring passes. Codex must not call Lightning.

## Owner approval — topic quality and T2 activity matching fix — 2026-09-22

- Approver: project owner direct instruction in the current conversation: “approve and implement”.
- Approved plan: `features/FEAT-018-live-image-canvas-flow/plan/TOPIC_AND_T2_ACTIVITY_MATCHING_FIX_PLAN.md`.
- Plan SHA-256 at approval: `6B8D86DB14B03D476D81E6F677672E4F141F8141BF2FD8D6473CA5F1A3A54A32`.
- Approved behavior: improve grounded Vietnamese topic composition and deterministic claim ranking;
  trigger T2 from the Gate-A-confirmed JSON; resolve activity by reviewed exact phrase, alias,
  concept-family, or safe age-baseline fallback; expose fallback provenance; and never present the
  hardcoded butterfly/mock activity as a backend result.
- Approved scope: FEAT-018 supervised backend/application ports and catalog composition, BaoVC mobile
  workflow state/presentation, contract-compatible adapters/tests/evidence, Android Emulator demo,
  synthetic/non-child images, PixiJS handoff continuity, and future auth/save seams.
- Preserved boundaries: no FEAT-003 schema/adapter change, no video, no Codex-triggered Lightning
  call, no provider credentials in mobile, no durable child data, no arbitrary LLM-generated
  activities, and no contract V1 widening without a revised approval.
- Live execution boundary: owner alone performs any Lightning smoke test under the existing
  approximately 25-credit ceiling after offline/API/UI verification passes.
