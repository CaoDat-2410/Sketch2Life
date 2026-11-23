# V3 T-7a plan, Draft 1: C-M1 School Manager roster summary (counts and opaque refs only)

Date 2026-11-19. Goal v3b. Branch `feature/backend-srs-api-v3`, facts verified at HEAD 2cd0d9be; T0.5, T0.11, T-2z, T-2a and T-3x are assumed landed first (T0.11 matters, see §2). Status: plan, not implemented, not reviewed.
**Superseded in two places by the implementation (evidence note `evidence/notes/V3_T_7A_EVIDENCE_20261119.md` §2, T-7a-DEC-2 and T-7a-DEC-3, is authoritative):** the cursor query maximum length is 1024, not 512; and A09 and A10 call `require_assignment` without a `roles` argument and decide the audience after `get_class` (so A10 does not keep `roles={"school_admin","teacher"}`). The text below is left as written at Draft 1.
Source: BE API plan Draft 5 WP-7, §2.3 C-M1 row, rows P-14a, P-26b, P-37; OD-05 (accepted, option b); the approved package `plan/PLAN_CM_SCHOOL_MANAGER_SLICE_PACKAGE_DRAFT4_20261118.md` (read in full; its C-M1 BE part is copied below, so this plan is complete without it); D-066-69 (BE) O-PRIV; D-066-75 (BE) CM-1 to CM-12; T0.11 review R1 P2-1 (session roster).
The package branch `feature/feat066-cm1` does not exist (`git branch -a`): this is a normal task on `feature/backend-srs-api-v3`, covered by the goal program approval; CM-9 and R-14 are moot.
**Owner scope rule:** no capacity, subscription, quota, billing or payment code and no `CLASS_CAPACITY_REACHED`. Class create, B01/G01 (C-M4) and UC-12 (C-M5) are untouched.

## 1. Task

School Manager reads class and consent data without child content, and a class-scoped Teacher keeps today's reads. SRS basis: l.796 (the `/v1/organizations/{org}/classes` family covers class list and roster), l.1640 (cursor lists: default 25, maximum 100, explicit deterministic order), l.2586 (Profile row: Manager "no profile contents by default"; Teacher only granted fields of an assigned class), l.863-865 (403 only inside a known scope). AC-64 (l.2733) covers child media only and is not cited for profile fields.

Not in T-7a: A09 paging (T-7e, OD-17), consent model and writes (X-19, X-16), the archived/suspended filter (T-7b, P-14b), profile create (T-7c), and the D-066-75 debt list (canvas, artifacts, gallery, observations, portfolio, session `configuration`, `teacher_note`, group `display_name`, pilot assistance list, consent-write echoes).

## 2. HEAD against the package (line numbers in `routers/be1_registry.py` unless named)

| Row | HEAD (before T-7a) | Package target (copied) |
|---|---|---|
| A07 `GET /api/be1/v1/organizations/{organization_id}/classes` (l.437) | no `limit` or `cursor`; `state == "active"` filter; order `created_at`; items `class_id, display_name, state, assignment_revision, has_active_teacher` (M9-B); a row with `class_id` NULL (org-wide) sees every class | paged: `limit` 1-100 default 25 (`limit_query()`), `cursor`, order (`created_at`, `class_id`) ascending, response adds `next_cursor`; items unchanged |
| A09 `GET …/classes/{class_id}/profiles` (l.598) | after T0.11: roles `{"teacher","guide","observer"}`, Manager gets 403; any such row passes, including org-wide `teacher`, `guide`, `observer`; returns `child_id, class_id, display_name, age_months`; 409 `CONSENT_NOT_EFFECTIVE` plus an audit row when any active profile lacks effective consent. `consent_is_effective` looks for state `effective`, the store allows only `pending` and `revoked` (`be1_models.py:272`), so a non-empty class always answers 409 | School Manager: 200 `Be1ClassRosterSummaryV1`, no gate, no audit row (CM-3, CM-5). Teacher: full list only for an active `teacher` row whose `class_id` equals the class (CM-11); other rows 403. Not paged |
| A10 `GET …/classes/{class_id}/consents` (l.875) | roles `{"school_admin","teacher"}` (guide and observer already 403); unpaged; `recorded_at` desc; items `consent_id, child_id, purpose_ref, state, effective` (`effective` always false) | paged (`recorded_at` desc, `consent_id` desc); Manager gets `Be1ConsentListManagerV1` without `child_id` and `purpose_ref` (CM-4); Teacher items only for a class-scoped `teacher` row (CM-11) |
| Session roster `GET …/sessions/{session_id}/roster` (`be1_sessions.py:299`) | roles `{"school_admin","teacher"}`; returns `child_id`, `display_name`, `device_grant_id`, group names, turns to the Manager. T0.11 left it open (review P2-1) | `school_admin` 403 `ACTION_NOT_ALLOWED` (CM-2); Teacher unchanged |
| Pilot profiles (l.653) | T0.11 already sets roles `{"teacher"}` | no code change; keep the Manager-403 test |

