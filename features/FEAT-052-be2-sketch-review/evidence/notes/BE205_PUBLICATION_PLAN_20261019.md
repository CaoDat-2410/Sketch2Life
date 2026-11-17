# BE2-05 offline component publication plan — 2026-10-19

**Status: READY_FOR_OWNER_APPROVAL.** This is a proposal to publish the already accepted
`SKETCH_REVIEW_COMPONENT_OFFLINE` checkpoint as 20 local commits on
`feature/be2-05-sketch-review`. It does not authorize staging, committing, pushing, merging,
deploying, or opening BE2-06. The task card remains IN_PROGRESS / NOT_DONE; runtime and integration
gates remain open.

## 1. Snapshot and scope

- Worktree: `.worktrees/be2-05-sketch-review`.
- Branch / base: `feature/be2-05-sketch-review` at `58293f1a29ec630e2603c2860b6a2337fadfa713`.
- Planned publishable paths: **48** (44 new paths including this plan and the acceptance record,
  plus 4 modified tracked paths); staged paths: **0**.
- Checkpoint evidence: `approvals/COMPONENT_ACCEPTANCE.md` and Codex
  `evidence/notes/BE205_CODEX_REREVIEW_20261019.md` (`CODEX_REREVIEW_PASS_WITH_NOTES`, 0 P1/P2).
- The five ignored local evidence trees under `features/FEAT-052-be2-sketch-review/evidence/local/`
  are receipts, probes, temporary inputs and raw logs. They are excluded from all pathspecs.
- No CRLF exception is needed for the current publishable snapshot: the four JSON metrics files
  are LF, and `.gitattributes` reports `text=auto`, `eol=lf`. Recheck the index blob hashes before
  any eventual commit if any pinned file changes.
- Re-review binding: the Codex report SHA256 is
  `f070810f085119ad3aa1df35045048ced9bc0210bebe04612b739a33ea10dc40`; its metrics SHA256 is
  `c79f438d3682aa7ae54b10ddc38390b4a2bdb841c07c5ee062230da86d26e93e`. All 25 implementation
  snapshot hashes and all 26 local receipt hashes match. The metrics' seven `governance_sha256`
  values describe the pre-acceptance current-state documents; this acceptance intentionally updates
  those seven documents, so their current hashes differ. The Codex report and metrics remain
  byte-identical. This expected ledger change is not implementation drift.

## 2. Proposed 20 commits

Execute in order, on this branch, only after separately approving this plan. Use the exact
pathspecs below; never use `git add -A`. Do not push between commits. Each commit message is a
proposal and may only be changed by a separately reviewed plan amendment.

### C1 — feature scaffold and local-evidence ignore

Message: `docs(be2-05): add FEAT-052 scaffold and local evidence boundary`

```text
.gitignore
features/FEAT-052-be2-sketch-review/assets/REVIEW.md
features/FEAT-052-be2-sketch-review/assets/applied/.gitkeep
features/FEAT-052-be2-sketch-review/assets/approved/.gitkeep
features/FEAT-052-be2-sketch-review/assets/generated/.gitkeep
features/FEAT-052-be2-sketch-review/evidence/metrics/.gitkeep
features/FEAT-052-be2-sketch-review/evidence/notes/.gitkeep
features/FEAT-052-be2-sketch-review/evidence/raw/.gitkeep
features/FEAT-052-be2-sketch-review/evidence/screenshots/.gitkeep
features/FEAT-052-be2-sketch-review/src/.gitkeep
```

### C2 — approved implementation plan and task approval

Message: `docs(be2-05): freeze approved SKETCH_REVIEW_COMPONENT_OFFLINE plan`

```text
features/FEAT-052-be2-sketch-review/approvals/TASK_APPROVAL.md
features/FEAT-052-be2-sketch-review/plan/PLAN.md
features/FEAT-052-be2-sketch-review/plan/PLAN_R2_APPROVED.md
```

### C3 — review domain and domain regressions

Message: `feat(be2-05): add sketch review domain model and rules`

```text
backend/src/sketch2life/domain/sketch_review.py
backend/tests/unit/test_sketch_review_domain.py
```

### C4 — review contract, producer example fixture and contract test

Message: `feat(be2-05): define sketch review contracts and examples`

```text
backend/src/sketch2life/contracts/schemas/sketch_reviews.py
backend/tests/contract/test_sketch_review_contracts.py
features/FEAT-052-be2-sketch-review/fixtures/h_ai_review/sketch_review_examples.json
```

### C5 — application ports

Message: `feat(be2-05): define sketch review application ports`

```text
backend/src/sketch2life/application/ports/sketch_review.py
```

### C6 — shared decision coordination

Message: `feat(be2-05): coordinate sketch review decision fences`

```text
backend/src/sketch2life/infrastructure/sketch_review/coordination.py
```

### C7 — offline repositories and fake adapters

Message: `feat(be2-05): add sketch review offline stores and fakes`

```text
backend/src/sketch2life/infrastructure/sketch_review/fakes.py
```

### C8 — concrete infrastructure adapters

Message: `feat(be2-05): add sketch review infrastructure adapters`

```text
backend/src/sketch2life/infrastructure/sketch_review/__init__.py
backend/src/sketch2life/infrastructure/sketch_review/adapters.py
```

### C9 — application service

Message: `feat(be2-05): implement offline sketch review service`

```text
backend/src/sketch2life/application/services/sketch_review.py
```

### C10 — composed fixture harness

Message: `feat(be2-05): compose sketch review offline harness`

```text
backend/src/sketch2life/infrastructure/sketch_review/harness.py
```

### C11 — service behavior tests

