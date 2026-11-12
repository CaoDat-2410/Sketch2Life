# FEAT-081 status

- Status: ACCEPTED (WAVE 1 ONLY; NOT COMMITTED)
- Plan revision: 2
- Plan Revision 2 SHA-256: DA807873F2AFEA2BC9A86457AE9BB13A3C4CE90F5E9388B816A5676EEACE3ECC
- Architecture decision: ADR-0023-feat081-mobile-ui-target.md, SHA-256 8EABECC21A95B21FB6C15198749BCFBF5EE3FF1C64834FBD8FBDF0E3A2C436C6
- Decision log after D-009: SHA-256 3952CB3BCA12ABD21109B3F209A181CF3B91F3D1D01FAEEB5DA64ABFD64A3805
- Approval: Addendum 3 appended to approvals/TASK_APPROVAL.md; pre-append pin 7,823 bytes / 76AD28534A90FD0C9A6B6572B9A2588B0717ED78A2E679DCE22CA3D1E8B7BC79; post-append pin 11,058 bytes / CFD32E6B3B3053F150AA6A73028051760A5B7AEEDBD6420DB7895BC3CCF4B266
- Implementation report: evidence/IMPLEMENTATION_REPORT_WAVE1_20261112.md, 8804 bytes, SHA-256 01A6760B4800F810F03D3C6C6CCDE4BE78472821B88FA74BF6E3A0F404738796
- Updated: 2026-11-13, Asia/Saigon

The following implementation note is a historical pre-acceptance snapshot; the Wave 1 owner acceptance checkpoint below is current.

The owner approved the final FEAT-081 target, source boundary, and two-run AC2 policy and explicitly launched Wave 1. The four allowlisted code paths are implemented. The coordinator's baseline test and typecheck passed; coordinator post-runs, owner Android review, and owner acceptance remain pending. No acceptance record has been written. See `evidence/IMPLEMENTATION_REPORT_WAVE1_20261112.md`.

The sample P01 shows an active-child selector; HomeScreen has no selected-child input and does not receive the controller's profile. Adding it needs ParentExpoApp.tsx, which is outside the Wave 1 allowlist. Owner chose Option A on 2026-11-12: label deferred. The item moves to a later wave that is separately approved to touch ParentExpoApp.tsx (together with useParentController.ts / workflowTypes.ts if that wave needs them). The active-child label is not applicable to Wave 1 and is not marked passed.

## Wave 1 owner acceptance checkpoint - 2026-11-12

- Status: ACCEPTED (Wave 1 only); not committed.
- Accepted scope: P01 Home and P02 Lesson gallery in `apps/ui-mobile`, based on the four final code hashes in Addendum 3. The H-pin files are unchanged.
- Coordinator post-runs: `pnpm run test` reported 4 files / 29 tests passed and `UI_COPY_AND_RECOVERY_VALID`; typecheck had no diagnostics.
- Owner-run confirmation on 2026-11-12 23:56 after the filtered reinstall: same test and UI-copy results; typecheck had no diagnostics; both exited 0.
- Owner-run final-byte validators all exited 0: `HARNESS_VALID`; `REPOSITORY_SECURITY_VALID` (7,239 files); `ARCHITECTURE_VALID`; `git diff --check` clean.
- Owner report: the app ran on the Pixel_6a emulator via `android:dev` and started and ran.
- Active-child label: deferred per Option A; not accepted as Wave 1 work. Wave 2 plan R2 remains a draft, not approved and not launched. `OWNER_MODAL_CALL_APPROVED=NO`.
- This acceptance does not cover backend/API wiring, Android behavior beyond "ran", later waves, a move to `apps/mobile`, or any SRS change. It authorizes no stage, commit, or push; the commit needs a separate owner instruction.
- `TASK_APPROVAL.md` post-append pin: 11,058 bytes / SHA-256 `CFD32E6B3B3053F150AA6A73028051760A5B7AEEDBD6420DB7895BC3CCF4B266`.
