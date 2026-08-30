# Task approval

- Status: APPROVED (P2-T1, P2-T2 Phase A, and P2-T2 Phase B)
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

## Explicitly not approved

- P2-T3 through P2-T5, mobile/API/session/job orchestration, Gate A UI, database/storage/queue integration, real child data, and any provider credentials.

## Notes

FEAT-012 and ADR-0006 still govern the standalone Sprint 1 boundary. Person 2 does not own Gate A UI or backend job orchestration in Sprint 1.
