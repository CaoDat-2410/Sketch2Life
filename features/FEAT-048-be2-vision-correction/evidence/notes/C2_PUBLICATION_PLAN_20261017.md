# BE2-02 C2 publication plan — 2026-10-17 (PROPOSED, for Codex review)

## Final Codex re-review —2026-10-17 (current)

Disposition: PUBLICATION_PLAN_REVIEW_PASS / PENDING_OWNER_EXECUTION_AUTHORIZATION.
The two earlier publication findings are resolved. Root independently checked37/37 exact
paths, groups6/17/11/3, zero gaps/duplicates/ignored/staged paths, all37 filtered/unfiltered
Git blob identities, and the three normalization negative controls. The original three CRLF
metrics and cross-referenced implementation receipt hash are preserved. All16 reviewed source/
test hashes, five authorization/approved-plan anchors, owner acceptance and seven image_only
golden blobs still match. Current handoff/index routing now reflects C2 offline acceptance.
The selected four-commit grouping remains appropriate; no new product code review is required
for these attribute/document-only fixes. Intermediate cumulative simulation/test counts below
are executor evidence; root did not repeat unchanged product tests.

Read-only verification receipt: evidence/local/codex-c2-review-20261017/publication_plan_rereview.json.
Earlier NEEDS_DOCUMENT_REVISION entry below is historical and superseded by this conclusion.
This review grants no stage/commit/push permission. One later explicit user instruction may
authorize staging and all four local commits together; separate confirmation for each commit
is not inherently required. Security must run before EACH commit; push remains separate.

## Latest Codex publication review —2026-10-17

Disposition: NEEDS_DOCUMENT_REVISION before execution. The four-commit grouping is coherent;
coverage is independently36/36 with no missing/extra/duplicate paths, staged0, reviewed16 source/
test hashes and seven C1 golden blobs unchanged. Product code review remains PASS_WITH_NOTES.
No source/config/index/HEAD change was made by this publication review.

Two publication issues remain; the original inventory/check claims below are the executor's
earlier report and must be corrected after these issues are resolved:

1. Encoding: C2_PLANNING_CHECKS_20261017.json, C2_IMPLEMENTATION_CHECKS_20261017.json and
   C2_CODEX_REVIEW_20261017.json in evidence/metrics/ actually contain CRLF (77/169/224 lines),
   without BOM. The repository's `* text=auto eol=lf` will normalize them. Review metrics line35
   pins the implementation receipt's ORIGINAL SHA25668aa985f…; normalization changes those bytes
   and breaks that cross-reference. Preserve the reviewed originals; preferred fix is three
   exact-path `-text whitespace=cr-at-eol` rules in .gitattributes, following the repository's
   existing hash-preservation convention. Include .gitattributes in commit1, giving6/17/11/3
   files,37 unique total; recheck hashes, Git filters and coverage before approval. Do not rewrite
   historical evidence merely to hide normalization.
2. Current state: H_AI_REVIEW_HANDOFF still says C2 not reviewed/accepted; evidence/README labels
   the current C2 owner acceptance pending; STATUS has an older implementation heading marked
   current. Add/update current acceptance routing and mark earlier checkpoints historical while
   preserving their dated evidence and the review/approved-plan bytes.

Root confirmed different filtered/unfiltered implementation blob hashes using read-only
`git hash-object`, and actual security/diff checks pass. Default validators do not detect this
cross-document SHA256 problem. Ignored inventory/hash receipt:
evidence/local/codex-c2-review-20261017/publication_plan_review.json. Cumulative scratch snapshot
simulation remains the executor's report; Codex did not repeat it because product hashes are
unchanged. No staging/commit/push is authorized by this review.

## Review resolution —2026-10-17 (Claude, latest; for Codex re-review)

User directly asked to fix the two publication issues above. Both are addressed; the review text
above is kept as written.

1. Encoding: CRLF confirmed byte-level in exactly the three metrics. Added three exact-path
   `-text whitespace=cr-at-eol` rules to `.gitattributes` (now in commit 1, which first adds a
   CRLF metric). `git check-attr` reports `text: unset` for each; filtered = unfiltered blob for
   all 37 files; under a `text=auto` path the three would normalize (negative control);
   `implementation_receipt_sha256` 68aa985f… still equals the receipt bytes. No metric, source,
   test, golden, approval or approved plan byte changed.
