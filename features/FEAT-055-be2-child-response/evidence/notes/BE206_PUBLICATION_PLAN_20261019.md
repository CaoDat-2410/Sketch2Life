# BE2-06 offline component publication plan — 2026-10-19

**Status: READY_FOR_OWNER_APPROVAL.** Proposed **14 local commits / 45 distinct paths**
on `feature/be2-06-child-response`. The owner accepted CHILD_RESPONSE_COMPONENT_OFFLINE
and requested this plan for review. Staging/commit execution is not authorized by this plan.
Card stays **IN_PROGRESS / NOT_DONE**; runtime and integration remain open.

## 1. Authority, snapshot and scope

- Verbatim acceptance: [COMPONENT_ACCEPTANCE.md](../../approvals/COMPONENT_ACCEPTANCE.md).
  Codex review **PASS_WITH_NOTES**, B6-CR01 closed, zero remaining known P1/P2 offline.
- Branch: `feature/be2-06-child-response`; worktree `.worktrees/be2-06-child-response`.
- Baseline HEAD: `818ec0778ffb044a77d95c425193f4f02fc3aa44`.
- Observed local upstream/tracking refs for task06 and `feature/be2-01-07` are at that same
  base. These are local observations, not a fresh remote-tip verification or a push guarantee.
- Inventory: **4 modified tracked + 41 new = 45 paths**, including this plan and acceptance.
  Staged paths **0**. No code/test edits to existing01–05; all 558 baseline files unchanged.
- Publish exactly the paths below. Ignored `evidence/local/` receipts, probes, scratch trees,
  environments and raw logs never enter pathspecs. No `.gitattributes` change is needed.
- The original implementation plan, task approval, prompt, review, metrics, tests and source
  retain their reviewed bytes. Only current-state records and the new acceptance/plan have
  been added or synchronized. Earlier dated shared-ledger entries retain their original bytes.
- No push, merge/shared-branch update, deploy, next-card code, dependency install, runtime
  service, provider or Studio command is included. Those actions need their own user instruction.

## 2. Exact ordered groups

All paths are repository-relative, literal and exhaustive. Execute C1-C14 in order only
after owner approval. Never stage by parent directory, wildcard or `git add -A`. No amend,
rebase or recreation of the already published01–05 commits. No push between groups.

The feature scaffold is complete in C1 so harness validation works throughout. C1 documents
describe the accepted final snapshot being published; they do not assert that the remaining
groups have already been committed. Cross-file links to later groups resolve at C14.


### C1 — Feature governance and local evidence boundary (19 paths)

Message: `docs(be2-06): establish FEAT-055 approval and publication records`

Complete required feature skeleton is present from C1; no partial feature folder. Current-state records describe the final accepted snapshot being published, not successful execution of later groups.

```text
.gitignore
features/FEAT-055-be2-child-response/CONTEXT.md
features/FEAT-055-be2-child-response/DECISIONS.md
features/FEAT-055-be2-child-response/approvals/TASK_APPROVAL.md
features/FEAT-055-be2-child-response/plan/PLAN.md
features/FEAT-055-be2-child-response/plan/PLAN_REV5_APPROVED.md
features/FEAT-055-be2-child-response/status/STATUS.md
features/FEAT-055-be2-child-response/assets/REVIEW.md
features/FEAT-055-be2-child-response/assets/applied/.gitkeep
features/FEAT-055-be2-child-response/assets/approved/.gitkeep
features/FEAT-055-be2-child-response/assets/generated/.gitkeep
features/FEAT-055-be2-child-response/src/.gitkeep
features/FEAT-055-be2-child-response/evidence/README.md
features/FEAT-055-be2-child-response/evidence/metrics/.gitkeep
features/FEAT-055-be2-child-response/evidence/notes/.gitkeep
features/FEAT-055-be2-child-response/evidence/raw/.gitkeep
features/FEAT-055-be2-child-response/evidence/screenshots/.gitkeep
features/FEAT-055-be2-child-response/evidence/notes/BE206_IMPLEMENTATION_PROMPT_20261019.md
features/FEAT-055-be2-child-response/evidence/notes/BE206_PUBLICATION_PLAN_20261019.md
```

