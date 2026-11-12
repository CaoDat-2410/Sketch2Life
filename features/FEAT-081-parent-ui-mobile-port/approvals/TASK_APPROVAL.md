# Task approval log
## FEAT-081 Wave 1 Allowlist Approval - 2026-11-12

- Status: APPROVED
- Launch status: NOT LAUNCHED
- Approver: Person 2 (AnhKhoaa157), direct owner instruction dated 2026-11-12.
- Decision basis: D-001 through D-008 in DECISIONS.md.
- Scope: first-wave P01/P02 home and lesson gallery only, using the alternative allowlist below.
- OWNER_MODAL_CALL_APPROVED=NO.

### Pinned governance records

| Record | Bytes | SHA-256 |
|---|---:|---|
| DECISIONS.md | 2986 | 35CC570FABE7144ECB8B9B3AE098E484A4E432D7FEDE5448FD6FACFCC3997CB9 |
| plan/PLAN.md | 6640 | 8E038026BDD4204CE296EE7E241F8E6BE24455A8ED40ABA1B4B054CA11BDA665 |

The first entry is appended to a header-only approvals/TASK_APPROVAL.md whose pre-append SHA-256 was E2678F67B73D33C0629BFEF8F48AA7D4481BD92AD96DEF5EAB398E0BD41B66D3 (20 bytes). Future approval entries must be appended; do not rewrite or remove this entry.

### Exact Wave 1 alternative allowlist

Local existing-file pins were computed from working-tree bytes and compared byte-for-byte with the mobile worktree HEAD blobs. All five matched. The two N paths were absent from both the working tree and HEAD.

| Mode | Exact path | Working-tree bytes | Working-tree SHA-256 | HEAD comparison |
|---|---|---:|---|---|
| E | apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx | 3485 B | A48B96CBEE051329EDDDCD557948D0141DF82670E4F54B2ACBC7D14FCA19F277 | MATCH |
| E | apps/ui-mobile/src/parent/presentation/screens/LessonGalleryScreen.tsx | 5529 B | 7E49888CAE0F908C5399D05BB6DDE4246184DEB7C3E157869369BC08476BCDDF | MATCH |
| N | apps/ui-mobile/src/parent/presentation/screens/catalogViewModel.ts | absent | n/a | absent from HEAD |
| N | apps/ui-mobile/tests/catalogViewModel.test.ts | absent | n/a | absent from HEAD |
| H | apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts | 16805 B | B448B9F13A153D2F90E1BAD6A284488117B4458223C1239FC2865F850438B918 | MATCH; remain byte-identical |
| H | apps/ui-mobile/package.json | 2081 B | AC8C5AB17D61B4DD126D28D9918CB4E4EB5C40EEFD3B4C965D9597294B9CD9FF | MATCH; remain byte-identical |
| H | pnpm-lock.yaml | 470780 B | 5D778524730134CAFE360564408CBF45030B476C99A69CCD32897BAB55559A72 | MATCH; remain byte-identical |

Shared apps/ui-mobile/src/parent/presentation/components/ui.tsx is deliberately not in this alternative allowlist and must not be edited.

### External read-only references

These R-mode references are in the sibling .worktrees/ui worktree, outside the mobile checkout. Working-tree bytes were pinned and compared with that sibling worktree's HEAD blob at feature/fe-ui-full-remediation, commit 30c94342. All eight matched. They are reference-only and must not be edited.

| Mode | External read-only path | Bytes | SHA-256 | Sibling HEAD comparison |
|---|---|---:|---|---|
| R | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx | 146061 B | C730BC255D193C1F7E86502E66808D73821D954168CC8C027E5979F21FCC575B | MATCH |
| R | .worktrees/ui/apps/parent-ui/src/data/mockParentData.ts | 18193 B | 7ED10C9590FAB3BF659B7D8D2E3FADB2E888329C565300C40445CE6424D92B26 | MATCH |
| R | .worktrees/ui/apps/parent-ui/src/components/Icon.tsx | 8494 B | FB8B219784F4E14D281804DB9EA25D5CF1E819EF4A5B82398CC7B57D981D0981 | MATCH |
| R | .worktrees/ui/apps/parent-ui/src/components/Kit.tsx | 15183 B | 45EAF898312297BB5F97B6AA4E6FD96C6354AEC1003A7CE21319D0E7AFFCF93E | MATCH |
| R | .worktrees/ui/apps/parent-ui/src/components/MobileLayout.tsx | 21561 B | 2AD1684F22EF7643E737B415B30E819A2A1098A0250F51EF02CF771F5E1D0F7C | MATCH |
| R | .worktrees/ui/apps/shared/ui.tsx | 2449 B | 3E8AB6500CCDAEED199DA030973901E08EC434910E5A8B40C79CCF563FAE0894 | MATCH |
| R | .worktrees/ui/apps/shared/backendApi.tsx | 24109 B | 2B126D8C7992F3A6C2BCFE5E05DFAD6622A4314DD072E1B376A61CFD0FF6FF5D | MATCH |
| R | .worktrees/ui/apps/parent-ui/src/styles/tokens.css | 62328 B | 84DB43957C041BBC9A60E4690DE93295D89E75124CA09E600B6E8F3734E7300F | MATCH |

