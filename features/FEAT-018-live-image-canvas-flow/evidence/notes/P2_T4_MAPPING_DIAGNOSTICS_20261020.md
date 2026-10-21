# FEAT-018 P2-T4 mapping diagnostics — 2026-10-20

**State: DIAGNOSTIC RUN COMPLETE; ACCEPTANCE REBASE RECORDED; TASK 4 REMAINS OPEN pending valid final gates and independent final review.**

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
| `backend/tests/unit/test_feat018_p2_t4_mapping_diagnostics.py` | 60,003 | `dbfe424bd14a8ddefec7d3fd077903e67abb537e8e2ba409941acf44ae3ef105` |
| `backend/tests/contract/test_feat018_p2_t4_manifest_contract.py` | 22,000 | `6dedf9f04346db6094978218a849ac9d63b4ee01fc9632971fcf42a0bd5dfb89` |

## Latest Modal Notebook run — 2026-10-20

The owner supplied the completed focused-test output from a Modal Notebook using the pinned
Task 4 checkout at `5c79741f9e3806626c1dc5c586fe409b2e9370a1`. Reported environment facts are
CPython 3.12.6 and pytest 8.4.2; `PIL` was importable after installing the backend development
extra, but the exact Pillow version was not captured. The focused command, run from `backend/`, was:

```text
python -B -m pytest -p no:cacheprovider tests/unit/test_feat018_p2_t4_mapping_diagnostics.py tests/contract/test_feat018_p2_t4_manifest_contract.py tests/unit/test_raw_understanding.py tests/unit/test_activity_semantics.py -ra
```

The owner-provided result was **368 passed, 1 warning in 3.23s**. The warning is Pydantic's
deprecation warning for the extra `Field` keyword `exclude_if`; it did not fail the run.

The approved report generator was then run with `--write-report`; it returned
`report_written=true`, `gate_a_prerequisite.code=AVAILABLE`, and `provider_execution=NOT_EXECUTED`.
The downloaded report was independently checked after receipt: **2,162,088 bytes**, SHA-256
`15d4c5dfaecb2212205e1e705a85ef64493f37a3f54800579b051250227233a0`.

| Boundary / group | Latest result |
| --- | --- |
| Primary cases | 120 rows; B1, B2 and B3 each COMPLETE for 120; primary execution COMPLETE for 120; requirements: 60 SATISFIED, 60 UNRESOLVED. |
| Supplemental cases | 43 rows; execution COMPLETE for 43; requirements: 28 SATISFIED, 10 EXPECTED_BLOCKED, 5 UNRESOLVED. |
| Full Task 4 acceptance | OPEN pending the 2026-10-21 amendment closure gates. |

The report-generation output also contained `FEAT018_T4_CONTROLLED_LOCAL_STUB_FAILURE`. This is the
intentional exception from the `SWALLOWED_AUTORIG_CALL` synthetic case: the local stub raises it and
the service catches and logs it. It is not a provider/AutoRig execution or a report-generation
failure; the generator completed and wrote the report. No model, provider, Lightning or live-media
request was made.

This Modal result supersedes the initial local preflight counts and report tuple below for current
execution status. It does not resolve the 60 primary and 5 supplemental requirement gaps. Person 2's
2026-10-21 amendment allows acceptance of the diagnostic deliverable without changing those row
statuses; Task 4 remains open pending valid final gates and independent final review.

## Acceptance rebase and observed findings — 2026-10-21

Person 2 issued `W2_FEAT018_P2_T4_DIAGNOSTIC_ACCEPTANCE_REBASE_01`. It supersedes only the original
approval clause that `UNRESOLVED` behavior keeps Task 4 open, and only for acceptance of this
diagnostic deliverable. It does not convert any result to `SATISFIED`, claim product behavior is
acceptable, or authorize runtime/schema/catalog/provider/contract changes. The amended deliverable
is the approved 120 primary cases, 43 separately counted supplemental cases, B1/B2/B3 within the
approved limits, metrics report and evidence. Task 4 itself remains `OPEN` until the four closure
gates in the approval record pass.

