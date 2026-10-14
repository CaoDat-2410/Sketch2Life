# BE2-01 Phase B plan — revision 2 evidence (PB-R01–PB-R06)

- Date: 2026-10-15, Asia/Saigon. Executor: Claude, docs only (`plan/CLAUDE_PHASE_B_PLAN_REVISION_PROMPT.md`).
- Input review: `PHASE_B_PLAN_CODEX_REVIEW_20261014.md` (NEEDS_REVISION). Review and its metrics
  unchanged.
- Rev 1 preserved: `PHASE_B_PLAN_REV1_ARCHIVE_20261014.md`, byte-identical to the reviewed plan
  (sha256 `cdbb2be692dcb8528438009d578cd2c904801ad9e74ccee3809290d57ffb7ec0`). ADR/port rev 1
  hashes (`04f6c35b…b6b2d03`, `b4e67a83…677074e`) are recorded in the review metrics.
- Outputs: `plan/PHASE_B_PLAN.md` revision 2, `plan/PHASE_B_ADR_PROPOSAL.md` revision 2,
  `plan/PHASE_B_PORT_REVIEW.md` revision 2. Six batches B1–B6 and acceptance IDs B-01..B-12 kept;
  subcases added, no new business task.
- Finding status (executor): **ADDRESSED_PENDING_REVIEW** for all six. Claude does not close the
  independent review.

