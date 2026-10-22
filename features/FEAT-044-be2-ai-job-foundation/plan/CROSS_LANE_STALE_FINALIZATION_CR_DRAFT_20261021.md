# BE2-01 / BE2-08 authoritative stale finalization CR — draft 2026-10-21

- Status: DRAFT / OWNER_C2_A_DESIGN_DIRECTION / CONTRACT_ADOPTION_PENDING.
- Owning foundation card: BE2-01 / FEAT-044; video participant: BE2-08 / FEAT-050.
- Owner decision: FEAT-057 `evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D3_20261021.md`, C2-A and its conditions; D1/D2 remain applicable.
- Source basis: FEAT-057 source manifest Rev4, SHA256 `2EAA11FCA7B510CA738D34ECED9EFD164C7734FCA8E6AD4792257F03AA68591F`.
- Reviewed parents: FEAT-044 UoW scope Rev5 and FEAT-057 slice plan Rev6; Claude rereview 3 returned CHANGES_REQUIRED.
- Branch/HEAD: `feature/be2-backend-ai-integration` / `1649b72978877d82b4d7662040ff3555dee0a3a7`; dirty source identity is the per-file manifest, not HEAD alone.
- Authority: proposed versioned CR and future verification requirements only. C2-A settles design direction; it does not adopt a BE1 artifacts contract or approve source/schema/test implementation.

## 1. Owner direction and correction

Authoritative context-stale success is B-stale, a foundation-owned finalization commit. It is not a rejection and must not be redirected into F-reject merely because its receipt disposition is not ACCEPTED.

The proposed B-stale commit atomically persists all of the following:

1. The foundation job transition to SUCCEEDED with result disposition STALE and the exact validated result refs.
2. The authoritative foundation completion receipt with disposition STALE and the original claim fingerprint.
3. The paired BE2-08 terminal stale outcome selected by D2, without an accepted artifact or ready-for-review state.
4. A durable keep-private/stage-cleanup intent for verified owned output refs, through the existing foundation quarantine-intent/outbox primitives, plus audit.

BE2-01 owns the UoW and the change to the stale branch of `AiJobService._decide_completion`. BE2-08 is a participant restricted to its video rows and cannot begin, commit, or roll back the UoW. External media/provider work stays outside all lifecycle UoWs.

The stale-cleanup intent is new proposed behavior. Source currently commits context-stale success and receipt without adding a stale quarantine intent. Worker `_quarantine` suppresses errors and cannot prove durable request acknowledgement or physical cleanup.

## 2. Complete completion classification

Authority, state and semantic outcome jointly determine the boundary. The same receipt disposition can occur for different lifecycle outcomes.

| Decision after source checks | Candidate boundary | Job/run mutation | Receipt and effects |
|---|---|---|---|
| Eligible, validated safe success, current context | B-accepted | Job SUCCEEDED/ACCEPTED; paired succeeded run with exact artifact and ready state | Authoritative ACCEPTED receipt and audit. |
| Eligible, validated safe success, context superseded | B-stale | Job SUCCEEDED/STALE with result refs; paired terminal stale run with no artifact/ready state | Authoritative STALE receipt; under C2-A, verified-ref keep-private intent in the same commit. |
| `OutcomeKind.FAILURE` after preconditions and eligibility pass | F-failure | Foundation chooses failed_retryable or failed_exhausted; video mirrors the outcome | Authoritative receipt ACCEPTED acknowledges the failure claim; it does not accept video output. |
| Current eligibility denied after preconditions pass | F-reject | Paired cancelled outcome | Authoritative REJECTED receipt; owned-ref intent where applicable. |
| Unsafe success output | F-reject | Paired blocked_unsafe outcome | Authoritative REJECTED receipt and owned-ref intent. |
| Malformed success output | F-reject | Paired failed_exhausted outcome | Authoritative REJECTED receipt; intent only for verified owned refs. |
| `JOB_CANCELLED`, `JOB_TERMINAL`, `ATTEMPT_SUPERSEDED` precondition | F-reject intent-only / incident | Preserve the current job/run winner | Non-authoritative response; durable audit and owned-ref intent may be written; do not occupy the authoritative completion-receipt slot. |
| `INVALID_STATE`, `INPUT_MISMATCH`, or claim rejected by `_normalise_claim` | Audit-only incident | No job/run lifecycle commit | Durable audit is allowed and required by the existing incident behavior; no authoritative completion receipt or temporary-guard quarantine. |
| Existing completion receipt | Lookup/replay | Preserve original authoritative winner | Exact fingerprint replays the stored receipt; a conflicting fingerprint records conflict audit and fails closed. |

