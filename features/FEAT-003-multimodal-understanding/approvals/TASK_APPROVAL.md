# Task approval

- Status: APPROVED (P2-T1, P2-T2 Phase A, P2-T2 Phase B, and P2-T3 Phase A)
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

## Explicitly not approved

- P2-T3 Phase B through P2-T5, mobile/API/session/job orchestration, Gate A UI, database/storage/queue integration, real child data, and any provider credentials.

## Notes

FEAT-012 and ADR-0006 still govern the standalone Sprint 1 boundary. Person 2 does not own Gate A UI or backend job orchestration in Sprint 1.
