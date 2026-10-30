# FEAT-064 B4a — T1 BE1 synthetic eligibility implementation

## Status and authority

- Task: FEAT-064 T1 (B4a), selected current classroom flow only.
- Plan status: `READY_FOR_TASK_APPROVAL`; the plan-level `PLAN.md` remains unchanged.
- Implementation approval must pin this file's exact SHA-256 and all four T0 evidence hashes in `approvals/TASK_APPROVAL.md` before any code edit.
- Task owner / integration owner: Person 2 (`AnhKhoaa157`). BE1 source owner: `CaoDat-2410`, as recorded in D-08. This task approval is not a BE1 co-signature or an `OwnerFenceV1` signature.
- **Precondition:** before the schema or any dependent eligibility guard is implemented, the BE1 owner must confirm the T0 option-X `data_origin` / proof representation and migration dependency in writing. T0 records that confirmation as unresolved. If it is not available, stop before P4 and all dependent guard edits; report the blocker. Do not infer consent from the project owner's approval.

## 1. Goal and bounded flow

Enable one operator-provisioned synthetic Child profile to traverse the existing BE1 flow:

`operator creates synthetic profile + scoped proof → Child joins → Teacher admits → Teacher starts session → Teacher assigns active group → Child receives turn → Child appends a stroke`

The operator creates the profile and proof through a local/test-only command. The existing public registry profile and consent routes remain legal-consent-only. The Child client cannot submit or assert `data_origin`, a synthetic proof, or synthetic eligibility. This task ends at accepted BE1 stroke persistence; it does not export an image or call vision.

## 2. Inputs pinned for this task

| Input | SHA-256 |
|---|---|
| `plan/T0_CONTRACT_FREEZE_EXECUTION_PLAN_20261031.md` | `9C62504CD2AD018B47F7D36B8B64D47016FAE19D3D8C3FADD4C911C98925945E` |
| `evidence/T0_CONTRACT_FREEZE_20261031.md` | `476D48398A6F5A6834D42BE9408BBF445A02200005BDFC59CE8FE4467491041B` |
| `evidence/T0_GUARD_DISPOSITIONS_20261031.csv` | `B02543FF2591BF4EF3B422E08E64865CF407299B6CE3FBBC88C8863BBD268F69` |
| `evidence/T0_METHOD_INVENTORY_20261031.csv` | `F1AA5BF4C54FD24D87FAE5454AE1CE4D8E1191C992AAB17EC671FE5AE0DF6191` |
| `evidence/T0_EXECUTION_MANIFEST_20261031.csv` | `3E5BC377117092D0872C97B922B95C3F464BD1C2F12ADC49D5604FFF83E51605` |
| `plan/PLAN.md` (parent rev6) | `CD7B3236A55E280D4722166C73AF462835DEC8503BCE882CE0CFF9D5601F9665` |
| `DECISIONS.md` | `FD7B9ED0943509B31C07284B2B42EA9FBA26EE203D68BAA09E512D5CD8230644` |

The T0 disposition CSV currently has 17 data rows, although its noted source inventory count says 14. T1 must use the row-level dispositions, not silently normalize that count. `KEEP_LEGAL_GATE` and `OUTSIDE_PILOT_DENY` remain binding.

## 3. Behavioral contract

1. Use a pure domain decision with exactly three outcomes: `LEGAL_CONSENT`, `SYNTHETIC_DEV`, and `DENIED`. The decision carries a versioned basis and a closed reason code; missing, invalid, expired, revoked, mismatched, or unreadable evidence fails closed.
2. Legal eligibility continues to require the existing effective legal-consent record. Synthetic eligibility is granted only from server-managed, current evidence bound to organization, class, Child profile, purpose, run, and expiry/revocation state. Synthetic evidence never creates a consent row, legal consent reference, or `consent_effective=true` value.
3. New profiles classify as `REAL` or `SYNTHETIC_DEV`; pre-existing profiles are classified `LEGACY_UNCLASSIFIED` through the new origin field only. Preserve all existing consent references and other stored values; never rewrite old consent rows or claim old rows are synthetic.
4. Profile consent-reference nullability and database checks must follow the approved T0 representation: `REAL` requires legal references; `SYNTHETIC_DEV` has no legal references and must be backed by a valid separate proof at decision time; `LEGACY_UNCLASSIFIED` is ineligible. Do not put a cross-table proof lookup in a SQL CHECK. The exact migration must be confirmed by BE1 before implementation.
5. The local/test operator issue/revoke command requires an explicit pilot opt-in and is disabled by default. It is not an HTTP route. Refuse issuance outside `local`/`test`; reject client attempts to self-assert synthetic fields.
6. Only T0 `SYNTHETIC_TYPED_ONLY` call sites needed for the bounded path may accept a typed synthetic decision. Keep all existing device key, grant, membership, class/session, Teacher assignment, active group, turn ownership, revision and idempotency checks. Preserve the existing 409 `CONSENT_NOT_EFFECTIVE` response and `denied_consent_pending` audit for legal consent denial.
7. Keep T0 `KEEP_LEGAL_GATE` paths legal-only and `OUTSIDE_PILOT_DENY` paths denied. In particular, do not relax generic records, artifacts, checkpoints/restore, progress/help, BE2, status-read, or video-review paths.

