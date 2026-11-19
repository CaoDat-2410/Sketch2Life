# FR-C-08 Draft 3 / Draft 5 Fresh-Context Cold Review

**Date:** 2026-11-16  
**Verdict:** **CHANGES REQUIRED**  
**Review scope:** Planning documents only. This is not Task Approval, implementation authorization, or launch authorization.

## Worktree identity and status

- Worktree: `D:\GitHub\Sketch2Life\.worktrees\m2-s2`
- Branch: `feature/feat063-m2-s2`
- HEAD: `5de30674bc826591ad4b3cc00fca53c7597ead51` (matches the requested identity)
- Branch relation: `ahead 4` of `origin/feature/feat063-m2-s2`.
- Before creating this report, the worktree had 69 status entries: 24 modified, 45 untracked, and 0 staged. These existing changes were preserved.

The worktree has no root `.codex/` directory. The shared checkout's `.codex/sketch2life-harness.md` was read, along with the worktree `AGENTS.md` and the `sketch2life-harness` skill. No repository file other than this new report was edited.

## Finding

### P2 — A repeated input pin is malformed, so the required pin gate fails

The SHA-256 pin for `features/FEAT-063-system-architecture-rearchitecture/evidence/FR_C08_ROUTE_AND_READINESS_DRAFT2_COLD_REVIEW_20261115.md` is recorded with only 63 hexadecimal characters in both:

- Lifecycle Contract Draft 3, §10, line 266.
- Exact-path Allowlist Draft 5, §11, line 194.

Both rows declare 3,449 bytes and `42A94A0E228ED403AFA234FA54E25D0B236083AE5686FA95165761FADFF0054`. The file is present at 3,449 bytes; its observed SHA-256 is `42A94A0E228ED403A4FA234FA54E25D0B236083AE5686FA95165761FADFF0054` (64 hexadecimal characters). The declared value therefore cannot match the observed SHA-256. The size agrees, but that does not validate the pin.

**Suggested fix:** In a successor revision, re-hash the intended evidence file and record the verified 64-character value in both pin registers. Preserve these pinned snapshots; do not silently repair them. Repeat the full pin audit before resuming the semantic cold review.

P1 findings: none assessed. P3 findings: none assessed. The substantive review stopped at the failed pin gate, so those severities do not imply the unreviewed content is clear.

## Pin audit

Every row in the requested registers was re-hashed, using the main checkout only for Draft 3 rows explicitly marked as main-checkout comparisons; all other rows were checked in this worktree.

| Register | Rows | Exact matches | Invalid/mismatching pins |
|---|---:|---:|---:|
| Draft 3 §9 | 38 | 38 | 0 |
| Draft 3 §10 supplemental inputs | 19 | 18 | 1 |
| Draft 5 §4 | 21 | 21 | 0 |
| Draft 5 §5 | 34 | 34 | 0 |
| Draft 5 §6 | 7 | 7 | 0 |
| Draft 5 §11 | 12 | 11 | 1 |
| **Total** | **131** | **129** | **2 occurrences of the same malformed pin** |

No referenced file was missing. All other 129 row pins matched both declared size and SHA-256. The task-listed top-level pins for Draft 3, Draft 5, the independent proposal, worktree authority/SRS/DTR/decisions, Draft 4 documents and review, M2 report and snapshot, approval ledger, and main-checkout Rev60 authority/SRS comparison also matched their stated sizes and hashes. That verifies byte identity only; it does not verify the documents' semantic claims.

## Review coverage

### Verified

- Worktree path, branch, HEAD, and pre-report status were read directly.
- The required pin tables and all 131 listed input rows were inspected and hashed. Main-checkout comparison rows were hashed from `D:\GitHub\Sketch2Life`; remaining rows were hashed from the worktree.
- The Draft 3 and Draft 5 top-level target pins and the task-listed source pins matched.
- The single malformed source pin is duplicated in the two cited registers; no hash was repaired.

### Not verified because review stopped at the pin gate

- Whether worktree authority, unsigned Rev68, D-203/D-208, the Rev57 DTR companion, and the main-checkout Rev60 lineage are accurately reconciled in the draft prose.
- The Rev68 18-state inventory, 13 cancel states, explicit DELETE eligibility, purge/revocation/fencing rules, owner-module deletion, reference proof, retry behavior, quota/sample preservation, audit/retention limits, blockers, owner questions, real-data gate, and M2 PARTIAL / NOT COMPLETE status.
- Whether the independent proposal is labeled not owner-approved, whether all eight blocker areas are recorded non-bindingly, and whether Rev68/DTR/source gaps remain unresolved.
- Whether Draft 5's E/N set is safely empty, exact-path classifications and frozen H paths are accurate, dirty and other-lane paths are excluded, migration and command ceilings are properly bounded, approval and launch are withheld, gate categories are distinct, and Draft 1 / approval-ledger history is described correctly.
- Whether any target document claims S2 complete, uses real child data, or approves or launches FR-C-08.
- Runtime behavior, test behavior, database state, and migration application.

## Independence and boundaries

This was a fresh-context review based on direct inspection of the worktree files and source hashes. It did not rely on an author's summary or explanation, and no other session was contacted. The malformed pin triggered the requested stop condition; this report does not provide a substantive approval of Draft 3 or Draft 5.

This is a read-only planning review, not Task Approval or launch authorization. No tests, validators, typecheck, lint, build, backend/runtime, database/migration, Docker, network/provider/Modal, install, staging, commit, or push command was run. No M2 command ceiling was used.