An unchanged guard can return STALE without an authoritative transition. It does not make an existing video run stale. A failure claim with receipt ACCEPTED must not enter the current success-only worker receipt path.

Current source `accept_completion` writes non-authoritative incident effects within its current transaction and does not persist an authoritative completion receipt for them. `_completion_replay` uses the separate `_commit_incident` helper for a conflicting prior receipt. Proposed boundary routing must preserve durable incident semantics; this CR does not claim those routing changes already exist. “No lifecycle commit” does not mean no persistence.

## 3. Valid paired states

`AiJob.result_disposition` and `CompletionReceipt.disposition` are distinct fields. Do not infer the job result axis from a receipt alone.

| Persisted job state | Job result_disposition | Authoritative completion receipt disposition | Candidate paired run |
|---|---|---|---|
| SUCCEEDED | ACCEPTED | ACCEPTED | Succeeded, exact accepted artifact, ready for review. |
| SUCCEEDED | STALE | STALE | Video-owned terminal stale, no artifact and no ready state. |
| FAILED_RETRYABLE / FAILED_EXHAUSTED from failure claim | None | ACCEPTED | Matching failure outcome; no accepted artifact. |
| CANCELLED from completion eligibility denial | None | REJECTED | Cancelled; no accepted artifact. |
| BLOCKED_UNSAFE | REJECTED | REJECTED | Blocked unsafe; no accepted artifact. |
| FAILED_EXHAUSTED from malformed output | None | REJECTED | Failed exhausted; no accepted artifact. |
| Queued/start/retry, administrative cancellation, dispatch loss or timeout | Its source-defined result axis; no fabricated disposition | No completion receipt is required solely for that lifecycle operation | Explicit paired transition; S binds attempt_id, retry clears it, and pre-start dispatch loss remains unbound. |

A non-authoritative guard response never replaces the stored winner or changes this table. Foundation JobState gains no stale state. The BE2-08 CR must change its model state type, legal transitions, codec, terminal-row guard and versioned projection consistently; current source does not support that complete contract.

## 4. Owned refs, fixed reason and deterministic intent identity

An intent may include only artifact refs supplied by the BE1 artifacts port and verified as produced by the exact foundation job and attempt. Use the actual descriptors and validated output identity. A private-stage key, pin digest, video id or caller-supplied ref is not an artifact-owner descriptor.

If any requested cleanup target cannot be mapped and verified, fail closed before the proposed B-stale commit. Do not fabricate a ref, issue a broad cleanup, or commit a partial job/run/intent result. Missing mapping remains a contract/adoption gate and pending recovery; it is not proof of a safe discard.

Candidate canonical reason is the existing source code `STALE_CONTEXT`. BE1 artifacts-owner adoption must explicitly accept that reason for keep-private/stage cleanup of these refs even when foundation `result_refs` contains them and job state is SUCCEEDED with disposition STALE. This document does not claim BE1 has signed that contract.

Reuse the verified canonical material of the existing `_quarantine_intent` algorithm:

```text
canonical_sha256({
  "kind": "quarantine",
  "job_id": exact_job_id,
  "attempt_id": exact_attempt_id,
  "artifact_refs": sorted_verified_owned_refs,
  "reason": "STALE_CONTEXT",
  "fingerprint": original_claim_fingerprint
})
```

The original claim fingerprint is produced by `CompletionClaim.fingerprint()` before `_normalise_claim`. It is not a digest reconstructed from a later fallback failure code or reason. Diagnostics are excluded by that fingerprint formula. Exact claim/stage inputs must have authenticated durable recovery provenance before restart recovery is claimed.

The event id is computed once for the committed decision; delivery/redelivery uses that stored id and reason. It is not recalculated from changing current policy or another reason. `STALE_CONTEXT` is the candidate fixed reason for this CR, not an adopted artifact-owner capability.

## 5. Accepted-reference protection and effect semantics

The intent authorizes only keep-private/stage-cleanup behavior after adoption. It is never permission to delete or hide an accepted artifact, nor proof that physical cleanup occurred.

The adopted storage/artifacts protocol must protect accepted references atomically with acceptance and cleanup:

- If accepted publication wins first, later or already queued cleanup cannot hide/delete that accepted ref. An absent receipt read before acceptance cannot authorize a later unsafe effect.
- If cleanup runs first, subsequent acceptance must revalidate the exact bytes/ref and protection state under the same adopted arbitration protocol. It cannot commit acceptance of a now-invalid or removed artifact. Once valid acceptance commits, its reference is protected from every pending/replayed cleanup intent.
- An old guard claiming JOB_TERMINAL or ATTEMPT_SUPERSEDED is not a bypass of this protection. Accepted references remain protected even if a stale worker still owns a private-stage handle.
- Failed/unknown protection checks leave the effect pending. Intent durability and actual storage action require separate evidence. No cleanup acknowledgement is inferred from a worker swallowing an exception.

