# M2 offline baseline — owner launch instruction R2

**Status: NOT LAUNCHED.** Owner-only run after the dedicated baseline approval entry is recorded in TASK_APPROVAL.md as APPROVED / NOT LAUNCHED. This instruction is not self-authorizing. Do not start S1a-T from this file.

## Pinned specification

Read and follow M2_BASELINE_RUN_APPROVAL_FINAL_20261107.md, SHA-256 A671DBD85B9622CB754C5CECB807BBBBA2C920CD76F0A22ABBA44F4A12DC1A18. If the pin, source pins, branch, HEAD or index differ from that specification and the approval entry, stop. Verify the approval section exists after G6; the pre-G6 TASK_APPROVAL.md hash in the spec is historical provenance only.

## Before creating output

Open PowerShell at the repository root. Run this preflight block as-is. It prints only Boolean verdicts; any `false` or command error means stop. Do not read `.env`, print environment values, or clear an inherited variable to pass the gate.

```powershell
$expectedBranch = 'feature/feat063-be-foundation'
$expectedHead = 'dd70685eae58aaaefea3e567f5c23d09345a8513'
$branchOk = (git branch --show-current) -eq $expectedBranch
$headOk = (git rev-parse HEAD) -eq $expectedHead
git diff --cached --quiet
$indexOk = $LASTEXITCODE -eq 0
$names = @('SKETCH2LIFE_DATABASE_URL','BE1_TEST_DATABASE_URL','S1A_T_TEST_DATABASE_URL','PGHOST','PGPORT','PGUSER','PGPASSWORD','PGSERVICE','PGSERVICEFILE','PGOPTIONS')
$envOk = -not (@($names | Where-Object { -not [string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($_)) }).Count -gt 0)
$running = @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object { $_.CommandLine -match '(?i)(pytest|mypy)' }).Count -gt 0
$processOk = -not $running
$logAbsent = -not (Test-Path -LiteralPath '.claude/handoff/logs/M2_BASELINE_RUN_20261107')
$tmpAbsent = -not (Test-Path -LiteralPath 'tmp/M2_BASELINE_RUN_20261107')
git check-ignore --quiet -- '.claude/handoff/logs/M2_BASELINE_RUN_20261107/probe'
$logIgnored = $LASTEXITCODE -eq 0
git check-ignore --quiet -- 'tmp/M2_BASELINE_RUN_20261107/probe'
$tmpIgnored = $LASTEXITCODE -eq 0
$outputPathsIgnored = $logIgnored -and $tmpIgnored
"BRANCH_OK=$($branchOk.ToString().ToLowerInvariant())"
"HEAD_OK=$($headOk.ToString().ToLowerInvariant())"
"INDEX_EMPTY=$($indexOk.ToString().ToLowerInvariant())"
"DB_ENV_CLEAN=$($envOk.ToString().ToLowerInvariant())"
"NO_TEST_PROCESS=$($processOk.ToString().ToLowerInvariant())"
"OUTPUT_PATHS_ABSENT=$((($logAbsent -and $tmpAbsent).ToString()).ToLowerInvariant())"
"OUTPUT_PATHS_IGNORED=$($outputPathsIgnored.ToString().ToLowerInvariant())"
if (-not ($branchOk -and $headOk -and $indexOk -and $envOk -and $processOk -and $logAbsent -and $tmpAbsent -and $outputPathsIgnored)) { throw 'Preflight failed; stop without clearing or changing anything.' }
```

Recompute every source/test/config/validator hash in the pinned approval specification. If any pin differs, stop. Do not read `.env`.

Confirm both output paths are absent and ignored before creating them:

    .claude/handoff/logs/M2_BASELINE_RUN_20261107/
    tmp/M2_BASELINE_RUN_20261107/

If either exists or is not ignored, stop without deleting or reusing it. After all preflight checks pass, create each directory once. Keep all raw output there; do not copy it into Git or include environment values in the report.

## Run

Run the commands exactly once and in the order in §4 of the pinned specification: mypy version, strict mypy, Ruff, the single 11-module offline pytest invocation, then the three validators and git diff --check. For each command use cmd.exe /d /c, direct stdout/stderr redirection to separate files and record the exit immediately. Keep the exact cwd, executable, flags, test selection, ceilings, cache and basetemp from the specification. Do not use a pipeline, Tee-Object or transcript.

If an assertion fails but pytest returns a complete official summary, preserve it as baseline data and continue with the remaining independent checks. On timeout, interruption, missing summary/exit, safety warning, secret/URI in output, or any sign of DB/network access, stop immediately; do not retry or change the command.

## Return evidence

Return the exact log directory name, command/executable/version/cwd, output file hashes, exit codes, complete pytest summary and failed/error node IDs. Report NOT RUN for any missing verdict. Do not call skipped or NOT RUN tests passed. Do not claim DB safety from absence of a connection string alone.

After owner review of results, a separate baseline closure record must be accepted before any S1a-T launch. No later phase is opened by running this baseline. OWNER_MODAL_CALL_APPROVED=NO.

## Revision 2 change record

The table follows the file order in the `git diff --no-index` comparison with the prior launch instruction. It records only the narrow correction approved in D-159 B1.

| Order | Location | Change |
|---:|---|---|
| 1 | Title | Label this copy as revision R2; the prior file is unchanged. |
| 2 | Preflight output-ignore check | Check the logs probe and temporary probe with separate single-path `git check-ignore --quiet` commands; capture each exit code independently. |
| 3 | Preflight verdict | Combine the two individual results and print `OUTPUT_PATHS_IGNORED=true` only when both paths are ignored; require that combined result in the stop gate. |
| 4 | Revision record | Add this change table and identify `git diff --no-index` as the comparison tool. |
