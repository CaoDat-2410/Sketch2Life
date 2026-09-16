# Task approval

- Status: APPROVED (P2-T1, P2-T2 Phase A, P2-T2 Phase B, P2-T3 Phase A, and P2-T3 Phase B)
- Approver: Project owner direct instruction in the current conversation

## Historical approved scope — P2-T1

- Scope: standalone deterministic image/audio quality validation, versioned fixture manifest/result contract, reason-code catalog, synthetic fixtures, unit/contract tests, and feature-local evidence.
- Plan revision: 3
- Approved at: 2026-08-26

## Current approved scope — P2-T2 Phase A

- Scope: freeze `AsrRequestV1` and discriminated-union `AsrResultV1` (`AsrSuccessV1 | AsrFailureV1`); implement `AsrProfileCatalogV1` with deterministic fake entries only, `AsrPort`, the approved retry/repair matrix, a deterministic fixture fake adapter, R2 synthetic fixture manifest, unit tests, contract tests, and feature-local evidence.
- Contract constraints: `source_audio_ref`/hash are always preserved from a synthetic P2-T1-`PASS` fixture; Phase A never creates a processing working copy; `processing_audio_ref` remains null; an out-of-catalog profile ID is rejected at request construction; ASR diagnostics never override P2-T1 validation.
- Plan revision: 4, including `plan/P2_T2_ASR_RESEARCH_PLAN.md` and `evidence/notes/P2_T2_LOGIC_CONSTRAINT_REVIEW.md`.
- Approved at: 2026-08-30

## Current approved scope — P2-T2 Phase B

- Scope: implement the additive ASR profile-contract/catalog change in B1; add the real local `faster-whisper` adapter and its isolated runtime configuration; exact-pin dependencies; download model weights only into the runtime-configured local cache; run real-adapter GPU preflight; execute the Round 1 AUTO_DETECT-only synthetic ASR benchmark and write feature-local evidence.
- Contract constraints: preserve all Phase A fake-entry values and behavior; use one static, versioned, phase-agnostic catalog; never hard-code a local cache path; retain provider-neutral shared contracts; keep `HONOR_HINT` out of Round 1; VAD/beam/word-timestamp alternatives are `NOT_MEASURED`; no profile is frozen or selected as a runtime default.
- Data and boundary constraints: synthetic/licensed fixtures only; no raw audio, transcript, credentials, endpoint detail, or absolute local path in logs/evidence; no HTTP/API/provider wiring, cloud deployment, P2-T5 CLI/end-to-end harness, mobile/UI/session/job/database/queue integration, or real child data.
- Plan revision: 4, including `plan/P2_T2_ASR_RESEARCH_PLAN.md` B1-B7 and `evidence/notes/P2_T2_PHASE_B_APPROVAL_REQUEST.md`.
- Approved at: 2026-08-30

## Current approved scope — P2-T3 Phase A

- Scope: freeze the feature-local image/reference/provenance, request, profile-catalog, discriminated result, candidate, policy, and port contracts in `plan/P2_T3_VISION_RESEARCH_PLAN.md`; implement deterministic fake catalog entries and adapter ingress validation; implement the lexical regression policy; add synthetic fixture-manifest and contract tests; and record feature-local evidence.
- Owner decisions: Phase A lexicon inputs are synthetic-only and versioned; the project owner reviews the lexicon, and any category-set, governance, policy/match-view-contract change needs renewed plan-and-approval review while a synthetic entry update must bump `lexicon_version` and be recorded as evidence. `label`/`predicate`/`note` use open normalized structured text with non-ground-truth `ObservedTextV1`/`TextLanguageDeclarationV1`. `AmbiguousRegionCandidateV1` has no geometry and cannot be an evidence target in Phase A.
- Contract and boundary constraints: preserve the immutable source image and require a P2-T1 `PASS`; the adapter, not the interface-only port, verifies profile/provenance/hash before inference; Phase A uses fake entries only and must not fabricate model provenance; policy remains a known-violation lexical regression layer, not a semantic-safety guarantee; no policy match text/entry is exposed in a result.
- Non-goals: no Qwen model/dependency/weight/download/GPU/provider/runtime/cloud execution, no real child data, credentials, API/UI/mobile/session/job/database/queue/storage work, P2-T4/P2-T5 work, user-facing output, Integration Sprint promotion, Gate A decision, real-model provenance, or semantic-paraphrase safety claim.
- Plan revision: 4, including `plan/P2_T3_VISION_RESEARCH_PLAN.md`, `evidence/notes/P2_T3_VISION_CONSTRAINT_REVIEW.md`, and `evidence/notes/P2_T3_PHASE_A_APPROVAL.md`.
- Approved at: 2026-08-31

## Current approved scope — P2-T3 Phase B

- Scope: implement exactly B1–B5 in `evidence/notes/P2_T3_PHASE_B_APPROVAL_REQUEST.md`: the isolated Qwen runtime and V2 contracts; typed Lightning L4 preflight; structured-output mapping study; held-out synthetic vision-only benchmark with its mandatory repeat; and the evidence-only recommendation/ADR gate.
- Contract and runtime constraints: preserve every V1 model, digest, and behavior; use the separate V2 identity/catalog/hash functions and exactly one candidate, `QWEN3_VL_8B_INSTRUCT_BF16_V1` at `GPU_BF16`; record immutable model revision, license, weight provenance, and exact dependency pins before download; apply the complete V2 terminal-outcome/provenance matrix; use lossless fence unwrap as the only repair; and never select a profile or runtime default.
- Data, evidence, and compute constraints: synthetic fixtures only; Person 2 authors and hashes ground truth before model output, with owner review before B4; `known_policy_trigger_rate` is `NOT_APPLICABLE` for the fixture lexicon; raw output is ephemeral and never enters evidence; Lightning L4 is development-only, with a one-hour soft cap total for B2–B4 including the repeat—stop and obtain explicit reauthorization before further GPU work if reached.
- Non-goals: no production/deployment/provider decision or credentials; no API/UI/mobile/session/job/database/queue/storage/P2-T4/P2-T5 work; no real child data; no Gate A or Integration Sprint promotion.
- Approval basis: `plan/P2_T3_VISION_RESEARCH_PLAN.md` and `evidence/notes/P2_T3_PHASE_B_APPROVAL_REQUEST.md` (Round-5 corrected).
- Approved at: 2026-09-01

