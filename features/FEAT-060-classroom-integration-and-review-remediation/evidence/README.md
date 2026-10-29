# FEAT-060 evidence index

## Rev5 CI and Iteration 1 verification — 2026-10-24

- Plan: `../plan/PLAN_REV5_CI_AND_ITERATION1_VERIFICATION_20261024.md`; owner approval and exact plan hash are in `../approvals/TASK_APPROVAL.md`.
- Added `.github/workflows/ci.yml` with pinned actions, locked installs, repository policy validators, active Child/Teacher/Admin checks, and focused backend tests. It passes no repository secrets and makes no provider/deployment calls. Hosted run `40101108871` at commit `83695ef1` completed: backend and Child UI passed; repository policy, Admin UI and Teacher UI failed. Failing steps were `Validate repository harness` and `Run UI checks` for Admin/Teacher. The accessible check details do not establish root cause. [Open hosted run](https://github.com/CaoDat-2410/Sketch2Life/actions/runs/40101108871).
- Local baseline receipts: all repository policy validators now pass; Child, Teacher and Admin `npm ci`/`npm run check` passed; backend locked sync and focused pytest passed (22 passed, four PostgreSQL cases skipped because `BE1_TEST_DATABASE_URL` is unset). Exact per-command receipts are under `raw/ci-rev5-20261024/`.
- ADR-0006 workstreams: P1 8/8 fixture tests passed; P2 22/22 tests passed; P3 typecheck passed and 67/67 tests passed in 14 suites; P4 learning-media tests passed 14/14, but the separate local component runner returned `FAIL`, reporting 460 owned cases, 1,436 regression cases, and 11 SQL-collection-only cases. SQL, provider, selected-decoder and adoption checks did not run. The failure means Iteration 1 is not fully accepted.
- `iteration1-p4-runner.log` contains an absolute workstation path and remains ignored/local. Its path-free result summary is `raw/ci-rev5-20261024/iteration1-p4-runner-results.txt`.
- Do not create `review-2` or claim tagged BM02 until the hosted workflow and all acceptance gates pass at one exact clean commit.

## Rev4 current result

- `plan/PLAN_REV4_IMPLEMENTATION_20261024.md` — owner-approved implementation plan; exact SHA-256 in `approvals/TASK_APPROVAL.md`.
- `notes/API_INTEGRATION_CATALOGUE_20261024.md` — current method/path, UI caller, backend effect, guard, and verification limit for the connected flow.
- `raw/` — Rev4 UI/backend test receipts and repository-security validation; no secrets or child data.
- `raw/backend-rev4-focused-check.log` — 22 passed; four PostgreSQL acceptance tests skipped because `BE1_TEST_DATABASE_URL` is unset.
- `raw/child-ui-rev4-check.log` — Child typecheck, export/build, lint and 18 suites/26 tests passed; existing `useOfflinePacing.ts` lint warning remains.
- `raw/teacher-ui-rev4-check.log` — Teacher build, lint and 3 suites/6 tests passed; Vite reports the existing large-bundle advisory.
- `raw/be1-migration-offline-sql.log` — Alembic rendered the BE1 upgrade through `20261024_0005` to PostgreSQL SQL without connecting to or modifying a database.
- `raw/repository-security-validation.log` — validator currently exits non-zero for existing FEAT-058 absolute-path/PDF findings and older FEAT-060 evidence logs; the findings are preserved without changing those unrelated artifacts.
- Local implementation is complete for the approved BE1 scope. PostgreSQL execution is pending because `BE1_TEST_DATABASE_URL` is not configured. No live migration, deploy, Modal request, or BE1 external review was performed.

## Current baseline

- `notes/BASELINE_20261023.md` — source, integration, and configuration preflight.
- `notes/SRS_STAGE_API_TRACEABILITY_20261023.md` — exact nine-stage mapping, current endpoints, caller screens/services, durable effects, auth/guards, and gaps.
- `../artifacts/BE1_SHARED_STAGE_CONTRACT_PROPOSAL.md` — design history for the locally implemented shared-stage and completion contract; database verification and BE1 review remain open.
- `../artifacts/BE1_NUMERIC_JOIN_CONTRACT_PROPOSAL.md` — design history for the locally implemented six-digit join contract; database verification and BE1 review remain open.
- `../artifacts/MODAL_HOSTING_BOUNDARY_REVIEW_20261023.md` — review of backend-container vs AI-worker placement and live-test gate.
- `../plan/PLAN_REV4_IMPLEMENTATION_20261024.md` — owner-approved local implementation plan (SHA-256 recorded in `approvals/TASK_APPROVAL.md`); FEAT-057, Modal, deployment, and PostgreSQL gates remain.

## Previous baseline and supporting evidence

- `metrics/SR_TRACEABILITY.json` — SR-01–SR-10 owners, contracts, status, acceptance evidence and unresolved gates.
- `metrics/changed_file_manifest.json` — paths/hashes attributable to FEAT-060; exclude pre-existing unrelated dirty files.
- `raw/` — focused build/test/validator logs, with secrets and sensitive data excluded.
- `notes/` — contract gaps, state/migration proposals, NFR profile, Modal availability, and per-workflow interpretation.

- `notes/IMPLEMENTATION_BASELINE_20261024.md` — baseline, migration-root finding, FEAT-057 gates and preservation manifest captured before product-source implementation.
- `raw/implementation-baseline-20261024/` — original status, HEAD, diff summary and selected source hashes.
- Baseline checks: Admin check passed; Child/Teacher checks exposed the recorded pre-existing failures; backend composition/session contract tests passed 10/10. Alembic in `backend/.venv` reports nine independent heads.

- `notes/API_INTEGRATION_CATALOGUE_20261024.md` — per-API method/path, caller, payload/response, purpose, backend effect, verification and remaining contracts for all nine SRS stages.
- `notes/OWNER_DECISIONS_REQUIRED_20261024.md` — record of all six owner product decisions and the separate BE1/FEAT-057/Modal gates.
- `raw/active-ui-full-check.log` — historical Rev3 combined Child/Teacher/Admin check; current Rev4 Child and Teacher receipts are listed above.
- `raw/backend-composition-session-check.log` — historical backend composition/session HTTP contract tests, 10 passed; Rev4 focused backend receipt is listed above.
- `metrics/changed_file_manifest.json` — hash inventory for the implementation-relevant files reviewed in this pass, with comparison to the preserved pre-implementation snapshot where available.

Plan Rev4 implementation is authorized and completed locally within its recorded gates. Existing dirty work was preserved. Current UI and backend test receipts are not a substitute for a configured PostgreSQL-backed end-to-end test.
