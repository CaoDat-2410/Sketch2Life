# Codex review — SK1 Claude follow-up 3

- Verdict: **NEEDS_CHANGES**: 0 P1, 1 P2 verification finding, 2 P3 evidence wording notes.
- No new production-code defect found in the reviewed delta. The P3 cleanup-reason fix passes
  inspection and regression checks; the remaining P2 concerns the claim that R31 proves
  quarantine waits for the actual C8 commit.
- SK1 **NOT_ACCEPTED**; BE2-04 **IN_PROGRESS / NOT_DONE**. This review records no owner decision,
  Git publication, common-branch creation, runtime claim or full-card acceptance.

## Identity and input integrity

- Branch `feature/be2-04-sketch-generation`; HEAD/base
  `113cdf956a09336a0abf5561bd939f5e13b31ea0`; staged0. Implementation remains uncommitted.
- Claude follow-up note SHA256:
  `fb3b2e1ff1e7ad4337acc459612c349a76a4ae5796e7c3f53f7ffa1bd9cecdc7`.
- Claude follow-up metrics SHA256:
  `82136e02218102a9aeddba00058b3b6c43ccd7090edcd5609a7c46edf63c506d`.
- All15 source/test/fixture references in those metrics match SHA256 and byte length.
- Approval, approved plan and earlier metrics retain their pinned hashes. Original follow-up
  evidence and receipts are preserved; review outcomes are recorded separately here.

## Confirmed improvements

- `schedule()` selects `latest.versions[current.version - 1].status_reason`, retaining the
  original job version's reason even if a newer version becomes current. Contiguous immutable
  version history supports that lookup. The consent/Teacher tests assert immediate cancellation
  and exact failure codes; the refused path spies the actual cancellation request.
- An additional in-memory review probe completed v1, revised to v2, cancelled v2, then resumed
  v1 scheduling: v1 cleanup used `SUPERSEDED_BY_REVISION`, while v2 retained
  `CANCELLED_BY_TEACHER`. No persistent source mutation was made by that delegated probe.
- R31/R33 now obtain genuine quarantine intents from the foundation's UNSAFE completion
  transaction. R33 covers both service instances draining both producer types and asserts the
  exact once-per-ref bump union. The old synthetic cases remain useful additional coverage.
- P02 checks text-only side-reference output plus actual result-document job/attempt lineage.
  P06 checks persisted proposal/job identities and actual generator call counts across replays.
- C06 uses the actual offline producer services; strict schemas accept its record, event,
  device projection and copy report. Quoted ETag, version and overlay-level values are coherent.

## F3-R31 — P2: the before-commit marker does not prove post-commit quarantine

Location: `backend/tests/unit/test_sketch_generation_races.py:1468–1494`, especially the
`on_commit_boundary` hook. Actual fake-store publication follows the hook at
`backend/src/sketch2life/infrastructure/sketch_generation/fakes.py:268`.

The hook appends `c8_commit_boundary` and releases the sink, then returns so the store can
publish staged state. There is no handshake ensuring the worker reaches publication while
the unit remains held, nor an assertion observing the committed state at raw mutation.
Consequently quarantine can happen after the marker but before the actual commit and still
satisfy `[c8_commit_boundary, quarantine_applied, drain_returned]`.

Confirmed by a review-only in-memory mutation probe. It removed the artifact sink's coordinator
call while preserving failure injection, raw mutation and audit behavior. A controlled release
kept the before-commit hook open until that raw mutation completed. The existing R31 assertions
still passed, although committed proposal state at mutation was **analyzing**, before the C8
`blocked_unsafe` publication. No production/test source file was patched.

Probe output:

```json
{"observations": [{"committed_pipeline_states_at_mutation": ["analyzing"], "quarantined_before_c8_commit": true}], "r31_assertions_passed_with_bypassed_lock": true}
```

Correction: add a worker publication-attempt handshake while C8 is deliberately held; assert
refs/epochs and delivery completion remain unchanged during that held window; observe committed
state before raw quarantine applies. The test must fail for the demonstrated no-coordinator
mutation. Keep the real completion-generated intent. Update the R31 evidence to the actual
commit boundary. Until then its completion provenance is demonstrated, but its lock/order claim
remains partial. This is not evidence that the current coordinated production path is broken.

## N1 — P3: C06 proves JSON value equality, not byte equality

`evidence/notes/SK1_CLAUDE_FOLLOWUP3_20261018.md:37` says "byte-level JSON equality".
`backend/tests/contract/test_sketch_proposal_contracts.py:148–150` compares decoded dictionaries.
That proves deterministic values and semantic fixture/producer equality; whitespace, escaping
and key order may differ. Correct the evidence wording; no extra byte-comparison test is
required for the current semantic contract.

## N2 — P3: narrow the P09 state-coverage description

`evidence/notes/SK1_CLAUDE_FOLLOWUP3_20261018.md:68` says the service test checks device view
"at every state". `backend/tests/unit/test_sketch_generation_service.py:198–210` samples
requested, pending review and cancelled states. Name those samples and cite other assertions
separately if needed. Do not enlarge a mapping claim merely because all tests are green.

## Checks and receipt audit

Independent checks used the existing CPython3.12.10 environment with PYTHONPATH/MYPYPATH pinned
to this worktree's source; no dependency installed:

| Check | Result |
|---|---|
| Focused SK1, six test files | 175 passed, 0 skipped, exit0 |
| Ruff, fourteen Python files | PASS, exit0 |
| Strict mypy, fourteen Python files | PASS, exit0 |
| R31 review mutation probe | exit0; demonstrates that the bad sink passes the current test |
| Initial untracked byte audit | 36 files, 0 CR-containing files; Claude's whitespace receipt also reports0 issues |

Claude's four JUnit hashes and XML counts were independently checked. Their receipts report
focused175/0skip; X01 337pass/1skip; X02 411pass/1skip; X03 127pass/1skip. The three regression
skips are explicitly live-app imports needing Pillow; they are not passes. X01–X03 were not
rerun because the audited final hashes and receipts match and those suites do not import SK1.
Claude's four validator receipts were inspected; all record exit0. Any new validator run for
this review's documentation changes is recorded in the separate review metrics.

Raw independent receipts and the mutation script/log are ignored under
`evidence/local/codex-followup3-review-20261018/`. A restricted old X01 temp directory could
not be enumerated during a receipt-file listing; directly referenced JUnit/log files were
read and hashed successfully, so the audited results do not depend on that temp directory.

## Remaining scope and next action

- Make the R31 test/evidence correction and the two wording corrections, then focused re-review.
  A test-only change does not itself require rerunning unrelated875 regression cases; rerun
  affected checks and preserve source-bound earlier receipts unless their inputs change.
- F-5 owner disposition, N04/N08/N11 chain partials, C03/C03b contract mapping, the unrun A1
  callback and N16 acknowledgement remain as already recorded. Do not infer acceptance here.
- No consolidation-plan rewrite is needed. After the scoped SK1 decisions, final review and
  authorized commit, the accepted consolidation plan can use that committed baseline.
- Source/tests/fixtures/approval/approved plan were read only. This review adds its own note,
  metrics and ignored probes, and updates current review routing in STATUS/CONTEXT/DECISIONS
  and the evidence index without rewriting prior evidence.