## 4. In-scope paths

Only these paths may be edited or created after approval. Do not reformat unrelated code.

| Path | Operation | Bound |
|---|---|---|
| `backend/src/sketch2life/domain/eligibility.py` | Create | Pure typed decision/evidence contract; no framework or persistence imports. |
| `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | Edit | Profile origin and separate synthetic evidence/revocation persistence; only after BE1 confirmation. |
| `backend/src/sketch2life/infrastructure/persistence/core_store.py` | Edit | Narrow proof/profile persistence methods; required methods are durable and fail closed. |
| `backend/src/sketch2life/infrastructure/config/settings.py` | Edit | Add only the synthetic-pilot opt-in, default `false`; no unrelated configuration changes. |
| `backend/src/sketch2life/interfaces/http/routers/be1_common.py` | Edit | Typed eligibility evaluation boundary; retain `consent_is_effective` as a compatibility wrapper for existing tests/callers. |
| `backend/src/sketch2life/interfaces/http/routers/be1_sessions.py` | Edit | Selected join/admit/Start/group/turn gates only, according to T0 dispositions. |
| `backend/src/sketch2life/interfaces/http/be1_runtime.py` | Edit | Selected accepted-stroke write gate; preserve device/grant/session/group/turn authority. |
| `backend/alembic/versions/20261031_be1_synthetic_eligibility.py` | Create | Migration source only; proposed child of `20261024_0005`; confirm revision graph and no unintended head before writing. Never invoke Alembic or apply it. |
| `tools/synthetic_eligibility.py` | Create | Local/test operator issue/revoke command; explicit pilot opt-in; no public route. |
| `backend/tests/unit/test_synthetic_eligibility.py` | Create | Pure decisions, binding, expiry/revocation and fail-closed cases. |
| `backend/tests/contract/test_be1_synthetic_pilot.py` | Create | Fake/in-memory HTTP contract for positive selected flow and negative identity/consent/client-assertion cases; must not start a database service. |
| `features/FEAT-064-current-flow-modal-vision-dev/evidence/notes/T1_IMPLEMENTATION_REPORT_20261031.md` | Create | Hashes, exact commands/results, guard disposition coverage and blockers. |

`be1_registry.py` and `be1_records.py` are read-only in this task: their legal gates must be covered by regression tests but must not be weakened or refactored. No other path is authorized. If source inspection shows another file must change, stop and ask for a new scoped approval.

## 5. Execution sequence (P0–P9)

| Phase | Work and exit condition |
|---|---|
| P0 — Preflight | Verify branch, T0 commit/artifacts, approval hashes and exact working-tree allowlist. Record SHA-256 for the seven FEAT-063 owner-local files: `docs/context/SOURCE_REGISTER.md`; FEAT-063 `CONTEXT.md`, `status/STATUS.md`, `evidence/notes/DEV_REMOTE_HISTORY_COMPARISON_20261030.md`, `evidence/notes/REMAINING_AI_MODEL_RECOMMENDATIONS_20261030.md`, `evidence/notes/REV36_DELTA_REVIEW_AND_S1_PREPARATION_20261030.md`, `evidence/notes/VIDEO_FLOW_COMPARISON_20261030.md`, `plan/S1_DECISION_CARD_20261030.md`. Stop if status contains any other path; compare the seven hashes after work. |
| P1 — Baseline | With `backend/.venv`, `PYTHONPATH=backend/src`, no `BE1_TEST_DATABASE_URL`, run exactly the five CI files: `tests/contract/test_app_composition.py`, `tests/contract/test_session_http_api.py`, `tests/unit/test_classroom_stage_policy.py`, `tests/unit/test_session_lock_pool.py`, `tests/integration/test_be1_postgres_api.py`; use `--basetemp` outside the repository. Expected reference is about 26 passed and 4 skipped. If actual status differs, stop and diagnose before editing. No database service is started. |
| P2 — Tests first | Add the two approved test files. Demonstrate expected failures for positive synthetic eligibility/flow and negative real, legacy, pending, revoked, expired, wrong-scope and client-self-assertion cases. Do not change old test expectations or monkeypatch points. |
| P3 — Domain decision | Implement typed `EligibilityDecision` and pure fail-closed decision logic. Keep legal consent and synthetic proof as separate bases. |
| P4 — Persistence source | **Only after written BE1 confirmation.** Add the separate proof record, profile origin constraints and migration source under the approved path. Preserve old consent values; classify only the new origin field. Verify the migration graph statically and document revision/parent; do not run Alembic or any DB. |
| P5 — Selected guards | Integrate typed decisions only at the approved `SYNTHETIC_TYPED_ONLY` sites in the selected lifecycle and accepted-stroke write. Preserve all remaining authority checks and existing legal denial shape/audit. Leave `KEEP_LEGAL_GATE` and `OUTSIDE_PILOT_DENY` untouched. Run focused tests after each guard group. |
| P6 — Operator issuance | Implement local/test-only issue/revoke command. Require environment plus explicit `--pilot` and the default-off setting; reject public/client issuance. Tests must prove default-off and refusal in other environments. |
| P7 — Bounded flow contract | Through fakes only, exercise operator-provisioned profile → join → admit → Start → group assignment → turn → append stroke. Assert the accepted stroke is scoped to the correct synthetic proof and all existing authorization/revision/idempotency guards remain active. No render/export or AI call. |
| P8 — Regression and static checks | Re-run the same five baseline files plus both new test files. Run Ruff and `mypy --strict` on changed Python paths. Separate pre-existing type-check issues from regressions; do not edit paths outside §4. Run `python tools/validate_harness.py`, `python tools/validate_repository_security.py`, `python tools/validate_architecture.py`, and `git diff --check`; inspect whitespace in new/untracked files separately. |
| P9 — Evidence | Complete the T1 report with before/after SHA-256 for each edited path, all test/lint/type/validator outputs, guard decisions, migration revision/parent and static-only verification, unmodified legal gates, skipped checks and remaining blockers. Recheck the seven owner-local hashes. No commit or push without a later owner instruction. |

## 6. Acceptance criteria

- AC1: Operator provisioning is disabled by default and cannot be invoked over a public Child HTTP route; only local/test with explicit opt-in can issue or revoke scoped proof.
- AC2: A valid, unexpired, unrevoked server-issued synthetic proof yields typed `SYNTHETIC_DEV` only for the exact org/class/Child/purpose/run scope.
- AC3: `REAL` still requires legal effective consent. `LEGACY_UNCLASSIFIED`, pending/revoked consent, absent/expired/revoked proof, mismatched scope, unknown decision or evaluator error denies.
- AC4: No synthetic consent row/reference is created and no synthetic request maps to `consent_effective=true`.
- AC5: The positive fake-backed flow completes through accepted stroke persistence without bypassing device, grant, membership, class/session, Teacher assignment, active group, turn, revision or idempotency checks.
- AC6: Existing public registry and records legal gates remain unchanged; negative tests retain 409 `CONSENT_NOT_EFFECTIVE` and `denied_consent_pending` behavior where currently specified.
- AC7: The five baseline suites and two new test files have recorded actual results; PostgreSQL integration remains skipped unless its required external DB approval exists. No result is described as a real-DB pass.
- AC8: Ruff, strict mypy, three repository validators and diff/whitespace checks are reported with real outputs. No DB, Alembic, backend service, MinIO, Modal, GPU, provider network, real child data, or secret is used.
- AC9: The T1 report records source hashes and limits; the seven FEAT-063 owner-local file hashes are unchanged from P0.

## 7. Stop conditions and non-goals

Stop without widening scope if the T0 manifest, guard inventory, approval pin, working-tree allowlist or test baseline does not match; if a selected guard lives outside §4; if the BE1 owner has not confirmed the schema/migration contract before P4/P5; if a new migration would create an unintended Alembic head; or if a test requires an actual database/service/network. Report the exact blocker and do not claim completion.

Out of scope: BE2 eligibility changes, `eligibility_basis` in BE2, canvas rendering/export, artifact ingress, status-own API, Teacher panel, worker/UoW/OwnerFence, persistence acceptance against PostgreSQL, live Modal, GPU, image-quality claims, production provider changes, frontend/UI, and any changes to FEAT-063 owner-local files.

## 8. Git boundary

T1 implementation remains uncommitted until the owner requests one task commit. Stage only paths in §4 when that later instruction arrives. Never stage or commit the seven pre-existing FEAT-063 owner-local files. Do not edit any other approval or project source.