Shared facts: `require_assignment` (`be1_common.py:88-156`) filters rows by account role (`school_manager` keeps `school_admin` rows; `teacher` keeps `teacher`, `guide`, `observer`) and gives the uniform 404 out of scope. `limit_query()` and `_invalid()` exist in `api_conventions.py`; there is **no shared cursor helper** (precedents `_encode_candidate_cursor` l.169 and `_encode_history_cursor` in `parent_story_runs.py:244` stay untouched). Assignment-API Teacher rows are class-scoped; org-wide `teacher` rows mark organization membership, which is why CM-11 matters.

## 3. Shapes (exact)

**Cursor helper**, new in `interfaces/http/api_conventions.py`:
- `encode_cursor(*, scope: str, sort_key: str, item_id: str) -> str`: JSON `{"i": item_id, "k": sort_key, "s": scope, "v": 1}`, `sort_keys=True`, compact separators, base64url without padding.
- `decode_cursor(cursor: str, *, scope: str) -> tuple[str, str]` and `decode_time_cursor(cursor, *, scope) -> tuple[datetime, str]` (parses `k` with `datetime.fromisoformat`, requires a timezone). Rules: ASCII, strict base64 (`validate=True`), a dict with exactly the keys `i, k, s, v`, `type(v) is int` and `v == 1`, `s == scope`, `1 <= len(i) <= 128`. Any failure raises `_invalid("cursor", "INVALID_FORMAT")` (400 `INVALID_REQUEST`, `field_errors` `[{"field":"cursor","code":"INVALID_FORMAT"}]`). The cursor is opaque, not signed; the scope binding only stops replay across routes, and the scope check still gates every page.
- Scopes: `be1.classes:{organization_id}` and `be1.consents:{organization_id}:{class_id}`. Query parameter `cursor: str | None = Query(default=None, min_length=1, max_length=512)`.
- Keyset: A07 `tuple_(created_at, class_id) > (k, i)`; A10 `tuple_(recorded_at, consent_id) < (k, i)`. Fetch `limit + 1`, `next_cursor` is built from the last returned row when a further row exists, else `null`. The key is always present.

**A07 body:** `{"contract":"Be1ClassListV1","items":[…as today…],"next_cursor": str|null}`. The Teacher scope filter (`allowed_class_ids` or org-wide) runs before paging. `limit=101` or `limit=0` gives 400.

**A09 Manager body** (`Be1ClassRosterSummaryV1`): `{"contract":"Be1ClassRosterSummaryV1","class_id":"<class_id>","active_profile_count":<int>}`. Count = rows of `ManagedProfileModel` for the organization and class with `state == "active"`, regardless of consent. No name, age, age band or `child_id`; no audit row, no consent lookup.
**A09 Teacher body:** `Be1ManagedProfileListV1` exactly as today (gate, 409, audit row unchanged); no `next_cursor`.

**A10 Manager body** (`Be1ConsentListManagerV1`): `{"contract":"Be1ConsentListManagerV1","items":[{"consent_id","state","effective"}],"next_cursor": str|null}`; `effective` stays `false`.
**A10 Teacher body:** `Be1ConsentListV1` with today's items plus `next_cursor`.

Optional Pydantic models for the two new bodies may go in `contracts/schemas/be1_runtime.py` (handlers return dicts today).

## 4. Handler design

