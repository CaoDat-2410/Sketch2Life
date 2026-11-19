# C-P addendum Draft 1 — cold review record (round 1, 2026-11-18)

- **Artifact:** `plan/PLAN_FEAT081_CP_PARENT_SLICE_ADDENDUM_DRAFT1_20261118.md`, 9,945 B, SHA-256 `8A417387B9CF5E3F46BBF37AE2E5BF98BC45BE557A44FAC1EF952ECE34D9CDC0`.
- **Reviewer:** a separate subagent. Model Sonnet 5.5, reasoning effort high, both set by the caller. Read-only, except one `git merge-tree --write-tree` to predict conflicts (writes tree objects only; no ref, index or working file changed).
- **Pin check:** PASS. Register `0F3F35FD…`, SRS `B9B1F42D…`; frozen client projection on `origin/dev` 213,111 B, SHA-256 `f23bf908a104667153f88d6438ae8e95be9895a76dab7099877ebe9efc49589d`; `ba295f11` not in `5aa9443a`, `1c9148e8` is; `5aa9443a` pushed.
- **Verdict:** **NOT READY**. P1 = 0, P2 = 8, P3 = 8.

## Main facts found

- `65e0332e` already fixed every legacy path and missing key for the 11 Parent operations, and the FE already has: the profile cursor loop (`loadAllProfiles`), STALE_REVISION re-read on patch, the delete-pending view, the active-run caller, `X-Request-ID` on every request, and an error parser that reads the §9.8 fields and `detail`.
- Parity of the 11 operations against the frozen projection: the 5 profile operations and subject confirmation are OK; create, active, read, context and script confirmation differ only in the **story-run response type** (`run_revision`, `created_at`, `updated_at` absent; several fields optional where required; `run_state` not the enum; `context_snapshot` incomplete; a `CONTEXT_PENDING` fixture value not in the enum).
- The projection has **two error envelopes**: profiles (`ParentErrorResponse` with `request_id` and optional `current_version`) and story runs (`ParentStoryErrorEnvelopeV1` without them); `X-Request-ID` is declared on the profile operations only.
- `git merge-tree` of `5aa9443a` with `ba295f11` predicts **one conflict: `.gitattributes`**. The mobile line's `backend/alembic/env.py` and `compose.yaml` differences survive the merge.
- The detail-only AI parser is in `apps/mobile` (outside FEAT-081 by ADR-0023); the `ui-mobile` parser is already dual; on `ba295f11` only `sketch-guides` lacks the top-level envelope, and it is blocked by O-ASSIST (M2 ledger O1).

## Findings

| ID | Sev | Finding (short) |
|---|---|---|
| CP-R1-01 | P2 | Remaining work lists things already done (cursor loop, STALE re-read, delete-pending, active caller, `X-Request-ID`, envelope parsing); "load more" contradicts the load-all design |
| CP-R1-02 | P2 | Two error envelopes; `correlation_id` not named |
| CP-R1-03 | P2 | "Reuse `X-Request-ID` on retry" is not in C-D2; the idempotency key is what stays stable; the current request-id generator collides on parallel calls |
| CP-R1-04 | P2 | C-P0 conflict list wrong; only `.gitattributes`; `env.py` and `compose.yaml` deviations to confirm with HieuNewBie; pin by commit; validators after the merge |
| CP-R1-05 | P2 | C-P2: `ui-mobile` parser already dual; `apps/mobile` is outside FEAT-081; BE remainder only `sketch-guides`, blocked by O-ASSIST |
| CP-R1-06 | P2 | Register gates O-MOB2, O-9, FEBASE, O-0 not dispositioned; independent review step missing |
| CP-R1-07 | P2 | Bruno requests: no path, numbering or runner; outside `apps/ui-mobile`; O-BRU open |
| CP-R1-08 | P2 | Confirmations put in C-P1 without naming O-PROJ |
| CP-R1-09 | P3 | Truncated pins; projection hash missing; freeze document citation |
| CP-R1-10 | P3 | No plan revision or addendum number; decision-record location |
| CP-R1-11 | P3 | Full list of run-type differences |
| CP-R1-12 | P3 | O3 and O4 status; SRS §21.2 main-activity selection absent from the projection |
| CP-R1-13 | P3 | Contract tests could read the frozen JSON after C-P0 |
| CP-R1-14 | P3 | "After C-T1 BE" refers to an unapproved slice |
| CP-R1-15 | P3 | Delegation decision ID; `SYNTHETIC_TEST` versus `SYNTHETIC_DEV` naming gap |
| CP-R1-16 | P3 | Observation: FEAT-081 STATUS line 122 still says `401ded3c`, not pushed |

## Next

Draft 2 (rounds used: 1 of 5).
