# BE2-01 Phase B plan — revision 3 evidence (PB-C01, PB-C02)

- Date: 2026-10-15, Asia/Saigon. Executor: Claude, docs only (`plan/CLAUDE_PHASE_B_REV2_COMPLETION_PROMPT.md`).
- Input: `PHASE_B_REV2_CLOSURE_REVIEW_20261015.md` — PB-R01–R06 CLOSED_ORIGINAL_PLAN_CASE;
  NEEDS_REVISION for PB-C01/PB-C02 only. Review, metrics and earlier receipts unchanged.
- Rev 2 preserved byte-identical: `PHASE_B_PLAN_REV2_ARCHIVE_20261015.md`
  (sha256 `6bdf86d05b5d95df18ad60381d28585b71e7ce21bbc57c38f2d713fde00869f1`, equal to the reviewed
  rev 2). Rev 1 archive unchanged. ADR/port rev 2 hashes (`48fa3c0e…fddae5b93`,
  `bfe46316…f2f46cac`) recorded in `metrics/PHASE_B_REV2_CLOSURE_REVIEW_CHECKS_20261015.json`.
- Outputs: `plan/PHASE_B_PLAN.md` revision 3, `plan/PHASE_B_ADR_PROPOSAL.md` revision 3 (D5/D6
  wording), `plan/PHASE_B_PORT_REVIEW.md` revision 3 (P3, P2-artifacts, P4 rows). B1–B6,
  B-01..B-12 and the 14 cards unchanged; only subcases added. The closed PB-R01–R06 mechanisms
  (fence, persistence, queue recovery, audit) are not redesigned.
- Status (executor): **ADDRESSED_PENDING_REVIEW** for PB-C01 and PB-C02.

| ID | Where changed (rev 3) | Exact proposal | Acceptance added (existing IDs) | Assumption / owner decision still missing |
|---|---|---|---|---|
| PB-C01 | Plan header/G2, §3 allowed outputs, §4 file map (`domain/ai_jobs/model.py`; Phase A tests/fakes/harness/runner/fixtures rows), Δ7, new **Δ13**, closing sentence (“beyond Δ1–Δ15; Δ13 only domain change; `DISPATCH_LOST` only new code”), B4 row, §7.1 receive/start row, B-04b(i–v); ADR D5 | Pure `record_dispatch_loss(job, attempt_id, *, public_message, now)`: only `queued` + active + `started_at is None`, else `InvalidJobTransition`; fixed code `DISPATCH_LOST`; attempt `finished_at`, `outcome="dispatch_lost"`, `started_at` stays null, request/provenance kept, history + `job_revision+1`; budget left ⇒ `failed_retryable` with existing `backoff_after`; none ⇒ `failed_exhausted`, `completed_at`, no schedule. `record_failure` remains RUNNING-only. Reconciler applies it only after re-reading the job as still queued with the same unstarted attempt and expected revision (CAS vs `start_attempt`) | B-04b: (i) retryable with schedule; (ii) final attempt exhausted, no schedule/reopen; (iii) no invented start/progress, provenance kept; (iv) one CAS winner vs start, no overwrite of running/completed; (v) republish before the bound keeps the same attempt; plus pure domain unit cases (`record_failure` still rejects queued) | `DISPATCH_MAX`, `DISPATCH_START_TIMEOUT` still PROPOSED; D5 adoption |
| PB-C02 (queue) | Δ8 carrier note, new **Δ14**, B4/B5 rows, B-05e, B-10c; ADR D6; port review P3 + P4 rows | Transient `WorkerDispatchEnvelope(message: DispatchMessage, capability: str)`; `DispatchQueuePort.enqueue(envelope)`; new P3 port `WorkerCapabilityIssuer.issue(job_id, attempt_id, now) -> str` called by dispatcher/reconciler just before enqueue; `AiJobDependencies.capability_issuer`; RQ args = envelope with `description=message_id`, `result_ttl=0`, short `failure_ttl`, no argument logging; worker uses `envelope.capability`. `DispatchMessage`, outbox, receipts, audit, logs token-free. Fakes: envelope-carrying `FakeQueue`, `FakeWorkerCapability` as issuer+verifier, `FakeWorker` no longer mints | B-05e: token reaches worker only via broker envelope; absent from SQL outbox, receipts, audit intents and captured dispatcher/RQ/worker logs. B-10c: same on real Redis/RQ | D6 adoption; key provisioning/rotation (P4 Q6) |
| PB-C02 (quarantine) | New **Δ15**, Δ9 (“authoritative settlement” wording), §7.1 new crash row, B5 row, B-06c/d; port review P2-artifacts row (Q4) | `QuarantineIntent(event_id, organization_id, job_id, attempt_id, artifact_refs, reason_code)`; `ArtifactPort.quarantine(intent)` replaces `quarantine(refs, reason)`; `event_id` deterministic, computed once when the intent is written in the committing transaction, stored in the outbox and resent unchanged on every redelivery; intents only from `_owned_refs`; fake keeps `quarantined` map + applied `event_id`s, repeat = no-op. Δ9 now says **authoritative settlement** for every committed job-changing completion (accepted, stale, rejected/unsafe/malformed, eligibility-cancel) and **non-authoritative rejection/conflict** for the audit-only path | B-06c: crash after quarantine effect before delivery mark ⇒ redelivery with the same stored `event_id` is a sink no-op; B-06d: no quarantine from loser/rolled-back work, intents only owned-lineage refs | P2 Q4: sink idempotency by `event_id` and lineage recording |

## Not done in this turn

No backend/test/runner/fixture/dependency change; approved Phase A `PLAN.md`/`TASK_APPROVAL.md`
untouched; no service start, install, cloud, upload, provider call, commit/push/deploy or contact.
D1–D7, Q1–Q8, policy values and environment remain PROPOSED/PENDING; no sign-off created.
Docs-check receipts: `raw/phase_b_plan_rev3_docs_{harness,security,diff_check}.txt`,
`metrics/phase_b_plan_rev3_docs_checks.json`; Phase A frozen-hash check
`metrics/phase_b_plan_rev3_frozen_hashes.json`.