```
list_profiles:
  rows = require_assignment(db, principal, org, class_id=class_id)   # no roles; 404 out of scope
  get_class(db, org, class_id)                                       # 404 before any 403
  if any(r.role == "school_admin" for r in rows): return summary     # Manager account only has these
  if not any(r.role == "teacher" and r.class_id == class_id for r in rows):
      raise failure(403, "ACTION_NOT_ALLOWED", ...)                  # org-wide teacher, guide, observer
  ...existing gate and list unchanged...
list_consents: same prefix with roles={"school_admin","teacher"}; Manager -> manager page;
  Teacher without a class-scoped teacher row -> 403; Teacher -> teacher page.
read_session_roster (be1_sessions.py): roles={"school_admin","teacher"} -> roles={"teacher"}.
```
403 (not 404) for the refused rows: the caller is assigned in the organization and the class exists (SRS l.864, CM-11). T0.11's interim `roles` argument on `list_profiles` is removed by this task (the Manager now gets the summary); the pilot-profiles change of T0.11 stays.

**OpenAPI:** the catalog derives one response schema per operation from one example (`add_response_examples`, `openapi_contract_amendments.py:1270`). Add a mapping `ALTERNATE_RESPONSE_EXAMPLES` and let that function publish `{"oneOf":[primary, alternate…]}`, with each variant's `contract` an `enum` of its own name and one named example each, for A09 and A10. Add `limit` and `cursor` to the catalog `request_inputs` of A07 and A10 (follow the lesson-library list rows) and the 400 cursor row; no new route, so `DECLARED_OPERATION_COUNT` is unchanged. Frozen FEAT-063 and FEAT-047 snapshots stay unchanged; the evidence note records the drift.

## 5. Tests

Existing tests that change:
- T0.11's class-profiles Manager-403 tests (unit file `test_be1_scope_guard_404_403.py`; the Manager case T0.11 adds in `test_be1_synthetic_pilot_postgres.py`) become Manager 200 summary; its pilot-profiles Manager-403 test stays.
- `tests/integration/test_be1_postgres_api.py::test_pending_consent_stays_pending_and_blocks_profile_admission_and_canvas` (l.731; fails at base: the Manager `POST` profile gets 403). Repair: create the profile and read A09 as the class-scoped Teacher the test already creates (swap `app.dependency_overrides[get_verified_adult]` for those calls); keep the 409 `CONSENT_NOT_EFFECTIVE`, admission 409, `start` 409, device-canvas 401, stored consent and enrollment rows, audit and outbox assertions; add a Manager A09 call asserting the summary.
- `tests/contract/test_openapi_contract_catalog.py` (hot): paging parameters on A07 and A10 (default 25, min 1, max 100, `cursor`), `oneOf` variants for A09 and A10, 400 row.
- No existing test covers the session roster, A07 paging or Manager A10.

New unit (no database): `tests/unit/test_api_conventions_cursor.py` (round trip; wrong scope; bad base64; extra or missing key; `v` as bool or 2; naive datetime; oversize id; all give the 400 shape) and `tests/unit/test_be1_roster_privacy_guards.py` (fake session of `test_be1_scope_guard_404_403.py`): A09 and A10 for Manager, class-scoped Teacher, org-wide Teacher, guide, observer, out-of-scope; 404 before 403 for a missing class; summary carries exactly the three keys.

New PostgreSQL (`tests/integration/test_t7a_roster_privacy_postgres.py`, fresh database whose name contains `be1_acceptance`, harness pattern of `test_m2_s1a_teacher_postgres.py:183-230`: manager, org-wide teacher, class-scoped teacher, foreign teacher):
- Manager A09: 200 summary with the right count (two profiles, one inactive), body has no `display_name`, `age_months`, `child_id`; no audit row written.
- Class-scoped Teacher A09: 200 on an empty class, 409 `CONSENT_NOT_EFFECTIVE` with its audit row on a non-empty class (the gate cannot pass today).
- Org-wide Teacher, guide, observer on A09 and A10: 403; foreign-organization Teacher and unknown class: 404 with the same body.
- Manager A10: manager contract, items without `child_id` and `purpose_ref`; class-scoped Teacher A10: current items.
- A07 paging: three classes, `limit=1`, walk to the end in (`created_at`, `class_id`) order; a class inserted between pages neither duplicates nor skips; `limit=101` gives 400; a cursor from another organization or from the consents route gives 400; default page is 25 (create 26).
- A10 paging: newest first; stable for two rows of equal `recorded_at`.
- Session roster: Manager 403, class-scoped Teacher 200, foreign 404; response for the Teacher unchanged.

