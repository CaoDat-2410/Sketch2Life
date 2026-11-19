# FR-C-08 Parent StoryRun lifecycle contract — Draft 12

**Status: SRS-ALIGNMENT REVISION of Draft 11 (program task B4, D-219).** No behaviour change.
**Approval:** made at the owner's instruction in the same step as the SRS edit (D-208 item 6)
and independently reviewed with it; recorded by D-219 together with the verified application.
The owner has not reviewed this file's text separately. Its statements that the SRS edit is
applied hold only from that verified application; Draft 11 remains the approved
implementation contract.
**Date:** 2026-11-19.
**Purpose:** the API and behaviour contract for the first, Parent-only FR-C-08 implementation,
consolidating D-214 to D-218, the approved lifecycle DTR and the approved Core port design. It
is the contract the implementation allowlist (Draft 13) maps to paths. It approves nothing and
grants no implementation, command, database, test, launch, push or merge authority.

**Change from Draft 11 (SRS alignment only):** the canonical SRS was revised by the FR-C-08
wording edit (`plan/FR_C08_SRS_WORDING_EDIT_DRAFT3_20261119.md`, D-219; D-208 item 6 requires
the corresponding contract to be updated in the same step). This draft changes only the SRS
references: the SRS pin and the wording-edit row (§1); the two extension states, which the SRS
now records at line 394 (§3.1); the aligned SRS lines of delete eligibility (§3.2); the two
deviation rows closed by the SRS revision (§5); the wording-edit bullet (§6); lineage (§9). No
route, state set, schema, error, path or acceptance condition changes. Draft 11 (17,168 bytes,
`A209D0976B84573CCA31A85475F3EFEACBC136F3B48BA91DB737254719DD6737`) stays the contract against
which the accepted implementation `ceb3ea27` was approved and accepted.

**Change from Draft 10 (final; not reviewed again):** applies the six P3 notes of the round-2
cold review (`tmp/frc08-cp9/review-r2/FR_C08_CONTRACT10_ALLOWLIST12_COLD_REVIEW_R2_20261119.md`,
READY WITH NOTES, 0 P1 / 0 P2 / 6 P3): N-1 `field_errors` rule (§3.6); N-2 header declaration and
OpenAPI status of cancel and delete (§3.1, §3.7); N-3 the two `/api/parent/v1/ai` routes on a
purged run (§3.3); N-4, N-5 are allowlist notes; N-6 the 404 position in the error order, the
allowlist reference and line lengths.

**Change from Draft 9:** fixes the round-1 cold review
(`tmp/frc08-cp9/review-r1/FR_C08_CONTRACT9_ALLOWLIST11_COLD_REVIEW_R1_20261119.md`, NEEDS REVISION,
0 P1 / 3 P2 / 5 P3): F-2 §3.6 now states the real transport of `/v1/story-runs/*` (the M2 Parent
error envelope served by `app.py`, not the CONV-1 envelope) and drops the `request_id` claim;
F-4 the error order of cancel and delete is fixed (§3.1, §3.2); F-5 the replay shape of the
create and three confirmation routes is stated (§3.3) and named in §7. F-1, F-3 and F-6 to F-8
are allowlist fixes (Draft 12).

**Change from Draft 8:** Draft 8 listed open blockers; D-215 to D-218 settle them. This draft
adopts the cancel and delete routes, the response and replay rules, the error transport, the
lifecycle protocol (by reference to the DTR) and the Core contract (by reference to the port
design), and carries the five wave-1 round-5 notes: R5-F1 (§3.6), R5-F2 (§6), R5-F3 (§3.1, now
superseded by D-216 item 4), R5-F4 (§1), R5-F5 (Allowlist Draft 11, kept in Draft 12).

## 1. Authority

