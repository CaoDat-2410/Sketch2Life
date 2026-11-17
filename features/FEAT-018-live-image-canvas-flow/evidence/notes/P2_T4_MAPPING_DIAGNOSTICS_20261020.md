# FEAT-018 P2-T4 mapping diagnostics — 2026-10-20

**Current state: P2-T4 diagnostic deliverable CLOSED by Person 2 at handoff commit `8ed2e8bbc7509eb236691bb8196eecb1e4f7e14f`. The 60 primary and 5 supplemental `UNRESOLVED` results remain product gaps; FU-01..FU-10 remain OPEN and unassigned.**

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
| `backend/tests/unit/test_feat018_p2_t4_mapping_diagnostics.py` | 60,257 | `72e6080bea0e1ae444e0e55a273fd6333e57564a26a5bd03af762209cddc4636` |
| `backend/tests/contract/test_feat018_p2_t4_manifest_contract.py` | 22,028 | `30fd2e6e94961ab2e30abde9c722992d3b2af5892bafbde1448dea33719b146f` |

Historical pre-typing-fix tuples, superseded by the current values above: the unit test was 60,003
bytes / `dbfe424bd14a8ddefec7d3fd077903e67abb537e8e2ba409941acf44ae3ef105`, and the contract test
was 22,000 bytes / `6dedf9f04346db6094978218a849ac9d63b4ee01fc9632971fcf42a0bd5dfb89`. These historical
tuples must not be used to identify the current test files.

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
statuses. At this point in the chronology, valid final gates and independent final review were still
pending; the later handoff record is documented below.

## Acceptance rebase and observed findings — 2026-10-21

Person 2 issued `W2_FEAT018_P2_T4_DIAGNOSTIC_ACCEPTANCE_REBASE_01`. It supersedes only the original
approval clause that `UNRESOLVED` behavior keeps Task 4 open, and only for acceptance of this
diagnostic deliverable. It does not convert any result to `SATISFIED`, claim product behavior is
acceptable, or authorize runtime/schema/catalog/provider/contract changes. The amended deliverable
is the approved 120 primary cases, 43 separately counted supplemental cases, B1/B2/B3 within the
approved limits, metrics report and evidence. At this stage, Task 4 itself remained `OPEN` until the
four closure gates in the approval record passed.

The Modal-generated execution report was received as 2,162,088 bytes with SHA-256
`15d4c5dfaecb2212205e1e705a85ef64493f37a3f54800579b051250227233a0`. After the owner amendment, a
coordinator-authored `coordinator_acceptance_annotation` was added to the JSON report; at that
pre-closure snapshot it did not change run rows, measured counts or `full_p2_t4_acceptance=OPEN`.
The annotated JSON tuple from that snapshot is recorded below. Do not describe the annotated file as
an unmodified Modal output.

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
their requirement basis is resolved or later dispositioned. The same applies to the supplemental
V1 correction and meaning/anchor-version rows. The owner amendment preserves the 60 primary and 5
supplemental `UNRESOLVED` rows as product gaps for diagnostic-deliverable acceptance. All 60 primary
unresolved rows carry static-review hypotheses; 40 (the conflict and adult-correction families) also
carry runtime boundary findings, while the 20 ambiguous rows have static hypotheses only. Among the
five supplemental unresolved rows, two carry static hypotheses and four carry runtime findings (six
finding entries), with one row in both groups. Do not describe every unresolved row as a separately measured runtime defect.
The rebase permits acceptance of the diagnostic deliverable without changing any row label.

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

The owner-relayed Claude pre-rebase review attachment named `Pasted text.txt` (received 2026-10-20)
was 10,978 bytes, SHA-256
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
| Final gates | The earlier default-cache `INTERNAL ERROR` is not a pass; the current scoped mypy result is tabulated below. `HARNESS_INVALID` remains a failing repository-wide result. |
| Evidence sanitization coverage | The prior reviewer said its static inspection did not find checks for every adult/correction label field. No disclosure was established; final review must check whether existing sanitizer coverage is sufficient before any future publication. |
| Synthetic stub/log distinction | The sentinel `FEAT018_T4_CONTROLLED_LOCAL_STUB_FAILURE` came from the intentional local stub; it is not a real provider execution. |
| Approved source versus execution checkout | `approved_source_commit` is `b39a9f2f56509b0543184876eb538fc9faf0e1aa`; owner-reported Modal execution used checkout `5c79741f9e3806626c1dc5c586fe409b2e9370a1`. |
| Plan digest provenance | Original Revision 3 digest remains the approval source; current post-amendment plan digest is recorded below as a derived record. |

