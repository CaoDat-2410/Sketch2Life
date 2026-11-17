# BE2-01 Phase B plan review — revision 1

- Review started: 2026-10-14; finalized: 2026-10-15, Asia/Saigon.
- Result: **NEEDS_REVISION** before implementation approval.
- Reviewed: PHASE_B_PLAN.md rev1, PHASE_B_ADR_PROPOSAL.md and PHASE_B_PORT_REVIEW.md.
- Reviewers: Codex primary, phase_b_persistence_review, phase_b_dispatch_review (read-only).
- This is design/implementability review of proposed changes, not a failure of the closed Phase A code review. Phase B has no implementation to test.
- Original six batches/14-card roadmap, P3 ownership and exclusions remain sound. No provider/UI/live-route/BE1-table scope is requested.

## PB-R01 — P1: job CAS does not fence owner decisions

Locations: PHASE_B_PLAN.md:75; PHASE_B_ADR_PROPOSAL.md:24; PHASE_B_PORT_REVIEW.md:15–17. Current EligibilityDecision/AuthorizationDecision/ArtifactDescriptor have no owner decision fence.

The proposed service reads authorization/eligibility/artifact state before the write, then claims job_revision CAS makes an intervening eligibility change re-decide. Counterexample: BE1 consent/context/quarantine changes after precheck; notice is delayed; the job revision stays equal. CAS succeeds, so start/retry/completion can use the old decision. SRS B19.11/B22.3 require current consent/context/epoch checks at acceptance; serialization of only AI rows does not synchronize owner state.

Required plan correction: define a P2-reviewed validity/version/fencing protocol and its ordering/linearization boundary; job CAS protects only the job. Keep unsupported external-owner guarantees pending until that protocol is adopted; do not present another unfenced precheck as an atomic guarantee or use direct BE1 DB writes. Map minimal port deltas and distinguish component proof under an owner-port assumption from actual integration evidence.

Exit: B-09 barrier tests change consent/context/quarantine between precheck and write while withholding notices and preserving job_revision; stale decisions cannot authorize acceptance/exposure. Current-authority read/cache guards and accepted historical receipts remain correct.

## PB-R02 — P2: SQL uniqueness and losing-create rollback need exact rules

Locations: PHASE_B_PLAN.md:90/101 and B-03/B-07/B-08. Current create inserts a candidate job before semantic/command receipts (service ai_jobs.py:297–302); put methods currently return None.