Both winner orders require independent evidence; this document supplies no storage implementation or race-test result. If the storage authority cannot adopt the protocol, stale cleanup and the corresponding B-stale implementation remain blocked.

## 6. Rejection identity and receipt recovery

F-reject remains a separate foundation-owned commit under D1. It must not be used as the B-stale receipt boundary. A business rejection re-evaluated before its first commit uses the current locked decision; the committed operation decision and effect identity must then become immutable for replay.

The proposed recovery-input/operation journal needs a versioned schema/contract decision. Same operation identity with changed canonical input conflicts; it cannot silently create a different event. A genuinely new authorized incident needs a distinct operation identity and can create a second effect. Intent-only incidents do not get a fabricated authoritative completion receipt.

Accepted B recovery independently reconstructs completion_key from authenticated persisted run/pin/strategy, media-operation identity, artifact material and blob hash. The adapter compares supplied input to its own reconstructed value and returns that independently derived value; it cannot echo the caller's completion_key.

B-stale/rejected runs have no accepted artifact. Recovery therefore requires the authenticated durable private-stage journal containing exact stage/key material and a verified authoritative receipt/effect decision. A fingerprint alone cannot reconstruct the claim or artifact. Unknown storage, receipt or operation identity remains pending; no rerender, refund or cleanup completion is inferred.

The current worker receipt contract requires `video_run=None` for a non-ACCEPTED receipt. A separately adopted adapter must prove the persisted stale pair while preserving that shape, or a versioned receipt CR must expose a typed outcome. No new shape is implied by this draft.

## 7. Candidate files and required adoption

No file edit is authorized by this list. Exact implementation/test manifests must be reviewed and approved separately.

- BE2-01: `application/services/ai_jobs.py` stale classification/intent branch and public UoW/receipt/operation recovery contract; `domain/ai_jobs/completion.py` and `application/ports/ai_jobs.py` are governing claim/receipt/intent contracts. Preserve foundation JobState.
- BE2-08: `domain/knowledge_video/model.py`; `infrastructure/knowledge_video/codec.py` and `sql.py`; `application/knowledge_video_worker.py` and `knowledge_video_create.py`; affected ports and versioned `contracts/schemas/knowledge_video.py` projection; owned tests. State/receipt/journal storage changes need explicit schema scope.
- FEAT-057: future composition adapter and cross-lane evidence, under its own approval. No adapter is asserted implemented.
- BE1 artifacts/storage owner: descriptor ownership, SUCCEEDED+STALE ref eligibility for `STALE_CONTEXT`, accepted-reference arbitration, durable effect acknowledgement and actual cleanup semantics; the companion adoption packet is a request, not a signed response.

Source fence owner/key/invalidator adoption remains separate. Every paired lifecycle mutation follows job/run locks before the complete canonical source-fence union. Missing same-store source fencing leaves X01 PARTIAL, including B-stale.

## 8. Planned evidence and gates

| ID | Planned verification requirement; no test is run or claimed |
|---|---|
| ST01 | Every decision row maps to its boundary; failure-claim ACCEPTED and guard-STale cannot enter accepted finalization. |
| ST02 | One B-stale UoW commits job result refs/disposition, receipt, stale run and intent together; participant CAS error rolls back all rows/effects. |
| ST03 | Foreign/missing/unmappable descriptors fail closed; only exact producing job/attempt refs enter the intent. |
| ST04 | Lost ACK recovers the same authoritative stale receipt and stored effect identity without regenerating media. |
| ST05 | Fixed STALE_CONTEXT and original fingerprint produce the expected canonical event id; replay never changes reason/id. |
| ST06 | Accepted-first and cleanup-first interleavings both protect every valid accepted reference; old guards cannot bypass protection. |
| ST07 | Corrupt/unavailable private journal or receipt leaves pending; completion_key is independently reconstructed rather than echoed. |
| ST08 | Video model/codec/terminal persistence/versioned projection agree; stale has no artifact/ready state, S binds and retry clears attempt_id. |
| ST09 | Temporary/normalization guard incidents remain durably audited without occupying the authoritative completion slot. |

Before implementation: independent document review; BE1 artifacts adoption; exact paired API, state/projection, operation-journal and storage contracts; reviewed file/test/schema manifests; separate supplemental approval for affected boundaries and cards. The owner D3 design decision does not satisfy these gates automatically.

X01 remains PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED. Budget unit/limit remain unprovided. This draft authorizes no source/test/schema edit, test run, database, provider, server, Modal, Lightning, acceptance or Git publication.