2. Current state: `H_AI_REVIEW_HANDOFF.md` C2 section and the `evidence/README.md` head now route
   to the Codex review and the 11:59 +07:00 owner acceptance; the STATUS/CONTEXT implementation
   (and CONTEXT review) headings are relabelled historical. Dated entries keep their text.
3. Plan: four commits, 6/17/11/3 = 37 files; §1 encoding claim corrected; §4 split wording
   qualified as the chosen whole-file importable boundary. Results in §5; ignored receipt
   `evidence/local/c2-publication-fix-20261017/`.

Status: **plan only**. Nothing staged, committed, pushed or merged. Owner acceptance of
C2_TYPED_CONTEXT_OFFLINE (component scope) is recorded in `approvals/C2_COMPONENT_ACCEPTANCE.md`;
it does not authorize publication. Branch `feature/be2-02-vision-correction`, HEAD `98876fe…`
(= origin after the C1 push), 0 staged paths. BE2-02 IN_PROGRESS/NOT_DONE; BE2-01 WAITING_STUDIO.

## 1. Inventory of uncommitted changes

**17 tracked files modified (including `.gitattributes`) + 20 untracked, not ignored = 37 files**,
all proposed for GitHub. Sources: C2 planning (Codex), C2 approval/implementation (Claude), C2
Codex review, C2 acceptance, this plan and the publication-review fix. Exact lists are in §4; together they equal
`git diff --name-only` ∪ `git ls-files --others --exclude-standard` (checked, §5).

- Backend: 6 existing source files and 2 existing C1 test files modified (C2 seam changes explained
  in `C2_IMPLEMENTATION_EVIDENCE_20261017.md`); 4 new source and 4 new test modules. No dependency
  declaration, production app/router, BE2-01/BE1/FEAT-018 code, Lightning server/prompt or SQL changed.
- Fixture: 1 new typed golden example. The 7 image_only C1 goldens are byte-identical to HEAD.
- Feature records: 2 C2 plan files, 2 approvals (C2 task approval, C2 acceptance), 4 notes and
  3 metrics, plus 5 modified FEAT-048 ledgers/handoff; 3 shared ledgers (project context, source
  register, BE2 tracker); `.gitattributes` (three exact-path rules, see below).
- Encoding (corrected): all files are UTF-8 without BOM. 34 are LF. Three metrics are CRLF in
  every line: `C2_PLANNING_CHECKS_20261017.json` (77), `C2_IMPLEMENTATION_CHECKS_20261017.json`
  (169), `C2_CODEX_REVIEW_20261017.json` (224). The first version of this plan wrongly reported
  all-LF (its shell `grep $'
'` loop did not detect CR). The review metrics pin the original
  implementation receipt bytes (`implementation_receipt_sha256` 68aa985f…), so `text=auto
  eol=lf` normalisation would break that cross-reference. The reviewed bytes are kept: three
  exact-path `-text whitespace=cr-at-eol` rules in `.gitattributes` (existing convention for
  byte-hashed artifacts; no broad JSON/global rule). No metric was regenerated or rewritten.
- The C1 approval, C1 approved plan, C1 acceptance and C2 approved plan bytes are unchanged
  (hashes in §5); historical C1 notes/metrics are not modified.

## 2. Local only (Git-ignored, never staged)

| Location | Content |
|---|---|
| `features/FEAT-048-be2-vision-correction/evidence/local/claude/prompts/CLAUDE_C2_IMPLEMENTATION_PROMPT_20261017.md` | Codex-prepared operator procedure (not an approval) |
| `…/evidence/local/c2-preparation-20261017/` | Codex planning receipts and the raw rev1 draft |
| `…/evidence/local/c2-typed-context-20261017/` | Claude C2 wrapper/metrics scripts, raw logs, JUnit, pytest temp, BE2-01 attempt-1 receipts |
| `…/evidence/local/codex-c2-review-20261017/` | Codex review runners, root/delegated receipts, probes, mypy cache |
| `…/evidence/local/c1-complete-checks-20261016/deps/` | pre-existing ignored python-multipart used process-locally (not reinstalled) |
| `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`, `backend/.mypy_cache/`, `backend/.ruff_cache/`, `__pycache__/` | tool caches |

