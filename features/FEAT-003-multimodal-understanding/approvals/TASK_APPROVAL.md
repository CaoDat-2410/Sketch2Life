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

## P2-T4 exact-seven-file match-view remediation implementation approval - 2026-09-16

- **Feature/task:** `FEAT-003` Multimodal understanding / `P2-T4`.
- **Plan revision:** `7`.
- **Approver:** Project Owner / Person 2.
- **Disposition:** `APPROVED_FOR_EXACT_SEVEN_FILE_MATCH_VIEW_REMEDIATION_ONLY`.
- **Approval timestamp:** `2026-09-16`.
- **Owner decision:** Project Owner / Person 2 approved the exact disposition above on
  2026-09-16. This record is the durable approval record; no timestamp was prefilled before
  that owner sign-off.
- **Approval-review/governance base:**
  `c84a92990adac62477c076e6f660da3bef319175`.
- **Status:** `REMEDIATION IMPLEMENTATION APPROVED - NOT STARTED`.

### Corrected artifact identity bindings

The approval binds all four corrected identity tuples from digest-binding erratum sections
4.1-4.4. Each tuple includes the repository path, source commit, Git blob ID, raw-file
SHA-256, and corrected normalized SHA-256. The four source artifacts remain immutable and
are not edited by this approval or its governance checkpoint.

| Artifact | Repository path | Source commit | Git blob ID | Raw-file SHA-256 | Corrected normalized SHA-256 |
|---|---|---|---|---|---|
| Freeze rev 11 | `features/FEAT-003-multimodal-understanding/plan/P2_T4_CONTRACT_FREEZE_DRAFT.md` | `18d0c33d35431ca96a76692a68c6b992098699e7` | `87227e5be0a58db88ac9f91ee7ddbdfa9bf4b05f` | `9521cb1482a10cefd235ea9596882d210912897289c182205aa93ee5a6685197` | `2b920e34f779ccbeabfec91e44858957b4f032dd6583879403b0fb748e367050` |
| Freeze rev 12 | `features/FEAT-003-multimodal-understanding/plan/P2_T4_CONTRACT_FREEZE_REVISION_12.md` | `5b6501b2d8b809f9dd4caf77b5c5d51d2e1e9cf2` | `1e7e487362efec02b3b5f3bbf9dd4c64eabaa0d9` | `b9606292e00b1b956ec38e141eb27f868bad2835f8ea5e8d20693a18acd2fa20` | `103695e5e1c49d9f9b1cc85fd5286f42980580f338578db799febdeedb310ee5` |
| Package rev 15 | `features/FEAT-003-multimodal-understanding/evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT_20260913.md` | `18d0c33d35431ca96a76692a68c6b992098699e7` | `a4ade521f288c0d07c8c9cfdb1f6bbe6b41fa839` | `255034c587e89f8b72122c7377566684dd7a718257555c7fa92175a444255681` | `7c76208d2ab3c98f9681fce67641049a93b21d2f0c2e9c843de1cac9e4d70b96` |
| Package rev 16 | `features/FEAT-003-multimodal-understanding/evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_REVISION_16.md` | `5b6501b2d8b809f9dd4caf77b5c5d51d2e1e9cf2` | `8784e84a537260668e81c6c889aadc8688086857` | `8ce46b5f762b27b556030d85666ccb6827a1fdbaeb56312dc8490d6e214a75ce` | `75cd5d69e6896d7fae10d3771a90019003e0644fff1138161b7ac330e840b270` |

### Contract identities and architecture binding

- The fused result identity remains unchanged: `P2T4.P2T4FusedResultV1@1.0`.
- The outer input-rejection identity is `P2T4.P2T4FusionInputRejectionV2@2.0`.
- The Architecture Policy-B validator fingerprint is
  `fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5`.
- The existing Policy-B baseline may remain the only architecture finding. No infrastructure
  import or new architecture violation is approved.

### Exact seven-file implementation allowlist

The future remediation may change exactly these seven paths and no other path:

1. `backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py`
2. `backend/src/sketch2life/application/services/p2_t4_fusion.py`
3. `backend/tests/contract/test_p2_t4_contract.py`
4. `backend/tests/unit/test_p2_t4_fusion.py`
5. `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json`
6. `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json`
7. `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json`

There is no wildcard scope and no authority to add helpers, generated files, evidence,
documentation, or unrelated paths.

### Required contract, precedence, and fixture outcomes

- Replace V1 rejection consistently with V2 at every outer rejection boundary.
- Do not expose a mixed V1/V2 rejection union.
- Keep `P2T4.P2T4FusedResultV1@1.0` unchanged.
- Keep `POLICY_MATCH_VIEW_VERSION` as a closed field code.
- For `VisionUnderstandingSuccessV1`, require exact equality between
  `policy_match_view_version` and `VISION_POLICY_MATCH_VIEW_VERSION`, whose canonical value is
  `"vision-policy-match-view-v2"`.
- Check ASR duplicate-index admissibility before Vision match-view admissibility.
- Check Vision admissibility before correlation and typed status.
- A noncanonical Vision failure remains `UPSTREAM_FAILURE`; the success-only match-view check
  must not reject it.
