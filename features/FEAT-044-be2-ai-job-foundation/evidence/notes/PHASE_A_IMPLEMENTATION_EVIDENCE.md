# BE2-01 Phase A — implementation evidence (fixture/contract scope)

> Publication disposition (2026-10-15): phase_a_run1/run2 raw receipts and metadata stay operator-local, byte-preserved; run3/final and independent review receipts remain candidates. See PUBLICATION_SELECTION_20261015.md for exact names/hashes. Recorded results are unchanged.

- Date: 2026-10-14, Asia/Saigon (checks run 21:07–21:10 +07:00). Executor: Claude.
- Approval: `approvals/TASK_APPROVAL.md` (Phase A revision 1, recorded 20:43 +07:00 before code).
- Worktree/branch: `.worktrees/be2-01-ai-job-foundation`, `feature/be2-01-ai-job-foundation`,
  baseline `b9204d8c9eb4f8a1ee6d4db4de5ee23672e0392c`. Nothing committed/pushed/deployed.
- Environment: Windows; default `python` 3.12.10 (Pydantic only); pre-existing
  `backend/.venv` Python 3.12.10 with pytest 8.4.2, FastAPI 0.141.1, Pydantic 2.13.4,
  ruff 0.16.4, mypy 1.20.2 (no install performed). Pillow is **not** in that venv.
- Module origin guard: `PYTHONPATH`/`MYPYPATH` pinned to `<worktree>/backend/src`; receipt
  `raw/phase_a_run3_module_origin.txt` shows `sketch2life` loaded from the worktree.
- Machine-readable receipts: `metrics/phase_a_run3_checks.json` (final), `phase_a_run2_checks.json`,
  `phase_a_run1_checks.json`; sanitized logs `raw/phase_a_run{1,2,3}_*.txt`; runner reports
  `raw/phase_a_run3_runner_report.json` and `..._report_http.json`.

## Check results (run 3, all receipts exit 0)

| Check | Command (from worktree root) | Result |
|---|---|---|
| Runner, default interpreter | `python -B features/FEAT-044-be2-ai-job-foundation/src/run_fixture_contracts.py --report …` | 20/20 criteria PASS, 164 checks, 0 failed, 1 NOT_RUN (HTTP surface needs FastAPI) |
| Runner, venv + HTTP | `<backend-venv>/python -B …/run_fixture_contracts.py --with-http --report …` | 21/21 PASS, 171 checks, 0 failed |
| Determinism | both runs | identical `results_sha256=364ca318…e7538d` across two interpreters; A-01 rerun digest equal |
| New tests | `python -m pytest backend/tests/unit/test_ai_job_lifecycle.py backend/tests/unit/test_ai_job_application.py backend/tests/contract/test_ai_job_contracts.py backend/tests/contract/test_ai_job_polling.py` | 140 passed, 1 skipped (live-app route check: Pillow missing) |
| Targeted regressions | `python -m pytest backend/tests/unit/test_ephemeral_storage_ports.py backend/tests/unit/test_whiteboard_video_job.py backend/tests/unit/test_story_video_job_input_gate.py backend/tests/contract/test_mobile_workflow_contracts.py` | 32 passed |
| Ruff | `ruff check --config backend/pyproject.toml <changed python files + feature src>` | All checks passed |
| Mypy (strict) | `mypy --config-file backend/pyproject.toml <14 new backend modules>` | Success, no issues in 14 files |
| Harness | `python tools/validate_harness.py --feature features/FEAT-044-be2-ai-job-foundation` | HARNESS_VALID |
| Architecture | `python tools/validate_architecture.py` | ARCHITECTURE_VALID |
| Repository security | `python tools/validate_repository_security.py` | REPOSITORY_SECURITY_VALID |
| Skeleton | `python tools/validate_skeleton.py` | valid |
| Diff | `git diff --check` | exit 0 (pre-existing Gradle CRLF warning only) |
| New/edited file scan | inline read-only scan of 136 files changed this session | 0 CR / trailing-whitespace / missing-newline problems |

Fixture manifest: `fixtures/MANIFEST.json` sha256 `86aec5ea3e693f4d437cf1492b470a137a62dd78d55fe9c679863e7728b072a2`
(63 synthetic files; runner A-02 regenerates and byte-compares them).

### Failures found and fixed during verification (receipts preserved)

- Run 1 `security` FAIL: `TOKENS = {...}` (synthetic principal map in the polling test) matched
  the validator's uppercase `*TOKEN* =` rule. Renamed to `FIXTURE_PRINCIPALS`; validator untouched.
