# FEAT-018 Person 4 — Cache, fallback, device flow, and evidence

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
