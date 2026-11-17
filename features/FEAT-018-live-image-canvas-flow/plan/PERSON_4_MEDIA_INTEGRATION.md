# FEAT-018 Person 4 — Cache, fallback, device flow, and evidence

Plan status: DRAFT ADDENDUM / AWAITING FEAT-018 APPROVAL / NOT AN IMPLEMENTATION AUTHORIZATION

## Mission

Make the real-image flow reliable after understanding: resolve reviewed media/cache first, preserve activity identity, fall back safely, and provide a repeatable device pilot/evidence matrix without silently owning backend or the entire Android application.

## Ownership boundary

Person 4 owns P4 cache/media contracts, fallback behavior, device matrix, redacted evidence, and replay fixtures. Backend/session orchestration and complete E2E wiring are shared integration work and require explicit allocation; they are not assigned to Person 4 by default.

## Task cards

### P4-T1 — Cache and media contracts

Version and validate:

- `LearningMediaRequestV1`;
- reviewed cache asset record;
- cache hit/miss result;
- media validation result;
- still+narration fallback result;
- provenance and source/activity/objective version references.

### P4-T2 — Cache-first resolver

- Resolve by exact activity/objective/version and renderer plan.
- A cache hit must be reviewed, source-linked, and compatible with the current scene contract.
- A cache miss must be typed and must not change activity identity.
- Reject stale, corrupt, unsafe, or hash-mismatched media.

### P4-T3 — Safe fallback

Cover provider timeout, unavailable media, invalid clip, renderer error, and cache miss. Fallback order:

1. approved cached media;
2. approved still + narration/onscreen guidance;
3. whole-image Pixi reveal;
4. supervised activity handoff with the same Gate B identity.

### P4-T4 — 20-activity device pilot

For every golden activity:

- run cache hit;
- run cache miss;
- run renderer/media fallback;
- verify Gate A/B identity/version remains unchanged;
- complete handoff and feedback state.

No test may use real child/personal data or a production endpoint.

### P4-T5 — Evidence and replay harness

- Produce a single command to replay each pilot row from sanitized fixture metadata.
- Record status, activity/objective IDs and versions, cache result, renderer event summary, latency, fallback reason, and screenshot path.
- Never record raw image bytes, prompts, provider output, tokens, signed URLs, or personal metadata.
- Run security/harness validation before review.

## Detailed 20-card breakdown

The five work packages above are expanded below into 20 traceable cards. These IDs are deliberately
feature-qualified to avoid collision with any prior Person 4 task numbering. All cards remain
blocked until the FEAT-018 contract-freeze gate and the required reconciliations in
`evidence/notes/PRE_APPROVAL_COMPLETENESS_REVIEW_20260908.md` are resolved and the owner records
an explicit approval.

Person 4 may build independently testable cache/media fixtures and a standalone resolver. Backend
orchestration, session/job state, mobile wiring, deployment, and full E2E ownership remain shared
integration work under ADR-0006.

### Phase A — contract and fixture freeze

| ID | Task | Done only when |
|---|---|---|
| FEAT018-P4-01 | Reconcile the selected contract registry | The owner-approved registry names the exact `LearningMediaRequest`/`LearningMediaResult` contract, version, producer, consumer, and source-of-truth schema. |
| FEAT018-P4-02 | Define cache-result and fallback reason vocabulary | Hit, miss, stale, corrupt, unsafe, renderer-failure, and unavailable-media cases have closed typed tokens and negative fixtures. |
| FEAT018-P4-03 | Define the exact cache key | The key binds activity/objective/renderer IDs and versions, source/session version where required, and never includes raw image or provider data. |
| FEAT018-P4-04 | Define reviewed-asset provenance | A synthetic fixture record requires source/asset hashes, review status, contract version, and provenance without credentials, signed URLs, or personal data. |

### Phase B — standalone cache resolver

| ID | Task | Done only when |
|---|---|---|
| FEAT018-P4-05 | Author the synthetic cache fixture package | Fixture inputs cover one reviewed hit, one typed miss, and one rejected asset; every payload/hash is deterministic and feature-local. |
| FEAT018-P4-06 | Implement the resolver port and fake store | The component can resolve fixtures without another person's runtime, database, storage bucket, or live provider. |
| FEAT018-P4-07 | Implement exact reviewed-cache hit behavior | A hit returns only an asset/plan compatible with the exact cache key and preserves activity/objective/renderer identity. |
| FEAT018-P4-08 | Implement typed cache miss behavior | A miss returns a typed result and cannot silently substitute another activity, objective, version, or asset. |
| FEAT018-P4-09 | Implement integrity and review rejection | Hash mismatch, stale version, unreviewed asset, corrupt metadata, and unsafe media fail closed before a result is handed to a renderer. |

### Phase C — safe fallback component

| ID | Task | Done only when |
|---|---|---|
| FEAT018-P4-10 | Freeze fallback precedence | The approved order is encoded as data/tests: reviewed cache, approved still plus guidance, whole-image reveal, then supervised handoff with unchanged identity. |
| FEAT018-P4-11 | Implement approved still-plus-guidance fallback | A typed fallback can reference only reviewed synthetic fixture assets and records why the primary asset was unavailable. |
| FEAT018-P4-12 | Implement whole-image reveal fallback request | The resolver emits a renderer-facing fallback request without owning Pixi playback or changing source/plan identity. |
| FEAT018-P4-13 | Preserve identity through every fallback | Contract tests prove the activity, objective, versions, Gate-B identity, and source linkage are identical before and after each fallback. |
| FEAT018-P4-14 | Prove no hidden generation/provider call | Unit tests prove cache miss, fallback, and corrupt-media paths neither call AI/generation nor require credentials/endpoints. |