| ID | Where changed (rev 2) | Proposed protocol / rule | Acceptance added/made concrete | Assumption / owner decision still missing |
|---|---|---|---|---|
| PB-R01 | Plan §2 G4, §5.1, Δ1–Δ3, §6 `accepted_fences`, B-09a–d, B-12; ADR D1 (shared DB), D4, new D7; port review P2 fence row + Q8 | Owner fence: P2 bumps epoch `FOR UPDATE` with the decision change and its notice; BE2 holds the decision's fences `FOR SHARE` in its write transaction via `OwnerFencePort` on the same connection; stale ⇒ rollback, one re-decision, else typed outcome. Linearization = fence-row commit order. Rev 1's “CAS re-decides” claim removed. Fallback (record epoch + read-time check) documented as weaker, requiring amendment | B-09a consent/context change between precheck and write with notice withheld and `job_revision` unchanged ⇒ no start/completion; B-09b artifact quarantine/version; B-09c authorization on create/cancel; B-09d read/cache current-authority + historical receipts unchanged. Component proof uses test-only ASSUMED_CONTRACT fixture; real owner integration listed in B-12 | P2 adoption of the fence (Q8), scope granularity; D7 adoption |
| PB-R02 | Plan Δ4, Δ5, §6 `semantic_request` PK, §7.2, B-03a–f, B-07, B-08a; ADR D4 | `semantic_key_sha256` over canonical JSON (NFC, explicit `null` session, sorted subjects, duplicates kept as Phase A) as PK — no NULL-sensitive unique index. Create = one candidate transaction with plain INSERT; any unique violation ⇒ full rollback (job, attempt, semantic, receipt, outbox, audit intent) then fresh READ COMMITTED re-read of the committed winner; ≤ 2 rounds, then typed retryable conflict | Two processes same key+payload; different keys same semantic (one job/attempt/dispatch/semantic row, per-key receipts); same key different payload; session null vs populated; permuted subjects; restart between rounds; no orphan rows/effects | None beyond D4 adoption (subject-duplicate handling follows Phase A; flag if owner wants dedupe) |
| PB-R03 | Plan §4 (`reconciler.py`, RQ retries disabled), Δ6, Δ7, Δ11, §6 outbox/attempt fields, §7.1 boundaries + crash table, B-04a–c, B-06a/b; ADR D3 (single preferred adapter, PG-only conditions), D5 | Boundaries: publish / durable start (`started_at` commit) / broker ack (not trusted) / completion. SQL reconciler republishes the **same attempt** when dispatched but not started after `DISPATCH_START_TIMEOUT`, ≤ `DISPATCH_MAX`, then `DISPATCH_LOST` → policy retry. Lease owner + generation fence mark/release. **No same-claim recovery** after provider output: bounded loss, old attempt provenance kept, orphan output superseded/quarantined if claimed later; no exactly-once claim | Kill after broker receive before start commit ⇒ progress with unchanged `attempt_id`; `DISPATCH_MAX` path; stale lease holder ack/release after takeover is a no-op; enqueue-before-mark, broker-down, provider/completion windows | D3/D5 adoption; PROPOSED values `DISPATCH_START_TIMEOUT`, `DISPATCH_MAX`; G5 Redis environment (Q7) |
| PB-R04 | Plan Δ8, §4 `worker_capability.py`, B-05e, B-10c; ADR D6; port review P4 Q6 | Typed `VerifiedCapability(job_id, attempt_id, issued_at, expires_at, key_id)`; `_require_worker(token, job_id, attempt_id)` at start/progress/completion (claim attempt). Issuer = backend service identity in dispatcher/reconciler, minted per publish, token only in broker message; TTL = start timeout + attempt timeout + slack; republish reissues; expired ⇒ denied ⇒ timeout/retry; stored-receipt replay requires a valid token for that attempt | Token for attempt A cannot start/progress/complete B; wrong job/tampered/expired denied; delayed delivery ⇒ reissue via reconciler; historical replay behaviour explicit | D6 adoption; secret provisioning/rotation (Q6) |
| PB-R05 | Plan Δ9, Δ6 (`event_id`), §6 outbox, §7.1 last rows, B-06c/d, B-08b; port review P2 audit/artifact rows (Q4, Q5) | Accepted path: mutation + receipt + audit/quarantine intents in the authoritative transaction. Rejection/conflict: audit-only incident transaction (quarantine intent only for committed-final verdicts) committed before responding; failure ⇒ `503 DEPENDENCY_UNAVAILABLE` (retryable), not 409. Deterministic `event_id` for dedup; loser/rolled-back work never delivers quarantine | Conflict stays 409 with job/receipt immutable; redacted conflict audit survives restart; sink redelivery dedups; storage failure at each commit boundary leaves no accepted success without audit intent; no quarantine from rolled-back work | P2 Q4/Q5 (idempotent quarantine/audit by `event_id`) |
| PB-R06 | Plan Δ10, Δ11, §6 `cancellation_notice.status`, B-09e–g | Keep Phase A all-match semantics atomically: one transaction selects all matching non-terminal jobs `FOR UPDATE`, cancels each, then records `COMPLETE`; guard `NOTICE_ATOMIC_MAX` fails typed without marking (no partial completion, no pagination engine). Sweeps that remain paged carry no seen-marker | > `NOTICE_ATOMIC_MAX`/2 matches cancelled atomically; duplicate notice no-op; crash mid-notice ⇒ rollback ⇒ redelivery cancels all, nothing reopened; concurrent create after owner bump fails the fence (PB-R01) | `NOTICE_ATOMIC_MAX` value (PROPOSED); P2 Q3 notice emission in the epoch-bump transaction |

## D3 consistency

Preferred and only planned queue adapter: Redis/RQ (retries disabled; SQL owns redelivery).
PostgreSQL-only remains an alternative whose adoption before approval requires editing plan §4,
G5/Q7 and B-02/B-04 and a re-review; the plan does not build both.

## Not done in this turn

No backend/test/runner/fixture/dependency change; approved Phase A `PLAN.md` and
`TASK_APPROVAL.md` untouched; no PostgreSQL/Redis start, install, cloud, upload, provider call,
commit/push/deploy or contact with anyone. Docs-check receipts:
`raw/phase_b_plan_rev2_docs_{harness,security,diff_check}.txt`,
`metrics/phase_b_plan_rev2_docs_checks.json`; Phase A frozen-hash check
`metrics/phase_b_plan_rev2_frozen_hashes.json`.
