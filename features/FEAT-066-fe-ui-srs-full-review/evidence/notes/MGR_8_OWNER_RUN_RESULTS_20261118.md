# MGR-8 owner-run results — 2026-11-18

**Status: NOT VERIFIED (pending owner disposition).** This note records the owner-run D2 and D3 diagnostics, the approved fixture amendment, and the owner-run D3 re-run. It does not decide whether MGR-8 is satisfied; the owner does.

Earlier records, unchanged by this note:

- `MGR_8_IMPLEMENTATION_VERIFICATION_20261118.md`: first attempt (Codex), interrupted.
- `MGR_8_DIAGNOSTIC_RUN_20261118.md`: diagnostic (Codex). D1 = 8 passed (exit 0); D2 stalled inside the Codex sandbox; D3 not run.

## Environment

- Worktree `.worktrees/manager-api`, branch `feature/feat066-manager-api-contracts`, HEAD `1c9148e88600a101887e477541c4c4893ba1c7df` (= `origin/dev`). 0 staged paths.
- All runs below were made by the owner in their own terminal, outside the Codex sandbox. The Codex sandbox hangs on loopback sockets (Starlette `TestClient` → asyncio self-pipe `socket.accept`), so `TestClient` and database tests are not run there.
- Interpreter (from the log headers): root `backend/.venv`, Python 3.12.10, pytest 8.4.2, rootdir the worktree `backend`. `PYTHONPATH=src`. This venv is not lock-exact (FastAPI 0.141.1 against `uv.lock` 0.162.0).
- Database: the owner-prepared disposable local `s2l_be1_acceptance` (container `s2l-be1-acceptance`, port 5434, `upgrade heads` applied). No database URL appears in any log: a scan of `d3-r2.txt` found no `postgresql` or `5434` string.

## D2 — `tests/contract/test_openapi_contract_catalog.py` (owner-run)

- **Result:** 2 passed, 1 failed in 4.42 s; `exit-codes.txt` records `D2=1`.
- **Failure:** `test_runtime_openapi_matches_all_mounted_rev37_operations_and_records_unmounted_candidates`, `KeyError: 'description'` at test line 332.
- **Cause (read from source and a read-only probe, not by a fix-and-rerun):** `dev` `interfaces/http/app.py` (about lines 1104–1115) sets an operation's `description` only when it finds a matching handler in `application.routes`. With the installed FastAPI, included routers appear as `_IncludedRouter` objects, so 130 of 134 catalogued operations get no description. The probe gave the same result with FastAPI 0.141.1 (root venv) and 0.162.0 (lock-exact `tmp/m2-s2-mapper-env/.venv`).
- **Attribution:** this code is pre-existing on `dev` and is not touched by MGR-7. The M2 branch commit `be5af631` removed the gate (`833df677` `app.py` line 276). That is not verified on a merged base.
- **Effect on MGR-8:** the MGR-7 catalog assertions are in the same test (hunk from line 460) and were never reached. **The MGR-7 catalog/OpenAPI change has no runtime test result.**
- **Not re-run.** The owner has not decided between waiting for M2 to reach `dev` (O-0), porting the `app.py` fix (outside the six-file allowlist, needs its own approval), or accepting the limitation.

## D3 — `tests/integration/lesson_library/test_lesson_library_api.py` (owner-run, before amendment)

- **Result:** 6 failed, 1 passed in 19.21 s; `D3=1`.
- **Failures:** all six with HTTP 403 `ACCOUNT_SCOPE_UNAVAILABLE`. The one pass was the storage-example test.
- **Cause:** the fixture created `AdultIdentityModel` rows without `account_role`. Three gates refuse such accounts:
  - `routers/be1_common.py` lines 90–114 (since `800c8e9f`, 2026-11-10) require `school_manager` or `teacher`.
  - `routers/lesson_library.py` line 124 requires `parent`.
  - `routers/lesson_library.py` line 138 requires `platform_admin`.
- **Attribution:** the fixture predates these gates. MGR-7 did not touch it, and the M2 branch does not fix it.

## Scope amendment and fixture edit

- **Owner approval in chat:** "Approve the fix". It is recorded as an appended paragraph, "Scope amendment, 2026-11-18 (MGR-8 fixture)", in `approvals/TASK_APPROVAL.md`.
  - Pre-append: 38,982 B, SHA-256 `5272BA9768407FFF04BD8414F1536DEFE1E8C8FBC0C5EF0596513CEA0BA6CCB3`.
  - Post-append: 40,237 B, SHA-256 `F16D0288784093F9F6E478721AEF944A83493E1BE340E5F7BE2987E168E21318`.
  - The prefix was byte-identical after the append; the file is LF only.