The Modal-generated execution report was received as 2,162,088 bytes with SHA-256
`15d4c5dfaecb2212205e1e705a85ef64493f37a3f54800579b051250227233a0`. After the owner amendment, a
coordinator-authored `coordinator_acceptance_annotation` was added to the JSON report; it does not
change run rows, measured counts or `full_p2_t4_acceptance=OPEN`. The current annotated JSON tuple is
recorded below after verification. Do not describe the annotated file as an unmodified Modal output.

Observed primary boundary findings (20 rows per applicable finding):

| Finding | Count | Meaning recorded by the diagnostic |
| --- | ---: | --- |
| `SOURCE_DISAGREEMENT_PROJECTED_AS_AGREEMENT` | 20 | Source disagreement is projected as agreement in the conflict family. |
| `NARRATION_PROJECTION_HAS_ABSENT_AUDIO_MARKER` | 20 | Narration projection carries an absent-audio marker. |
| `ADULT_CONFIDENCE_CONVENTION_REQUIRES_REVIEW` | 20 | Adult-confidence convention needs policy review; no threshold was adopted here. |

The report also records 80 primary static-hypothesis instances: 20 each for ambiguity-decision
provenance not projected, Raw conflict references not projected, adult-assertion provenance
registration not assessed, and actor/meaning-version projection requiring review. The actor/version
hypothesis examines `actor_ref` and `meaning_version`; it does not assert that an anchor-version
field is missing. Two supplemental static-hypothesis rows record V1-correction owner disposition
and meaning/anchor-version flow not represented by a service transition.

The five supplemental rows still marked `UNRESOLVED` are:

| Case | Observed diagnostic finding or limitation |
| --- | --- |
| `feat018-p2-t4-supp-narration-source-status-mismatch` | `RAW_ACCEPTS_NARRATION_SOURCE_STATUS_MISMATCH`. |
| `feat018-p2-t4-supp-v1-adult-correction` | `V1_CORRECTION_REUSES_VISION_PROVENANCE`; correction provenance remains unresolved. |
| `feat018-p2-t4-supp-successive-meaning-versions` | Synthetic setup uses `TEST_ONLY_SESSION_REWIND`; product transition is not represented. |
| `feat018-p2-t4-supp-v2-word-boundary` | `V2_WORD_BOUNDARY_MATCHER_EXPECTATION_MISMATCH` and `MANIFEST_REQUIREMENT_EXPECTATION_MISMATCH`. |
| `feat018-p2-t4-supp-v2-whitespace` | `V2_WHITESPACE_MATCHER_EXPECTATION_MISMATCH` and `MANIFEST_REQUIREMENT_EXPECTATION_MISMATCH`. |

These results are diagnostics, not fixes or newly adopted contracts. Ten supplemental rows remain
`EXPECTED_BLOCKED`; none are relabeled. All product gaps below are separate, unassigned follow-ups;
none is automatically allocated to Task 5:

| Follow-up | Topic | State |
| --- | --- | --- |
| `P2T4-FU-01` | Verify registry/contract provenance for the `AdultSubjectConfirmationV1` name. Static search found the string in `supervised_flow.py:834`, `test_live_image_demo_api.py:1178`, and `test_topic_activity_matching.py:172`; it did not establish a registered contract definition in the searched paths. | OPEN / unassigned |
| `P2T4-FU-02` | Ambiguity-decision provenance and its projection. | OPEN / unassigned |
| `P2T4-FU-03` | Source conflict references, agreement projection, and absent-audio marker semantics. | OPEN / unassigned |
| `P2T4-FU-04` | Adult assertion provenance, confidence convention, actor and meaning-version representation. | OPEN / unassigned |
| `P2T4-FU-05` | Raw narration source/status mismatch. | OPEN / unassigned |
| `P2T4-FU-06` | V1 adult-correction provenance reuse. | OPEN / unassigned |
| `P2T4-FU-07` | Successive meaning/anchor-version product transition. | OPEN / unassigned |
| `P2T4-FU-08` | V2 word-boundary matcher behavior. | OPEN / unassigned |
| `P2T4-FU-09` | V2 whitespace matcher behavior. | OPEN / unassigned |
| `P2T4-FU-10` | Candidate-envelope/no-match contract requirement and ownership. | OPEN / unassigned |

