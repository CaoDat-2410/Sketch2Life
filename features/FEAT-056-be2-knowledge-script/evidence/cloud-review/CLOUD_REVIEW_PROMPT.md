# BE2-07 — Independent Claude cloud rereview

Review the published BE2-07 final snapshot after remediation of the original Claude report.
Work independently: read actual source and tests, verify portable evidence, rerun checks when
the existing cloud environment permits, and report concrete remaining defects.

## Identity and authorization

- Repository: `CaoDat-2410/Sketch2Life`.
- Review branch: `feature/be2-07-knowledge-script`.
- Original inherited base: `23acf9e83e181305edfeb345be9a8e7eb9dbef88`.
- The launch message supplies `EXPECTED_REVIEW_COMMIT`. Verify that full SHA with
  `git rev-parse HEAD`; if a cloud work branch is used, confirm its reviewed source tree is
  exactly that commit before analysis. If missing or mismatched, report `SOURCE_SNAPSHOT_MISMATCH`.
- Feature root (F): `features/FEAT-056-be2-knowledge-script`.
- Read `AGENTS.md`, relevant governance, project context/source register, frozen approved plan
  `F/plan/PLAN_REV1_APPROVED.md`, and both task/publication approval records. The frozen plan
  retains its original pre-approval header; `TASK_APPROVAL.md` records the later approval.
- Component remains `NOT_ACCEPTED`; card `IN_PROGRESS / NOT_DONE`. Review is separate from
  owner acceptance, actual08 adoption and runtime/integration gates.

Review only. Do not modify source/tests/plan/status/metrics/approvals, install dependencies,
stage/commit/push, open a PR, merge, deploy, contact application providers or run Lightning.
Use existing Python/dependencies. No DB, HTTP application run, child media or live credentials.
Temporary probes/mutants may run on a copy or in memory. Record new outputs only under the
ignored `F/evidence/local/claude-cloud-review-<UTC>/`; never overwrite historical evidence.

## Start with portable evidence

Read `F/evidence/cloud-review/README.md` and `EXPORT_PROVENANCE.json`, then run:

```sh
python F/evidence/cloud-review/verify_evidence.py
```

Replace the F shorthand with the actual feature path in every command. This standard-library
verifier is a starting point; independently inspect its checks and the source/tests it pins.
Original raw paths in old notes/maps identify historical local receipts. They are not commands
to fetch private files or evidence that all local-only checks have been independently verified.
The portable XML is a documented sanitized derivative: its hash differs from the old raw XML.
The historical 601-entry manifests include local-only refs and publication-updated documents;
use the verifier's explicit scope rather than claiming the whole old snapshot is current.

Read:

- `F/evidence/cloud-review/original-review/REVIEW.md` (the original 3 P2 / 6 P3 findings).
- `F/evidence/notes/CLAUDE_REMEDIATION_20261020.md` and `CLAUDE_RESOLVER_REGRESSION_20261020.md`.
- `F/evidence/notes/INDEPENDENT_POST_CLAUDE_REVIEW_20261020.md` (claims, not a trusted verdict).
- `F/evidence/metrics/OFFLINE_HANDOFF_BE207_20261020_POST_CLAUDE.md`.
- `F/evidence/metrics/ACCEPTANCE_MAP_BE207_20261020_POST_CLAUDE.json`.
- `F/evidence/metrics/BE207_FINAL_OFFLINE_CHECKS_20261020_POST_CLAUDE.json`.
- Published portable batch, selected-files, mutation and provenance receipts.

Historical claims to verify within the available evidence: 262 focused07 tests pass; the
56-file batch has 1,587 cases, 1,584 passes / 3 Pillow skips / 0 fail-error; 42 map rows with
354 exact passed-node references. Keep the three Pillow skips and the excluded V2 server
module `NOT_RUN`. X01/X02 distinguish product support from evidence-only gates. Other checkout
baseline invariants that lack published original inputs are `NOT_VERIFIABLE_ON_CLOUD`.

## Verify old findings and related regressions

1. **P2-1:** product tests no longer freeze 572 shared backend files or a fixed count of task07
   test modules. Task-specific evidence can still check its baseline/profile. Distinguish the
   extracted baseline assertion experiment from an actual complete evidence-runner execution.
2. **P2-2:** domain and DTO use the same comparison helper for punctuation/spacing, Unicode Cf,
   NFKC/fullwidth and reverse token containment. Check empty signatures and token boundaries.
   Canonical text must remain unchanged. Probe plausible overblocking and bypasses; semantic
   truth, all homoglyphs and paraphrases are outside the claimed heuristic guarantee.
3. **P2-3 / P3-1:** exact requested hash/id/version negatives; stale expected context/audience;
   same-revision changed audience/source record; replay receipt body/readiness/status. Verify
   all six former surviving mutants are killed by real assertions, not collection/import errors.
4. **P3-2:** unchanged submitted claims retain their original attestor; changed/new claims use
   the appropriate trusted catalog/current Teacher attribution. Check mixed lists and no-op edits.
5. **P3-3:** mutation pause denies unseen writes while read/resolve/replay preserve all other
   current guards. Queued publication stays invisible until the held transaction boundary exits.
6. **P3-4:** recall denial and new-bundle remedy are an explicit frozen R01 disposition. Assess
   implementation against that approved rule; do not silently require a different architecture.
7. **P3-5:** readiness/action truth table, explicit unavailable reason, record/resolver consistency,
   and no export when a fact section is missing.
8. **P3-6:** H1 ordering, LF and untracked-file hygiene coverage. The exact frozen approval's EOF
   blank-line exception is preserved deliberately; do not claim it was removed. Prior immutable
   metrics/reviews/approval/plan must retain their pinned bytes.
9. **Evidence/tooling:** exact file-set/hash/size, XML/summary identities and status, receipt/log
   hashes, profile/baseline references and no-overwrite guards. Do not treat sanitized paths,
   missing historical local files, or Git publication document changes as product regressions;
   report limits and any actual unsupported claim accurately.

Inspect the diff against the inherited base and all task07 source/test files. The 12 commits
are publication groups of an already-reviewed final snapshot, not its execution chronology.

## Fresh checks and output

Run the six current task07 test modules first with a new JUnit and basetemp under your new
review directory. If dependencies permit, run the 56 modules in published `selected-files.json`,
Ruff, strict mypy, and the existing harness/architecture/skeleton/security validators. Use the
repository Python configuration and existing environment; report missing tools as NOT_RUN.
Do not substitute a smaller suite while describing it as the full historical batch.

Use assertions and small in-memory/copy probes to confirm suspicious behavior. Test collection
errors do not count as mutant kills. Capture actual commands, exit codes, counts and outputs.

Write `REVIEW.md` containing:

- Full reviewed commit/base, source pin/export verification and actual environment.
- One disposition for every old finding: `FIX_CONFIRMED`, `STILL_OPEN` or `DISPOSITION_VALID`,
  with concrete current file:line plus test/probe evidence.
- Any new findings, severity P0–P3, trigger, expected/actual result and reproducible evidence.
- Fresh checks versus historical portable evidence versus NOT_RUN/NOT_VERIFIABLE_ON_CLOUD.
- Verdict `CHANGES_REQUIRED`, `NO_BLOCKING_FINDINGS` or `REVIEW_INCOMPLETE` and its limits.

If quota or context ends early, save partial findings and precise remaining steps in the new
review directory and return `REVIEW_INCOMPLETE`. Finish with a concise Vietnamese report and
the full report path. Do not self-accept the component or mark the card done.
