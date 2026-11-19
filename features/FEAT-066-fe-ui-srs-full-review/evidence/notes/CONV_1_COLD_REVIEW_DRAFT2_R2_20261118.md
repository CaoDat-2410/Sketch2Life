# CONV-1 Draft 2 — cold review record (round 2, 2026-11-18)

- **Artifact:** `plan/PLAN_CONV1_BE_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT2_20261118.md`, 27,355 B, SHA-256 `7338792B82D0CB3C9E42B2E7107DB6B8DD56346A5EBB47EDDB5FC97AC1B0EF03`.
- **Reviewer:** a fresh subagent, not the round-1 reviewer, started by the coordinator session. Model Sonnet 5.5 (`claude-sonnet-5-5`), reasoning effort high, both set explicitly. It was read-only: no repository edits, tests, validators, database or network.
- **Pin check:** PASS. It covered the package, the round-1 record (5,470 B, `801D0246…`) and the conventions contract (13,999 B, `1F41B74A…`).
- **Verdict:** **NOT READY**. P1 = 1, P2 = 1, P3 = 13. P1 + P2 fell from 9 in round 1 to 2.
- **Round-1 status:**
  - Fixed: F3, F5 to F16 (F9 in design).
  - Partly fixed: F1 (see N1), F2 (see N2), F4 (see N5).

## New findings

| ID | Sev | Finding (short) | Planned fix |
|---|---|---|---|
| N1 | P1 | `routers/be1_registry.py` (not allowlisted) checks existence before the guard, with a uniform 403 `SCOPE_DENIED` (lines 57–58, 136–142, 421–430). Its wrapper `_require_m2_assignment` (lines 61–83) rewrites the guard's refusals to that 403. After CONV-1, a missing class (403) and an existing but unassigned class (404) become distinguishable on two mutating routes. This is the same class of issue as round-1 F1 | Allowlist `be1_registry.py`, limited to `_scope_denied`, `_require_m2_assignment` and the two pre-guard lookups. Missing gives 404. Add a same-body test for both routes. Audit the other in-scope routers for non-404 pre-guard raises |
| N2 | P2 | For non-BE1 families, `published_responses` returns catalog rows unchanged (`openapi_contract_amendments.py:1279–1288`). `_apply_catalog_metadata` (`app.py:250–340`) keeps FastAPI's automatic 422 for non-BE1 paths. The restore-checkpoint constants carry old codes | State the non-BE1 mechanism and cite `app.py:250–340`. Name the constants in allowlist row 8 |
| N3 | P3 | Platform Admin, auth and Teacher AI send dict details with codes, not strings. `teacher_ai` drops its own `request_id`. There is no default for 405 or 410. The fate of the 404 codes `JOIN_UNAVAILABLE` and `CANVAS_SOURCE_UNAVAILABLE` is unstated | Correct the sentence. Add a generic fallback. Keep `JOIN_UNAVAILABLE` |
| N4 | P3 | Other 403 guards are not named as kept (device guards, `TEACHER_ORGANIZATION_ACCESS_REQUIRED`, the Lesson Library platform-admin and parent guards). Issuer mismatch → 404 goes beyond CV-5 | List them as kept. Note the issuer choice in §8 |
| N5 | P3 | The 422 list is incomplete (`CANVAS_PROFILE_INVALID`, the dynamic `CoreRuleViolation` codes, `ORGANIZATION_UNAVAILABLE`, `ORGANIZATION_REQUIRED`, the dynamic `exc.code`). The §6 slice mapping is wrong for the BE1 and Platform Admin codes | Complete the list. Fix the mapping. Note that C-D3 is only partly applied under CV-2 = A |
| N6 | P3 | Mobile `firebaseAuthSession.ts:185,232` calls `/api/auth/v1`, which is in scope | Correct the mobile line and add a follow-up check |
| N7 | P3 | The validation error-type map is unspecified, and the `Idempotency-Key` codes conflict with item 2e. The handler's acceptance of `field_errors` from the detail is unspecified | Add the type table. Every non-missing key issue becomes `INVALID_FORMAT`. Whitelist `field_errors` from the detail |
| N8 | P3 | The coverage scan cannot see dynamic codes, and the module list is not named | Name the modules. Dynamic codes use the status fallback |
| N9 | P3 | The CV-1 guard is weak. AC7 conflicts with the header rule | Add a through-app assertion that `/api/parent/v1/ai` bodies are unchanged. Reword AC7 |
| N10 | P3 | The middleware overwrites `X-Request-ID` that legacy routers set themselves. Some legacy and Parent tests are unguarded | Keep an existing header. Add those tests as regression guards |
| N11 | P3 | The 413 `else` branch is shared with `/api/dev/v1/storage-examples` | Condition the change on the Lesson Library prefix. State the dev exception in AC5 |
| N12 | P3 | `STATUS.md` and the evidence note are not in the allowlist | Add a governance-docs line |
| N13 | P3 | Declared-name collection needs a cycle guard and alias handling | One sentence each |
| N14 | P3 | The decision row should record CV-1 as a scoped deferral of C-D1 "every route" | Note it in §1 |

## Review-limit note (D-171 item 11)

- P1 + P2 fell (9 → 2), so the "not falling" stop condition is not met.
- N1 is the same class as round-1 F1: an existence disclosure through the 404/403 split, found in a different file. The repeat-class stop condition can therefore be read as met.
- The coordinator does not continue to Draft 3 on its own. The owner decides whether to stop, or to continue with Draft 3 and round 3, before any further round.
