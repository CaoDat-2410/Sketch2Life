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
| `tests/fixtures/feat018-p2-t4-mapping/manifest.v1.json` | 228,305 | `1ba728ca3b02646bafd6b75d27b6c70461957ceb8628ec8e75f11e3aea62bd5a` |
| `backend/tests/unit/test_feat018_p2_t4_mapping_diagnostics.py` | 57,510 | `43a0fd40d6caea07460cd7827b89be67a92acf2e14815c6deeba49e46716d3a8` |
| `backend/tests/contract/test_feat018_p2_t4_manifest_contract.py` | 22,000 | `6dedf9f04346db6094978218a849ac9d63b4ee01fc9632971fcf42a0bd5dfb89` |

## Result

The regenerated metrics report is
[`P2_T4_MAPPING_DIAGNOSTICS_20261020.json`](../metrics/P2_T4_MAPPING_DIAGNOSTICS_20261020.json),
614,556 bytes, SHA-256
`2bbbcf3230f74f65435f0bed076533775e5e89d3926b9f4cfd5d6e2d5dedf7b0`.

| Boundary / group | Result |
| --- | --- |
| Primary cases | 120 rows; B1 COMPLETE for 120; B2 NOT_RUN for 120; B3 NOT_RUN for 120; requirements UNRESOLVED for 120. |
| Supplemental cases | 43 rows; 34 execution COMPLETE and 9 NOT_RUN; requirements: 25 SATISFIED, 6 EXPECTED_BLOCKED, 12 UNRESOLVED. |
| Full Task 4 acceptance | OPEN. |

The B2 prerequisite is that the active backend test environment lacks the required project
dependency `Pillow>=11,<13` (import module `PIL`) while importing the existing
`SupervisedFlowService`. Pillow is a required project dependency, not an optional Gate A or live
dependency. No package was installed, no import was bypassed, and no runtime file was changed. The
dedicated dependency preflight fails for this environment; case-level B2/B3 rows stay NOT_RUN. The
nine unexecuted supplemental rows are the Gate-A-dependent cases. The other unresolved supplemental
observations are:

- `NARRATION_SOURCE_STATUS_MISMATCH`: the existing Raw contract accepts the supplied source/status
  mismatch, so the diagnostic records it as UNRESOLVED.
- `V2_WORD_BOUNDARY_MATCHER_EXPECTATION_MISMATCH` and
  `V2_WHITESPACE_MATCHER_EXPECTATION_MISMATCH`: the supplemental
  matcher-only inputs expose two different inputs: the word-boundary probe is an explicit synthetic
  anchor, while the whitespace probe travels through narration text because Gate A normalizes anchor
  labels first. They are matcher observations, not fixes or new public error codes. V1 substring
  behavior for the word-boundary fixture is recorded as existing design behavior. The manifest marks
  the desired matcher outcomes SATISFIED, so the observed deviations also receive
  `MANIFEST_REQUIREMENT_EXPECTATION_MISMATCH`; the fixtures do not encode the known defects as expected.

The `static_review_hypotheses` field is separate from runtime `boundary_findings`; it records schema
shape and provenance-registration limits, owner-disposition markers, and synthetic test-route
limitations, and is counted separately in the report summary. This report contains 60 primary rows
with 80 hypothesis instances (20 each for ambiguity-decision projection, Raw conflict projection,
adult-provenance registration not assessed, and actor/meaning-version projection), plus 2
supplemental rows with 2 instances (the V1 correction owner-disposition marker and the synthetic
meaning-version transition). The actor/meaning-version hypothesis checks the `actor_ref` and
`meaning_version` fields; it does not assert that an anchor-version field is missing. These static
observations are available even though Gate A did not run; they are not runtime measurements.

Every primary row with a static-review hypothesis remains `UNRESOLVED` even if B2/B3 later execute,
until the corresponding schema/provenance-registration limitation is resolved or the required owner
disposition is recorded. This applies to the 60 ambiguity, conflict, and adult-correction rows in
this report; it is separate from their current `NOT_RUN` execution status. The supplemental V1
correction row also remains `UNRESOLVED` until its owner-disposition marker is dispositioned.

Supplemental `expected.outcome`, `expected.requirement_status`, and matcher target modes are read by
the diagnostics path. Outcome predicates inspect the observed rejection code or observed fields;
the B2 expected error code is derived from the manifest outcome. Correction provenance checks the
returned primary adult-assertion provenance and retained secondary Vision claim IDs against IDs in
the synthetic Raw input. Empty adult confirmation uses the returned Gate A confirmation IDs and
requires a primary adult-assertion anchor with no secondary anchors. A mismatch is recorded rather
than reported as a pass. The primary target V1/V2 expectations are compared with observed target modes
when B2/B3 execute, and the test independently recomputes the target mode from the observation list
to check the row's mismatch disposition. The no-match recipe is checked against all 100 base V2
profiles, and the primary row must report any non-fallback match it observes. A passing diagnostics
test means the observation and its disposition were recorded consistently; it does not mean the
underlying requirement is satisfied or Task 4 is accepted. The schema-default-backed scene
`conflict_preserved` value is reported with projection metadata and is not called proof that Raw
conflicts survived.

