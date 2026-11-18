# MGR-8 verification — owner-run on the consolidated M2 branch (2026-11-18)

- **Result:** MGR-8 is **VERIFIED**, with one environment limit: the Lesson Library PDF upload test needs ClamAV. MGR-7 does not change that flow.
- **Owner decision** (in chat, 2026-11-18): "R ok verified làm bước 5 đi". This followed the coordinator's recommendation and the owner's question "Có cần thiết k ?" about a ClamAV re-run. The coordinator answered that it is not needed for MGR-8. ClamAV becomes a prerequisite in the Teacher C-T slice, the L5 Bruno upload runs and Phase D.
- **Supersedes the MGR-8 status of earlier notes** (none edited):
  - `MGR_8_IMPLEMENTATION_VERIFICATION_20261118.md`: first Codex run, interrupted;
  - `MGR_8_DIAGNOSTIC_RUN_20261118.md`: Codex diagnostic; D2 hung in the Codex sandbox;
  - `MGR_8_OWNER_RUN_RESULTS_20261118.md`: PARTIAL, catalog pending.

## Base and placement

The owner approved a consolidation plan. Under it, the S-LL work moved from the `.worktrees/manager-api` worktree to the root checkout, on the M2 branch `feature/feat063-m2-parent-teacher-foundation`.

- **Step 1:** commit `b95fed64` (Bruno and FEAT-081 records).
- **Step 2:** merge commit `b93d7334ecb0dba6e5b0ababe57171a71b8a50b7`. It merges `feature/feat066-manager-api-contracts` (`dev` `1c9148e8` plus the FEAT-066 Phase A commit `9ceaf6cf`) into the M2 branch at `833df677`. The only conflict was `.gitattributes`, resolved by keeping both blocks.
- **Step 3:** the uncommitted S-LL diff was exported from the manager-api worktree as a patch and applied with `git apply --3way`. It applied cleanly, uncommitted.
- **Byte check after the transfer:**
  - These files are byte-identical to their manager-api versions: the five MGR-7 source and test files other than the catalog test, the FEAT-066 `CONTEXT.md`, `STATUS.md` and `TASK_APPROVAL.md`, and the three earlier `MGR_8_*` notes.
  - The catalog test differs, as expected, because it now combines the M2 changes and the MGR-7 changes.
- **No migration or dependency change:** `backend/alembic`, `pyproject.toml` and `uv.lock` are the same as on `dev` `1c9148e8`. The existing disposable database therefore applies.

**Pins at the run (root working tree):**

| File | Bytes | SHA-256 |
|---|---:|---|
| `backend/src/sketch2life/interfaces/http/routers/lesson_library.py` | 28,784 | `732DB7C469B9900C94A8B85E92A530934A346AA3BABE4D88C4CB61358DFC9400` |
| `backend/src/sketch2life/infrastructure/lesson_library/service.py` | 91,447 | `F37DB928B3C7CA5115A537D9E82D740D4BF9B23F34C02A0CBEE3C30BB995255D` |
| `backend/src/sketch2life/interfaces/http/openapi_contract.py` | 1,379,096 | `35801B20DC67630B9AAEEFDD46F82886CD91F34990BA2CCE6C2B3E67B6A989B7` |
| `backend/tests/integration/lesson_library/test_lesson_library_api.py` (includes the approved `account_role` fixture amendment) | 48,381 | `13EFCC2A277188A0A41FBF17B2B841DA1ECD74DAB51ED1B19D8386E9B1174563` |
| `backend/tests/unit/test_lesson_library_receipt_compatibility.py` | 8,798 | `B2DAFF304574DB55ABA438783567BAE2EE9F5BEE1237A3F2CF3FF6F3CD384E5C` |
| `backend/tests/contract/test_openapi_contract_catalog.py` (M2 + MGR-7) | 23,667 | `B7CF9F8CB6E05D3E584E6D95FBC9D221441448C530A2F0A596754ABB1AAB0CF0` |
| `backend/src/sketch2life/interfaces/http/app.py` (M2 + `dev`, auto-merged; not an MGR-7 file) | 74,569 | `1387A59354DCCED45A74872721E3BA9ECEDEDE8CC44DE43A1BF33CBEDDCCC439` |
| `backend/tests/contract/test_app_composition.py` (auto-merged; not an MGR-7 file) | 13,755 | `E18FA7478B0C7CB0D7369D3089CB07F139F7AE2670C7865AC4098480D61505B2` |

