# BE2-04 SK1 publication inventory and commit plan — 2026-10-18

Status: **PLAN_ONLY — awaiting owner review**. Prepared after the owner's SK1 component acceptance
(`../../approvals/SK1_COMPONENT_ACCEPTANCE.md`). Nothing has been staged, committed, pushed,
merged or deployed, and no branch has been created. Executing this plan, the later push, and
creating the shared branch each need a separate explicit owner instruction. No new checkpoint is
opened. BE2-01 WAITING_STUDIO, BE2-02 PARKED, BE2-03 A1 accepted offline / card IN_PROGRESS, BE2-04
IN_PROGRESS / NOT_DONE.

Identity: worktree `.worktrees/be2-04-sketch-generation`, branch
`feature/be2-04-sketch-generation`, HEAD `113cdf956a09336a0abf5561bd939f5e13b31ea0` (= pushed BE2-03
A1 tip; not dev), staged 0. The local remote-tracking ref `origin/feature/be2-04-sketch-generation`
(last fetch) is also `113cdf9`. This is only the locally recorded ref; before any push the actual
remote tip must be re-checked (§6). Revised 2026-10-18 at the owner's request from a 4-commit
to a 7-commit split; the inventory is unchanged.

## 1. Inventory of uncommitted changes (49 paths)

Measured with `git diff --name-only` and `git ls-files --others --exclude-standard` (43 untracked),
plus this plan note and the `.gitattributes` exception (§3b).

| Kind | Count | Paths |
|---|---|---|
| Tracked, modified | 5 | `.gitignore` (FEAT-050 `evidence/local/` rule), `.gitattributes` (one exact-path CRLF exception, §3b), `docs/context/PROJECT_CONTEXT.md`, `docs/context/SOURCE_REGISTER.md`, `features/FEAT-044-be2-ai-job-foundation/plan/BE2_EXECUTION_TRACKER.md` |
| New SK1 source | 8 | `backend/src/sketch2life/domain/sketch_proposal.py`, `backend/src/sketch2life/contracts/schemas/sketch_proposals.py`, `backend/src/sketch2life/application/ports/sketch_generation.py`, `backend/src/sketch2life/application/services/sketch_generation.py`, `backend/src/sketch2life/infrastructure/sketch_generation/{__init__,adapters,fakes,harness}.py` |
| New SK1 tests | 6 | `backend/tests/unit/test_sketch_proposal_domain.py`, `backend/tests/unit/test_sketch_generation_{service,adapters,chain,races}.py`, `backend/tests/contract/test_sketch_proposal_contracts.py` |
| New FEAT-050 records | 29 | skeleton (`.gitkeep` ×8, `assets/REVIEW.md`), `CONTEXT.md`, `DECISIONS.md`, `status/STATUS.md`, `evidence/README.md`, `plan/PLAN.md`, `plan/PLAN_REV5_APPROVED.md`, `approvals/TASK_APPROVAL.md`, `approvals/SK1_COMPONENT_ACCEPTANCE.md`, 6 evidence notes, 5 metrics, producer-built fixture `fixtures/h_ai_review/sketch_proposal_examples.json` |
| This plan note | 1 | `evidence/notes/SK1_PUBLICATION_PLAN_20261018.md` |

5 + 8 + 6 + 29 + 1 = 49 (44 new files: 14 source/test + 29 FEAT-050 records + this note; 5
modified tracked files). No existing tracked source or test is modified; no foundation, Vision or
A1 source changed. Group coverage was checked by script against the live inventory (49 paths, 0
missing, 0 extra, 0 duplicates, 0 ignored).

## 2. Local only (Git-ignored; never staged)

`features/FEAT-050-be2-sketch-generation/evidence/local/` (rule `.gitignore:136`, verified with
`git check-ignore`): approval receipt copies, Claude/Codex handoff prompts, raw JUnit/logs/pytest
temp dirs, mypy caches, baseline hash lists, review probes (`r31_mutation_probe.py`,
`r31_boundary_probe.py`) and all review receipts. Also ignored: `__pycache__/`, `.mypy_cache/`,
`.ruff_cache/`, `.pytest_cache/`. No virtualenv exists in this worktree (`backend/.venv` absent;
the shared venv lives outside it). Nothing under `evidence/local/` is listed in §3.

Published records reference local paths only as provenance. Everything a clone needs to check
the checkpoint is published: approved plan bytes, approval, acceptance with all 15 snapshot hashes,
every review note and its metrics (commands, interpreter, exit codes, JUnit hashes), and the
follow-up notes that summarise each probe result. Local-only references, by category:

| Category | Where cited | Why acceptable |
|---|---|---|
| Planning drafts/reviews rev1–rev5 in FEAT-049 `evidence/local/be204-preparation/` (incl. `BE204_PLAN_CODEX_REREVIEW_REV5_20261018.md`, `codex-rev4-probes/`) | `PLAN.md`, `PLAN_REV5_APPROVED.md`, `TASK_APPROVAL.md` | Historical inputs; the approved bytes and verbatim approval are published |
| Consolidation proposal Rev3 (FEAT-049 local) | `SK1_CLAUDE_FOLLOWUP3_20261018.md` | The residual table used is reproduced in that note |
| Raw receipts/probes (`baseline-hashes.txt`, `r31_*`, `codex_r31_probe_rerun.log`, JUnit/logs) | follow-up and review notes/metrics | Results, exits and JUnit hashes are recorded in published notes/metrics |
| `tests/contract/test_sketch_proposal_examples.py` (plan §9 test file name) | `PLAN.md`, `PLAN_REV5_APPROVED.md` | Not created: SK-C06 examples are tested in `test_sketch_proposal_contracts.py` (recorded in the review chain) |

## 3. Proposed commits (7; by layer; explicit pathspecs, never `git add -A`)

Paths without a prefix in C1 and C6 are under `features/FEAT-050-be2-sketch-generation/`.

| # | Message | Paths | Exact paths |
|---|---|---|---|
| C1 | `docs(be2-04): add FEAT-050 feature records, approved plan and task approval` | 17 | `.gitignore`; `{assets/applied,assets/approved,assets/generated,evidence/metrics,evidence/notes,evidence/raw,evidence/screenshots,src}/.gitkeep` (8); `assets/REVIEW.md`; `CONTEXT.md`; `DECISIONS.md`; `status/STATUS.md`; `evidence/README.md`; `plan/PLAN.md`; `plan/PLAN_REV5_APPROVED.md`; `approvals/TASK_APPROVAL.md` |
| C2 | `feat(be2-04): add sketch proposal domain, DATA-23 contracts and ports` | 3 | `backend/src/sketch2life/domain/sketch_proposal.py`; `backend/src/sketch2life/contracts/schemas/sketch_proposals.py`; `backend/src/sketch2life/application/ports/sketch_generation.py` |
| C3 | `feat(be2-04): add sketch generation service and in-memory fakes` | 3 | `backend/src/sketch2life/application/services/sketch_generation.py`; `backend/src/sketch2life/infrastructure/sketch_generation/fakes.py`; `backend/src/sketch2life/infrastructure/sketch_generation/__init__.py` |
| C4 | `feat(be2-04): add sketch adapters, chain harness and unit tests` | 5 | `backend/src/sketch2life/infrastructure/sketch_generation/adapters.py`; `backend/src/sketch2life/infrastructure/sketch_generation/harness.py`; `backend/tests/unit/test_sketch_proposal_domain.py`; `backend/tests/unit/test_sketch_generation_service.py`; `backend/tests/unit/test_sketch_generation_adapters.py` |
| C5 | `test(be2-04): add sketch chain, race and contract tests with H-AI-REVIEW examples` | 4 | `backend/tests/unit/test_sketch_generation_chain.py`; `backend/tests/unit/test_sketch_generation_races.py`; `backend/tests/contract/test_sketch_proposal_contracts.py`; `features/FEAT-050-be2-sketch-generation/fixtures/h_ai_review/sketch_proposal_examples.json` |
| C6 | `docs(be2-04): record SK1 evidence, reviews, follow-ups and owner acceptance` | 14 | `.gitattributes`; `approvals/SK1_COMPONENT_ACCEPTANCE.md`; notes `evidence/notes/{SK1_IMPLEMENTATION_EVIDENCE_20261018,SK1_CODEX_FOLLOWUP_20261018,SK1_CLAUDE_FOLLOWUP3_20261018,SK1_CODEX_FOLLOWUP3_REVIEW_20261018,SK1_CLAUDE_FOLLOWUP3A_20261018,SK1_CODEX_FOLLOWUP3A_REVIEW_20261018,SK1_PUBLICATION_PLAN_20261018}.md` (7); metrics `evidence/metrics/{SK1_CHECKS_20261018,SK1_CHECKS_FOLLOWUP3_20261018,SK1_CODEX_FOLLOWUP3_REVIEW_20261018,SK1_CHECKS_FOLLOWUP3A_20261018,SK1_CODEX_FOLLOWUP3A_REVIEW_20261018}.json` (5) |
| C7 | `docs(be2): route BE2-04 SK1 acceptance in project context, source register and BE2 tracker` | 3 | `docs/context/PROJECT_CONTEXT.md`; `docs/context/SOURCE_REGISTER.md`; `features/FEAT-044-be2-ai-job-foundation/plan/BE2_EXECUTION_TRACKER.md` |

