# BE2-03 A1 plan review — 2026-10-17

Disposition: **NEEDS_REVISION — 1 P1 / 4 P2** before owner implementation approval.
These are defects in the proposed protocol, not findings against implemented BE2-03
code: implementation is NOT_STARTED. The existing prerequisite code is evidence for
the review and is unchanged.

## Identity and scope

- Branch: `feature/be2-03-assistance-orchestration`, parent HEAD
  `f120c4fce8f7853e5ab5e061eff4bf916d45603c`; staged 0.
- Reviewed plan: `plan/PLAN.md` revision 1, SHA256
  `bb072cf54cc9012f05fcee984b8aae7b6bec2d53dc21a70f446c33cf9c0afe5e`, 32784 bytes.
- Approval remains AWAITING_APPROVAL. This review selects no D1–D10 decision and
  does not open an implementation slot. The reviewed plan bytes are preserved.
- Root Codex reviewed the source and plan, with three delegated same-family source
  audits. This is not a different-model review or BE1/P1/P4 sign-off.
- BE2-01 remains WAITING_STUDIO; BE2-02 remains IN_PROGRESS / NOT_DONE. B-12 HANDOFF
  and OwnerFence ASSUMED_CONTRACT are unchanged.

Python module paths below are relative to `backend/src/sketch2life/`; plan/evidence
paths are relative to this feature. Other source paths are repository-relative at
the pinned parent. Plan line numbers refer to reviewed revision 1, not a later correction.

## Findings

### A1-PR01 — P1: cancellation can miss an in-flight job creation

Plan lines 195–207 separate request commit, job creation and job-link CAS. Line 231
allows releasing the reservation while the request is still `scheduling`.

Interleaving: the reconciler starts `create_job`; cancellation commits while
`job_id` is still null; BE2-01 commits the job/outbox; the late job-link CAS loses
against the cancelled request. The stated cancellation step has no linked job to
cancel, but the new queued job remains runnable. A bumped AssistancePin rejects a
later observation; it does not itself prevent provider execution.

BE2-01 evidence: `application/services/ai_jobs.py` lines 418–445 commit creation
independently; `infrastructure/ai_jobs/fakes.py` lines 564–596 do not inspect BE2-03
request state. A cancellation notice processed before creation is not a standing
subscription: it records completion over currently existing jobs (service lines
517–537).

Revision required: retain the original scheduling command identity/key/revision
and execution authority; define handling of a late returned/replayed job when link
CAS loses; keep a cleanup obligation until cancellation is settled. Do not release
budget merely because the link is absent. An injected request-aware eligibility
adapter and/or explicit compensating cleanup can use existing foundation ports;
the plan must state the chosen guarantee and uncertainty. Add controlled cancel
and stale races before create commit and between create commit and linking.

### A1-PR02 — P2: semantic dedup omits the newly validated pin

Plan lines 188–191 and DECISIONS TC-04 omit the exact resolved audience, source
`input_hash` and `assistance_context_digest` from semantic equivalence; the winner
only has to be readable.

Example: an existing group request pins members A/B; current roster becomes A/C
with the same numeric context revision before any notice is processed. A new
request validates A/C, then deduplicates into the old job whose subjects are A/B.
Same-revision age/consent movement or a changed resolved render has the same gap.
Foundation semantic identity already includes source hash and subjects (service
lines 364–374); C2 explicitly detects same-revision fact movement.

Revision required: include the resolved immutable source/audience/purpose/context
binding in equivalence, or revalidate the winner and reject/stale mismatches before
returning it. Define digest canonicalization and exclusion of operation identity
where needed for semantic comparison. Add changed-roster, changed owner-fact and
changed-render cases with unchanged scalar revision and no processed notice.

### A1-PR03 — P2: queued retry can refund an already spent stage

Plan lines 230–232 and A1-R06 classify a queued cancellation as releasable. A job
can instead be queued for attempt 2 after attempt 1 already ran and failed. If the
assistance reconciler did not observe the earlier running state, it refunds a
spent stage.

BE2-01 `domain/ai_jobs/model.py` lines 311–334 and 390–408 retain earlier attempts
but create a fresh queued active attempt. The public Teacher projection uses only
the active attempt's `started_at` (`application/services/ai_jobs.py` lines
1364–1406). Current state or that timestamp cannot prove that no attempt ever ran.

