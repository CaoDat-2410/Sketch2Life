# FEAT-081 — Plan Revision 28: accept backend-resolved custom topics and diagnose contract rejection

- **Status:** APPROVED under the owner's active 2026-11-20 instruction to continue fixing the real Parent workflow.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>
- **Authority:** FEAT-063 canonical working SRS v2.7-draft through Rev72; unsigned.
- **Relationship:** Follow-up to Plan Revision 26 after its first real UI verification returned HTTP 200 but remained on the topic screen. It does not expand the AI-call budget.

## 1. Observed result

The backend service deterministically resolves custom text `Dong vat` to catalog topic ID `animals`, display label `Động vật`, and three unique curated cards. The authenticated HTTP endpoint returned 200, but the Expo screen did not advance and surfaced an unrelated generic account message. A client-side rejection or runtime contract mismatch remains to be isolated.

## 2. Fix

- For a catalog card selected by the Parent, require the response topic ID to equal the selected card ID and compare display labels after Vietnamese-aware case/diacritic/whitespace normalization.
- For a custom topic, let the authenticated backend's resolver return the canonical topic ID and display label. Require a non-empty canonical ID/label and valid three-card response, then use the returned canonical values. Do not compare the canonical label verbatim to the custom input.
- On rejected responses, emit a development-only diagnostic event with booleans/counts only: contract match, draft match, topic consistency, card count, unique subject count, and set freshness. Never log the entered topic, profile/child data, response IDs, or credentials.
- Keep a specific safe Parent-flow error message for any rejected subject suggestion contract.

## 3. Verification

- Run the focused topic matching test and mobile typecheck.
- Load the new bundle in the active Android app and make exactly one catalog-only subject request for the same synthetic topic flow; inspect sanitized app/API logs and verify the subject screen advances.
- If the UI still fails, stop before any AI call and use only the sanitized diagnostic flags to identify the next defect. Do not keep submitting the same request.
- The bounded activity/story/video allowances in Plan Revision 25 remain unchanged and are usable only after the UI topic/subject steps succeed.

## 4. Boundaries and paths

- Synthetic-only; no fixture/mock, real child data, account enumeration/reset, direct DB mutation, `.env`/secret edit, quota/payment change, migration, SRS change, Modal request, retry, warm-up, commit, push, or unrelated service shutdown.
- Authorized code: `apps/ui-mobile/src/parent/domain/topicMatching.ts`, `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`, and `apps/ui-mobile/tests/parentTopicMatching.test.ts`.
- Authorized records: this plan, FEAT-081 approval/status and evidence under `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/`.

