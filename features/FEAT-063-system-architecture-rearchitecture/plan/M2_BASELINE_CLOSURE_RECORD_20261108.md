# FEAT-063 M2 — Baseline Run Closure Record

**Status: DRAFT / NOT ACCEPTED.** This record reports an owner-run baseline. It does not accept the baseline, approve an S1a-T launch, or open another phase.

## 1. Provenance and pinned context

- Operator: owner-run on 2026-11-08. The coordinator read the captured files and source; it did not rerun any command or connect to a database.
- Baseline specification: `plan/M2_BASELINE_RUN_APPROVAL_FINAL_20261107.md`, SHA-256 `A671DBD85B9622CB754C5CECB807BBBBA2C920CD76F0A22ABBA44F4A12DC1A18`.
- Repository state observed during review: branch `feature/feat063-be-foundation`, HEAD `dd70685eae58aaaefea3e567f5c23d09345a8513`, index empty.
- All 17 source/test/tool hashes in baseline specification §2 matched when rechecked after the owner-run. No pin mismatch was found.
- This baseline was specified as offline and pre-S1a-T-code. These results are not an S1a-T implementation verdict.

## 2. C1 preflight results

| Check | Result | Evidence and qualification |
|---|---|---|
| C1(a) log/cache locations | PARTIAL | `.claude/handoff/logs/M2_BASELINE_RUN_20261107/` contains exactly 24 files: three files for each of the eight command prefixes. `tmp/M2_BASELINE_RUN_20261107/` exists and contains `mypy-cache/` and `ruff-cache/`. Both locations are ignored by Git. The `.claude/` directory at the repository root exists, holds the log directory above, and is ignored by Git. No `.claude/` directory exists one level above the repository root (`../.claude/`), where the exit files would have been written had the relative paths resolved against the wrong process directory. A whole-repository search found no additional matching run path in accessible locations, but could not certify global absence because the search reported access denied in unrelated historical `tmp/` and backend test directories. |
| C1(b) exit files and pytest result | PARTIAL — pytest has no verdict | All eight `.exit.txt` files contain integers. Pytest was invoked and its raw exit file contains `1`; however, `pytest.stdout.txt` ends after the failed node and has no complete aggregate line with passed/failed/skipped/errors and elapsed time. Under baseline specification §5, the pytest result is recorded as **NOT RUN / NO VERDICT**. The raw exit code is retained as data only. No passed-test count is inferred. |
| C1(c) pins and Git state | PASS | HEAD, branch and empty index matched the specification. All 17 §2 pins matched after the run. |
| C1(d) secret and access-indicator scan | PASS under the owner’s clarified rule | No database-URI, password, credential-assignment or token pattern was found in the 24 logs. The run-log set (`pytest.stdout/stderr`, validator stdout/stderr, `git-diff-check.stdout/stderr`, `mypy.stderr`, `ruff.stderr`) had no `psycopg`, `connection refused`, `socket`, `http client` or `alembic` hits. `ruff.stdout.txt` has such words only in Ruff code excerpts/import-diff suggestions: 9 `psycopg` occurrences, 9 `socket` occurrences, and 25 `alembic` occurrences (occurrence counts, not line counts); `mypy.stdout.txt` has none. Three non-credential HTTPS strings occur in static output: two mypy documentation references and one synthetic example endpoint in a Ruff source excerpt. They contain no userinfo, query, password or token and are not database connection URIs. These are recorded as keyword/URI scan matches, not evidence of a connection. The owner clarified that the Ruff/mypy source excerpts are not runtime-access evidence. |
| C1(e) command time ceilings | PARTIAL — timestamp estimates | File timestamps place the run between 13:34:40 and 13:44:28 (588 seconds total). Estimates for each command appear in §4. File timestamps do not prove exact process wall time. Mypy stdout stopped changing at 13:35:17, while its exit file was written at 13:42:44, a 447-second gap with no explanation in the logs. |
| C1(f) offline source assessment | PASS as static evidence only | Re-reading baseline specification §3 and the 11 selected test modules plus `backend/tests/conftest.py` found no call to production `get_settings()` or `create_app()`. `test_age_provenance_columns.py:82,98` configures `MigrationContext` with `as_sql=True` and a `StringIO` buffer. `test_synthetic_eligibility.py:641` defines a fake database-URL string; `_run()` injects a lambda settings loader, URL loader and fake store factory, and its tests assert the fake factory/store behavior. `test_vision_analysis_review_fixes.py:331,363,442,472` uses a fixture app with in-process `TestClient`. The source read supports the specified offline boundary; it is not runtime proof that no connection occurred. |

