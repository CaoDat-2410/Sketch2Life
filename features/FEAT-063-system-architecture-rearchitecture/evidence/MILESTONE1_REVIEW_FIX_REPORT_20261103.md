# Milestone 1 independent-review fixes — 2026-11-03

Status: **FIXED — XONG-CHƯA REVIEW**. This is an implementation report, not independent acceptance. Baseline HEAD remains `c4edf51fd5af69a327d6776625cf387447f4ec59`. The owner explicitly authorized recording approval and fixing the six findings under `plan/STORYRUN_LITE_MILESTONE1_INDEPENDENT_REVIEW_FIX_20261103.md` (SHA-256 `B054B44289EA9DE32F26878F719E06A1EA34591518BDDF5690EA62AB3BB295C4`).

## Finding disposition

| Finding | Change | Verification |
| --- | --- | --- |
| P1 repeat demo | Existing cancel now permits PREPARATION_REVIEW, transitions to DELETE_PENDING and releases active-owner identity atomically. No new state or migration. Assets, understanding and receipts remain stored. | Two full synthetic HTTP flows with different images on the same DB, including upload bytes, confirm, explicit cancel, next run and checks of retained data. |
| P2 ledger reconciliation | Query uses committed understanding revision joined to run ID, revision and canonical/raw hashes; no SUBJECT_REVIEW state filter. Existing bridge still requires matching organization/run/job/attempt and SENT. | Six crash/finalize-false scenarios combined with confirm/cancel/confirm-then-cancel; mismatch tuple/hash; no redispatch. |
| P2 attach replay | New scoped repository receipt lookup runs before mutable target/admission checks in service; checks actual run owner before lookup and preserves fingerprint validation. | HTTP/service replay tests; PG replay after success, confirm, cancel and recovery; different owner/fingerprint rejected; dispatch count unchanged. |
| P2 singleton loss | Startup uses pg_try_advisory_lock. Probe pins backend PID and exact advisory key; lost/replaced session latches unready and does not reacquire. New HTTP operations and startup recovery check lock health. | Dead/replaced/missing-lock unit cases; on real PG, terminate old lock backend, reject old instance, acquire with new instance, and fail fast while lock held. |
| P2 upload guide | README explicitly sends request 03, verifies length/hash and 200 before complete. | Contract suite and synthetic HTTP upload flow. |
| P3 confirm GET | New request 11 asserts PREPARATION_REVIEW; docs use 07 before confirm and 11 after confirm, then optional explicit cancel closeout. | Collection/contract checks and HTTP state assertions. |

OpenAPI runtime resource and artifact have matching cancel descriptions. D17 remains: already claimed work may continue after lock loss; cancellation does not establish provider termination. Direct repository methods are storage APIs; the new readiness gate is enforced at HTTP runtime entry and startup recovery.

## Actual verification

- Offline command (from backend, with AWS_EC2_METADATA_DISABLED=true): `python -m pytest tests/contract/test_story_run_lite_api.py tests/contract/test_story_run_lite_main_composition.py tests/contract/test_story_run_lite_review_replay.py tests/contract/test_openapi_contract_catalog.py tests/unit/test_story_run_lite_domain.py tests/unit/test_story_run_lite_photo_bridge.py tests/unit/test_story_run_lite_quarantine_cleanup.py tests/unit/test_story_run_lite_singleton_health.py tests/unit/test_invocation_guard_transport_ga1.py -p no:cacheprovider --basetemp <task>/m1-offline-final` — **163 passed, 1 skipped**, 20.97 seconds. The skip is the real-PG singleton test; it passed in the separate database run.
- Isolated PostgreSQL 17 cluster, unique loopback port, new `storyrun_lite_review_*` DB, current user/owner postgres, legacy synthetic asset seeded before StoryRun migration, `upgrade heads`: `python -m pytest tests/integration/test_story_run_lite_postgres.py tests/integration/test_story_run_lite_loopback.py tests/unit/test_story_run_lite_singleton_health.py -vv --tb=short -p no:cacheprovider --basetemp <task>/pytest -o faulthandler_timeout=30` — **36 passed**, 10.46 seconds, no skips/timeouts. Sanitized raw output is `MILESTONE1_REVIEW_FIX_POSTGRES_20261103.log`. The temporary cluster was stopped successfully; existing PostgreSQL services and DBs were untouched.
- First DB runner attempt could not start PostgreSQL inside the restricted Windows token. Authorized execution outside that restriction then worked. The first full run was **35 passed, 1 failed** because the helper seeded a legacy organization name different from the existing fixture contract. Correcting only that helper and rerunning on a new cluster produced the 36/36 result above; no application assertion was weakened.
- Ruff check on changed source and new/changed tests passed using `--no-cache`; default cache was inaccessible. Mypy passed for five changed source modules using a task-local cache. Ruff format and final governance/security/architecture/diff checks are verified at closeout.
- **NOT RUN:** Bruno CLI execution, a repeated demo with real ClamAV and OS image worker, Modal/GPU/provider, full BE/A2 regression and production auth/CORS. Synthetic scanners/normalizers in the new HTTP regression are test doubles. This report does not label those doubles real antivirus verification.

## Preservation and review

The 55 pre-existing local paths are checked against the pre-merge snapshot (three already-reconciled previews, 52 original byte copies). No A2 file is part of this fix. No stage, commit, push or merge was performed; index remains empty. Original review source is retained as sanitized feature evidence. Review round 2 must use the changed working-tree files and supplemental snapshot, since HEAD alone does not contain these fixes. Historical live Modal evidence is not a post-fix live run.

Closeout checks: HARNESS_VALID, REPOSITORY_SECURITY_VALID (6,219 publishable files), ARCHITECTURE_VALID and git diff --check all exit 0. Ruff check passed on nine scoped source/test files; Ruff format check passed on seven scoped source/new-test files. No claim is made that unrelated baseline files are fully formatted or type-clean.

This was the round-1 implementation checkpoint. The later round-2 review and corrections are recorded separately in `evidence/MILESTONE1_REVIEW_ROUND2_FIX_REPORT_20261103.md`; its final test totals supersede the interim counts above.
