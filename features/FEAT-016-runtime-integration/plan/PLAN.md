# Runtime Integration Sprint plan

- Status: REVIEW
- Plan revision: 1
- Implementation status: IN_PROGRESS
- Feature: FEAT-016-runtime-integration
- Owner: allocation pending under ADR-0006
- Precondition: FEAT-015 revision-2 offline integration is complete; no implementation is authorized by this document alone.

## Problem and goal

The four Sprint 1 workstreams now have independently tested contracts and an offline fixture flow. The product still lacks an application-owned runtime that carries one supervised session from capture through P2 understanding, Gate A, P1 deterministic filtering, Gate B, P3 playback, P4 learning media, activity handoff and feedback.

This feature will implement that runtime boundary with fixture-only providers first. Application commands and versioned contracts remain authoritative. FastAPI, queues, storage and Android are adapters around the application layer; no provider SDK is called from a router or mobile screen.

## Scope

### Work package A — Application/session state

Define a session aggregate and application commands for:

- create supervised session;
- submit immutable drawing/narration artifacts;
- record media validation;
- accept P2 raw proposal;
- confirm/correct Gate A;
- request additional context;
- produce P1 eligible candidates;
- approve Gate B activity/objective pair;
- attach P3/P4 artifacts or typed fallback;
- complete Activity Bridge handoff;
- record adult feedback.

Every mutation carries `expected_session_version`, rejects stale updates, and is idempotent for a caller command ID. Domain state cannot import FastAPI, database, queue, provider or UI modules.

### Work package B — Versioned HTTP/job contracts

Define command/result envelopes with contract name/version, session ID/version, artifact IDs/versions, source artifact IDs, timestamps and provenance. Expose only application commands through ports. The first adapter may be an in-memory transport and a local HTTP contract test; production auth/storage/queue wiring is a later gated slice.

Async progress uses a versioned job resource. The client contract supports roughly two-second initial polling, backoff up to ten seconds, ETag/job version where available, terminal stop, retry-after and background pause. Transport can change later without changing state semantics.

### Work package C — P2 and P1 runtime adapters

Consume P2 typed ASR/vision/fusion results, preserve conflicts and stop before Gate A. Gate A confirmation creates a new meaning version. P1 receives only confirmed meaning and explicit adult context, applies hard deterministic rules before any selector, and returns canonical activity/objective references. Unknown labels never become activity IDs by string conversion.

### Work package D — P3 asset bridge and P4 media boundary

P3 receives an approved activity/objective and immutable source-art reference, validates the asset manifest/hash and emits a renderer plan plus version-bound playback events. P4 receives the same approved identity, checks cache before generation, rejects identity mismatch, and returns generated, fallback or block typed results. Media failure cannot remove an approved off-screen activity handoff.

### Work package E — fixture-only client/E2E harness

Exercise the Android-facing bridge and application flow with synthetic fixtures. Cover renderer lifecycle, duplicate/out-of-order events, background/resume, stale job completion, Gate double-submit and feedback. No production UI polish or product visual asset application is included.

## Explicit exclusions

- Lightning, Runpod, Whisper, Qwen3-VL or Wan2.2 live execution.
- Public or production API deployment.
- PostgreSQL, S3, Redis/RQ and cloud infrastructure wiring unless a later plan explicitly adds them.
- Android release/signing/Play distribution.
- Real child data, accounts, credentials or provider secrets.
- Product visual assets or copying synthetic fixtures into `assets/applied/`.
- Changing P1 production eligibility or bypassing qualified Montessori review.

## Proposed allocation for approval

This is a proposal, not an approved assignment:

| Work package | Lead proposal | Required reviewer |
|---|---|---|
| A application/session state and invariants | P1 + P2 pair | all workstreams |
| B contracts, job semantics and adapter ports | P2 | P1 + P4 |
| C P2/P1 runtime boundary and Gate commands | P2 + P1 | project owner |
| D P3 bridge and P4 media composer | P3 + P4 pair | P1 + P2 |
| E fixture-only client/E2E harness | shared rotation | each workstream owner |

Final assignment, estimates and sequencing require explicit owner review. No person inherits the entire backend/infra/E2E or Android application by default.

## Implementation sequence

