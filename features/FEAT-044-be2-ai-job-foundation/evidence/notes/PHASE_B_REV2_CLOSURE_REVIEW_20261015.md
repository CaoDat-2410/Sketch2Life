# Phase B revision 2 — focused closure review

- Date: 2026-10-15, Asia/Saigon.
- Overall result: **NEEDS_REVISION for two bounded implementation-contract corrections only**.
- Original PB-R01–PB-R06: CLOSED_ORIGINAL_PLAN_CASE at design-review scope.
- Reviewers: Codex primary, phase_b_persistence_review, phase_b_dispatch_review (read-only).
- Phase B implementation: NOT_STARTED/UNAPPROVED; runtime evidence: NOT_RUN.
- Plan/ADR/port rev2 and executor evidence retained unchanged by this review. This is not owner approval or adoption of D1–D7.

## Original finding closure

| ID | Closure | Evidence in plan rev2 | Remaining external gate |
|---|---|---|---|
| PB-R01 | CLOSED_ORIGINAL_PLAN_CASE | §5.1 / Δ1–Δ3: P2 changes owner epoch/decision/notice in one transaction; BE2 holds FOR SHARE on the same connection until its commit, rejects stale epochs; B-09a–d | D7/Q8 adoption; component fixture is ASSUMED_CONTRACT, real owner integration still B-12. Weaker fallback requires amendment/re-review |
| PB-R02 | CLOSED_ORIGINAL_PLAN_CASE | Δ4/Δ5, semantic hash PK, §7.2: explicit null/sorted subjects and full losing-candidate rollback before fresh reread; exact-count B-03 subcases | D4 adoption |
| PB-R03 | CLOSED_ORIGINAL_PLAN_CASE | Δ6/Δ7, §7.1: SQL same-attempt queued recovery, lease generation, separate publish/start/ack; no unsupported same-claim recovery | PB-C01 below; D3/D5/policy/environment adoption |
| PB-R04 | CLOSED_ORIGINAL_PLAN_CASE | Δ8/D6: typed capability checks both job and attempt; issuer, TTL, per-publish reissue/expiry/replay are explicit | Queue carrier part of PB-C02; D6/secrets provisioning |
| PB-R05 | CLOSED_ORIGINAL_PLAN_CASE | Δ9: authoritative mutation/receipt/intents together; audit-only incident commit before response with 503 on failure; stable event identity | Quarantine carrier part of PB-C02; P2 sink contract |
| PB-R06 | CLOSED_ORIGINAL_PLAN_CASE | Δ10: all matching jobs FOR UPDATE, one transaction, notice COMPLETE only after all; oversize typed-fail without completion, B-09e–g | NOTICE_ATOMIC_MAX remains PROPOSED; oversized notice is pending, never accepted as processed |

No unrelated correctness/security/style audit was added. The two follow-ups are exact deltas needed to implement the selected revision2 mechanisms, not new business cards.

## PB-C01 — P2: declare the queued dispatch-loss domain transition

Source: PHASE_B_PLAN.md:123 (Δ7), :170 (crash table), :193 (B-04b); current domain/ai_jobs/model.py:311–341, especially :320–322.

Rev2 says a still-queued attempt exceeding DISPATCH_MAX becomes retryable DISPATCH_LOST then follows normal retry. Current pure record_failure rejects every state except RUNNING. The plan omits domain/model.py from allowed outputs/file map and :130 says no other domain change. As written, the executor would either hit InvalidJobTransition, fake a started event, or make an unlisted domain change.

Required correction: explicitly authorize a small pure queued dispatch-loss transition as part of the already-selected D5/Δ7. Preserve started_at=None, finish/history/revision/provenance, apply existing remaining-attempt/backoff rules, and exhaust when there is no retry budget. Add exact domain file/service/fake/test deltas to the map and remove the conflicting blanket sentence. Keep DATA-25 states closed; do not allow arbitrary queued failures through the existing provider-failure operation.

Acceptance under existing B-04b: queued with retries left → failed_retryable with correct schedule; final attempt → failed_exhausted without scheduling; no invented provider-start/progress; start-versus-reconciler CAS race has one valid winner and cannot overwrite a committed running/completed outcome. Transport republish before the bound still uses the same attempt.

## PB-C02 — P2: complete the transient transport/side-effect port contracts

Sources: PHASE_B_PLAN.md:124–125 (Δ8/Δ9), D6 in PHASE_B_ADR_PROPOSAL.md, artifacts/Q4 in PHASE_B_PORT_REVIEW.md. Current ports/ai_jobs.py:107–115/212–223.

Two related carrier omissions are grouped here so they receive one small compatibility-table revision:

1. Dispatcher/reconciler mint a capability per publish, but DispatchQueuePort.enqueue(DispatchMessage) cannot receive it and DispatchMessage has no capability field. Specify an explicit transient envelope or keyword parameter (or a fully described equivalent issuer/adapter protocol), updating queue-port/fake/worker call compatibility. Keep SQL outbox DispatchMessage and receipts token-free.
2. P2 quarantine is required to dedup by event_id, but ArtifactPort.quarantine(refs, reason) cannot receive that id. Specify QuarantineIntent(event_id, refs, reason) or an event_id argument/envelope with the corresponding fake/sink compatibility. The outbox's event_id must be the exact delivered id, not regenerated per retry.

Acceptance under existing B-05e/B-10c/B-06c/d: broker carries the right token to the worker; SQL outbox/receipts/logs contain none. Crash after the quarantine effect but before delivery acknowledgement replays the same event id idempotently. Reuse current owned-lineage rules and never deliver quarantine from rolled-back work.

Use “authoritative settlement” for every committed job-changing completion, including rejected/stale/unsafe dispositions; only non-authoritative guards/conflicts use the audit-only path. This wording clarification belongs in the same table update, not another finding/card.

## Evidence independently checked

- All 24 source/test/runner/approved PLAN.md/TASK_APPROVAL.md hashes in the final Phase A snapshot remain unchanged.
- Rev1 plan archive is byte-identical to the reviewed cdbb2be6…ffb7ec0.
- Rev2 executor documentation receipts exist with exit0; no actual Phase B runtime tests were executed.
- Exact record_failure guard and current token/event-id-less port signatures inspected. These are logical implementability counterexamples, not claimed runtime reproductions.
- Frozen rev2 document hashes and final review documentation gates recorded in metrics/PHASE_B_REV2_CLOSURE_REVIEW_CHECKS_20261015.json.

## Next bounded step

Use plan/CLAUDE_PHASE_B_REV2_COMPLETION_PROMPT.md to prepare revision3 with **PB-C01/PB-C02 only**, preserving six batches/B-01–B-12/14 cards. Do not redesign the fence, persistence, queue recovery or audit mechanisms whose original cases closed here, except their directly required compatibility wording.

After these two corrections receive focused closure review, the remaining path is explicit Phase A disposition, D1–D7/ports/environment owner decisions and separate Phase B approval. Code cannot start from a plan review alone. ACTIVE Q00 remains; Phase A code review PASS retained; whole BE2-01 IN_PROGRESS.
