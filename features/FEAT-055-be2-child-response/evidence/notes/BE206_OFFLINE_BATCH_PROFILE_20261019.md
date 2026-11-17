# BE2-06 final offline batch profile — 2026-10-19

Status: **PREPARED / NOT_RUN by this note's author**. Execute once after all 06 source/tests
are final, then bind actual outcomes to that exact snapshot. Development checks may be focused;
do not present earlier 01–05 receipts or this path inventory as a new passing batch.

## Existing environment and scope

Use the existing shared `backend/.venv/Scripts/python.exe` from the repository root, with
imports pinned to this task worktree's `backend/src`; do not install dependencies. The executor
reports CPython 3.12.10 / pytest 8.4.2 / pydantic 2.13.4 / Ruff 0.16.4 / mypy 1.20.2.
Pillow is unavailable. Record these versions again in the actual receipt; they are an
environment inventory, not evidence of test completion. `backend/pyproject.toml` requires
Python >=3.12,<3.14 and sets pytest's `pythonpath=["src"]`.

Select these **44 existing 01–05 files**, plus the **six planned 06 files** below (50 total if
the final inventory is unchanged). These are component/fake contract tests; no integration,
E2E, provider, model, DB, Redis or Docker suite is selected.

| Group | Paths/globs, relative to `backend/` | Existing files |
|---|---|---:|
| 01 foundation | `tests/unit/test_ai_job_*.py`; `tests/contract/test_ai_job_contracts.py`; `tests/contract/test_ai_job_polling.py` | 11 |
| 02 Vision C1/C2 | `tests/unit/test_vision_analysis_*.py`; `tests/unit/test_vision_context_*.py`; `tests/contract/test_analysis_result_contracts.py`; `tests/contract/test_analysis_corrections_api.py`; `tests/contract/test_vision_context_contracts.py`; `tests/contract/test_h_ai_review_handoff_examples.py` | 12 |
| 03 orchestration | `tests/unit/test_assistance_*.py`; `tests/contract/test_assistance_request_contracts.py`; `tests/contract/test_assistance_requests_api.py` | 8 |
| 04 generation | `tests/unit/test_sketch_generation_*.py`; `tests/unit/test_sketch_proposal_domain.py`; `tests/contract/test_sketch_proposal_contracts.py` | 6 |
| 05 review | `tests/unit/test_sketch_review_*.py`; `tests/contract/test_sketch_review_contracts.py` | 7 |
| 06 response, reserved by executor | `tests/unit/test_child_response_domain.py`, `test_child_response_adapters.py`, `test_child_response_service.py`, `test_child_response_chain.py`, `test_child_response_races.py`; `tests/contract/test_child_responses.py` | Planned; verify all six exist before execution |

The globs were checked against actual current files, not a hypothetical suite name. Expand and
record the final sorted paths before running; require all six 06 files, do not silently drop
missing files. Each 06 unit filename in the final row is under `tests/unit/`.

Source selection: FEAT-049 `evidence/metrics/A1_CODEX_FINAL_REVIEW_20261017.json`
(`root_pytest.paths`) and FEAT-048 `evidence/metrics/C2_IMPLEMENTATION_CHECKS_20261017.json`
(C1/C2/foundation groups); actual 04/05 test tree and FEAT-052
`evidence/notes/BE205_CODEX_REREVIEW_20261019.md`. Historical test totals are not expected
totals for a changed 06 snapshot.

## Concrete invocation template

Run from this task worktree's root. This is a **future invocation**, not an executed command.
It expands PowerShell wildcards before passing paths to pytest and uses a fresh feature-local
output directory. The root directory derivation assumes the documented `.worktrees/<task>` layout.