### Local Claude handoff review — 2026-10-21

The owner supplied a local Claude preliminary-handoff review attachment named `Pasted text.txt`
(received 2026-10-21; 9,303 bytes, SHA-256
`8aea9063f2fc35b19af315a8597d44fa50907da8ab94a16477bbf2609231b5e4`). It reported
`PASS WITH NOTES` after reading the plan, evidence note, approval, decisions, README, status, context,
and portions of the JSON. The reviewer used Read/Grep only. It explicitly did not inspect the Git
diff, compute hashes/byte counts, or audit all report rows, and therefore did not establish that its
working-tree view matched HEAD `54d482d5`. This is a preliminary static review, not the required
independent final review. It does not verify execution results or close Task 4.

Coordinator verification after receiving that review established that the repository was clean at
HEAD `54d482d55b570e17b224a3a3506970b0970759f7`. The commit-to-Modal-checkout diff
`5c79741f9e3806626c1dc5c586fe409b2e9370a1..54d482d55b570e17b224a3a3506970b0970759f7` changes
only eight governance/evidence files; it does not change the Task 4 manifest, test files, or runtime
source. This supports reusing the owner-supplied Modal test result as evidence for unchanged tests
and inputs, but the Modal execution remains attributed to checkout `5c79741f`, not relabeled as a
run at `54d482d5`.

The review findings are handled as follows:

| Finding | Handoff update / disposition |
| --- | --- |
| M1: gate provenance | Local pytest was rerun on clean HEAD `54d482d5`. Ruff, mypy, and repository validators were run by the coordinator against the current uncommitted candidate working tree based on that HEAD; they are not bound to an immutable handoff commit. |
| M2: original versus annotated report | The JSON annotation now records the original Modal tuple; README and this note distinguish it from the current annotated file tuple. |
| M3: review findings/limits discoverability | This note is the detailed review record; plan, status, context, README and JSON annotation link to it and preserve the review limitations and observed findings. |
| L1: local pytest wording | The pre-install local rerun at `54d482d5` produced 238 passed, 129 skipped and 1 failed because `Pillow>=11,<13`/`PIL` was missing. The owner-supplied Modal run at `5c79741f` passed 368 tests; a later current-candidate local run also passed 368 after installing the declared dependency in the ignored `.venv`. |
| L2: plan digest provenance | The derived plan tuple below is tied to the exact plan content at the amended handoff candidate; the original Revision 3 digest remains the approval source. |
| L3: unresolved-row wording | Corrected with exact overlap counts: all 60 primary unresolved rows have static hypotheses; 40 also have runtime findings, and 20 have static hypotheses only. Supplemental unresolved rows: two carry static hypotheses and four carry runtime findings (six finding entries), with one row in both groups. Further corrected by Person 2 disposition M-1 (2026-10-21). |
| L4: original approval clause | The original approval text remains historical. The later acceptance rebase in `TASK_APPROVAL.md` explicitly supersedes only the unresolved-requirements closure clause. |
| L5: JSON closure gates | The report annotation records all four amendment gates and their current state rather than presenting only two pending items. |

### Local Claude re-review of the prior candidate — 2026-10-21

The owner relayed a second `PASS WITH NOTES` report in chat from the same local Claude reviewer that
produced the preliminary review above. It checked HEAD, the seven-file diff, JSON rows/counts, and
the JSON and plan tuples at that time (JSON 2,163,571 bytes / `eca5cf3b…`, plan 17,192 bytes /
`723a05e3…`). It did not rerun tests or validators. Because it is the same reviewer session, it
explicitly does not count as the independent final review required for Task 4. Its six Low findings
identified the needed exact row-basis wording, candidate-versus-commit gate provenance, need to
distinguish coordinator-run gates from reviewer-run checks, exact STATUS commit-range wording, LF
line endings, and disambiguation of the two same-named attachments.