The 11 selected pytest modules are the exact list in baseline specification §3: `test_profile_age_invariant.py`, `test_be1_synthetic_pilot.py`, `test_age_provenance_columns.py`, `test_synthetic_eligibility.py`, `test_assistance_domain.py`, `test_assistance_service.py`, `test_be1_fact_reader.py`, `test_vision_analysis_service.py`, `test_vision_analysis_review_fixes.py`, `test_vision_context_domain.py` and `test_vision_context_service.py`.

## 3. Owner-run command records

The commands below were run by the owner using the command selection and capture scheme in specification §4. Cwd and executable are recorded from that specification. Logs are owner-run evidence read by the coordinator; they were not reproduced.

| Command | Cwd / executable | Exit | Timestamp estimate / ceiling |
|---|---|---:|---|
| `mypy --version` with `PYTHONPATH=src`, `MYPYPATH=src` | `backend` / `.venv/Scripts/mypy.exe` | 0 | About 11 s / 60 s |
| `mypy --package sketch2life --config-file pyproject.toml --strict --no-incremental --cache-dir ../tmp/M2_BASELINE_RUN_20261107/mypy-cache` | `backend` / `.venv/Scripts/mypy.exe` | 1 | At most 472 s by recorded start/exit timestamps / 900 s |
| `ruff check --select E,F,I,UP,B,SIM --cache-dir ../tmp/M2_BASELINE_RUN_20261107/ruff-cache src tests` | `backend` / `.venv/Scripts/ruff.exe` | 1 | About 2 s / 300 s |
| `pytest` with the exact 11 node paths listed in §2, `-p no:cacheprovider --basetemp ../tmp/M2_BASELINE_RUN_20261107/pytest -q` | `backend` / `.venv/Scripts/python.exe` | 1 | About 31 s / 1800 s; incomplete aggregate output, so no test verdict |
| `python tools/validate_harness.py` | repository root / `backend/.venv/Scripts/python.exe` | 0 | About 2 s / 300 s |
| `python tools/validate_repository_security.py` | repository root / `backend/.venv/Scripts/python.exe` | 0 | About 25 s / 300 s |
| `python tools/validate_architecture.py` | repository root / `backend/.venv/Scripts/python.exe` | 0 | About 1 s / 300 s |
| `git diff --check` | repository root / Git | 2 | About 1 s / 300 s |

Duration estimates use the creation/last-write times of redirected files and exit files, not a process timer. The mypy run began at 13:34:52 and its exit file was written at 13:42:44 (472 seconds). Its stdout last changed at 13:35:17; the remaining 447 seconds are unexplained. The time ceiling appears satisfied from these timestamps, but exact command wall time is not independently established.

### 3.1 Hashes of captured logs

Each row gives SHA-256 for the corresponding stdout, stderr and exit file. Empty stderr files have the standard SHA-256 shown below.

