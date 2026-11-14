# Plan Rev16 — CI Feature Harness Compliance (`4/5` -> `5/5`)

- **Feature:** FEAT-069
- **Revision:** 16
- **Status:** APPROVED
- **Implementation status:** IN_PROGRESS
- **Approval basis:** Direct owner instruction after pushing `56980fe7` to `origin/FE_UI_Project_Ver2`: *"bạn thấy báo lỗi 4/5 không tôi muốn bạn fix cái đó"* (with GitHub Commits screenshot showing `✗ 4 / 5` since `FEAT-068` creation).

## Goal

Restore `Repository policy checks` (`.github/workflows/ci.yml`) from failing (`4/5`) to passing (`5/5`) by satisfying `tools/validate_harness.py` across `FEAT-068` and `FEAT-069` on clean Git checkouts, without touching runtime source code (`UI_Project/`, `backend/`, `apps/`), CI workflows, or canonical `FEAT-063` SRS `v2.5-draft`.

## Verified Root Cause

Running all five `Repository policy checks` scripts from `.github/workflows/ci.yml` locally on commit `56980fe7` identified that 4/5 validators pass (`validate_skeleton.py`, `validate_architecture.py`, `validate_repository_security.py`, `validate_team_allocation.py`), while `tools/validate_harness.py` fails (`HARNESS_INVALID`, exit code `1`) on three items:

1. Missing tracked `evidence/raw` and `evidence/metrics` directories in `features/FEAT-068-project-uiux-coverage/`.
2. Missing tracked `evidence/raw` and `evidence/metrics` directories in `features/FEAT-069-leader-uiux-review-remediation/`.
3. `features/FEAT-068-project-uiux-coverage/approvals/TASK_APPROVAL.md` line 3 uses ``- Status: `APPROVED` for the exact scope in Plan revision 1.`` rather than exact `- Status: APPROVED`, failing `validate_harness.py` line 97 when `plan/PLAN.md` declares `- Implementation status: IN_PROGRESS`.

Additionally, `git ls-files features/` confirms all other `FEAT-*` directories already have tracked files across all four required `evidence/` subdirectories (`raw`, `screenshots`, `metrics`, `notes`). Commit `aff7cb76` (`fix(ci): satisfy feature harness requirements`) previously established the exact repository precedent for resolving this on `FEAT-066` and `FEAT-067`.

## Scope

1. Create 0-byte `.gitkeep` files inside:
   - `features/FEAT-068-project-uiux-coverage/evidence/raw/.gitkeep`
   - `features/FEAT-068-project-uiux-coverage/evidence/metrics/.gitkeep`
   - `features/FEAT-069-leader-uiux-review-remediation/evidence/raw/.gitkeep`
   - `features/FEAT-069-leader-uiux-review-remediation/evidence/metrics/.gitkeep`
2. Normalize `features/FEAT-068-project-uiux-coverage/approvals/TASK_APPROVAL.md` using `FEAT-067`'s `aff7cb76` pattern (`- Status: APPROVED` followed by `- Authorization: APPROVED for the exact scope in Plan revision 1.`), and add top-level `- Status: APPROVED` in `features/FEAT-069-leader-uiux-review-remediation/approvals/TASK_APPROVAL.md` right above the existing Plan Rev1 entry while keeping all existing approval text intact.
3. Update `FEAT-069` records (`CONTEXT.md`, `DECISIONS.md`, `status/STATUS.md`, `evidence/notes/REV16_CI_HARNESS_COMPLIANCE_20261114.md`) and `approvals/TASK_APPROVAL.md`.
4. Verify all five `Repository policy checks` validators, `git ls-files` clean-clone completeness, and `git diff --check`, then commit cleanly and fast-forward push to `origin/FE_UI_Project_Ver2`.

## Explicit Exclusions

- No changes to `.github/workflows/ci.yml`, `tools/validate_*.py`, `backend/`, `apps/`, `UI_Project/`, or `features/FEAT-063-system-architecture-rearchitecture/`.
- No `--force` push or commit history rewrite.

## Acceptance Criteria

- **AC1:** `python tools/validate_harness.py` prints `HARNESS_VALID` and exits `0`.
- **AC2:** All five CI policy validators (`validate_harness.py`, `validate_skeleton.py`, `validate_architecture.py`, `validate_repository_security.py`, `validate_team_allocation.py`) exit `0`.
- **AC3:** `git ls-files features` confirms every `FEAT-*` folder has tracked files inside `evidence/{raw,screenshots,metrics,notes}`.
- **AC4:** `git diff --cached --check` and `python tools/validate_repository_security.py` pass before commit and push; `origin/FE_UI_Project_Ver2` updates cleanly via fast-forward push.