Coverage: 17 + 3 + 3 + 5 + 4 + 14 + 3 = **49**. Checked by script against the live inventory
(`git diff --name-only` ∪ `git ls-files --others --exclude-standard`): 0 missing, 0 extra,
0 duplicates, 0 ignored. Each commit message ends with the project's Claude co-author line.

### 3a. Dependency order (checked)

| After | New importable/testable unit | Depends on | Check |
|---|---|---|---|
| C1 | FEAT-050 folder satisfies `tools/validate_harness.py` (CONTEXT, DECISIONS, plan, approval, evidence index) | — | validators |
| C2 | `domain.sketch_proposal`, `contracts.schemas.sketch_proposals`, `application.ports.sketch_generation` | existing `domain.ai_jobs`, `domain.vision_context`, `application.ports.ai_jobs` (at 113cdf9) | import smoke |
| C3 | `application.services.sketch_generation`, `infrastructure.sketch_generation`, `…fakes` | C2 + existing ai_jobs ports/fakes | import smoke |
| C4 | `…adapters`, `…harness` (A1/Vision/foundation public parts at 113cdf9); unit tests domain/service/adapters | C2–C3; the domain test needs `harness.make_binding`, so it cannot go in C2 | 3 unit test files |
| C5 | chain, race and contract tests; the H-AI-REVIEW fixture lands with the contract test that compares it | C2–C4 | **full focused suite (6 files)** |
| C6 | evidence/acceptance/plan + `.gitattributes` exception with the CRLF metrics it protects | — | blob hashes, validators |
| C7 | shared ledgers | C6 records they cite | validators |

Static check: AST scan of all `sketch2life.*` imports in the 14 Python files — no file imports a
module introduced in a later commit (0 violations); only `test_sketch_proposal_contracts.py` (C5)
reads the fixture. Dry run (read-only, outside the repository: `git archive HEAD backend` plus the
cumulative group files, interpreter as §4): C2 and C3 import smoke OK; the C4 state runs the three
unit test files **79 passed, 0 skipped**; the C5 state runs the six focused files **175 passed,
0 skipped**. CONTEXT, DECISIONS, STATUS, evidence README and `plan/PLAN.md` (C1) point forward to
records that arrive in C6 (same as the A1 precedent; no partial-file staging); after C7 nothing
dangles.

### 3b. CRLF review metrics (exact-path exception, in C6)

Byte-level scan of all 49 paths (Python, not `grep`): CR occurs only in
`evidence/metrics/SK1_CODEX_FOLLOWUP3_REVIEW_20261018.json` (349 CRLF; SHA256
`4fd43990328da8249535c377b439aca29060d625dc659e48f677025b57c88ed5`, pinned by
`SK1_CHECKS_FOLLOWUP3A_20261018.json` and `SK1_CODEX_FOLLOWUP3A_REVIEW_20261018.json`). With
`* text=auto eol=lf` alone, staging would normalize it (filtered blob `e6b53de6…`, raw bytes
`4cd29a1b…`) and break those references. The working tree carries one exact-path exception,
following the FEAT-048/049 precedent, with no directory-wide rule:

```text
# Preserve byte-level hash of the BE2-04 SK1 Codex review metrics cross-referenced by SHA256 (reviewed CRLF bytes).
features/FEAT-050-be2-sketch-generation/evidence/metrics/SK1_CODEX_FOLLOWUP3_REVIEW_20261018.json -text whitespace=cr-at-eol
```

Verified: `git check-attr` reports `text: unset`, `whitespace: cr-at-eol`; `git hash-object
--path=<file>` equals `git hash-object --no-filters` (`4cd29a1b153c08d6e4a3ced76181f07a2bd56d88`).
The bytes were not normalized. `.gitattributes` and this file are both in C6. All other 48 paths
are LF, so LF normalization leaves their pinned hashes unchanged.

## 4. Execution procedure (for each of C1–C7, in order)

Interpreter: existing repository venv (`<repo-root>/backend/.venv`, CPython 3.12.10) with
`PYTHONPATH`/`MYPYPATH` pinned to this worktree's `backend/src`; no installation.

1. `git status --short`; `git diff --cached --name-only` must be empty.
2. `git add -- <the group's paths>`.
3. Compare the sorted staged list with the group list; any difference → `git restore --staged --
   <paths>` and stop.
