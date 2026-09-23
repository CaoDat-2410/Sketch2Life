# Task approval

- Status: APPROVED (P1 implementation slice; FEAT-018 P2-T1 D2/D3-R2 with offline Cohorts A+B
  closed; completed P2-T2 offline contract/mapping and approved bounded-runner offline
  implementation; and approved offline P3/P4 slices integrated. P2-T3 optional narration planning
  remains a DRAFT and is not implementation-approved. P2-T2 live Lightning execution, P2-T4
  through P2-T5, provider, mobile/shared integration and production scope remain separately gated)
- Approver: Project owner direct instruction in the current conversation
- Plan revision: 2
- Requested scope: FEAT-018 revision 2 P1 implementation slice only: catalog promotion/provenance, Activity Template Library, adult context and deterministic eligibility, semantic-anchor to objective/template selection, ExperienceSpec compilation and fit validation, Gate B identity/version locking, catalog/pilot harness and feature-local evidence.
- Explicit exclusions: P2/P3/P4/shared implementation, production API/cloud, Runpod, Android release, real child/personal data, and mobile provider credentials.

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

## Owner approval and P2-T2 offline closure — 2026-09-12

The project owner approves the completed FEAT-018 P2-T2 offline implementation at commit
`11468d3a5a327697a491f09251a3210987337da0` (`fix(feat018): validate ASR correlation before mapping`).
Independent verification reported no blocker: the mapper now rejects supplied ASR results with a
mismatched correlation ID before Raw construction, while absent, matching-success and matching-
failure cases remain valid. Focused tests (17), related tests (801 passed, 5 skipped), ruff, mypy,
all repository validators and `git diff --check` passed. No model/GPU/Lightning/provider/network
execution occurred. This approval closes P2-T2 offline only; live execution and P2-T3 through P2-T5,
mobile, Gate A, P1 eligibility, P3/P4 and shared integration remain separately gated.

## Approved P2-T2 bounded-runner offline implementation addendum — 2026-09-14

The project owner approves the FEAT-018 P2-T2 bounded-runner offline implementation described in
`features/FEAT-018-live-image-canvas-flow/evidence/notes/P2_T2_BOUNDED_RUNNER_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT_20260914.md`
revision 5 (SHA-256 `f36216432620e21eba2fc2f3f0c735ace529d15f827ad957dcf9b5e74ab8c9e5`), following the
independent audit recorded at `tmp/feat018-p2-t2-revision5-independent-audit-20260914/REVIEW.md`
(verdict `PASS_WITH_FINDINGS`).

Approved exact file scope:

- `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py`
- `backend/tests/unit/test_feat018_live_lightning_execution.py`

No other file may be created or modified as part of this implementation stage.

Required corrections during implementation (the three MINOR findings from the independent audit):

1. Windows Job Object assignment must use a valid native process handle (for example via
   `ctypes`/`OpenProcess` with the required access rights), never a bare PID treated as a handle.
2. POSIX containment confirmation must use a bounded retry loop with an explicit timeout and must
   fail closed if group/session membership cannot be confirmed in time.
