# FEAT-081 — Plan Revision 50: one synthetic Parent registration and UI video E2E

**Status:** APPROVED by the owner's direct 2026-11-20 instruction: “thì m đký đi, chạy đi, nào nối đc, test đc trên UI thì ngừng”.  
**Product authority:** FEAT-063 canonical working SRS v2.7-draft, local amendments through Rev71; unsigned. This plan is a bounded synthetic development test, not a product requirement amendment.  
**Feature/worktree:** FEAT-081, branch `feature/fe-mobile-remediation`.

## 1. Goal

Recover the real Android Parent UI test path by registering one fresh synthetic Parent account, then continue only as far as required to exercise the currently connected Parent workflow and, if all gates pass, submit one silent video candidate through the UI. Stop when the UI confirms a successful candidate or at the first terminal blocker.

The previous credential sets failed authentication. The prior video test run is owned by another Firebase identity and is inaccessible from a newly registered account. Therefore this revision explicitly permits one fresh test account and one corresponding synthetic Parent run instead of altering ownership or accessing the old run through a backend/database bypass.

## 2. Scope and limits

1. Register exactly one synthetic Parent through the real Expo Android UI; sign in with the same account and verify the Parent role/session through the UI's normal backend integration.
2. Create at most one synthetic profile and one new StoryRun through the UI. Reuse the already generated synthetic turtle drawing from FEAT-081 evidence via Android Photo Picker; no new artwork generation is needed.
3. Exercise current real UI/API stages only as needed: subject understanding, activity selection, and story generation. Maximum one actual inference per stage; no retries. If the catalog has eligible published activities, use them without activity-model inference; call the fallback only if the existing UI requires it and the catalog has none.
4. Adult-review the exact story shown in the UI. Continue only if the returned story is contract-valid, Vietnamese, age-appropriate, and consistent with the selected drawing/activity. Do not carry Rev49's one-run test override to this new run and do not bypass story, safety, consent, identity, or ownership gates.
5. If the story passes review and the existing local synthetic candidate path is eligible, temporarily enable only `SKETCH2LIFE_PARENT_VIDEO_DEV_CANDIDATE_ENABLED` in the task API process environment for this one UI submission, keeping `SKETCH2LIFE_ENV=local`, `SKETCH2LIFE_AI_PROVIDER=modal_dev`, and the synthetic pilot gate unchanged. Do not edit `.env` or secrets. Restore the flag to false immediately after the result or before stopping on failure.
6. Submit one candidate from the UI only. Reuse the deployed `sketch2life-srs23-dev-video`; do not deploy, warm, or stop Modal apps. Poll only through the UI. If Modal has accepted the call or the result is uncertain, never resend.
7. Use no fixtures, preview harness, direct API/worker calls, database business-data edits, quota/billing reads or writes, payment, or quota bypass. Synthetic account credentials must remain ephemeral and must not be printed, logged, or committed. No real child data or fabricated legal consent.
8. If the UI requires acceptance of legal terms, stop before acceptance and hand the emulator to the owner. No account deletion or password reset is in scope.

## 3. Execution steps

### M0 — preflight

- Confirm branch/worktree, current task API health, Expo's active API URL, Firebase app/project presence without exposing secrets, local/test synthetic gates, and existing Modal video app inventory using read-only checks.
- Confirm the synthetic image path/hash and the current registration screen. Do not print `.env`, Firebase tokens, Modal credentials, or account credentials.
- Keep existing dirty changes; do not reset, stage, commit, or push unrelated work.

### M1 — registration and Parent API connection

- Generate one unique synthetic email/password in memory and register through the actual Expo form.
- If Firebase registration succeeds but backend identity synchronization fails, stop at that error; do not create another account.
- Verify the resulting role is Parent and the account can load Parent home/profile APIs through the UI. Do not use a direct API shortcut.

### M2 — one synthetic Parent run

- Create/read back one synthetic profile through the UI, with no real child information and no fabricated legal consent.
- Select the existing synthetic sea-turtle image through Android Photo Picker, then follow subject/context review.
- Make at most one drawing inference, one necessary activity suggestion inference, and one story inference. Record request/Modal IDs and durations if provided; redact credentials, token material, and raw sensitive content.
- Review the story in the app. If quality, contract, or safety is unacceptable, stop without video.

### M3 — one video candidate request

- Temporarily enable the local synthetic candidate flag for the task API only, without editing `.env`; verify the effective local/provider/synthetic guards before dispatch.
- Submit once via the real Parent UI, then poll status in the UI. Open the private technical preview only if the candidate is ready.
- Restore the candidate flag to false immediately; do not query or mutate quota.

### M4 — evidence and cleanup

- Save sanitized screenshots of the successful UI state or exact blocker, plus event timings, status transitions, request/candidate/Modal IDs, and safe error codes under a new FEAT-081 evidence directory.
- Update FEAT-081 context/status and report accurately whether the stop point was registration, Parent API, AI stage, candidate dispatch, or preview.
- Leave the task API and unrelated Docker services running unless they entered an unhealthy loop. Do not stop or change Modal apps. Do not commit or push.

## 4. Acceptance criteria

- One real Expo signup creates one synthetic Firebase Parent account, and the same UI session reaches the Parent backend successfully.
- At most one new synthetic profile and StoryRun are created, and each required AI workload is called at most once.
- If all gates pass, exactly one video candidate request reaches the existing Modal LTX worker through the real UI and the UI displays its persisted result/preview. Otherwise, the UI exposes the precise safe blocker and no duplicate request is sent.
- The local candidate flag is false at the end; no quota/billing state is accessed; no fixture, direct API/worker bypass, secret/.env edit, migration, or unrelated data change occurs.
- Evidence and FEAT-081 status/context are updated; no commit/push.

## 5. Authorized repository paths

- `features/FEAT-081-parent-ui-mobile-port/{CONTEXT.md,approvals/TASK_APPROVAL.md,status/STATUS.md,plan/**,evidence/**}`
- If a UI defect blocks signup or the approved video screen, make only the narrow fix in the existing Parent UI/API adapter paths and add focused coverage. No product-gate or server authorization relaxation is permitted.

No other repository paths are in scope.
