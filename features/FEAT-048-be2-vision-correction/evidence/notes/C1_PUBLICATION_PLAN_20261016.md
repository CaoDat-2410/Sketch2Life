# BE2-02 C1 publication plan — 2026-10-16 (PROPOSED, awaiting review)

Status: **plan only**. Nothing staged, committed, pushed or merged. Owner acceptance of
C1_COMPONENT_OFFLINE is recorded in `approvals/C1_COMPONENT_ACCEPTANCE.md`; it does not authorize
publication. Branch `feature/be2-02-vision-correction`, HEAD = base `6dcc57ee…`, 0 staged paths.

## 1. Inventory

- 4 tracked files modified + 64 untracked, not ignored = **68 files proposed for GitHub**.
- No existing backend file is modified; legacy V2/Qwen adapters, BE2-01 code, production app and
  dependency declarations are unchanged.
- `.gitattributes` is `* text=auto eol=lf`. **Five** metrics files are CRLF in the working tree
  and will be stored as LF: `C1_CODEX_REVIEW_20261016.json`, `C1_CODEX_REREVIEW_20261016.json`,
  `C1_CODEX_R04_CLOSURE_20261016.json`, `C1_REMAINING_CHECKS_20261016.json`,
  `C1_FINAL_VERIFICATION_20261016.json`. Their CRLF and LF SHA256 values were searched in every
  readable file under `features/`, `docs/` and `backend/tests/` (2,439 files, ignored local
  receipts included): no reference found. One ignored directory could not be read (Access
  denied): `features/FEAT-048-be2-vision-correction/evidence/local/codex-rereview-20261016/legacy-temp/`
  (a Codex legacy-test temp directory), so the search is complete only for readable files. None of
  the 68 publishable files records these hashes, so normalisation breaks no published receipt.
  The working-tree bytes are not rewritten by this plan.

## 2. Local only (already Git-ignored, never staged)

| Location | Content | Ignore rule |
|---|---|---|
| `features/FEAT-048-be2-vision-correction/evidence/local/claude/` | operator prompts (implementation, review-fix, R04 follow-up) | `/features/FEAT-048-be2-vision-correction/evidence/local/` (new line in `.gitignore`) |
| `…/evidence/local/c1-complete-checks-20261016/deps/` | locally installed `python-multipart 0.0.32` test target | same |
| `…/evidence/local/{junit,claude-fix-20261016,claude-r04-followup-20261016}/` | Claude JUnit, before/after logs, basetemp, mypy cache, probe reruns | same |
| `…/evidence/local/{codex-review,codex-rereview,codex-r04-final,c1-existing-pillow,c1-complete-checks}-20261016/` | Codex probes/scripts, raw logs/JUnit, runner/package reports, setup-failure logs | same |
| `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`, `backend/.pytest_cache/`, `backend/.ruff_cache/`, `__pycache__/` | tool caches | existing rules |

Published metrics keep only hashes and ignored-path names of those receipts (marked "ignored"),
not the raw content. `git check-ignore` confirms the local root is ignored. The unreadable
`codex-rereview-20261016/legacy-temp/` directory is inside this ignored root and is not staged.

## 3. Link check before classifying

Re-run after the ledger condensation: 33 candidate Markdown/JSON documents (fixtures excluded)
scanned for path tokens and local-path mentions.

- Every referenced publishable `.md`/`.json` document exists.
- Bare file names in prose (e.g. `test_qwen_vision_adapter.py`, `app.py`) resolve under
  `backend/`. Remaining unresolved tokens are not links of this change: the pre-existing
  `FORM_V1_8_ALIGNMENT_20261012.md` row in `SOURCE_REGISTER.md` (outside this change, also quoted
  here) and the prose suffix `_result.json` in the Codex re-review note.
- 22 documents mention ignored local paths, always as local receipts expected to be absent on
  GitHub. In the two ledgers these mentions are only in the unchanged BE2-01 history; the new
  BE2-02 entries link published FEAT-048 files only.
- `notes/C1_REMAINING_CHECKS_20261016.md` (+ metrics) is an intermediate check inventory that
  `C1_FINAL_VERIFICATION` supersedes. After the ledger condensation it is still linked from 4
  feature records (CONTEXT, DECISIONS, STATUS, evidence README). **Recommendation: publish it** as
  a short history item rather than rewrite those links.