## Phase 8 D-7 decision addendum — 2026-09-09

- Scope: Prompt-v3 Phase 8 held-out quality local/no-GPU preparation and any separately approved
  future Phase 8 execution under the same raw-output boundary.
- D-7 is fixed as `CLASSIFY_ONLY`. Persist only safe aggregate classification flags/counts and
  closed typed identifiers. Never persist raw provider output, prompt text, predicted text, or
  ground-truth text.
- This narrow addendum does not approve D-5, D-6, D-8, manifest/fixture review, model execution,
  Lightning/GPU use, or Phase 8 completion. The separate B3 `EPHEMERAL_CAPTURE` behavior remains
  unchanged and is not enabled for the Phase 8 runner.

## Phase 8 D-5/D-6 decision addendum — 2026-09-09

- Scope: the pre-registered acceptance and repeat gates for the separately held-out prompt-v3
  Phase 8 quality benchmark.
- D-5 is fixed as follows: entities, actions, relations, and themes each require aggregate
  coverage and accuracy of at least `0.80`. Ambiguous regions require count-rate lower and upper
  bounds of `1.00`; their accuracy remains `NOT_MEASURED` and their note text is never compared.
- D-6 is fixed as follows: each pass requires exactly eight attempted fixtures, eight run records,
  and eight schema-valid runs. Both passes must independently meet D-5, use the same Lightning
  session, and start Repeat no later than 15 minutes after Pass 1 completes. Configuration drift;
  input, runtime, or device failure; and two or more truncated outputs in either pass are blocking.
- This addendum does not by itself approve the manifest/fixture review, D-8 compute budget, model
  execution, Lightning/GPU use, a profile freeze/default, or Phase 8 completion.

## Phase 8 manifest and D-8 execution approval — 2026-09-09

- The owner approves manifest `vision-v3-quality-manifest-v1` in state
  `OWNER_REVIEW_APPROVED` and its current ordered set of eight synthetic held-out fixtures,
  including the image SHA-256 values recorded in that manifest. Ground truth and matching-rule
  identity remain bound by their recorded hashes; this approval does not permit fixture mutation.
- D-8 authorizes one Lightning Studio session on `1 x NVIDIA L4` for exactly one readiness check,
  one `V3_QUALITY_PASS_1`, one immediate `V3_QUALITY_REPEAT_1`, safe report serialization, and
  shutdown. The hard wall-clock cap is 30 minutes, measured from immediately before the Studio is
  started or awakened. `CLASSIFY_ONLY` remains mandatory; downloads, tuning, exploratory calls,
  extra diagnostics, and automatic reruns are not authorized.
- If readiness is not `READY`, package identity fails, the run becomes incomplete/non-comparable,
  or the cap is reached, the operator records `ABORTED`/`NON_COMPARABLE` as applicable and stops
  the Studio immediately. Operator start/stop plus official Lightning Activity duration/cost are
  recorded afterward. This approval does not freeze a profile or select a runtime default.

## Explicitly not approved

- Any P2-T3 work outside the approved Phase B B1–B5 scope, P2-T4 implementation through P2-T5, mobile/API/session/job orchestration, Gate A UI, database/storage/queue integration, real child data, and any provider credentials.

## Historical compatibility-review authorization — 2026-09-05

- Scope: fetch the then-current Person 2 and Person 1 branches, run isolated offline tests, review
  compatibility, and record evidence and next-step recommendations.
- Boundary: review only; no P2-to-P1 runtime wiring, fusion implementation, live provider call, or
  implementation-status promotion. All Phase A/Phase B approvals above remain authoritative and
  unchanged.
- Plan: `plan/P2_P1_REVIEW_20260905.md`, revision `review-20260905-1`.

## P2-T1 maintenance approval — T0 incremental source hashing — 2026-09-10

- Scope: replace whole-file source hashing with incremental SHA-256 over fixed-size reads of at
  most 1 MiB in `_source_reference` in
  `backend/src/sketch2life/application/services/media_validation.py`, plus its focused tests.
- Origin: requested by FEAT-018 Person 2 research; implementation and evidence belong to
  FEAT-003 P2-T1 because every current caller is FEAT-003 (its unit tests and the ASR/vision
  benchmark validation helpers). This does not transfer P2-T1 ownership to FEAT-018.
- Acceptance: SHA-256 is computed over the complete file; digests, source statuses, decisions,
  reasons, messages, policy version, contract version, field ordering and the serialized
  `MediaValidationResultV1` are byte-identical for unchanged inputs; the `OSError`-to-
  `MISSING`/`UNREADABLE` mapping is preserved; a focused test fails on the previous whole-file
  implementation and asserts every hashing read requests a positive size of at most 1 MiB.
- Explicitly not approved: changes to byte/pixel limits, decoding, optional-audio behavior,
  reason enums, policy thresholds, EXIF handling, derivatives, inspector defaults, model
  adapters, prompts, profiles, dependencies, benchmark scoring, frozen fixtures, or historical
  evidence; and any FEAT-018 integration, provider execution or readiness promotion.
- Bounded effect: this bounds hashing memory only. It does not bound total bytes read, elapsed
  time or decoding memory, and it does not close the validation-to-inference mutation window.
- Approved at: 2026-09-10, project owner direct instruction in the current conversation.

## FEAT-018 cross-feature consumption addendum — 2026-09-12

The project owner approves FEAT-018 P2-T2 consumption of the already-approved FEAT-003 Phase B
typed boundary, limited to the following canonical contracts and adapter boundary:

- `backend/src/sketch2life/contracts/schemas/vision_v2.py`: `VisionUnderstandingRequestV2`,
  `VisionUnderstandingResultV2`, its success/failure variants, `VisionProfileV2`, and
  `VisionModelProvenanceV1`.
