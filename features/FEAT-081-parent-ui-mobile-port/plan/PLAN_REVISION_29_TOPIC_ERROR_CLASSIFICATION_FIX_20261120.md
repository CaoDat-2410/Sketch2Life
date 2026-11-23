# FEAT-081 — Plan Revision 29: classify Parent topic errors by code, not class identity

- **Status:** APPROVED under the owner's active direct instruction on 2026-11-20 to continue fixing the real Parent flow.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>
- **Authority:** FEAT-063 canonical working SRS v2.7-draft through Rev72; unsigned.
- **Relationship:** Narrow follow-up to Plans 26 and 28 after the Android UI continued showing an account/authentication message for a topic-subject request that returned HTTP 200. No additional AI allowance.

## 1. Fix

- Classify topic-subject failures by a safe structural `code` field, not `instanceof ParentApplicationError`, so Expo Fast Refresh/module reload cannot change the user-facing error classification.
- Preserve the session-expired message only for known authentication-expiry codes.
- Use a topic-flow-specific generic fallback for all other failures; never tell the Parent to log in again for a topic/catalog contract failure.
- Keep the custom-topic canonicalization behavior and boolean/count-only diagnostic in Revision 28.
- Add focused coverage for Vietnamese normalization and structural topic-error classification.

## 2. Verification and bounds

- Run focused topic tests and mobile typecheck.
- Make one final catalog-only drawing-subject request from the already authenticated synthetic Parent UI after the code update. It must either show the three catalog cards or show an accurately classified safe topic error; inspect worker/API logs and sanitized UI diagnostics.
- Do not retry that request. Stop before any AI inference if it still fails; report the precise safe boundary.
- No inference budget changes: Plan Revision 25 limits remain unchanged and are usable only after the topic/subject UI gate succeeds.

## 3. Boundaries and paths

- Synthetic-only; no fixture, real child data, Modal call, retry, warm-up, direct DB mutation, account enumeration/reset, `.env`/secret edits, quota/payment change, migration, SRS change, commit, push, or unrelated service shutdown.
- Authorized code: `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`, `apps/ui-mobile/src/parent/domain/topicMatching.ts`, and `apps/ui-mobile/tests/parentTopicMatching.test.ts`.
- Authorized records: this plan, FEAT-081 approval/status, and evidence under `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/`.