- The observed noncanonical token must never enter output.
- Migrate all 16 existing `REJECTED` expected entries from V1/`1.0` to V2/`2.0` and recompute
  their canonical hashes.
- Keep all 26 non-rejected `FUSED`/`UPSTREAM_FAILURE` entries byte-identical.
- Rebind `manifest-v1.json` to the corrected artifact identities and the future recorded
  approval.
- Preserve deterministic, hand-authored fixtures.
- The contract test must use an independent hand-authored schema-parity oracle covering every
  field, requiredness, nullability, enum, literal, cross-field invariant, and rejection
  precedence rule. It must not introspect implementation fields, load a schema snapshot, or
  generate expected schemas from `p2_t4_fusion.py`.

### Fixture privacy rule

Fixture JSON may identify each synthetic match-view scenario, its mutation category, coverage,
and expected closed rejection semantics, but must not store or echo the observed noncanonical
`policy_match_view_version` value.

A fixed synthetic noncanonical sentinel may be constructed only inside the approved Python
unit/contract test source to exercise the input path.

The sentinel must not appear in:

- `manifest-v1.json`;
- `cases-v1.json`;
- `expected-v1.json`;
- rejection or fused output;
- canonical expected bytes or hashes;
- test failure snapshots;
- logs, evidence, or final reports.

Tests must assert non-disclosure without printing or serializing the sentinel. Fixture data must
remain deterministic and hand-authored, and expected schemas/results must not be generated from
the implementation under test.

### Required match-view fixture coverage

The remediation must add or verify all six scenarios below. The manifest coverage list,
`cases-v1.json`, `expected-v1.json`, contract tests, and unit tests must remain mutually
consistent for all six scenarios:

1. **AC-MV-1:** A `VisionUnderstandingSuccessV1` with a synthetic noncanonical match-view
   value is rejected at `ADMISSIBILITY`.
2. **AC-MV-2:** The T4 policy literal `vision_policy_match_view-v2`, when used as the upstream
   observed value, is rejected, proving comparison against `VISION_POLICY_MATCH_VIEW_VERSION`
   rather than the T4 policy literal.
3. **AC-MV-3:** Duplicate ASR segment-index admissibility wins when both the ASR duplicate-index
   invariant and Vision match-view invariant would fail.
4. **AC-MV-4:** Vision match-view admissibility wins over correlation mismatch.
5. **AC-MV-5:** A `VisionUnderstandingFailureV1` carrying a noncanonical match-view value remains
   `UPSTREAM_FAILURE`, proving the check is success-only.
6. **AC-MV-6:** Strict-validation versus admissibility precedence is exercised with ASR checked
   before Vision where slot ordering applies.

The approved Python tests may construct the fixed synthetic sentinel in memory as defined by the
fixture privacy rule. JSON fixtures identify the scenario and mutation category only; they do
not persist the offending sentinel.

### Acceptance criteria

- AC-MV-1 through AC-MV-6 are each implemented and independently asserted.
- Each of AC-MV-1 through AC-MV-6 is represented consistently in the manifest coverage list,
  cases, expected results, contract tests, and unit tests.
- The sentinel is absent from all fixture JSON, rejection/fused output, canonical bytes/hashes,
  failure snapshots, logs, evidence, and reports.
- Every outer rejection uses V2 only, with no V1/V2 rejection union.
- ASR-before-Vision and Vision-before-correlation precedence is observable and tested.
- The success-only Vision match-view rule and noncanonical-failure `UPSTREAM_FAILURE` behavior
  are observable and tested.
- All 16 `REJECTED` entries have V2 identities and recomputed hashes; all 26 non-rejected
  entries remain byte-identical.
- The manifest uses the corrected identity tuples and the future recorded approval binding.
- No infrastructure import or new Policy-B architecture finding is introduced.

### Required validation and independent review

Validation must run under CPython `3.13.x` and include:

- focused P2-T4 pytest;
- full pytest;
- Ruff;
- strict mypy;
- canonicalization and canonical-hash checks;
- privacy validation;
- harness, repository-security, skeleton, and architecture validators.

An independent candidate review must complete before the separate local implementation
checkpoint commit.

### Approval-record and implementation topology

This approval is recorded in one governance-only commit whose direct parent must be
`c84a92990adac62477c076e6f660da3bef319175`.

That governance commit may change only the repository-required approval record. It may not change
any implementation, test, fixture, evidence, freeze, package, erratum, `CONTEXT`, `DECISIONS`,
remediation-plan, or unrelated file.

The resulting full governance-commit SHA is the sole authorized implementation base and must be
reported in the execution handoff before any implementation edit begins. `c84a9299` itself must
not be treated as the implementation base.

The later implementation checkpoint must:

- use the governance approval commit as its direct parent;
- change exactly the seven approved implementation/test/fixture paths;
- contain no governance, approval, evidence, or unrelated path;
- be exactly one implementation commit unless separately reauthorized.

Abort and request renewed approval if this topology cannot be preserved.

### Explicit exclusions and current state

This approval does not authorize:

- G6-G9 or evidence creation;
- FEAT-018, FEAT-020, or any non-allowlisted path;
- mapping, adoption, integration, or runtime wiring;
- model, provider, GPU, Lightning, or network work;
- migration, production, or live execution;
- implementation push or PR creation.

