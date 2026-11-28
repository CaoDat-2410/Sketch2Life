# FEAT-066 Goal v4 Phase B T-12b/T-12c web wiring — Teacher profile revisions and support needs

- Plan revision: 54
- Job: `fe-v4b-web-t12bc`
- Date: 2026-11-24 (Asia/Saigon)
- Status: `APPROVED_FOR_IMPLEMENTATION` by the owner's direct launch prompt (`GIVEN`).
- Worktree: `D:\GitHub\Sketch2Life\.worktrees\ui`
- Branch: `codex/fe-ui-web-remediation`

## Goal and sources

Wire the Phase B Teacher profile revision/edit and support-needs routes into `apps/web`. Use the final route contract in `D:\GitHub\Sketch2Life\tmp\phase-v4\PHASE_B_FINAL_ROUTE_LIST_20261124.md`, sections 3 and 4, and FEAT-066 decision D-066-101. The worktree's `DECISIONS.md` does not yet contain D-066-101; the source record is in the repository-root FEAT-066 decision file. The canonical product baseline remains FEAT-063 SRS v2.7-draft and unsigned. D-066-101 leaves the support-needs key source unapproved and Teacher permission default-deny; the route contract's production responses therefore remain 503 and uniform 404 respectively.

The T-7e roster task is complete and pending owner review. Its changes are present and uncommitted in this worktree. Preserve and build on them.

## Scope and boundaries

- Change only the Teacher web implementation and named tests under `apps/web/src`: add a sibling `shared/api/teacherProfileApi.ts`, profile revision/support-needs UI components, wire them into `modules/teacher/pages/T05ClassesScreen.tsx`, extend the shared safe error table, and add API/component tests.
- Update this FEAT-066 plan, task approval, context, decisions, status, evidence index, and one evidence note.
- Do not modify School Manager code, backend, mobile, contracts, environment files, credentials, signing files, debug keystore, or model weights. Do not stage, stash, switch branches, commit, or push. Run logs stay only in `E:\AI_LOG\CODEX\fe-v4b-web-t12bc\`.

## Implementation choices

- Load revision history page on demand at `limit=100`; pass `next_cursor` unchanged when the user selects “Tải thêm”. Do not fetch all history eagerly.
- Use `teacherHttp.request` for auth and BE1 error parsing. It already preserves `current_version` as `currentVersion` and safe field errors through `OccurrenceApiError`.
- Keep decrypted support-needs values only in the mounted panel's component state. Use `cache: "no-store"`, never log or persist values, fetch only when opened, and unmount/clear state on close. Treat 404, 503, and `CONSENT_NOT_EFFECTIVE` as the same neutral unavailable state.
- Use one idempotency key per submit payload; retain it only for an unclear/retryable outcome and discard it when the form changes or a definitive result arrives.

## Acceptance criteria

1. The API client implements revision page, revision detail, profile edit, support-needs read, and support-needs write routes with encoded path segments, strict typed payloads, and `Idempotency-Key` on every write. No body contains `class_id`. Content reads and writes use `cache: "no-store"`.
2. The revisions panel shows newest first with revision number, display name, age, band label, interests, and creation time; it never renders an author. “Tải thêm” follows the opaque cursor.
3. The profile editor uses the newest revision number as `expected_revision`, validates the synthetic prefix, age, and interest limits, sends only changed fields, and renders safe messages for diagnosis-like input, stale revision, consent not effective, invalid class state, 404, and 503. After success, refresh the roster and revision list.
4. The support-needs panel loads only after open, supports revision-aware writes, displays the same neutral “Mục này chưa khả dụng.” state for 404, 503, and `CONSENT_NOT_EFFECTIVE`, and never stores values in URL, query, browser storage, logs, or a cache. Closing unmounts and clears the values.
5. Shared safe error mapping includes `SUPPORT_NEEDS_UNAVAILABLE`. No School Manager code changes.
6. Mock-only Vitest coverage pins every route's method, headers, body, page cursor behavior, `current_version` mapping, UI error mapping, the identical support-unavailable copy, state clearing on close, and absence of values from console/storage.
7. Run and record the actual output of `npm --prefix apps/web run check`, `python tools/validate_harness.py`, `python tools/validate_repository_security.py`, `python tools/validate_architecture.py`, and `git diff --check` from the worktree root. Do not repair pre-existing validator gaps.

## Plan

1. Record this plan and its SHA-256 in a narrowly scoped task-approval amendment before editing `apps/web`.
2. Reconcile the missing D-066-101 record into the worktree's FEAT-066 decision copy and record the page-on-demand and safe-state implementation choices without changing backend or product requirements.
3. Implement the typed API client and safe error mapping.
4. Add the revision/edit and support-needs panels, then wire them into each Teacher roster row while preserving T-7e behavior.
5. Add mocked API and UI tests, run the requested gates, and record evidence and any contract or baseline discrepancy.
6. Update FEAT-066 context/status/evidence index and leave the working tree unstaged for owner review.

## Verification notes

- Contract source is the final Phase B route list, sections 3 and 4; D-066-101 is the open-item decision source.
- Support-needs BE1 operations are catalogued but absent from the published SRS operation set. This remains the owner's SRS question; the UI follows the supplied final route contract and degrades safely under current production defaults.
- No visual asset generation is needed.
