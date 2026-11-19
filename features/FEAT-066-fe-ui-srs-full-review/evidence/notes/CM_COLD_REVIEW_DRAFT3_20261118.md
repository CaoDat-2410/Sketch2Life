# C-M package Draft 3 — cold review record (round 3, 2026-11-18)

- **Artifact:** `plan/PLAN_CM_SCHOOL_MANAGER_SLICE_PACKAGE_DRAFT3_20261118.md`, 23,609 B, SHA-256 `B78DD5FF46E275C2E06ED644AA1F5309E7178E09BD9F5608BB163A5349613607`.
- **Reviewer:** a separate subagent. Model Sonnet 5.5, reasoning effort high, both set explicitly. It worked read-only.
- **Pin check:** PASS (artifact, both earlier records, Draft 2, every §1 input including DECISIONS 59,489 B; branches and web worktree).
- **Verdict:** **NOT READY**. P1 = 0, P2 = 2, P3 = 7. Round 2 was 0 / 5 / 6.
- **D-171 item 11:** P1 + P2 fell from 5 to 2. Some classes recur at P3 (OpenAPI shape, snapshots, privacy completeness, test claims), and CM-R3-01 relates to the CM-R2-01 test-claim class. The reviewer states both P2s are mechanical text fixes.
- **Privacy answer:** after C-M1 as written, no School-Manager-callable route returns a child name, age or a profile-issued `child_id`; the remaining gaps are `purpose_ref` (CM-R3-06) and four §8 entries (CM-R3-07).

## Round-2 status

FIXED: CM-R2-01, 02, 04, 08, 09, 10, 11. PARTIAL: CM-R2-03 (CM-R3-06), 05 (CM-R3-07), 06 (CM-R3-03), 07 (CM-R3-05).

## Findings

| ID | Sev | Finding (short) |
|---|---|---|
| CM-R3-01 | P2 | `test_be1_synthetic_pilot_postgres.py` calls `/pilot-profiles` as a School Manager and expects 200 or 409 (T9 tests around lines 1325, 1386, 1400, 1411); CM-2 makes them 403. The file is not in the allowlist and its harness needs a class-scoped Teacher |
| CM-R3-02 | P2 | The pinned DECISIONS now carries D-066-74 (Billing unfrozen; C-M4 waits for B-1 and B-2; queue after PAY-0c open), but the plan still says "Billing frozen" and omits D-066-73 and D-066-74; CM-1 omits B01 |
| CM-R3-03 | P3 | The A10 Manager item `oneOf` has no discriminator (items carry no `contract`); use a distinct page contract |
| CM-R3-04 | P3 | `create_profile` gives an org-wide Teacher 404, not 403; `require_assignment` cannot express a class-scoped check, so a post-check is needed; cite SRS 2586 for reads; A10 still gives an org-wide Teacher `child_id` |
| CM-R3-05 | P3 | "As CONV-1 handled the snapshots" has no support; reword to "stay unchanged; C-M1 evidence records the drift" |
| CM-R3-06 | P3 | `purpose_ref` is also a free 1–128 character string returned to the School Manager |
| CM-R3-07 | P3 | §8 lacks file and line for gallery and group `display_name`, and misses `read_session` `configuration` (`be1_sessions.py` 262–271) and `teacher_pending` (`pilot_assistance.py` ~509–560) |
| CM-R3-08 | P3 | The outdated test also asserts admission, start, canvas, stored rows and events; repair it with a Teacher actor rather than rewriting it |
| CM-R3-09 | P3 | CM-9 bundles three points; several recommendations lack a grounding sentence |

## Checks passed

BE and FE facts, SRS lines 796, 1640, 1649, 1650, 1525 and 2586, the class-scoped Teacher fixture pattern (`test_be1_postgres_api.py` 233–265), queue consistency with D-066-73, the §10 and §11 maps, and governance (no dollar sign, secret, local path or owner chat quote).

## Not verified

Nothing was run; MGR-2/3/6 bodies; FE unit tests and Bruno content; SEED-1 Teacher row shape; mobile worktrees beyond a text search; `oneOf` rendering in the generated catalog.

## Next

Draft 4 (rounds used: 3 of 5).
