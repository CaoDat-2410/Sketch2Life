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

- Any P2-T3 work outside the approved Phase B B1–B5 scope, P2-T4 through P2-T5, mobile/API/session/job orchestration, Gate A UI, database/storage/queue integration, real child data, and any provider credentials.

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

## Notes

FEAT-012 and ADR-0006 still govern the standalone Sprint 1 boundary. Person 2 does not own Gate A UI or backend job orchestration in Sprint 1.