Message: `test(be2-05): cover sketch review service decisions`

```text
backend/tests/unit/test_sketch_review_service.py
```

### C12 — eligibility and child-access tests

Message: `test(be2-05): cover sketch review eligibility and child access`

```text
backend/tests/unit/test_sketch_review_eligibility.py
```

### C13 — composed producer-to-review chain tests

Message: `test(be2-05): verify sketch producer and review chain`

```text
backend/tests/unit/test_sketch_review_chain.py
```

### C14 — race and rollback tests

Message: `test(be2-05): cover sketch review races and rollback`

```text
backend/tests/unit/test_sketch_review_races.py
```

### C15 — Codex review-fix regression tests

Message: `test(be2-05): pin sketch review re-review regressions`

```text
backend/tests/unit/test_sketch_review_review_fixes.py
```

### C16 — initial implementation evidence

Message: `docs(be2-05): record offline component implementation checks`

```text
features/FEAT-052-be2-sketch-review/evidence/metrics/BE205_CHECKS_20261019.json
features/FEAT-052-be2-sketch-review/evidence/notes/BE205_IMPLEMENTATION_EVIDENCE_20261019.md
```

### C17 — first Codex review record

Message: `docs(be2-05): record initial Codex review findings`

```text
features/FEAT-052-be2-sketch-review/evidence/metrics/BE205_CODEX_REVIEW_20261019.json
features/FEAT-052-be2-sketch-review/evidence/notes/BE205_CODEX_REVIEW_20261019.md
```

### C18 — review-fix evidence and executor handover

Message: `docs(be2-05): record review fixes and verification`

```text
features/FEAT-052-be2-sketch-review/evidence/metrics/BE205_REVIEW_FIX_CHECKS_20261019.json
features/FEAT-052-be2-sketch-review/evidence/notes/BE205_CLAUDE_TO_CODEX_HANDOVER_20261019.md
features/FEAT-052-be2-sketch-review/evidence/notes/BE205_REVIEW_FIX_EVIDENCE_20261019.md
```

### C19 — final Codex re-review evidence index

Message: `docs(be2-05): record PASS_WITH_NOTES offline re-review`

```text
features/FEAT-052-be2-sketch-review/evidence/README.md
features/FEAT-052-be2-sketch-review/evidence/metrics/BE205_CODEX_REREVIEW_20261019.json
features/FEAT-052-be2-sketch-review/evidence/notes/BE205_CODEX_REREVIEW_20261019.md
```

### C20 — owner acceptance, current-state routing and this plan

Message: `docs(be2-05): accept offline checkpoint and plan publication`

```text
docs/context/PROJECT_CONTEXT.md
docs/context/SOURCE_REGISTER.md
features/FEAT-044-be2-ai-job-foundation/plan/BE2_EXECUTION_TRACKER.md
features/FEAT-052-be2-sketch-review/CONTEXT.md
features/FEAT-052-be2-sketch-review/DECISIONS.md
features/FEAT-052-be2-sketch-review/approvals/COMPONENT_ACCEPTANCE.md
features/FEAT-052-be2-sketch-review/evidence/notes/BE205_PUBLICATION_PLAN_20261019.md
features/FEAT-052-be2-sketch-review/status/STATUS.md
```

## 3. Coverage and ordering

The 20 groups contain **48 distinct pathspecs**. Every currently modified or untracked,
non-ignored path is assigned exactly once; there are no overlaps, omissions or ignored local
artifacts. Recompute this equality against `git diff --name-only` plus
`git ls-files --others --exclude-standard` immediately before execution. Abort if the count or
path set differs. The group sizes are:

```text
C1–C20 = 10, 3, 2, 3, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 2, 3, 3, 8 = 48 paths
```

The implementation sequence preserves dependency order: domain/contracts → ports/coordinator →
fakes/adapters/service/harness → focused tests → implementation/review evidence → owner and shared
current-state records. Tests are not claimed to be independently green at intermediate commits;
run the full approved offline verification on the final planned snapshot before beginning C1.

## 4. Execution checks if the plan is approved

Before C1: verify branch and base, clean staged index, exact 48-path coverage, local-only ignore
rules, approved/frozen plan hashes, all 25 implementation snapshot hashes, all 26 local review
receipt hashes, report/metrics hashes, line endings, and all four repository validators; run
focused05, SK1, selected contract, BE2-02/03, Ruff and mypy checks recorded in the re-review
receipt. Compare current governance files to the post-acceptance values, not to the historical
`governance_sha256` values captured by the review metrics.

For every C1–C20: stage only that group's explicit pathspecs; compare the staged path set to the
group list; run `git diff --cached --check`; verify pinned byte hashes for any included artifact;
run `python tools/validate_repository_security.py` immediately before creating that commit. Stop
on any mismatch, non-VALID result or unplanned file. Do not amend/rebase or force.

After C20: verify exactly 20 new commits and 48 paths against the plan, `git status` clean,
all four validators and final focused checks pass, and all pinned hashes/blobs match. Push is a
separate owner decision after rechecking the actual remote tip and rerunning security.

## 5. Exclusions and open gates

- Excluded: every ignored path under `features/FEAT-052-be2-sketch-review/evidence/local/`;
  no receipt, probe, raw test output or private planning input is published.
- Not included or authorized: merge into `feature/be2-01-07`, push, deploy, next-card work,
  runtime/provider execution, SQL/durable fencing, BE1 integration, BE2-14 adoption, routes/UI,
  cross-feature integration, or full BE2-05 completion.
- The accepted checkpoint remains offline and single-process where the fakes/coordinator are
  involved. Runtime and integration gates remain open after publication.