The coordinator applied those documentary corrections after receiving the re-review. A subsequent
scoped mypy run using a per-command cache under `%TEMP%` exposed ten typing errors in the two already-
approved test files. The coordinator made typing-only fixes in those files; no test expectations,
diagnostic behavior, fixture, runtime, schema, or catalog changed. After installing the declared
`Pillow>=11,<13` dependency (Pillow 12.3.0) into the ignored local virtual environment, the focused
suite passed. The current working tree therefore differs from the candidate Claude re-reviewed; its
verdict and tuple checks do not cover the current state. A distinct local reviewer must inspect the
current candidate and the final gate evidence.

Gate execution provenance: on 2026-10-21 the coordinator reran the focused pytest, Ruff, scoped mypy,
repository harness, architecture, skeleton, and repository security checks against the current
uncommitted working tree based on HEAD `54d482d55b570e17b224a3a3506970b0970759f7`. The Claude
reviewer did not run these checks, and no standalone raw-log files were created. These results are
bound to the current working tree, not an immutable commit. Before Task 4 closure, preserve or rerun
the applicable final gates against the exact committed handoff state.

The original owner-approved plan digest remains the source approval provenance. The current plan is
a derived status/acceptance update that records the 2026-10-21 amendment. The report's
`approved_source_commit` identifies the approved source, while the Modal execution checkout is
separately recorded as `5c79741f9e3806626c1dc5c586fe409b2e9370a1`.

## Historical candidate gate snapshot — 2026-10-21

This table records a candidate-stage snapshot, not the final handoff verification. In particular,
its Ruff row is a result from a distinct candidate invocation and must not be read as the final
commit-bound result. The later post-commit record below is the applicable final handoff evidence.

| Gate | Result | Scope/limitation |
| --- | --- | --- |
| Focused pytest — Modal | **368 passed, 1 Pydantic deprecation warning** (owner-supplied output) | Ran at pinned checkout `5c79741f9e3806626c1dc5c586fe409b2e9370a1`. The diff from that checkout to `54d482d5` does not change the Task 4 manifest, tests, or runtime source. |
| Focused pytest — local | **368 passed** | Rerun on the current uncommitted candidate after installing declared Pillow 12.3.0 into the ignored `.venv`; includes the approved test files after typing-only fixes. |
| Ruff 0.16.4 | **PASS — historical candidate run** | Scoped command on an uncommitted candidate for both approved diagnostic test modules; superseded for final handoff by the separate commit-bound record below. |
| mypy 1.20.2 | **PASS — no issues in 2 source files** | The exact PowerShell command and its output are recorded immediately below. It used a per-command cache directory under `%TEMP%`; no project config or persistent settings changed. The default cache path previously failed to open its database; the valid temporary-cache run exposed ten test typing errors, which were fixed in the two approved test files before this passing run. |
| Repository harness validator | **HARNESS_INVALID** | Rerun on the current candidate; reports missing `evidence/screenshots` and `evidence/metrics` paths for FEAT-045, FEAT-046 and FEAT-047. These unrelated feature paths were not changed. |
| Architecture validator | **ARCHITECTURE_VALID** | Rerun on the current uncommitted candidate based on HEAD `54d482d55b570e17b224a3a3506970b0970759f7`. |
| Repository security validator | **REPOSITORY_SECURITY_VALID** | Rerun on the current candidate; 2,588 publishable files scanned and no absolute machine paths found. |
| Skeleton validator | **SKELETON_VALID** | Rerun on the current uncommitted candidate based on HEAD `54d482d55b570e17b224a3a3506970b0970759f7`. |
| `git diff --check` | **PASS** | Rerun against HEAD after the latest edits; exit 0 with no whitespace or line-ending warnings. |

The current-candidate scoped mypy command was run from `backend/` in PowerShell:

```powershell
$cacheDir = Join-Path $env:TEMP 'feat018-p2t4-mypy-cache-20261021'
& '.venv/Scripts/mypy.exe' --no-incremental --cache-dir $cacheDir --config-file pyproject.toml tests/unit/test_feat018_p2_t4_mapping_diagnostics.py tests/contract/test_feat018_p2_t4_manifest_contract.py
```

