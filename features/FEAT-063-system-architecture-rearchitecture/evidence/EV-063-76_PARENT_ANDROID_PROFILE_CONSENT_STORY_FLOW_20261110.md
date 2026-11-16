# EV-063-76 — Parent Android profile, consent, and story flow

**Date:** 2026-11-10
**Plan:** Rev67, approved hash `0991C06B3052A0E78634AA6CB00FF3015EC7C9A338E8A2A529B7F0696438F0B5`
**Lifecycle:** Implemented; static review only. This is not runtime or product acceptance evidence.

## Scope delivered

- Parent Android now manages owned child profiles with immutable revisions, age in months (36–120), interests summary, explicit consent-policy acceptance, re-consent, revoke, and archive.
- Backend adds authenticated, role-checked Parent profile/data-authorization and StoryRun routes. A run pins the selected profile revision, confirmed context snapshot, consent policy version, and private artwork lineage. The active run can be resumed after reopening the app.
- The Parent screen uses camera/gallery capture for physical paper drawings, previews JPEG/PNG before upload, supports adult subject confirmation, renders the versioned story draft as readable sections/scenes, offers AI rewrite instructions up to the existing three-rewrite limit, and persists adult story confirmation.
- The optional line-sketch guide is requested only when the adult enables it and remains topic-only, independent of profile/run/artwork.
- Added `20261110_parent_profile_story_context` as an additive migration joining the twelve existing migration heads. Downgrade refuses to drop profile/context data.
- Added the versioned API contract at `artifacts/PARENT_API_CONTRACT_REV67_20261110.md`.

## Static verification

| Check | Result | Notes |
|---|---|---|
| Mobile TypeScript typecheck | PASS | `tsc --noEmit -p apps/mobile/tsconfig.json` |
| Changed Python syntax compile | PASS | 19 changed Python files compiled under local Python 3.12/3.14 |
| Alembic revision graph | PASS (static AST check) | 30 migration scripts; no missing revision references; the new revision joins all 12 prior heads into one graph head |
| `git diff --check` | PASS | No whitespace errors |
| Repository security validator | PASS | 7,157 publishable files scanned; no credential, environment, seed-account, external-reference, or absolute-machine-path finding |
| ESLint | BLOCKED | Existing config references `jest/globals`, but the required ESLint plugin/environment is unavailable to the invoked ESLint installation |
| Ruff | NOT RUN | Ruff is not installed in the available local Python 3.12 environment |
| Alembic CLI / migration execution | NOT RUN | Alembic CLI is unavailable in the local Python environment; no database was touched |

## Runtime boundary

No product test suite, PostgreSQL upgrade, Docker lifecycle, Firebase operation, or live Modal request was run for this slice. No real child data or credentials were used. The migration has not been applied to a database. Because the root consent text/version values remain blank, profile creation and consent-dependent Parent AI requests correctly fail closed until the owner supplies those values in the single root `.env`.

## Known remaining gaps against the canonical SRS

- Subject correction is persisted as an adult-corrected understanding revision; a second VLM reinterpretation has not been implemented.
- Voice capture, Whisper transcription, transcript review, video generation/playback, and the post-video outdoor activity list remain outside this slice.
- Parent history, cancellation/deletion, durable AI-job polling/reconciliation, and manual recovery from unknown Modal outcomes remain incomplete.
- Temporary line-sketch asset expiry and the complete SRS line-art/output-safety checks remain incomplete.
- Modal story input currently uses the existing worker contract; age and adult-confirmed idea are passed, while topic/interests remain in the saved context snapshot and are not added to that worker request.

See `artifacts/PARENT_API_CONTRACT_REV67_20261110.md` for endpoint schemas and detailed contract boundaries. These findings do not change the unsigned canonical SRS or close its open requirements.