Implementation has not started. No implementation, test, fixture, evidence, freeze/package,
erratum, context, or decisions file was changed by this approval record.

- **Final state:** `REMEDIATION IMPLEMENTATION APPROVED - NOT STARTED`.
- **G6-G9:** `PAUSED`.
- **Integration/runtime/live:** `NOT APPROVED`.
- **Runtime/live/GPU/provider/Lightning:** `NOT APPROVED`.
- **Recorded:** 2026-09-16 by Project Owner / Person 2 direct instruction in the current
  conversation.

## P2-T4 G9 governance closeout — 2026-09-17

The current task authorizes this governance-only closeout against the committed evidence
checkpoint. It does not authorize implementation, evidence-byte changes, or any downstream
execution.

P2-T4: COMPLETE — GOVERNANCE-CLOSED
CLOSEOUT: COMPLETE_WITH_ACCEPTED_G6_FINDINGS
G6: PASS_WITH_FINDINGS
G7: PASS
G8: PASS
G9: COMPLETE
P2-T5: NOT APPROVED
INTEGRATION/RUNTIME/LIVE: NOT APPROVED

### Immutable topology and evidence bindings

- Implementation candidate: `21249dc696c8ea3d958e78394ed69b8ac9f9505a`.
- Direct parent: `dc107cd45a21ccb47031a58cb7c782084624bff4`.
- Evidence checkpoint: `c80c58fbd2b76d28af52156301caca87e7a794f5`, with the candidate as its
  direct parent and exactly the three G7/G8 evidence paths below.
- The G9 governance checkpoint has the evidence checkpoint as its direct parent. Its own commit
  SHA is intentionally not written into tracked files and is reported only in the final handoff.

| Gate | Status | Canonical path | Raw SHA-256 | Git blob ID |
|---|---|---|---|---|
| G7 | PASS | `features/FEAT-003-multimodal-understanding/evidence/P2_T4_G7_CLOSEOUT_EVIDENCE.json` | `5b5e26753f5b4489cb559f06fc645884ca8e0af233cd563d791a56ad2ca5e40d` | `dfad83aac7a5c53bf5bab60239500f68f32e09be` |
| G7 | PASS | `features/FEAT-003-multimodal-understanding/evidence/P2_T4_G7_EVIDENCE_REVIEW_20260916.md` | `f204dc33ad0d73a26db4596f8c9f657c4dbbf71a9fa911ca34a4a6007071f824` | `d906827e466f357c74af0cbaf6f58eb96eaf54fa` |
| G8 | PASS | `features/FEAT-003-multimodal-understanding/evidence/P2_T4_G8_INDEPENDENT_EVIDENCE_GOVERNANCE_REVIEW_20260917.md` | `fe0e43b00edc7141e23b53cc9499c5c769c1e1c370fb005c88a6a17f6b827119` | `5e2665f4096d5316ab1eaf49d7da2677ec6a58ee` |

### Preserved findings and boundaries

OPEN P2-T4 IMPLEMENTATION DEFECTS: NONE IDENTIFIED BY G6-G8

- `FEAT-018-TIMING-001` remains a separate FEAT-018 remediation and is outside P2-T4.
- The inherited mypy findings remain unchanged and outside P2-T4: the three existing
  arg-type findings at `learning_media_resolver.py:101` and
  `learning_media_fallback.py:82` and `learning_media_fallback.py:85`.
- The inherited Ruff findings remain unchanged and outside P2-T4: E501 at
  `learning_media.py:79`, I001 at `test_learning_media_scenario_matrix.py:1`, and E501 at
  `test_learning_media_scenario_matrix.py:14`.
- The Policy-B architecture baseline remains unchanged and must be reported truthfully as
  `ARCHITECTURE_INVALID`: exactly one approved `application imports an outer layer` finding at
  `backend/src/sketch2life/application/services/backend_ai_workflow.py`, with validator
  fingerprint `fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5`.
- P2-T5, integration/runtime/live, provider/model, GPU, Lightning, network, migration,
  production, and PR/push activity remain not approved.

## P2-T5 fixture-only v1 owner decision bundle approval — 2026-09-19

The Project Owner approved the exact `P2T5.OwnerDecisionBundleV3@1.0` planning decision object
after the read-only confirmation audit at
`tmp/p2-t5-v3-owner-confirmation-20260919-r2/REPORT.md`.

The approved decision is bound to the current pre-G1 plan inputs:

| Path | Revision | Raw SHA-256 | Prospective Git blob |
|---|---:|---|---|
| `features/FEAT-003-multimodal-understanding/plan/PLAN.md` | 7 | `c70ba9012c2d30467fd485d37b1a8312d45a9a3574609d94bf774264f05cbefb` | `831ded8c7676130ac39e279fbba36022ee033fe4` |
| `features/FEAT-003-multimodal-understanding/plan/P2_T5_EVALUATION_HARNESS_PLAN.md` | 0.14 | `2c5d9d2b1c4780585f874ea768dafd12caa3459b0bb6a51bd0cb008fd7608280` | `ba77759c0ff1ec8a416c11a4a6e6795954aa7fc1` |

