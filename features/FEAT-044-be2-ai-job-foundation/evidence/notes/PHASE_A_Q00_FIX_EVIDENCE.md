# BE2-01 Phase A — Q00 review corrections R01–R11 (evidence)

- Date: 2026-10-14, Asia/Saigon. Executor: Claude. Slot: Q00 (tracker), within the existing
  Phase A revision 1 approval; no new approval, card or Phase B work.
- Input: `PHASE_A_CODEX_INDEPENDENT_REVIEW_20261014.md` (NEEDS_REVISION) and its probes.
- This note records the executor's fixes and runs only. **It does not close the review**; the
  independent reviewer must re-check (see last section). BE2-01 stays IN_PROGRESS.
- Environment: same as `PHASE_A_IMPLEMENTATION_EVIDENCE.md` (pre-existing `backend/.venv`,
  Python 3.12.10, pytest 8.4.2, FastAPI 0.141.1, Pydantic 2.13.4, ruff 0.16.4, mypy 1.20.2;
  no install; Pillow absent). `PYTHONPATH`/`MYPYPATH` pinned to `<worktree>/backend/src`,
  bytecode writes disabled; module origin receipt `raw/q00_module_origin.txt`.
- Preserved outside scope: Gradle wrapper edit; `docs/context/PROJECT_CONTEXT.md` and
  `SOURCE_REGISTER.md` working-tree edits by another author (not touched).

## Before/after reproduction

`raw/q00_repro_source.txt` (scenario script, same calls as the review probes) was run before any
fix → `raw/q00_repro_before.json` (all 11 `defect_present: true`) and after → `raw/q00_repro_after.json`
(all 11 `false`). The permanent pytest regressions were written after the fixes, mirroring these
scenarios; their pre-fix failure is evidenced by the before receipt, not by a pytest run.

| ID | Before (observed) | Fix (owning module) | After / regression |
|---|---|---|---|
| R01 | INPUT_MISMATCH / OUTPUT_MALFORMED quarantined foreign-org and unowned refs | `ArtifactDescriptor` gains producer lineage; service only accepts/quarantines refs with same org **and** this job/attempt lineage (`services/ai_jobs.py` `_owned_refs`, `_produced_by`) | no foreign/other-job ref quarantined; own rejected output still quarantined; other-attempt output = OUTPUT_MALFORMED — `test_r01_*` (4), runner A-15 |
| R02 | same request, target/session/child B → same job “deduplicated” | `SemanticRequestKey` includes target, purpose, session, sorted subjects | different scope → new job; matching scope still dedups across principals — `test_r02_*` (5), runner A-03 |
| R03 | INVALID_STATE / INPUT_MISMATCH receipts occupied the attempt slot; valid claim then rejected / COMPLETION_CONFLICT | only job-changing (authoritative) completions are stored; guard rejections return `authoritative=false`, audited, not stored | same claim lands after start; corrected claim accepted; genuine conflict after accepted completion still raised; only accepted receipt stored — `test_r03_*` (2), runner A-11 |
| R04 | failure code `http 503 from provider` persisted; CMD-44 HTTP 500 | worker-claim normalisation: unknown codes → PROVIDER_ERROR (original only hashed); malformed kind/moderation/retryable/mixed claims → non-authoritative MALFORMED_CLAIM; domain rejects non-`^[A-Z][A-Z0-9_]{1,79}$` codes | HTTP 200 with PROVIDER_ERROR, raw code absent from response/audit; malformed claims don't poison the attempt — `test_r04_*` (8), runner A-15 |
| R05 | two concurrent same-key purges → 2 dispatches, receipts disagree | registry `scope_lock` fake atomic boundary; `put_purge_receipt` returns stored receipt | 3 concurrent calls → 1 dispatch, one receipt everywhere — `test_r05_*`, runner A-18 |
| R06 | replay p1 after p2 deleted → InvalidCopyTransition | replay returns that key's immutable result computed from its stored receipt; never mutates/re-dispatches | replay == original result; copy stays deleted with p2 receipt; 2 dispatches total — `test_r06_*` (2), runner A-18 |
| R07 | `request_reason=[]`/`{}` → TypeError | enum check requires a string member | 20 `shapes/negative_types` fixtures (list/dict/null/number × 5 enum fields) return errors — `test_r07_*` (20), runner A-19 |
| R08 | queued + accepted + refs accepted by strict schema | refs only with `succeeded`+`accepted`; non-terminal states require null disposition | 4 new DATA-25 negatives rejected — `test_r08_*` (4), runner A-02 |
| R09 | revoked job enqueued by dispatch | `dispatch_outbox` rechecks eligibility; denied → cancelled, entry dropped, audited | consent/session/recall/expiry/kill-switch + retry-requeue path — `test_r09_*` (6), runner A-14 |
| R10 | 60 s later hint 10000 ms but old ETag → 304 | ETag variant includes computed `poll_after_ms`; retry-wait part rounded up to whole seconds | conditional poll returns 200 + new hint, then 304 on new tag; 1 ms later still 304 during backoff — `test_r10_*` (2), runner A-10 |
| R11 | Child schema accepted terminal polling / missing failure / succeeded+failure | `_check_state_rules` shared by full and Child views | 3 new Child negatives rejected — `test_r11_*` (3), runner A-02 |