`SUCCESSIVE_MEANING_VERSIONS` is explicitly marked
`recipe_input_origin=TEST_ONLY_SESSION_REWIND`; the observed setup uses a separate
`observed.input_origin` field if execution completes. The recipe field does not imply the case
executed in this report. When run, the test directly advances a synthetic session from
`UNDERSTANDING_PROPOSED` to `GATE_A_PENDING` because the service has no product transition for that
route. It is a test setup, not evidence of a production user flow; the report keeps its
meaning/anchor-version observation unresolved.

The report does not turn missing B2/B3 execution into a pass. B3 did not run on primary Gate-A
outputs, so no primary matcher or end-to-end mapping claim follows from the completed B1 checks.
The existing P1 fallback observations and Task 4's known provenance/version/confirmation gaps remain
subject to the row-level dispositions in the report and the approved plans.

## Offline checks

Environment: CPython 3.12.10, pytest 8.4.2, Pydantic 2.13.4, Ruff 0.16.4, mypy 1.20.2.

From `backend/`, the focused command was:

```powershell
& '.venv/Scripts/python.exe' -B -m pytest -p no:cacheprovider tests/unit/test_feat018_p2_t4_mapping_diagnostics.py tests/contract/test_feat018_p2_t4_manifest_contract.py tests/unit/test_raw_understanding.py tests/unit/test_activity_semantics.py -ra
```

After this review remediation: **238 passed, 129 skipped, 1 failed**. The sole failure is the explicit
required-dependency preflight for missing `Pillow>=11,<13`; this is intentionally not reported as a
clean run. The skip summary identifies 120 primary B2/B3 cases and 9 supplemental Gate-A cases as
NOT_RUN. This environment does not establish B2/B3 results.

Ruff command:

```powershell
& '.venv/Scripts/ruff.exe' check --no-cache tests/unit/test_feat018_p2_t4_mapping_diagnostics.py tests/contract/test_feat018_p2_t4_manifest_contract.py
```

Result: **All checks passed.** The scoped mypy command was
`& '.venv/Scripts/mypy.exe' --no-incremental --config-file pyproject.toml tests/unit/test_feat018_p2_t4_mapping_diagnostics.py tests/contract/test_feat018_p2_t4_manifest_contract.py`.
The latest invocation terminated inside mypy 1.20.2 with its generic `INTERNAL ERROR`; an earlier
invocation reported `OperationalError: unable to open database file`. Neither produced a type-check
result. No cache path, settings, dependency, or application code was changed to work around the tool
error.

The metrics report was generated from `backend/` with this command, which runs the approved test
module's explicit `--write-report` option and writes only the metrics path above:

```powershell
& '.venv/Scripts/python.exe' -B -c "import sys,runpy; sys.path.insert(0,'src'); sys.argv=['test_feat018_p2_t4_mapping_diagnostics.py','--write-report']; runpy.run_path('tests/unit/test_feat018_p2_t4_mapping_diagnostics.py',run_name='__main__')"
```

The result was **SKELETON_VALID**, **ARCHITECTURE_VALID**, and **REPOSITORY_SECURITY_VALID** (2,588
publishable files scanned; the validator's path checks are pattern-based and are not a general
absolute-path detector). The commands above are relative to the `backend/` working directory.
`git diff --check` passed. The
repository harness validator returned `HARNESS_INVALID` because pre-existing `evidence/screenshots` and
`evidence/metrics` paths are missing under FEAT-045, FEAT-046 and FEAT-047. Those unrelated feature
directories were left unchanged.

The report integrity test checks that primary labels, supplemental aliases and narration text are
absent from the JSON. No model/provider/Lightning request or live media was used.

## Review and remaining work

Static review of the new tests and report path found no production-code changes and no unbounded
provider or filesystem effects. The only file-writing code is the explicit report option, which
writes the one metrics path named in the approved plan. The contract tests read the pinned source
files and validate manifest provenance, identities, counts, and recipes.

The plan requires independent implementation review. That review is not represented by the
coordinator's own checks in this note and remains pending, along with executable B2/B3 evidence and
owner disposition for unresolved behaviors. Task 4 stays open; this note does not claim acceptance.
