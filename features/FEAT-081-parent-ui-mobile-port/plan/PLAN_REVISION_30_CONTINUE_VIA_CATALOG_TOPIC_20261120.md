# FEAT-081 — Plan Revision 30: continue the Parent E2E from a curated topic card

- **Status:** APPROVED under the owner's active 2026-11-20 direct instruction to continue fixing the Parent flow and use it once the flow works.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>
- **Authority:** FEAT-063 canonical working SRS v2.7-draft through Rev72; unsigned.
- **Relationship:** Bounded recovery after the custom-topic API returned 200 but the current Android JS session did not reflect the source fix. This amendment bypasses further custom-topic attempts only for the current E2E by choosing the already visible curated “Động vật” card; it does not remove or replace custom-topic support in source.

## 1. Starting state and action

- Continue in the current authenticated synthetic Parent app/session and synthetic profile; do not restart the app or create another account/profile.
- Select the curated `animals` topic card in the UI and make one catalog-only request for its three drawing-subject cards. Require the screen to advance and show valid curated suggestions before continuing.
- If the catalog request fails or the screen still does not advance, stop before any AI request and record the sanitized API/UI boundary.

## 2. Continue the existing bounded workflow

- From the curated subject card, select a suitable animal, skip the optional guide if it requires an unapproved AI draft, then continue via the actual UI with the existing synthetic child artwork.
- Use Plan Revision 25's limits only: one fresh drawing inference if required by this new profile/run, up to two activity calls only after an actionable fix (8-minute cap), one story after the persisted activity selection, and at most one silent LTX-2.5 video after every preceding gate passes.
- No topic-subject AI, duplicate call, warm-up, automatic retry, scene retry, quota/payment, real child data, fixture/mock, direct DB edit, or model substitution.

## 3. Cleanup and records

- Append sanitized timestamps, IDs, phase timing, API status, worker evidence and UI screenshots to the existing FEAT-081 evidence folder; never log credentials/tokens or child data.
- Keep emulator online; stop only task-used Modal apps, Metro, and task Docker project after evidence is captured. Preserve volumes and unrelated services.
- No `.env`/secret edits, migration, commit, push, branch/history operation, or unrelated work.

## 4. Authorized paths

- Current Android UI interactions only for the synthetic account/profile/run.
- This plan, FEAT-081 approval/status, and evidence under `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/`.