- **Edit:** only the fixture loop that creates the four synthetic adults now passes `account_role`:
  - teacher → `teacher`
  - manager → `school_manager`
  - parent → `parent`
  - platform admin → `platform_admin`

  `role_revision` is left at the model default of 1. No assertion or other line changed.
- **New pin** of `backend/tests/integration/lesson_library/test_lesson_library_api.py`: 48,381 B, SHA-256 `13EFCC2A277188A0A41FBF17B2B841DA1ECD74DAB51ED1B19D8386E9B1174563` (was 48,196 B / `BD0FEE18…`).

## D3-R2 — same file, after the amendment (owner-run)

The command was given to the owner and run by the owner. It used the root `backend/.venv` interpreter, `PYTHONPATH=src`, `PYTHONUNBUFFERED=1`, `BE1_TEST_DATABASE_URL` set to the disposable database, and these pytest flags: `-X faulthandler -m pytest -p no:cacheprovider -vv --durations=20 -o faulthandler_timeout=120`.

- **Result:** 6 passed, 1 failed, 7 warnings in 25.88 s; `exit-codes-r2.txt` records `D3R2=1`.
- **Passed:**
  - `test_teacher_lesson_crud_revision_guards_and_organization_scope`
  - `test_manager_public_review_parent_read_export_moderation_and_revocation`
  - `test_direct_parent_and_group_sharing_can_be_accepted_then_revoked`
  - `test_local_storage_example_upload_download_and_delete_routes`
  - `test_parent_group_accept_replays_legacy_receipt_without_repeating_effects`. MGR-7 changed this test's conflicting-retry assertion to HTTP 400 with `INVALID_IDEMPOTENCY_KEY` (line 1061).
  - `test_manager_list_routes_default_to_25_and_preserve_limit_and_cursor_inputs`. This is the new MGR-7 test.
- **Failed:** `test_teacher_uploads_and_reviews_a_synthetic_pdf_through_http`, at test line 594. The upload-complete call returned 503 `DEPENDENCY_UNAVAILABLE`, "Security scanning is temporarily unavailable".
  - The fixture wires a real `ClamAvScanner` at `127.0.0.1:3310`, and no ClamAV daemon answered there.
  - MGR-7 has no hunk in this test: its hunks are the import at line 35, this amendment's fixture lines, and the block from line 1060.
  - Whether a ClamAV service was running was not checked; no Docker or service command was run.
- **Warnings:** 7 × SQLAlchemy `SAWarning` about the table cycle `parent.child_profiles` ↔ `parent.profile_revisions` during fixture teardown (test line 221). They are not related to MGR-7.

## Summary against the MGR-7 behaviors

| MGR-7 behavior | Runtime evidence | State |
|---|---|---|
| Parent Groups and access-grants lists default to 25, max 100, cursors kept | D3-R2 `test_manager_list_routes_default_to_25_…` PASSED | covered |
| Same-key/different-payload reuse returns 400 `INVALID_IDEMPOTENCY_KEY`; same-payload replay kept | D3-R2 `test_parent_group_accept_replays_…` PASSED; D1 unit `test_reused_key_with_different_fingerprint_is_invalid_idempotency_key` PASSED | covered |
| Legacy receipt compatibility (unit) | D1 8 passed (Codex diagnostic) | covered |
| Static OpenAPI catalog alignment | D2 stops at line 332, before the MGR-7 assertions | **not covered** (pre-existing `dev` blocker) |
| Teacher PDF upload/review flow (not changed by MGR-7) | D3-R2 failed: ClamAV not reachable | environment-dependent, not attributed to MGR-7 |

## Artifacts

All under `tmp/feat066-phase-a/mgr8-owner/` (git-ignored):

| File | Bytes | SHA-256 |
|---|---:|---|
| d2.txt (UTF-16) | 13468 | 7430271EA19A0FD22DE694B1EE6E89007729F8F78B5F029E2A53B1362466AB3B |
| d3.txt (UTF-16) | 41878 | 426A4A814C4B00618E882CA4CA0527A248183F18FD7179139CD0F6C391922EAB |
| exit-codes.txt | 27 | C836F0C03BCC50607F69AAF33AA461BC942DD1A3FCBCBFD96A87C44C62E228F3 |
| d3-r2.txt (UTF-16) | 20070 | 785DCC3523C88C882BDE61A3A719789FE25D8C2320190AB902B9DD622BDA2ACF |
| exit-codes-r2.txt | 8 | D129FA798E7A17A918FA90FE683EC1E0F889AFA372602E488927FB0B0E441683 |

