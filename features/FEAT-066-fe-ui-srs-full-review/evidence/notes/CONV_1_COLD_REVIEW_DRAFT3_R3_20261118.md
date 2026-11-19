# CONV-1 Draft 3 — cold review record (round 3, 2026-11-18)

- **Artifact:** `plan/PLAN_CONV1_BE_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT3_20261118.md`, 40,443 B, SHA-256 `32C0261652FC258175D3F5D65BC5AB8298E9CCC31CC18B015EE7D2FD995EBF6F`.
- **Reviewer:** a fresh subagent, distinct from the reviewers of rounds 1 and 2. Model Sonnet 5.5 (`claude-sonnet-5-5`), reasoning effort high, both set explicitly. It worked read-only and statically.
- **Pin check:** PASS. It covered Draft 3, the round-1 and round-2 records, the conventions contract, the SRS and HEAD `08439b22`.
- **Verdict:** **NOT READY**. P1 = 0, P2 = 2, P3 = 8.
- **Round-2 status:**
  - Fixed: N1, N3 to N14 (N6 only for `apps/mobile`).
  - Partly fixed: N2.
  - The round-1 and round-2 class "existence disclosure through the 404/403 split" did **not** repeat, and no new oracle was found.
- **Coordinator spot-check:** both P2s are confirmed in source.
  - `lesson_library.py:611–617` swallows only a 403 from `_manager`.
  - `app.py:273–275` skips operations with no catalog row, and `openapi_contract.py` has 0 rows for `/api/platform-admin`, `/api/auth/v1` and `/api/teacher/v1`.

## Findings

| ID | Sev | Finding (short) | Same class as earlier? |
|---|---|---|---|
| R3-01 | P2 | `revoke_parent_group_membership` (`lesson_library.py:611–617`) swallows only 403 from `_manager` so that it can fall through to the Parent self-revoke path. After §3.2 item 3, a Parent account gets 404, which is re-raised, so Parent self-revoke breaks. The code is outside allowlist row 6, and no test covers it | No: a new class, where a consumer depends on the guard's status |
| R3-02 | P2 | `_apply_catalog_metadata` skips operations without catalog rows (`app.py:273–275`). Platform Admin, auth and Teacher AI have none, so the proposed OpenAPI mechanism cannot reach them, and AC8 cannot hold for them | **Yes:** the same class as round-2 N2, the OpenAPI mechanism |
| R3-03 | P3 | The BE1 422-row rule refers to a "documented code", but catalog rows carry no code | No |
| R3-04 | P3 | `be1_canvas.py:370–371` maps domain codes to 403 and is missing from the kept-403 list | No |
| R3-05 | P3 | `apps/ui-mobile` (the Parent app) calls in-scope `/api/auth/v1` and `/api/lesson-library/v1` routes, but §6 names only `apps/mobile` | No |
| R3-06 | P3 | `assistance_requests.py:207` builds its own `CollaborationErrorV1` under `/api/be1/v1`. It needs an explicit exclusion | No |
| R3-07 | P3 | The §3.2 item 4 rationale wording is inaccurate: the legacy routers require the inbound header, they do not set it | No |
| R3-08 | P3 | There is no §6 row for the account `Idempotency-Key` follow-up (D-066-69 O-ACCREV, C-A) | No |
| R3-09 | P3 | Four nits: row order; `value_error` mapping undeclared; the Lesson Library slice name; `ACCOUNT_SETUP_UNAVAILABLE` is 403 in source but 409 in §9.8 | No |

## Review-limit check (D-171 item 11)

| Round | P1 + P2 |
|---:|---:|
| 1 | 9 |
| 2 | 2 |
| 3 | 2 |

- P1 + P2 did not fall from round 2 to round 3.
- R3-02 repeats the OpenAPI-mechanism class.
- **Both stop conditions are therefore met.** The coordinator does not start Draft 4 on its own. The owner decides whether to stop or to continue to round 4 (rounds used: 3 of 5).