- Run 1 runner `--with-http` FAIL: FastAPI 0.141 wraps included routers (`_IncludedRouter`), so a
  plain `app.routes` walk returned an empty set — which also made the pytest subset assertion
  vacuous. Added `route_surface()` and changed both checks to exact, non-empty equality; also
  replaced a "passing" placeholder for the no-HTTP case with an explicit `not_run` entry.
- Run 2 `ruff` FAIL: import order in the runner (fixed with ruff's import sort only).
- Before run 1: two runner scenarios (A-11, A-13) wrongly sent a *different* second claim for an
  attempt that already reported failure; the code correctly raised `COMPLETION_CONFLICT`. The
  scenarios now supersede via timeout / replay the identical claim. A-06 detail string sorted to
  keep the determinism digest stable.

## A-01..A-20 mapping (fake/contract semantics only)

| ID | Result | Evidence (runner scenario + pytest) |
|---|---|---|
| A-01 | PASS | Runner on default interpreter with no FastAPI/DB/broker/SDK modules loaded; deterministic rerun digest |
| A-02 | PASS | 30 runner checks; `test_ai_job_contracts.py` strict positive/negative fixtures, UTC round trip |
| A-03 | PASS | one job/attempt, provider called once; `test_duplicate_semantic_request_yields_one_job_attempt_and_cost` |
| A-04 | PASS | `IDEMPOTENCY_PAYLOAD_MISMATCH`, scope includes principal/org; `test_command_scope_includes_principal_and_organization` |
| A-05 | PASS | redelivery `DUPLICATE_DELIVERY`, duplicate completion = prior receipt |
| A-06 | PASS (fake) | two threads → one `accepted`, one `COMPLETION_CONFLICT` incident; stale CAS; injected commit failure leaves no partial state. Not DB concurrency |
| A-07 | PASS | 3 attempts (named PROPOSED policy) → `failed_exhausted`; timeout sweep → `failed_retryable` |
| A-08 | PASS | unknown → null; truthful % kept; malformed rejected (domain + schema) |
| A-09 | PASS | other org / ungranted / revoked → `404` identical to missing (service + HTTP) |
| A-10 | PASS | 304 only while authorized; consent revoke changes ETag and hides refs; grant revoke → 404 before cache |
| A-11 | PASS | superseded attempt stale; input/request/context mismatch rejected + incident; newer attempt intact |
| A-12 | PASS | `succeeded`+`stale`, pinned context kept with lineage note, refs not projected |
| A-13 | PASS | cancel from queued/running/failed_retryable; retry callback no-op; late result `JOB_CANCELLED`; If-Match 428/412 |
| A-14 | PASS | consent/session/recall/expiry/kill-switch (+budget) gate create/start/retry/completion; notices idempotent |
| A-15 | PASS | unsafe → `blocked_unsafe` + quarantine; malformed → `OUTPUT_MALFORMED`; diagnostics redacted (sha256 only) |
| A-16 | PASS | Teacher exact refs/hash; no approval/playback fields; Device projection minimal |
| A-17 | PASS | forged/missing/other-job capability denied; fixture app exposes exactly `GET /jobs/{job_id}`; POST 404/405 |
| A-18 | PASS (fake) | duplicate purge idempotent; fixture delete labelled `fixture_deleted_not_actual`; pending/unsupported/exception/unverified never deleted; no resurrection. Not actual deletion |
| A-19 | PASS | DATA-24 (owner BE2-05), ProviderCopyLifecycle (owner BE2-14) and DATA-21..23/26..29/33 shape fixtures |
| A-20 | PASS (artefacts) / PENDING (review) | `PHASE_A_HANDOFF.md`, error catalogue, P1 poll example, manifest, runner report exist. P1/P2/P4 cross-review not yet performed |

## Not run / blockers

- `REQUIRES_LIGHTNINGAI_TEST` (or any environment with full backend deps incl. Pillow):
  `python -m pytest backend/tests/contract/test_ai_job_polling.py::test_live_app_routes_have_no_candidate_job_route`
  — skipped here; the AST check that `app.py` imports nothing from `ai_jobs` did run and pass.
- Full backend suite not run (only the PLAN's targeted regressions). Default interpreter lacks
  pytest/FastAPI; the existing venv lacks Pillow.
- Not in Phase A scope and not claimed: durable storage/restart/outbox/real concurrency (Phase B),
  real provider inference or deletion, LightningAI environment, device/visual QA.
- No independent reviewer pass yet (this evidence is the executor's own run). Adoption of
  candidate schemas/names/policies remains a cross-review decision (see handoff §6).