1. Contract review and allocation approval; pin FEAT-015 fixture/contract versions.
2. Add domain/application state transitions and typed commands with in-memory repository.
3. Add contract round-trip and stale/idempotency tests.
4. Add P2 fusion/Gate A and P1 filtering/Gate B application handlers.
5. Add P3 asset bridge and P4 cache/fallback handlers.
6. Add local HTTP/job adapter with polling semantics and failure injection.
7. Add fixture-only client bridge and E2E transition harness.
8. Run the full standalone regression plus runtime matrix.
9. Review evidence, architecture/security output, and update status before any later infrastructure plan.

## Acceptance criteria

- [ ] One fixture session traverses capture -> validation -> P2 proposal -> Gate A -> P1 filtering -> Gate B -> P3/P4 -> handoff -> feedback.
- [ ] P1 canonical activity/objective IDs and versions remain unchanged across every command/result.
- [ ] Gate A is mandatory; conflict and unconfirmed meaning cannot reach P1 or media.
- [ ] Missing context returns a typed request and allows controlled re-evaluation without losing source artifacts.
- [ ] Hard P1 rules run before selectors or media generation.
- [ ] Gate B approves both activity and objective version and rejects mismatch/staleness.
- [ ] P3 validates whole-drawing asset provenance/hash and ignores stale/duplicate playback events.
- [ ] P4 cache HIT avoids generation; provider error/timeout, unsafe media and identity mismatch produce typed fallback/block.
- [ ] Stale, duplicate and out-of-order job completion cannot mutate newer session state.
- [ ] Activity Handoff remains reachable when learning media falls back or blocks according to policy.
- [ ] Mobile-facing code calls only the application/API boundary and contains no provider/storage credentials or endpoints.
- [ ] Fixture-only E2E covers normal, conflict, context-needed, stale, fallback, block and feedback cases.
- [ ] Evidence records command, environment, commit references, fixture hashes, output and limitations.
- [ ] Harness, architecture, security and team-allocation validators pass before commit/push.

## Test strategy

### Contract and domain

- producer/consumer round-trip for every envelope;
- unknown field, unsupported version, missing provenance and ID/version mismatch rejection;
- P1 74 Golden cases remain an oracle;
- Gate A/B double-submit, correction versioning and actor checks;
- immutable source hash and derived-artifact provenance checks.

### Application/job

- stale expected session version;
- duplicate command ID/idempotent replay;
- worker completion after newer state;
- retry-after/backoff/terminal polling;
- job timeout, cancellation and bounded retry;
- authorization mismatch and artifact access denial.

### P3/P4

- asset hash change, missing source, stale renderer event and duplicate completion;
- cache hit spy proves no generator call;
- cache miss, provider exception, timeout, invalid media, unsafe media and still+narration fallback;
- activity/objective identity preserved through every result.

### Fixture E2E

Run the FEAT-015 fixture scenarios plus:

1. normal happy path;
2. modality conflict and Gate A correction;
3. additional context then re-evaluation;
4. stale Gate B and stale worker completion;
5. P3 asset rejection/fallback;
6. P4 cache hit, cache miss, timeout/fallback and block;
7. feedback after handoff;
8. background/resume and duplicate playback events.

## Evidence plan

Store under `features/FEAT-016-runtime-integration/evidence/`:

- contract review note and allocation decision;
- unit/contract/integration/E2E command logs;
- transition traces with fixture and commit hashes;
- stale/idempotency/fallback failure evidence;
- bridge screenshots/recordings only after visual/device approval;
- security and architecture validation output;
- limitations and unmeasured metrics.

## Approval gate

Implementation begins only after `approvals/TASK_APPROVAL.md` changes to `APPROVED` with the owner, timestamp, exact plan revision, allocation, acceptance criteria and exclusions recorded. Any later addition of live provider, production API, Android release or real data requires a new revision/approval.

## Implementation evidence

Completed in this bounded slice:

- framework-free session aggregate and typed transitions;
- P2/P1 Gate A/B enforcement;
- P1 activity/objective identity locking;
- local versioned transport envelope;
- local job stale-completion and idempotency semantics;
- fixture-only runtime tests.

The approved fixture-only client/lifecycle harness is implemented in the mobile app with reducer and renderer-event evidence. Device screenshots/APK execution remain environment-limited; production API, cloud infrastructure and live providers require a later approval.

## Deep review result

- Full regression across FEAT-015 and FEAT-016: 32 passed.
- Replay idempotency was hardened so historical command results cannot roll back current state.
- Contract input validation now rejects malformed artifact hashes and invalid Gate confirmations/approvals.
- Device lifecycle screenshots/APK execution remain environment-limited; production API/cloud/provider work is excluded.