| Input | Pin |
|---|---|
| Canonical working SRS (D-209, revised by D-219) | `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,810 bytes, SHA-256 `443A3CA37272D2FE96127564BAF400461F394E098724A6BD999D723A4E504021` (owner-supplied, unsigned; before the D-219 wording edit 701,157 bytes, `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5`; no line moved, so every SRS line cited here is unchanged) |
| Owner decisions | FEAT-063 `DECISIONS.md` D-208, D-209, D-214 to D-218; working tree 260,722 bytes, SHA-256 `6F6DC3291E9AF96FD26400AFD8F4837F02FB7B9856086F79F19485CD6E6E9AE0` (D-214 to D-218 uncommitted) |
| Lifecycle DTR (D-218 A-1) | `plan/FR_C08_LIFECYCLE_DTR_DRAFT6_20261119.md`, 40,580 bytes, `E4B255427A59B7D97E15D1530367AD5E406A12549A3785981A2C641C15BAB30C` |
| Core port design (D-218 A-1) | `plan/FR_C08_CORE_REFERENCE_CLOSURE_PORT_DESIGN_DRAFT6_20261119.md`, 21,768 bytes, `C8EDD923785AF25283C55B2C94405C1AE5979949CF8DDE0085344CC6BE6FA86A` |
| SRS wording edit (applied, D-219) | `plan/FR_C08_SRS_WORDING_EDIT_DRAFT3_20261119.md` (applies the round-2 notes to Draft 2; reviewed before application) |
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
| Eligible states | the 13 SRS cancel-eligible states (SRS lines 394, 1518) plus the documented extensions `SCRIPT_GENERATING` and `SCRIPT_GENERATION_UNKNOWN` (D-216 item 4; recorded in the SRS remarks of line 394 since D-219); in practice the states `story.runs` can hold (DTR §5.4) |
| Request | body `{"expected_revision": int ≥ 1}`; header `Idempotency-Key`, exactly one value of 1-128 visible ASCII characters (D-066-68 C-D5; D-217 item 7), declared as an **optional** FastAPI header parameter with no length constraint and read with `parse_idempotency_key`, so a missing or invalid key is 400 `INVALID_REQUEST` |
| Success | **202** with the lifecycle envelope (§3.4); the run is `DELETE_PENDING` and the active lock is released in the same transaction (SRS line 1520) |
| Errors | 409 `STALE_REVISION` with `current_version` (C-D7); 409 `INVALID_STATE_TRANSITION` (ineligible state, including `DELETE_PENDING` and `DELETED`); 400 `INVALID_IDEMPOTENCY_KEY` (same key, changed payload; SRS line 1697, D-200); 400 `INVALID_REQUEST` (shape, missing key); 404 `RESOURCE_NOT_FOUND` |
| Replay | same key and payload → the stored body (DTR §6.5) |

**Error order (F-4, N-6):** the owner-scoped lookup first (404 `RESOURCE_NOT_FOUND`); then replay; then the revision (409 `STALE_REVISION` with
`current_version`); then the state (409 `INVALID_STATE_TRANSITION`). A second cancel with a new key
and the old `expected_revision` therefore gets `STALE_REVISION`; with the current revision it gets
`INVALID_STATE_TRANSITION`.

R5-F3: the two extension values are no longer mapped away; D-216 item 4 keeps them as documented
extensions in the response and stored values. Since the D-219 wording edit the SRS records them
in the remarks of line 394 as a noted exception to its 18-state inventory, kept in the response
and stored values and cancellable under UC-11, so they are no longer a deviation from the SRS
text; D-216 item 4 stays their authority.

### 3.2 Delete — `DELETE /v1/story-runs/{run_id}` (new route; SRS lines 1465-1475, 1674)

| Item | Rule |
|---|---|
| Actor | the Parent who owns the run |
| Eligible states | `COMPLETED`, `FAILED`, `ABANDONED` (D-214 item 1; SRS lines 270, 500, 1465, 1470 and 1674 as aligned by D-219; `ABANDONED` only once a producer stores it, DTR §5.4); `FAILED` and `ABANDONED` are never purged automatically (SRS line 270) |
| Request | no body; header `Idempotency-Key` as §3.1; no expected revision (SRS line 1674; D-217 item 6) |
| Success | **202** with the lifecycle envelope (§3.4) |
| Errors | 409 `INVALID_STATE_TRANSITION`; 400 `INVALID_IDEMPOTENCY_KEY`; 400 `INVALID_REQUEST`; 404 `RESOURCE_NOT_FOUND` |
| Replay | as §3.1 |

**Error order:** the owner-scoped lookup (404), then replay, then the state (409
`INVALID_STATE_TRANSITION`); the delete route
has no revision and never returns `current_version`.

Cancel and delete of one run share one lifecycle request (deterministic `request_id`, DTR rule 6);
a second command on a run already in `DELETE_PENDING` or `DELETED` is refused with 409.

### 3.3 Read — `GET /v1/story-runs/{run_id}` (existing route; SRS lines 805, 1811)

- While the run is in any other state the response is the current one, unchanged except that the
  `run_state` enum is the 18 SRS states plus the two extensions (D-215 item 4, D-216 item 4).
- From `DELETE_PENDING` on, the response is the lifecycle envelope (§3.4): no context snapshot,
  story, candidate, subject label, profile ref or asset ref (access is revoked at acceptance; SRS
  lines 1053, 1520). `DELETED` is reported only after Story has written it (D-215 item 5); access
  denial or a missing read is never reported as `DELETED`.
- **Replays on other routes (F-5):** a replay of a create, context-confirmation,
  subject-confirmation or script-confirmation receipt whose run is in `DELETE_PENDING` or
  `DELETED` returns the lifecycle envelope (§3.4) under the route's normal success status (DTR
  §6.5); each of these four operations declares its response as the union of its current
  envelope and the lifecycle envelope.
- **The two Parent AI routes on a purged run (N-3):** `POST /api/parent/v1/ai/drawing-understandings`
  (reads the current input) refuses a run in `DELETE_PENDING` or `DELETED` with 409
  `INVALID_STATE_TRANSITION`; `POST /api/parent/v1/ai/story-runs/{run_id}/story-revisions`
  returns the lifecycle envelope under its normal status when the request is a replay, and 409
  `INVALID_STATE_TRANSITION` otherwise. Neither ever returns a 5xx for a purged run. This reads
  DTR §6.5 ("a lifecycle error") and DTR §10 ("no error") together: §10 means no server error,
  and §6.5 governs. Both routes are uncatalogued in OpenAPI at the base and need no declaration.

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

### 3.6 Error transport (the M2 Parent error envelope; F-2)

The `/v1/story-runs/*` routes do **not** use the CONV-1 envelope: `error_envelope.py` lists the
CONV-1 prefixes and leaves the frozen M2 Parent families out on purpose (`error_envelope.py:14-22`;
`tests/unit/test_http_error_envelope.py:211`), and D-066-68 C-D1 keeps the M2 Parent envelope for
them. Errors of cancel, delete and GET are therefore the M2 Parent envelope built by the handlers
in `app.py` (request context middleware, HTTP-exception, validation and unexpected-exception
handlers; `app.py:430-520, 600, 766-792`), which this contract does not change (`app.py` is H):
- body fields `code`, `message`, `correlation_id`, `retryable`, `retry_after_seconds`,
  `field_errors`, and `current_version` only on the cancel 409 `STALE_REVISION`
  (`_parent_story_cancel_path`, `app.py:187-188`); the delete route never carries it;
- `field_errors` is null except for request-shape (body, path) validation errors, which carry a
  list of `{field, code, message}` from the validation handler (`app.py:601-662`); key errors
  raised by `parse_idempotency_key` carry null (N-1);
- the `X-Request-ID` header equals `correlation_id`;
- a missing or invalid `Idempotency-Key` on cancel or delete is 400 `INVALID_REQUEST` raised by
  `parse_idempotency_key` (`api_conventions.py:59-69`), so the FastAPI header validation path of
  `app.py:642-646` is not reached for the key.

D-066-68 is recorded in the root checkout (FEAT-066 `DECISIONS.md` line 382) and at the base;
D-066-71 and the CONV-1 approval and evidence are on the local branch only (R5-F1). The other
four Parent POST routes keep their 1-256 key range and are outside FR-C-08 (D-217 item 7).

### 3.7 OpenAPI status (N-2)

Cancel and delete stay **uncatalogued** operations: cancel is already listed in
`PR22_UNCATALOGUED_OPERATIONS` at the base (`test_openapi_contract_catalog.py:120`), and delete is
added to that list (12 → 13). The catalogued operations whose declared response changes are GET
and the create and three confirmation operations (§3.3); `openapi_contract.py` and the catalogue
tests change for those only.

## 4. Key source facts at the base (`03342207`, read-only)

| Fact | Evidence |
|---|---|
| The Parent cancel route exists (202, body `expected_revision`, key 1-256) and its response embeds the full run | `interfaces/http/routers/parent_story_runs.py:253-294`; `contracts/schemas/parent_story_runs.py:148-151` |
| No `DELETE /v1/story-runs/{run_id}` route exists | `parent_story_runs.py` route list (`@router.post` at 126, 253, 297, 322, 353; `@router.get` at 210, 232) |
| The M2 cancel accepts seven source states and writes no lifecycle request, notice, event or audit | `infrastructure/persistence/parent_story_repository.py:328-438` |
| `ParentStoryRunResponseV1.run_state` has ten values (no `ABANDONED`, `DELETED`) | `contracts/schemas/parent_story_runs.py:113-117` |
| The lifecycle request, notice, audit, outbox and aggregate tables require `organization_id` | DTR Draft 6 §3 (S1, S3, S5, S7) |
| The CONV-1 key parser accepts 1-128 visible ASCII | `interfaces/http/api_conventions.py:59-69` |
| `/v1/story-runs/*` errors use the M2 Parent envelope from `app.py`, not CONV-1 | `interfaces/http/error_envelope.py:14-22`; `interfaces/http/app.py:187-188, 430-520` |

DTR Draft 6 §3 and port design Draft 6 §3 hold the full source-fact tables.

## 5. Recorded deviations

| Deviation | Decision |
|---|---|
| User DELETE allowed for `FAILED` and `ABANDONED` (the SRS said completed runs) | D-214 item 1; **closed** by the D-219 SRS revision, which names the three states at every delete site |
| Two extension run states beyond the 18 of SRS line 394 | D-216 item 4; **closed as an SRS deviation** by D-219, which records them in the remarks of line 394 |
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
- The SRS wording edit was applied after the implementation was accepted, by a separately
  started session on the owner's word (D-216 item 6; D-219); this draft is its contract
  alignment.

## 7. Client impact (outside this contract's paths)

The cancel 202 body, the new delete route, the GET union and the replay union of the create and
three confirmation routes change the Parent API that the
mobile Parent client (FEAT-081) and the frozen client-facing OpenAPI projection use. The client
change is FE work in its own lane and approval; this contract does not edit client code or the
client projection. The backend OpenAPI contract files are updated only for the FR-C-08
operations (Allowlist Draft 13).

## 8. Acceptance conditions for the implementation task

1. Cancel accepts exactly the eligible states, enforces revision and the 1-128 key in
   the §3.1 error order, returns the §3.4 envelope, releases the lock in the same transaction, and writes the event, audit and
   receipt as DTR §6.1.
2. Delete accepts only `COMPLETED`, `FAILED` (and `ABANDONED` once storable), returns the same
   envelope, and converges with cancel on one lifecycle request.
3. GET returns the live envelope before `DELETE_PENDING` and the lifecycle envelope after it, with
   `DELETED` only after Story writes it; every replay, including the four other routes of §3.3,
   follows DTR §6.5; error bodies match §3.6.
4. The purge protocol, token rule, retry and reconciliation pass every DTR §10 check, including
   the crash points; the Core step passes every port design §12 check.
5. `DELETED` is terminal for every Parent Story writer; no late result changes a purged run.
6. No fabricated organization in any row; audit rows are metadata only.
7. The schema delta migrates up and down on a disposable database as DTR §9; existing
   organization writers behave as before.
8. Static composition and OpenAPI evidence are reported separately from runtime evidence.

## 9. Lineage

Contract Draft 11 succeeds Draft 10; the matching allowlist is Draft 13. Both were approved for
implementation and the implementation was accepted (FEAT-063 `approvals/TASK_APPROVAL.md`,
FR-C-08 entries of 2026-11-19). Draft 12 succeeds Draft 11 for SRS alignment only (D-219); it
needs no allowlist change, because no path, route or behaviour changes.
