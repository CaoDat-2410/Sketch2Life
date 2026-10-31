# FEAT-063 B5 — Parent Group invitation/accept idempotency-receipt compatibility

- Status: **APPROVED** for the exact scope and allowlist in this plan, by the owner's direct instruction in chat on 2026-11-01. This is independent of the FEAT-064 pilot.
- Baseline before B5: `b111916ef4089b5ca1273de520cbeb9c1d47ae90` (parent `6910b603daac4f7f75bd090467d57f7ed7ea8ec3`).
- Backlog row: B5, preserve compatibility for old idempotency receipts for Parent Group invitations and acceptance. The source-level risk is a stored pre-revision response failing current response-model validation; no database was inspected and no incident is claimed.

## 1. Verified scope from P1

Commit `08459372` added `revision` to the Parent Group membership response contract and to invitation/accept response shapes. The database column already existed. The two affected persisted-response scopes are:

| Operation scope | Route / response model | Before `08459372` | After `08459372` | Current-row lookup for legacy receipt |
|---|---|---|---|---|
| `POST /organizations/{organization_id}/parent-groups/{group_id}/invitations` | `POST /organizations/{organization_id}/parent-groups/{parent_group_id}/invitations` / `ParentGroupInvitationV1` | `contract`, `membership_id`, `parent_group_id`, `state`, `invited_at`, `expires_at`, `accepted_at` | Same fields plus `revision` | By response `membership_id` and `parent_group_id`, joined to group for `organization_id` |
| `POST /me/parent-group-invitations/{membership_id}/accept` | `POST /me/parent-group-invitations/{membership_id}/accept` / `ParentGroupMembershipV1` | `contract`, `membership_id`, `parent_group_id`, `state`, `invited_at`, `expires_at`, `accepted_at` | Same fields plus `revision` | By route/response `membership_id`, `parent_principal_ref` equal to receipt principal, joined to group for receipt `organization_id` |

Other replay scopes with a `revision` field or revision-bearing response model were checked and are unaffected by `08459372`: lesson creation, access-grant creation and decision, lesson-invitation response, and lesson moderation. Parent Group invitation listing and membership revocation can return a revision-bearing model but do not persist command receipts. Parent Group creation and upload-session/source-document operations do not have the affected membership response shape. No other scope is added to B5.

Receipts are found by `(organization_id, principal_ref, operation_scope, idempotency_key)` and protected by the existing request fingerprint. For a legacy Parent Group receipt, the current membership row is needed only when `revision` is absent. A missing, malformed, or mismatched row/response is a typed incompatibility error; it is not a successful replay. The reconstructed revision is the current row revision and can be newer than the revision at the original response time. Whether any live database contains such a receipt remains unknown by design; no database is read.

## 2. Owner decisions

- **OD-B5-1 — APPROVED, option A:** perform a read-time upgrade in `_replay`; do not rewrite the stored receipt.
- **OD-B5-2 — APPROVED:** add optional response field `revision_source`, default `None`, with the closed values `recorded` and `reconstructed_from_current_row`. Do not infer provenance for a current-shape receipt. The revision field remains required.
- **OD-B5-3 — APPROVED:** task owner implements; perform an independent internal read-only review in P5. No other person's signature or confirmation is a prerequisite.
- **OD-B5-4 — APPROVED:** cover exactly the two operation scopes in §1 that gained `revision` in commit `08459372`.
- **OD-B5-5 — APPROVED:** add a PostgreSQL replay test under the existing `BE1_TEST_DATABASE_URL` skip gate; do not configure or access a database in this task.

## 3. Implementation rules

