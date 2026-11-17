# BE2-01 Phase A — Q00 closure follow-ups R03a, R04a, A18a (evidence)

> Publication disposition (2026-10-15): q00a initial/run2 raw receipts/metadata stay operator-local, byte-preserved; q00a_run3, before/after repros and codex_q00a_final remain candidates. See PUBLICATION_SELECTION_20261015.md. No result or approval changes.

- Date: 2026-10-14, Asia/Saigon. Executor: Claude. ACTIVE slot Q00, existing Phase A revision 1
  approval; no new card, no Phase B.
- Input: `PHASE_A_Q00_CODEX_CLOSURE_REVIEW_20261014.md` (NEEDS_REVISION, three follow-ups).
  Original review, closure review and all earlier receipts are unchanged.
- Executor status: **FIXED_PENDING_REVIEW**. This note does not close the independent review.
- Environment: pre-existing `backend/.venv` (Python 3.12.10, pytest 8.4.2, FastAPI 0.141.1,
  Pydantic 2.13.4, ruff 0.16.4, mypy 1.20.2), no install, Pillow absent; `PYTHONPATH`/`MYPYPATH`
  pinned to `<worktree>/backend/src`, bytecode writes disabled; origin receipt
  `raw/q00a_run3_module_origin.txt`. Gradle wrapper and the other author's
  `docs/context/*` edits untouched.

## Before / after

Script `raw/q00a_repro_source.txt` (same calls as the closure-review probes; A18a uses events,
no sleeps) → `raw/q00a_repro_before.json` (3/3 defect present) and `raw/q00a_repro_after.json`
(0/3). Original R01–R11 script re-run after these changes → `raw/q00a_original_r01_r11_repro.json`
(11/11 still absent).

| ID | Before (observed) | Fix (owning module) | After / regression | Status |
|---|---|---|---|---|
| R03a | INVALID_STATE (and INPUT_MISMATCH) quarantined the output; the later accepted claim projected that same ref while it stayed quarantined | `services/ai_jobs.py`: `INVALID_STATE`/`INPUT_MISMATCH` are temporary verdicts and change no artifact state; final outcomes (cancelled/terminal/superseded/revoked/unsafe/malformed) still quarantine own outputs. Port `ArtifactDescriptor.quarantine_reason` (fake reports it); admission rejects quarantined refs → `OUTPUT_MALFORMED`, so nothing quarantined is ever released or projected | projected refs == accepted output, not quarantined, for both paths; accepted replay/conflict kept; unsafe/revoked/cancelled still quarantined; pre-quarantined ref not admitted; foreign untouched — `test_r03a_*` (5), amended `test_r01_*`/`test_r03_*`, runner A-11 | FIXED_PENDING_REVIEW |
| R04a | `failure_code=[]`/`{}` → `TypeError: unhashable` at allowlist lookup; job left running | `_normalise_claim` type-checks before lookup: non-string non-null code → non-authoritative `MALFORMED_CLAIM`, audit gets only sha256 of repr. Non-string `job_id`/`attempt_id` → typed `400 MALFORMED_REQUEST`. `canonical_json` fingerprints non-JSON values via typed repr instead of raising | list/dict/secret-bearing list/dict/int/bool/bytes/set → MALFORMED_CLAIM, job running, secret absent from view/audit, later valid completion accepted and projected; string codes keep R04 mapping — `test_r04a_*` (10), runner A-15 | FIXED_PENDING_REVIEW |
| A18a | cancel read DISCOVERED, paused in adapter; purge completed (deleted + receipt); cancel resumed and saved `cancel_requested`, receipt null | `services/provider_copy_lifecycle.py`: `cancel_scope` (and `register_copy`) read/dispatch/save inside the existing registry `scope_lock` used by purge; no new infrastructure | event-controlled: purge provably waits while cancel is in flight, then final copy keeps purge status + receipt, discover/replay consistent, one dispatch (3 profiles); cancel after deletion leaves it untouched — `test_a18a_*` (4), runner A-18 | FIXED_PENDING_REVIEW |