Then: unit and contract against the 83-id base list (the repaired consent test leaves the known-failing set), PostgreSQL run on the fresh database, ruff and mypy on touched files, the validators, `git diff --check`.

## 6. Allowlist and hot files

Edit (source paths under `backend/src/sketch2life/interfaces/http/` unless noted): `api_conventions.py`; `routers/be1_registry.py` (**hot**: A07, A09, A10, removal of T0.11's `roles` line); `routers/be1_sessions.py` (one `roles` argument); `openapi_contract.py` and `openapi_contract_amendments.py` (**hot**); `sketch2life/contracts/schemas/be1_runtime.py` (optional); tests under `backend/tests/`: `contract/test_openapi_contract_catalog.py` (**hot**), `unit/test_be1_scope_guard_404_403.py`, `integration/test_be1_postgres_api.py`, `integration/test_be1_synthetic_pilot_postgres.py` (T0.11's Manager class-roster case only) and the three new files of §5; evidence note `features/FEAT-066-fe-ui-srs-full-review/evidence/notes/V3_T_7A_EVIDENCE_20261119.md`.
**Not touched:** `be1_models.py` (hot; no DDL and no new index (the paged queries filter on organization and class and use the existing `ix_be1_class_org_state` and primary keys; a performance index would be a separate DDL task)), `be1_common.py`, `app.py`, `error_envelope.py`, DECISIONS and approval files, web, mobile, Bruno, any billing or capacity file.
Sequencing: after T0.9 (shared catalog files), before T-7b (same A07 handler; if T-7a is skipped T-7b must page too) and T-7c.

## 7. FE impact (not done; web `.worktrees/ui` at 8a112b01; mobile has no caller)

- `classService.ts`, `managerBusinessService.ts`, `ClassesPage.tsx`, the `RosterConsentPage.tsx` class picker: `next_cursor` and "load more"; Manager roster reads `Be1ClassRosterSummaryV1` and shows the count only; the consent table reads `Be1ConsentListManagerV1` (no purpose column); labels `pending`, `revoked` (CM-6).
- `shared/api/backendApi.tsx`, `T05ClassesScreen.tsx`, `TeacherWorkbenchPage.tsx`: follow `next_cursor` to the end for classes and consents (they join consents to profiles and look a class up by id).
- Window (CM-8, local development only): between the BE and FE commits Teacher screens see only the first 25 classes and consents, and `RosterConsentPage` breaks on the summary body (it already shows the refusal line after T0.11).
- Bruno 012 and the roster and pilot-profiles variants belong to the Bruno tasks (decisions 86-89); they must expect the summary and the 403s.

## 8. Rollback and risks

Rollback: revert the single local commit; no data, DDL or flag. `next_cursor` is additive; visible changes are the Manager bodies (A09, A10) and the new 403s. Risks: R-17 and the BE-before-FE window; `oneOf` publication touches the shared catalog builder (mitigation: a unit test of the published schema of the two operations).

## 9. Deviations from the package and BLOCKED_OPEN questions

Deviations: (a) base moved from `2dddc607` to HEAD (line numbers differ); (b) CM-9 branch policy replaced by the program approval; (c) T0.11 already did CM-2 for pilot-profiles and an interim class-roster 403; (d) the session-roster 403 is closed here (T0.11 review P2-1).
Open, none blocks the build:
- Q-1 (owner via coordinator): A07 for a Teacher with an **org-wide** `teacher` row lists every class (`org_wide` in `list_classes`); P-14b says the Teacher should see only assigned classes. CM-11 covers A09 and A10 only. Plan: leave unchanged here and let T-7b decide; confirm.
- Q-2: CM-11 is not applied to the session roster and pilot-profiles; an org-wide Teacher row still passes there (CM-2 decides the Manager only). Plan: record as residual in the evidence note; extend only on an owner word.
- Q-3: consent writes still echo `child_id` and `purpose_ref` to a Manager (MGR-5, X-16 debt); unchanged.
- Q-4: guide and observer lose A09 (CM-11, a stated behaviour change); no web caller per the package reviews and no mobile caller found in `apps/ui-mobile/src` and `apps/mobile/src`.
