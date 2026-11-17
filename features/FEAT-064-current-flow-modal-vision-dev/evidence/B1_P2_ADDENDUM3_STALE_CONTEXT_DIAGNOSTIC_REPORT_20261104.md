# B1 P2 Addendum 3 — STALE_CONTEXT diagnostic report

**Disposition:** `XONG-CHƯA REVIEW`  
**Scope:** diagnosis only; no production fix and no acceptance of B1 P2 / Finding 2.

## Checkout and input hashes

| Item | Observed value |
| --- | --- |
| Branch | `feature/feat063-be-foundation` |
| HEAD | `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9` |
| Staged paths | 0 before and after |
| Status entries before diagnostic plan | 101 |
| Status entries before this report | 102 (the plan added one entry) |
| Status entries after this report | 103 |
| Addendum 2 report SHA-256 | `3645DE2E2382BAC289F9EDFAC4DDF296CEE195A170330FA791D71A500282E2B0` |
| Diagnostic plan SHA-256 | `61DACAE1C93088933ED8D54F7803E1CB74B797D3385E5D3689EEBCFDBC1C8AE1` |
| PostgreSQL test SHA before diagnostic instrumentation | `4D81FDD3B4F73FF56027DB632EAB2AF0AF7C102CFEFB53990FAEC83A0D6FD0E6` |
| PostgreSQL test SHA after diagnostic instrumentation | `40CF435AF6D6A5374F1A1692C92043D5CDF8EE295B894A7BA0EC8012B9CBAFC2` |

The PostgreSQL test file was already dirty before Addendum 3. Its before/after hashes delimit the diagnostic instrumentation, but the full working-tree diff also contains the earlier B1 work. All unrelated dirty files were preserved. The report SHA-256 is recorded in the new snapshot manifest to avoid a self-referential hash.

## Actual completion path and diagnostic probes

`GuardedVisionJobProvider.run` (`backend/src/sketch2life/infrastructure/vision_analysis/pilot_composition.py:418,436`) calls the real Vision Analysis service and returns a completion claim. `DispatchWorker` passes it to `AiJobService.accept_completion` (`backend/src/sketch2life/application/services/ai_jobs.py:799`). Completion starts with a `STALE_CONTEXT` failure and permits two decision rounds (`:172,821`). `_decide_completion` (`:1068`) computes the proposed job state and artifact fences; `_hold` (`:1216`) rejects a missing fence before asking the unit of work to hold the present fences. Each `_StaleOwnerDecision` is retried; exhaustion becomes `_unresolved(STALE_CONTEXT)` (`:218,887,1216-1222`).

The test-only wrappers call the originals and preserve their return/raise behavior. They record eligibility conditions, pinned/current revision, completion decision, fence categories and transaction state, fence outcomes/exceptions, decision-round exhaustion, and read-only state for only the test-created job and its attempt. Identifiers, digests, URL values, credentials, and payloads are not emitted.

Relevant source evidence:

- `CurrentFactsBe1PilotEligibility.check` (`backend/src/sketch2life/infrastructure/vision_analysis/pilot_composition.py:202-249`) allowed the request and reported no false eligibility conditions.
- `_CombinedBe1OwnerFence.hold` (`pilot_composition.py:252-292`) and `PostgresBE1OwnerFence.hold` (`backend/src/sketch2life/infrastructure/assistance/owner_fence.py:298-363`) both returned current on the facts fence. The run observed all seven expected target rows and no resolver/SQL exception.
- `_decide_completion` (`ai_jobs.py:1068-1124`) accepted its proposed completion decision. The artifact fence collection is built from each owned descriptor (`:1107`).
- `_hold` (`ai_jobs.py:1216-1222`) requires every fence to be non-`None`. `PilotFakeArtifacts.write_output` constructs `ArtifactDescriptor` without a fence, and `describe` reconstructs it without one (`backend/src/sketch2life/infrastructure/vision_analysis/pilot_composition.py:326-365`).

## Focused PostgreSQL run record

The only test node used was:

```text
python -m pytest -o addopts= -s -q --tb=short tests/integration/test_be1_synthetic_pilot_postgres.py::test_b1_succeeded_is_durable_before_real_app_result_acceptance
```

Runs used the retained task-owned database `s2l_b1_review_20261104_6a1af65b` on local PostgreSQL 17, with the approved loopback target, port, and user. No database was created, reset, migrated, dropped, truncated, or manually cleaned. Only the test fixture's normal exact-row cleanup ran. No external provider or network was called.

| Attempt | Captured result | Diagnostic evidence |
| --- | --- | --- |
| 1 | `1 failed in 4.61s`; exit 1 | Eligibility allowed; pinned/current context revision both `860346270`; completion hold had 2 fences (`be1_facts`, `missing`), with 1 missing; both decision rounds exhausted as `STALE_CONTEXT`. |
| 2 | `1 failed in 4.43s`; exit 1 | Same path; pinned/current context revision both `1282792233`; one missing fence in each of 2 completion rounds; unresolved `STALE_CONTEXT`. |
| 3 | The command was launched after test-only annotation/format edits, but its tool output was truncated and is not recoverable. | Outcome and exit code: **not verifiable**; not counted as a confirmed matching diagnostic. |
| 4 | URL guard rejected the synthesized target before opening a DB connection; pytest process exit 1. Captured output: `DIAGNOSTIC_MARKER_NOT_FOUND`, `PYTEST_SUMMARY: pytest summary not found`, and `AssertionError: BE1_TEST_DATABASE_URL must target an approved loopback PostgreSQL acceptance database`. | No test-created rows or provider stub call from this attempt. The local URL had an existing database-routing query value; the target was then constructed with consistent task-owned database/loopback fields and checked by the existing guard. |
| 5 | URL guard accepted the explicit task-owned loopback target. `1 failed in 4.25s`; exit 1. | Final detailed result below; matches attempts 1 and 2. This was the fifth attempt, so no further PostgreSQL test was run. |

Final captured diagnostic facts:

- Eligibility: `allowed=true`, `false_conditions=[]`.
- Facts fence: PostgreSQL transaction held; all seven expected fence target rows were present; resolver returned matching/current facts; no SQL or resolver exception was observed.
- Completion decision: `disposition=accepted`, `updated_state=succeeded` on both rounds, before owner-fence enforcement.
- Completion hold: two fences, `be1_facts` plus `missing`; one missing. `_StaleOwnerDecision` occurred on both rounds; `_unresolved` reported `failure=STALE_CONTEXT`, `decision_rounds_used=2`.
- Test-created persisted state before fixture cleanup: `job_state=running`; `result_disposition=null`; result refs empty; one attempt outcome was null; no completion receipts; one analysis head; invocation state `SUCCEEDED`; outbox dispatch delivered once with one publish attempt and no error; stub call count `1`.
- Test assertion output: `WorkerOutcome(status='rejected', reason_code='STALE_CONTEXT', receipt=None)` instead of `completed`.

Thus, three captured database executions showed the same failure. One earlier run's output remains unavailable; one URL-guard rejection never connected. No assertion was changed or weakened.

## H1–H4 assessment

| Hypothesis | Finding | Evidence |
| --- | --- | --- |
| H1 — default stale failure plus repeated `_StaleOwnerDecision` exhausts bounded completion rounds | **CONFIRMED** | Two completion rounds, each proposed accepted/succeeded but failed `_hold`; `_unresolved` then emitted `STALE_CONTEXT`. Persisted job remained running, attempt outcome stayed null, and no result/receipt was written. |
| H2 — `_CombinedBe1OwnerFence` converts an underlying exception to stale | **NOT THE CAUSE OBSERVED** | The facts-fence resolver and PostgreSQL hold returned current; all seven target lookups succeeded; no caught exception was observed. The completion hold rejected the missing fence before a failing combined hold. This does not prove the broad catch is harmless in other cases. |
| H3 — genuinely stale eligibility/facts/artifact state | **PARTLY CONFIRMED: missing artifact fence** | Eligibility and BE1 facts were current. The artifact descriptor supplied by `PilotFakeArtifacts` has `fence=None`; `_hold` rejects that missing required fence. No stale artifact row was observed. |
| H4 — pinned context revision differs from current revision | **REJECTED FOR CAPTURED RUNS 1–2** | Revisions were equal in both runs. Final run also produced an accepted decision before fence rejection; its captured event did not include revision values. |