## Run

- **Who ran it:** the owner, in their own terminal, outside the Codex sandbox, at 2026-11-18 about 17:25.
- **Interpreter:** root `backend/.venv` Python, with `PYTHONPATH=src` and `PYTHONUNBUFFERED=1`.
- **Database:** the disposable local `be1_acceptance` database (container on loopback, `upgrade heads` applied). The URL is not recorded.
- **Command form for each file:** `python -X faulthandler -m pytest -p no:cacheprovider -o addopts="" -vv -s --durations=20 -o faulthandler_timeout=120 <file>`.

| Run | Test file | Exit | Result |
|---|---|---:|---|
| d1 | `tests/unit/test_lesson_library_receipt_compatibility.py` | 0 | 8 passed (0.74 s) — includes the same-key/different-payload → `INVALID_IDEMPOTENCY_KEY` case |
| d2 | `tests/contract/test_openapi_contract_catalog.py` | 0 | **5 passed** (7.47 s). The MGR-7 catalog assertions are reached and pass, together with the M2 description fix |
| d3 | `tests/integration/lesson_library/test_lesson_library_api.py` | 1 | 6 passed, 1 failed (22.58 s). Passed: `test_manager_list_routes_default_to_25_and_preserve_limit_and_cursor_inputs`, `test_parent_group_accept_replays_legacy_receipt_without_repeating_effects`, CRUD, sharing, moderation, storage. Failed: `test_teacher_uploads_and_reviews_a_synthetic_pdf_through_http` → 503 `DEPENDENCY_UNAVAILABLE` ("Security scanning is temporarily unavailable"), because ClamAV is not running at 127.0.0.1:3310 |
| comp | `tests/contract/test_app_composition.py` | 0 | 7 passed (5.14 s) — the auto-merged `app.py` composes as before |

**Logs** (git-ignored, local; UTF-16 from PowerShell `Tee-Object`; they contain no database URL):

| File under `tmp/feat066-phase-a/root-run/` | Bytes | SHA-256 |
|---|---:|---|
| `d1.txt` | 12,830 | `88C8882D0AC380876C6E68F646C349AFA214F12AD9EAB79711361531C95FCE7E` |
| `d2.txt` | 6,414 | `9F8B9A4DAF190774003456AF5EA9580164A70D62FDFCD65AFAA671A2A1FBB6C2` |
| `d3.txt` | 20,364 | `B9C1708F63CD4143045171BBC44811CC6539F025A8E5833453650E668DB9A89B` |
| `comp.txt` | 7,526 | `0ECAC0C1F96C221A30D5BD20E7FA42D8B9C8317A68A4BA8C916ED9D21734D4B1` |
| `exit-codes.txt` | 31 | `74A2991635A49CE6545DDAB094E48AAB65C8559F204129A791EE357C758D5609` |

## MGR-7 behaviours and their evidence

| MGR-7 behaviour (SRS) | Evidence |
|---|---|
| Parent Groups and access-grants lists default to 25, maximum 100 (§21.1 line 1640) | d3 `test_manager_list_routes_default_to_25_…` passed; d2 catalog assertions passed |
| Same key with a different payload → HTTP 400 `INVALID_IDEMPOTENCY_KEY` (§21.4 line 1697) | d1 `test_reused_key_with_different_fingerprint_is_invalid_idempotency_key` passed; d3 receipt-replay test passed; d2 catalog 400 responses passed |
| Catalog and OpenAPI reflect both (§9.6 line 818 reconciliation) | d2 5/5 passed |

## Limits

- One run, on one machine, against a local throwaway database.
- The PDF upload test was not run with ClamAV. That is an environment limit outside the MGR-7 change.
- No validators, lint or type checks were part of this verification run.
- `app.py` and `test_app_composition.py` come from the merge, not from MGR-7. They were exercised by d2 and comp.
- This note authorizes no commit or push. The S-LL commit needs the owner's word.
