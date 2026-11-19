# C-P addendum Draft 3 — cold review record (round 3, 2026-11-19)

- **Artifact:** `plan/PLAN_FEAT081_CP_PARENT_SLICE_ADDENDUM_DRAFT3_20261118.md`, 18,939 B, SHA-256 `0AFD7DAFFFB2B5CDA761DEB5AC887D56793C7E02B92C6115991780A153A2C155`.
- **Reviewer:** a separate subagent. Model Sonnet 5.5, reasoning effort high, set by the caller. Read-only; no file written.
- **Pin check:** PASS (Draft 3, Draft 2 and its record, Draft 1, projection `F23BF908…`, freeze document `B72228CE…`, ledger `A82335EC…`, SRS, register, FEAT-066 DECISIONS 68,171 B; merge facts and FEAT-081 numbering confirmed).
- **Verdict:** **NOT READY**. P1 = 0, P2 = 2, P3 = 6. Round 2 was 0 / 4 / 7.
- **D-171 item 11:** P1 + P2 fell from 4 to 2; both P2s repeat earlier classes (contract-test method; allowlist completeness), so the stop condition is met. The reviewer states each P2 is a one-sentence fix and the field table is now correct.

## Round-2 status

FIXED: CP-R2-01, 02 (for the named items), 04 to 11. PARTIAL: CP-R2-03 (CP-R3-01).

## Findings

| ID | Sev | Finding (short) |
|---|---|---|
| CP-R3-01 | P2 | `satisfies` fixtures cannot catch an FE field made optional again or an enum widened to `string`; add compile-time `RequiredKeys` and two-way enum-literal assertions, checked at runtime against the JSON `required` and `enum` lists |
| CP-R3-02 | P2 | Certain typecheck breaks in unnamed files: `parentFlowV1.ts` (`readDrawingCandidate` returns legacy `ParentCandidate`; a `decision === 'CONFIRMED'` branch outside the enum) and `useParentController.ts` (run rebuilt with the candidate); name them, keep `ParentCandidate` for the legacy `StoryRun`, validate the three-value enum; keep the `parentSrsBehavior` string assertions intact |
| CP-R3-03 | P3 | `StoryHistoryScreen.tsx` has the same stale `ABANDONED`/`DELETED` values (legacy type, history route unavailable): include or exclude explicitly |
| CP-R3-04 | P3 | Retry-stable key citation is SRS line 1636, not 1635 |
| CP-R3-05 | P3 | `lesson_pin_snapshot` row wording; `activities` items have 3 required fields while FE `Activity` requires 8 |
| CP-R3-06 | P3 | The merge also brings 7 non-backend files (three `docs/context` files, three FEAT-047 files, one FEAT-059 file); Addendum 35 should authorize all paths of `git diff 1c9148e8 ba295f11` |
| CP-R3-07 | P3 | Literals in `parentLearningI2.test.ts` and `parentFlowV1.test.ts` and the harness `decision: 'PENDING'` must be completed; the header check must tolerate an undeclared `X-Request-ID` on story-run operations |
| CP-R3-08 | P3 | Request bodies and the response `request_id` format are not checked by the new test (optional note) |

## Checks passed

Field table matches the projection for all run fields, the context snapshot, both envelopes and the subject confirmation; stale values found; deleting the HomeScreen copy is safe for the UI-copy validator; contract test path, `import.meta.url`, typecheck coverage of tests and `satisfies` support confirmed; two-task split and numbering consistent; governance clean.

## Not verified

Test, typecheck and validator runs; the real merge; live remote state; backend runtime envelope behaviour; register content beyond its pin.

## Next

Rounds used: 3 of 5. The owner decides between a Draft 4 that fixes these notes without a further round, and a round 4.