The provenance-name search was limited to `backend/src`, `backend/tests`, `docs/governance`, and
this feature folder. It is a lookup record, not proof that no definition exists elsewhere.

## Initial local preflight result (historical)

The initial metrics report, last regenerated in commit `87599013` before the Modal follow-up, was
recorded as 614,556 bytes, SHA-256
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
observations are not runtime measurements and do not establish the underlying schema/provenance
policy.

The 60 primary rows with static-review hypotheses remain `UNRESOLVED` after B2/B3 execution until
their product limitation is resolved or later dispositioned. The same applies to the supplemental
V1 correction and meaning/anchor-version rows. Under the 2026-10-21 rebase, these unresolved labels
remain product gaps but no longer block acceptance of the diagnostic deliverable itself.

Supplemental `expected.outcome`, `expected.requirement_status`, and matcher target modes are read by
the diagnostics path. Outcome predicates inspect the observed rejection code or observed fields;
the B2 expected error code is derived from the manifest outcome. The V1 correction predicate
checks the returned primary `source_claim_ids` against the returned confirmation IDs and reference
Vision IDs, checks the original-label hash against Raw input, and checks the normalized-label hash
against the correction input. These input IDs and hashes are recorded separately under `references`,
not described as observations. The known V1 provenance reuse remains a separate
`V1_CORRECTION_REUSES_VISION_PROVENANCE` boundary finding; it does not become a manifest expectation
mismatch. Empty adult confirmation uses the returned Gate A confirmation IDs and requires a primary
adult-assertion anchor with no secondary anchors. A mismatch is recorded rather than reported as a
pass. The primary target V1/V2 expectations are compared with observed target modes
when B2/B3 execute, and the test independently recomputes the target mode from the observation list
to check the row's mismatch disposition. The no-match recipe is checked against all 100 base V2
profiles, and the primary row must report any non-fallback match it observes. A passing diagnostics
test means the observation and its disposition were recorded consistently; it does not mean the
underlying requirement is satisfied or Task 4 is accepted. The schema-default-backed scene
`conflict_preserved` value is reported with projection metadata and is not called proof that Raw
conflicts survived.

`SUCCESSIVE_MEANING_VERSIONS` is explicitly marked
`recipe_input_origin=TEST_ONLY_SESSION_REWIND`; the completed report records the observed setup in a
separate `observed.input_origin` field. This test setup directly advances a synthetic session from
`UNDERSTANDING_PROPOSED` to `GATE_A_PENDING` because the service has no product transition for that
route. It is a test setup, not evidence of a production user flow; the report keeps the
meaning/anchor-version requirement unresolved.

The completed B2/B3 observations do not convert unresolved requirements into passes. The report
contains primary matcher observations at B3 for the approved base-profile scope, but does not claim
end-to-end activity selection, eligibility resolution, Gate B, or production user-flow behavior.
The existing P1 fallback observations and Task 4 provenance/version/confirmation gaps remain as
row-level diagnostic dispositions and separate follow-ups.

## Initial local offline checks (historical)

Environment: CPython 3.12.10, pytest 8.4.2, Pydantic 2.13.4, Ruff 0.16.4, mypy 1.20.2.

From `backend/`, the focused command was:

```powershell
& '.venv/Scripts/python.exe' -B -m pytest -p no:cacheprovider tests/unit/test_feat018_p2_t4_mapping_diagnostics.py tests/contract/test_feat018_p2_t4_manifest_contract.py tests/unit/test_raw_understanding.py tests/unit/test_activity_semantics.py -ra
```

