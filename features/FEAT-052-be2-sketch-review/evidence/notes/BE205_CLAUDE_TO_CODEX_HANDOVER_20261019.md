# BE2-05 — Claude → Codex handover (review-fix round 1)

- Date: 2026-10-19. Author: Claude (last Claude turn for this work). Status:
  **READY_FOR_CODEX_REREVIEW**. Component NOT_ACCEPTED; card BE2-05 IN_PROGRESS / NOT_DONE.
- No background process or unfinished check is running. Nothing staged, committed, pushed or
  merged. No message was sent to any teammate. Task 06/07 not opened (07 PARKED, WIP1).

## 1. Identity and changes

- Worktree `.worktrees/be2-05-sketch-review` (under the repository root), branch
  `feature/be2-05-sketch-review`, HEAD `58293f1a29ec630e2603c2860b6a2337fadfa713` (no upstream),
  staged 0. All BE2-05 work is uncommitted.
- Tracked files modified: `.gitignore` (FEAT-052 `evidence/local/` rule),
  `docs/context/PROJECT_CONTEXT.md`, `docs/context/SOURCE_REGISTER.md`,
  `features/FEAT-044-be2-ai-job-foundation/plan/BE2_EXECUTION_TRACKER.md`.
- New (untracked): `backend/src/sketch2life/{domain/sketch_review.py,
  contracts/schemas/sketch_reviews.py, application/ports/sketch_review.py,
  application/services/sketch_review.py, infrastructure/sketch_review/*}`, 7 test files
  `backend/tests/unit/test_sketch_review_*.py` + `backend/tests/contract/test_sketch_review_contracts.py`,
  and the whole `features/FEAT-052-be2-sketch-review/` folder (ignored `evidence/local/` excluded
  from Git).
- Authority: `approvals/TASK_APPROVAL.md` (SHA256 6ba9f310d0735e6bdfaf80dc8696308989d0ed51012d813c0b991788f2aeeb24);
  approved plan `plan/PLAN_R2_APPROVED.md` SHA256 ab29530545b94346102bd037822572e483828fa697582e74a74be334cecf0c00;
  Codex review `evidence/notes/BE205_CODEX_REVIEW_20261019.md` SHA256
  0091e8e7fcdab235beee98f28fefc6919decd2b94e43d2c2f721416e4a91194a. All three unchanged.

## 2. Findings

| Finding | Status | Where | Regression | Before → after |
|---|---|---|---|---|
| RV-CR01 P1 | FIXED | moderation keyed by content + ref hashes + policy (`domain/sketch_review.py:300-337`; store `coordination.py`; service `sketch_review.py:275-282, 729-738`) | `test_sketch_review_review_fixes.py::test_rv_cr01_*` (3) | 201 + Child available → INVALID_STATE; v1 PASSED kept, v2 BLOCKED + quarantine intent |
| RV-CR02 P2 | FIXED | decisive authority/policy/generation read after token (`sketch_review.py:177-181, 212-224, 366-376`), final hold verifies | `::test_rv_cr02_*` (4: policy/grant × record_review/moderate) | 201 → POLICY_UNRESOLVED / RESOURCE_NOT_FOUND, nothing stored |
| RV-CR03 P2 | FIXED | `FakeChildCache` reauthorizes every hit (`fakes.py:169-201`) | `::test_rv_cr03_warm_cache_never_serves_after_denial` (5 changes) | cached text+asset → unavailable, no content |
| RV-CR04 P2 | FIXED | monotonic 05 generation pinned per entry (`domain/sketch_review.py:258-261`; `sketch_review.py:290-295, 719-722`; `ReviewTokenPort.generation`) | `::test_rv_cr04_*` (2, incl. fresh approve reopens) | restore → old review available again → stays closed |
| RV-CR05 P2 | FIXED | `canonical_review_command` for the fingerprint (`sketch_reviews.py:93-113`; `sketch_review.py:166-168`) | `::test_rv_cr05_*` (4, typed/json; different payload still 409) | retry 409 → 201 replayed |

Also: RV-C02 now literal-byte (`test_sketch_review_contracts.py`); RV-N15c asserts the full
lifecycle-only mutation, one event and the eligibility epoch bump (`test_sketch_review_chain.py`).
Details: `evidence/notes/BE205_REVIEW_FIX_EVIDENCE_20261019.md`.