```powershell
$be206SharedRoot = Split-Path (Split-Path (Get-Location).Path -Parent) -Parent
$be206Python = Join-Path $be206SharedRoot 'backend\.venv\Scripts\python.exe'
$env:PYTHONPATH = (Resolve-Path 'backend\src').Path
$be206Patterns = @(
  'backend/tests/unit/test_ai_job_*.py',
  'backend/tests/unit/test_vision_analysis_*.py',
  'backend/tests/unit/test_vision_context_*.py',
  'backend/tests/unit/test_assistance_*.py',
  'backend/tests/unit/test_sketch_generation_*.py',
  'backend/tests/unit/test_sketch_review_*.py'
)
$be206Explicit = @(
  'backend/tests/unit/test_sketch_proposal_domain.py',
  'backend/tests/contract/test_ai_job_contracts.py',
  'backend/tests/contract/test_ai_job_polling.py',
  'backend/tests/contract/test_analysis_result_contracts.py',
  'backend/tests/contract/test_analysis_corrections_api.py',
  'backend/tests/contract/test_vision_context_contracts.py',
  'backend/tests/contract/test_h_ai_review_handoff_examples.py',
  'backend/tests/contract/test_assistance_request_contracts.py',
  'backend/tests/contract/test_assistance_requests_api.py',
  'backend/tests/contract/test_sketch_proposal_contracts.py',
  'backend/tests/contract/test_sketch_review_contracts.py',
  'backend/tests/unit/test_child_response_domain.py',
  'backend/tests/unit/test_child_response_adapters.py',
  'backend/tests/unit/test_child_response_service.py',
  'backend/tests/unit/test_child_response_chain.py',
  'backend/tests/unit/test_child_response_races.py',
  'backend/tests/contract/test_child_responses.py'
)
$be206Suite = @(
  foreach ($be206Pattern in $be206Patterns) {
    $be206Matches = @(Get-Item -Path $be206Pattern -ErrorAction Stop)
    if ($be206Matches.Count -eq 0) { throw "No matches: $be206Pattern" }
    $be206Matches.FullName
  }
  foreach ($be206File in $be206Explicit) {
    (Get-Item -LiteralPath $be206File -ErrorAction Stop).FullName
  }
) | Sort-Object -Unique
$be206Output = 'features/FEAT-055-be2-child-response/evidence/local/final-offline-batch-20261019'
New-Item -ItemType Directory -Path $be206Output -ErrorAction Stop | Out-Null
$be206Suite | Set-Content -LiteralPath "$be206Output/selected-files.txt"
& $be206Python -m pytest -c backend/pyproject.toml @be206Suite -ra `
  "--junitxml=$be206Output/junit.xml" "--basetemp=$be206Output/pytest-temp" `
  *> "$be206Output/pytest.log"
$be206PytestExit = $LASTEXITCODE
$be206PytestExit | Set-Content -LiteralPath "$be206Output/pytest-exit.txt"
```

Use a new output directory name if it already exists; preserve all earlier receipts. Record
the interpreter/pytest versions, branch/base, complete relevant source/test SHA256 manifest
before and after, expanded selection, command, log, JUnit and native exit. A source change
after the batch invalidates its claim over the changed files and justifies a bounded rerun.

## Honest limits and result handling

- `tests/unit/test_lightning_vision_v2_server.py` is **excluded / NOT_RUN** here: line 14
  imports `PIL` at collection time. This is a missing-dependency gate, not a skipped PASS.
  No Pillow installation or silent dependency-path substitution is proposed.
- Three selected fixture-contract files contain individual `pytest.importorskip("PIL")`
  live-app route checks: `test_ai_job_polling.py:180`,
  `test_analysis_corrections_api.py:218`, `test_assistance_requests_api.py:155`.
  Keep the files selected, report actual skips as **NOT_RUN**, and retain the remaining
  component coverage. Their presence does not mean production HTTP behavior was tested.
- Do not select all `tests/unit` or `tests/contract` for this batch. FEAT-052's preserved full
  unit baseline contains 18 failures, 34 errors and 37 skips, and its selected contract run
  excluded seven Pillow-importing modules. That is historical baseline evidence, not a new
  06 failure allowance or permission to conceal newly failing selected cases.
- The foundation B6 unit suite legitimately launches a local pytest **collection** subprocess.
  Do not block all subprocesses or mislabel resulting harness failures as product defects;
  FEAT-048 C2 implementation evidence records that earlier failure mode. This does not authorize
  service startup, external network or model/provider calls.
- Failures/collection errors retain the actual nonzero exit and details; missing checks stay
  NOT_RUN. Inspect skips and JUnit testcase identities, not only the aggregate count. No new
  expected count is promised before final 06 collection.
- This pytest batch complements the executor's required Ruff, strict mypy, harness/security/
  architecture/skeleton and diff checks. It does not execute the frozen A17 package or replace
  the separate deferred runtime checklist. Stop at owner component review; do not mark runtime,
  integration or any BE2 card DONE from these offline results.
