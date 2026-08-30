# Task approval

- Status: APPROVED (P2-T1 and P2-T2 Phase A only)
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

## Explicitly not approved

- P2-T2 Phase B: `faster-whisper`/Whisper dependency or model weights, GPU/provider access, real adapter execution, live ASR profile comparison, benchmark evidence, and profile-freeze recommendation.
- P2-T3 through P2-T5, mobile/API/session/job orchestration, Gate A UI, database/storage/queue integration, real child data, and any provider credentials.

## Notes

FEAT-012 and ADR-0006 still govern the standalone Sprint 1 boundary. Person 2 does not own Gate A UI or backend job orchestration in Sprint 1.
