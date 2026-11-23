# Goal v3 Phase C web wiring evidence

Date: 2026-11-21 (Asia/Saigon). Environment: Windows worktree `claude/phase-c-web-wiring-f934d5`; web app at `apps/web`. Evidence is from mocked local tests; no network, API, database, Docker, or Firebase calls were made. No Git write operation was performed.

## Changes

- Added a shared notification API, inbox hook, empty template registry, and inbox page for Teacher and School Manager. Connected the two routes and marked the two shell links available without adding a badge.
- Added a typed private-share API for the three non-PUBLIC audiences and a gate based on current-version presence and archived state. PUBLIC review and occurrence-pin approval checks were left as they were.
- Created 12 new web files: 6 implementation files and 6 mocked test files. Added 36 tests across the 6 new test files. The plan was written before implementation; `SUMMARY.md` and `REVIEW.md` contain the full file list, SRS references, UI copy inventory, strict review, and follow-ups.

## Verification

- `npm run check` in `apps/web` — exit 0.
  - Build: passed, 2,086 modules transformed, 0 build errors.
  - Oxlint: 0 errors, 31 warnings, matching the measured 31-warning baseline; no new-file warnings.
  - Vitest: 39 files passed, 344 tests passed (after the independent review fixes below). Baseline was 33 files / 308 tests.
- `python tools/validate_repository_security.py` from the worktree root — exit 0; `REPOSITORY_SECURITY_VALID`; 7,880 publishable files scanned; environment files, seed accounts, credentials/signing keys, and external reference documents excluded; absolute machine paths absent.
- `git diff --check` — exit 0. Git printed a CRLF-to-LF notice for `apps/web/src/modules/teacher/App.tsx`; the tracked change is only the inbox import and route replacement.

## Independent review (Sonnet 5.5, high effort)

Verdict READY WITH NOTES, 0 P1 / 4 P2 / 11 P3. Fixed: request timeout in the notification client (15 s, `REQUEST_TIMEOUT`, key kept on retry); routing tests now assert the inbox content and the mocked list call; read-all shows the items as read at once and claims success only after a confirmed refresh; mark-one 404 refreshes the list; retry disabled while busy; invalid timestamps render a dash; group-state 409 copy only for the PARENT_GROUP audience; stale read-all key dropped on a fresh page; CRLF removed from the edited line. Not changed (P3, recorded): focus after mark-one, per-item accessible names, live-region mounting, a few weak tests. The private-share client and gate have no consumer yet: nothing in the web UI can create a private share until a Parent/group picker exists.

## Limits and follow-ups

- The notification template registry remains empty until notification producers and SRS-sourced template copy exist.
- The shell unread badge remains a separate follow-up. The private-share dialog waits for a web Parent/group picker data source.
- T-13a Teacher run cancel/delete and T-4a1 remain for Phase D when a Teacher run screen exists.
- The canonical local SRS is v2.7-draft and awaits owner sign-off. Its SHA-256 differs from the prompt's separate v3-worktree copy; the cited line content was checked and matches. See `SUMMARY.md` for the authority/source details.
