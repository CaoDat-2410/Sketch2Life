# Q Run 3 — PostgreSQL check, BE1→BE2 adapter, T3 plan

Date: 2026-10-31 (Asia/Saigon). Baseline commit: `d7adeec2c23c867edc599c63d8af46cea150bbc3` on `feature/feat063-be-foundation`.

## Q0–Q6 disposition

| Phase | Result | Evidence / reason |
|---|---|---|
| Q0 — preflight | DONE | Branch and HEAD matched the required baseline; no merge/rebase/cherry-pick; initial index was empty and only the three known owner-local tracked edits were present. Seven protected local hashes matched. `BE1_TEST_DATABASE_URL_SET=False`. Baseline selected suite: 288 passed, 20 skipped, 6 warnings. Baseline strict mypy on six BE2 domain/port/service files: success, no issues. |
| Q1 — T12-lite PostgreSQL | NOT RUN | Required `BE1_TEST_DATABASE_URL` was not set. No URL was read, no connection or Alembic operation was attempted, and no test database was touched. |
| Q2 — offline BE1→BE2 adapter | PARTIAL / code NOT DONE | Created the field inventory and T2B plan, then stopped before code under the plan’s stop rule. BE1 has no authoritative age provenance/revision, consent revision, coherent context revision, complete CanvasFacts policy source, or GroupRoster revision. Synthetic profiles have no consent reference by design, while `MemberFact` requires consent ref/revision. Filling sentinels or borrowing unrelated timestamps/session revisions would invent semantics. No reader or tests were created. |
| Q3 — T3 and UI blockers | DONE — DRAFT only | Created `plan/T3_STROKE_PROFILE_AND_UI_BLOCKERS_PLAN_DRAFT1_20261101.md`. It records the fixed white/strokes-only profile, current payload/geometry gaps, and the current reconnect and Teacher profile-list blockers with options and owner questions. No implementation approval is recorded. |
| Q4 — B4b | DEFERRED BY OWNER | No B4b work performed. |
| Q5 — verification | DONE | The isolated migration graph test passed. The selected regression suite passed at the same count as Q0. Validators and diff check are reported below. No Python source changed, so Ruff and Q5 strict mypy were not run; baseline mypy was successful. |
| Q6 — commit | ONE NEW COMMIT AUTHORIZED; no amend or push | The first Q6 attempt stopped after the index lock could not be created and a later snapshot showed an unresolved FEAT-063 approval conflict. After the owner reported the conflict resolved, the live workspace advanced beyond the stated `555a0732` checkpoint: at resume it was on `feature/feat063-be-foundation`, HEAD `57b3a9c3daaf8e0e6ff161c09d6f617dd5db550d`, with an empty index and no merge/rebase/cherry-pick state. The four protected ignored-file hashes matched. Per the owner's direct instruction to stop only for protected-hash drift or an out-of-scope edit, this report and the T2B plan, T3 draft plan, and FEAT-064 `TASK_APPROVAL.md` are prepared for one new commit on the actual current HEAD. The commit hash is recorded in the completion message, not embedded in this report. No push is authorized. |

## Q2 BE1→BE2 field map summary

| BE2 target | Available BE1 source | Missing / disposition |
|---|---|---|
| `MemberFact.participant_id`, age months | Exact session membership and active managed profile | Age provenance reference and age revision are absent. |
| `MemberFact` consent fields | REAL profile consent refs and consent row; current legal predicate | Consent revision is absent; synthetic profile correctly has no consent ref. The DB CHECK only allows pending/revoked while the legal predicate looks for effective. |
| Typed eligibility basis/version/evidence/scope | Profile origin, synthetic proof, exact session/run/purpose, current setting and `evaluate_eligibility` | Potentially mappable for synthetic only if all fields revalidate; no consent booleans may be forged. |
| `ContextDecision` ages/session | Membership, profiles, session row | No revision fencing the complete profile/consent/proof/membership context; optional topic/age-policy values have no trusted catalog source. |
| `CanvasFacts` | Turn, aggregate revision, accepted operations/checkpoints | No persisted canvas mode/region/age-policy contract or region-policy revision. |
| `GroupRoster` | Group and admitted membership rows | No roster revision. |
| Current turn | Active `ChildTurnModel` | Query must be exact-scope and fail closed if absent/ambiguous. |