3. The stale internal cross-reference to the revision-3 section title ("Total adapter cap
   coordinator and bounded cleanup") must be corrected to the current section title ("Outer
   adapter-call supervisor and total adapter cap") in the approval package.

Offline-only gate: approved work uses injected fakes (fake clocks, fake process/containment
doubles, fake bounded transports) for every test. No model, provider, network, GPU, or Lightning
session may be used, loaded, or opened. `qwen_vision.py` and all other FEAT-003 source, FEAT-017,
contracts, registry, ports, routes, mobile code, Gate A UI, and P1/P3/P4/shared-integration scope
remain excluded and unchanged.

All twelve `P2T2-LIVE-D1` through `P2T2-LIVE-D12` decisions remain open; this approval is not a
live-execution approval. A separate, independent review of the completed implementation is
required before any future live-execution approval is considered.

Approved at: 2026-09-14, project owner direct instruction in the current conversation.

## Approved four-finding offline correction - 2026-09-14

Authority: the project owner's direct request to write a goal and execute fixes
for B1/B2/M1/N1 from the independent live-plan review. This addendum records
that request; it does not authorize a live run or resolve any live decision.

Acceptance is defined in the live execution plan, Section 2.5, "Four-finding
correction scope and acceptance". Correct the plan's claims about existing
primitives, define the remaining coordinator scope, separate D10 approval
inputs from runtime facts, and add the explicit live non-authorization marker.
Implement the evidence finalizer and precommit regression coverage only in:

- `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py`
- `backend/tests/unit/test_feat018_live_lightning_execution.py`

Documentation updates are limited to this approval record, the existing live
plan, FEAT-018 CONTEXT.md and DECISIONS.md, plus the ignored correction report.
No other code scope is allocated. Tests use offline injected dependencies;
no real subprocess, model, GPU, provider, network or Lightning execution.
The complete live coordinator remains explicitly incomplete and requires its
implementation and independent review before Stage 4. The historical reviewed
commit does not certify the changed code; a new independent review is required.
No commit, push, P2-T2 live closure, or D4 model acquisition is authorized.

Continuation of the same repair request includes the bounded worker mapper
handoff specified in live-plan Section 2.5, within those same source/test paths.
Reuse the unchanged FEAT-018 mapper inside the supervised worker and extend
terminal IPC only with a closed raw_status; retain the existing no-text and
deadline rules. Offline tests must exercise the real mapper and adapter with
fake generation. This records implementation authority for that correction,
not a new live approval or a claim that the entire coordinator is finished.

The continuing B1/B2 repair also implements the bounded metadata inventory and
sanitized incident primitive specified by Section 2.5 in the same two files,
with synthetic local filesystem tests. No actual model/cache/source inventory
is executed by this task; no other worktree is inspected. Future runtime roots
and incident destination remain subject to the separate live approval.

The same correction includes `finalize_smoke_run` orchestration of those
primitives and its offline integration tests as specified in Section 2.5.
No additional files or live execution are allocated.

## Approved four-finding finalization - 2026-09-15

The owner-approved safety invariant for evidence publication is single-writer
and quiescent-session: after cleanup succeeds, every supervised process and
descendant is absent, no runtime writer remains, and evidence finalization is
the sole authorized writer. The implementation rechecks the explicit inventory
after the Markdown rename and immediately before the authoritative JSON rename.
This closes the ordinary mutation window under that invariant; it does not claim
filesystem-wide atomicity or protection from an unrelated hostile external writer.

Incident fallback is constrained to the exact relative destination
`tmp/feat018-live-lightning-incident-<run_id>/INCIDENT.md`. The writer validates
the bounded opaque run ID, exact filename and run-directory match, repository
containment, traversal absence, and symlink/reparse safety. The future
coordinator/preflight must explicitly supply `git_ignored=True`; the primitive
does not infer Git state and rejects tracked, publishable, arbitrary absolute,
traversal and mismatched-run destinations. Payload bytes remain fixed and
sanitized, with no paths, exceptions, secrets or provider data.

The synthetic session ID is supplied in adapter-worker bootstrap arguments and
may be serialized by spawn multiprocessing. It is bounded, opaque and
non-secret, and is excluded from progress/event IPC and evidence payload bodies;
the approval does not claim that it never crosses a process boundary. The
current focused total is 196 passed. The earlier 170-test figure is an
intermediate historical checkpoint only. D1, D4 and D11 remain BLOCKED, Stage 4
has not started, and the exact `NOT A LIVE EXECUTION AUTHORIZATION` marker is
preserved. No live subprocess, model, GPU, provider, network, Lightning session,
 model acquisition or Stage 4 action is authorized.

## Approved exact two-file offline coordinator implementation - 2026-09-15

Authorization marker:
`APPROVED_FOR_EXACT_TWO_FILE_OFFLINE_COORDINATOR_IMPLEMENTATION_ONLY`

The project owner authorizes offline implementation and regression testing only
in these exact files:

- `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py`
- `backend/tests/unit/test_feat018_live_lightning_execution.py`

This approval permits FEAT-018 P2-T2 coordinator remediation, including the B3
host-enforceable timeout correction, using injected offline fakes and killable
test workers only. It does not authorize Lightning, GPU, model, provider,
network, production, Stage 4, D4 snapshot acquisition, or live execution.
FEAT-003, FEAT-017, contracts, routes, registries, mobile, Gate A, P1/P3/P4,
shared integration, published evidence, and all other files remain out of scope.

D1-D12 remain unresolved for live approval. An independent review is required
after implementation and offline validation. No commit or push is implied by
this approval.

## Approved FEAT-018 POSIX CI workflow — 2026-09-16

The project owner authorizes adding exactly one CI workflow:

- `.github/workflows/feat018-posix.yml`

The workflow may run only on Ubuntu/Linux and only execute the synthetic FEAT-018 POSIX process-group cleanup test.

Ordinary GitHub Actions control-plane operations, including checkout and dependency installation required to provision the existing backend project environment, are permitted only for CI setup. The FEAT-018 test and application code must perform no external network, provider, model, download, or live-service activity.

No application code, tests, contracts, plans, evidence, or other worktrees may be changed by this task. The workflow must remain bounded and fail if the POSIX test is skipped.

The workflow is limited to:

- push events for `feature/feat018-p2t2-live-lightning`;
- manual `workflow_dispatch`;
- an Ubuntu/Linux runner;
- existing backend project configuration;
- the approved POSIX process-group cleanup test only;
- bounded logs and explicit failure when the test is skipped.

This approval does not authorize:

- Lightning, GPU, model, provider, network, or live benchmark execution;
- Stage 4, D1-D12, or D4;
- production use, deployment, merge, or cutover;
- any application commit or push.

No commit or push is authorized by this addendum.

## Owner binding of reviewed FEAT-018 P2-T2 runtime source — 2026-09-16

The project owner binds `reviewed_runtime_code_commit` to:

`9549a341194f40b1a9be419d6fce0d70f1ca0384`

This binding identifies the exact reviewed FEAT-018 P2-T2 runner/coordinator
source and test blobs only. It does not resolve D4, does not resolve all
D1-D12, and does not authorize Lightning, GPU, model, provider, network, or
Stage 4 execution. The binding does not alter the existing exact-file scope,
does not approve any FEAT-003/FEAT-017 change, and does not authorize a commit
or push by itself.

## Owner approval of FEAT-018 P2-T2 pre-staged local snapshot - 2026-09-17

The project owner approves `PRESTAGED_LOCAL_SNAPSHOT` for `P2T2-LIVE-D4` with
the following exact identity:

- Model: `Qwen/Qwen3-VL-8B-Instruct`
- Revision: `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`
- Logical snapshot: `qwen3-vl-8b-instruct`
- Sanitized manifest SHA-256: `8a1d50d6aef809130acd7b05b71369cccbb2360192b157f7871de2bd40c43eaf`
- Manifest file count: `16`
- Indexed safetensors shard count: `4`
- Runtime setting: `allow_model_download=false`
- Observed Lightning device fact: NVIDIA L4, `23034` MiB VRAM; this observation does not resolve D10 approval inputs.

This approval closes D4 snapshot readiness only. It does not authorize model
loading, Lightning inference, provider or network execution, Stage 4,
production use, or any change to the remaining D1-D12 decisions. D1 and D11
remain pending, and a separate Stage 4 approval resolving all live decisions
is required before any FEAT-018 live smoke.

## Owner recording of FEAT-018 P2-T2 D6 sub-decisions - 2026-09-18

Approver: Project owner direct instruction in the current conversation.

The project owner records the following two `P2T2-LIVE-D6` sub-decisions,
after the fifth independent binding review of the live-Lightning plan
returned `PASS`:

`P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE` =
`SELECTED_PENDING_SEPARATE_IMPLEMENTATION_AND_REVIEW`. This selects a policy
direction only, not a concrete implementation: the future validator must
accept image-only input, must never fabricate or accept a placeholder audio
input, and is not the existing `DeterministicMediaValidator` (which requires
audio and is disqualified for this image-only smoke). No validator module,
class, function, or Git blob is named or approved by this record. This
sub-decision becomes `RESOLVED` only after a separate implementation
approval defines the validator/result contract and its provenance
serialization/hash rule, its exact identity is recorded, focused offline
tests exist and pass, and an independent review of that implementation
returns without a blocking finding. `P2T2-LIVE-D6` overall remains
`NOT FINALLY RESOLVED` until then.

`P2T2-LIVE-D6.MIME_EXTENSION_RULE` = `RESOLVED: REMOVE_REQUIREMENT`. The live
path makes no MIME/extension-agreement claim. `image_admission_evaluation.py`
(including `validate_cohort_b_source` and `load_cohort_b_manifest`) and the
offline Cohort B tooling remain outside the live path and are not added.
D2 admission's responsibilities are unchanged: bounded decode,
container/codec/pixel-format checks, and source/staged digest equality.
B01.jpg's MIME/extension remains owner-reviewed metadata only. No
MIME/extension enforcer is added by this record.

This is a documentation/governance record only. It does not implement or
test any media validator, does not finally resolve `P2T2-LIVE-D6`, does not
bind any `P2T2-LIVE-D11.LIVE_SEAM_BINDING` seam, does not select or change
D1/D2/D3/D4/D5/D7-D12, and does not create a Stage 4 approval. D1 and D11
remain `BLOCKED`, Stage 4 remains `NOT READY`, and Lightning/model/GPU/
provider/network execution remains `NOT AUTHORIZED`. The recorded files are
the live-Lightning plan, `CONTEXT.md`, `DECISIONS.md`, and this approval
record; no source, test, evidence, P2-T4, or P2-T5 file changed. The next
gate is a separate owner approval authorizing the image-only
media-validation implementation, followed by its independent review.

## Approved exact four-file offline image-only validator implementation — 2026-09-19

Approver: Project owner direct instruction in the current conversation.

`APPROVED_FOR_EXACT_FOUR_FILE_OFFLINE_IMAGE_ONLY_VALIDATOR_IMPLEMENTATION_ONLY`

The project owner approves Design A for offline implementation and focused
offline tests only. The implementation may modify only these four files:

- `backend/src/sketch2life/contracts/schemas/media_validation.py`
- `backend/src/sketch2life/application/services/media_validation.py`
- `backend/src/sketch2life/domain/understanding/media_quality.py`
- `backend/tests/unit/test_media_validation.py`

The existing D2 decoder port and implementation, pure D2 structural policy,
D2 application service, D2 tests, and dependency metadata remain read-only.
The implementation may reuse the D2 decoder interfaces and pure policy facts,
but must not modify D2 source, API, behavior, or tests and must not depend on
`Feat018ImageAdmission` as an application service. If Design A requires any
additional writable path, implementation must stop with
`DESIGN_A_INSUFFICIENT` / `BLOCKED_PENDING_SCOPE_DECISION`.

No committed fixture is approved. Deterministic JPEG and PNG inputs must be
generated in memory in the approved test file. The image-only path has no
audio, fabricated audio, `staged_sha256`, MIME/extension enforcement,
subjective quality claim, model execution, GPU, provider, network, Lightning,
or live-smoke behavior.

This addendum does not authorize D11, staging, filesystem/evidence publication,
Stage 4, live execution, production use, or any commit or push. D6 remains
`SELECTED_PENDING_SEPARATE_IMPLEMENTATION_AND_REVIEW` and is not finally
resolved until the bounded implementation passes focused offline validation,
independent review, and exact identity/provenance binding. D1 and D11 remain
`BLOCKED`, and Stage 4 remains `NOT READY`.

## Separate security-fixture hygiene addendum - 2026-09-20

Approver: Project owner direct instruction in the current conversation.

This is a separate governance addendum for the currently blocked hygiene gate.
It records a hygiene decision only. It does not implement the exemption, change
the security validator, change test fixtures, or rerun the blocked validation
matrix.

### A. Four-file implementation approval

- Owner decision: already approved.
- Repository marker: already recorded exactly once in this approval record.
- Scope: the exact four-file offline implementation only:
  `backend/src/sketch2life/contracts/schemas/media_validation.py`,
  `backend/src/sketch2life/application/services/media_validation.py`,
  `backend/src/sketch2life/domain/understanding/media_quality.py`, and
  `backend/tests/unit/test_media_validation.py`.
- This hygiene addendum does not replace, duplicate, broaden, or alter that
  existing marker or its surrounding approval text.

### B. Security-fixture hygiene decision

- Owner decision: Route A is approved separately.
- This is a new hygiene authorization and is not part of the original four-file
  marker.
- `HYGIENE_ROUTE = A_NARROW_SECURITY_VALIDATOR_EXEMPTION`
- The authorization is for a future, narrowly machine-checkable correction only;
  no correction is implemented by this record.

### New writable hygiene scope

The only newly authorized hygiene target is:

- `tools/validate_repository_security.py`

The test file may be changed only if an explicit synthetic-fixture marker is
required, and only at:

- `backend/tests/unit/test_media_validation.py`

No other file is authorized by this hygiene addendum. The following remain
outside scope: all other source files; runtime files; configuration files;
`.env` files; provider credentials; real API keys; real access tokens;
passwords; private keys; service-account files; production data; D2
decoder/policy files; FEAT-003 files; Qwen/runner/mapper/coordinator files;
plans, context, decisions, evidence, and runtime integration files.

### Exemption precision

Any future exemption must be narrowly machine-checkable and constrained by all
of the following:

- the exact relative file path;
- the exact security rule/category; and
- the exact explicitly marked synthetic-fixture block.

The exemption must not be a path-wide ignore for the entire test file, a
repository-wide test exemption, a broad regex suppression, an ignore for all
token/secret/private-key strings, an ignore for runtime or configuration files,
or a general suppression of the security validator. All unmarked findings in
the test file must continue to fail the security validator.

### Fixture integrity

The synthetic fixtures exist to prove that unsafe references are rejected and
sanitized. Future hygiene work must preserve coverage for token-like,
secret-like, credential-like, and private-key-like references; malformed
references; structured diagnostic sanitization; parser-level sanitization; and
direct mapping sanitization.

The future implementation must not concatenate strings merely to evade scanner
detection, encode or obfuscate strings merely to evade scanner detection,
rename fixtures to hide their security meaning, replace all sensitive-looking
cases with harmless values, remove privacy assertions, or weaken the
negative-test matrix. If a marker is required, it must identify synthetic test
data explicitly and narrowly while preserving the actual test semantics.

### Strict-mypy correction authorization

This addendum may also authorize the related typing-only correction at
`backend/src/sketch2life/contracts/schemas/media_validation.py:284`. The
correction must preserve `hide_input_in_errors=True`; the expected direction is
to express the option through a typing-safe `ConfigDict` declaration instead of
mutating a `TypedDict` through an unsupported update call. This authorization
does not permit semantic result-contract changes, privacy weakening, or scope
expansion beyond the approved hygiene files.

### Exemption versus waiver

If the narrow exemption is implemented and the validator exits successfully,
the result is:

`REPOSITORY_SECURITY_VALIDATOR = PASS`

If the owner accepts the current finding without changing the validator, the
result must instead be:

`REPOSITORY_SECURITY_VALIDATOR = FAIL_WITH_EXPLICIT_OWNER_WAIVER`

A waiver must never be labeled as technical validator `PASS`. A waiver does
not authorize live execution, Stage 4, D11, model/GPU/provider/network
activity, commit, or push.

### Required future validation

After the hygiene correction is separately implemented, run strict mypy on
changed source files; the repository security validator; Ruff on all four
applied Python files; focused `test_media_validation.py`; D2 image-admission
regression tests; the harness validator; the skeleton validator; the
architecture validator; and `git diff --check`.

Known baselines must remain separately classified and must not hide new
failures:

- three semantic-catalog failures caused by the missing file
  `backend/data/activity-catalog/golden/v1/semantic-anchor-profiles.v1.json`;
- the unchanged architecture violation in
  `backend/src/sketch2life/application/services/backend_ai_workflow.py`.

### Governance and runtime limits

This addendum does not authorize model download or loading, GPU use, provider
calls, network calls, Lightning sessions, live inference, Stage 4, D11
resolution, D6 final resolution, production use, migration or cutover,
evidence publication, routes, registries, ports, integrations, commit, or push.
It authorizes only the future narrow hygiene correction and its offline
validation.

Recorded state:

`FOUR_FILE_IMPLEMENTATION_APPROVAL = ALREADY_RECORDED`

`HYGIENE_APPROVAL = RECORDED`

`SECURITY_VALIDATOR_CORRECTION = AUTHORIZED_PENDING_IMPLEMENTATION`

`STRICT_MYPY_CORRECTION = AUTHORIZED_PENDING_IMPLEMENTATION`

`FOUR_FILE_IMPLEMENTATION = APPLIED_UNCOMMITTED`

`COMMIT_READY = NO`

`D6 = NOT FINALLY RESOLVED`

`D11 = BLOCKED`

`STAGE_4 = NOT READY`

`LIVE/MODEL/GPU/PROVIDER/NETWORK/LIGHTNING = NOT AUTHORIZED`

`NEXT = IMPLEMENT_NARROW_HYGIENE_CORRECTION`

## Owner binding of FEAT-018 P2-T2 D6 image-only media-validation source - 2026-09-20

Approver: Project owner direct instruction in the current conversation.

The D6 binding package independent review returned `PASS`:

`D6_BINDING_REVIEW = PASS`

`D6_OWNER_DECISION = RECORDED`

`D6_BINDING_PACKAGE = OWNER_APPROVED`

The project owner approves binding `D6.MEDIA_VALIDATION_SOURCE` and
`P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE` to the exact committed FEAT-018
image-only validator at commit:

`16c52da26c444947ab4388712d9b7310480360b4`

The exact binding identities are:

- Contract: `ImageOnlyValidationResultV1@1.0`
- Validator: `feat018-image-only-structural-validator-v1`
- Policy: `feat018-image-only-structural-policy-v1`

The accepted artifact-reference grammar is exactly:

- `fixture-b[0-9]{2}`
- `fixture:drawing:v[0-9]+`
- `fixture:small-dark-drawing:v[0-9]+`
- `fixture:corrupt-drawing:v[0-9]+`
- `fixture:rejected-reference:v1`

This grammar syntactically permits `fixture-b00` through `fixture-b99`. It
does not assert that every such fixture exists, that every such fixture was
owner-reviewed, or that every such fixture is independently authorized for a
live run. Fixture existence, identity, and authorization remain separate
run-specific gates.

The owner records:

`D6.MEDIA_VALIDATION_SOURCE = RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR`

`P2T2-LIVE-D6.MEDIA_VALIDATION_SOURCE = RESOLVED: EXACT_COMMITTED_IMAGE_ONLY_VALIDATOR`

`D6.MIME_EXTENSION_RULE = RESOLVED: REMOVE_REQUIREMENT`

This resolves only the D6 media-validation-source binding. It does not resolve
D11 or authorize Stage 4. D6 overall remains `NOT FINALLY RESOLVED` while the
fixture identity remains `RESOLVED_WITH_PROPOSED_VALUE`.

Before Stage 4:

`D4 snapshot/readiness/identity = RESOLVED_FOR_RUNTIME_REVALIDATION`

D4 runtime/session-local revalidation remains Stage-4-local and may occur only
after an authorized session reaches `SESSION_READY`. The lifecycle is:

```text
Stage-4 approval
-> provision session
-> SESSION_READY
-> D4 runtime/session-local revalidation
-> D8 staging and staged digest verification
-> exactly one smoke
```

D4 runtime/session-local revalidation is not required before Stage 4 approval.

CI run `35500484772` proves only that the `feat018-posix` process-group
cleanup workflow passed for commit `16c52da`. It must not be described as full
validator CI or full repository validation.

This addendum does not resolve D11, authorize Stage 4, or authorize Lightning,
model loading, model inference, GPU use, provider calls, network calls,
adapter invocation, or live execution. It does not authorize a commit or push.

`D11 = BLOCKED`

`STAGE_4 = NOT READY`

`LIVE/MODEL/GPU/PROVIDER/NETWORK/LIGHTNING = NOT AUTHORIZED`

`NEXT = INDEPENDENT_REVIEW_OF_D6_GOVERNANCE_COMMIT`

## Owner approval for FEAT-018 P2-T2 D9 stdout/stderr enforcement implementation scope - 2026-09-21

Approver: Project owner direct instruction in the current conversation.

The D9 implementation-approval package was independently reviewed with verdict
`PASS` and is ready for this bounded owner approval record:

`features/FEAT-018-live-image-canvas-flow/evidence/notes/P2_T2_D9_STDOUT_STDERR_ENFORCEMENT_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT_20260921.md`

The owner selects the exact positive stream ceilings:

`stdout_max_bytes = 16384`

`stderr_max_bytes = 32768`

The ceilings are owner policy values, not values inferred from runtime
observation. They apply cumulatively to raw bytes for each captured
process/stream observation. The outer adapter worker and inner generation child
are captured separately; stdout and stderr are counted independently; exactly
the configured ceiling is accepted; the first byte beyond it is overflow; and
raw bytes are capture-and-discard only, before any UTF-8 or binary decoding.

The only authorized implementation paths are exactly:

- `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py`
- `backend/tests/unit/test_feat018_live_lightning_execution.py`

The source path may receive the bounded outer/inner capture boundaries,
raw-byte accounting, typed D9 observations/failures, metadata-only bounded IPC
handoff, finalization/cleanup wiring, cardinality preservation, and sanitized
result propagation. The test path may receive only offline injected/fake tests
for the D9 byte, lifecycle, privacy, cleanup, cardinality, POSIX, and Windows
seams.

No other path is authorized. In particular, this addendum does not authorize
fixtures, versioned contracts or schemas, `pyproject.toml`, lockfiles,
workflows, environment files, provider/dependency configuration,
`qwen_vision.py`, FEAT-003, D6, D10, D11 concrete seams, plans, context,
decisions, validators, routes, registries, evidence destinations, worktrees,
stashes, branches, or any Stage-4 artifact.

Implementation remains gated until the approval record itself receives an
independent review with verdict `PASS`:

`D9_IMPLEMENTATION_APPROVAL_RECORD = RECORDED`

`D9_IMPLEMENTATION = NOT_AUTHORIZED_UNTIL_INDEPENDENT_APPROVAL_RECORD_REVIEW_PASS`

The implementation must preserve the approved fail-closed contract: bounded
capture-and-discard at both child boundaries; raw-byte accounting before
decoding; typed limit/read/late/death/finalization failures; bounded
metadata-only handoff; deterministic capture -> stop/close -> drain ->
finalize -> publish -> reject-late ordering; exactly one cleanup sequence; no
raw stream or diagnostic leakage; truthful adapter/attempt cardinality; and no
D9-created retry, outer retry, third attempt, second adapter call, or second
session.

The following remain unresolved or blocked:

`D9 = BLOCKED_PENDING_D11_AND_CONTRACT_REVIEW`

`D11 = BLOCKED`

`D1 = BLOCKED_BY_D11`

`STAGE_4 = NOT READY`

`LIVE/MODEL/GPU/PROVIDER/NETWORK/LIGHTNING = NOT AUTHORIZED`

This addendum does not authorize D11 implementation or resolution, Stage 4,
Lightning provisioning, model loading, inference, GPU use, provider/network
access, adapter invocation, commit, push, or live execution. After the required
independent approval-record review passes, a separate implementation goal may
begin within the exact two-file scope only.

## Owner transition and conditional D1/D6 prerequisite commit approval - 2026-09-23

Approver: Project owner, by direct instruction in the current conversation,
"Complete D1/D6 Prerequisite Governance and Approval", dated 2026-09-23.
Recorded by: Codex at 2026-09-23 05:52:09 UTC.
Instruction SHA-256:
`8a1663664625561fc4f952850dd8d48be7f5da1d06080bcb7fde5d2491721243`.
Plan/scope revision: `P2T2-D1D6-PREREQUISITE-R1`, defined in this addendum.
Baseline branch: `feature/feat018-p2t2-live-lightning`.
Baseline HEAD: `86836d24cfcd83ca14c0bc50e79fff1103cb9ecc`; index empty.

### Historical review lineage and current transition

The owner preserves the preceding 2026-09-20 D6 approval and its
`NEXT = INDEPENDENT_REVIEW_OF_D6_GOVERNANCE_COMMIT` text unchanged as
historical provenance. That NEXT described the gate at the time of the
validator-source binding; it is satisfied and is not the current global gate.

The completed review/correction lineage is:

- `tmp/feat018-p2t2-d6-governance-independent-review-20260920/REVIEW.md`:
  reviewed the D6 governance commits and identified stale NEXT markers (F-001).
- `tmp/feat018-p2t2-next-gate-correction-20260920/REPORT.md`:
  recorded the F-001 current-marker synchronization.
- `tmp/feat018-p2t2-f002-next-prose-correction-20260920/REPORT.md`:
  recorded the five F-002 current-sequence prose corrections.
- `tmp/feat018-p2t2-d6-governance-independent-review-rerun-20260920/REVIEW.md`:
  returned `PASS` for that historical review/correction sequence and permitted
  owner-resolution package preparation, without resolving execution gates.

The later prerequisite boundary review
(`tmp/feat018-p2t2-d1-d6-prerequisite-commit-boundary-review-20260923/REPORT.md`)
found that the old approval NEXT remained in the actual file and that O-01
still stated an unqualified old sequence. This new owner decision disposes
of those discrepancies prospectively; it does not rewrite history or claim
that the previously reported approval-marker edit was present.

The owner now records the completed D6 review as moving the global/current
NEXT to:

```text
NEXT = PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING
```

The live plan's Section 11 `CURRENT` remains the sole canonical current-state
block. This approval records that same gate; it does not establish a competing
sequence. Preparation and exact fixture binding remain pending activities,
not completed D1/D6 resolutions. The independent prerequisite review below is
a package-local commit gate and does not replace or satisfy the global NEXT.

### Exact authorized documentation scope and preparation plan

`D1_D6_PREREQUISITE_PREPARATION = APPROVED`

Only the following five tracked paths and thirteen semantic hunks belong to
the future prerequisite candidate. All paths are under
`features/FEAT-018-live-image-canvas-flow/`.

| Path | Authorized candidate changes |
|---|---|
| `CONTEXT.md` | Existing global NEXT replacement only |
| `DECISIONS.md` | Existing D6-entry NEXT replacement only |
| `plan/P2_T2_LIVE_LIGHTNING_EXECUTION_PLAN_DRAFT_20260913.md` | Existing current execution sequence, update-history items 3 and 8, Stage-3 table NEXT, Section 11 CURRENT NEXT, first THEN action, Section 12.6 NEXT; plus the explicit O-01 historical qualification |
| `evidence/notes/P2_T2_D6_MEDIA_VALIDATION_BINDING_PACKAGE_DRAFT_20260920.md` | Existing top and final NEXT replacements only |
| `approvals/TASK_APPROVAL.md` | This additive transition/approval record only; all preceding text is preserved |

The eleven existing synchronization hunks are the prior boundary report's
context-U01, decisions-U01, plan-U04/U05/U06/U12/U14/U16/U17, and d6-U01/U02.
The plan's pre-D9 snapshot is blob
`c80e1299c19472f8ba6d8d9933504faf20761cfe`. Its "current Section 12.6"
pointer belongs in the prerequisite-only candidate, which has no D9 Section
12.7. The later D9-owned "historical Section 12.6" pointer remains preserved
in the working tree and excluded from the prerequisite candidate.

O-01 is the three-line stale sequence at baseline HEAD plan lines 2835-2837
(entry working-tree lines 2963-2965). The authorized correction explicitly
labels the old D6 governance-review sequence historical/satisfied, points to
Section 11 `CURRENT` as the sole canonical current gate, and preserves D11
binding/resolution as downstream unresolved work. No unrelated plan meaning
may change.

Preparation records this approval first, then corrects only O-01 in the
working plan, reconstructs the five-file candidate in memory from HEAD plus
the exact scope above, runs the required checks, and records its exact blobs
and deterministic recipe. All current D9 working-tree content is preserved.
The untracked D1 owner-resolution package, D9 reconciliation note, every
D9-only delta, and every other path are excluded from the future commit.
The separately permitted feature-local preparation evidence note and ignored
report are review support only and are not added to this five-file candidate.

Acceptance criteria for revision `P2T2-D1D6-PREREQUISITE-R1`:

1. Preserve historical approval bytes; the new attributable record and all
   candidate current markers agree on the preparation NEXT.
2. O-01 is explicitly historical/satisfied and cannot be read as the current
   gate; Section 11 `CURRENT` remains canonical.
3. Reproduce exact candidate blobs from HEAD plus only the thirteen semantic
   hunks above, with no D1 package or D9-only additions.
4. Preserve the protected states below, the existing runtime binding, all
   unrelated working-tree content, HEAD, and the empty index.
5. Run harness, repository-security, skeleton and architecture validators plus
   both working-tree/cached diff checks; architecture may retain only the
   unchanged `backend_ai_workflow.py` outer-layer finding.
6. Obtain a fresh independent review of this exact scope, approval record,
   candidate contents/identities, consistency and preservation with verdict
   `PASS` before any staging or commit.

### Conditional commit authorization and limits

The owner authorizes the exact prerequisite candidate to be staged and
committed only after that fresh independent review returns `PASS`. Earlier
D6/D9 reviews and authoring checks do not satisfy this new gate. Any change
to the reviewed candidate or baseline requires revalidation and a fresh
independent PASS; scope expansion requires separate owner authorization.

Proposed future commit message:

```text
docs(feat018): synchronize D1/D6 preparation gate
```

At recording time:

```text
D1_D6_PREREQUISITE_SCOPE = OWNER_AUTHORIZED_CONDITIONAL_ON_FRESH_INDEPENDENT_PASS
D1_D6_PREREQUISITE_INDEPENDENT_REVIEW = PENDING
D1_D6_PREREQUISITE_STAGING_AND_COMMIT = NOT_PERMITTED_BEFORE_FRESH_INDEPENDENT_PASS
PUSH = NOT_AUTHORIZED
```

This preparation task performs no staging or commit. This approval does not
authorize push, D9 publication, source/tests, fixtures, contracts, dependencies,
workflows, branch/worktree/stash/remote changes, or any runtime activity.
It does not resolve D1, D6 fixture identity, D11, Stage 4 or live execution:

```text
D1 = BLOCKED_BY_D11
D6 = NOT FINALLY RESOLVED; FIXTURE IDENTITY = RESOLVED_WITH_PROPOSED_VALUE
D11 = BLOCKED
STAGE_4 = NOT READY
LIVE/MODEL/GPU/PROVIDER/NETWORK/LIGHTNING = NOT AUTHORIZED
reviewed_runtime_code_commit = 9549a341194f40b1a9be419d6fce0d70f1ca0384
```

D6 media-validation-source and MIME/extension decisions remain as previously
owner-bound. No D9 numeric value, enforcement, carrier or live status changes.

## Owner scope amendment for plan update-history item 7 (B-03) - 2026-09-23

Approver: Project owner, by direct instruction in the current conversation,
"Correct the FEAT-018 D1/D6 prerequisite-governance package after independent
review REVIEW_2.md", dated 2026-09-23.
Recorded by: Claude Code (Claude Opus 5.5) at 2026-09-23 07:50:28 UTC.
Instruction SHA-256 (UTF-8 text, LF line endings, no trailing newline):
`bd3f37d20a599b0d555d7ab83fedaf293b6c52c0a97d8b4f00e8d691ad67f400`.
Plan/scope revision: `P2T2-D1D6-PREREQUISITE-R2`, amending revision
`P2T2-D1D6-PREREQUISITE-R1` recorded in the preceding addendum.
Baseline branch: `feature/feat018-p2t2-live-lightning`.
Baseline HEAD: `86836d24cfcd83ca14c0bc50e79fff1103cb9ecc`; index empty.

### Reason for the amendment

The second fresh independent review of the R1 candidate,
`tmp/feat018-p2t2-d1-d6-prerequisite-independent-review-20260923/REVIEW_2.md`,
returned `BLOCKED`. Its finding B-03 identified that live-plan update-history
item 7 still stated the 2026-09-18 next gate in the present tense and called
the Section 12.5 entry "current". That contradicts the Section 12 preamble,
the Section 12.5 `HISTORICAL (SUPERSEDED)` heading, item 3 and item 8. Its
findings B-01 and B-02 concern only the non-candidate supporting note and
the ignored preparation report; they do not change the candidate scope.
The review reports `REVIEW.md` and `REVIEW_2.md` are preserved unchanged.

### Amended exact candidate scope

The owner authorizes exactly one additional candidate hunk:

- `plan-I07`: in live-plan update-history item 7 (baseline HEAD plan lines
  166-168), qualify the 2026-09-18 next gate and the Section 12.5 reference
  as historical ("at that time"), state that they are not the present gate
  or the current validation record, and state that the later item 8 records
  the subsequent state. The historical facts of item 7 are preserved and no
  other plan meaning changes.

The candidate remains exactly the same five tracked paths under
`features/FEAT-018-live-image-canvas-flow/` (`CONTEXT.md`, `DECISIONS.md`,
`plan/P2_T2_LIVE_LIGHTNING_EXECUTION_PLAN_DRAFT_20260913.md`,
`evidence/notes/P2_T2_D6_MEDIA_VALIDATION_BINDING_PACKAGE_DRAFT_20260920.md`
and `approvals/TASK_APPROVAL.md`). It now has exactly fourteen semantic
hunks:

1. the eleven existing synchronization hunks context-U01, decisions-U01,
   plan-U04/U05/U06/U12/U14/U16/U17 and d6-U01/U02;
2. the plan-O01 historical qualification;
3. the plan-I07 historical qualification authorized here;
4. approval-ADD01, the additive approval text appended after the historical
   prefix of this file. It now consists of the R1 addendum and this R2
   amendment as one contiguous appended block; every earlier byte is
   preserved.

In the R1 scope table, the plan row gains only plan-I07. The R1 addendum is
preserved unchanged as historical provenance. Where it says "thirteen
semantic hunks" or defines the candidate by revision R1, this amendment
supersedes it for the current candidate. No other scope expansion is
authorized. In particular, the dated 2026-09-18 wording in `CONTEXT.md`
noted as observation O-02 in `REVIEW_2.md` is not changed by this amendment.
The D1 package, the D9 reconciliation note, every D9-only delta, the
supporting preparation note, the ignored reports and every other path remain
excluded.

### Amended acceptance criteria for revision `P2T2-D1D6-PREREQUISITE-R2`

1. Preserve historical approval bytes, including the complete R1 addendum;
   the attributable records and all candidate current markers agree on
   `NEXT = PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING`.
2. O-01 and item 7 are explicitly historical and cannot be read as the
   current gate or current validation record; Section 11 `CURRENT` remains
   canonical.
3. Reproduce exact candidate blobs from HEAD plus only the fourteen semantic
   hunks above, using a recipe that yields them when applied literally, with
   no D1 package or D9-only additions.
4. Preserve the protected states below, the existing runtime binding, all
   unrelated working-tree content, HEAD, and the empty index.
5. Run harness, repository-security, skeleton and architecture validators plus
   both working-tree/cached diff checks; architecture may retain only the
   unchanged `backend_ai_workflow.py` outer-layer finding.
6. Obtain a new fresh independent review of this exact R2 scope, approval
   record, candidate contents/identities, consistency and preservation, in a
   session separate from the authoring session and written to a new report
   filename, with verdict `PASS` before any staging or commit.

### Conditional commit authorization and limits

The R2 candidate remains conditional. It may be staged and committed only
after the new fresh independent review returns `PASS`. `REVIEW.md`,
`REVIEW_2.md`, earlier D6/D9 reviews and authoring checks do not satisfy this
gate. Any change to the reviewed candidate or baseline requires revalidation
and a fresh independent PASS; scope expansion requires separate owner
authorization.

At recording time:

```text
D1_D6_PREREQUISITE_SCOPE = OWNER_AUTHORIZED_R2_CONDITIONAL_ON_FRESH_INDEPENDENT_PASS
D1_D6_PREREQUISITE_INDEPENDENT_REVIEW = PENDING
D1_D6_PREREQUISITE_STAGING_AND_COMMIT = NOT_PERMITTED_BEFORE_FRESH_INDEPENDENT_PASS
PUSH = NOT_AUTHORIZED
```

This amendment performs no staging or commit and authorizes no push, D9
publication, source/tests, fixtures, contracts, dependencies, workflows,
branch/worktree/stash/remote changes, or any runtime activity. It does not
resolve D1, D6 fixture identity, D11, Stage 4 or live execution:

```text
D1 = BLOCKED_BY_D11
D6 = NOT FINALLY RESOLVED; FIXTURE IDENTITY = RESOLVED_WITH_PROPOSED_VALUE
D11 = BLOCKED
STAGE_4 = NOT READY
LIVE/MODEL/GPU/PROVIDER/NETWORK/LIGHTNING = NOT AUTHORIZED
NEXT = PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING
reviewed_runtime_code_commit = 9549a341194f40b1a9be419d6fce0d70f1ca0384
```

## Owner scoped push authorization for the D1/D6 prerequisite commit - 2026-09-23

Approver: Project owner, by direct instruction in the current conversation,
"Safely commit and publish the reviewed FEAT-018 D1/D6 prerequisite package",
dated 2026-09-23.
Recorded by: Claude Code (Claude Opus 5.5) at 2026-09-23 12:50:07 UTC.
Verbatim authorization clause from that instruction:

> The owner authorizes one normal, non-force push to
> `origin/feature/feat018-p2t2-live-lightning` of only the commits described
> below. This supersedes the prior `PUSH = NOT_AUTHORIZED` only for this branch
> and operation.

This entry is additive. The R1 addendum, the R2 amendment and every earlier
byte of this file are preserved unchanged.

### Basis

The R2 condition for staging and commit was met: the new fresh independent
review of the exact R2 candidate,
`tmp/feat018-p2t2-d1-d6-prerequisite-independent-review-20260923/REVIEW_3.md`,
returned `PASS`. The exact staged R2 candidate was then committed as:

- `62d132ea3b0013e4c3ef72350990b18a6ce41a1f`
  `docs(feat018): synchronize D1/D6 preparation gate`; parent
  `86836d24cfcd83ca14c0bc50e79fff1103cb9ecc`; exactly five paths and fourteen
  semantic hunks, with blobs `CONTEXT.md` `f4b9e9e10a027e18426b334c60f4d34e33604255`,
  `DECISIONS.md` `63dbca5e6f91757191315ef2004c13bcebfbe79c`, live plan
  `5485f60957cee77beee93ebb85e20d57bc4c1ffc`, D6 package
  `b80e4d4d5e565f575155c7e31787a4f6b4c0ddf2` and `TASK_APPROVAL.md`
  `e091c923f70a4d6a919e7eed5059b8bad896c5bd`.

### Exact push scope

The owner authorizes exactly one normal, non-force, fast-forward push to
`origin` branch `feature/feat018-p2t2-live-lightning`, whose remote value
before the push must be `86836d24cfcd83ca14c0bc50e79fff1103cb9ecc`. The push
may publish only these two commits:

1. the prerequisite commit `62d132ea3b0013e4c3ef72350990b18a6ce41a1f`;
2. the approval-record follow-up commit that adds only this entry, subject
   `docs(feat018): authorize scoped prerequisite push`, whose parent is the
   prerequisite commit.

The push must not use force, tags or any other ref, and must not be preceded
by fetch, rebase, merge or reconciliation. If the remote rejects the push or
has diverged, the operation stops without retry or reconciliation.

This authorization does not publish or approve the remaining D9 worktree
changes, the untracked D1 package, the D9 reconciliation note, the supporting
preparation note, the owner commit-readiness note or the ignored reports. It
authorizes no other push, branch/worktree/stash/remote change, source/tests,
fixtures, contracts, dependencies, workflows, or runtime activity.

At recording time:

```text
D1_D6_PREREQUISITE_INDEPENDENT_REVIEW = PASS (REVIEW_3.md)
D1_D6_PREREQUISITE_COMMIT = 62d132ea3b0013e4c3ef72350990b18a6ce41a1f
PUSH = AUTHORIZED_ONCE: origin/feature/feat018-p2t2-live-lightning, fast-forward from 86836d24cfcd83ca14c0bc50e79fff1103cb9ecc, prerequisite commit plus this approval-record commit only
PUSH (every other branch, ref, commit or operation) = NOT_AUTHORIZED
```

It does not resolve D1, D6 fixture identity, D11, Stage 4 or live execution:

```text
D1 = BLOCKED_BY_D11
D6 = NOT FINALLY RESOLVED; FIXTURE IDENTITY = RESOLVED_WITH_PROPOSED_VALUE
D11 = BLOCKED
STAGE_4 = NOT READY
LIVE/MODEL/GPU/PROVIDER/NETWORK/LIGHTNING = NOT AUTHORIZED
NEXT = PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING
reviewed_runtime_code_commit = 9549a341194f40b1a9be419d6fce0d70f1ca0384
```

## Owner D9 governance publication and scoped push authorization - 2026-09-23

Approver: Project owner, by direct instruction in the current conversation,
"Publish the reviewed FEAT-018 D9 governance candidate only if every gate
below is clean", dated 2026-09-23.
Recorded by: Claude Code (Claude Opus 5.5) at 2026-09-23 13:44:29 UTC.
Verbatim authorization clause from that instruction:

> This goal authorizes one D9 candidate commit and one normal, non-force push
> to `origin/feature/feat018-p2t2-live-lightning`. This is a new, one-time
> authorization; it supersedes prior PUSH=NOT_AUTHORIZED only for this
> operation.

This entry is additive. The R1 addendum, the R2 amendment, the D1/D6 push
authorization and every earlier byte of this file are preserved unchanged.

### Basis

The post-prerequisite independent review of the D9 governance
reconciliation,
`tmp/feat018-p2t2-d9-post-prerequisite-independent-review-20260923/REVIEW.md`,
returned `PASS` for the exact four-path D9-only candidate on parent
`b976da5e6195ade65fb8ca701161b7c704e17b84`. The owner accepts that review's
non-blocking observations N-01 through N-04 unchanged as the owner
disposition; no candidate content was edited. All preflight gates were clean,
and the exact candidate was committed as:

- `c0f39d586a438be85a1a036ba8c8a21f4cefe4af`
  `docs(feat018): publish D9 governance reconciliation`; parent
  `b976da5e6195ade65fb8ca701161b7c704e17b84`; tree
  `ece12f5d98befe9686a70c161eaaa518d3e6ba15`; exactly four paths under
  `features/FEAT-018-live-image-canvas-flow/`: `CONTEXT.md`
  `4a2e2c20e4ebf2eeb373987b1a7902752fbcc85a`, `DECISIONS.md`
  `2508cd3a3cc91bb78631feaa8dbaa22c9a196246`, live plan
  `16feda7c2804b57e72d0833b3b9e4235acbae206`, and the new
  `evidence/notes/P2_T2_D9_GOVERNANCE_RECONCILIATION_20260922.md`
  `88af91a03bc53dd42a878360fe173bc8553aa7bb`.

### Exact push scope

The owner authorizes exactly one normal, non-force, fast-forward push to
`origin` branch `feature/feat018-p2t2-live-lightning`, whose remote value
before the push must be `b976da5e6195ade65fb8ca701161b7c704e17b84`. The push
may publish only these two commits:

1. the D9 governance commit `c0f39d586a438be85a1a036ba8c8a21f4cefe4af`;
2. the approval-record follow-up commit that adds only this entry, subject
   `docs(feat018): authorize scoped D9 push`, whose parent is the D9
   governance commit.

The push must not use force, tags or any other ref, and must not be preceded
by fetch, rebase, merge or reconciliation. If the remote rejects the push or
has diverged, the operation stops without retry or reconciliation.

This authorization does not publish or approve the untracked D1
owner-resolution package draft, the D1/D6 owner commit-readiness review note,
the D1/D6 prerequisite governance approval correction note, or the ignored
reports. It authorizes no other commit, push, branch/worktree/stash/remote
change, source/tests, fixtures, contracts, dependencies, workflows, or runtime
activity.

At recording time:

```text
D9_POST_PREREQUISITE_INDEPENDENT_REVIEW = PASS
D9_REVIEW_OBSERVATIONS_N01_N04 = ACCEPTED_UNCHANGED_BY_OWNER
D9_GOVERNANCE_COMMIT = c0f39d586a438be85a1a036ba8c8a21f4cefe4af
PUSH = AUTHORIZED_ONCE: origin/feature/feat018-p2t2-live-lightning, fast-forward from b976da5e6195ade65fb8ca701161b7c704e17b84, D9 governance commit plus this approval-record commit only
PUSH (every other branch, ref, commit or operation) = NOT_AUTHORIZED
```

It does not resolve D9, D1, D6 fixture identity, D11, Stage 4 or live
execution:

```text
P2T2-LIVE-D9 = NOT RESOLVED
D9_LIVE_D11_CARRIER_SCOPE = UNKNOWN_UNRESOLVED_PENDING_D11
D9 numeric ceilings (raw_output_max_bytes=65536, ipc_envelope_max_bytes=98304) = OWNER_SELECTED_CANDIDATE_ONLY
D1 = BLOCKED_BY_D11
D6 = NOT FINALLY RESOLVED; FIXTURE IDENTITY = RESOLVED_WITH_PROPOSED_VALUE
D11 = BLOCKED
STAGE_4 = NOT READY
LIVE/MODEL/GPU/PROVIDER/NETWORK/LIGHTNING = NOT AUTHORIZED
NEXT = PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING
reviewed_runtime_code_commit = 9549a341194f40b1a9be419d6fce0d70f1ca0384
```
