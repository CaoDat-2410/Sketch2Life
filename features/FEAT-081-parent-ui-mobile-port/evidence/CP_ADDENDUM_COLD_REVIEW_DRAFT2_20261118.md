# C-P addendum Draft 2 — cold review record (round 2, 2026-11-18)

- **Artifact:** `plan/PLAN_FEAT081_CP_PARENT_SLICE_ADDENDUM_DRAFT2_20261118.md`, 13,540 B, SHA-256 `4BEA9D32C1D811ADDA6B3BA3C0E0D894FABCD270EC945807AA40F131DECAA95C`.
- **Reviewer:** a separate subagent. Model Sonnet 5.5, reasoning effort high, both set by the caller. Read-only; one early command with a temp-folder redirect was refused by the classifier and wrote nothing; no `merge-tree` run.
- **Pin check:** PASS (Draft 2, round-1 record, projection `F23BF908…`, freeze document `B72228CE…`, register, SRS; `5aa9443a` contains `1c9148e8`, not `ba295f11`).
- **Verdict:** **NOT READY**. P1 = 0, P2 = 4, P3 = 7. Round 1 was 0 / 8 / 8.
- **D-171 item 11:** P1 + P2 fell from 8 to 4, but CP-R2-01 repeats the CP-R1-11 class and CP-R2-03 partly repeats CP-R1-13, so the stop condition is met; a round 3 needs the owner's word. The reviewer judges the draft close: one focused revision should do it.

## Round-1 status

FIXED: CP-R1-01 to 08, 10, 12, 14, 15, 16. PARTIAL: CP-R1-09 (CP-R2-06), 11 (CP-R2-01), 13 (CP-R2-03).

## Findings

| ID | Sev | Finding (short) |
|---|---|---|
| CP-R2-01 | P2 | The story-run difference list is incomplete: 14 of the 23 required run fields are optional in the FE (not 5); three enums untyped (`run_state`, `story_status`, `job_state`); `context_snapshot` `age_months` and `interests_summary` optional; envelope `request_id` optional; subject confirmation `decision` is the constant `CONFIRMED`; `story`, `candidate` and `lesson_pin_snapshot` looser than the projection. Needs a field-by-field table |
| CP-R2-02 | P2 | Allowlist misses `ParentVisualPreviewHarness.tsx` (builds a run literal with `ACTIVE`), three test files with `CONTEXT_PENDING`, and HomeScreen `terminalRunStates` with `ABANDONED` and `DELETED` |
| CP-R2-03 | P2 | A vitest test cannot compare TypeScript types at runtime; state the method (stub `fetch` against the JSON for path, method, headers; fixtures from the projection's `required` lists checked with `satisfies`) and the JSON path |
| CP-R2-04 | P2 | C-P0 ends with a push while §5 has one commit and a push after review; say whether C-P0 and C-P1 are two tasks or defer the C-P0 push |
| CP-R2-05 | P3 | O4 wording: C-D1 covers every Parent route; the runtime already sends `request_id` and `current_version` on story-run errors; the projection under-documents them |
| CP-R2-06 | P3 | Pin the M2 limitation ledger; name `ADR-0023-feat081-mobile-ui-target.md` (two ADR-0023 files exist) |
| CP-R2-07 | P3 | State the `X-Request-ID` pattern and the randomness source; the per-attempt convention is borrowed from the Demo client |
| CP-R2-08 | P3 | `validate_skeleton.py`; Addendum 35 must authorize the merge-commit scope; D-066-70 says HieuNewBie joins; check the remote tip before the side branch |
| CP-R2-09 | P3 | Say the register and L5 wording will be aligned for the Bruno move, and that approval closes the C-P half of CV-1 |
| CP-R2-10 | P3 | `CONTEXT_PENDING` should be deleted (runs start as `INPUT_PROCESSING`); "type the two envelopes" has no FE consumer |
| CP-R2-11 | P3 | §2 attribution wording; only the 7 state-changing operations carry a key |

## Checks passed

Two envelopes and `X-Request-ID` declaration match the projection; 11 operations (5 + 6); profile types match; numbering consistent; CP-2 and O-PROJ honest; C-P0 pinning matches D-066-70 D-C; Parent AI claims hold; governance clean.

## Not verified

Live remote state; real merge result; test, typecheck and validator results; archived Revision 19 files; HieuNewBie's timing; reused `X-Request-ID` behaviour; full SRS §21.2 wording.

## Next

The owner decides between Draft 3 with round 3 and stopping (rounds used: 2 of 5).