All are covered by `/features/FEAT-048-be2-vision-correction/evidence/local/` or existing cache
rules (`git status --ignored`). Published notes/metrics keep only hashes and names of these
receipts. Pillow was loaded from the base interpreter in-process and is not a repository file.

## 3. Link check

The 18 publishable C2 documents (fixtures excluded) were scanned for `.md`/`.json`/`.py` path
tokens, resolved against the document folder, the feature, the repo, `backend/src/sketch2life`
and `backend/tests`, and checked for tracked-or-planned status:

- Every path added by this change resolves to a tracked file or a file in §4, except this plan
  itself before it was written.
- Intentional ignored-local mentions: `CONTEXT.md` names the BE2-01 worktree's ignored
  `handover/BE2_RESUME_ORDER_20261017.md` (stated as local), `evidence/README.md` names ignored C1
  prompts (pre-existing), `metrics/C2_CODEX_REVIEW_20261017.json` names its ignored root receipt.
- Other unresolved tokens are pre-existing text outside this change (external URLs and FEAT-042/
  FEAT-044-relative names in `SOURCE_REGISTER.md`, `PROJECT_CONTEXT.md`, `BE2_EXECUTION_TRACKER.md`).

## 4. Proposed commits (by content)

Four commits. Plan/approval precede code; `.gitattributes` is in commit 1 because the first
CRLF metric (`C2_PLANNING_CHECKS_20261017.json`) is added there and the rule must exist no later
than the file. Code, its tests, changed C1 seam tests and the typed golden stay together: with
the files as they are (whole-file commits, no source refactor), the new tests import the harness,
which imports the adapter, which needs the whole domain/contract/service change, so this is the
chosen importable boundary; it is not a claim that no alternative refactor could split it. Feature
ledgers follow the code so their acceptance text never precedes the code it describes; the shared
ledgers come last, as for C1. Each message ends with the session's `Co-Authored-By` trailer.

### Commit 1 — `docs(be2-02): approve C2 typed-context plan revision 2` (6)

```text
.gitattributes
features/FEAT-048-be2-vision-correction/approvals/C2_TASK_APPROVAL.md
features/FEAT-048-be2-vision-correction/evidence/metrics/C2_PLANNING_CHECKS_20261017.json
features/FEAT-048-be2-vision-correction/evidence/notes/C2_PLAN_REVIEW_20261017.md
features/FEAT-048-be2-vision-correction/plan/C2_TYPED_CONTEXT_PLAN.md
features/FEAT-048-be2-vision-correction/plan/C2_TYPED_CONTEXT_PLAN_REV2_APPROVED.md
```

### Commit 2 — `feat(be2-02): add offline typed Vision context, pinned digests and context adapter` (17)

```text
backend/src/sketch2life/application/ports/vision_analysis.py
backend/src/sketch2life/application/services/vision_analysis.py
backend/src/sketch2life/contracts/schemas/analysis_context_results.py
backend/src/sketch2life/contracts/schemas/vision_context.py
backend/src/sketch2life/domain/vision_analysis.py
backend/src/sketch2life/domain/vision_context.py
backend/src/sketch2life/infrastructure/vision_analysis/context_adapter.py
backend/src/sketch2life/infrastructure/vision_analysis/fakes.py
backend/src/sketch2life/infrastructure/vision_analysis/harness.py
backend/src/sketch2life/infrastructure/vision_analysis/legacy_v2.py
backend/tests/contract/test_vision_context_contracts.py
backend/tests/unit/test_vision_analysis_legacy_bridge.py
backend/tests/unit/test_vision_analysis_service.py
backend/tests/unit/test_vision_context_adapter.py
backend/tests/unit/test_vision_context_domain.py
backend/tests/unit/test_vision_context_service.py
features/FEAT-048-be2-vision-correction/fixtures/h_ai_review/typed_context_example.json
```

### Commit 3 — `docs(be2-02): record C2 evidence, Codex review, owner acceptance and handoff` (11)

