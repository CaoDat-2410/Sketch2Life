# FEAT-081 — Plan Revision 27: re-authenticate Parent after Android bundle reload

- **Status:** APPROVED under the owner's active 2026-11-20 instruction to continue fixing and run the real Parent flow until it completes.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>
- **Authority:** FEAT-063 canonical working SRS v2.7-draft through Rev72; unsigned.
- **Relationship:** Recovery amendment to Plan Revision 25 and topic-canonicalization Addendum 49. It does not renew or expand any AI inference allowance.

## 1. Starting condition

To ensure the revised JavaScript bundle was loaded by Android, the Expo dev app was restarted. It returned to the Firebase Parent sign-in screen and did not restore the in-memory session used for the previous profile/run. The previous synthetic records are not modified or deleted.

## 2. Approved recovery

- Create one additional synthetic Firebase Parent account through the real Android signup UI using transient generated credentials. Do not print, save, screenshot, or add credentials to repository/evidence.
- Create one synthetic profile through the real UI, then proceed through the same real Parent path: topic → catalog subject suggestions → SVG guide if available → synthetic drawing → drawing analysis → adult subject/context confirmation → catalog-first activity request and persisted selection → one story/review/confirmation → one silent LTX-2.5 video only if all prior gates pass.
- Do not reuse/transfer the previous account's profile/run, query Firebase user listings, reset another account's password, or mutate/delete any prior records directly.

## 3. Bounds and evidence

- No new live AI allowance is granted. The only allowed calls remain those in Plan Revision 25: a fresh drawing call only if required by this new UI run, at most two activity calls after a specific fix/deploy and within 8 minutes each, one story after persisted activity selection, and one silent video after all gates.
- All AI requests must originate from the authenticated UI and pass existing schema, business, safety, quality, and worker checks. No fixtures, warm-up, retries, scene retries, quota/payment changes, real child data, or Modal calls beyond those caps.
- Capture only workflow screens without credentials; record sanitized request/call IDs and timing in FEAT-081 evidence. Keep the emulator on. Stop only task-used Modal apps, Metro, and Docker stack after evidence capture; preserve volumes and unrelated services.
- No `.env`/secret edits, direct DB mutation, migration, commit, push, branch/history operations, or unrelated implementation.

## 4. Authorized paths

- This plan, `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md`, `features/FEAT-081-parent-ui-mobile-port/status/STATUS.md`, and evidence under `features/FEAT-081-parent-ui-mobile-port/evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/`.
- Real Android UI interactions for synthetic authentication and workflow verification only.