Output: `Success: no issues found in 2 source files` (mypy 1.20.2). The command uses a temporary
cache path and does not change persistent settings or repository configuration.

The focused local suite and scoped mypy result are valid checks of the current uncommitted candidate.
The repository harness remains invalid because of missing paths in unrelated features; no unrelated
feature directories were created or modified. Person 2 dispositioned the harness result on
2026-10-21: it stays recorded as `HARNESS_INVALID`, is not a pass, and is a separate repository-wide
issue outside P2-T4; FEAT-045/046/047 are not changed under Task 4.

The unmodified Modal-generated JSON is **2,162,088 bytes**, SHA-256
`15d4c5dfaecb2212205e1e705a85ef64493f37a3f54800579b051250227233a0`. At handoff commit
`c54b5a5a4a0dfe8f5c494cd47cd9f432e115f61b`, the coordinator-annotated JSON was **2,163,861 bytes**,
SHA-256 `06d467a2629f5d03511cc4ef41997a5c9d84480a2dc7aa3433b3e8ed18e691b0`; it is distinct from the
Modal artifact. The owner-approved Revision 3 plan source digest is
`1482c047476049e44ecd515178d64b2d4c9e60d13511c92aa8112fd5269d2d66`. At that same handoff commit,
the derived plan was 20,324 bytes, SHA-256
`1417e71a46271f605d72521468223b3c5c33287f761a142894a9922a0bde6807`. These are commit-bound
provenance tuples, not the current working-tree tuples after the review synchronization below.

### Person 2 disposition — 2026-10-21

Person 2 dispositioned the independent working-tree review in the coordinator conversation (recorded
in `DECISIONS.md`; `approvals/TASK_APPROVAL.md` is untouched because the APP write hold is in force):

| Item | Disposition |
| --- | --- |
| M-1 supplemental counts | Accepted. Four supplemental rows carry runtime findings (six finding entries); one row carries both a static hypothesis and a runtime finding. `UNRESOLVED` results are unchanged and are not satisfied behavior. Wording updated in CONTEXT, DECISIONS, STATUS, the plan and this note. |
| M-2 attribution | Accepted. Coordinator validation text is a separate coordinator-attributed `DECISIONS.md` entry, not part of the owner amendment. |
| L-1 test edits | Authorized. The typing-only edits stay in the two approved test files, limited to call forms and types needed for mypy; no change to test behavior, fixtures, runtime, schema or manifest. |
| `HARNESS_INVALID` | Recorded as the actual result, not a pass; outside P2-T4 scope; separate repository-wide issue; FEAT-045/046/047 not changed under Task 4. |
| `P2T4-FU-01` | Remains an OPEN follow-up; the contract-name gap is not resolved. |

At that pre-handoff candidate review, Task 4 was still OPEN. Remaining closure conditions were:
synchronized artifacts, validation evidence
bound to the final commit (the gate results above are bound to the uncommitted working tree), valid
gates confirmed on that commit, and an independent final review of the exact handoff commit. Security
remains PENDING. This note does not claim that any product gap has been fixed or that Task 4 is
closed.

## Closure Gate 3 disposition and pre-continuation attempt — 2026-10-21

Person 2 issued `W2_FEAT018_P2_T4_GATE3_HARNESS_DISPOSITION_01` in the coordinator conversation.
The disposition keeps the repository-wide result `HARNESS_INVALID`, not a pass or waiver, and places
that unrelated result outside the P2-T4-specific closure gate. Gate 3 is met only when every listed
P2-T4 gate has a valid passing result bound to the final handoff commit. At this pre-continuation
stage, Task 4 remained OPEN.

At this pre-continuation stage, checkout was HEAD `4310fcbfafa48a14e5fce31f38a2089e24079e52`;
the test files had the current tuples listed above. On 2026-10-21 the listed gates were run against
the uncommitted working tree based on that HEAD. This historical candidate run is not bound to a
final handoff commit:

| Gate | Command/result | Working directory and limitation |
| --- | --- | --- |
| Focused pytest | `& '.venv/Scripts/python.exe' -B -m pytest -p no:cacheprovider tests/unit/test_feat018_p2_t4_mapping_diagnostics.py tests/contract/test_feat018_p2_t4_manifest_contract.py tests/unit/test_raw_understanding.py tests/unit/test_activity_semantics.py -ra` — **368 passed in 2.62s** | `backend/`; CPython 3.12.10, pytest 8.4.2, Pillow 12.3.0. |
| Ruff 0.16.4 | `& '.venv/Scripts/ruff.exe' check tests/unit/test_feat018_p2_t4_mapping_diagnostics.py tests/contract/test_feat018_p2_t4_manifest_contract.py` — **NOT RUN / no lint verdict**; command exited 1 before lint because it could not create a temporary file under `backend/.ruff_cache` (`Access is denied`, OS error 5). | `backend/`; not retried with another cache path, shell, or split command. |
| Scoped mypy 1.20.2 | **Success: no issues found in 2 source files**; command used `--no-incremental --cache-dir $cacheDir --config-file pyproject.toml` for the two test paths, with `$cacheDir = Join-Path $env:TEMP 'feat018-p2t4-mypy-cache-20261021-gate3'`. | `backend/`; per-command cache under `%TEMP%`. |
| Architecture validator | **ARCHITECTURE_VALID** | Repository root; `python tools/validate_architecture.py`. |
| Skeleton validator | **SKELETON_VALID** | Repository root; `python tools/validate_skeleton.py`. |
| Repository security validator | **REPOSITORY_SECURITY_VALID**; 2,588 publishable files scanned; no absolute machine paths. | Repository root; `python tools/validate_repository_security.py`. |
| `git diff --check` | **PASS**, exit 0. | Repository root. |

The last recorded repository-harness result is `HARNESS_INVALID`: FEAT-045, FEAT-046 and FEAT-047
each lack `evidence/screenshots` and `evidence/metrics`. The harness validator is not among the seven
P2-T4 gates listed for this disposition, so it was not rerun; the missing paths remain an unrelated
repository-wide issue and those feature directories were not changed.

That Ruff attempt produced no lint verdict, so Gate 3 was **NOT MET**. Ruff was recorded as NOT RUN
and no further invocation was made at that stage. The issued rule requires stopping and reporting a
gate without a verdict, and prohibits bypassing that rule by changing shell or splitting commands.
The other six checks passed on
the uncommitted candidate but do not substitute for a valid Ruff result or final-commit binding. No
commit or push was authorized, so the final-commit gate has not been completed.

Earlier coordinator wording extended the restriction to cache paths. That extension was the
coordinator's interpretation, not an explicit owner-issued cache restriction. That wording correction
authorized no new Ruff attempt and did not change the failed invocation's missing-verdict status.

After the documentation updates, architecture and skeleton validators were rerun and returned
`ARCHITECTURE_VALID` and `SKELETON_VALID`; repository security returned
`REPOSITORY_SECURITY_VALID` (2,588 publishable files scanned; no absolute machine paths); and
`git diff --check` exited 0. The focused test files and their current tuples did not change after the
pytest, mypy, and Ruff attempts above.

Before the continuation issuance, step C had not been applied because the successful final-gate
condition was not established. The then-existing JSON tuple was 2,163,728 bytes / SHA-256
`3e882fe75c1f8449b34d1af1717379765ee6e97dff2eefd4f01a28fb28abadec`; its old `NOT_MET` explanation
predated this disposition and was not authority for treating `HARNESS_INVALID` as a P2-T4 blocker. The
original Modal tuple remains 2,162,088 bytes / `15d4c5dfaecb2212205e1e705a85ef64493f37a3f54800579b051250227233a0`.

At that pre-continuation point, the owner disposition did not close Task 4, resolve product gaps,
change Security `PENDING`, or authorize runtime/provider work; independent final review and valid
gates bound to a final handoff commit remained outstanding. The later outcome is recorded below.

## Issued continuation and candidate synchronization — 2026-10-21

Person 2 issued the entire `W2_FEAT018_P2_T4_CONTINUATION_AND_FINAL_GATE_SCOPE_01` in the
coordinator conversation. The issuance and Gate 3 disposition are relayed in `DECISIONS.md`, not
recorded in `approvals/TASK_APPROVAL.md`, because the APP write hold remains in force. This permits
one new candidate Ruff invocation and the seven named documentation/evidence updates; it does not
retroactively turn the failed invocation above into a pass.