- `backend/src/sketch2life/infrastructure/ai/qwen_vision.py`: the typed local Qwen adapter/port
  boundary, including its in-process test seam and subprocess-isolated runtime design.

Ownership remains FEAT-003. This is a read/consume permission only. FEAT-018 must not modify
FEAT-003 schemas, Qwen runtime, profiles, dependency pins, benchmarks, fixtures, approval evidence,
or Phase B results. FEAT-018 must not use FEAT-017's flat `understanding.py` contract or remote
HTTPS `LightningVisionAdapter` for P2-T2. The FEAT-003 contract identity and source revision must
be recorded in FEAT-018 implementation evidence; drift requires renewed review.

This addendum does not authorize FEAT-018 implementation by itself, model-weight download, GPU or
Lightning execution, provider/network calls, credentials, mobile/API/session/job/database/queue
wiring, Gate A UI, P1 eligibility, P3/P4, shared integration, or any FEAT-003 modification.

Approved at: 2026-09-12, project owner direct instruction in the current conversation.

## Current approved scope — P2-T4 Blocker-0 contract reconciliation — 2026-09-13

- Scope: the separately bounded contract-reconciliation workstream described in
  `plan/P2_T4_CONTRACT_RECONCILIATION_PLAN.md` and
  `evidence/notes/P2_T4_CONTRACT_RECONCILIATION_APPROVAL_REQUEST.md`. The owner selected B0
  Option 3: reconcile the live FEAT-018 contract family with the P2-T2/P2-T3/P2-T4 family
  through an explicit canonical versioned contract or versioned mapping, with compatibility
  analysis and a synthetic migration/compatibility fixture.
- Permitted outputs: documentation and contract-registry analysis, field-by-field compatibility
  matrix/report, a new synthetic-only compatibility fixture, follow-up ownership/acceptance
  checks, and narrowly scoped identity/mapping documentation. Existing code and fixture baselines
  are inspection-only.
- Explicit boundary: this approval does not authorize P2-T4 fusion implementation, schema
  implementation, migration execution or cutover, runtime wiring, FEAT-018 implementation,
  changes to routes/adapters/ports/loaders/flows/consumers, changes to existing FEAT-015 or
  FEAT-018 fixtures, changes to P2-T2/P2-T3 contracts or evidence, provider/GPU/Lightning work,
  or any P1/Gate A behavior change.
- Approval status: approved only for this Blocker-0 reconciliation scope. A separate approval is
  required for any implementation or adoption follow-up and for the complete P2-T4 fusion scope.
- Approved at: 2026-09-13, project owner direct instruction in the current conversation.

## Notes

FEAT-012 and ADR-0006 still govern the standalone Sprint 1 boundary. Person 2 does not own Gate A UI or backend job orchestration in Sprint 1.

## Current approved scope — P2-T4 docs-only remediation and reissue — 2026-09-14

- Scope: remediate and reissue the P2-T4 documentation package for the seven-file offline
  core direction, and prepare a reviewable versioned contract-freeze draft. This approval is
  documentation-only and does not authorize implementation.
- Authorized documentation files, and only these files, are:
  `approvals/TASK_APPROVAL.md`, `CONTEXT.md`, `DECISIONS.md`, `plan/PLAN.md`,
  `plan/P2_T4_FUSION_RESEARCH_PLAN.md`,
  `evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT_20260913.md`, and
  `plan/P2_T4_CONTRACT_FREEZE_DRAFT.md`.
- The future offline implementation allowlist is exactly:
  `backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py`,
  `backend/src/sketch2life/application/services/p2_t4_fusion.py`,
  `backend/tests/contract/test_p2_t4_contract.py`,
  `backend/tests/unit/test_p2_t4_fusion.py`,
  `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json`,
  `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json`, and
  `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json`.
- The seven paths are a future implementation allowlist, not a total documentation workflow.
  No path in that list may be created, edited, stubbed, or pre-populated during this task.
- The reissue removes `p2_t4_mapping.py`, mapping tests, any preservation-envelope
  implementation, and mapping cases from the Sprint-1 T4 implementation proposal. The
  mapping family `P2T4_FEAT018_CONTRACT_FAMILY_MAPPING_V1@1.0` remains
  `PROPOSED_NOT_ADOPTED`.
- FEAT-018 mapping/adoption, session/request/idempotency, registry work, edge 3, Gate A,
  migration, runtime/provider/GPU/network work, and changes to FEAT-017, FEAT-018, P2-T2,
  P2-T3, or existing fixtures remain deferred and unapproved.
- This approval does not freeze a contract, approve the seven-file implementation scope,
  approve migration or runtime behavior, or change any prior implementation approval. The two
  earlier full-document reviews remain historical review evidence; during post-sync
  reconciliation the separate owner freeze decision and separate implementation approval remain
  required.
- Post-sync reconciliation records the current FEAT-018 implementation at review base
  `d706d88a70c6a9136e397bea10d29f96bafd190b`: the FEAT-018-owned, frozen/implemented
  live-development handoff is `RawUnderstandingResultV1 / 1.0`, with offline closure approved
  at `11468d3a5a327697a491f09251a3210987337da0`. The existing 2026-09-12 FEAT-018 consumption
  addendum above remains unchanged and continues to authorize only the approved V2 consume-only
  boundary; it does not authorize this task to modify FEAT-018 or FEAT-003 implementation.
- The current handoff is not the proposed P2-T4 output and is not an alias or replacement for it.
  The actual boundary difference is recorded: FEAT-018's mapper consumes Vision V2 plus optional
  P2 ASR, while P2-T4 consumes Vision V1; FEAT-018 uses `SUCCEEDED | FAILED` Raw branches and
  requires session/image/Gate-A/V2 provenance, while P2-T4 proposes `FUSED | UPSTREAM_FAILURE`
  with distinct fused-claim, ambiguity, conflict, confidence, uncertainty, and failure shapes.
