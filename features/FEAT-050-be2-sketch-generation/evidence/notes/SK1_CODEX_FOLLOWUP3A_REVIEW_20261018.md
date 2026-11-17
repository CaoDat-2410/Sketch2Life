# Codex focused re-review - SK1 Claude follow-up 3A

- Verdict: **PASS for follow-up 3A**. F3-R31 (P2), N1 and N2 (P3 wording) are closed.
  No new actionable finding in the reviewed delta. The wider SK1 checkpoint retains its
  previously recorded owner dispositions and residuals; this is not owner acceptance.
- SK1 **NOT_ACCEPTED**; BE2-04 **IN_PROGRESS / NOT_DONE**.
- Branch `feature/be2-04-sketch-generation`, HEAD/base
  `113cdf956a09336a0abf5561bd939f5e13b31ea0`, staged 0; implementation remains uncommitted.

## Scope and integrity

Reviewed the changed R31 test, the coordination/store/sink behavior it exercises, and the
follow-up 3A wording corrections. All 15 source/test/fixture references match SHA256 and byte
length. Comparing with follow-up 3 proves that only
`backend/tests/unit/test_sketch_generation_races.py` changed in those 15 files; production
source and the example fixture are unchanged. The four preserved historical references,
task approval and approved plan also match their pinned hashes.

- Follow-up 3A note SHA256:
  `2932fc191312dfc914e9cc7aa11dee0e30d79f41ebc50e7b6a289d42b275044b`.
- Follow-up 3A metrics SHA256:
  `eeca663f43a7f5c1ac2b9973707df06900333a4f16508b3e6ea34dfced9c13aa`.
- Current race-test SHA256:
  `964cb21c67ca0c34e658f3d5601da3eb607f2c372a87a7a1d83a00db05ec615f`.

## Findings disposition

**F3-R31 closed.** In `test_sketch_generation_races.py:1470-1476`, the observer signals the
actual worker's entry into `request_publication`. The C8 before-commit hook at 1491-1503
waits for that entry while holding the unit, checks unchanged quarantine/epochs/delivery,
and observes the previously committed `ANALYZING` state. At 1481-1486 the raw mutation
observer reads the committed proposal through lock-free `store.peek`; the assertion at
1529 requires exactly `BLOCKED_UNSAFE`. Store publication occurs after the hook at
`infrastructure/sketch_generation/fakes.py:268`.

The label `c8_commit` is still appended before actual publication. It is only an order
marker: the committed-state observation at raw mutation is the independent proof that
closes the original gap. A separate read-only reviewer reached the same conclusion.

Both existing mutation probes were independently rerun against these exact test bytes:

- Claude's probe: exit 0, reporting that the no-coordinator sink fails R31 with
  `the sink never reached the coordinated publication`, while the real sink passes.
- Original Codex probe: exit 1 at the same assertion, as required. This is expected
  rejection of the deliberately broken sink, not a failure of the real implementation.

**N1 closed.** Follow-up 3A explicitly supersedes the old byte-equality claim with JSON
value equality and determinism. This matches the decoded-object assertions in
`test_sketch_proposal_contracts.py:148-150`.

**N2 closed.** The correction names the three service-level samples: requested,
pending_teacher_review and cancelled. R30 and the pure domain function checks are cited
separately; no claim of service coverage at every state remains in the new disposition.
Historical note bytes were preserved, with explicit superseding statements in follow-up 3A.

## Independent verification

Existing repository venv, CPython 3.12.10; PYTHONPATH and MYPYPATH point to this worktree's
`backend/src`. No package installed. Commands, exit codes and hashes are in the accompanying
review metrics and ignored receipts at `evidence/local/codex-followup3a-review-20261018/`.

| Check | Result |
|---|---|
| Focused SK1, six files | 175 passed, 0 skipped, exit 0 |
| Ruff, fourteen Python files | PASS, exit 0 |
| Strict mypy, fourteen Python files | PASS, exit 0 |
| Claude no-coordinator mutation probe | Expected rejection plus real-sink PASS, exit 0 |
| Original Codex mutation probe | Expected rejection, exit 1 |

Claude's focused JUnit hash and counts also match: 175 tests, 0 failures/errors/skips.
X01-X03 were not rerun: this delta changes only an SK1 test and evidence. The previously
audited regression receipts remain historical results for unchanged production source:
875 passed / 3 Pillow skips, not 878 passes. New documentation validators and final security
results are recorded in the accompanying metrics.

## Publication note: preserve the already-pinned CRLF receipt

Confirmed: `metrics/SK1_CODEX_FOLLOWUP3_REVIEW_20261018.json` has 349 CRLF sequences;
its SHA256 is `4fd43990328da8249535c377b439aca29060d625dc659e48f677025b57c88ed5`.
Follow-up 3A metrics already pin that exact hash. The current Git attributes resolve to
`text=auto eol=lf`, so ordinary staging would normalize its bytes and break that reference.

Recommended for the later publication plan: an exact-path `-text whitespace=cr-at-eol`
exception for this historical receipt, following the existing FEAT-048/049 precedent,
then compare the staged blob SHA256 with the pinned hash before committing. Do not silently
normalize this cross-referenced historical evidence. This review leaves the old receipt and
`.gitattributes` unchanged; new review documents and metrics use LF.

## Remaining owner decisions and next step

- F-5: disposition of the fixture-only `SketchChainEligibility` composition deviation from
  approved plan section 6.5. Technical review does not approve that deviation on the owner's behalf.
- N04/N08/N11 chain coverage and C03/C03b contract-column mappings remain partial.
- Actual A1 callback end-to-end remains NOT_RUN; N16 retains the planned Child-cancel
  response distinction and needs the recorded owner acknowledgement.
- Studio, PG, Redis/RQ, live provider/decoder and durable multi-process behavior remain outside
  the demonstrated SK1 runtime scope. BE2-01 still WAITING_STUDIO; BE2-02 PARKED.

The next step is scoped owner disposition and SK1 component acceptance, followed by an
authorized publication plan. Shared-branch creation can then use the accepted committed SK1
baseline under the already-reviewed consolidation proposal. There is no new consolidation
plan rewrite or additional code change required by this focused review.

Only new review evidence and current feature routing are written in this review. No production
source/test/fixture/approval/approved-plan edit, stage, commit, push or branch creation occurred.
