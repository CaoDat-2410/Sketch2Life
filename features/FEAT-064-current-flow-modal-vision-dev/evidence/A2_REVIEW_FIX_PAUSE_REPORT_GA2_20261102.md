# GOAL A2 review-fix pause report — GA2

Status: **TẠM DỪNG / XONG-CHƯA REVIEW**. This is an implementation checkpoint only; A2 has not been independently reviewed or accepted.

## Authority and repository checkpoint

- Branch: `feature/feat063-be-foundation`; HEAD: `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58`; index empty.
- Pinned V4: `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`.
- Pinned Goal A2 REV2: `47CEA408AA9A4984C2EFD9E71A2EF0CDB2DF02C46E56FD7281086EBAE574AE10`.
- Pinned T2C plan: `1B1EB635FEA67D6EFCD19B3506F83538454D5A75012742F54B2CA0EA15086774`.
- Pinned T7b plan: `FDA943CE81C207F51616032A05AC1FB976934178A019BDCEF95DA73478A40C46`.
- Pinned fake-owner addendum: `E04F41D3F765C24DDB1E59A36ED2E24A0287A40AD8CC5FF1215B054287E15857`.
- Pinned review-fix plan: `BAF5E76B5E11F05F19DD1863BD0F8BBCDE981729F76C59B392CFD386A9A5B450`.
- No source/test change was made after the PostgreSQL teardown error. No stage, commit, push, merge, or Modal call occurred.

## Work present at pause

- `application/services/assistance.py`: recomputes typed-context revision from the canonical complete `ResolvedFacts` digest; supports passing an already-loaded assistance request and caller-supplied owner/source adapters so the owner-fence resolver can reuse its SQL connection.
- `be1_canvas_source_adapter.py`: exporter, artifact-loader, malformed callback, and field-access exceptions fail closed as unavailable; catches `Exception`, not `BaseException`.
- Unit regressions cover full-facts revision/digest changes after a member age/proof fact change, legacy compatibility, fake-owner scoped and no-scope behavior, and malformed/failing source callbacks.
- PostgreSQL test additions exercise a real SQL assistance repository, BE1 owner/source adapters, real `SqlAiJobRepository` and `AiJobService.create_job`, same-connection owner resolution, both authorization and BE1 fences, stale facts, lock timeout, and rollback.
- The `fakes.py` source is unchanged in this review-fix; its previously owner-approved scope behavior is covered by direct tests.

## Verification actually run

### Unit tests

Command from `backend/`:

```powershell
$env:PYTHONPATH='src'; & '.venv\Scripts\python.exe' -m pytest -q --tb=short -o addopts='' -o cache_dir="$env:TEMP\sketch2life-a2-reviewfix-stop-cache" --basetemp "$env:TEMP\sketch2life-a2-reviewfix-stop" tests/unit/test_assistance_t2c_adapters.py tests/unit/test_t2c_digest_pin.py
```

Result: **34 passed in 1.25s**, exit 0.

### PostgreSQL safety gate

The local T12 gate reported: readable approved connection file; database name matched `be1_acceptance`; URL host/query targets loopback-only; connection succeeded to PostgreSQL 17.11; 108 tables; 0 unknown tables; 0 unknown schemas. No URL or credential was printed. The first probe attempt had a script-only `AttributeError` before connection; the corrected probe produced the result above.

### PostgreSQL integration attempts

The first full module run collected 72 tests and ended **68 passed, 4 failed in 96.43s**, exit 1. All four new acceptance cases failed before reaching AI Jobs because `AssistanceService.submit()` calls `SqlAssistanceRepository.find_cache()`, which intentionally raises `NotImplementedError("cache is outside this pilot")`.