- The immutable B0 reconciliation snapshot predates the implemented FEAT-018 Raw module. Its
  mapping remains `P2T4_FEAT018_CONTRACT_FAMILY_MAPPING_V1@1.0` / `PROPOSED_NOT_ADOPTED`; a
  separately approved integration reconciliation is required before adoption, registry change,
  consumer update, or edge-3 handoff.
- Two independent post-remediation final audits (technical/contract and governance/security/scope)
  passed; current docs-only reissue status is **READY FOR OWNER FREEZE DECISION**. This is not
  a contract freeze or implementation approval. `review_base_commit` is the current
  `d706d88a70c6a9136e397bea10d29f96bafd190b`; the future
  T4 freeze/implementation source commit is `UNKNOWN_UNTIL_REVIEW_APPROVED_COMMITTED`.
- For this documentation reissue, the owner selected the following values to synchronize
  across the authorized records: active output `P2T4.P2T4FusedResultV1@1.0` serialized as
  `P2T4FusedResultV1 / 1.0`; prior `RawUnderstandingResultV1` wording is historical only;
  FEAT-018 rejection identities are `FEAT018.LiveAsrResultV1@1.0` and
  `FEAT018.LiveVisionUnderstandingResultV1@1.0`; matching is per validated
  `AsrSegmentV1.text` with per-segment coordinate/window reset and no cross-segment match;
  coordinates are `(segment_index, claim_start, claim_end)` over normalized segment tokens;
  `transcript_raw` is non-authoritative; `corroboration_increment` is canonical string
  `"0.10"` with approved `Decimal` arithmetic; ambiguous Vision regions are not fused and
  retain only canonical source-result provenance; mixed positive/refuting spans retain support
   and canonical positive/refuting refs while suppressing adjustment and primary eligibility.
- The confirmed ASR admissibility invariant is exactly: `For AsrSuccessV1, all
  AsrSegmentV1.index values MUST be unique.` The terminal pipeline is exactly
  `identity/version -> strict upstream-contract validation -> P2-T4 admissibility invariants ->
  correlation equality -> typed upstream status -> fusion`; the first failing stage is terminal
  and ASR is checked before Vision where slot ordering applies. A duplicate index is rejected
  with `status=REJECTED`, `phase=ADMISSIBILITY`, `code=INVALID_STRUCTURE`, `input_slot=ASR`, and
  `field_code=DUPLICATE_SEGMENT_INDEX`, with no duplicated index, transcript, input object,
  exception, or validation path exposed.
- Vision V1 already enforces global `observation_id` uniqueness across entities, actions,
  relations, themes, and ambiguous regions through `_validate_observation_references`; T4 adds
  no redundant Vision uniqueness rule or new owner decision. Canonical narration references are
  ordered exactly by `(segment_index ASC, claim_start ASC, claim_end ASC)`. Identical coordinate
  tuples are deduplicated before independently selecting the canonical earliest positive and
  earliest refuting reference, independent of source tuple traversal order.
- These selected values are draft semantics for the owner-freeze decision, not a contract
  freeze or implementation authorization. The synchronized draft also requires exact field
  tables, deterministic canonical bytes/conflict IDs, evidence hash bindings, and a separate
  hand-authored schema-parity oracle.
- Approved at: 2026-09-14, project owner direct instruction in the current conversation.

## P2-T4 G1 contract-freeze approval and architecture policy — 2026-09-15

- The project owner approved **Architecture Policy B / BASELINE** for P2-T4. The accepted
  baseline fingerprint is: validator identity `tools/validate_architecture.py` (SHA-256
  `fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5`), rule/category
  `application imports an outer layer`, exact file
  `backend/src/sketch2life/application/services/backend_ai_workflow.py`, expected violation
  count `1`. The validator must continue to report `ARCHITECTURE_INVALID` with only this exact
  baseline finding; any new or changed finding blocks P2-T4 completion.
- The project owner approved the immutable P2-T4 contract freeze at commit
  `18d0c33d35431ca96a76692a68c6b992098699e7` with contract identity
  `P2T4.P2T4FusedResultV1@1.0` and these normalized artifact bindings:
  `P2_T4_CONTRACT_FREEZE_DRAFT.md` SHA-256
  `be96b32aa675b7b6e46eea30effb2dbb91c718dc68ba7ce36d4d627ad6058ee2` and
  `P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT_20260913.md` SHA-256
  `6821755722daf3bce622fe98eaf39124adb835c6854661143d79f48a943030d7`.
- This G1 approval freezes the contract/package bytes and authorizes only governance records
  that reference the exact commit, identity, and digests, plus preparation of a separate G2
  implementation-approval request at
  `plan/P2_T4_IMPLEMENTATION_APPROVAL_REQUEST_20260915.md`. The freeze/package must not be
  edited in place.
- G2 implementation approval is **NOT GRANTED**. The exact seven-file offline allowlist remains
  a future scope only; no implementation, schema/runtime wiring, fixture generation, mapping
  adoption, migration, integration, provider/model/GPU/Lightning/network execution, or P2-T5
  work is authorized. Runtime/integration/live status remains **NOT APPROVED**.
- Approved at: 2026-09-15, project owner direct instruction in the current conversation.

## P2-T4 G2 exact-seven-file offline implementation approval — 2026-09-15

- The project owner approves P2-T4 G2 for **exactly** the seven-file offline implementation
  scope below. This approval is separate from the immutable G1 contract freeze.
- G1 binding remains: contract identity `P2T4.P2T4FusedResultV1@1.0`; immutable freeze commit
  `18d0c33d35431ca96a76692a68c6b992098699e7`; freeze SHA-256
  `be96b32aa675b7b6e46eea30effb2dbb91c718dc68ba7ce36d4d627ad6058ee2`; implementation-package
  SHA-256 `6821755722daf3bce622fe98eaf39124adb835c6854661143d79f48a943030d7`.
- The exact authorized implementation paths are:
  `backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py`,
  `backend/src/sketch2life/application/services/p2_t4_fusion.py`,
  `backend/tests/contract/test_p2_t4_contract.py`,
  `backend/tests/unit/test_p2_t4_fusion.py`,
  `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json`,
  `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json`, and
  `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json`.