| Command prefix | stdout SHA-256 | stderr SHA-256 | exit SHA-256 |
|---|---|---|---|
| `mypy-version` | `8CAF0E5DD4A743E9B0768CADC27E18106AC9B95DD542BC1C630718DE77B6EDD6` | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` | `5FECEB66FFC86F38D952786C6D696C79C2DBC239DD4E91B46729D73A27FB57E9` |
| `mypy` | `21BB93E81BC15DFCC6F391D23B67E5393A147D88A7515447D3F5018E8B1B82ED` | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` | `6B86B273FF34FCE19D6B804EFF5A3F5747ADA4EAA22F1D49C01E52DDB7875B4B` |
| `ruff` | `9A134AD89BF8FE4E353BFE6F01A55DE0E8E3DD0A41831118A109C9BE5B61AE65` | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` | `6B86B273FF34FCE19D6B804EFF5A3F5747ADA4EAA22F1D49C01E52DDB7875B4B` |
| `pytest` | `9704CC62A1B506BEAB63A5DAAFE3D9FE3DF3D859ADFCF78C0AE19B7E7A0EBF2C` | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` | `6B86B273FF34FCE19D6B804EFF5A3F5747ADA4EAA22F1D49C01E52DDB7875B4B` |
| `validate-harness` | `E4A0E355C8F2077E3E189D523894697E42EA4ADABF31FDC4ED0FC42FAC46181B` | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` | `5FECEB66FFC86F38D952786C6D696C79C2DBC239DD4E91B46729D73A27FB57E9` |
| `validate-repository-security` | `62196ED6D7B3107379EF18535070D62BC737D19018BEB988079756EF06FCBE26` | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` | `5FECEB66FFC86F38D952786C6D696C79C2DBC239DD4E91B46729D73A27FB57E9` |
| `validate-architecture` | `67F1BC538FC90B4F70000A89126DDE0AA14C688B8C3DBBA796E1A89D6CAEF80E` | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` | `5FECEB66FFC86F38D952786C6D696C79C2DBC239DD4E91B46729D73A27FB57E9` |
| `git-diff-check` | `6E3D7E605C5DC1766F10BDF2CF30A632FFA5AA2960889F77E0788E801AD1CA5A` | `7C84F4F2BAC8844B625D18EA5C0DBD853E99373B378CDA57F6F5E6BD2A82D25F` | `D4735E3A265E16EEE03F59718B9B5D03019C07D8B6C51F90DA3A666EEC13AB35` |

### 3.2 Raw result summaries

- `mypy --version`: `mypy 1.20.2 (compiled: yes)`; exit 0.
- Strict mypy: `Found 255 errors in 50 files (checked 579 source files)`; exit 1. This is baseline data, not PASS.
- Ruff: `Found 202 errors.`; exit 1. This is baseline data, not PASS.
- Pytest stdout contains the failure heading and node below, but no complete final aggregate line:

  ```text
  FAILED tests/unit/test_synthetic_eligibility.py::test_head_counts_by_both_methods_match_the_derived_expectation
  E       AssertionError: assert 28 == 25
  ```

  The recorded node is `tests/unit/test_synthetic_eligibility.py::test_head_counts_by_both_methods_match_the_derived_expectation`. The progress output has 560 dots and one `F` marker (561 progress markers in total); this is unofficial progress output and is not used to infer any pass count. Do not rerun under this record.
- The three validators each wrote a valid marker and exit 0: `HARNESS_VALID`; `REPOSITORY_SECURITY_VALID` with `publishable_files_scanned=6596`; `ARCHITECTURE_VALID`.
- `git diff --check` wrote `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md:908: new blank line at EOF.` and exited 2. The owner reports this blank-EOF condition was already present before this baseline run, from the Baseline approval entry appended earlier that day. The log proves the condition at run time; the earlier existence is owner-reported. Keep it visible and do not worsen it in any later append.

## 4. Stop-gate sequence and file-write overlap

The pytest output lacked the required final aggregate summary. After that, the owner ran the three validators and `git diff --check`; baseline specification §5 treats the missing pytest summary as a stop condition. This sequence deviation is recorded. Validator exit 0 values do not replace the missing pytest verdict.

Recorded file times show the baseline log span was 13:34:40–13:44:28. `DECISIONS.md` was last written at 13:29:01, before the run. During the run, the R3 launcher was last written at 13:38:49, the R3 specification at 13:42:48 and the R3 launch instruction at 13:43:01. The 17 baseline §2 source/test/tool pins still matched after the run. This is a timing/coordination deviation to disclose, not a pin mismatch.

## 5. Limits and owner decision

- No database, migration or network command was run by the coordinator. The source assessment is static evidence and must not be described as proof of runtime behavior.
- Pytest has no official aggregate verdict; record it as NOT RUN / NO VERDICT for acceptance purposes. Do not infer passed tests from the progress line and do not rerun it under this record.
- Mypy and Ruff returned nonzero baseline results; neither is PASS. Validator exit 0 outputs are recorded separately and occurred after the pytest stop condition.
- The whole-repository search for extra baseline artifacts was incomplete because of access-denied locations; no absence claim is made for those unreadable directories.
- This record remains **DRAFT / NOT ACCEPTED**. Only the owner may accept it. No Baseline Closure Acceptance entry, S1a-T launch, S1a-P, or later phase is approved here. `OWNER_MODAL_CALL_APPROVED=NO` remains unchanged.

### Owner review

Owner decision: ______________________________

Date: ____________________

## Owner disposition — narrow fake URI fixture exemption (2026-11-08)

The owner authorizes a narrow classification exemption for URI-shaped strings using the `_PROBE` placeholder in `backend/tests/unit/test_synthetic_eligibility.py` lines 641, 728–732, 745–749 and 782; separately, `backend/tests/unit/test_be1_fact_reader.py` line 255 is an intentionally fake URI-shaped parameter value in `pytest.mark.parametrize` for `test_reader_fails_closed_without_leaking_source_errors` (lines 252–272). This line does not use `_PROBE`. The owner reports reading lines 252–272 and confirms its fake host/password fields occur only three times in that file and exercise the assertion that source error text is not copied into rendered output (line 272). The reviewer may record these exact occurrences as fake test fixtures and redact their values. This does not exempt any other source file, log, document, or approval entry. Any URI, password or token outside these exact locations remains a stop condition; if found, stop and ask the owner. No credential value is reproduced here.

The owner reports independently scanning all URI-scheme-marker strings in the 24 baseline logs. Apart from the three HTTPS strings listed below, the owner found no other URLs and no URL containing a user-info credential component. The coordinator's scan found no database-connection URI, credential-bearing URI, password or token. The three non-credential HTTPS strings are separately exempted in the “exact generic HTTPS log-string exemption” section below. This does not make an unqualified claim that the logs contain no URI.

## Owner disposition — exact generic HTTPS log-string exemption (2026-11-08)

The owner confirms that the three generic HTTPS strings identified in baseline diagnostics are noncredential documentation/example text and permits only these exact occurrences for this review: `mypy.stdout.txt` lines 58 and 68 (documentation references), and `ruff.stdout.txt` line 4481 (a synthetic example endpoint in a source excerpt). Their values remain redacted and are not copied here.

This exemption is limited to those three occurrences in the baseline logs. It does not apply to other URI-shaped strings or to passwords/tokens in any file. Any other such finding remains a stop condition; report only its file, line and category, redact its value, and ask the owner before continuing. This owner decision supersedes the preceding note that treatment of these three strings was unresolved.

## Owner disposition — exact mypy-cache URI-like occurrences (2026-11-08)

The owner reports scanning all 25 files under `tmp/M2_BASELINE_RUN_20261107/` and finding exactly 11 scheme-marked string occurrences, all HTTPS: one in `mypy-cache/CACHEDIR.TAG` (host `bford.info`) and ten in `mypy-cache/3.12/cache.db` (two `docs.pydantic.dev`, two `mypy.readthedocs.io`, six `fastapi.tiangolo.com`). Full values are not reproduced. The owner reports no user-info credential component, PostgreSQL URI, credential-bearing URI, password or token in this directory. This is owner-reported evidence; it does not establish that network access occurred or did not occur.

The independent reviewer identified the occurrences at `tmp/M2_BASELINE_RUN_20261107/mypy-cache/CACHEDIR.TAG:3` and `tmp/M2_BASELINE_RUN_20261107/mypy-cache/3.12/cache.db` lines 4714, 4716, 12127, 13348, 13766, 13910 and 13917, with multiple occurrences at line 12127. The owner grants a narrow exemption for exactly these 11 occurrences in those two files for this review only. This does not exempt any other URI in cache files, any baseline log beyond the three previously listed HTTPS strings, any new document, or any URI/password/token with credential information. Any other finding remains a stop condition; redact its value and ask the owner.

These are URI-like strings in mypy cache data, not evidence of a network request or proof that no network request occurred.