### Command ceilings and non-scope

- Vitest / pnpm test: at most 2 invocations total, one baseline before app edits and one post-implementation. AC2 names pnpm run test and the single-file Vitest form; any invocation counts against that ceiling.
- pnpm run typecheck: at most 2 invocations total, baseline and post-implementation.
- validate_harness.py, validate_repository_security.py, and validate_architecture.py: at most 2 invocations each.
- git diff --check: at most 2 invocations.
- No Codex command may require network access, an install, Gradle, adb, or an emulator. Test and Android runs are owner/coordinator-run outside the Codex sandbox; Codex must not run long tests without a later owner instruction.
- Non-scope: Android applicationId / validate_skeleton repair, backend-route wiring, Android runtime work, package changes, sample asset copying, later waves, and the move to apps/mobile. Each is a separate gate. P08c, P14, and P15 remain held.

This approval records a bounded scope and exact allowlist only. It authorizes nothing until the owner launches it. Implementation, any later wave, Android work, and the move to apps/mobile are separate gates.
## Addendum 2 — FEAT-081 Plan Revision 2, target, and AC2 policy — 2026-11-12

- Status: APPROVED
- Launch status: NOT LAUNCHED
- Authority: Direct owner instruction dated 2026-11-12; D-009 appended to DECISIONS.md.
- Approval scope: Final Plan Revision 2 and the FEAT-081-only apps/ui-mobile location exception recorded in ADR-0023. This addendum leaves the original approval entry unchanged.

### Final pinned records

| Record | Bytes | SHA-256 |
|---|---:|---|
| plan/PLAN_REVISION_2.md | 9473 | DA807873F2AFEA2BC9A86457AE9BB13A3C4CE90F5E9388B816A5676EEACE3ECC |
| docs/adr/ADR-0023-feat081-mobile-ui-target.md | 3207 | 8EABECC21A95B21FB6C15198749BCFBF5EE3FF1C64834FBD8FBDF0E3A2C436C6 |
| DECISIONS.md after appending D-009 | 3950 | 3952CB3BCA12ABD21109B3F209A181CF3B91F3D1D01FAEEB5DA64ABFD64A3805 |

DECISIONS.md was 35CC570FABE7144ECB8B9B3AE098E484A4E432D7FEDE5448FD6FACFCC3997CB9 immediately before D-009 was appended. The hash above is the recomputed post-append hash. The current approval file was 23655F15D57812ACE465255C7DACF3DC1488CAC485A50F961BE4AFA747993AF5 immediately before this addendum was appended.

### Adopted AC2 policy — two-run option

Require pnpm run test exactly twice: once as the pre-edit baseline and once post-implementation. The full suite runs vitest run tests followed by node scripts/validate-ui-copy.mjs, so the post-implementation suite includes tests/catalogViewModel.test.ts and the existing UI-copy validation script.

The focused command pnpm exec vitest run tests/catalogViewModel.test.ts is optional diagnostic guidance, not a required acceptance command or an additional invocation. Do not add it to the two-run sequence. Any later owner-directed focused invocation counts against the same two-invocation ceiling unless the owner separately approves a changed budget.

### Target and launch boundary

For FEAT-081 Wave 1 and any separately approved FEAT-081 Parent UI follow-on wave, apps/ui-mobile is the implementation location; do not move or duplicate these feature screens into apps/mobile. This is feature-scoped and does not amend SRS Rev60 or globally supersede ADR-0020/0021. apps/mobile remains unchanged and outside FEAT-081.