For delta `fe5bcde..988fc91`, the focused command was run on the candidate working tree before
commit and produced **238 passed, 129 skipped, 1 failed**. The sole failure is the explicit
required-dependency preflight for missing `Pillow>=11,<13`; this is intentionally not reported as a
clean run. The skip summary identifies 120 primary B2/B3 cases and 9 supplemental Gate-A cases as
NOT_RUN. This environment does not establish B2/B3 results.

Ruff command:

```powershell
& '.venv/Scripts/ruff.exe' check --no-cache tests/unit/test_feat018_p2_t4_mapping_diagnostics.py tests/contract/test_feat018_p2_t4_manifest_contract.py
```

For delta `fe5bcde..988fc91`, Ruff was run on the candidate working tree before commit. Result:
**All checks passed.** Scoped mypy was **not rerun for this delta**. The recorded mypy outcomes below
are from earlier invocations and are historical only.

```powershell
& '.venv/Scripts/mypy.exe' --no-incremental --config-file pyproject.toml tests/unit/test_feat018_p2_t4_mapping_diagnostics.py tests/contract/test_feat018_p2_t4_manifest_contract.py
```

The latest earlier invocation terminated inside mypy 1.20.2 with its generic `INTERNAL ERROR`; an
earlier invocation reported `OperationalError: unable to open database file`. Neither produced a
type-check result. No cache path, settings, dependency, or application code was changed to work around
the tool error.

For delta `fe5bcde..988fc91`, `python tools/validate_repository_security.py` was run before commit and
returned **REPOSITORY_SECURITY_VALID** (2,588 publishable files scanned; the validator's path checks
are pattern-based and are not a general absolute-path detector). `git diff --check` also passed for
the candidate delta. `validate_skeleton.py`, `validate_architecture.py`, and the repository harness
validator were not rerun for this delta.

The following validator results are historical and are not evidence for delta `fe5bcde..988fc91`:
**SKELETON_VALID**, **ARCHITECTURE_VALID**, and **HARNESS_INVALID**. The harness validator had reported
pre-existing `evidence/screenshots` and `evidence/metrics` paths missing under FEAT-045, FEAT-046 and
FEAT-047; those unrelated feature directories were left unchanged.

The metrics report artifact and its generation command below are recorded as prior report provenance;
the report was not regenerated for delta `fe5bcde..988fc91`. This command runs the approved test
module's explicit `--write-report` option and writes only the metrics path above:

```powershell
& '.venv/Scripts/python.exe' -B -c "import sys,runpy; sys.path.insert(0,'src'); sys.argv=['test_feat018_p2_t4_mapping_diagnostics.py','--write-report']; runpy.run_path('tests/unit/test_feat018_p2_t4_mapping_diagnostics.py',run_name='__main__')"
```

The pytest, Ruff, scoped mypy, and `--write-report` commands above are relative to the `backend/`
working directory. `python tools/validate_repository_security.py` runs from the repository root.

The report integrity test checks that primary labels, supplemental aliases and narration text are
absent from the JSON. No model/provider/Lightning request or live media was used.

## Review and remaining work

The owner-relayed Claude review attachment `Pasted text.txt` was 10,978 bytes, SHA-256
`fdcdd2aeb77afb3812ef998ee1fb39c5965d42d232516e1e81d0ff2ba58fe7ad`. It reported PASS WITH NOTES
for the pre-rebase diagnostic slice and identified review gaps around observed runtime findings,
candidate-envelope ownership, provenance contract-name registration, final gates, finding counts,
sanitization coverage, synthetic-stub/log distinction, source-versus-execution commit provenance,
and edited-plan digest provenance. The current note and follow-up table incorporate these limits.

The reviewer also disclosed that it ran shell/Git commands despite its stated read-only/no-command
boundary. Record that as a review-process deviation. The attachment was a partial static review of an
earlier state, not a final independent review of this amended handoff. Its observations are retained
with that limitation; they are not treated as runtime evidence. A new independent final review of the
post-amendment files and gate results is still required.

The earlier review's issue mapping for this handoff is:

