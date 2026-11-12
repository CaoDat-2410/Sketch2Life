# FEAT-081 — Parent UI mobile port

- Owner: Person 2 (AnhKhoaa157)
- Date: 2026-11-12, Asia/Saigon
- Status: ACCEPTED (Wave 1 only; not committed)
- Baseline: feature/fe-mobile-remediation at 1f5bb0b5b1ab501a7120598a7e6e0de75217ddb3; HEAD tree equals local origin/dev.

## Goal

Implement the approved first wave of the Parent UI port: P01 home and P02 lesson gallery in apps/ui-mobile. Wave 1 is accepted and not committed; later waves remain separately gated.

## Product and source context

The current product source is the unsigned FEAT-063 v2.7-draft SRS, routed by docs/context/SRS_AUTHORITY.md and docs/context/SOURCE_REGISTER.md. It is the canonical working baseline, not formal SRS sign-off. Requirements in older feature records and the web sample are not current product authority. Preserve missing or conflicting product requirements as open questions.

The target is the Expo SDK 52 Parent application in apps/ui-mobile, using React Native 0.76.9 and React 18.3.1. The web sample is in sibling worktree .worktrees/ui on feature/fe-ui-full-remediation at 30c94342. It is external read-only reference material; no sample code or visual assets are copied by this plan.

## Owner and merge context

CaoDat built the existing ui-mobile base. The owner will edit the Parent UI from here on, without per-file ownership reservations. CaoDat may later edit the same paths on dev, so overlapping changes carry merge risk and must be reconciled before merging. Git history does not establish current in-flight ownership.

## Approved boundary

Wave 1 is limited to the alternative allowlist pinned in approvals/TASK_APPROVAL.md: edit HomeScreen.tsx and LessonGalleryScreen.tsx, add catalogViewModel.ts and catalogViewModel.test.ts, and keep the listed hash-only files byte-identical. Shared components/ui.tsx is not edited. The new test uses synthetic fixtures only and the wave makes no API changes.

Waves 2-5 are outline only and require separate approvals. P08c, P14, and P15 remain held pending a recorded product requirement. The move to apps/mobile, Android applicationId / validate_skeleton repair, backend-route wiring, package installs, runtime/provider operations, and external publication are outside this feature. OWNER_MODAL_CALL_APPROVED=NO; no Modal action is authorized.

For the later, separately approved move to apps/mobile, the recorded portability constraints are in D-006. Any sample image, avatar, icon, or font must first pass the repository generated-asset, provenance, and visual approval gate recorded in D-007.
## Revision 2 target clarification — 2026-11-12

The owner-directed FEAT-081 location is apps/ui-mobile for Wave 1 and for any separately approved FEAT-081 follow-on UI wave, with no move to apps/mobile under this feature. ADR-0023 and appended D-009 record this as a feature-scoped implementation-location exception. The canonical SRS Rev60 and the broader apps/mobile product target remain unchanged. This clarification supersedes the older future-move wording only within FEAT-081.

## Wave 1 implementation update — 2026-11-12

This is the pre-acceptance snapshot; the later owner acceptance checkpoint below is current.

Wave 1 P01/P02 code is implemented within the approved four-path allowlist. Coordinator post-implementation tests and typecheck, owner Android review, and owner acceptance remain pending. See `evidence/IMPLEMENTATION_REPORT_WAVE1_20261112.md` and the ignored command ledger at `tmp/fe081-impl/COMMAND_LEDGER.md` for file hashes and results.

The sample P01 shows an active-child selector; HomeScreen has no selected-child input and does not receive the controller's profile. Adding it needs ParentExpoApp.tsx, which is outside the Wave 1 allowlist. Owner chose Option A on 2026-11-12: label deferred. The item moves to a later wave that is separately approved to touch ParentExpoApp.tsx (together with useParentController.ts / workflowTypes.ts if that wave needs them). The active-child label is not applicable to Wave 1 and is not marked passed.

## Wave 1 owner acceptance checkpoint — 2026-11-12

- Status: ACCEPTED (Wave 1 only); not committed.
- Accepted scope: FEAT-081 P01 Home and P02 Lesson gallery in `apps/ui-mobile`.
- Final code pins accepted from the implementation report:
  - `HomeScreen.tsx`: 4,349 bytes, SHA-256 `A09E8BC37C30DCFB293B68172119DB62C06DF93D1201C068BCC79958433B28E3`.
  - `LessonGalleryScreen.tsx`: 9,876 bytes, SHA-256 `35D75628DF9220FABA787010E5E40A895FA99AE3A3A34F325E7B752DDFB04003`.
  - `catalogViewModel.ts`: 1,962 bytes, SHA-256 `5BE1210C95C9F1CEBABADEE7DAD2169620B5B438BA85DE24941236DF018630F0`.
  - `catalogViewModel.test.ts`: 3,254 bytes, SHA-256 `8FAA29A92BD4D750C27E2109256611BA3DA8ECFE1BE72044127A81B78699C978`.
- H-pin files are unchanged.
- Coordinator runs: `pnpm run test` passed 4 files / 29 tests and printed `UI_COPY_AND_RECOVERY_VALID`; typecheck had no diagnostics.
- Owner-run confirmations on 2026-11-12 23:56 after the filtered reinstall had the same test and UI-copy results; typecheck had no diagnostics; both exited 0.
- Owner-run validators on final bytes all exited 0: `HARNESS_VALID`; `REPOSITORY_SECURITY_VALID` (7,239 files); `ARCHITECTURE_VALID`; `git diff --check` clean.
- Owner report: the app ran on the Pixel_6a emulator via `android:dev` and started and ran.
- The active-child label is deferred per Option A. Wave 2 plan R2 is a draft, not approved and not launched. `OWNER_MODAL_CALL_APPROVED=NO`.
- This acceptance does not cover backend/API wiring, Android runtime behavior beyond "ran", later waves, a move to `apps/mobile`, or any SRS change. No stage, commit, or push is authorized; the commit requires a separate owner instruction.
- `TASK_APPROVAL.md`: pre-append pin 7,823 bytes / SHA-256 `76AD28534A90FD0C9A6B6572B9A2588B0717ED78A2E679DCE22CA3D1E8B7BC79`; post-append pin 11,058 bytes / SHA-256 `CFD32E6B3B3053F150AA6A73028051760A5B7AEEDBD6420DB7895BC3CCF4B266`.