- No other implementation, test, fixture, helper, adapter, mapping, runtime, registry,
  migration, API, queue, database, storage, UI, or integration path is authorized by G2.
- Implementation must conform exactly to G1: P2 ASR/Vision V1 identities; separate outer
  validation/rejection and pure typed `fuse()` boundaries; terminal rejection precedence;
  duplicate-ASR-segment-index admissibility; deterministic narration-reference ordering;
  support/refutation and conflict semantics; primary selection from original confidence before
  adjustment; primary-only `Decimal("0.10")` adjustment; null/conflict certainty precedence;
  original-base low-confidence evaluation; canonical serialization/conflict IDs; provenance and
  privacy rules; and only `FUSED | UPSTREAM_FAILURE` result statuses.
- The implementation must remain deterministic, offline, model-free, provider-free,
  network-free, GPU-free, and Lightning-free. B0 mapping adoption, FEAT-018 replacement or
  runtime integration, FEAT-020 changes, registry/session/idempotency work, preservation
  envelope, Gate A, migration/cutover, P2-T5, production use, and live execution remain
  **NOT APPROVED**.
- Architecture validation uses Policy B. The only accepted baseline is one finding with rule
  `application imports an outer layer` at
  `backend/src/sketch2life/application/services/backend_ai_workflow.py`; expected count is `1`,
  validator SHA-256 is
  `fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5`, and
  `validate_architecture.py` must be reported truthfully as `ARCHITECTURE_INVALID`. Any new,
  removed, relocated, or changed finding blocks the implementation checkpoint unless separately
  reviewed and approved.
- Canonicalization and deterministic-output evidence must run under CPython 3.13.x.
- Before accepting the implementation checkpoint, run focused P2-T4 tests, the full backend test
  suite, Ruff, mypy, harness, repository security, skeleton, architecture validation under
  Policy B, `git diff --check`, and the required deterministic/canonicalization checks. An
  independent diff, contract, privacy, and governance review is required before the checkpoint
  commit.
- Evidence artifacts are not authorized by this approval. They may be produced only after the
  exact implementation source commit exists and must bind that commit to the immutable G1
  digests. The sole non-implementation mutation additionally authorized now is this governance-
  only record in `approvals/TASK_APPROVAL.md`; it does not expand the seven-file scope.
- Disposition: **APPROVED_FOR_EXACT_SEVEN_FILE_OFFLINE_IMPLEMENTATION_ONLY**.
- Approved at: 2026-09-15, project owner direct instruction in the current conversation.

## P2-T4 Vision match-view successor decisions and package-issuance authorization — 2026-09-15

- A post-checkpoint contract audit of the G2-approved offline core (checkpoint
  `064ba62f32f1ffb964bc2208577eb0650b98e26a`) found a **VERIFIED_DEFECT**: G1 freeze section 5.2
  states that successful fusion requires the declared v2 match view, but upstream Vision V1
  accepts any non-empty `policy_match_view_version` and the checkpoint performs no check, so a
  schema-valid non-canonical Vision success reaches `FUSED`. Full evidence, reproduction, and
  option analysis are in `plan/P2_T4_MATCH_VIEW_REMEDIATION_PLAN.md`.
- The project owner recorded the following five decisions:
  - **MV-1 = B.** Add a new closed field code, `POLICY_MATCH_VIEW_VERSION`, to the outer-boundary
    rejection vocabulary, at the `ADMISSIBILITY` phase.
  - **MV-2 = S2.** Enforce the invariant only for `VisionUnderstandingSuccessV1`; a
    `VisionUnderstandingFailureV1` is not subject to it.
  - **MV-3 = T1.** Compare the observed `policy_match_view_version` for exact equality with the
    upstream constant `VISION_POLICY_MATCH_VIEW_VERSION` (`vision-policy-match-view-v2`); the T4
    policy literal `vision_policy_match_view-v2` and `fusion_policy_config_hash` are unchanged.
  - **MV-4 = V2.** Keep `P2T4.P2T4FusedResultV1@1.0` unchanged. Replace the outer rejection
    contract with a new major identity, `P2T4.P2T4FusionInputRejectionV2@2.0`, superseding
    `P2T4.P2T4FusionInputRejectionV1@1.0` for every outer-boundary rejection; no code path may
    emit a `P2T4FusionInputRejectionV1` instance or a mixed V1/V2 rejection union once this
    successor is the approved contract.
  - **MV-5.** Issue standalone successor artifacts at new paths rather than editing revision
    11/15 in place. Revision 11
    (`plan/P2_T4_CONTRACT_FREEZE_DRAFT.md`) and revision 15
    (`evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT_20260913.md`) remain
    byte-identical, immutable G1 history at their existing paths and are not edited.
- The normative successor semantics that follow from these decisions: after strict upstream
  validation, the ASR duplicate-index admissibility invariant runs first; for
  `VisionUnderstandingSuccessV1`, `policy_match_view_version` must then equal
  `VISION_POLICY_MATCH_VIEW_VERSION` exactly; a mismatch returns
  `contract_name=P2T4FusionInputRejectionV2`, `contract_version=2.0`, `status=REJECTED`,
  `input_slot=VISION`, `phase=ADMISSIBILITY`, `code=INVALID_STRUCTURE`,
  `expected_identity=observed_identity=P2.VisionUnderstandingResultV1@1.0`,
  `observed_status=SUCCEEDED`, `field_code=POLICY_MATCH_VIEW_VERSION`, never exposing the
  observed token or raw input; a Vision failure does not receive this check; match-view
  admissibility precedes correlation equality and typed upstream-status handling; and the fused
  result and all unrelated fusion semantics remain unchanged.