| Review item | Current record |
| --- | --- |
| Missing observed findings/counts | The three repeated primary boundary findings and five supplemental unresolved case IDs are listed above; row-level facts remain in the JSON. |
| Candidate-envelope ownership | `P2T4-FU-10`, OPEN and unassigned. |
| Provenance contract-name | `P2T4-FU-01`; searched paths and exact matching references are listed above. |
| Final gates | Results are tabulated below. `INTERNAL ERROR` and `HARNESS_INVALID` are not passes. |
| Evidence sanitization coverage | The prior reviewer said its static inspection did not find checks for every adult/correction label field. No disclosure was established; final review must check whether existing sanitizer coverage is sufficient before any future publication. |
| Synthetic stub/log distinction | The sentinel `FEAT018_T4_CONTROLLED_LOCAL_STUB_FAILURE` came from the intentional local stub; it is not a real provider execution. |
| Approved source versus execution checkout | `approved_source_commit` is `b39a9f2f56509b0543184876eb538fc9faf0e1aa`; owner-reported Modal execution used checkout `5c79741f9e3806626c1dc5c586fe409b2e9370a1`. |
| Plan digest provenance | Original Revision 3 digest remains the approval source; current post-amendment plan digest is recorded below as a derived record. |

The original owner-approved plan digest remains the source approval provenance. The current plan is
a derived status/acceptance update that records the 2026-10-21 amendment. The report's
`approved_source_commit` identifies the approved source, while the Modal execution checkout is
separately recorded as `5c79741f9e3806626c1dc5c586fe409b2e9370a1`.

## Final handoff gate results — 2026-10-21

| Gate | Result | Scope/limitation |
| --- | --- | --- |
| Focused pytest | **368 passed, 1 Pydantic deprecation warning** (owner-supplied Modal output) | Ran at the reported pinned checkout; not rerun in this Windows workspace. |
| Ruff 0.16.4 | **PASS** | Local scoped command for the two diagnostic test modules. |
| mypy 1.20.2 | **NO VALID RESULT — INTERNAL ERROR** | Default cache ended at `OperationalError: unable to open database file`; a separate ignored cache path failed with `PermissionError: [WinError 5]`. Neither is a type-check pass. |
| Repository harness validator | **HARNESS_INVALID** | Reports pre-existing missing `evidence/screenshots` and `evidence/metrics` paths for FEAT-045, FEAT-046 and FEAT-047; no unrelated paths were created. |
| Architecture validator | **ARCHITECTURE_VALID** | Current workspace result. |
| Repository security validator | **REPOSITORY_SECURITY_VALID** | Rerun after replacing the absolute attachment locator with the attachment name and tuple. |
| Skeleton validator | **SKELETON_VALID** | Current workspace result. |
| `git diff --check` | **PASS** | Rerun after the final documentation edits recorded in this handoff. |

The focused pytest result is valid owner-provided execution evidence, but it does not override the
failed/unavailable local mypy result or the unrelated harness invalidity. Task 4 cannot close until
the final gates have valid outcomes and the independent final review is complete.

The current annotated metrics JSON is **2,162,989 bytes**, SHA-256
`35be57cb029d6f18a96a82dd95390a9de183245b76d05bfa173e874b5d8bf68e`. The unmodified Modal-generated
JSON remains separately identified above as 2,162,088 bytes / `15d4c5dfaecb2212205e1e705a85ef64493f37a3f54800579b051250227233a0`.
The owner-approved Revision 3 plan source digest is
`1482c047476049e44ecd515178d64b2d4c9e60d13511c92aa8112fd5269d2d66`; the current derived plan
record after status and acceptance updates is 16,540 bytes, SHA-256
`ef14640c5a2f6ee80c1ec840994b7e8f3f5d6a8332ad6ce5ef604e3e156b7b48`.

Task 4 is still OPEN. Remaining closure conditions are: valid final gates (mypy `INTERNAL ERROR` is
not PASS), the provenance contract-name check or an explicitly recorded follow-up, consistent
handoff artifacts, and independent final review. This note does not claim that any product gap has
been fixed or that Task 4 is closed.
