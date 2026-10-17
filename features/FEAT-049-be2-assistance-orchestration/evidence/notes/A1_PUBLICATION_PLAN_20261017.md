# BE2-03 A1 publication inventory and commit plan — 2026-10-17

Status: **PLAN_ONLY — awaiting owner review**. Prepared after the owner's A1 component acceptance
(`../../approvals/A1_COMPONENT_ACCEPTANCE.md`). Nothing has been staged, committed, pushed,
merged or deployed. Executing this plan, and any later push, each need an explicit owner
instruction. No new checkpoint is opened. BE2-01 WAITING_STUDIO, BE2-02 PARKED, BE2-03
IN_PROGRESS / NOT_DONE.

Identity: worktree `.worktrees/be2-03-assistance-orchestration`, branch
`feature/be2-03-assistance-orchestration`, HEAD f120c4fce8f7853e5ab5e061eff4bf916d45603c
(= pushed BE2-02 C2 checkpoint, not dev), staged 0. The local branch tracks
`origin/feature/be2-03-assistance-orchestration`; the local remote-tracking ref (last fetch)
is at f120c4f, so the branch is even with it. This is only the locally recorded ref: before any
later push the actual remote tip must be re-checked (`git ls-remote origin
refs/heads/feature/be2-03-assistance-orchestration`) and must still be f120c4f or an
owner-reviewed ancestor of the local head; otherwise stop and report. A future PR to dev must
account for the BE2-01/BE2-02 parent commits (stacked base).

## 1. Inventory of uncommitted changes (64 paths)

| Kind | Count | Paths |
|---|---|---|
| Tracked, modified | 5 | `.gitignore` (FEAT-049 `evidence/local/` ignore rule), `.gitattributes` (`-text` for the 4 CRLF review metrics, §3a), `docs/context/PROJECT_CONTEXT.md`, `docs/context/SOURCE_REGISTER.md`, `features/FEAT-044-be2-ai-job-foundation/plan/BE2_EXECUTION_TRACKER.md` |
| New A1 source | 10 | `backend/src/sketch2life/{domain/assistance.py, contracts/schemas/assistance_requests.py, application/ports/assistance.py, application/services/assistance.py, infrastructure/assistance/{__init__,adapters,fakes,harness}.py, interfaces/http/assistance_requests_fixture_app.py, interfaces/http/routers/assistance_requests.py}` |
| New A1 tests | 8 | `backend/tests/unit/test_assistance_{domain,service,chain,races,review_fixes,cr03_followup}.py`, `backend/tests/contract/test_assistance_{request_contracts,requests_api}.py` |
| New FEAT-049 records | 40 | feature skeleton (`.gitkeep` ×8, `assets/REVIEW.md`), CONTEXT, DECISIONS, STATUS, evidence README, plan PLAN.md + PLAN_REV3_APPROVED.md, approvals ×2, 13 planning/A1 notes, 9 metrics, golden `fixtures/h_ai_review/assistance_handoff_examples.json` |
| This plan note | 1 | `evidence/notes/A1_PUBLICATION_PLAN_20261017.md` |

No existing tracked source or test file is modified; no foundation/Vision source changed.

## 2. Local only (Git-ignored; never staged)

`features/FEAT-049-be2-assistance-orchestration/evidence/local/` (≈32 MB; ignore rule verified
with `git check-ignore`): operator prompts (`claude/`), historical plan drafts (revisions 1–2),
runner scripts, raw logs/JUnit/pytest temp, probe copies and all Codex review receipts
(`codex-*`). Also ignored: `backend/.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`,
`__pycache__/`. Published notes reference these local paths as provenance only.

## 3. Proposed commits (by function; explicit pathspecs, no `git add -A`)

