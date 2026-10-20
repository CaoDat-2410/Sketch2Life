# FEAT-018 P2-T4 mapping diagnostics — 2026-10-20

**State: PARTIAL DIAGNOSTIC RESULT; TASK 4 REMAINS OPEN.**

## Approved scope

Person 2 approved Revision 3 at source commit `b39a9f2f56509b0543184876eb538fc9faf0e1aa`.
The exact owner issuance and approved file list are recorded in
[`approvals/TASK_APPROVAL.md`](../../approvals/TASK_APPROVAL.md). The work uses synthetic fixtures,
existing B1/B2 boundaries and B3 only as a matcher observer. Its report vocabulary is diagnostic
metadata, not a new public contract. Runtime, schema, catalog and provider behavior are outside the
approved scope.

The manifest pins the three input sources and the original Revision 3 document digests. It contains
120 primary cases (20 golden activities × six families) and 43 separately counted supplemental
cases. It records synthetic provenance and `provider_execution=NOT_EXECUTED`.

Artifact tuples:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `tests/fixtures/feat018-p2-t4-mapping/manifest.v1.json` | 213,541 | `da3ebff06ddd899692f4c7fd20752dbb81f5cafb3da22a951149bfa2ef9ed9d0` |
| `backend/tests/unit/test_feat018_p2_t4_mapping_diagnostics.py` | 40,414 | `80020fc0e0902244ef08ce23972d4d90af3452dcbd7817469e78e08fc029fee3` |
| `backend/tests/contract/test_feat018_p2_t4_manifest_contract.py` | 17,302 | `947f3f07b163e66d186663b2f14b221066fb59c570916a4db71a34ea5725f3d4` |

## Result

The generated metrics report is
[`P2_T4_MAPPING_DIAGNOSTICS_20261020.json`](../metrics/P2_T4_MAPPING_DIAGNOSTICS_20261020.json),
570,191 bytes, SHA-256
`9ff53835e63c65a1d3dcecdd71dd920267cd2862ef64443780c86b3133674e4b`.

| Boundary / group | Result |
| --- | --- |
| Primary cases | 120 rows; B1 COMPLETE for 120; B2 NOT_RUN for 120; B3 NOT_RUN for 120; requirements UNRESOLVED for 120. |
| Supplemental cases | 43 rows; 34 execution COMPLETE and 9 NOT_RUN; requirements: 25 SATISFIED, 6 EXPECTED_BLOCKED, 12 UNRESOLVED. |
| Full Task 4 acceptance | OPEN. |

The B2 prerequisite is the missing `PIL` import while importing the existing `SupervisedFlowService`.
No package was installed, no import was bypassed, and no runtime file was changed. The nine
unexecuted supplemental rows are the Gate-A-dependent cases. The other unresolved supplemental
observations are:

- `NARRATION_SOURCE_STATUS_MISMATCH`: the existing Raw contract accepts the supplied source/status
  mismatch, so the diagnostic records it as UNRESOLVED.
- `V2_WORD_BOUNDARY_MATCHER_DEVIATION` and `V2_WHITESPACE_MATCHER_DEVIATION`: the supplemental
  matcher-only inputs exposed both behaviors in the existing V2 matcher. They are observations, not
  fixes or new public error codes.

The report does not turn missing B2/B3 execution into a pass. B3 did not run on primary Gate-A
outputs, so no primary matcher or end-to-end mapping claim follows from the completed B1 checks.
The existing P1 fallback observations and Task 4's known provenance/version/confirmation gaps remain
subject to the row-level dispositions in the report and the approved plans.

## Offline checks

Environment: CPython 3.12.10, pytest 8.4.2, Pydantic 2.13.4, Ruff 0.16.4, mypy 1.20.2.

From `backend/`, the focused command was:

```powershell
& 'D:/GitHub/Sketch2Life/backend/.venv/Scripts/python.exe' -B -m pytest -p no:cacheprovider tests/unit/test_feat018_p2_t4_mapping_diagnostics.py tests/contract/test_feat018_p2_t4_manifest_contract.py tests/unit/test_raw_understanding.py tests/unit/test_activity_semantics.py -ra
```

Result: **231 passed, 129 skipped**. The skip summary reports 120 primary B2/B3 cases and 9
supplemental Gate-A cases blocked by missing `PIL`; B1, manifest checks, all runnable supplemental
cases, and the two existing focused suites completed.

Ruff command:

```powershell
& 'D:/GitHub/Sketch2Life/backend/.venv/Scripts/ruff.exe' check --no-cache tests/unit/test_feat018_p2_t4_mapping_diagnostics.py tests/contract/test_feat018_p2_t4_manifest_contract.py
```

Result: **All checks passed.** The scoped mypy command was
`mypy --no-incremental --config-file pyproject.toml tests/unit/test_feat018_p2_t4_mapping_diagnostics.py tests/contract/test_feat018_p2_t4_manifest_contract.py`.
It terminated inside mypy 1.20.2 with `OperationalError: unable to open database file`; it produced
no type-check result. No cache path, settings, dependency, or application code was changed to work
around that tool error.

The metrics report was generated from `backend/` with this command, which runs the approved test
module's explicit `--write-report` option and writes only the metrics path above:

```powershell
& 'D:/GitHub/Sketch2Life/backend/.venv/Scripts/python.exe' -B -c "import sys,runpy; sys.path.insert(0,'src'); sys.argv=['test_feat018_p2_t4_mapping_diagnostics.py','--write-report']; runpy.run_path('tests/unit/test_feat018_p2_t4_mapping_diagnostics.py',run_name='__main__')"
```

The result was **SKELETON_VALID**, **ARCHITECTURE_VALID**, and **REPOSITORY_SECURITY_VALID** (2,588
publishable files scanned; no absolute machine paths). `git diff --check` passed. The repository
harness validator returned `HARNESS_INVALID` because pre-existing `evidence/screenshots` and
`evidence/metrics` paths are missing under FEAT-045, FEAT-046 and FEAT-047. Those unrelated feature
directories were left unchanged.

The report integrity test checks that synthetic labels and narration text are absent from the JSON.
No model/provider/Lightning request or live media was used.

## Review and remaining work

Static review of the new tests and report path found no production-code changes and no unbounded
provider or filesystem effects. The only file-writing code is the explicit report option, which
writes the one metrics path named in the approved plan. The contract tests read the pinned source
files and validate manifest provenance, identities, counts, and recipes.

The plan requires independent implementation review. That review is not represented by the
coordinator's own checks in this note and remains pending, along with executable B2/B3 evidence and
owner disposition for unresolved behaviors. Task 4 stays open; this note does not claim acceptance.