The coordinator verified HEAD `4310fcbfafa48a14e5fce31f38a2089e24079e52`, no Git diff in tested
source/config, and matching current test tuples. Tool versions remained CPython 3.12.10, pytest
8.4.2, Pillow 12.3.0, Ruff 0.16.4 and mypy 1.20.2. The six earlier valid candidate results therefore
remain applicable under the issued continuation: focused pytest 368 passed, scoped mypy success in
two files, architecture/skeleton/security valid, and `git diff --check` exit 0. The post-edit
validator mini-cycle is a separate check after this synchronization.

Exactly one new candidate Ruff command was dispatched from `backend/`:

```powershell
& '.venv/Scripts/ruff.exe' check --no-cache --no-fix --no-fix-only tests/unit/test_feat018_p2_t4_mapping_diagnostics.py tests/contract/test_feat018_p2_t4_manifest_contract.py
```

Requested tool parameters were `exec_command`, `shell=powershell`, `login=false`, `tty=false`,
`max_output_tokens=4000`, and `yield_time_ms=10000`, without escalation. The result completed with
exit 0, tool chunk `0d8e49`, and the complete output:

```text
All checks passed!
```

No running-session identifier or clipping was returned for this invocation. Installed CLI help
describes `--no-cache` as disabling cache reads; this record does not claim runtime attestation that
every possible filesystem write was absent. Test/runtime/config changes and fixes were not made.

The candidate now has passing evidence for the seven listed checks. JSON changes are confined to
`coordinator_acceptance_annotation.closure_gates.artifact_consistency` and `valid_final_gates`.
Byte comparison with HEAD confirms that everything outside the annotation is identical; comparison
within it confirms only those two strings changed. The 120 primary and 43 supplemental rows,
summary, original Modal tuple, `provider_execution=NOT_EXECUTED`, and acceptance `OPEN` are preserved.

The explicit C/D amendment permits this candidate synchronization before commit. The candidate
annotation records `CANDIDATE_CHECKS_PASS` and references
`W2_FEAT018_P2_T4_POST_COMMIT_GATE_RECORD_01`. It does not establish final Gate 3 MET. The committed
note/report need not embed their own future commit SHA; the final chat record will contain the full
handoff SHA, exact commands/cwd, tool versions, completion/exit/verdicts, working-tree observations
and limitations. Final Gate 3 MET requires all seven valid passing results in that record.

After these edits, the scope permits one sequential mini-cycle from the repository root:
`python tools/validate_architecture.py`, `python tools/validate_skeleton.py`,
`python tools/validate_repository_security.py`, then `git diff --check`, each once. Its actual
results are supplied in the accompanying coordinator chat; this note does not pre-claim a pass for
an unexecuted cycle. Any failed or missing verdict ends the scope without further gate dispatches.

The preceding authorization language was accurate when that candidate-synchronization scope was
issued. Person 2 later accepted the chat chronology for the separate commit and push; the earlier
wording is an issuance-time snapshot and does not require retrospective rewriting solely to repeat
those later facts. This chronology disposition does not itself close Task 4.

## Post-commit handoff verification and final review — 2026-10-21 (state before owner closure)

The handoff is commit `c54b5a5a4a0dfe8f5c494cd47cd9f432e115f61b` (parent
`4310fcbfafa48a14e5fce31f38a2089e24079e52`), pushed to the matching feature branch. Person 2's
post-commit gate record in the coordinator conversation reports all seven P2-T4 gates passing on
that exact commit: focused pytest (368 passed), Ruff, scoped mypy, architecture, skeleton, repository
security, and `git diff --check`. The repository-wide harness remains `HARNESS_INVALID` for missing
evidence paths in FEAT-045/046/047; the owner disposition keeps that separate from P2-T4 and does not
call it a pass or waiver.