The owner decision freezes the bundle's eleven P2-T5 identities, exact T4/B4/ASR/conflict rule
bindings, report canonicalization, exact fixture IDs and 20/12/8/40 matrix, oracle independence,
metric formulas and unavailable states, deterministic correlation/retry/recapture semantics,
CPython 3.13.5 PRE-G1 policy, `NO_PYTHON_LOCKFILE`, privacy/output boundaries, inherited
baseline fingerprints, deferred OD-1/OD-17/OD-18, and the separate G1-G9 topology.

This is a planning decision only. It authorizes no G1, G2, implementation, fixture/media,
evidence, runtime, provider/model, GPU, Lightning, network, migration, production, integration,
commit, push, or PR activity. The plans must next be synchronized without semantic change,
independently reviewed, and checkpointed before a separate G1 approval can be requested.

```text
P2-T5: PRE-G1
OWNER DECISION BUNDLE V3: APPROVED
G1: NOT GRANTED
G2: NOT GRANTED
IMPLEMENTATION: NOT APPROVED
FIXTURE/MEDIA/EVIDENCE: NOT AUTHORIZED
RUNTIME/LIVE: NOT APPROVED
```

## P2-T5 G2 exact implementation approval — 2026-09-20

The Project Owner's direct authorization was:

> I approve the P2-T5 G2 exact implementation scope exactly as listed in the reviewed draft,
> including all 54 individually named source, test, fixture/oracle, and synthetic media paths.
>
> The G2 governance record must be directly parented to:
> `6464ad700a424fe7c0e0e1fcac34b69571be82a4`
>
> The G2 record may modify only these governance paths:
> `features/FEAT-003-multimodal-understanding/approvals/TASK_APPROVAL.md`,
> `features/FEAT-003-multimodal-understanding/CONTEXT.md`, and
> `features/FEAT-003-multimodal-understanding/DECISIONS.md`.
>
> No other path is authorized. This does not authorize evidence, runtime, provider/model, GPU,
> Lightning, network, migration, production, push, or PR.

The Project Owner approved the exact P2-T5 fixture-only v1 implementation scope as listed in
this section. This G2 governance record is directly parented to the G1 approval record commit
`6464ad700a424fe7c0e0e1fcac34b69571be82a4`. The G2 record may modify only these three
governance paths; no other governance or implementation path is authorized by this record:

- `features/FEAT-003-multimodal-understanding/approvals/TASK_APPROVAL.md`
- `features/FEAT-003-multimodal-understanding/CONTEXT.md`
- `features/FEAT-003-multimodal-understanding/DECISIONS.md`

The exact implementation allowlist is 54 individually named paths: 10 source/test paths, four
fixture/oracle JSON paths, and 40 synthetic media paths. No 55th path, `__init__.py`, packaging or
entrypoint file, fake-adapter change, T1–T4 path, evidence path, or unrelated governance path is
authorized.

### Immutable G1 bindings

- G1 plan checkpoint: `4b2bd6012c4069dcee021497670da13cabbe852c`.
- G1 approval record (direct parent required for this G2 record):
  `6464ad700a424fe7c0e0e1fcac34b69571be82a4`.
- `PLAN.md`, revision 8: 61590 bytes, raw SHA-256
  `4c52ccf63320de411d3551933e75a1ec05479a9471df68d8ef67fb2ee1b37b35`, Git blob
  `6db2089ca9f2d38f8c58f28b22de2c2a58ceb26a`.
- `P2_T5_EVALUATION_HARNESS_PLAN.md`, revision 0.15: 211691 bytes, raw SHA-256
  `2a102acd689c0b53854562694692ce3a139ecdbbdee88f7c9fce7c136a5eea20`, Git blob
  `f9f81f9c1dbbd8fe92d8083ce163ac85f3721ce4`.

### Exact G2 environment and inherited baselines

The canonical interpreter is `backend/.venv/Scripts/python.exe`, CPython 3.13.5. The PATH
interpreter (3.14.5) is not acceptable, and packages may not be installed, upgraded, resolved,
or substituted. `backend/pyproject.toml` is bound to source commit
`0fda47f432212c6d79e467c8064c116ae468d34d`, Git blob
`8f8a344f505be839b9bd0bd0d640fa0d18cf6b33`, and raw SHA-256
`9ca3a54905d11fdb7f30a84356d23741f256b2115b254bcc9fba4efacdf17df6`. No Python lockfile is
present (`NO_PYTHON_LOCKFILE`).

The exact installed package set contains 55 distributions. Its canonical binding is the SHA-256
`217f418ce003e9279bdcbe863437b90d0219f43264c3dafbcd7f6d459cefed48` of sorted UTF-8
`<distribution-name>==<version>` lines joined with LF and one final LF. The materialized set is:

