# P2-T3 Phase B B4 — local runner implementation

**Status:** IMPLEMENTED AND TESTED. Evidence ID `EV-003-T3-12`, indexed in `evidence/README.md`
and summarized in `CONTEXT.md`, "P2-T3 Phase B B4 runner implementation status (2026-09-07)".
This note itself remains local-only (`evidence/notes/` is gitignored); only the safe summary is
published. It does not authorize a model call, Lightning/GPU execution, profile freeze, runtime
default, or B5 conclusion.

**Status update (2026-09-07, later the same day):** "REVIEW AND COMMIT PENDING" below is the
status at the time this note was first written. The runner and its tests were subsequently
committed (`c3d3a2b`) and then fixed twice under real Lightning execution — a companion-audio
P2-T1 fix (`eec214f`) and a `source_image_ref.artifact_ref` fix (`88c90f8`) — see
`P2_T3_PHASE_B_B4_QUALITY_BENCHMARK_EXECUTION.md` (`EV-003-T3-09`) for that later, separate
milestone. The verification numbers below (19 focused tests, 622 collected) predate both fixes
and their added regression tests; they are left unchanged here as a record of that point in time.

## Authority and scope

The owner authorized local B4 runner and unit-test implementation after approving the held-out
fixture package. The scope was limited to the owner-approved manifest, pre-authored ground truth,
matching rule, and explicit C1-v2 prompt. No B4 runtime execution was authorized.

## Implemented files

- `backend/src/sketch2life/benchmark/vision_b4_quality_benchmark.py`
- `backend/tests/unit/test_vision_b4_quality_benchmark.py`
- `fixtures/vision-b4/manifest-v1.json` status updated from `OWNER_REVIEW_REQUIRED` to
  `OWNER_REVIEW_APPROVED` to reflect the recorded owner review.

## Runner boundaries

- Internal non-CLI `run_b4_quality_pass`; `B4_PASS_1` and `B4_REPEAT_1` are individual runs and
  are never pooled.
- Rejects an unapproved/malformed manifest, mismatched image/ground-truth/rule hash, wrong
  taxonomy/order, invalid authored references, or non-C1-v2 prompt before adapter construction.
- Generates only a temporary synthetic audio companion; earns all eight P2-T1 provenances before
  the adapter is created; cleanup runs in `finally`.
- Constructs the adapter with the explicitly verified C1-v2 prompt and the raw-output collector
  hook; exactly one adapter call per fixture and no retry.
- Scores schema-valid results under the frozen matching rule: deterministic maximum bipartite
  matching; endpoint/evidence integrity; fixed normalizer; confidence unscored; ambiguous-region
  accuracy `NOT_MEASURED`. Raw text, prompt text, local paths, candidates, and ground-truth text
  are structurally absent from reports.
- Fixture 06/07 relation caveat remains a B4 report-interpretation constraint, not a scoring
  override.

## Local verification (measured 2026-09-07, after the tie-break/eligibility test additions)

- Focused B4 unit suite: 19 passed.
- Full backend suite: 622 collected, 617 passed, 5 skipped, 0 failed, 0 errors.
- Ruff and `mypy --strict src`: clean (`54` source files).
- `validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`, and
  `validate_skeleton.py`: valid. `git diff --check`: clean.
- The live owner-approved package loaded with 8 fixtures and the expected ground-truth/matching
  hashes. No Qwen, model, GPU, Lightning, dependency, or `.vision.env` action occurred.

## Red-team hardening after initial implementation

An independent read-only review found no blocker but identified two medium-priority hardening
items. The runner now uses polynomial augmenting-path maximum matching plus a deterministic
feasible-choice tie-break rather than enumerating every matching, so schema-valid outputs with a
large candidate count do not create factorial/exponential work. No candidate cap was introduced, so
a large schema-valid candidate list stays a scored result rather than a new untyped runtime failure.
The test suite now also covers each authored-reference rejection class, invalid run labels, a large
candidate set, and separate pass/repeat invocation with no collector-state leak.

A follow-up review of that hardening closed three remaining coverage gaps in the same two files:
a tie-break test asserting the exact chosen assignment (shuffled inputs on both sides must still
resolve to ascending ground-truth then prediction IDs); an eligibility test proving an ineligible
lower-ID action/theme candidate does not consume or block the match that a higher-ID eligible
candidate earns; and stronger pass/repeat assertions proving each report independently carries
eight runs with equal, non-pooled aggregate counts and that both scratch directories are removed.

## Remaining gates

1. Review the uncommitted fixture metadata, runner, and tests; decide whether to commit/push.
2. Reconcile the operator-attested B2–B4 GPU ledger.
3. Obtain explicit B4 Lightning reauthorization, rerun readiness and require `READY` immediately
   before execution.
4. Run and report `B4_PASS_1` and `B4_REPEAT_1` separately, then evaluate B5 only within the
   already-approved evidence boundaries.