Existing behaviour kept: accepted receipts immutable; same-identity different-output conflict;
fake atomicity remains fake (no DB/broker introduced). Two pre-existing lifecycle tests used
`reason_code="C"`; they now use `CANCELLED_BY_TEACHER` because the domain validates code format.

## Checks (receipts `raw/q00_*.txt`, metadata `metrics/q00_checks.json`; all exit 0)

Post-documentation re-run: `raw/q00_final_*.txt`, `metrics/q00_final_checks.json` (runner, harness, architecture, security, skeleton, diff; all exit 0). The three repro receipts were then converted CRLF→LF (Windows stdout redirect); content unchanged, security/diff re-checked PASS.

| Check | Command (from worktree root) | Result |
|---|---|---|
| Runner, default interpreter | `python -B features/FEAT-044-be2-ai-job-foundation/src/run_fixture_contracts.py --report …/q00_runner_report.json` | 20/20 PASS, 210 checks, 0 failed, 1 NOT_RUN (HTTP surface; needs FastAPI) |
| Runner, venv + HTTP | `<backend-venv>/python -B …/run_fixture_contracts.py --with-http --report …/q00_runner_report_http.json` | 21 rows PASS (20 criteria + A-17-http), 217 checks, 0 failed |
| Determinism | both runs | identical `results_sha256=308b4c93…20b1f791` |
| Phase A tests + R-regressions | `python -m pytest backend/tests/unit/test_ai_job_review_regressions.py backend/tests/unit/test_ai_job_lifecycle.py backend/tests/unit/test_ai_job_application.py backend/tests/contract/test_ai_job_contracts.py backend/tests/contract/test_ai_job_polling.py` | 204 passed, 1 skipped (Pillow) |
| PLAN targeted regressions | `python -m pytest backend/tests/unit/test_ephemeral_storage_ports.py backend/tests/unit/test_whiteboard_video_job.py backend/tests/unit/test_story_video_job_input_gate.py backend/tests/contract/test_mobile_workflow_contracts.py` | 32 passed |
| Ruff | `ruff check --config backend/pyproject.toml --no-cache <affected files + feature src>` | All checks passed |
| Mypy strict | `mypy --config-file backend/pyproject.toml --no-incremental <14 Phase A modules>` | no issues |
| Harness / architecture / security / skeleton | `python tools/validate_{harness --feature …,architecture,repository_security,skeleton}.py` | VALID |
| Diff | `git diff --check` | exit 0 (pre-existing Gradle CRLF warning only) |

Fixtures: 90 synthetic files; `fixtures/MANIFEST.json` sha256
`245e8b21de0a31d093080056414c880e7cbe279174ee8ec9a524777366360c51` (was `86aec5ea…`). Changes:
27 new negatives, regenerated P1 poll example (ETags now include the poll-hint variant), error
catalogue adds `MALFORMED_CLAIM`, non-authoritative reasons and the worker-code mapping.

## A-01..A-20 after Q00

All twenty criteria PASS at fake/contract scope in both runner runs; A-06/A-18 remain fake-only
(no DB concurrency, no actual deletion); A-20 artefacts present, P1/P2/P4 cross-review PENDING.

## Not run / remaining gates

- `REQUIRES_LIGHTNINGAI_TEST` (any env with full backend deps incl. Pillow):
  `python -m pytest backend/tests/contract/test_ai_job_polling.py::test_live_app_routes_have_no_candidate_job_route`
- Full backend suite not run. Runner core still lists A-17 HTTP surface as NOT_RUN even when the
  supplemental `A-17-http` row runs (reporting quirk noted by the reviewer; unchanged).
- Independent re-review of R01–R11 and P1/P2/P4 candidate adoption: PENDING.

## Scope for the independent re-review

1. Completion receipt model (`authoritative` flag, what is stored, conflict rule) vs B22.3.
2. Artifact lineage requirement on `ArtifactDescriptor` (P2/DATA-20 port impact).
3. Semantic key scope fields; whether purpose/subject inclusion matches business dedup intent.
4. Worker failure-code allowlist and `MALFORMED_CLAIM` handling.
5. ETag variant including `poll_after_ms` and seconds quantisation.
6. Purge `scope_lock` port and replay semantics (result-of-that-request vs current state).
7. New fixtures/negatives and manifest; shared Child/full state rules.