```text
alembic==1.20.0
annotated-doc==0.0.5
annotated-types==0.8.0
anyio==4.15.1
av==18.1.0
boto3==1.43.95
botocore==1.43.95
click==8.5.0
colorama==0.4.6
croniter==6.2.4
fastapi==0.141.1
greenlet==3.5.6
h11==0.16.0
httpcore2==2.13.0
httptools==0.8.0
httpx2==2.13.0
idna==3.19
iniconfig==2.3.0
jmespath==1.1.0
librt==0.15.0
Mako==1.4.1
MarkupSafe==3.0.3
mypy_extensions==1.1.0
mypy==1.20.2
packaging==26.3
pathspec==1.1.1
pluggy==1.6.0
psycopg==3.3.5
psycopg-binary==3.3.5
pydantic_core==2.46.5
pydantic==2.13.5
pydantic-settings==2.15.0
Pygments==2.21.0
pytest==8.4.2
pytest-asyncio==1.4.0
python-dateutil==2.9.0.post0
python-dotenv==1.2.3
PyYAML==6.0.3
redis==6.4.0
rq==2.12.0
ruff==0.16.7
s3transfer==0.19.2
six==1.17.0
sketch2life-backend==0.0.0
SQLAlchemy==2.0.54
starlette==1.6.0
structlog==25.5.0
truststore==0.10.4
typing_extensions==4.16.0
typing-inspection==0.4.4
tzdata==2026.4
urllib3==2.8.0
uvicorn==0.53.0
watchfiles==1.2.0
websockets==17.1
```

The validator identities are immutable: `validate_harness.py` source commit
`0f0c546193f698ea2987a956348714dea2dc95e7`, blob
`c2ffe59008c8ab86332953621faa328b76bd55bb`, raw SHA-256
`0804eabbaecf471f191e259760e48aa0dc2d5a4d23da5d38336d8ede2f09d232`;
`validate_repository_security.py` source commit `0f0c546193f698ea2987a956348714dea2dc95e7`,
blob `08a8614f1152e0a1f5158430f26a143a0eb6e66b`, raw SHA-256
`efd691df935565d1fa148b5b4a765ef77c90d701d210fc5e869bfbd1548dd210`;
`validate_skeleton.py` source commit `1c2c6d357b0c27cd19f790e748f9525e3e50e2b2`, blob
`e68970c4062837f982707123e18db480e1e6e06e`, raw SHA-256
`82da58bfdd3fd7f406e6d9597b33a4375ba0c591e9a455c74d92ee0aba8d4a39`; and
`validate_architecture.py` source commit `0f0c546193f698ea2987a956348714dea2dc95e7`, blob
`efe2f642c403e2fa3c00e650a2ac505e2bf9076c`, raw SHA-256
`fa236c8d389b608251153d601fc370efe3f3e2479446ca4a56a3d395f892e0b5`.

The inherited baseline is preserved exactly: Policy B reports one `ARCHITECTURE_INVALID`
finding for `backend/src/sketch2life/application/services/backend_ai_workflow.py` (application
imports an outer layer); mypy retains the three recorded `learning_media_*` arg-type findings;
Ruff retains the three recorded `learning_media.py`/`test_learning_media_scenario_matrix.py`
findings. `FEAT-018-TIMING-001` remains a separate out-of-scope finding and is not a P2-T5
regression.

### Exact 54 implementation paths

Source and tests (10):

1. `backend/src/sketch2life/contracts/schemas/p2_t5_evaluation.py`
2. `backend/src/sketch2life/application/services/p2_t5_evaluation.py`
3. `backend/src/sketch2life/application/services/p2_t5_scoring.py`
4. `backend/src/sketch2life/infrastructure/ai/p2_t5_fixture_loader.py`
5. `backend/src/sketch2life/interfaces/cli/p2_t5_evaluation.py`
6. `backend/tests/contract/test_p2_t5_evaluation_contract.py`
7. `backend/tests/unit/test_p2_t5_evaluation.py`
8. `backend/tests/unit/test_p2_t5_scoring.py`
9. `backend/tests/unit/test_p2_t5_cli.py`
10. `backend/tests/unit/test_p2_t5_privacy.py`

Fixture/oracle JSON (4):

11. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/manifest-v1.json`
12. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/cases-v1.json`
13. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/expected-v1.json`
14. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/matching-rule-v1.json`

Synthetic media (40):

15. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-001.png`
16. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-001.wav`
17. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-002.png`
18. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-002.wav`
19. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-003.png`
20. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-003.wav`
21. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-004.png`
22. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-004.wav`
23. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-005.png`
24. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-005.wav`
25. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-006.png`
26. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-006.wav`
27. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-007.png`
28. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-007.wav`
29. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-008.png`
30. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-008.wav`
31. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-009.png`
32. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-009.wav`
33. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-010.png`
34. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-010.wav`
35. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-011.png`
36. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-011.wav`
37. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-012.png`
38. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-dev-012.wav`
39. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-001.png`
40. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-001.wav`
41. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-002.png`
42. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-002.wav`
43. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-003.png`
44. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-003.wav`
45. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-004.png`
46. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-004.wav`
47. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-005.png`
48. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-005.wav`
49. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-006.png`
50. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-006.wav`
51. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-007.png`
52. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-007.wav`
53. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-008.png`
54. `features/FEAT-003-multimodal-understanding/fixtures/p2-t5-evaluation-v1/media/feat003-p2t5-heldout-008.wav`

G2 authorizes only preparation of the exact 54-file offline fixture-only implementation. G3 may
start only after this G2 record exists; G4/G5/G6/G7/G8/G9 remain future gates. Evidence is a
separate G7 authorization. Integration, runtime/live, provider/model, GPU, Lightning, network,
migration, production, push, and PR activity remain not approved. This record does not authorize
any self-referential commit-SHA edit.

```text
P2-T5: G1 APPROVED
G2: APPROVED_FOR_EXACT_54_FILE_FIXTURE_ONLY_IMPLEMENTATION
IMPLEMENTATION: NOT STARTED
G3: NOT STARTED
G4-G9: NOT STARTED
FIXTURE/MEDIA: AUTHORIZED ONLY WITHIN THE EXACT 54-PATH G2 SCOPE
EVIDENCE: NOT AUTHORIZED (G7 SEPARATE)
RUNTIME/LIVE/PROVIDER/MODEL/GPU/LIGHTNING/NETWORK: NOT APPROVED
```

## P2-T5 G1 fixture-only plan approval — 2026-09-19

The Project Owner approved G1 against the immutable pre-G1 plan checkpoint
`4b2bd6012c4069dcee021497670da13cabbe852c`, whose direct parent is
`f11a6f4fee81032a677b492303cdecd9b09663d4`. The checkpoint contains exactly the
two synchronized P2-T5 plan paths below.

| Path | Revision | Raw bytes | Raw SHA-256 | Git blob ID |
|---|---:|---:|---|---|
| `features/FEAT-003-multimodal-understanding/plan/PLAN.md` | 8 | 61590 | `4c52ccf63320de411d3551933e75a1ec05479a9471df68d8ef67fb2ee1b37b35` | `6db2089ca9f2d38f8c58f28b22de2c2a58ceb26a` |
| `features/FEAT-003-multimodal-understanding/plan/P2_T5_EVALUATION_HARNESS_PLAN.md` | 0.15 | 211691 | `2a102acd689c0b53854562694692ce3a139ecdbbdee88f7c9fce7c136a5eea20` | `f9f81f9c1dbbd8fe92d8083ce163ac85f3721ce4` |

G1 freezes the approved P2-T5 fixture-only v1 plan and its documented contract,
metrics, privacy, reproducibility, topology, and evidence-authorization policy.
It does not grant G2, implementation, fixture/media creation, evidence creation,
integration, runtime/live, provider/model, GPU, Lightning, network, migration,
production, push, or PR authority. G2 remains a separate exact-path approval and
must have this G1 record commit as its direct parent. The G1 commit SHA is reported
outside tracked content and is not embedded in the records.

```text
P2-T5: G1 APPROVED
OWNER DECISION BUNDLE V3: APPROVED
G1: APPROVED
G2: NOT GRANTED
IMPLEMENTATION: NOT APPROVED
FIXTURE/MEDIA/EVIDENCE: NOT AUTHORIZED
RUNTIME/LIVE: NOT APPROVED
```

## P2-T5 G7 exact evidence-authorization decision - 2026-09-21

Owner approval is recorded for the exact draft at:

`tmp/p2-t5-g7-evidence-authorization-draft-20260921-01/DRAFT.md`

The approved draft raw SHA-256 is:

`eb163b86954d0355189375480145828e8ab9372f89eba0f7f196082427caca10`

This record authorizes only the separately governed P2-T5 G7 authorization-record
mutation and, after this record exists, creation of the two exact evidence files
listed below. It does not authorize runtime execution, live provider/model
execution, G8, G9, push, PR, or unrelated changes. The authorization record
commit must contain only this file; it must not contain either evidence file.

### Traceable evidence assembler identity

| Field | Value |
|---|---|
| Model/session | `Codex / GPT-5` (system-reported) |
| Stable session ID | `01a0c26b-d0e5-7861-9da6-d495e8667e61` (`CODEX_SESSION_ID` / `CODEX_THREAD_ID`) |
| Authorization-record UTC timestamp | `2026-09-21T06:13:46.5812190Z` |
| Role | `Codex agent; G7 evidence author/assembler` |

If the executor creating the evidence cannot produce this traceable identity,
the exact required stop is
`G7: BLOCKED_PENDING_TRACEABLE_EVIDENCE_ASSEMBLER_IDENTITY`; no approval,
evidence, staging, commit, or push may proceed.

### Exact run and evidence outputs

| Field | Exact value |
|---|---|
| Owner run ID | `p2-t5-g7-evidence-20260921-01` |
| JSON output | `features/FEAT-003-multimodal-understanding/evidence/P2_T5_G7_EVIDENCE_CREATION_p2-t5-g7-evidence-20260921-01.json` |
| Markdown output | `features/FEAT-003-multimodal-understanding/evidence/P2_T5_G7_EVIDENCE_CREATION_p2-t5-g7-evidence-20260921-01.md` |

Exactly these two evidence files may be created. No raw media, transcripts,
prompts, provider payloads, credentials, tokens, endpoints, host paths,
usernames, hostnames, environment values, raw exceptions or stack traces,
unapproved labels, child data, or live-execution claims may be included.
The Markdown output is sanitized only and must contain closed-contract values.

The JSON output must use identity `P2T5.P2T5EvaluationReportV1@1.0` and
canonicalization `P2T5-REPORT-CANONICAL-JSON-V1`. It must bind the stable run
ID, G5 implementation, G6 checkpoint, fixture package, T4 policy, environment
identity, deterministic core, typed findings/statuses, and privacy redactions.
It must not contain a self-hash or self-blob binding. The report is fixture-only
and deterministic; no runtime, provider, model, GPU, network, or live execution
is authorized.

### G5 and G6 checkpoint bindings

| Binding | Value |
|---|---|
| G5 implementation commit | `323ebf9d78fff10e204875770672b21e4b58dec9` |
| G5 parent | `9d6340672c5d1bbdd7a95004f5fad811718ec4a0` |
| G5 tree | `09f9cea8addd6922916514dde96b1a4c583ef24f` |
| G5 ordered 54-path digest | `dabf603ea2ccd6296a1f547a6b250b5f918f729048de1275d02ec9b7e03bbcf1` |
| G6 report | `tmp/p2-t5-g6-checkpoint-verification-20260920/REPORT.md` |
| G6 report bytes | `19412` |
| G6 report raw SHA-256 | `c7d1057daa2ee7175675f5e6513dbca0520710ab3a1f73b5c7e829687089e410` |
| G6 status | `PASS_WITH_ACCEPTED_FINDINGS` |

G6 accepted findings are bound as recorded in its report: four inherited or
out-of-scope pytest findings (`FEAT-018-TIMING-001` and three semantic catalog
findings), three inherited mypy findings, three inherited Ruff findings, the
owner-accepted Policy B architecture finding, two accepted blank-at-EOF
warnings in `cases`/`expected`, and the report limitations.

### Fixture, T4, and environment bindings

| Artifact | Bytes | Raw SHA-256 |
|---|---:|---|
| `fixtures/p2-t5-evaluation-v1/manifest-v1.json` | 17336 | `17f2a1af1f3644b9178283d8097ec5b73d11e54ae4e76da22be23fb66e07d21d` |
| `fixtures/p2-t5-evaluation-v1/cases-v1.json` | 13527 | `f715c8b65697b747751720726c10f1fcf744d7ce4cfe4fd760565c39c519fcbb` |
| `fixtures/p2-t5-evaluation-v1/expected-v1.json` | 4838 | `23b7668f9ca30814e325cf1ba4f5f1ccae03bd37b52b3e49198e045fb5235b83` |
| `fixtures/p2-t5-evaluation-v1/matching-rule-v1.json` | 1053 | `43fa4f06e456cf1e1b7a2d79c7ad515d4caf89c556a590790f5ab0b6879f3a49` |

The fixture package is `p2-t5-evaluation-v1` version `1.0`, with 20 entries
(12 development and 8 held-out) and 40 synthetic-only media references.

| T4 binding | Value |
|---|---|
| Policy identity | `P2T4FusionPolicyConfigV1@1.0` |
| Policy SHA-256 | `4b378f69a33b86aeefc7443a23ac819e46b986132525cdd8a55d112dfb96415c` |
| Upstream contracts | `P2.AsrResultV1@1.0`, `P2.VisionUnderstandingResultV1@1.0` |
| Deterministic profile | `FAKE_DETERMINISTIC_V1` |
| Fused contract | `P2T4.P2T4FusedResultV1@1.0` |
| Rejection contract | `P2T4.P2T4FusionInputRejectionV2@2.0` |

| Environment binding | Value |
|---|---|
| Python executable | `backend/.venv/Scripts/python.exe` |
| Python | `CPython 3.13.5` |
| Lockfile state | `NO_PYTHON_LOCKFILE` |
| Package identity hash | `217f418ce003e9279bdcbe863437b90d0219f43264c3dafbcd7f6d459cefed48` |
| P2-T5 plan revision | `0.15` |
| P2-T5 plan raw SHA-256 | `2a102acd689c0b53854562694692ce3a139ecdbbdee88f7c9fce7c136a5eea20` |

### Authorized topology and status

```text
G5 implementation checkpoint
  -> G7 authorization record (this record; direct parent G5)
  -> G7 evidence creation (exactly two files)
  -> G7 evidence checkpoint (direct parent authorization record)
  -> G8 independent review (separate approval required)
  -> G8 checkpoint
  -> G9 (separate approval required)
