# FEAT-066 goal v3 Phase C - Android Parent wiring: evidence note (2026-11-21)

Status: implemented by Codex (gpt-6.1-terra, high) from `CODEX_PROMPT_MOBILE_WIRING_PHASE_C.md`, verified and fixed by Claude; one independent review (Sonnet 5.5, high) with one round of fixes; one commit on `feature/v3-phase-c-mobile`; not pushed. Codex summary (outside the repository): `tmp/codex-parallel/mobile-phase-c/SUMMARY.md`. Backend range read: `feature/backend-srs-api-v3` `00d5ee60..5d1af59b` (T-4a1 `50649f29`, T-8a `fa8f8e39`, T-13a `b637e679`, T-10d `5d1af59b`); the coordinator squash is `258ff4c0` on the integration branch. SRS authority: SHA-256 prefix `443A3CA3`.

## 1. What changed (all under `apps/ui-mobile`)

- T-8a notification inbox (main item): `GET /v1/notifications` (cursor, limit 25), keyed bodyless `POST /v1/notifications/{id}/read` and `POST /v1/notifications/read-all`; strict readers (`application/parentNotifications.ts`), `ParentApi`, platform use case and controller (page merge, unread count with `100+`, retained Idempotency-Key per action signature, stale 404 reload), `NotificationsScreen` with loading, empty, error and content states, capability `notifications` available when the API base URL is configured. The screen shows generic copy only and never `notification_type` or `safe_parameters`.
- T-4a1: no production Parent change; contract tests that a Teacher-owned run id answers the Parent app with the uniform 404.
- T-13a and T-10d: no Parent change (checked against the backend commits by the reviewer: Parent bodies, codes, lesson list/detail fields unchanged).
- Review fixes by Claude: inbox and run list are cleared on sign-out and on another sign-in (`resetAccountData`, effect keyed on the account subject); a mark-read that finishes after a newer load no longer overwrites the list or clears its busy flag; the key of a notification action is dropped after any definitive 4xx or `INVALID_API_RESPONSE`; read items no longer say "Thông báo mới"; stale 404 shows a calm "Thông báo này không còn nữa; danh sách đã được tải lại.".
- Tests: `parentNotifications.test.ts`, `parentActorGuardContract.test.ts` (new); `parentSrsBehavior.test.ts` pins updated.

## 2. Checks (actual results, final state)

- `apps/ui-mobile`: `npm test` 18 files, 219 tests passed, `UI_COPY_AND_RECOVERY_VALID`; `npm run typecheck` 0 errors. Codex could not run these (the worktree had no `node_modules` junction); Claude linked them and ran both.
- Worktree root: `validate_harness.py` HARNESS_VALID; `validate_repository_security.py` REPOSITORY_SECURITY_VALID; `validate_architecture.py` ARCHITECTURE_VALID; `git diff --check` exit 0.
- Not checked: device or emulator, live API.

## 3. Review (Sonnet 5.5, high, one round)

ACCEPT WITH NOTES, no P1, one P2 (previous account's inbox stayed after sign-out; fixed, also for the run list which had the same pattern) and P3 notes. Fixed: stale mark-read snapshot, busy flag ownership, key retention after definitive errors, copy of read items and of the stale 404. Left as follow-ups (P3): at 100+ unread a mark-one reloads page 1 and drops "load more" pages; strict exact-key readers reject an unknown future field (privacy fail-closed, brittle for T-8b); every item shows the same generic text until a notification-type copy table exists; the error card title is "Chưa tải được thông báo" even when a mark-read failed; no controller-level React tests (hook logic is covered by pure helpers and source pins); `parentActorGuardContract.test.ts` is a regression pin, not proof of the backend guard. The fixes after the review were checked by the tests and validators but not reviewed again (one round rule).

## 4. Open questions for the owner

1. No notification producer is wired on the backend (T-8a: tests act as producer), so the inbox is empty in practice; push (T-8b) is deferred.
2. T-10d: a Parent may now see lessons shared privately in any review state (including unreviewed Teacher drafts); the Parent lesson pin and run creation path must accept a non-approved version (backend behaviour, not verified here).
3. `docs/context/SRS_AUTHORITY.md` points to a different SRS snapshot than the `443A3CA3` file used by the goal; reconcile before future requirement work.

## 5. Vietnamese copy for owner review (no SRS string exists)

- Thông báo mới (unread item label) and Thông báo (read item label)
- Bạn có một cập nhật mới trong ứng dụng. (generic item text)
- Chưa đọc {count} (100 is shown as 100+)
- Đánh dấu tất cả đã đọc
- Thông báo này không còn nữa; danh sách đã được tải lại. (after a stale 404)
- Chưa tải được thông báo / Thử tải lại (error card, existing screen text)