The coordinator's D2 analysis and read-only probes are in `tmp/feat066-phase-a/mgr8-probe/`.

## Source and test pins at the time of this note

| File | Bytes | SHA-256 |
|---|---:|---|
| backend/src/sketch2life/interfaces/http/routers/lesson_library.py | 28784 | 732DB7C469B9900C94A8B85E92A530934A346AA3BABE4D88C4CB61358DFC9400 |
| backend/src/sketch2life/infrastructure/lesson_library/service.py | 91447 | F37DB928B3C7CA5115A537D9E82D740D4BF9B23F34C02A0CBEE3C30BB995255D |
| backend/src/sketch2life/interfaces/http/openapi_contract.py | 1379096 | 35801B20DC67630B9AAEEFDD46F82886CD91F34990BA2CCE6C2B3E67B6A989B7 |
| backend/tests/integration/lesson_library/test_lesson_library_api.py | 48381 | 13EFCC2A277188A0A41FBF17B2B841DA1ECD74DAB51ED1B19D8386E9B1174563 |
| backend/tests/unit/test_lesson_library_receipt_compatibility.py | 8798 | B2DAFF304574DB55ABA438783567BAE2EE9F5BEE1237A3F2CF3FF6F3CD384E5C |
| backend/tests/contract/test_openapi_contract_catalog.py | 21114 | 7D242528CC5BD3AACDE5EF2C1106B734B710D67E8D88C33AEB2A14D2237D428B |

## Limits

- Each run happened once, on one machine, with a non-lock-exact interpreter.
- D2 was not re-run after the amendment.
- No validator, lint, type check, build, OpenAPI generation, Docker or ClamAV command was run.
- Whether D1 + D2 + D3-R2, with the catalog gap and the ClamAV-dependent failure, count as the MGR-8 verification is the owner's decision.

## Owner disposition — 2026-11-18

Source: relayed by the coordinating BE session. The owner's instruction, verbatim: "Theo SRS và đề xuất cho tôi sau đó đưa câu trả lời cho phiên đó đi". The coordinator proposed the answers below against the SRS, and the owner told it to send them. This session recorded them and checked the SRS line citations read-only. The canonical copy is at the root checkout, `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 B, SHA-256 prefix `B9B1F42D`, per D-209. The worktree's copy of that path is an older one (553,948 B, SHA-256 prefix `70DA43A3`), and the cited line numbers do not apply to it.

**Q1 — Do D1 + D2 + D3-R2 count as the MGR-8 verification? Not as a full verification.** MGR-8 is recorded as **PARTIAL — runtime behaviour verified, catalog pending**.

- **Runtime behaviour: verified.** D1: 8 unit tests passed. D3-R2: 6 of 7 passed, covering both MGR-7 behaviours.
  - Lists default to 25 with a maximum of 100: SRS §21.1, line 1640.
  - Reusing a key with a different payload returns `INVALID_IDEMPOTENCY_KEY`: SRS §21.4, line 1697. The test asserts HTTP 400.
- **Environment limit, accepted:** the teacher PDF upload test returned 503 `DEPENDENCY_UNAVAILABLE` because ClamAV was not running at 127.0.0.1:3310. That test is outside the MGR-7 change. Optionally, the owner starts a ClamAV container before the next run.
- **Catalog: not verified.** The MGR-7 catalog change in `openapi_contract.py` (the `limit` text and the 400 responses) has no passing test, because the MGR-7 assertions from line 460 were never reached. SRS §9.6, line 818, requires the target API (path, schema, error enum, idempotency) to be reconciled with the current OpenAPI. The catalog change therefore must not be committed unverified.

**Q2 — D2 direction: (a), wait for M2 on `dev`.**

- Not (b), porting the `app.py` fix: M2 commit `be5af631` already removes the description gate, so a port would duplicate it and conflict when M2 merges.
- Not (c), accepting the limit, for the §9.6 reason above.

**Next steps, each only on the owner's word:**

1. M2 reaches `dev` (O-0).
2. S-LL is brought onto that base.
3. The owner re-runs D2 and D3 in their own terminal.
4. If both pass, an independent evidence review runs on Sonnet 5.5, high effort.
5. Then one S-LL commit is proposed.

**State:** MGR-8 is PARTIAL and not fully VERIFIED. There is no S-LL commit until the steps above are done. No independent review was run, and nothing was staged, committed or pushed.