- This authorization permits, and only permits, the following docs-only successor-package work:
  1. recording the five decisions above;
  2. creating exactly two new standalone documents implementing them:
     `plan/P2_T4_CONTRACT_FREEZE_REVISION_12.md` (freeze successor, revision 12) and
     `evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_REVISION_16.md` (package successor,
     revision 16), both computed and independently reproduced with the same normalized-digest
     algorithm as revisions 11/15, and both status `HOLD - NOT APPROVED`;
  3. relocating the match-view approval-request content from its previously ignored
     `evidence/notes/` path to the publishable
     `plan/P2_T4_MATCH_VIEW_REMEDIATION_APPROVAL_REQUEST_20260915.md` path, and removing the
     now-superseded ignored duplicate;
  4. reconciling gate-state wording in `CONTEXT.md`, `DECISIONS.md`, `plan/PLAN.md`, and
     `plan/P2_T4_FUSION_RESEARCH_PLAN.md` to reflect that the decisions above are recorded and
     that the successor documents exist and are pending independent review; and
  5. exactly one `.gitignore` exception, for the new package path in item 2, mirroring the
     existing exception for its predecessor.
- This authorization does **not** grant successor-freeze approval, does **not** approve the
  seven-file remediation implementation, and does **not** authorize G6 verification, G7 evidence,
  runtime, provider, model, GPU, Lightning, network, migration, integration, P2-T5, or production
  work. It does not edit or replace the immutable G1 freeze (revision 11) or package (revision
  15) in place. The successor-freeze approval and the remediation-implementation approval each
  remain separate, future owner actions.
- Approved at: 2026-09-15, project owner direct instruction in the current conversation.

## P2-T4 successor contract-freeze approval ("G1 successor") — 2026-09-15

- The project owner approved the P2-T4 successor contract freeze and successor package, in these
  exact words:

  > I approve the P2-T4 successor contract freeze revision 12 and successor package revision 16
  > using the four verified SHA-256 identities stated above. This approval authorizes governance
  > recording only; remediation implementation and integration/runtime/live remain not approved.

- The approval is bound to four full SHA-256 identities, each independently reproduced twice
  (two differently coded implementations of the documented normalization algorithm) immediately
  before this record was written, and each confirmed to still match:
  - **Successor freeze, revision 12**
    (`plan/P2_T4_CONTRACT_FREEZE_REVISION_12.md`): normalized SHA-256
    `d592b135d2d8a90024d48d1b8335321660e8d7f089873e48687707c760e3d3e9`.
  - **Successor package, revision 16**
    (`evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_REVISION_16.md`): normalized SHA-256
    `ad886d261d2807bcc95264d05d6a385dc79cd2f0cad44e2b4f004531b8097d4f`.
  - **Immutable predecessor freeze, revision 11**
    (`plan/P2_T4_CONTRACT_FREEZE_DRAFT.md`, unchanged, still committed at
    `18d0c33d35431ca96a76692a68c6b992098699e7`): normalized SHA-256
    `be96b32aa675b7b6e46eea30effb2dbb91c718dc68ba7ce36d4d627ad6058ee2`.
  - **Immutable predecessor package, revision 15**
    (`evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT_20260913.md`, unchanged, still
    committed at `18d0c33d35431ca96a76692a68c6b992098699e7`): normalized SHA-256
    `6821755722daf3bce622fe98eaf39124adb835c6854661143d79f48a943030d7`.
- Frozen successor semantics under this approval: the five MV-1 through MV-5 decisions recorded
  in the entry immediately above; the outer safe-rejection identity
  `P2T4.P2T4FusionInputRejectionV2@2.0`, superseding `P2T4.P2T4FusionInputRejectionV1@1.0` for
  every outer-boundary rejection (not only the new match-view case); the Vision match-view
  admissibility invariant for `VisionUnderstandingSuccessV1` only, checked after the ASR
  duplicate-index invariant and before correlation/typed status, with the exact rejection form
  and field code `POLICY_MATCH_VIEW_VERSION` defined in freeze revision 12 sections 3-4. The
  fused-result identity `P2T4.P2T4FusedResultV1@1.0` is **unchanged** by this approval.
- This is a **governance/freeze checkpoint approval, not an implementation approval**. It
  authorizes recording this approval in the governance records named below and nothing else. The
  seven-file remediation implementation (`backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py`,
  `backend/src/sketch2life/application/services/p2_t4_fusion.py`,
  `backend/tests/contract/test_p2_t4_contract.py`, `backend/tests/unit/test_p2_t4_fusion.py`,
  and the three `fixtures/p2-t4-fusion-v1/*.json` paths) remains **PENDING / NOT APPROVED** and
  is a separate, future owner action. Integration, runtime, provider, model, GPU, Lightning,
  network, migration, production, and live execution all remain **NOT APPROVED**.
- Freeze revision 11 and package revision 15 remain immutable historical artifacts at their
  existing paths and were not edited to record this approval; freeze revision 12 and package
  revision 16 were likewise not edited — both were verified byte-identical to the digests above
  immediately before this entry was written, and this approval binds them by digest rather than
  by amending their text. This is the same convention already used for the original G1 approval.
- The known `application imports an outer layer` finding in
  `backend/src/sketch2life/application/services/backend_ai_workflow.py` remains the owner-approved
  Architecture Policy B baseline (validator `tools/validate_architecture.py` SHA-256
  `fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5`, exactly one finding). It is
  unrelated to and unchanged by this governance checkpoint, and is not a P2-T4 regression.
- Approved at: 2026-09-15, project owner direct instruction in the current conversation.

## P2-T4 digest-binding integrity defect acceptance and Option A erratum authorization — 2026-09-16

- A read-only integrity audit (2026-09-15) found a **VERIFIED_INTEGRITY_DEFECT** in the four
  normalized SHA-256 identities recorded for freeze revisions 11/12 and package revisions 15/16,
  including those cited in the G1, G2, and successor contract-freeze entries above. Each value was
  computed with a first-substring search for the revision-history heading, which matches an inline
  mention of that heading in the document's own algorithm prose before the real heading, so each
  value binds only a prefix of its document's intended scope. No artifact bytes changed.
