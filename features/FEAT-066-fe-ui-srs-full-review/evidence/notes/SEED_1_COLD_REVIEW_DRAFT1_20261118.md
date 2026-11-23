# SEED-1 Draft 1 — cold review record (round 1, 2026-11-18)

- **Artifact:** `plan/PLAN_SEED1_S1_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT1_20261118.md`, 7,909 B, SHA-256 `3B74E04F8515F35124BC8006318B7109360B46BF33784A6D60B6074CE26D4DC5` (the version with the owner's SD-1 to SD-5 answers).
- **Reviewer:** a separate subagent with fresh context. Model Sonnet 5.5, reasoning effort high, both set explicitly by the coordinator. It worked read-only and statically.
- **Pin check:** PASS. It covered the package, the seed design Draft 6 (28,192 B, `CABC4BCA…`), the SRS (701,157 B, `B9B1F42D…`) and HEAD `08439b22`.
- **Verdict:** **NOT READY**. P1 = 0, P2 = 4, P3 = 6. All findings are text-level. The slice itself (S1 only) is sound and consistent with the design's stage table.
- **Coordinator spot-check:** the coordinator confirmed three points in source:
  - `_recalculate_visibility` is an instance method of `LessonLibraryService` (`service.py:1280`) that queries the database;
  - the Parent StoryRun routes take `run_id: UUID` (`parent_story_runs.py:239`, `:267`);
  - `actor_scope_ref` comes from `_principal_scope_ref` (`parent_story_repository.py:1654–1656`).

## Findings

| ID | Sev | Finding (short) | Planned fix (Draft 2) |
|---|---|---|---|
| S1R-01 | P2 | `_recalculate_visibility` cannot run without a session and service, so the "unit test without a database" claim fails. The lesson tables are Core `Table` objects, and `canonical_content_hash` and `validate_content` are missing from the imports | A pure re-derivation in `data.py`. The product method runs only in owner-run test 7, for parity, and only for lessons inserted in this run. Exact imports listed |
| S1R-02 | P2 | StoryRun rows are not plain inserts. They need a UUID `run_id`, `actor_scope_ref` from issuer and subject, and `active_owner_parent_account_id` only on the single active run per account. `run_inputs` has CHECKs. Test 6 has the wrong grain | A StoryRun column rule. Test 6 checks one active run per Parent account |
| S1R-03 | P2 | SD-3 (no port 5432 or 5433) is not enforced. `S2L_SEED_DATABASE_URL` is not named. Test 7 does not skip when the variable is unset | Guard delta, the variable named, test 7 uses the guard and skips when the variable is unset |
| S1R-04 | P2 | The design's acceptance "each role can open its main FE screen" is dropped without disclosure, and the §2 claims overreach | Deferred with SD-5 and disclosed; §2 reworded |
| S1R-05 | P3 | Guard details are missing: explicit port; alternate URL variables unset or equal; engine comparison before writes; fixed error messages with `from None`; its own owner SQL | Added |
| S1R-06 | P3 | `data_origin='SYNTHETIC_DEV'` with no consent is not restated, and the ORM default is `REAL` | Added to the rules and to test 6 |
| S1R-07 | P3 | Atomicity is unstated (deferred circular FK; a crash halfway would leave a partial seed) | One transaction, all or nothing |
| S1R-08 | P3 | Lesson source documents and revisions are not handled; a target age band placeholder is needed | Not seeded; placeholder band ref |
| S1R-09 | P3 | The command ceiling is prose. mypy needs namespace handling; tests are not linted; `validate_skeleton.py` is missing; `.env` isolation for guard tests; runbook notes (`PYTHONPATH=src`, never `upgrade` a seeded database) | Explicit command list and runbook notes |
| S1R-10 | P3 | The evidence note and the expected-count table have no home; security-validator naming cautions; the base claim | Added; base re-pinned at SD-4 |

## Next

Draft 2, then round 2 (rounds used: 1 of 5).