## Proposed minimal follow-up — not implemented

The pilot artifact source/composition must provide a real, valid artifact owner fence for each accepted output and the completion path must hold/check it with the BE1 facts fence before persisting acceptance. Likely touch points are `PilotFakeArtifacts` and the pilot artifact-fence composition in `pilot_composition.py`, plus focused tests. This is **outside Addendum 3's diagnostic-only allowlist**. No dummy/no-op fence, weakening of `_hold`, production edit, or approval change was made. Owner approval and a separate implementation scope are required before any fix.

## Optional step 6 and repository checks

- Route-surface comparison on clean HEAD: **NOT DETERMINED**. No external worktree was created because the checkout contains extensive unrelated dirty work and step 6 is optional.
- Re-run of the historical 37-passed PostgreSQL URL-guard group: **NOT RUN**; the exact saved command was not established. The URL guard was exercised only as a preflight for the fifth focused run.
- PostgreSQL suite beyond the single named node: **NOT RUN**.

| Command | Result |
| --- | --- |
| `& 'backend/.venv/Scripts/python.exe' tools/validate_harness.py` | `HARNESS_VALID`; exit 0. |
| `& 'backend/.venv/Scripts/python.exe' tools/validate_repository_security.py` | `REPOSITORY_SECURITY_VALID`; 6408 publishable files scanned; exit 0. |
| `& 'backend/.venv/Scripts/python.exe' tools/validate_architecture.py` | `ARCHITECTURE_VALID`; exit 0. |
| `git diff --check` | Exit 0; Git printed only existing CRLF-to-LF working-copy warnings for unrelated dirty docs/approval/status files. |
| `& 'backend/.venv/Scripts/python.exe' -m ruff check --no-cache --config backend/pyproject.toml --output-format concise backend/tests/integration/test_be1_synthetic_pilot_postgres.py` | Exit 1: one `I001` import-order finding at line 10, already present in the pre-existing dirty test file and reported by the prior Addendum 2 work. Not auto-fixed. |
| `& 'backend/.venv/Scripts/python.exe' -m ruff format --check --no-cache --config backend/pyproject.toml backend/tests/integration/test_be1_synthetic_pilot_postgres.py` | Exit 1: the whole pre-existing dirty file would be reformatted across existing URL-guard/setup sections and the diagnostic area. No whole-file formatting was applied to avoid unrelated changes. |
| `& 'backend/.venv/Scripts/python.exe' -m mypy --no-incremental --config-file backend/pyproject.toml backend/tests/integration/test_be1_synthetic_pilot_postgres.py` | **No type verdict**: mypy 1.20.2 raised an internal `OperationalError: unable to open database file` while initializing its cache. |
| `& 'backend/.venv/Scripts/python.exe' -m mypy --no-incremental --show-traceback --config-file backend/pyproject.toml backend/tests/integration/test_be1_synthetic_pilot_postgres.py` | Same cache-initialization failure; traceback ended in `OperationalError: unable to open database file`. |

No clean-HEAD route-surface test, DB suite, Alembic, Modal, GPU, provider, or external network check was run.

## Snapshot and review boundary

Snapshot: `.claude/handoff/snapshots/GB1_P2_STALE_CONTEXT_DIAGNOSTIC_20261104T141225/`. It contains byte copies of this plan, the scoped PostgreSQL test, and this report, plus a manifest with their SHA-256 hashes and checkout/status metadata. The report SHA-256 and manifest SHA-256 are supplied in the handoff response; the manifest also records the report hash. Earlier snapshots and reports were not changed.

**Disposition remains `XONG-CHƯA REVIEW`.** The diagnostic identified the immediate missing-fence condition but did not fix it. B1 P2 / Finding 2 remains unresolved; do not begin B2 from this report.