SemanticRequestKey.session_id is nullable. Default PostgreSQL UNIQUE permits multiple rows whose constrained identity contains NULL; the proposed unique key alone therefore does not enforce Phase A semantic dedup for session_id=None. Specify NULLS NOT DISTINCT or a collision-safe canonical representation, and canonical subject-order hashing. [PostgreSQL 17 UNIQUE documentation](https://www.postgresql.org/docs/17/ddl-constraints.html) supports this behavior.

Separately, ON CONFLICT DO NOTHING + re-read must not leave the losing candidate job/attempt/outbox committed. Define typed conflict/winner selection and full candidate-transaction rollback before bounded authorized replay/redecision; a silent ignored insert is insufficient with the present create sequence. READ COMMITTED reread visibility must be explicit, consistent with [PostgreSQL transaction isolation](https://www.postgresql.org/docs/17/transaction-iso.html).

Exit: two processes, same command key; different keys/same semantic identity; different payload conflict; session None and populated; permuted subject lists; process restart. Assert exact one job/active attempt/dispatch/semantic mapping, correct receipts for each caller key, no orphan candidate rows or effects.

## PB-R03 — P1: recovery stops at broker enqueue, before durable worker start

Locations: PHASE_B_PLAN.md:102/112–114; ADR D3/D5:23–25. Current overdue sweep only selects running jobs with started_at (service:492–500).

Counterexample within process-crash scope: outbox enqueue succeeds and row is marked; RQ execution starts; worker dies before start_attempt commits. SQL job stays queued and no overdue-running sweep selects it. Installed RQ 2.11.0 StartedJobRegistry cleanup only retries when retries_left>0; otherwise abandoned execution becomes FAILED. The plan specifies neither transport retries nor SQL queued reconciliation. RQ same broker id is not a durable application-start acknowledgement.

Required correction: define receive/start/ack boundaries, durable evidence of worker start, bounded same-attempt queued recovery and dispatcher lease ownership/fencing at mark/release. Pick a minimal recovery path; no semantic retry/attempt increment merely to recover transport. Align Redis-required gates/file map/tests with the selected D3 path; PostgreSQL-only remains a proposal until the affected checks/environment are rewritten for it.

The after-provider-before-completion window also says “new attempt or resubmit same claim” without naming a durable source for the latter. Choose supported behavior. If same-claim recovery is promised, identify its durable source/identity; otherwise clearly bound uncommitted output loss/retry and preserve old-attempt provenance/disposition without inventing restored fingerprints.

Exit: kill after broker receive but before SQL start commit; restart proves eventual progress and unchanged attempt identity. Include stale lease holder ack/release after lease takeover, enqueue-before-mark crash, broker-down, running/provider/completion crash boundaries. Never claim exactly-once provider execution.

## PB-R04 — P1: attempt-scoped capability requires a matching port contract

Locations: PHASE_B_ADR_PROPOSAL.md:26; plan §5:69–79. Current WorkerCapabilityVerifier.verify(capability, job_id) and service _require_worker call sites only validate job identity (ports:200–201; service:406–407/433–436/451–453).

D6 signs job/attempt but §5 omits a way to compare the signed attempt with the requested/claimed attempt. With the existing interface, a still-valid token for attempt A can be considered job-authorized for attempt B. Implementing a signature alone does not enforce its attempt scope.

Required correction: list verifier/call-site compatibility changes or a typed verified capability plus service scope check. Define issuer/service authority, expected job+attempt binding, issue/expiry/reissue/replay lifecycle, especially delayed queue delivery and post-restart completion replay. Keep real secret provisioning in runtime config; no credentials in outbox/mobile/logs.

Exit: token A cannot start/progress/complete B in the same job; wrong job, tampered or expired token denied; delayed delivery/recovery and allowed historical completion replay remain explicit.

## PB-R05 — P2: audit moved into a rollback transaction can erase incidents

Locations: PHASE_B_PLAN.md:74; PHASE_B_PORT_REVIEW.md:18. Current completion conflict emits audit then raises inside transaction (service:461–465).

If _audit merely becomes an outbox insert in that transaction, the subsequent COMPLETION_CONFLICT exception rolls the incident back. The accepted branch also needs domain mutation/receipt/audit intent committed together to meet FIX-NFR-03, while speculative side effects from a losing transaction must not escape.

Required correction: specify success audit intent with authoritative commit; rejection/conflict audit committed through a defined audit-only/post-rollback path before the incident response is acknowledged. Define failure behavior and stable delivery event/message identity in the compatibility table (the current AuditEvent has no event_id). Retain transactional quarantine intent, idempotent delivery and no artifact mutation from rolled-back candidate work.

Exit: identical replay vs conflicting replay, immutable job/receipt unchanged on conflict, durable redacted conflict audit survives restart, sink redelivery dedups. Inject storage failure at each commit boundary; no accepted sensitive mutation without durable audit intent; no rolled-back quarantine delivery.

## PB-R06 — P1: limited notice query cannot use the existing final seen marker

Location: PHASE_B_PLAN.md:73. Current apply_cancellation_notice processes all matching jobs then record_notice (service:345–365), with duplicate notices returning immediately.

Replacing the full matching query by jobs_for_notice(notice, limit) and retaining that marker completes only the first page. Remaining matching jobs are omitted permanently on replay, violating existing cancellation behavior.

Required correction: either keep all matching jobs handled atomically (scoped query without limiting notice coverage), or define durable per-notice progress and mark COMPLETE only after draining all pages, with restart-safe replay. Do not add a general scheduler or BE1 lifecycle implementation.

Exit: more than two pages, duplicate delivery and crash after the first page; resume cancels every match, never reopens jobs. Bind newly created concurrent jobs to the owner eligibility/fencing rule in PB-R01.

## Verification and next action

- Independently rehashed all 24 Phase A source/test/runner/approval/approved-plan files: unchanged.
- Reviewed plan rev1 hashes recorded in metrics/PHASE_B_PLAN_REVIEW_CHECKS_20261014.json. Rev1 is preserved as delivered; this review does not edit its design or adopt D1–D6.
- Source traces verified in current ports/service and canonical SRS. PostgreSQL behavior checked against official v17 documentation; installed RQ source inspected, no broker/process failure test was executed.
- Runtime tests NOT_RUN (there is no Phase B code). Existing executor docs receipts are documentation validation only.

Next: Claude revises only these six groups into plan revision2, updating proposed ADR/port questions/file deltas/crash matrix/acceptance consistently. Use plan/CLAUDE_PHASE_B_PLAN_REVISION_PROMPT.md. All are corrections inside planned B1–B6, not additional business cards. No implementation, install, service start, owner sign-off or stack adoption in this revision turn.

ACTIVE Q00 remains pending Phase A consumer/task-owner and Pillow test disposition. Q01 plan review NEEDS_REVISION; implementation NOT_STARTED/UNAPPROVED. G2 cannot close until corrected plan review passes; other owner/environment gates remain explicit.
