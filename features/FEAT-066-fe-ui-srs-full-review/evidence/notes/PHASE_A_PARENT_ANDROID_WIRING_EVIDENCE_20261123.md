# Goal v4 Phase A Parent Android wiring evidence

Date: 2026-11-23 (Asia/Saigon)

## Scope

- Worktree: the mobile worktree, branch `feature/fe-mobile-remediation`.
- App: `apps/ui-mobile` only, plus FEAT-066 task records.
- No commit, stage, stash, branch switch, push, backend edit, `.env` edit, signing-config edit, or `apps/mobile` edit.
- The frozen M2 projection JSON was not edited.

## Verification results

All commands ran from the worktree root. Every command exited 0.

| Command | Captured result |
|---|---|
| `npm --prefix apps/ui-mobile test` | 18 test files passed; 228 tests passed; printed `UI_COPY_AND_RECOVERY_VALID`. |
| `npm --prefix apps/ui-mobile run typecheck` | `tsc --noEmit -p tsconfig.typecheck.json` exited 0 with no diagnostics. |
| `python tools/validate_harness.py` | `HARNESS_VALID`; approval and frontend asset gates enabled. |
| `python tools/validate_repository_security.py` | `REPOSITORY_SECURITY_VALID`; 7,724 publishable files scanned; no absolute machine paths. Environment files, seed accounts, credentials/signing keys, and external reference documents excluded. |
| `python tools/validate_architecture.py` | `ARCHITECTURE_VALID`; dependency direction, mobile feature isolation, frontend asset gate, mobile AI boundary, and Firebase data-product checks valid. |
| `git diff --check` | Exit 0; no whitespace errors. Git warned that two edited FEAT-066 Markdown files have CRLF lines that will normalize to LF. |

No lint script or native Android test suite exists in `apps/ui-mobile`. Optional `gradlew assembleDebug` was not run.

## Implemented and tested

- Typed activity list and future-compatible selection body; Parent API, ports, use case, bounded response readers, visible-ASCII idempotency key, and allow-listed activity-route errors.
- Activity review with persisted selection, selection race reload for both 409 codes, a cancel-only empty-result state, and no first-story call to legacy `story-revisions`.
- Story confirmation-required path, same-revision re-confirmation, video-cap cancel-only state, safety-block display and legacy `SAFETY_BLOCKED` support.
- Completed-run playback through history: reload run, request a fresh playback grant, then play. Completed rows hide unsuitable, complete, and generation actions.
- Nullable post-video activity rendering with `is_main` labels.

The prompt contains one sequencing conflict: work item 3 says to load activities after subject and context confirmation, while the final R3 statement says activity selection is expected first and context confirmation last. The implementation follows the explicit final ordering and handles either gate as last. No other contradiction with the supplied final route list was found.

