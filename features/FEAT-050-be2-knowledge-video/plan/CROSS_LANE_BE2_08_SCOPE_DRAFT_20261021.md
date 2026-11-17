# BE2-08 cross-lane submission and finalization scope addendum

- Status: DRAFT / AWAITING_OWNER_APPROVAL
- Card: FEAT-050 / BE2-08, video pipeline ownership
- Addendum to: plan/PLAN.md revision 1; the frozen plan is not edited
- Integration design: FEAT-057 plan revision 4, SHA256
  6AF69E07E7FC51BD6AAA992A703FBE97AC2BC8E588FEC9F8735FBF74E88C6601
- Proposed scope SHA256: fill after final review, before approval

## Purpose and approval boundary

BE2-08's component ports describe atomic submission and finalization, but no durable
cross-card adapter has been adopted. This addendum proposes the narrow BE2-07 ->
BE2-01 -> BE2-08 generation and committed-output path. It does not rewrite the frozen
BE2-08 plan, authorize a provider/runtime, or claim a transaction spanning generation.

## Proposed implementation scope

### Boundary A: atomic submission

One authorized submission commit creates or replays the exact video run, foundation
job/attempt, dispatch/outbox, semantic/idempotency receipt and required audit intent.
The boundary is scoped to the original organization/session/principal and exact
command body. Same-key/same-body returns the authoritative original receipt;
same-key/different-body conflicts. The foundation's authorized create path is used;
BE2-08 never writes foundation tables directly.

### External work

Source resolution, media preparation, rendering/provider work, validation and private
staging happen between the two commits. No database transaction is held open across
external generation. The worker must reauthorize/revalidate at each phase and must
not turn a missing or ambiguous receipt into permission to generate again.

### Boundary B: atomic finalization

One authorized finalization commit records the exact final artifact ref/hash and
terminal video run state together with the authoritative foundation completion
receipt/job outcome/outbox/audit state. The commit uses a current producer source
fence and the applicable BE2-14 policy gates. Lost acknowledgement is resolved by
an authoritative scoped receipt lookup; unavailable lookup remains pending. Late or
losing results cannot overwrite accepted artifacts and follow the adopted quarantine
protocol.

### Worker and policy consumer

BE2-08 owns VideoWorker admission and finalization behavior. BE2-01 owns the typed
router. BE2-14 owns policy decisions and accounting primitives. BE2-08 checks the
adopted policy boundary at create, dispatch/retry, generation/validation/staging and
finalization as defined by an approved phase mapping. Current-use eligibility does
not itself grant worker/provider authority or budget.

## Candidate allowed files

- Modify: backend/src/sketch2life/application/knowledge_video_create.py
- Modify: backend/src/sketch2life/application/knowledge_video_worker.py
- Modify only with approved contract changes:
  backend/src/sketch2life/application/ports/knowledge_video.py
  backend/src/sketch2life/application/ports/knowledge_video_media.py
  backend/src/sketch2life/application/ports/knowledge_video_worker.py
- Modify owned persistence only if the final contract fits the existing schema:
  backend/src/sketch2life/infrastructure/knowledge_video/tables.py
  backend/src/sketch2life/infrastructure/knowledge_video/sql.py
- Card-owned tests: backend/tests/unit/test_knowledge_video_create.py,
  backend/tests/unit/test_knowledge_video_worker.py,
  backend/tests/unit/test_knowledge_video_persistence.py. Any new contract-test path
  must be added to a reviewed scope revision before implementation.
- Excludes foundation table/schema files, BE2-07 producer code, BE2-09 review rows,
  BE2-14 policy storage, FEAT-057 composition tests, router registration, and live
  HTTP/provider/runtime configuration.

No migration is included in this draft. If CR08-01 requires a schema change, stop,
write a schema-specific revision and approval, and do not edit an existing migration.

## Acceptance criteria

| ID | Required result |
|---|---|
| V01 | Submission atomically creates the video run and authorized foundation job/dispatch/receipt intent, or returns the exact committed replay; no split success. |
| V02 | Same idempotency key with a different canonical body conflicts; an ambiguous create acknowledgement is resolved by scoped authoritative lookup, never by guessing. |
| V03 | Foundation job reaches VideoWorker only through the approved BE2-01 route; admission validates persisted job/request/attempt identity before external work. |
| V04 | External generation is between submission and finalization commits, with no DB/UoW held across it. |
| V05 | Finalization atomically commits exact artifact lineage and foundation completion receipt/state; duplicate, lost-ack, and competing late-result cases have a single authoritative winner. |
| V06 | Source-fence loss or policy denial before finalization leaves no accepted output; ambiguous receipt authority remains pending and cannot trigger rerender. |
| V07 | Worker phase checks distinguish eligibility, execution authorization and budget/concurrency reservation; unknown or unavailable required gates fail closed. |
| V08 | Existing BE2-08 offline acceptance/regression passes; FEAT-057 separately proves composed X01 and X09-08. No runtime/provider pass is inferred. |

## Blocking contracts and stop conditions

- CR08-01 must name the owner of each commit, exact rows/receipt, connection/UoW,
  rollback rule, unique conflicts and recovery query.
- BE2-07 must adopt the source-currentness contract held through finalization. Without
  it, source re-read is insufficient and X01 remains PARTIAL.
- BE2-01 must adopt the dispatch receiver contract and request/run mapping.
- BE2-14 must adopt phase mapping, execution authorization, and budget/concurrency
  reserve/settle semantics before generation is enabled.
- Unknown currentness, authorization, policy, or receipt state fails closed.
- Excludes BE2-09 review/playback and X05c/CR09-02; X05d is a separate BLOCKED gate.

## Proposed implementation sequence

1. Approve CR08-01 owner/transaction/recovery semantics and exact file manifest.
2. Implement and test Boundary A with replay/conflict/lost-ack cases.
3. Integrate typed admission and policy gates without invoking a real provider.
4. Implement and test Boundary B with source-fence, receipt, late-result and rollback races.
5. Run BE2-08 offline regressions, then FEAT-057 composition on one pinned snapshot.
6. Conduct independent review/fix/retest. Keep runtime and card acceptance gates open.

## Approval state

No implementation approval is recorded. Existing BE2-08 approval for revision 1 is
card-local and does not approve this CR08-01 cross-card addendum.