The owner supplied a fresh-session Claude review attachment on 2026-10-21 (7,027 bytes, 57 LF,
SHA-256 `ae37d9847c25798cdb2001797aacad22ea5912187e50cddabf87267ff62b6d3a`). It reports `PASS WITH
NOTES` after checking the exact commit, seven-file scope, report/plan tuples, JSON rows, and rerunning
the same seven gates in a separate Linux environment (CPython 3.12.3, pytest 8.4.2, Pillow 12.3.0,
Ruff 0.16.4, mypy 1.20.2). The review reports 368 tests passed, Ruff passed, mypy succeeded for two
source files, architecture/skeleton/security valid, and diff-check passed. These are reviewer-
reported results; raw logs and a complete command transcript were not added to the repository.

Person 2 accepted this fresh session as independent at the session-isolation level for this review.
The reviewer disclosed that it is the same Claude model family as earlier local reviews; organization-
level or model-family independence is not established. The review's three Low notes are dispositioned
as follows:

| Review note | Disposition |
| --- | --- |
| Earlier Ruff table could be confused with a later distinct attempt | The table above is now labeled as a historical candidate snapshot; the final commit-bound record is identified separately. |
| Pre-commit “not authorized” wording remains in older candidate text | Person 2 accepted the chronology in chat and did not require retrospective edits solely to repeat commit/push and final-gate facts. |
| `TASK_APPROVAL.md` does not contain later chat decisions | Deferred while APP hold is IN FORCE; that file remains untouched. |

This evidence-note update and the matching status/plan/report annotation are a documentation-only
follow-on to handoff commit `c54b5a5a4a0dfe8f5c494cd47cd9f432e115f61b`; execution rows and summary are
unchanged. The synchronized JSON is 2,164,151 bytes, SHA-256
`c6d094d5512596ad055d51e30a4595283c266bcb2ec8f56c34e01ce14119cff2`; the derived plan is 20,955
bytes, SHA-256 `b37f1d51b7a6602069e854133e19819a617e010f41704d48cc29010a24312be8`. The JSON row data
and summary remain unchanged from the handoff commit; only the coordinator acceptance annotation
changed.

After the document synchronization, `validate_architecture.py` returned `ARCHITECTURE_VALID`,
`validate_skeleton.py` returned `SKELETON_VALID`, `validate_repository_security.py` returned
`REPOSITORY_SECURITY_VALID` (2,599 publishable files scanned; no absolute machine paths), and
`git diff --check` exited 0. At the time of that synchronization check, no code tests had been rerun
because the changes were limited to governance/evidence documents and the coordinator annotation;
the follow-on final cycle is recorded separately. The diagnostic handoff was reviewed
at the commit above; at that stage Task 4 remained OPEN pending Person 2's closure disposition.
`P2T4-FU-01` through `P2T4-FU-10` remain OPEN and unassigned; the 60 primary and 5 supplemental
`UNRESOLVED` results remain product gaps, not passing behavior. `provider_execution=NOT_EXECUTED`,
APP hold was IN FORCE, and Security was PENDING.

## Owner closure disposition — 2026-10-21

Person 2 directly confirmed closure of FEAT-018 P2-T4 at handoff commit
`8ed2e8bbc7509eb236691bb8196eecb1e4f7e14f`, solely as the approved diagnostic deliverable. The owner
accepted all four closure gates: the missing provenance contract-name is recorded as
`P2T4-FU-01 OPEN`; artifacts are consistent; final gates PASS on this exact commit; and the
independent final review is PASS with no findings. The review history and its disclosed limitations
remain recorded above.

The 60 primary and 5 supplemental `UNRESOLVED` results remain product gaps. `P2T4-FU-01` through
`P2T4-FU-10` remain OPEN and unassigned; none is automatically assigned to Task 5. No runtime,
schema, catalog, contract, or provider authority is granted. `provider_execution=NOT_EXECUTED`; APP
hold remains IN FORCE and Security remains PENDING. `TASK_APPROVAL.md` was not modified under the
APP hold. The coordinator annotation records this closure; diagnostic execution rows and their
summary remain untouched. The post-closure annotated JSON is 2,164,965 bytes, SHA-256
`3cad584c5b560c165d8d052c6e1c42346e6d465d04952e4626f7a8e1a076f4cf`. The synchronized plan is
21,950 bytes, SHA-256 `bb076e50c5036ec77792a3c545339afbd99f3064473c88aff5d688c714ffa414`.