- The project owner accepted the finding and selected Option A, in these exact words:

  > I accept the VERIFIED_INTEGRITY_DEFECT finding and select Option A: an immutable digest-binding
  > erratum. The erratum must preserve revisions 11/12/15/16 byte-for-byte, record legacy digests as
  > historical only, establish corrected normalized SHA-256, raw-file SHA-256, Git blob IDs and
  > source commits for all four artifacts, and require independent review before renewed owner
  > approval. This authorization is documentation-only and does not authorize seven-file
  > remediation implementation, G6–G9, integration, runtime, GPU, Lightning, provider/model,
  > migration, production or live execution.

- Under this authorization the erratum `plan/P2_T4_DIGEST_BINDING_ERRATUM_20260915.md` was issued
  with status `READY FOR INDEPENDENT ERRATUM REVIEW — NOT OWNER REAPPROVED`, and the decision was
  recorded in this file, `CONTEXT.md`, `DECISIONS.md`, `plan/PLAN.md`,
  `plan/P2_T4_MATCH_VIEW_REMEDIATION_PLAN.md`, and
  `plan/P2_T4_MATCH_VIEW_REMEDIATION_APPROVAL_REQUEST_20260915.md`. Freeze revisions 11/12 and
  package revisions 15/16 are preserved byte-for-byte and are not edited.
- The legacy digests cited in the entries above are historical and non-canonical; those entries
  are not rewritten. The corrected identities are recorded in the erratum for independent review.
- **No renewed binding approval is granted.** The erratum awaits independent review, and only after
  that review may the owner decide a renewed binding approval against the corrected identities. The
  successor contract semantics recorded above are unchanged.
- **No implementation authority is granted.** The seven-file remediation implementation remains
  **NOT APPROVED**, and G6–G9 remain **PAUSED**. Evidence, integration, runtime, provider/model,
  GPU, Lightning, network, migration, production, and live execution remain **NOT APPROVED**.
- Recorded at: 2026-09-16, project owner direct instruction in the current conversation.

## P2-T4 renewed digest-binding approval after independent erratum review - 2026-09-16

- The independent erratum review is **PASS**. The four corrected normalized and raw-file SHA-256
  hashes were reproduced independently. Their source paths, source commits, Git blob IDs, byte/line
  counts, and binding-table/heading ranges were verified against erratum sections 4.1-4.4 and 5.
  The immutable erratum raw-file SHA-256
  `8975d94b0d9be8e78935b66e1e851493c1cff5b2f1b83cdf49acfe7f9929276e` and Git blob ID
  `4b7ed999fed45e176d57c395e63fe62e8f12accc` were verified as well.
- The owner renewed approval exactly as follows:

  > I approve the P2-T4 renewed digest-binding decision exactly as written above.

- The previously approved successor semantics include P2T4.P2T4FusedResultV1@1.0 and P2T4.P2T4FusionInputRejectionV2@2.0; their contract semantics remain unchanged, with no semantic reapproval.
- No implementation authority is granted by this binding approval.
- Renewed corrected artifact bindings are **APPROVED** against erratum sections 4.1-4.4. The renewed
  approval binds the following full corrected identity tuples from erratum section 4; each tuple
  includes repository path, source commit, Git blob ID, raw-file SHA-256, corrected normalized
  SHA-256, and the historical legacy value for audit traceability:

| Artifact | Repository path | Source commit | Git blob ID | Raw-file SHA-256 | Corrected normalized SHA-256 | Legacy first-substring SHA-256 (historical, non-canonical, incomplete) | Size / lines |
|---|---|---|---|---|---|---|---|
| Freeze rev 11 | `features/FEAT-003-multimodal-understanding/plan/P2_T4_CONTRACT_FREEZE_DRAFT.md` | `18d0c33d35431ca96a76692a68c6b992098699e7` | `87227e5be0a58db88ac9f91ee7ddbdfa9bf4b05f` | `9521cb1482a10cefd235ea9596882d210912897289c182205aa93ee5a6685197` | `2b920e34f779ccbeabfec91e44858957b4f032dd6583879403b0fb748e367050` | `be96b32aa675b7b6e46eea30effb2dbb91c718dc68ba7ce36d4d627ad6058ee2` | 62,792 / 989 |
| Freeze rev 12 | `features/FEAT-003-multimodal-understanding/plan/P2_T4_CONTRACT_FREEZE_REVISION_12.md` | `5b6501b2d8b809f9dd4caf77b5c5d51d2e1e9cf2` | `1e7e487362efec02b3b5f3bbf9dd4c64eabaa0d9` | `b9606292e00b1b956ec38e141eb27f868bad2835f8ea5e8d20693a18acd2fa20` | `103695e5e1c49d9f9b1cc85fd5286f42980580f338578db799febdeedb310ee5` | `d592b135d2d8a90024d48d1b8335321660e8d7f089873e48687707c760e3d3e9` | 80,834 / 1,193 |
| Package rev 15 | `features/FEAT-003-multimodal-understanding/evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT_20260913.md` | `18d0c33d35431ca96a76692a68c6b992098699e7` | `a4ade521f288c0d07c8c9cfdb1f6bbe6b41fa839` | `255034c587e89f8b72122c7377566684dd7a718257555c7fa92175a444255681` | `7c76208d2ab3c98f9681fce67641049a93b21d2f0c2e9c843de1cac9e4d70b96` | `6821755722daf3bce622fe98eaf39124adb835c6854661143d79f48a943030d7` | 34,337 / 451 |
| Package rev 16 | `features/FEAT-003-multimodal-understanding/evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_REVISION_16.md` | `5b6501b2d8b809f9dd4caf77b5c5d51d2e1e9cf2` | `8784e84a537260668e81c6c889aadc8688086857` | `8ce46b5f762b27b556030d85666ccb6827a1fdbaeb56312dc8490d6e214a75ce` | `75cd5d69e6896d7fae10d3771a90019003e0644fff1138161b7ac330e840b270` | `ad886d261d2807bcc95264d05d6a385dc79cd2f0cad44e2b4f004531b8097d4f` | 43,682 / 530 |

