# FR-C-08 Parent StoryRun lifecycle contract — Draft 9

**Status: DRAFT / NOT APPROVED / NOT LAUNCHED.**
**Date:** 2026-11-19.
**Purpose:** the API and behaviour contract for the first, Parent-only FR-C-08 implementation,
consolidating D-214 to D-218, the approved lifecycle DTR and the approved Core port design. It
is the contract the implementation allowlist (Draft 11) maps to paths. It approves nothing and
grants no implementation, command, database, test, launch, push or merge authority.

**Change from Draft 8:** Draft 8 listed open blockers; D-215 to D-218 settle them. This draft
adopts the cancel and delete routes, the response and replay rules, the error transport, the
lifecycle protocol (by reference to the DTR) and the Core contract (by reference to the port
design), and carries the five wave-1 round-5 notes: R5-F1 (§3.6), R5-F2 (§6), R5-F3 (§3.1, now
superseded by D-216 item 4), R5-F4 (§1), R5-F5 (Allowlist Draft 11).

## 1. Authority

| Input | Pin |
|---|---|
| Canonical working SRS (D-209) | `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` (owner-supplied, unsigned) |
| Owner decisions | FEAT-063 `DECISIONS.md` D-208, D-209, D-214 to D-218; working tree 260,722 bytes, SHA-256 `6F6DC3291E9AF96FD26400AFD8F4837F02FB7B9856086F79F19485CD6E6E9AE0` (D-214 to D-218 uncommitted) |
| Lifecycle DTR (D-218 A-1) | `plan/FR_C08_LIFECYCLE_DTR_DRAFT6_20261119.md`, 40,580 bytes, `E4B255427A59B7D97E15D1530367AD5E406A12549A3785981A2C641C15BAB30C` |
| Core port design (D-218 A-1) | `plan/FR_C08_CORE_REFERENCE_CLOSURE_PORT_DESIGN_DRAFT6_20261119.md`, 21,768 bytes, `C8EDD923785AF25283C55B2C94405C1AE5979949CF8DDE0085344CC6BE6FA86A` |
| SRS wording edit (applied last) | `plan/FR_C08_SRS_WORDING_EDIT_DRAFT2_20261119.md` (review round 2 READY WITH NOTES) |
| Code base (D-216 item 2) | local branch `feature/feat066-conv1`, commit `03342207ab10379e6c53449274edaf4d9bcf60e4` (docs-only above `2dddc607`, the CONV-1 code commit) |

D-214 records the owner's answers to the twelve questions first asked in Owner Questions Rev3;
later revisions restate them (R5-F4). D-218 records the V1 simplification of the Core port and
amends D-217 items 2, 3 and 5. The M2 closure satisfies D-208 item 8 (D-214 item 11); M2
approvals, allowlists and command ceilings do not transfer.

## 2. Scope

- **Parent only** (D-214 item 4; D-215 item 7). The lifecycle design is shared; the Teacher
  authorization adapter and every Teacher route change are a later P2 slice (SRS lines 667-668).
- **In scope:** the cancel and delete commands, the lifecycle projection on the existing GET, the
  purge protocol, the schema delta and migration of the DTR, the Core port of the port design,
  the access fence, metadata-only audit.
- **Out of scope:** Teacher; video, playback and audio (no Parent run stores them at the base,
  port design C7); retention periods, an audit reader and backup/DSR (gated before real data);
  the client applications (§7); the StoryRun-lite demo routes.

## 3. Contract

### 3.1 Cancel — `POST /v1/story-runs/{run_id}/cancel` (existing route; SRS lines 1515-1523, 1673)