- Add a pure helper in `infrastructure/lesson_library/receipt_compat.py`. It accepts an operation scope, stored JSON response and, only for a legacy Parent Group response, the current membership row. It returns the current response unchanged, an upgraded response, or a typed incompatibility error. It does not import routers, access storage, read the clock, or perform I/O.
- `_replay` invokes the helper before returning. It looks up the current membership only for the two confirmed scopes and only when the stored response lacks `revision`. Scope, organization, membership, group, and principal identity must agree.
- Keep request fingerprint checks and `409 IDEMPOTENCY_KEY_REUSED` unchanged. Replay remains read-only: no receipt rewrite, membership insert/update, audit row, or outbox event. Do not change `_idempotent`'s write path.
- Do not make `revision` optional. Keep `revision_source` absent from newly constructed service dictionaries unless needed; its schema default is `None`. The provenance marker is added only to a reconstructed response.
- Malformed or unreconstructable targeted receipts return a typed `IDEMPOTENCY_RECEIPT_INCOMPATIBLE` error rather than silently succeeding or surfacing an uncontrolled exception.

## 4. Exact allowlist

- `backend/src/sketch2life/infrastructure/lesson_library/service.py`
- `backend/src/sketch2life/contracts/schemas/lesson_library.py` — add only optional `revision_source` to the Parent Group membership response model (inherited by invitation response).
- New: `backend/src/sketch2life/infrastructure/lesson_library/receipt_compat.py`
- New: `backend/tests/unit/test_lesson_library_receipt_compatibility.py`
- `backend/tests/integration/lesson_library/test_lesson_library_api.py` — add a PostgreSQL replay test, skipped by the existing `BE1_TEST_DATABASE_URL` fixture when unset.
- New: `features/FEAT-063-system-architecture-rearchitecture/evidence/B5_RECEIPT_COMPATIBILITY_REPORT_20261101.md`
- `features/FEAT-063-system-architecture-rearchitecture/plan/B5_PARENT_GROUP_RECEIPT_COMPATIBILITY_PLAN_20261031.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` — append only the B5 approval entry.

## 5. Acceptance and verification

1. Capture the P0 baseline before editing: the five fixed CI files plus existing offline Lesson Library tests, and strict mypy on the service and contract. P0 measured **273 passed, 4 skipped** for the selected pytest set and **30 pre-existing mypy errors** across those two files; compare final results and report only new mypy errors.
2. Add offline synthetic tests before implementation and run them on the baseline; they must fail before code changes. Cover: current-shape receipt unchanged with no inferred provenance; legacy invite/accept receipt upgraded from the current row with explicit provenance and no writes; missing current row typed failure; fingerprint conflict remains 409; malformed response typed failure; foreign organization/principal cannot see a receipt; upgraded response validates against the current model.
3. Add a PostgreSQL acceptance case that inserts a legacy receipt and retries it (same key succeeds without another effect; different payload with the same key returns 409). It remains skipped unless the existing test fixture receives an approved disposable database URL. Do not run it in this task.
4. Run the new offline tests, the five fixed CI files and all existing offline Lesson Library tests. Run Ruff with `--config backend/pyproject.toml`, `ruff format --check` only on newly created files, strict mypy on edited/created Python files, all three repository validators, `git diff --check`, and byte checks on new files.
5. Internal independent review checks the exact allowlist, unchanged fingerprint/409 behavior, no replay writes, coverage of both P1 scopes, provenance handling and required contract revision. Record method and findings in the evidence report.
6. Before commit, recheck the seven owner-local hashes and run `python tools/validate_repository_security.py` immediately before staging/commit. Stage only the allowlist paths in §4. Commit according to the verified Case X or Y in the owner's prompt. Do not push.

## 6. Commit case

P0 found Case X: HEAD is the single unpushed commit after `6910b603`, its subject begins `feat(feat063,feat064):`, and the remote comparison is `0 1`. The owner-authorized action is one `git commit --amend`, preserving the author and adding B5 to the subject/body. If the commit state changes before P6, follow §B.3 of the owner's prompt; do not create a different commit for an unlisted case.

## 7. Not in B5

No database or Alembic operation, receipt data migration, Modal/GPU/network operation, real family data, route/grant/upload change, `_idempotent` write-path change, FEAT-064 pilot change, push, or edits outside §4. The database presence of legacy receipts is unknown; the PostgreSQL replay test is intentionally NOT RUN.
