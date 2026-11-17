# FEAT-065 — CI repair plan

- Status: APPROVED
- Plan revision: 2
- Implementation status: NOT_STARTED

## Goal

Repair the confirmed CI input defects on existing `feature/modal-vision-dev`, verify the smallest relevant checks, then commit and push the reviewed scoped change as authorized by Person 2. No new branch or product runtime changes.

## Scope

- Pin the UI CI matrix to Node 24.15.0, which satisfies locked jsdom/undici engine constraints. Preserve all checks and matrix members.
- Refresh `backend/uv.lock` from the existing `backend/pyproject.toml`, retaining compatible existing locked versions where possible. Keep `uv sync --locked` and current CI uv/Python pins; do not hand-edit resolution data or remove extras.
- Add tracked `.gitkeep` files to FEAT-043 `evidence/screenshots` and FEAT-063 `evidence/raw`, `screenshots`, `metrics`, `notes`. Do not modify other files of these features.
- Update only the existing route-surface contract test's explicit allowlist for FEAT-063's already implemented Lesson Library endpoints and methods, as listed in the approved API inventory. Preserve exact equality and baseline assertions; do not change runtime routers or loosen unexpected-route detection.
- Record this authorization/evidence and source-register entry. Preserve FEAT-061/063/064 plans and approvals; no `.env`, credentials, media, service or provider execution.

## Steps

1. Record approval of this scope before CI input edits.
2. Apply workflow/directory fixes and resolve lock metadata with an existing executable; no package installs. Stop and diagnose any resolver failure without weakening `--locked`.
3. Verify lock consistency, repository validators, staged diff and independent review. Run existing local tests only if matching dependencies are available without installs; record environment limits.
4. Commit only listed scope, push `HEAD:feature/modal-vision-dev`, inspect the resulting CI and report actual outcomes. Address further CI findings only within this scope; report any expansion requiring product-source changes.

## Acceptance criteria

- AC1: Node pin matches locked UI package engines; backend root requirements include pypdf, python-docx and python-pptx in resolved lock and metadata.
- AC2: All harness-required directories are tracked; validators do not bypass approval/security checks.
- AC3: Security, harness, skeleton, architecture, allocation and diff checks report actual results; lock validation succeeds or blocks publication with evidence.
- AC4: Scoped independent review has no unresolved material defect; no protected plan/approval or unrelated change is staged.
- AC4a: The existing composition test accepts the documented Lesson Library method/path pairs and continues to reject missing, unexpected or changed routes/methods.
- AC5: Commit/push match the reviewed scope; report new CI result without claiming unrun tests passed.

## Risks and mitigations

Local uv/Python differ from CI pins. Prefer a conservative resolution and validate compatibility; remote CI remains authoritative for Linux. No local package installs are authorized. Node configuration repair may expose additional UI failures; do not claim engine mismatch is the only cause.

## Verification plan

Existing Python validator suite, lock check without syncing/installing, relevant already-available tests, `git diff --check`, staged review and GitHub Actions after authorized push. No service or GPU calls.

Revision 2 follows an actual focused run: one composition test failed because its FEAT-060-only allowlist predates the FEAT-063 Lesson Library router. This test-maintenance correction is within the owner's CI-repair instruction; no product behavior changes are approved.

## Evidence plan

Record commands, actual outputs, tool versions, review and commit/run references under this feature's evidence directory. This plan is frozen for approval; progress is tracked in `status/STATUS.md`.

Implementation is blocked until `approvals/TASK_APPROVAL.md` says `APPROVED` for this plan revision.