## 3. Snapshot (SHA256, bytes; all LF)

| File | SHA256 | Bytes |
|---|---|---|
| `backend/src/sketch2life/domain/sketch_review.py` | `124619be5443f56746100c7c4430a8c183a6766496e022dfa05c88e5e70d0e6c` | 20587 |
| `backend/src/sketch2life/contracts/schemas/sketch_reviews.py` | `5e24fa034d231bd275a682b1afec5b169417ba443e5f133ed9fffcbe3e321f18` | 8807 |
| `backend/src/sketch2life/application/ports/sketch_review.py` | `75396a9f82d21b87707d9cdaa040ed78b00d760f85d596a497140fa32a2a06fa` | 7999 |
| `backend/src/sketch2life/application/services/sketch_review.py` | `e3e7bbaff0656d83b882d8aebf030374350bb489d18097369422bff17bc4d724` | 38835 |
| `backend/src/sketch2life/infrastructure/sketch_review/__init__.py` | `b5d6dbd574c882db7b5a42b354906b30f34c963f44b50199b920b78fe2197462` | 73 |
| `backend/src/sketch2life/infrastructure/sketch_review/adapters.py` | `b454de10c6a8c617663c4155aa8388437c400993453037b130b14ed4429008a3` | 5176 |
| `backend/src/sketch2life/infrastructure/sketch_review/coordination.py` | `7b912e66ac5955271b5b0fbeae94985c53e6dfada8371b76d0a73f79a880d7dd` | 11725 |
| `backend/src/sketch2life/infrastructure/sketch_review/fakes.py` | `e3ac43cb4380c99359120a6cc99ef6284b4561122da8d1f73a1554dafbb0c237` | 10106 |
| `backend/src/sketch2life/infrastructure/sketch_review/harness.py` | `d4da138b1204939b69c22769740cd5958e1bbb252eb1b67978e68a5a515ac5b0` | 12727 |
| `backend/tests/unit/test_sketch_review_domain.py` | `4a1970f8bc3f3912f858af9ae5f0ec4c867214c97560a54f99f31fa99d049304` | 9696 |
| `backend/tests/unit/test_sketch_review_service.py` | `9d40253d54673e436233c2f751f203b04f93410a2ed787194e72ed72a12c935a` | 18283 |
| `backend/tests/unit/test_sketch_review_eligibility.py` | `6c49181060cb55fdf76ac9f30f9f67166b5e30dce0ac8eda218021f33a1bdf32` | 7205 |
| `backend/tests/unit/test_sketch_review_races.py` | `49ec8e90c35088efb41ea484a25864fc1d26f0c6b8184b3c614031f6bfd63e2d` | 19217 |
| `backend/tests/unit/test_sketch_review_chain.py` | `e350e1419cc7b46d27736692b7f7e51657890da5c38212252fd7988f493dc6d6` | 7186 |
| `backend/tests/unit/test_sketch_review_review_fixes.py` | `1d405caf61c64b1fdcfe73b2f229e2578ecf1cbf22145c5325a22f7303865cf0` | 11734 |
| `backend/tests/contract/test_sketch_review_contracts.py` | `b13a5c05c1b6e41c8f88ce6fba21c8b1e1c7248fcc70e92fc3ad29b289243767` | 6533 |
| `features/FEAT-052-be2-sketch-review/fixtures/h_ai_review/sketch_review_examples.json` | `7336987387242dd07ee671fde706a0c1b1314cbb5f3a87c31b5ee758ca6396dc` | 3582 |
| `features/FEAT-052-be2-sketch-review/plan/PLAN_R2_APPROVED.md` | `ab29530545b94346102bd037822572e483828fa697582e74a74be334cecf0c00` | 68805 |
| `features/FEAT-052-be2-sketch-review/plan/PLAN.md` | `41b393cca148db6d88a83ac0a9fa2442ec0a5241a88d0c5a631766716f2663b8` | 71170 |
| `features/FEAT-052-be2-sketch-review/approvals/TASK_APPROVAL.md` | `6ba9f310d0735e6bdfaf80dc8696308989d0ed51012d813c0b991788f2aeeb24` | 3925 |
| `features/FEAT-052-be2-sketch-review/evidence/notes/BE205_CODEX_REVIEW_20261019.md` | `0091e8e7fcdab235beee98f28fefc6919decd2b94e43d2c2f721416e4a91194a` | 12360 |
| `features/FEAT-052-be2-sketch-review/evidence/metrics/BE205_CODEX_REVIEW_20261019.json` | `3964d566eb549e4318edbaccd9d483e4ffcb2d059f8b304bf285b84096be1f70` | 29511 |
| `features/FEAT-052-be2-sketch-review/evidence/notes/BE205_IMPLEMENTATION_EVIDENCE_20261019.md` | `452e8e9376c594d846e7e1102a4a3881f103820c716ebb270085d31dfe9ceb70` | 11757 |
| `features/FEAT-052-be2-sketch-review/evidence/metrics/BE205_CHECKS_20261019.json` | `0ebda6b9ad810b8ee974ee29cf4ee9aaf54245df95ea07015b7306560fb0af1e` | 5377 |
| `features/FEAT-052-be2-sketch-review/evidence/notes/BE205_REVIEW_FIX_EVIDENCE_20261019.md` | `169691a45511a71fe04bc0a513dfd9e4ba365bc100e77a8d3207186fd553af84` | 8992 |