- `PROJECT_CONTEXT.md` and `BE2_EXECUTION_TRACKER.md`: the iterative BE2-02 entries (71/70 lines)
  were condensed into one current-state entry each (15/14 lines) linking STATUS, approval,
  acceptance, final verification, R04 closure, handoff and this plan; all linked files exist. The
  text below the BE2-02 entry (BE2-01 and older history) is byte-identical to HEAD.

## 4. Classification

- **Code/contracts (11):** domain, candidate contracts, application port/service,
  `infrastructure/vision_analysis/*` (5), CMD-34 router and fixture app.
- **Tests and consumer fixtures (15):** 8 test modules, 7 golden H-AI-REVIEW examples.
- **Required feature records (42):** plan + approved snapshot, approval and acceptance, CONTEXT/
  DECISIONS/STATUS, evidence index, planning audit/review, implementation evidence, three Codex
  review notes and their metrics, two fix notes and their metrics, final/remaining verification,
  handoff, this plan, harness `.gitkeep`/asset placeholders; plus `.gitignore` and three shared
  context ledgers.

## 5. Proposed commits (functional; each keeps the harness valid and the code importable)

Feature records come first so plan/approval precede code; their forward links to later evidence
resolve by commit 6. Every commit is test-runnable for the files it adds (import graph checked).

### Commit 1 — `docs(be2-02): open FEAT-048 with approved C1 plan and planning audit` (20)

```text
.gitignore
features/FEAT-048-be2-vision-correction/CONTEXT.md
features/FEAT-048-be2-vision-correction/DECISIONS.md
features/FEAT-048-be2-vision-correction/approvals/TASK_APPROVAL.md
features/FEAT-048-be2-vision-correction/plan/PLAN.md
features/FEAT-048-be2-vision-correction/plan/PLAN_REV1_APPROVED.md
features/FEAT-048-be2-vision-correction/status/STATUS.md
features/FEAT-048-be2-vision-correction/assets/REVIEW.md
features/FEAT-048-be2-vision-correction/assets/applied/.gitkeep
features/FEAT-048-be2-vision-correction/assets/approved/.gitkeep
features/FEAT-048-be2-vision-correction/assets/generated/.gitkeep
features/FEAT-048-be2-vision-correction/src/.gitkeep
features/FEAT-048-be2-vision-correction/evidence/README.md
features/FEAT-048-be2-vision-correction/evidence/metrics/.gitkeep
features/FEAT-048-be2-vision-correction/evidence/notes/.gitkeep
features/FEAT-048-be2-vision-correction/evidence/raw/.gitkeep
features/FEAT-048-be2-vision-correction/evidence/screenshots/.gitkeep
features/FEAT-048-be2-vision-correction/evidence/notes/SOURCE_AUDIT.md
features/FEAT-048-be2-vision-correction/evidence/notes/PLAN_REVIEW.md
features/FEAT-048-be2-vision-correction/evidence/metrics/PLANNING_CHECKS.json
```

### Commit 2 — `feat(be2-02): add DATA-22 analysis domain, contracts and application service` (4)

```text
backend/src/sketch2life/domain/vision_analysis.py
backend/src/sketch2life/contracts/schemas/analysis_results.py
backend/src/sketch2life/application/ports/vision_analysis.py
backend/src/sketch2life/application/services/vision_analysis.py
```

### Commit 3 — `feat(be2-02): add offline fakes, BE2-01 lineage adapter and legacy V2 bridge` (10)

```text
backend/src/sketch2life/infrastructure/vision_analysis/__init__.py
backend/src/sketch2life/infrastructure/vision_analysis/fakes.py
backend/src/sketch2life/infrastructure/vision_analysis/harness.py
backend/src/sketch2life/infrastructure/vision_analysis/job_lineage.py
backend/src/sketch2life/infrastructure/vision_analysis/legacy_v2.py
backend/tests/unit/test_vision_analysis_domain.py
backend/tests/unit/test_vision_analysis_service.py
backend/tests/unit/test_vision_analysis_legacy_bridge.py
backend/tests/unit/test_vision_analysis_job_lineage.py
backend/tests/contract/test_analysis_result_contracts.py
```

### Commit 4 — `feat(be2-02): add isolated CMD-34 corrections fixture API` (3)

```text
backend/src/sketch2life/interfaces/http/routers/analysis_corrections.py
backend/src/sketch2life/interfaces/http/analysis_corrections_fixture_app.py
backend/tests/contract/test_analysis_corrections_api.py
```