Full path-by-path mapping and proposed future reader/test scope are in `plan/T2B_BE1_TO_BE2_FACT_ADAPTER_PLAN_IMPL_20261101.md`.

## Q3 plan summary

- **Stroke profile:** finite normalized coordinates, five existing colors, server-side rejection outside a versioned profile, append-only accepted operations, white strokes-only fixed-aspect canvas. Exact aspect/width mapping, profile binding and one-point behavior remain to be frozen in a separate implementation approval; T0’s 1:1 / 1024 proposal is not treated as a decision.
- **Child blocker:** `/reconnect` uses the write-oriented device dependency and then the legal-only `_require_group_consent`; T1’s typed synthetic helper is limited to append. Decide whether to add a read-only scoped reconnect path, keep the current path and explicitly limit pilot behavior, or add a separate pilot reconnect route.
- **Teacher blocker:** the lobby calls class `list_profiles`; that route returns 409 if any profile fails legal effective-consent lookup, including synthetic profiles. The existing session roster only covers admitted members and is not a lobby candidate list. Decide whether to add a session-bound pilot projection, alter the class endpoint with typed scope, or use an operator-seeded bounded pilot path.
- **AC20:** reuse existing styles/components; synthetic screenshots are evidence, not visual approval. Any new asset still follows the repository visual approval process.

## Verification results

- P1 isolated migration graph check: one test passed (exit code 0).
- Q0 selected regression baseline: `288 passed, 20 skipped, 6 warnings`.
- Q5 selected regression run before resume: `288 passed, 20 skipped, 6 warnings` in 21.49 seconds.
- Resume regression run (five CI files plus T1, synthetic status, BE2 basis, B5 receipt, Lesson Library and migration tests): `288 passed, 20 skipped, 6 warnings` in 27.86 seconds. PostgreSQL-backed cases skipped because `BE1_TEST_DATABASE_URL` was unset; no database connection was attempted.
- Separate `tests/contract/test_live_image_demo_api.py`: `31 failed, 1 passed` in 8.82 seconds. The observed common startup failure is `create_app()` constructing `Boto3S3CompatibleObjectStorage`; boto3 has no configured credentials and tries `http://169.254.169.254/latest/api/token`, which this offline contract test's socket guard rejects. `app.py` and this test file were not edited in this task; the failure is recorded as present in the post-Swagger working baseline, not attributed to these documentation changes.
- `python tools/validate_harness.py`: `HARNESS_VALID`.
- `python tools/validate_repository_security.py`: `REPOSITORY_SECURITY_VALID` (`publishable_files_scanned=5958`; environment/credentials excluded; absolute machine paths absent).
- `python tools/validate_architecture.py`: `ARCHITECTURE_VALID`.
- `git diff --check`: exit code 0, no output.
- Ruff check/format: NOT RUN; no Python file was created or modified in this run.
- Q5 strict mypy: NOT RUN; no Python file was created or modified. Q0 baseline strict mypy on six existing BE2 source files succeeded with no issues.
- PostgreSQL, Alembic apply, MinIO, Modal, GPU and provider call: NOT RUN.

## Current output paths

- `plan/T2B_BE1_TO_BE2_FACT_ADAPTER_PLAN_IMPL_20261101.md` — SHA-256 `5830B2E1712615DB10C7775C71A59F13B2B71E013BCBB1BD0EBA1F351CC128AB`.
- `plan/T3_STROKE_PROFILE_AND_UI_BLOCKERS_PLAN_DRAFT1_20261101.md` — SHA-256 `8BD963281672AB97599E2B26CBA500AB629C5F3BAF076ED48B1735E1FEFA1F70`.
- `approvals/TASK_APPROVAL.md` — SHA-256 before adding this report: `1CC6D1EDA8119B688024E5B8E90F60C139A3E0D36F0257A83CBE63BE3FDCFD5F`.
- This report’s own SHA-256 is given in the final chat response to avoid a self-referential hash.

The four protected ignored-file hashes are rechecked at Q5/Q6 and reported in the final chat response. Other working-tree changes outside this task's allowlist are left untouched and unstaged.