The test helper was then adjusted within the approved integration-test path to persist a request through the real SQL UoW after the real `_resolve_for()` path, avoiding the unsupported cache-read path without introducing a fake AssistanceRepository. The four focused acceptance tests then reported **4 passed plus 1 teardown error in 8.57s**, exit 1. The success case assertions passed, and the three stale/lock-timeout/rollback cases passed. Teardown failed with a foreign-key violation deleting `ai_jobs.job` while `ai_jobs.attempt` still referenced it. The generic fixture cleanup skips `attempt` because that table has no `organization_id`; the cleanup transaction therefore rolled back. Test-owned synthetic rows from the successful case may remain in the local acceptance database. They were not queried or manually deleted during this pause; reconcile them with a precisely scoped cleanup before another PostgreSQL run.

No schema/migration was applied, and no `DROP` or `TRUNCATE` was run.

### Static checks and validators

- Ruff check on the seven scoped source/test paths: **All checks passed!**, exit 0.
- Ruff format check on the seven paths: **1 file would be reformatted, 6 files already formatted**, exit 1. The sole file is `application/services/assistance.py`; the same file also failed format check in the copied pre-review baseline snapshot. No formatter changes were made to that source file.
- `python tools/validate_harness.py`: `HARNESS_VALID`, exit 0.
- `python tools/validate_repository_security.py`: `REPOSITORY_SECURITY_VALID`, 6,090 publishable files scanned, exit 0.
- `python tools/validate_architecture.py`: `ARCHITECTURE_VALID`, exit 0.
- `git diff --check`: clean, exit 0. This does not scan untracked files.
- Strict mypy and the pinned offline GA2 runner were **NOT RUN** during this pause. Earlier 396-pass offline evidence predates this review-fix and is not evidence for the current changes.

## Hash checkpoint

SHA-256 for current in-scope source/test files:

| Path | SHA-256 |
| --- | --- |
| `backend/src/sketch2life/application/services/assistance.py` | `B9D399E667FDE3C9A7FBF7EE4F5CA0B64EDF16D2247FD3D266E64502B1A9DAC7` |
| `backend/src/sketch2life/infrastructure/assistance/be1_owner_adapter.py` | `AF631BD9E7790F7BC17E2B10B1E8215FE97BA1049D77E0753CA85F875F61F233` |
| `backend/src/sketch2life/infrastructure/assistance/be1_canvas_source_adapter.py` | `8184ED5DA78657C49A190134ABCF916DAA745001C9B67DEED1FA6165D5FB8EF1` |
| `backend/src/sketch2life/infrastructure/assistance/fakes.py` | `E97A40AB5EEC4937BF1F9336162D731E4185F3A7B583DC16FAB11AAC636B71D5` |
| `backend/src/sketch2life/infrastructure/vision_analysis/resolved_facts_context.py` | `DED888FC460039C024AE2CE1555B30A438CD5BC0C966287D93EEFDC98C976FAA` |
| `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` | `9E1ECB029735273636FEF9CCB93BACFA0A9E5DB496BA72E6E23C67E8EDC21E35` |
| `backend/tests/unit/test_assistance_t2c_adapters.py` | `60E4BCF42B25F1DD47D1B57C74E920CE35BE5B7342A6AF33D5EFF795A66AB272` |
| `backend/tests/unit/test_t2c_digest_pin.py` | `E1AE9A2B3E32E30DA7348A873D1A318DDAEF6AE2AC3F9345D05790FD0968D4E7` |

Protected local hashes remain unchanged: SOURCE_REGISTER `0B43E4BA`; FEAT-063 CONTEXT `E7C8143A`; FEAT-063 STATUS `F1ADB793`; REMAINING_AI `8BBFD0ED`; REV36_DELTA `B61B0607`; VIDEO_FLOW `93374E96`; S1_DECISION_CARD `4D95D303`.

## Blocker and next handoff

The outstanding blocker is test-owned PostgreSQL cleanup ordering for `attempt` and `job`. Do not mark the real-SQL acceptance regression clean until teardown removes only its synthetic test rows without a foreign-key error. A2 remains **TẠM DỪNG / XONG-CHƯA REVIEW**, not independently accepted. No A2 work should resume until the owner changes priority; the next priority is the new Parent/Teacher flow.