No new test file in this group; verify imports and required validators.


### C2 — Participant/version domain and domain assertions (2 paths)

Message: `feat(be2-06): add participant-scoped child response state rules`

Immutable response attribution, participant/version terminal decline, visibility transitions and viewer revision preconditions.

```text
backend/src/sketch2life/domain/child_response.py
backend/tests/unit/test_child_response_domain.py
```

New tests on this intermediate tree: `backend/tests/unit/test_child_response_domain.py`.


### C3 — Strict command, projection and event contracts (2 paths)

Message: `feat(be2-06): define strict child response contracts`

Versioned DTOs and explicit safe payload mapping; extra client identity/audience fields remain forbidden.

```text
backend/src/sketch2life/contracts/schemas/child_responses.py
backend/tests/contract/test_child_responses.py
```

New tests on this intermediate tree: `backend/tests/contract/test_child_responses.py`.


### C4 — Application boundaries (1 paths)

Message: `feat(be2-06): define child response application ports`

Unit of work, current disclosure/turn authority and exact public review access boundaries.

```text
backend/src/sketch2life/application/ports/child_response.py
```

No new test file in this group; verify imports and required validators.


### C5 — Response commands and receipt replay (1 paths)

Message: `feat(be2-06): implement child choices and authorized receipt replay`

New commands and replay remain separate; a winning receipt is reread after CAS rollback. Service/race tests follow the complete harness in C9/C10.

```text
backend/src/sketch2life/application/services/child_response.py
```

No new test file in this group; verify imports and required validators.


### C6 — Atomic single-process fake persistence (1 paths)

Message: `feat(be2-06): add atomic response and receipt fixture storage`

Atomic state/history/receipt/event publication, rollback, unique operation handling and local-generation guard for B6-CR01.

```text
backend/src/sketch2life/infrastructure/child_response/fakes.py
```

No new test file in this group; verify imports and required validators.


### C7 — Public dependency and authority adapters (1 paths)

Message: `feat(be2-06): adapt public review access and scoped turn authority`

Public BE2-05 exact access/read and BE2-03 current-turn adapters plus separate synthetic disclosure/Teacher grants; no producer private state access.

```text
backend/src/sketch2life/infrastructure/child_response/adapters.py
```

No new test file in this group; verify imports and required validators.


### C8 — Actual fixture chain and adapter checks (2 paths)

Message: `test(be2-06): compose the response harness with public dependencies`

Harness imports require C2-C7. Adapter tests use this real fixture composition and must not appear earlier.

```text
backend/src/sketch2life/infrastructure/child_response/harness.py
backend/tests/unit/test_child_response_adapters.py
```

New tests on this intermediate tree: `backend/tests/unit/test_child_response_adapters.py`.


### C9 — Service policy and replay regressions (1 paths)

Message: `test(be2-06): pin response authorization and terminal choice behavior`

Current disclosure, exact review/version, If-Match, fresh-key aliases, restore and cross-turn terminal decline assertions.

```text
backend/tests/unit/test_child_response_service.py
```

New tests on this intermediate tree: `backend/tests/unit/test_child_response_service.py`.


### C10 — Atomicity, nested commits and scope races (1 paths)

Message: `test(be2-06): cover response rollback and nested commit races`

Before/after rebind, rollback and competing receipts; B6-CR01 inner commit must survive stale outer publication.

```text
backend/tests/unit/test_child_response_races.py
```

New tests on this intermediate tree: `backend/tests/unit/test_child_response_races.py`.


### C11 — Producer examples and 04-to-06 chain proof (3 paths)

Message: `test(be2-06): bind producer examples to the reviewed fixture chain`

Example producer, JSON artifact and consumer assertions ship together; JSON value equality, not byte-order equality. Synthetic child fixtures only.