4. `git diff --cached --check` (C6: the CRLF file is exempted by `whitespace=cr-at-eol`).
5. Pinned-blob check on the **staged bytes**, read without any text pipeline (no PowerShell or
   shell text pipes for hashed data):

   ```python
   import hashlib, subprocess
   def staged_sha256(path):
       data = subprocess.check_output(["git", "cat-file", "blob", f":{path}"])
       return hashlib.sha256(data).hexdigest()
   ```

   - C1: `plan/PLAN_REV5_APPROVED.md` →
     `461d06849899ea41f2c93432ed8b88c5a64428cf17bce5d2959a6d26ef4fa819`;
     `approvals/TASK_APPROVAL.md` → `0f356d32b7cab883be6b3079400ada26495555cef160a6fb6a2a3b742a607d25`.
   - C2–C5: each staged source/test/fixture equals its SHA256 in
     `approvals/SK1_COMPONENT_ACCEPTANCE.md` (= `verified_file_references` of the final review
     metrics); together C2–C5 cover all 15 snapshot files exactly once (3 + 3 + 5 + 4).
   - C6: `SK1_CODEX_FOLLOWUP3_REVIEW_20261018.json` → `4fd43990…8ed5` and staged blob id
     (`git ls-files -s`) `4cd29a1b153c08d6e4a3ced76181f07a2bd56d88`; `SK1_CHECKS_20261018.json`
     `8d93f907…`; follow-up 3 note `fb3b2e1f…` and metrics `82136e02…`; Codex follow-up 3 review
     note `9e95f05a…`; follow-up 3A note `2932fc19…` and metrics `eeca663f…`; Codex 3A review note
     `c084884c…` and metrics `10ace5f6…`; `approvals/SK1_COMPONENT_ACCEPTANCE.md` and this plan equal
     their working bytes recorded at the start of execution.
   Any mismatch → unstage and stop.
6. `python tools/validate_repository_security.py` **immediately before each commit**; a non-VALID
   result stops the sequence with nothing further committed.
7. `git commit` with the group's message (HEREDOC, co-author line). Then `git status --short` shows
   exactly the remaining expected paths and staged is 0.

Per-commit tests:

- After C2 and after C3: import smoke of the modules listed in §3a.
- After C4: the three unit test files (domain, service, adapters).
- After C5: the **full focused SK1 suite** (6 files) with JUnit and `--basetemp` under the ignored
  `evidence/local/`; expected 175 passed, 0 skipped.
- After C7 (no further suite rerun when there is no drift): committed blobs of the 15 snapshot
  files (`git cat-file blob HEAD:<path>`, same Python byte hashing) equal the acceptance hashes; the
  C6 pinned evidence blobs equal their hashes; the four validators VALID; `git diff --check` clean;
  `git log --oneline 113cdf9..HEAD` shows exactly **7** new commits; `git ls-files
  features/FEAT-050-be2-sketch-generation/evidence/local` is empty; staged 0. If any snapshot hash drifts, stop, report and rerun the
  affected checks before any further step.

Current results (before any commit, 2026-10-18): harness, security, architecture and skeleton
validators VALID; `git diff --check` clean; byte scan as §3b; all 15 snapshot hashes and the pinned
review references match; approval and approved plan unchanged; dependency scan and dry run as §3a.

## 5. Not part of this plan

PR, merge to dev, deploy, Studio/provider runs and any next BE2-04 checkpoint each require a
separate owner instruction.

## 6. Push (separate step, separate instruction)

Immediately before pushing `feature/be2-04-sketch-generation`:

1. `git ls-remote origin refs/heads/feature/be2-04-sketch-generation` → must equal `113cdf9…` or an
   owner-reviewed ancestor of the local head (`git merge-base --is-ancestor <remote> HEAD`);
   otherwise stop and report.
2. `git log --oneline <remote>..HEAD` lists exactly the 7 reviewed commits C1–C7.
3. `python tools/validate_repository_security.py` → VALID.
4. `git push origin feature/be2-04-sketch-generation` (never `--force`); record the receipt.

## 7. Next step after publication (not executed here)

Per Person 2's chosen direction, the shared working branch `feature/be2-01-07` is created from the
accepted and committed SK1 tip, i.e. the **C7** commit SHA. That tip already contains the
BE2-01–04 history; nothing is merged or cherry-picked again. Creating it (branch + worktree),
recording the workflow decision and choosing the next ACTIVE card are separate, later
owner-authorized steps.