```text
features/FEAT-048-be2-vision-correction/CONTEXT.md
features/FEAT-048-be2-vision-correction/DECISIONS.md
features/FEAT-048-be2-vision-correction/approvals/C2_COMPONENT_ACCEPTANCE.md
features/FEAT-048-be2-vision-correction/evidence/README.md
features/FEAT-048-be2-vision-correction/evidence/metrics/C2_CODEX_REVIEW_20261017.json
features/FEAT-048-be2-vision-correction/evidence/metrics/C2_IMPLEMENTATION_CHECKS_20261017.json
features/FEAT-048-be2-vision-correction/evidence/notes/C2_CODEX_REVIEW_20261017.md
features/FEAT-048-be2-vision-correction/evidence/notes/C2_IMPLEMENTATION_EVIDENCE_20261017.md
features/FEAT-048-be2-vision-correction/evidence/notes/C2_PUBLICATION_PLAN_20261017.md
features/FEAT-048-be2-vision-correction/evidence/notes/H_AI_REVIEW_HANDOFF.md
features/FEAT-048-be2-vision-correction/status/STATUS.md
```

### Commit 4 — `docs(be2): route BE2-02 C2 acceptance in project context and BE2 tracker` (3)

```text
docs/context/PROJECT_CONTEXT.md
docs/context/SOURCE_REGISTER.md
features/FEAT-044-be2-ai-job-foundation/plan/BE2_EXECUTION_TRACKER.md
```

Total: 6 + 17 + 11 + 3 = **37** unique files.

Known intermediate states: after commit 1 the C2 plan/approval exist while CONTEXT/STATUS still
show C1 only (as at HEAD); commit 3 brings them current. In state 1 the plan names the four new
modules it proposes (they arrive in commit 2) and the approval's verbatim text names the ignored
operator prompt. From state 2 on, every C2 path resolves; in state 3 the only unresolved names are
ignored local prompts (two pre-existing C1 ones in the evidence index, the C2 one in §2 here).

## 5. Coverage and checks for this plan

Current results (after the review fix, 2026-10-17 ~05:30Z) from a scratch verifier that parses §4
itself; the earlier 36-file run is superseded:

| Check | Result |
|---|---|
| §4 vs `git diff --name-only` ∪ untracked-not-ignored | 37 = 37; missing 0, extra 0, duplicates 0 |
| Listed paths existing / ignored / staged | 37 exist; 0 ignored; 0 staged |
| Git filters (real repo, read-only `git hash-object --path` vs `--no-filters`) | equal for all 37 files |
| CRLF files / `text` attribute | exactly the 3 metrics; `text: unset` for each |
| `implementation_receipt_sha256` in the review metrics vs receipt bytes | equal (68aa985f…) |
| Commit-2 code vs hashes in `metrics/C2_CODEX_REVIEW_20261017.json` | 16/16 equal (the typed golden is pinned by its test and the implementation metrics) |
| Image_only C1 goldens vs HEAD blobs | equal |
| Cumulative states 1–4 (HEAD export + commits 1..k, scratch git repo, `core.autocrlf=true` as in this worktree): `git add -A` there, staged blob bytes vs working bytes | equal for every listed file in every state |
| Same states: harness, security, architecture, skeleton validators | exit 0 in every state |
| States 2–4: C2 4 files + C1 8 files, import root asserted inside the export | 412 collected, 0 failed, 0 errors, 1 skipped each (`test_v12_production_app_routes_do_not_mount_cmd34`: python-multipart is not on the plain venv path; it passed 240/240 with the process-local dependency in the C2 run) |
| Final working tree: four validators and `git diff --check` | exit 0 each (session report) |

The simulation wrote only to scratch directories; the repository index, HEAD, config and working
tree were not modified by it.

Unchanged-byte anchors: `approvals/TASK_APPROVAL.md` ebe826ce…, `plan/PLAN_REV1_APPROVED.md`
f4733c88…, `approvals/C1_COMPONENT_ACCEPTANCE.md` 2d2e109a…, `approvals/C2_TASK_APPROVAL.md`
16af8a94…, `plan/C2_TYPED_CONTEXT_PLAN_REV2_APPROVED.md` 4b339514…; the 16 source/test files and
the typed golden equal the hashes Codex reviewed in `metrics/C2_CODEX_REVIEW_20261017.json`.

## 6. Execution (only after plan review and an explicit owner instruction)

1. Re-run `tools/validate_repository_security.py` (required before every commit), harness,
   architecture, skeleton and `git diff --check` on the final bytes.
2. Stage each commit by explicit path (`git add -- <paths>`), never `git add -A`; check
   `git diff --cached --name-only` equals the list above before each commit.
3. Push only under a separate explicit instruction; no merge/deploy; no next checkpoint opened.
