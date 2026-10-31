# T12-lite PostgreSQL report — 2026-11-01

## Scope and limits

- Disposable local PostgreSQL acceptance database only; no external host, Modal, GPU, or real child data.
- The owner-provided ignored connection file was read into this process only. No connection URL or credential is recorded here.
- This report records the observed local integration run. It does not claim production readiness or provider quality.
- The only test file added for T12 is `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`.

## Database safety and migrations

| Check | Result | Evidence |
| --- | --- | --- |
| Connection file exists and is readable | Met | Read into the process environment; its contents were not printed or copied. |
| Database name contains `be1_acceptance` | Met | Parsed target matched the required substring. |
| Host and query overrides are loopback only | Met | Host was loopback; no non-loopback `host` or `hostaddr` override. |
| Connection reaches the approved database | Met | Connected to PostgreSQL 17.11 on the local loopback interface; actual database name matched the parsed name. |
| Database schema/data are within the disposable test scope | Met | Before migration, the database had no user tables. Repository migrations created the application schemas; before downgrade, all application tables were empty and synthetic profile/proof counts were zero. |

R2 applied all 10 Alembic heads using `upgrade heads`; `current` matched `heads`:

`20261015_ai_0001`, `20261017_lc_0001`, `20261018_ap_0009`, `20261018_kv_0001`, `20261018_vr_0001`, `20261019_ae_0001`, `20261019_pa_0001`, `20261019_vf_0001`, `20261028_ll_0001`, `20261031_be1_se_0001`.

After tests and exact cleanup of their rows, the `be1_core@-1` downgrade and `be1_core@head` upgrade both exited successfully. `current` and `heads` again showed the same 10 revisions. The post-upgrade check found zero synthetic proofs and zero invalid `data_origin` rows.

## Test results

| Phase / file | Result | Notes |
| --- | --- | --- |
| R0 offline baseline, 18 files | 388 passed, 4 skipped | Ran before setting database variables. |
| `tests/integration/test_be1_postgres_api.py` | 3 passed, 1 failed | `test_room_code_start_revocation_stage_and_early_outcome_are_durable` expected canvas append HTTP 200 but received 409 `CONSENT_NOT_EFFECTIVE`. Its fixture creates a pending real-consent profile and patches the session router's consent helper; the canvas router still evaluates its own guard. No source or existing test was changed. 118 rows created in this run were removed by exact primary-key comparison; pre-existing rows were preserved. |
| `tests/integration/lesson_library/test_lesson_library_api.py` | 5 passed, 1 failed | `test_teacher_uploads_and_reviews_a_synthetic_pdf_through_http` received 503 `DEPENDENCY_UNAVAILABLE` because the configured ClamAV scan dependency was unavailable. No source or existing test was changed. 126 rows created in this run were removed by exact primary-key comparison; pre-existing rows were preserved. |
| B5 replay test, isolated PostgreSQL rerun | 1 passed | `test_parent_group_accept_replays_legacy_receipt_without_repeating_effects`. This fixture does not tear down its rows. Since the database was empty immediately before the isolated run, I verified the only organization was the synthetic Lesson Library fixture, checked the related rows belonged to it, and deleted those exact rows by organization/group/principal keys. No table was dropped or truncated. All application tables were empty afterward. |
| `test_be1_synthetic_pilot_postgres.py` | 4 passed | Full synthetic profile/proof → join → teacher admission → start → group assignment → turn → accepted canvas stroke succeeded. The six negative admission cases returned 409 `CONSENT_NOT_EFFECTIVE`; no consent row was created and the synthetic profile retained `consent_id = NULL`. PostgreSQL checks rejected invalid profile origin and `effective` consent state. The status guard allowed `active` and `paused` without a turn and denied `lobby` and `finished`. Fixture cleanup left all application tables empty. |
| Final offline regression, 13 files | 280 passed, 24 skipped | Included the five CI files, T1, migration, status-guard, BE2-basis, Lesson Library, and new T12 files; DB variables were explicitly absent. Database-gated cases skipped in this offline run. |

The new integration test uses lowercase Base36 encoding of random 128-bit UUID values for `synthetic-` identifiers that must fit existing 36-character BE1 ID columns and the operator's lowercase ID validation. No schema was changed.

## B4a and B5 conclusions on PostgreSQL

- **B4a synthetic pilot:** The end-to-end synthetic eligibility and accepted-canvas-stroke chain **passed on local PostgreSQL 17.11** in the new integration test. The separate legacy BE1 PostgreSQL suite is not fully green because one existing test conflicts with the current consent guard, as described above.
- **B5 receipt replay:** **Passed on local PostgreSQL 17.11** in the isolated replay test. Its test-created rows were removed afterward.

## Not done / limitations

- `GET .../status` is not mounted as an HTTP route in this code. The PostgreSQL test calls the T2 `get_verified_device_status` guard directly; it does not claim an HTTP GET endpoint was tested.
- A production PostgreSQL source implementing `BE1FactSource.current_facts()` was not found. A live PostgreSQL `BE1FactReader` → BE2 projection is therefore **NOT DONE**; no adapter was added outside the allowlist.
- The existing legacy BE1 consent test and Lesson Library scanner test remain failed for the observed reasons above; they were not patched.
- No Modal/GPU request, real-child-data test, production-provider test, or B4b consent-lifecycle implementation was performed.

## Git closeout

No commit was created. At closeout, local `HEAD` was `f1f97747` and `origin/feature/feat063-be-foundation` was `9f337aff`; the refs had diverged (`1` remote-only commit and `1` local-only commit). This is neither approved commit case X (`0 1`) nor case Y (remote already contains `f1f97747`). No stage, amend, rebase, merge, or push was performed.