Metrics: `evidence/metrics/BE205_REVIEW_FIX_CHECKS_20261019.json` SHA256 c8a1b8b58d70be6e59d45cf9527746301f61d1443565867e2b69ca5272ee1e1a.

## 4. Commands and results

Environment: Windows 11; root checkout `backend/.venv` CPython 3.12.10 (no installs);
`PYTHONPATH`/`MYPYPATH` = `<worktree>/backend/src`; pytest from `backend/`.

```bash
BE205_TMP=<empty-scratch-dir> BE205_PY=<repo-root>/backend/.venv/Scripts/python.exe bash features/FEAT-052-be2-sketch-review/evidence/local/fix-20261019/run_fix_checks.sh
```

| Kind | Check | Exit / result |
|---|---|---|
| new run | focused05 (7 files) | 0 — 117 passed |
| new run | X01 SK1 focused | 0 — 175 passed |
| new run | X02 contract minus 7 Pillow modules | 0 — 400 passed, 3 skipped (Pillow) |
| new run | X03 BE2-02/03 (14 files) | 0 — 405 passed |
| new run | X04 all unit | 1 — 2444 passed / 18 failed / 34 errors / 37 skipped |
| kept receipt | X04 baseline 58293f1 (`local/checks-20261019/x04_unit_all_baseline_58293f1.xml`) | 2340 / 18 / 34 / 37; sets identical to the new run, 104 new cases pass |
| new run | Ruff backend cwd | 1 (I001 in chain test, from this fix) → fixed → 0 |
| new run | chain test after import fix | 0 — 6 passed |
| new run | mypy project / `--strict` (9 source files) | 0 / 0 |
| new run | 4 validators, `git diff --check` | all 0 |
| new run | races+eligibility+regressions ×5 | 48 passed each |
| NOT_RUN | 7 Pillow-importing contract modules; Studio/runtime; providers; SQL; HTTP; UI | environment/scope |

JUnit/logs: ignored `evidence/local/fix-20261019/checks/`; probe before/after:
`evidence/local/fix-20261019/{before,after}/`.

## 5. Residuals, gates, next steps for Codex

Residuals: the 05 invalidation generation is session/org-wide (fail closed on any review-policy/
context publication); a target not yet re-moderated after a policy change stays `pending` without
content; the fake cache is a fixture consumer; single-process coordinator; DI-18 unbumped owner
facts caught only at the next pull read.

Open gates (unchanged): runtime BE2-01/04; adopted moderation/reviewer policy (BE2-14) and real
moderation; BE1 authority/consent/CMD-60 ticket/read model; database fencing/transaction boundary;
SQL; event delivery; HTTP; FE-06/T07/C04 UI; INTG-05; reviews by P2/P1/P4.

Codex next:
1. Verify this snapshot (table above) and rerun the focused + regression checks independently.
2. Re-review RV-CR01..05 against the regressions and probe outputs; decide REREVIEW verdict.
3. If PASS, present component acceptance to the owner (Claude does not self-accept), then a
   publication plan (commit groups for the four tracked docs + new files) and, separately, the
   owner's Git decision to merge into `feature/be2-01-07`.