Revision required: monotonic evidence of any started attempt; release only after
creation/cancellation is settled and no attempt started. Unknown evidence retains
the hold or follows an explicit conservative policy. The new adapter may obtain
trusted history via existing repository ports; no foundation mutation is needed.
Cover prior-start/retry/cancel, never-started dispatch-loss/retry/cancel, and start
winning a cancellation race.

### A1-PR04 — P2: completion-first contradicts the terminal state machine

Plan lines 143–157 make `analysis_ready` terminal and allow cancellation only from
nonterminal states. Lines 203–207 and A1-R03 at line 299 require cancel to win in
both orders with no handoff, even when completion can already have committed
`analysis_ready` and a Sketch intent (lines 252–254).

Revision required: state the linearization point. Distinguish a BE2-02 observation
accepted before the BE2-03 handoff commit from a handoff already committed. Either
completion-first is terminal and a new cancel returns INVALID_STATE, or define a
cancellable post-analysis stage and withdrawal/invalidation of emitted intents.
An emitted intent cannot retroactively have never been emitted. Add tests for both
commit orders and for observation acceptance before handoff.

### A1-PR05 — P2: the queue-failure case tests the wrong boundary

Plan lines 195–199 and A1-R08 at line 304 say QueueUnavailable after request commit
leaves assistance `scheduling` and job reconciliation recovers it. Existing
`create_job` persists a job/outbox and returns without calling the queue (lines
428–445). Publication later catches QueueUnavailable, retains/releases the outbox
lease and returns false (lines 595–607).

Revision required: split (1) lost reply/crash after job commit but before assistance
link, recovered with the same creation command, and (2) broker failure after
linking, leaving assistance `scheduled` and the job queued, recovered by foundation
outbox dispatch. Both must retain one job; do not inject an impossible broker
exception into the creation adapter and call it actual foundation behavior.

## Additional clarifications for revision 2

- Cache lines 240–242 say "BE2-02 replay authoritative". Specify a supported
  current-read gate (for example authorized record plus `downstream_meaning` and
  exact bindings). Do not implement that phrase by calling `record_observation`
  after job success: its lineage guard rejects terminal jobs before replay lookup
  (`application/services/vision_analysis.py` lines 307–317;
  `domain/vision_analysis.py` lines 411–412). Preserve original cache provenance;
  do not relabel an old analysis as created for the new request. This wording
  ambiguity is a clarification, not a sixth blocking finding.
- Explicitly test CMD-33's own idempotency scope, missing key, accepted replay after
  revision bump/turn closure, changed-payload conflict and revoked disclosure. The
  generic receipt rule already requires these; the field map currently names only
  the create scope. No separate new defect is claimed.
- D3 cancellation authority, D5 contributor restrictions and D9 deferred enum
  mapping are explicit owner choices, not implementation approvals or review bugs.
- The reported FEAT-048 number collision on the teammate branch predates this
  feature. It is a separate integration concern, not a reason to rename FEAT-049
  silently during this review.

## Verification and next step

Root ran the existing harness, security, architecture and skeleton validators:
all VALID, exit 0. `git diff --check` passed. This is structural/security evidence,
not proof of the future A1 protocol.

Two narrow probes ran against the actual prerequisite modules in this worktree:

1. With the fake broker unavailable, create still returned one queued job; dispatch
   returned 0 and queued no message.
2. A started, retryably failed job requeued with two attempts and active
   `started_at=None`, while an earlier attempt had started. The Teacher projection
   also returned `started_at=None`.

Both probes' assertions passed. Raw result is ignored under
`evidence/local/codex-plan-review-20261017/foundation_probe.json`; source hashes and
final validation results are in `../metrics/PLAN_CODEX_REVIEW_20261017.json`.
No BE2-03 application tests exist or were claimed to run; no service/provider/
Studio execution, dependency installation or Git publication occurred.

Next: Claude revises planning documents only, makes a new revision/hash and adds
acceptance cases for the findings. Codex re-reviews before the owner approves the
exact scope and choices. Do not approve revision 1 as-is.
