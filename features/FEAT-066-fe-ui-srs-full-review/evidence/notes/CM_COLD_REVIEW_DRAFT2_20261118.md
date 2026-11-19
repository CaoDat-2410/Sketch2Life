# C-M package Draft 2 — cold review record (round 2, 2026-11-18)

- **Artifact:** `plan/PLAN_CM_SCHOOL_MANAGER_SLICE_PACKAGE_DRAFT2_20261118.md`, 21,618 B, SHA-256 `CB0CABD2521E20ADF20C296A408FD01A64C4685244716FA39E2B99F03E100371`.
- **Reviewer:** a separate subagent. Model Sonnet 5.5, reasoning effort high, both set explicitly. It worked read-only.
- **Pin check:** PASS for the artifact, the round-1 record and every §1 input. `08439b22` is an ancestor of `2dddc607`, and CONV-1 changed `lesson_library.py`.
- **Verdict:** **NOT READY**. P1 = 0, P2 = 5, P3 = 6. Round 1 was 1 / 6 / 8.
- **D-171 item 11:** P1 + P2 fell from 7 to 5. Finding classes repeat: CM-R2-01 (evidence claims), CM-R2-03 and CM-R2-05 (privacy false assurance, the CM-R1-01 class), CM-R2-04 (role rule, CM-R1-12). The stop condition is met; a round 3 needs the owner's word.
- **Privacy answer:** after C-M1 as written, no School-Manager-callable route returns a child `display_name` or `age_months`. Residual leaks are free-text and media routes (CM-R2-03, CM-R2-05).

## Round-1 status

| Status | IDs |
|---|---|
| FIXED (9) | CM-R1-01, 04, 05, 06, 08, 09, 10, 11, 14, 15 |
| PARTIAL (5) | CM-R1-02 (CM-R2-01, 02); 03 (CM-R2-03); 07 (CM-R2-06, 07); 12 (CM-R2-04); 13 (CM-R2-09) |

## Findings

| ID | Sev | Finding (short) | Repeats |
|---|---|---|---|
| CM-R2-01 | P2 | The cited 409 assertion (`test_be1_postgres_api.py` 757–759) runs as a School Manager and is recorded by the CONV-1 evidence as failing with 403 (outdated), so the gate has no passing assertion; no Teacher fixture exists on `be1_acceptance` | CM-R1-02, 14 |
| CM-R2-02 | P2 | `consent_is_effective` needs a state the store cannot hold, so every non-empty class answers 409 on the Teacher path; A09 paging and its acceptance are untestable on PostgreSQL. Defer A09 paging to MGR-5, or unit-test it with a stubbed gate | CM-R1-02 (partly) |
| CM-R2-03 | P2 | `child_id` is opaque only when a profile issued it; `RecordConsentRequest.child_id` is a free 1–128 character string that `record_consent` stores without a profile check, so A10 can return caller-typed text (for example a name) to the School Manager. CM-4 needs re-grounding | CM-R1-01, 03 |
| CM-R2-04 | P2 | "Assignment role is teacher" is ambiguous for an org-wide Teacher row (`class_id` NULL); A09 today uses `roles=None`, so the guide/observer 403 is an undisclosed behaviour change | CM-R1-12 |
| CM-R2-05 | P2 | Other School-Manager-callable routes return child media or teacher free text (checkpoint latest/save/restore, artifact download, gallery, observations, portfolio, session `teacher_note`, group `display_name`); SRS 2586 area says "Occurrence and child media: School Manager Deny". The plan neither lists nor defers them | CM-R1-01 class |
| CM-R2-06 | P3 | OpenAPI shape for a role-dependent A09 response not stated; `Be1PilotProfileItem.display_name` is required, so omitting it needs a second model, or deny `school_admin` on the synthetic pilot-profiles route | CM-R1-07 |
| CM-R2-07 | P3 | The frozen snapshots (`openapi-runtime-frozen.json`, `openapi-client-projection-frozen.json`, `API_CONTRACT.md`, `OPENAPI_FEAT063_REV45_20261101.json`) do pin these operations; decide to leave them and record drift (as CONV-1 did) or amend them | CM-R1-07 |
| CM-R2-08 | P3 | The BE-before-FE window also breaks the Manager screens (`setProfiles(result.items)` on a summary; 25 classes only) | CM-R1-04 |
| CM-R2-09 | P3 | CM-5 is compound; CM-1 omits pilot-profiles; the "86 untouched" count shifts | CM-R1-13 |
| CM-R2-10 | P3 | Cite SRS 796 (classes family incl. roster management) and 1640 (explicit deterministic sort) | CM-R1-09 |
| CM-R2-11 | P3 | A web branch carrying a local-only BE merge cannot be pushed until an owner-approved publication step | CM-R1-05 |

## Checks passed

- All claimed routes and line ranges exist; `map_code` and `CONV1_PREFIXES` behave as claimed; the Parent cursor precedent exists (`parent_profile_repository.py` 347–395).
- SRS FR-T-04 (line 543), 2586, 1649, 1650, 1525 and C-D8, D-066-69 quotes are accurate; profile `child_id` is `synthetic-<24 hex>`.
- FE facts: T05 joins on `child_id` and finds the class on page 1; the label map uses uppercase keys; no other `apps/` callers.
- MGR-9 reuse and queue positions are consistent; test-DB rule matches CONV-1; governance clean.

## Not verified

- Nothing was run; CM-R2-01 rests on the CONV-1 evidence note and on reading the test code.
- FE unit tests and Bruno content; mobile code outside `apps/`; MGR-2/3/6 bodies; the exact "86 untouched" set.

## Next

The owner decides between Draft 3 with round 3 and stopping (rounds used: 2 of 5).