```text
backend/src/sketch2life/infrastructure/child_response/examples.py
features/FEAT-055-be2-child-response/artifacts/CHILD_RESPONSE_EXAMPLES.json
backend/tests/unit/test_child_response_chain.py
```

New tests on this intermediate tree: `backend/tests/unit/test_child_response_chain.py`.


### C12 — Immutable implementation and deferred-runtime evidence (7 paths)

Message: `docs(be2-06): preserve offline verification and deferred runtime evidence`

Preserve reviewed bytes, including historical NOT_ACCEPTED fields. Raw local receipts remain ignored; future runtime checklist is not an executed result.

```text
features/FEAT-055-be2-child-response/evidence/metrics/BE206_IMPLEMENTATION_CHECKS_20261019.json
features/FEAT-055-be2-child-response/evidence/notes/BE206_IMPLEMENTATION_EVIDENCE_20261019.md
features/FEAT-055-be2-child-response/evidence/notes/BE206_CODEX_IMPLEMENTATION_REVIEW_20261019.md
features/FEAT-055-be2-child-response/evidence/notes/BE206_ACCEPTANCE_AUDIT_20261019.md
features/FEAT-055-be2-child-response/evidence/notes/BE206_HANDOVER_20261019.md
features/FEAT-055-be2-child-response/evidence/notes/BE206_OFFLINE_BATCH_PROFILE_20261019.md
features/FEAT-055-be2-child-response/evidence/notes/BE206_DEFERRED_RUNTIME_BATCH_20261019.md
```

No new test file in this group; verify imports and required validators.


### C13 — Verbatim owner offline acceptance (1 paths)

Message: `docs(be2-06): record owner acceptance of the offline component`

Accept CHILD_RESPONSE_COMPONENT_OFFLINE only; preserve all runtime/integration gates and IN_PROGRESS / NOT_DONE card status.

```text
features/FEAT-055-be2-child-response/approvals/COMPONENT_ACCEPTANCE.md
```

No new test file in this group; verify imports and required validators.


### C14 — Project source and execution routing (3 paths)

Message: `docs(be2): route the accepted child response checkpoint`

Append the latest acceptance/routing facts; earlier dated checkpoints remain byte-identical. No task07 activation or shared-branch publication is implied.

```text
docs/context/PROJECT_CONTEXT.md
docs/context/SOURCE_REGISTER.md
features/FEAT-044-be2-ai-job-foundation/plan/BE2_EXECUTION_TRACKER.md
```

No new test file in this group; verify imports and required validators.


## 3. Checks before every eventual commit

1. Reconfirm branch, expected parent HEAD, zero initial staged files, and immutable input
   hashes against the approved plan snapshot. The remaining working diff must equal exactly
   the not-yet-committed groups. Stop on unknown changes, drift, or a different feature's files.
2. Stage only that group's literal paths, then compare the sorted `git diff --cached --name-only`
   list with the exact group. Check `git diff --cached --check` and ordinary `git diff --check`.
3. Read index blobs as binary (`git cat-file blob :path` via byte-preserving subprocess),
   compute SHA256/length, and compare with approved working bytes and any pinned hash.
   A Git object ID is not a SHA256 of file bytes. Do not hash PowerShell-decoded text output.
4. Run required harness and architecture validators, plus skeleton on C1 or any structure
   change. Validate the actual index-derived intermediate tree; the working tree already
   contains later groups and cannot prove the staged snapshot is complete. Use the tested
   ordering below and run any new group's test file with imports pointing to that snapshot.
5. Run `python tools/validate_repository_security.py` **after staging/list validation and
   immediately before each individual commit**. Save command, exit, output, timestamp and
   staged list under the ignored feature-local execution receipt directory. Require exit0
   and REPOSITORY_SECURITY_VALID. No tracked edit between that pass and commit.
6. Commit the specified group/message. Verify its changed paths equal the group, committed
   blob bytes match the approved bytes, index returns empty, and remaining diff is the union
   of later groups. Record parent/commit SHAs, per-file SHA256/length and check receipts.