### Phase D — replay, evidence, and review

| ID | Task | Done only when |
|---|---|---|
| FEAT018-P4-15 | Build a standalone deterministic replay runner | One local command replays each sanitized fixture scenario; it is not backend/session orchestration and requires no live service. |
| FEAT018-P4-16 | Build the component scenario matrix | The matrix covers hit, miss, stale, corrupt, unsafe, provider/media unavailable, renderer failure, and each permitted fallback outcome. |
| FEAT018-P4-17 | Build redacted evidence output | Reports contain only IDs/versions, typed statuses, safe hashes, latency when measured, fallback reasons, and approved screenshot references; scans prove prohibited content absent. |
| FEAT018-P4-18 | Prepare the named smoke-subset pack | The owner-approved 3-5 activity smoke subset receives component-level cache/fallback fixtures; this is distinct from and does not claim the 20-row device pilot. |
| FEAT018-P4-19 | Prepare 20-row expansion evidence templates | Each golden row has a checklist for cache hit, miss, fallback, identity preservation, handoff input, and feedback input; unrun measurements remain `NOT_MEASURED`. |
| FEAT018-P4-20 | Publish a bounded integration handoff review | Person 4 publishes schemas, fixtures, replay results, evidence index, known blockers, and an explicit statement that shared integration owns backend/mobile wiring and full E2E. |

## Dependencies and stop gates

1. `FEAT018-P4-01` through `-04` require the owner to resolve the canonical P2 contract, task-ID
   namespace, catalog provenance, ACT-0004 migration plan, and staged pilot definition.
2. `FEAT018-P4-05` through `-14` may begin only after the selected P4 contract and synthetic
   fixture boundary are approved; no live provider, real image, database, cloud storage, or mobile
   credential is needed or allowed.
3. `FEAT018-P4-15` through `-20` require the standalone resolver/tests first. Component evidence
   may be handed to a separately allocated integration owner, but Person 4 does not own the full
   device/E2E run.
4. Stop immediately on contract/version drift, stale identity, missing review provenance, hash
   mismatch, unredacted evidence, or any fallback that bypasses Gate A/Gate B.

## Card-level evidence minimum

- Every implemented card links a feature-local test or deterministic fixture result.
- Every aggregate report separates `MEASURED`, `NOT_MEASURED`, and typed failure outcomes.
- Any screenshot is a reviewed, non-sensitive artifact under `evidence/screenshots/`; raw images,
  raw model output, prompts, secrets, endpoints, and signed URLs are never stored.
- No card authorizes a commit, provider/GPU execution, Lightning call, or production promotion by
  itself.

## Required evidence

- Contract tests for hit, miss, stale, corrupt, unsafe, timeout, and fallback.
- 20-row device pilot report with all required states.
- Gate identity preservation report.
- Screenshot set for capture, Gate A, Gate B, canvas, fallback, handoff, and feedback.
- Replay command output and redaction scan.
- `REPOSITORY_SECURITY_VALID` and harness validation output.

## Acceptance criteria

- Every pilot row reaches feedback through either cached media or the safe fallback chain.
- Cache never changes activity/objective identity or bypasses Gate A/B.
- All typed failures are visible and recoverable.
- Device evidence is reproducible without live production services.
- Evidence contains only sanitized metadata.

## Handoff contract

P4 publishes media/cache/fallback result contracts and the device evidence matrix. The shared integration owner wires these contracts into the session/API state machine after explicit approval.

## Definition of done

Cache/fallback contracts, 20-row replay/device evidence, redaction/security checks, and integration compatibility note are complete.

## Contract alignment checklist (mandatory)

Before implementation, read [CONTRACT_FREEZE.md](CONTRACT_FREEZE.md). P4 owns media/cache result semantics but may not redefine activity/objective identity or Gate state.

### Exact inputs

- `LearningMediaRequestV1` containing exact activity/objective/renderer IDs and versions, source session version, and cache key.
- Approved `ArtAnimationPlanV1` and `PixiArtAssetManifestV1` references.
- Typed provider/cache failure codes.

### Exact outputs

- `LearningMediaResultV1` with status, exact identity/version pair, asset/plan refs, `generation_called`, provenance, and typed failure/fallback reason.
- `ActivityHandoffV1` only after Gate B and media resolution.
- `FeedbackV1` with the same activity/objective identity.

### Contract tests owned by P4

- cache hit/miss and exact-key mismatch;
- stale/corrupt/unsafe media;
- timeout/provider error and fallback chain;
- identity preservation across fallback;
- all 20 golden rows and replay metadata redaction;
- contract registry and evidence-path validation.

P4 must publish cache/fallback fixtures before the shared integration owner wires the session state machine.

## Execution order and stop gates

1. Freeze `LearningMediaRequestV1`/`LearningMediaResultV1` and identity propagation fixtures.
2. Implement cache-key and reviewed-asset checks.
3. Implement typed miss/error/fallback chain without changing identity.
4. Build replay harness for all 20 golden rows.
5. Join the shared device pilot after P1/P2/P3 contracts pass.
6. Stop on stale identity, unsafe/corrupt media, unredacted evidence, or fallback that bypasses a gate.

Evidence naming: `P4_<cache-or-fallback>_<YYYYMMDD>.json` plus a redacted device-run summary; store screenshots only under the feature evidence directory.

## Revision-2 engine additions — pending approval

P4 additionally owns `FEAT018-P4-E1` through `FEAT018-P4-E4` in `ENGINE_REFINEMENT_PLAN.md`: consume the approved `ExperienceSpecV1`, include objective/template/spec identity in cache and result provenance, validate video continuity, and preserve the same concept through still+narration fallback. P4 does not own the Activity Template Library or objective selection.