| # | Message | Paths | Content |
|---|---|---|---|
| C1 | `docs(be2-03): add FEAT-049 plan, approval and planning reviews` | 28 | `.gitignore`; `.gitattributes`; feature skeleton (`.gitkeep` ×8, `assets/REVIEW.md`); `CONTEXT.md`, `DECISIONS.md`, `status/STATUS.md`, `evidence/README.md`, `plan/PLAN.md`, `plan/PLAN_REV3_APPROVED.md`, `approvals/TASK_APPROVAL.md`; notes `SOURCE_AUDIT`, `PLANNING_CHECKS`, `PLAN_REV2_CHANGES`, `PLAN_REV3_CHANGES`, `PLAN_CODEX_{REVIEW,REREVIEW,FINAL_REVIEW}`; metrics `PLAN_CODEX_{REVIEW,REREVIEW,FINAL_REVIEW}` |
| C2 | `feat(be2-03): add offline assistance request orchestration component (A1)` | 19 | the 10 source files, 8 test files and the pinned golden `fixtures/h_ai_review/assistance_handoff_examples.json` (read by the contract test) |
| C3 | `docs(be2-03): record A1 evidence, Codex reviews, fixes and owner acceptance` | 14 | `approvals/A1_COMPONENT_ACCEPTANCE.md`; notes `A1_IMPLEMENTATION_EVIDENCE`, `A1_CODEX_REVIEW`, `A1_REVIEW_FIX_EVIDENCE`, `A1_CODEX_REREVIEW`, `A1_CR03_FOLLOWUP_EVIDENCE`, `A1_CODEX_FINAL_REVIEW`, `A1_PUBLICATION_PLAN`; metrics `A1_CHECKS`, `A1_CODEX_REVIEW`, `A1_REVIEW_FIX_CHECKS`, `A1_CODEX_REREVIEW`, `A1_CR03_FOLLOWUP_CHECKS`, `A1_CODEX_FINAL_REVIEW` |
| C4 | `docs(be2): route BE2-03 A1 acceptance in project context, source register and BE2 tracker` | 3 | `docs/context/PROJECT_CONTEXT.md`, `docs/context/SOURCE_REGISTER.md`, `features/FEAT-044-be2-ai-job-foundation/plan/BE2_EXECUTION_TRACKER.md` |

Coverage: 28 + 19 + 14 + 3 = 64; every path exactly once. Each commit message ends with the
project's Claude co-author line.

Ordering notes:

- C1 must precede C2: `tools/validate_harness.py` requires each `features/FEAT-*` folder to have
  CONTEXT, DECISIONS, plan, approval and evidence index, and C2 adds the golden fixture inside
  FEAT-049.
- CONTEXT, DECISIONS, STATUS, evidence README and the working `plan/PLAN.md` are single files
  carrying the whole dated history up to the acceptance, so in C1 they point forward to notes
  and the acceptance that arrive in C3 (no partial-file staging). The final tree after C4 has
  no dangling reference. `PLAN_REV3_APPROVED.md` stays byte-identical
  (e1fce645…; `.gitattributes` `eol=lf`, file already LF).
- C2 at C1+C2 state is self-contained for tests (A1 tests import only C2 code, the f120c4f
  foundation/Vision code and the golden fixture).

## 3a. CRLF review metrics (amendment, owner instruction 2026-10-17)

When C1 was first staged under the approved plan, Git reported that four Codex-written metrics
files are CRLF and would be normalized to LF (`* text=auto eol=lf`):
`PLAN_CODEX_REVIEW_20261017.json` (918a7b5e…), `PLAN_CODEX_REREVIEW_20261017.json` (c94af697…),
`PLAN_CODEX_FINAL_REVIEW_20261017.json` (9fa86b29…) and `A1_CODEX_REVIEW_20261017.json`
(c6722e6f…). Their CRLF SHA256 values are recorded in other review metrics, so normalization
would have made those recorded hashes disagree with the committed blobs. C1 was unstaged
(nothing committed) and the owner chose to preserve the reviewed bytes: `.gitattributes` gains
`-text whitespace=cr-at-eol` for exactly these four paths (same pattern as the BE2-02 C2
metrics) and joins C1 as path 64. The earlier statements that the new-file CR scan was clean
were wrong: that Git Bash `grep` check did not detect CR; a byte-level Python scan now finds CR
in exactly these four files and nowhere else among the 64 paths.

## 4. Checks to run during execution

Immediately before **each** of C1, C2, C3 and C4 (after staging exactly that group's
pathspecs and checking the staged list, before `git commit`), run
`python tools/validate_repository_security.py` as AGENTS.md requires before every commit; a
non-VALID result stops the sequence with nothing further committed. After each commit: harness
and security validators, `git diff --check`, `git status` (expected remaining paths), staged 0.
After C2: the A1 focused suite (8 files). After C4: full A1 + BE2-01 + BE2-02 runner, ruff and
strict mypy on the 10 A1 source files, all four validators; `git log` shows exactly 4 new
commits on `feature/be2-03-assistance-orchestration`; no ignored path committed; for each of the
four CRLF metrics the committed blob id equals `git hash-object --no-filters` of the reviewed
working bytes. Source hashes
of C2 files are compared with `../metrics/A1_CODEX_FINAL_REVIEW_20261017.json`.

Current results for the plan (2026-10-17, before any commit): harness, security,
architecture and skeleton validators VALID; `git diff --check` clean; byte-level scan: no
trailing whitespace, CR only in the four protected metrics (§3a); all 34 hashes in the final-review metrics match the working files; approval
(f6a266c9…) and approved plan (e1fce645…) unchanged.

## 5. Not part of this plan

Push to `origin/feature/be2-03-assistance-orchestration` (after re-checking its actual remote tip
as above and running the security validator again), PR, merge to dev, deploy, Studio/provider
runs and any next BE2-03 checkpoint each require a separate owner instruction.