```

```text
P2-T5: G7 AUTHORIZATION RECORDED
G5: CHECKPOINT BOUND
G6: PASS_WITH_ACCEPTED_FINDINGS
G7 EVIDENCE: AUTHORIZED, NOT YET CREATED
G8: NOT STARTED
G9: NOT STARTED
RUNTIME/INTEGRATION/LIVE: NOT APPROVED
```

After this authorization commit, the executor may create exactly the two named
evidence files. The evidence checkpoint must verify exact file count, raw
SHA-256, Git blob IDs, unchanged bytes, and absence of extra paths; it must be
a direct child of this authorization commit. No amend, split, push, or PR is
authorized.

## P2-T5 G9 governance-closeout authorization and completion — 2026-09-21

The Project Owner approved the P2-T5 G9 governance-closeout authorization
exactly as bound by draft raw SHA-256
`8c6b8f79bc10a132d2abdede86caa5beb9299fddb876a383344f9434edf27765`.
This section authorizes exactly one local governance-only G9 commit whose
direct parent is `d9d32d9a7ff7977d86dd0596d0447a10abd75098`. The resulting G9
commit SHA is intentionally not written into tracked content and must be
reported externally.

Exactly these six literal repository-relative paths may change in that commit:

1. `features/FEAT-003-multimodal-understanding/approvals/TASK_APPROVAL.md`
2. `features/FEAT-003-multimodal-understanding/plan/PLAN.md`
3. `features/FEAT-003-multimodal-understanding/plan/P2_T5_EVALUATION_HARNESS_PLAN.md`
4. `features/FEAT-003-multimodal-understanding/CONTEXT.md`
5. `features/FEAT-003-multimodal-understanding/DECISIONS.md`
6. `features/FEAT-003-multimodal-understanding/evidence/README.md`

No wildcard, seventh path, implementation, test, fixture, media, evidence
payload, freeze/package artifact, erratum, or unrelated path is authorized.
The G7 JSON, G7 Markdown, G8 correction, and G8 review record remain immutable.

### Immutable G5–G8 topology and artifact identities

| Gate/artifact | Binding |
|---|---|
| G5 implementation checkpoint | `323ebf9d78fff10e204875770672b21e4b58dec9` |
| G7 authorization commit | `bea4da49c9dad6228446747bfad0df3bb1ac79c5` |
| G7 evidence checkpoint | `78e08ab11a7ac1f8b42dac8459f6088e4496fcd3` |
| G8 correction commit | `55d8a6426a27533980e3f5bd2210c784e73eaa44`; direct parent `78e08ab11a7ac1f8b42dac8459f6088e4496fcd3` |
| G8 review checkpoint / required G9 parent | `d9d32d9a7ff7977d86dd0596d0447a10abd75098`; direct parent `55d8a6426a27533980e3f5bd2210c784e73eaa44` |

| Artifact | Repository-relative path | Raw SHA-256 | Identity |
|---|---|---|---|
| G8 final report (ignored/untracked) | `tmp/p2-t5-g8-independent-evidence-review-20260921-final/REPORT.md` | `488d41732fee30611488838052b27a8a4b4d1f3057a3f54c0fe87b8f616252dc` | prospective Git blob / `git hash-object`: `5988bc338c34d25c67e7eeb3d0dc995244a64a7f`; not a committed-tree blob |
| G8 review record | `features/FEAT-003-multimodal-understanding/evidence/P2_T5_G8_INDEPENDENT_EVIDENCE_REVIEW_20260921-final.md` | `31eee8922098809324b5d3130f0465d9043fd5b6527595ed2fc912880a85bc41` | Git blob `9c7d0fe19f92ee48aae8a7fc7d2fab167ba604a5` |
| G7 JSON evidence | `features/FEAT-003-multimodal-understanding/evidence/P2_T5_G7_EVIDENCE_CREATION_p2-t5-g7-evidence-20260921-01.json` | `e574a02dc3b018162eb08fb63eaff7a1ad0be1370a736d6d405d1c50c82d116a` | Git blob `d029fb364a8076bb617acc710b8d1ba8942b3631` |
| G7 Markdown evidence | `features/FEAT-003-multimodal-understanding/evidence/P2_T5_G7_EVIDENCE_CREATION_p2-t5-g7-evidence-20260921-01.md` | `deaa2ecba7563f453a6f84bdb919854b76ce51cf3e6ded8d0a336542f4fd6746` | Git blob `4bf34c69f78354f4c201ddebb5b5c5a93bdf9b83` |

The G8 verdict is `PASS`, the G7 evidence checkpoint is complete and bound,
and the G7 assembler, G8 correction author, and independent G8 reviewer
sessions remain distinct as recorded in the immutable G8 review record.

### Preserved G6 disposition and boundaries

The closeout preserves `G6: PASS_WITH_ACCEPTED_FINDINGS`, including the single
owner-accepted Policy-B architecture baseline reported truthfully as
`ARCHITECTURE_INVALID`, inherited mypy and Ruff findings, the out-of-scope
`FEAT-018-TIMING-001` finding, accepted inherited/out-of-scope pytest and
blank-at-EOF findings, and the sanitized
`WIN_TEMP_DIRECTORY_PERMISSION_DENIED` limitation. The fixture-only
12-case `DEVELOPMENT` authorization, privacy/output exclusions, and all
G7/G8 hashes and reviewer provenance remain unchanged.

This G9 closeout is governance-only. It grants no runtime, integration, live,
provider/model, GPU, Lightning, network, migration, production, mobile, API,
storage, push, or PR authority. It does not authorize a separate G9 evidence
record or any modification outside the six paths above.

```text
P2-T5: COMPLETE — GOVERNANCE-CLOSED
CLOSEOUT: COMPLETE_WITH_ACCEPTED_G6_FINDINGS
G6: PASS_WITH_ACCEPTED_FINDINGS
G7: COMPLETE — EVIDENCE CHECKPOINT BOUND
G8: PASS
G9: COMPLETE
P2-T5 IMPLEMENTATION: COMPLETE AT G5 CHECKPOINT
RUNTIME/INTEGRATION/LIVE: NOT APPROVED
PROVIDER/MODEL/GPU/LIGHTNING/NETWORK: NOT APPROVED
```