- The legacy first-substring digests are historical, non-canonical, and incomplete; they are not
  the renewed binding. The four original freeze/package artifacts remain byte-immutable, and the
  issued erratum remains byte-immutable and was not edited.
- This approval corrects bindings only. The successor contract semantics previously approved are
  unchanged; this record does not reapprove those semantics or grant implementation authority.
- The exact governance checkpoint allowlist for this docs-only commit is exactly these seven paths:
  `features/FEAT-003-multimodal-understanding/CONTEXT.md`,
  `features/FEAT-003-multimodal-understanding/DECISIONS.md`,
  `features/FEAT-003-multimodal-understanding/approvals/TASK_APPROVAL.md`,
  `features/FEAT-003-multimodal-understanding/plan/PLAN.md`,
  `features/FEAT-003-multimodal-understanding/plan/P2_T4_MATCH_VIEW_REMEDIATION_PLAN.md`,
  `features/FEAT-003-multimodal-understanding/plan/P2_T4_MATCH_VIEW_REMEDIATION_APPROVAL_REQUEST_20260915.md`,
  and `features/FEAT-003-multimodal-understanding/plan/P2_T4_DIGEST_BINDING_ERRATUM_20260915.md`.
- The exact seven-path remediation allowlist is separate from the governance allowlist and remains
  unchanged; its paths are listed in the following bullet.
- Separately, the seven-path remediation allowlist from checkpoint
  `064ba62f32f1ffb964bc2208577eb0650b98e26a` remains unchanged:
  `backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py`,
  `backend/src/sketch2life/application/services/p2_t4_fusion.py`,
  `backend/tests/contract/test_p2_t4_contract.py`,
  `backend/tests/unit/test_p2_t4_fusion.py`,
  `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json`,
  `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json`, and
  `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json`.
  None of those seven remediation files was modified in this checkpoint.
- The seven-file remediation is **NOT APPROVED / NOT STARTED**. G6-G9 remain **PAUSED**.
  Integration, runtime, provider/model, GPU, Lightning, network, migration, production, and live
  execution remain **NOT APPROVED**.
- No future checkpoint commit SHA is written into tracked files. The executor will report the
  resulting local governance commit SHA in the final handoff without modifying tracked files. This
  additive record supersedes the pre-renewal pending wording as the current approval state; earlier
  records and the immutable erratum preserve the historical issuance state.
- Recorded at: 2026-09-16, project owner direct instruction in the current conversation after the
  independent erratum review PASS.

## P2-T4 four-file renewed-binding status synchronization approval - 2026-09-16

- **Feature/task:** FEAT-003 Multimodal understanding / P2-T4.
- **Plan revision:** 7.
- **Disposition:** `APPROVED_FOR_EXACT_FOUR_FILE_DOCUMENTATION_STATUS_SYNCHRONIZATION_ONLY`.
- **Base commit:** `23992c54c8b19c0eb0a707ec0934599bddb97560` (required base; the direct parent of
  the resulting local documentation commit).
- **Exact editable scope, and no other path:**
  1. `features/FEAT-003-multimodal-understanding/approvals/TASK_APPROVAL.md`;
  2. `features/FEAT-003-multimodal-understanding/plan/PLAN.md`;
  3. `features/FEAT-003-multimodal-understanding/plan/P2_T4_MATCH_VIEW_REMEDIATION_PLAN.md`;
  4. `features/FEAT-003-multimodal-understanding/plan/P2_T4_MATCH_VIEW_REMEDIATION_APPROVAL_REQUEST_20260915.md`.
- **Acceptance criteria:** current/active records must state independent erratum review
  **COMPLETE/PASS**; renewed corrected artifact bindings **APPROVED**; successor semantics
  **PREVIOUSLY APPROVED / UNCHANGED**; digest decision **BINDING CORRECTION ONLY**; the
  seven-file remediation **NOT APPROVED / NOT STARTED**; G6-G9 **PAUSED**; and
  integration/runtime/provider/model/GPU/Lightning/network/migration/production/live
  **NOT APPROVED**. They must show the ordered gates: erratum issued **COMPLETE**, independent
  review **COMPLETE/PASS**, renewed corrected binding approval **COMPLETE/APPROVED**, this
  four-file synchronization **APPROVED / COMPLETE**, remediation approval **NOT GRANTED**,
  remediation **NOT STARTED**, and G6-G9 **PAUSED**. Stale pending/review-not-started wording
  may remain only as explicitly historical or immutable issuance-status text and must not remain
  active/current.
- **Verification acceptance:** the two complete reviews must confirm the exact base and gate order;
  only the four paths above may change; the immutable erratum and all four freeze/package artifacts
  must remain byte-unchanged; all seven remediation paths must remain byte-identical to checkpoint
  `064ba62f32f1ffb964bc2208577eb0650b98e26a`; no implementation or evidence path may be created;
  and architecture validation may report only the unchanged Policy-B baseline in
  `backend/src/sketch2life/application/services/backend_ai_workflow.py`, using validator SHA-256
  `fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5`. The required checks are
  `git diff --check`, the harness, repository-security, skeleton, and architecture validators.
- **Approver:** Project Owner / Person 2.
- **Owner approval (verbatim):**

  > I approve the P2-T4 four-file renewed-binding status synchronization exactly as written above.

- **Approval boundaries and exclusions:** documentation status synchronization only; no edits to
  `CONTEXT.md`, `DECISIONS.md`, the immutable erratum, either freeze artifact, either package
  artifact, source code, tests, fixtures, or evidence; no seven-file remediation implementation;
  no G6-G9 verification/evidence/review/completion; no FEAT-018/FEAT-020 work; and no integration,
  runtime, provider/model, GPU, Lightning, network, migration, production, or live execution.
  This approval does not reapprove successor semantics, does not grant remediation-implementation
  approval, and does not authorize any new path or evidence artifact.
- **No implementation authority** is granted by this approval.
- **Recorded:** 2026-09-16 by Project Owner / Person 2 direct instruction in the current
  conversation.