This addendum authorizes no implementation, tests, Android run, staging, commit, or push. Wave 1 still requires a separate explicit owner launch instruction. Each later wave, Android work, and any product-wide target change remain separate gates. No SRS change is claimed.

The prior one invocation of each of the three validators and git diff --check is already consumed; none is rerun under this addendum. The established ceilings remain tests 2 total, typecheck 2 total, each validator 2, and git diff --check 2.
## Addendum 3 - FEAT-081 Wave 1 owner acceptance - 2026-11-12

- Status: ACCEPTED (Wave 1 only).
- Owner: Person 2 (AnhKhoaa157); direct owner acceptance dated 2026-11-12.
- Scope: FEAT-081 Wave 1 P01 Home and P02 Lesson gallery in `apps/ui-mobile` only.
- Pre-append pin for this addendum: 7,823 bytes; SHA-256 `76AD28534A90FD0C9A6B6572B9A2588B0717ED78A2E679DCE22CA3D1E8B7BC79`.

### Accepted code pins

| Path | Final bytes | Final SHA-256 |
|---|---:|---|
| `apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx` | 4,349 | `A09E8BC37C30DCFB293B68172119DB62C06DF93D1201C068BCC79958433B28E3` |
| `apps/ui-mobile/src/parent/presentation/screens/LessonGalleryScreen.tsx` | 9,876 | `35D75628DF9220FABA787010E5E40A895FA99AE3A3A34F325E7B752DDFB04003` |
| `apps/ui-mobile/src/parent/presentation/screens/catalogViewModel.ts` | 1,962 | `5BE1210C95C9F1CEBABADEE7DAD2169620B5B438BA85DE24941236DF018630F0` |
| `apps/ui-mobile/tests/catalogViewModel.test.ts` | 3,254 | `8FAA29A92BD4D750C27E2109256611BA3DA8ECFE1BE72044127A81B78699C978` |

The three H-pin files are unchanged: `ParentApi.ts` 16,805 bytes / `B448B9F13A153D2F90E1BAD6A284488117B4458223C1239FC2865F850438B918`; `apps/ui-mobile/package.json` 2,081 bytes / `AC8C5AB17D61B4DD126D28D9918CB4E4EB5C40EEFD3B4C965D9597294B9CD9FF`; `pnpm-lock.yaml` 470,780 bytes / `5D778524730134CAFE360564408CBF45030B476C99A69CCD32897BAB55559A72`.

### Acceptance evidence

- Coordinator post-run: `pnpm run test` reported `Test Files 4 passed (4)`, `Tests 29 passed (29)`, and `UI_COPY_AND_RECOVERY_VALID`; `pnpm run typecheck` reported no diagnostics.
- Owner-run confirmations on 2026-11-12 23:56 after the filtered reinstall: the same test and UI-copy results; typecheck had no diagnostics; both commands exited 0.
- Owner-run validators on the final bytes all exited 0: `validate_harness` / `HARNESS_VALID`; `validate_repository_security` / `REPOSITORY_SECURITY_VALID` (7,239 files); `validate_architecture` / `ARCHITECTURE_VALID`; `git diff --check` clean.
- The owner ran the app on the Pixel_6a emulator via `android:dev`; it started and ran.

### Hash note

The coordinator confirmed that the pre-Addendum-2 hash `23655F15D57812ACE465255C7DACF3DC1488CAC485A50F961BE4AFA747993AF5` is the SHA-256 of the first entry up to the Addendum 2 heading with the final LF removed (5,118 bytes). The raw prefix including that LF is 5,119 bytes with SHA-256 `3A341AC34394B898BB5890DE3945DCCFAE9E790779F21739FC5637B2E0CA0771`. The file has no CRLF and no BOM; no bytes changed. This is a hashing-convention difference, not a content difference.

### Acceptance exclusions and publication boundary

This acceptance does not cover backend/API wiring; Android runtime behavior beyond "ran"; the deferred active-child label, which requires a separately approved later wave; later waves (Wave 2 plan R2 is a draft, not approved, and not launched); a move to `apps/mobile`; or any SRS change. `OWNER_MODAL_CALL_APPROVED=NO`.

This acceptance authorizes no stage, commit, or push. The Wave 1 commit requires a separate explicit owner instruction. The post-append byte length and SHA-256 of this approval file are recorded in the contemporaneous status/context checkpoint and command ledger after this append.