### Commit 5 — `test(be2-02): pin C1 review regressions and H-AI-REVIEW handoff examples` (9)

```text
backend/tests/unit/test_vision_analysis_review_fixes.py
backend/tests/contract/test_h_ai_review_handoff_examples.py
features/FEAT-048-be2-vision-correction/fixtures/h_ai_review/analysis_record.json
features/FEAT-048-be2-vision-correction/fixtures/h_ai_review/analysis_worker_candidate.json
features/FEAT-048-be2-vision-correction/fixtures/h_ai_review/correction_child_receipt.json
features/FEAT-048-be2-vision-correction/fixtures/h_ai_review/correction_teacher_receipt.json
features/FEAT-048-be2-vision-correction/fixtures/h_ai_review/downstream_meaning.json
features/FEAT-048-be2-vision-correction/fixtures/h_ai_review/invalidation_intents.json
features/FEAT-048-be2-vision-correction/fixtures/h_ai_review/provider_result_record.json
```

### Commit 6 — `docs(be2-02): record C1 evidence, Codex reviews, owner acceptance and handoff` (19)

```text
features/FEAT-048-be2-vision-correction/approvals/C1_COMPONENT_ACCEPTANCE.md
features/FEAT-048-be2-vision-correction/evidence/notes/C1_IMPLEMENTATION_EVIDENCE.md
features/FEAT-048-be2-vision-correction/evidence/notes/C1_CODEX_REVIEW_20261016.md
features/FEAT-048-be2-vision-correction/evidence/notes/C1_REVIEW_FIX_EVIDENCE_20261016.md
features/FEAT-048-be2-vision-correction/evidence/notes/C1_CODEX_REREVIEW_20261016.md
features/FEAT-048-be2-vision-correction/evidence/notes/C1_R04_FOLLOWUP_EVIDENCE_20261016.md
features/FEAT-048-be2-vision-correction/evidence/notes/C1_CODEX_R04_CLOSURE_20261016.md
features/FEAT-048-be2-vision-correction/evidence/notes/C1_REMAINING_CHECKS_20261016.md
features/FEAT-048-be2-vision-correction/evidence/notes/C1_FINAL_VERIFICATION_20261016.md
features/FEAT-048-be2-vision-correction/evidence/notes/H_AI_REVIEW_HANDOFF.md
features/FEAT-048-be2-vision-correction/evidence/notes/C1_PUBLICATION_PLAN_20261016.md
features/FEAT-048-be2-vision-correction/evidence/metrics/C1_COMPONENT_CHECKS_20261016.json
features/FEAT-048-be2-vision-correction/evidence/metrics/C1_CODEX_REVIEW_20261016.json
features/FEAT-048-be2-vision-correction/evidence/metrics/C1_REVIEW_FIX_CHECKS_20261016.json
features/FEAT-048-be2-vision-correction/evidence/metrics/C1_CODEX_REREVIEW_20261016.json
features/FEAT-048-be2-vision-correction/evidence/metrics/C1_R04_FOLLOWUP_CHECKS_20261016.json
features/FEAT-048-be2-vision-correction/evidence/metrics/C1_CODEX_R04_CLOSURE_20261016.json
features/FEAT-048-be2-vision-correction/evidence/metrics/C1_REMAINING_CHECKS_20261016.json
features/FEAT-048-be2-vision-correction/evidence/metrics/C1_FINAL_VERIFICATION_20261016.json
```

### Commit 7 — `docs(be2): route BE2-02 C1 acceptance in project context and BE2 tracker` (3)

```text
docs/context/PROJECT_CONTEXT.md
docs/context/SOURCE_REGISTER.md
features/FEAT-044-be2-ai-job-foundation/plan/BE2_EXECUTION_TRACKER.md
```

Total: 20 + 4 + 10 + 3 + 9 + 19 + 3 = **68**.

## 6. Before executing (after plan approval)

1. Ledger condensation: done (see §3).
2. Run once more: `validate_repository_security.py` (required before commit), harness,
   architecture, skeleton, `git diff --check`, and the eight-file focused suite on the final bytes.
3. Stage each commit by explicit path (`git add -- <paths>`), never `git add -A`; verify
   `git diff --cached --name-only` equals the list above before each commit; attribution trailer.
4. Push only with a separate explicit instruction; no merge/deploy; C2 not started.