| Item | Rule |
|---|---|
| Actor | the Parent who owns the run (owner-scoped lookup; another Parent's run is 404) |
| Eligible states | the 13 SRS cancel-eligible states (SRS lines 394, 1518) plus the documented extensions `SCRIPT_GENERATING` and `SCRIPT_GENERATION_UNKNOWN` (D-216 item 4); in practice the states `story.runs` can hold (DTR §5.4) |
| Request | body `{"expected_revision": int ≥ 1}`; header `Idempotency-Key`, exactly one value of 1-128 visible ASCII characters (D-066-68 C-D5; D-217 item 7) |
| Success | **202** with the lifecycle envelope (§3.4); the run is `DELETE_PENDING` and the active lock is released in the same transaction (SRS line 1520) |
| Errors | 409 `STALE_REVISION` with `current_version` (C-D7); 409 `INVALID_STATE_TRANSITION` (ineligible state, including `DELETE_PENDING` and `DELETED`); 400 `INVALID_IDEMPOTENCY_KEY` (same key, changed payload; SRS line 1697, D-200); 400 `INVALID_REQUEST` (shape, missing key); 404 `RESOURCE_NOT_FOUND` |
| Replay | same key and payload → the stored body (DTR §6.5) |

R5-F3: the two extension values are no longer mapped away; D-216 item 4 keeps them as documented
extensions in the response and stored values (an explicit deviation from SRS line 394).

### 3.2 Delete — `DELETE /v1/story-runs/{run_id}` (new route; SRS lines 1465-1475, 1674)

| Item | Rule |
|---|---|
| Actor | the Parent who owns the run |
| Eligible states | `COMPLETED`, `FAILED`, `ABANDONED` (D-214 item 1; `ABANDONED` only once a producer stores it, DTR §5.4); `FAILED` and `ABANDONED` are never purged automatically |
| Request | no body; header `Idempotency-Key` as §3.1; no expected revision (SRS line 1674; D-217 item 6) |
| Success | **202** with the lifecycle envelope (§3.4) |
| Errors | 409 `INVALID_STATE_TRANSITION`; 400 `INVALID_IDEMPOTENCY_KEY`; 400 `INVALID_REQUEST`; 404 `RESOURCE_NOT_FOUND` |
| Replay | as §3.1 |

Cancel and delete of one run share one lifecycle request (deterministic `request_id`, DTR rule 6);
a second command on a run already in `DELETE_PENDING` or `DELETED` is refused with 409.

### 3.3 Read — `GET /v1/story-runs/{run_id}` (existing route; SRS lines 805, 1811)

- While the run is in any other state the response is the current one, unchanged except that the
  `run_state` enum is the 18 SRS states plus the two extensions (D-215 item 4, D-216 item 4).
- From `DELETE_PENDING` on, the response is the lifecycle envelope (§3.4): no context snapshot,
  story, candidate, subject label, profile ref or asset ref (access is revoked at acceptance; SRS
  lines 1053, 1520). `DELETED` is reported only after Story has written it (D-215 item 5); access
  denial or a missing read is never reported as `DELETED`.

### 3.4 Lifecycle envelope and projection (D-217 items 5 and 8, D-218 A-3)

```text
ParentStoryRunLifecycleEnvelopeV1:
  request_id: UUID              # per-request correlation id, as today
  lifecycle: ParentStoryRunLifecycleProjectionV1

ParentStoryRunLifecycleProjectionV1:
  run_id: UUID
  run_state: "DELETE_PENDING" | "DELETED"
  revision: int
  version: int
  lifecycle_request_ref: UUID   # deterministic, DTR rule 6
  purge_state: "PENDING" | "COMPLETED"   # COMPLETED exactly when run_state == DELETED
```

The cancel 202, the delete 202 and GET for a purged run return this envelope. The frozen
`ParentStoryRunCancelEnvelopeV1` (which embedded the full run) is replaced (D-218 A-3). GET for a
live run keeps `ParentStoryRunEnvelopeV1`; the GET response is declared as the union of the two
envelopes. No percentage, counts, content or storage key appear (SRS line 1809).

### 3.5 Lifecycle, purge and fence

The command transaction, the BE1 lifecycle consumer, the four purge steps, the token rule, leases
and retry, the pre-existing `DELETE_PENDING` reconciliation, replays, the `exception` re-open, the
access fence and the audit rows are exactly those of DTR Draft 6 §6-§8; the Core asset step is
port design Draft 6 (all or nothing: any retained asset → `exception`, nothing deleted). Events:
`StoryRunCancellationRequestedV1` on cancel, `StoryRunDeletedV1` on delete, no completion event
(D-218 A-2). Provider interruption is best-effort and never purge evidence (D-214 item 6).
Consumed quota is never refunded and a Teacher sample claim is never touched (SRS lines 1053,
1521-1522); no Parent quota row exists at the base.

### 3.6 Error transport (D-066-68, implemented by CONV-1 at the base)

Error body fields: `code`, `message`, `correlation_id`, `request_id` (equal to `correlation_id`;
C-D1, `error_envelope.py:230`), `retryable`, `retry_after_seconds`, `field_errors`;
`current_version` only with `STALE_REVISION`. The `X-Request-ID` header equals `correlation_id`
(C-D2). Shape errors are 400 `INVALID_REQUEST` (C-D3); out-of-scope or missing resources are the
same-shape 404 `RESOURCE_NOT_FOUND`, and 403 `ACTION_NOT_ALLOWED` only after scope is
established (C-D4). D-066-68 is recorded in the root checkout (FEAT-066 `DECISIONS.md` line 382)
and at the base; D-066-71 and the CONV-1 approval and evidence are on the local branch only
(R5-F1). The other four Parent POST routes keep their 1-256 key range and are outside FR-C-08
(D-217 item 7).

## 4. Key source facts at the base (`03342207`, read-only)

| Fact | Evidence |
|---|---|
| The Parent cancel route exists (202, body `expected_revision`, key 1-256) and its response embeds the full run | `interfaces/http/routers/parent_story_runs.py:253-294`; `contracts/schemas/parent_story_runs.py:148-151` |
| No `DELETE /v1/story-runs/{run_id}` route exists | `parent_story_runs.py` route list (`@router.post` at 126, 253, 297, 322, 353; `@router.get` at 210, 232) |
| The M2 cancel accepts seven source states and writes no lifecycle request, notice, event or audit | `infrastructure/persistence/parent_story_repository.py:328-438` |
| `ParentStoryRunResponseV1.run_state` has ten values (no `ABANDONED`, `DELETED`) | `contracts/schemas/parent_story_runs.py:113-117` |
| The lifecycle request, notice, audit, outbox and aggregate tables require `organization_id` | DTR Draft 6 §3 (S1, S3, S5, S7) |
| The CONV-1 key parser accepts 1-128 visible ASCII | `interfaces/http/api_conventions.py:59-69` |

DTR Draft 6 §3 and port design Draft 6 §3 hold the full source-fact tables.

## 5. Recorded deviations

| Deviation | Decision |
|---|---|
| User DELETE allowed for `FAILED` and `ABANDONED` (SRS says completed runs) | D-214 item 1; SRS edit applied last |
| Two extension run states beyond the 18 of SRS line 394 | D-216 item 4 |
| Receipt row and notice written by the consumer, not at acceptance (SRS lines 1520, 1797) | DTR §6.1 (follows SRS line 404) |
| Cancel envelope replaced; pre-existing `CANCEL_RUN` bodies rewritten; fingerprints replaced; other receipts replayed without a fingerprint check | D-218 A-3 |
| `profile_ref` nullable, cleared on the tombstone | D-218 A-4 |
| No per-object deletion-state column (SRS line 1949) | D-218 A-5 |
| Retained asset → `exception`, nothing deleted, no release path | D-218 A-1 |

## 6. Open, not blocking implementation

- The existing GET still lacks the SRS `StoryRunDetailV1` timeline; M2 recorded this as
  OPEN-OWNER and non-blocking (`approvals/TASK_APPROVAL.md` line 3250); it is not lifecycle
  evidence (R5-F2).
- A least-privilege storage principal for the lifecycle worker (port design §4 item 3), retention
  periods, backup/DSR and deletion-evidence policy: gated before real data (SRS lines 656, 1057).
- The owner-review re-open command for an `exception` request (DTR §6.6) is separate work.
- The SRS wording edit is applied after implementation approval, by the owner or a separately
  started session (D-216 item 6).

## 7. Client impact (outside this contract's paths)

The cancel 202 body, the new delete route and the GET union change the Parent API that the
mobile Parent client (FEAT-081) and the frozen client-facing OpenAPI projection use. The client
change is FE work in its own lane and approval; this contract does not edit client code or the
client projection. The backend OpenAPI contract files are updated only for the FR-C-08
operations (Allowlist Draft 11).

## 8. Acceptance conditions for the implementation task

1. Cancel accepts exactly the eligible states, enforces revision and the 1-128 key, returns the
   §3.4 envelope, releases the lock in the same transaction, and writes the event, audit and
   receipt as DTR §6.1.
2. Delete accepts only `COMPLETED`, `FAILED` (and `ABANDONED` once storable), returns the same
   envelope, and converges with cancel on one lifecycle request.
3. GET returns the live envelope before `DELETE_PENDING` and the lifecycle envelope after it, with
   `DELETED` only after Story writes it; every replay follows DTR §6.5.
4. The purge protocol, token rule, retry and reconciliation pass every DTR §10 check, including
   the crash points; the Core step passes every port design §12 check.
5. `DELETED` is terminal for every Parent Story writer; no late result changes a purged run.
6. No fabricated organization in any row; audit rows are metadata only.
7. The schema delta migrates up and down on a disposable database as DTR §9; existing
   organization writers behave as before.
8. Static composition and OpenAPI evidence are reported separately from runtime evidence.

## 9. Lineage

Contract Draft 9 succeeds Draft 8; the matching allowlist is Draft 11. Both are DRAFT / NOT
APPROVED / NOT LAUNCHED.
