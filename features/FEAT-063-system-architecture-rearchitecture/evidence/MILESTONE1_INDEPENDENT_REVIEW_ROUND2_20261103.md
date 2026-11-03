# Independent review round 2 — StoryRun-lite Milestone 1

Verdict: **NEEDS_REVISION**. Read-only review of the round-1 working tree; no code or test was changed by the reviewer.

## New blocking findings

1. **P2 — attach replay time-of-check/time-of-use race.** The first receipt lookup can finish before a concurrent initial attach commits its receipt and changes the run state. The replay can then fail a mutable target-state check with 404 even though the initial request has committed a 202 receipt. The reviewer asked for serialized reservation/checking or a locked durable recheck after the mutable check fails, with a service/HTTP concurrency test.
2. **P2 — no public StoryRun readiness signal.** Business routes reject work after the singleton lock is lost, but the standalone StoryRun app had no readiness endpoint. The main `/health` route is liveness and must remain distinct. The reviewer asked for public readiness to probe the latched runtime state and a PostgreSQL test that terminates the lock-owning session.

## Round-1 finding matrix from the reviewer

| Finding | Round-2 assessment | Remaining request |
| --- | --- | --- |
| Cancel after confirmation and release active owner | NOT VERIFIED | Add race, duplicate cancel, and stale-revision tests for the confirmed state. |
| Reconcile committed Story result with A1 ledger | CLOSED by code/log evidence | No additional change requested; evidence is loopback, not a live provider run. |
| Attach receipt replay | OPEN | Cover the concurrent first-miss window and PENDING recovery over HTTP/service. |
| Singleton lock | OPEN | Add public readiness, probe concurrency, and actual terminated-session evidence. |
| Bruno upload bytes and admission | NOT VERIFIED | Run the collection and prove upload-part bytes/hash precede completion. |
| GET after confirmation | CLOSED by static inspection | Run Bruno and confirm the separate post-confirm GET asserts PREPARATION_REVIEW. |

The reviewer verified the pinned round-1 plan and prompt hashes, branch/HEAD, the 81-path manifest, and 17 offline tests. The reviewer did not run PostgreSQL, Bruno, ClamAV, the OS worker, Modal, or a provider. The offline regression total lacked a raw output file at that time. The follow-up record and new raw logs below address those evidence gaps; the previous review itself remains historical.
