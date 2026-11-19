# C-M package Draft 1 — cold review record (round 1, 2026-11-18)

- **Artifact:** `plan/PLAN_CM_SCHOOL_MANAGER_SLICE_PACKAGE_DRAFT1_20261118.md`, 14,598 B, SHA-256 `550CD244E4619DA8B8583F5B685B65975939C0651B5C04DD6365C14DDE5E6F1E`.
- **Reviewer:** a separate subagent. Model Sonnet 5.5, reasoning effort high, both set explicitly. It worked read-only.
- **Pin check:** PASS for every input in §1, the branches and commits (`2dddc607` local only; `08439b22` pushed) and the web worktree (`297a28b1`). CONV-1 Draft 5 (47,483 B, `3FCF4741…`) matches D-066-71 but is not pinned in the artifact.
- **Verdict:** **NOT READY**. P1 = 1, P2 = 6, P3 = 8.
- **Coordinator spot-check:** two points are confirmed:
  - `GET /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/roster` (`be1_sessions.py` line 299) allows `school_admin` and returns `display_name` (line 352) (CM-R1-01);
  - the consent state `CHECK` allows only `pending` and `revoked` (`be1_models.py` line 241), while the School Manager label map expects `ACTIVE`, `PENDING`, `REVOKED` (CM-R1-02, CM-R1-10).

## Findings

| ID | Sev | Finding (short) |
|---|---|---|
| CM-R1-01 | P1 | Two other School-Manager-callable routes return child names: the session roster (`be1_sessions.py` ~297–360) and the synthetic pilot-profiles route (`be1_registry.py` 326–396, local/test only). The C-M1 acceptance "School Manager response never contains a name or an age" gives false assurance for D-066-69 and SRS 2586 |
| CM-R1-02 | P2 | A09 has a consent gate: `list_profiles` returns 409 `CONSENT_NOT_EFFECTIVE` when any profile lacks effective consent, and `effective` cannot exist in the store, so today A09 returns items only for an empty class (asserted in `test_be1_postgres_api.py` 757–759). The plan does not say whether the Manager projection bypasses the gate or how the gate works with cursors |
| CM-R1-03 | P2 | The opaque-reference idea is not shown to be needed: `child_id` is already an internal opaque ID, the Manager consent table never shows it, and a new reference needs storage not in the allowlist. CM-4 should offer real options |
| CM-R1-04 | P2 | Teacher impact under-specified: default 25 truncates silently; `T05ClassesScreen` joins profiles and consents and finds the class on page 1; BE lands before the FE fix; CM-2 bundles two asks |
| CM-R1-05 | P2 | C-M1 is stacked on a local-only branch with no question on branch, base and publication; the pin must be refreshed when the queue slot opens; C-M2 cannot start from `08439b22` because CONV-1 changed `lesson_library.py` |
| CM-R1-06 | P2 | Missing question: what does the Manager roster show (counts only, or counts plus opaque rows); the count chip uses `profiles.length`, which breaks once paged |
| CM-R1-07 | P2 | Implementer would guess: no cursor helper exists (only `limit_query()`); invalid-cursor behaviour; per-route ordering (A10 sorts `recorded_at` newest first); one contract name for two shapes; allowlist misses CONV-1 tests, frozen OpenAPI snapshots, FEAT-047 `API_CONTRACT.md` and Bruno request 012 |
| CM-R1-08 | P3 | `SchoolOverviewPage` is not a list caller; the `RosterConsentPage` class picker is; FE ordering with M9-A and M9-B not stated |
| CM-R1-09 | P3 | CM-1 cites SRS 1649/1650 (POST routes) for read rows; readiness line omits O-5 and O-9 |
| CM-R1-10 | P3 | BE consent states are `pending` and `revoked` only; the FE "Đã ghi nhận" label has no BE value |
| CM-R1-11 | P3 | `get_class` still raises `CLASS_NOT_FOUND`; the plan should say how the public code is aligned |
| CM-R1-12 | P3 | Full fields must be Teacher-only with default deny (`guide`, `observer` rows exist); "enrollment state" source ambiguous |
| CM-R1-13 | P3 | CM-1 and CM-4 are compound; CM-5's recommendation applies equally to C-M3 |
| CM-R1-14 | P3 | Missing pins (CONV-1 Draft 5, uncommitted DECISIONS); "Today" column source; NEW markers; D-066-66/67 not cited; test runner not named |
| CM-R1-15 | P3 | Bruno L5 per-slice update not mentioned |

## Checks passed

- All claimed routes exist; B02, B01, A07, A09, A10 behaviours match the source; callers of A07, A09, A10 are exactly the School Manager services, the two Teacher screens and `shared/api/backendApi.tsx`.
- CONV-1 "no paging for BE1 lists" (Draft 5 line 236), G0 closure at `08439b22`, the decision quotes, SRS 1525, 1649, 1650, 2586 and §21.1, Q168 at line 2924, and the MGR-9 reuse are accurate.
- Governance: authorizes nothing; English; no dollar sign, secret or absolute local path.

## Not verified

- Runtime behaviour (no tests run); full MGR-2/3/6 contracts; FE unit tests and Bruno requests beyond presence; A12, A13, G06 behaviour beyond route existence; mobile code outside `apps/`.

## Next

Draft 2 (rounds used: 1 of 5).