All four repository validators and final whitespace checks must pass after C14. Reusing the
existing final 01–06 regression receipt is allowed only when all tested source/test/config
bytes match its pinned inputs exactly. Any implementation/config change requires review
and a fresh required final batch; a docs-only acceptance/publication change does not.
Do not rewrite frozen evidence to make its historical NOT_ACCEPTED fields look current.

## 4. Coverage, hashes and EOL

Counts by group (C1-C14): **19/2/2/1/1/1/1/2/1/1/3/7/1/3 = 45**. Coverage is 45/45,
no duplicate, missing, unexpected or ignored path. The machine-readable group/byte manifest
and checks are ignored local execution aids; this publishable plan contains the full list.

- Independently checked **31 hash/size bindings**: 14 new source/test files, the JSON fixture,
  frozen approved plan, execution prompt and 14 local raw receipts; 0 mismatch.
- Frozen plan Rev5 SHA256:
  `65299121abc3576c344a95f00369e5f18764c51faa8b1dee7dbd39a16b5804f0`.
- TASK_APPROVAL SHA256:
  `37dc9f73bcf31d527a09aec45ac5d499d5f6d054555c09b404d4b075d8107b4a`.
- Reviewed metrics SHA256:
  `7c124d9c029b7e8452e7824ea3dfdab25d3449047413fd0d865bdf00213760f3`.
- Independent review SHA256:
  `3ab6d3e5bf3c21c3571c7123dd2d4eefaaeff72e03999b0fc3f560c5c9aeb7b3`.
- Prompt SHA256:
  `56a47968fca472fda86632c70c3ef31fddae7a2264e8233db9766bd361d81719`.
- Source/test and fixture hashes are recorded in the unchanged reviewed metrics; historical
  owner_acceptance=false/NOT_ACCEPTED there refers to the pre-acceptance review checkpoint.
- All 41 new publication files use UTF-8 LF, no BOM or CR; tracked changes also preserve LF.
  Existing `text=auto eol=lf` therefore preserves every pinned new file's working bytes in
  the index. Recheck index SHA256 before each commit; never silently normalize a pinned file.
- New local receipt trees remain ignored. Existing evidence, approval and runtime packages
  in other features are unchanged; `.gitattributes` is unchanged.

## 5. Verification of this publication split

A temporary extracted HEAD tree was overlaid in C1-C14 order without creating any Git branch, worktree registration, index, commit or push. Harness, architecture and skeleton validators passed on all 14 intermediate trees. Each newly introduced test file ran once at its owning group: C2=28 pass; C3=29 pass; C8=21 pass; C9=44 pass; C10=21 pass; C11=12 pass. Total 155 pass, 0 skip. PYTHONPATH/MYPYPATH pointed only at the temporary tree backend/src; imported harness paths were checked. This proves the proposed split is executable offline; no real publication commits have been made. Raw logs/JUnit and dry-run.json remain in the ignored publication-planning directory.

The already completed full required offline batch selected50 files and collected1325:
**1322 pass / 3 skip / 0 failure or error**, including **155 BE2-06 pass / 0 skip**.
The three live-app import skips require missing Pillow; the Pillow-dependent Vision V2 server
module was NOT_RUN. This is offline regression evidence, not runtime/integration closure.

## 6. Future gates after local publication

When separately instructed to push, first confirm a clean index/tree, the exact reviewed tip
and intended remote branch. Fetch/recheck the **actual** task remote tip with `ls-remote`;
require the planned ancestry/fast-forward, no unexpected remote commits, and security exit0
immediately before push. Push only the exact task branch, no force. Verify remote tip equals
local HEAD and save ignored receipts. A later update of `feature/be2-01-07` must use its then-current
tip and reviewed task ancestry; do not assume the shared branch has stood still.

No shared-branch update, task07 activation or runtime/integration acceptance is included in
this 14-commit plan. Frozen A17 package/base and all deferred runtime gates remain unchanged.