Semantics changes are recorded in `plan/PHASE_A_CANDIDATE_SPEC.md` (§3 matrix + “Temporary vs
final rejection”, R04a paragraph, purge/cancel paragraph) and `PHASE_A_HANDOFF.md` (P2 artifact
port row, provider-copy note). Fixtures did not change (manifest still
`245e8b21de0a31d093080056414c880e7cbe279174ee8ec9a524777366360c51`).

## Checks (final set `raw/q00a_run3_*.txt`, `metrics/q00a_run3_checks.json`; all exit 0)

| Check | Command (from worktree root) | Result |
|---|---|---|
| Runner, default interpreter | `python -B features/FEAT-044-be2-ai-job-foundation/src/run_fixture_contracts.py --report …` | 20/20 PASS, 215 checks, 0 failed, 1 NOT_RUN (HTTP needs FastAPI) |
| Runner, venv + HTTP | `<backend-venv>/python -B …/run_fixture_contracts.py --with-http --report …` | 21 rows PASS, 222 checks, 0 failed; same `results_sha256=d17f58a3…f41f68` on both |
| Follow-up + Phase A tests | `python -m pytest backend/tests/unit/test_ai_job_q00_followups.py backend/tests/unit/test_ai_job_review_regressions.py backend/tests/unit/test_ai_job_lifecycle.py backend/tests/unit/test_ai_job_application.py backend/tests/contract/test_ai_job_contracts.py backend/tests/contract/test_ai_job_polling.py` | 223 passed, 1 skipped (Pillow) |
| PLAN targeted regressions | `python -m pytest backend/tests/unit/test_ephemeral_storage_ports.py backend/tests/unit/test_whiteboard_video_job.py backend/tests/unit/test_story_video_job_input_gate.py backend/tests/contract/test_mobile_workflow_contracts.py` | 32 passed |
| Ruff / mypy strict | affected Python files + feature src / 14 Phase A modules | clean / no issues |
| Harness, architecture, security, skeleton, diff | repository validators + `git diff --check` | VALID; diff exit 0 (Gradle CRLF warning only) |

Preserved intermediate receipts: `q00a_*` (security FAIL: `SECRET = …` constant in the new test
matched the validator's uppercase assignment rule → renamed `SENSITIVE_FRAGMENT`, validator
untouched) and `q00a_run2_*` (ruff E501 from that rename → wrapped). Run 3 is the clean set.

## Not run / remaining gates

- `REQUIRES_LIGHTNINGAI_TEST` (env with Pillow):
  `python -m pytest backend/tests/contract/test_ai_job_polling.py::test_live_app_routes_have_no_candidate_job_route`
- Full backend suite not run. Runner core A-17 NOT_RUN entry unchanged (reporting quirk).
- Independent closure review of R03a/R04a/A18a; P1/P2/P4 adoption (now including
  `quarantine_reason` and cancel-under-`scope_lock`) — PENDING.

## Files for the reviewer to verify

- `backend/src/sketch2life/application/services/ai_jobs.py` (`TEMPORARY_VERDICTS`, guard branch,
  `_validated_outputs` quarantine check, `_normalise_claim` type check, identity type check)
- `backend/src/sketch2life/application/ports/ai_jobs.py` (`ArtifactDescriptor.quarantine_reason`)
- `backend/src/sketch2life/infrastructure/ai_jobs/fakes.py` (`FakeArtifacts.describe`)
- `backend/src/sketch2life/domain/ai_jobs/completion.py` (`canonical_json` fallback)
- `backend/src/sketch2life/application/services/provider_copy_lifecycle.py` (`cancel_scope`,
  `register_copy` under `scope_lock`)
- `backend/tests/unit/test_ai_job_q00_followups.py`; amended `test_ai_job_review_regressions.py`
  (R01 final-rejection test, R03 availability asserts); runner A-11/A-15/A-18 checks
- `plan/PHASE_A_CANDIDATE_SPEC.md`, `evidence/notes/PHASE_A_HANDOFF.md` (Q00 amendments)
