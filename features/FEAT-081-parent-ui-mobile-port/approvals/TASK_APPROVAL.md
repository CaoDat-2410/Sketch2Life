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
## Addendum 4 - FEAT-081 Wave 2 plan approval

- Status: APPROVED.
- Launch status: NOT LAUNCHED.
- Authority: direct owner approval from Person 2 dated 2026-11-13; D-010 records the owner decisions and command baselines.
- Wave 1: committed as `3c75b10d` on `feature/fe-mobile-remediation`; not pushed.
- Approved plan: `plan/PLAN_REVISION_3.md`, copied verbatim from `tmp/fe081-wave2/WAVE2_API_WIRING_PLAN_DRAFT_R2_20261112.md`, 34,224 bytes, SHA-256 `73A5873DB1F37366A7A4C69C97ED2F4A81B565C3777E10C3C0F63341FF41DA1E`.
- The `DRAFT` header in PLAN_REVISION_3.md is superseded by this approval addendum. The plan approval does not launch Wave 2.
- Pre-append TASK_APPROVAL.md pin for this addendum: 11,058 bytes, SHA-256 `CFD32E6B3B3053F150AA6A73028051760A5B7AEEDBD6420DB7895BC3CCF4B266`.
- DECISIONS.md after appending D-010: 6,312 bytes, SHA-256 `B1D747786B88AC0F0F4DCCE4221099687764752E45B2D90D6080C9E79FD165FC`. The previous DECISIONS.md prefix was 3,950 bytes, SHA-256 `3952CB3BCA12ABD21109B3F209A181CF3B91F3D1D01FAEEB5DA64ABFD64A3805`.
- Post-append TASK_APPROVAL.md size and SHA-256 are recorded in the status/context checkpoints and the command ledger after this append.

### Owner decisions and launch gates

D-010 records the six adopted product decisions: require a lesson preset/version pin; leave `drawing-understandings` unchanged with no added `Idempotency-Key`; keep consent/data-authorization removed; use the existing Activity skip instead of `activity-suggestions`; use synthetic profiles and restore them through the list route; and retain `OWNER_MODAL_CALL_APPROVED=NO` with the owner-run flow stopping before `drawing-understandings`.

2A and 2B are separate launch gates. 2A requires a separate explicit owner launch instruction. 2B requires its own explicit owner instruction after 2A passes. This addendum approves the plan only and authorizes no implementation or runtime operation.

The pending, not-yet-ACCEPTED S1a-P2 list/delete/Parent-role-gate contract is accepted as the working basis for 2A and may change slightly. Any change after S1a-P2 acceptance must be handled by a new addendum.

### Exact Wave 2 allowlists

`Both` rows apply to both checkpoint manifests. E means editable existing path; N means a new path; R means read-only; H means hash-only and must remain byte-identical. All E/H byte and SHA-256 pins below are copied from the refreshed R2 table and were rechecked against the working tree before approval.

| Checkpoint | Mode | Exact path | Pinned bytes | Pinned SHA-256 |
|---|---|---|---:|---|
| 2A | E | `apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts` | 16,805 | `B448B9F13A153D2F90E1BAD6A284488117B4458223C1239FC2865F850438B918` |
| 2A | E | `apps/ui-mobile/src/parent/application/ports/ParentPorts.ts` | 6,318 | `52041644201401DB3CEDCBC7E9C34B7954B715FA80505990ACCB9897CC87D284` |
| 2A | E | `apps/ui-mobile/src/parent/application/ports/ParentApplicationModule.ts` | 1,766 | `0635F3E3C3278C8582C071A57E18C0ACB3EA3A766BD6A89167C5DA6D36E6F73B` |
| 2A | E | `apps/ui-mobile/src/parent/application/ParentApplicationError.ts` | 252 | `B62AC222CF5CDE6915ED23EE7052A82AA636BD1F1B7603E5D3E4413D0E7E4165` |
| 2A | E | `apps/ui-mobile/src/parent/domain/types.ts` | 7,338 | `76293E25E2F3157A7EC4053703CED9F25D9213DB0347FF2B59DDE44FFD18AD24` |
| 2A | E | `apps/ui-mobile/src/parent/application/use-cases/ParentProfileUseCases.ts` | 1,472 | `9035F49E23B8077131B1EC6AB8386FF8833CB5E6908AD7C595E79219C2E8DED1` |
| 2A | E | `apps/ui-mobile/src/parent/application/use-cases/ParentLearningUseCases.ts` | 3,563 | `F24500EF6F17C105F723B9B6EAC83924A66056C3F9608E418EB546BE4050E464` |
| 2A | N | `apps/ui-mobile/tests/parentApiI2Contract.test.ts` | absent | n/a |
| 2A | N | `apps/ui-mobile/tests/parentLearningI2.test.ts` | absent | n/a |
| Both | H | `apps/ui-mobile/package.json` | 2,081 | `AC8C5AB17D61B4DD126D28D9918CB4E4EB5C40EEFD3B4C965D9597294B9CD9FF` |
| Both | H | `pnpm-lock.yaml` | 470,780 | `5D778524730134CAFE360564408CBF45030B476C99A69CCD32897BAB55559A72` |
| Both | H | `apps/ui-mobile/app.json` | 1,560 | `9489E92A02306F6F0C1F575F3FF1C1FB9331BCB58ED2FD52E49880781F2D0651` |
| Both | H | `apps/ui-mobile/app.config.js` | 1,578 | `8D78BFAE71EF705299603BD4F6FBE74388756BBEEE93A1C6F1C4D99341ED1F43` |
| Both | H | `apps/ui-mobile/metro.config.js` | 2,145 | `068C704CC6F14F15178424B584DF4FD36169C221A57C534FD39D59C209E7B5A1` |
| Both | H | `apps/ui-mobile/tsconfig.json` | 147 | `B16D29C183DA613864125B17F2C6EC4E19419EF3E47E7C207FD8E7622F941130` |
| Both | H | `apps/ui-mobile/src/parent/presentation/components/ui.tsx` | 11,444 | `722636038EE8CBDFA36A90F6D102ABB4F69A43DC5B6848978EEC8795DFFDB773` |
| Both | H | `apps/ui-mobile/src/parent/infrastructure/config.ts` | 1,049 | `F0C1E0198460E9A432E81D9E8724BCC35CD030CA8C411F2050503F1C87C0FF07` |
| Both | H | `apps/ui-mobile/src/parent/infrastructure/auth/ParentAuth.ts` | 10,305 | `BBFEEF77C3CABD2632AFE7EE96D6996509C809BB8521FBD80326223961DD6077` |
| 2B | E | `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts` | 26,476 | `E9626384DC22C9F8A2F74E9F5683D9F53DACE6596DF8FE16A80CE49CCDC3ABEF` |
| 2B | E | `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx` | 15,960 | `7319EFF269ED8C714E7AC1AD5F5BB91277E4F3ECB022E59473169C20F9D84C12` |
| 2B | E | `apps/ui-mobile/src/parent/presentation/screens/ContextScreen.tsx` | 2,499 | `B1E96B75C4E2396CDE249A4D7B191D22F50F673A6490A3CDDF0C6F5B715758B2` |
| 2B | E | `apps/ui-mobile/src/parent/presentation/screens/ProfileFormScreen.tsx` | 4,780 | `99EC05ABBE0C0460668CEE8418B3CF071945580ADC28311EE72A54EC12BA59E6` |
| 2B | E | `apps/ui-mobile/src/parent/presentation/screens/ProfileScreen.tsx` | 3,928 | `36C7C0732AF25DFAC7911C9B44E55253C2A358EB05CC1BDB03CCF5A869139773` |
| 2B | E | `apps/ui-mobile/src/parent/presentation/screens/ProfileSharingScreen.tsx` | 3,771 | `F0BA4F7FA51E887161CFBF88DC1A1C6` |
| 2B | E | `apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx` | 4,349 | `A09E8BC37C30DCFB293B68172119DB62C06DF93D1201C068BCC79958433B28E3` |

| Both | R | `apps/ui-mobile/src/parent/presentation/navigation/workflowTypes.ts` | read-only | n/a |
| Both | R | `apps/ui-mobile/src/parent/presentation/screens/ActivityScreen.tsx` | read-only | n/a |
| Both | R | `apps/ui-mobile/src/parent/application/use-cases/ParentLessonUseCases.ts` | read-only | n/a |
| Both | R | `apps/ui-mobile/src/parent/application/use-cases/ParentPlatformUseCases.ts` | read-only | n/a |
| Both | R | `apps/ui-mobile/src/parent/presentation/navigation/useParentPlatformController.ts` | read-only | n/a |
| Both | R | `apps/ui-mobile/src/parent/ParentModule.ts` | read-only | n/a |
| Both | R | `apps/ui-mobile/tests/mainFlowSafety.test.mjs` | read-only | n/a |
| Both | R | `apps/ui-mobile/tests/storyDraft.test.ts` | read-only | n/a |
| Both | R | `apps/ui-mobile/tests/apiRetryIdentity.test.mjs` | read-only | n/a |
| Both | R | `.worktrees/dev-on-s1ap/features/FEAT-063-system-architecture-rearchitecture/plan/M2_INTEGRATION_DEV_ON_S1AP_CHANGES_VS_DEV_20261112.md` | read-only | n/a |
| Both | R | `.worktrees/dev-on-s1ap/tmp/dev-on-s1ap/FE_API_MIGRATION_GUIDE_apps-mobile.md` | read-only | n/a |
| Both | R | `backend/src/sketch2life/interfaces/http/routers/parent_profiles.py` | read-only | n/a |
| Both | R | `backend/src/sketch2life/contracts/schemas/parent_profiles.py` | read-only | n/a |
| Both | R | `backend/src/sketch2life/domain/parent_profiles.py` | read-only | n/a |

### Command ceilings and owner baselines

| Command | Total ceiling | Baseline accounting | Remaining planned use |
|---|---:|---|---|
| `pnpm run test` from `apps/ui-mobile` | 3 | Baseline consumed by owner-run results at 2026-11-12 23:56 and 2026-11-13 00:15. | One post-2A and one post-2B run. |
| `pnpm run typecheck` from `apps/ui-mobile` | 3 | Baseline consumed by owner-run results at 2026-11-12 23:56 and 2026-11-13 00:15. | One post-2A and one post-2B run. |
| `python tools/validate_harness.py` from repository root | 2 | Baseline invocation consumed; owner reported exit 0. | One final post-2B run. |
| `python tools/validate_repository_security.py` from repository root | 2 | Baseline invocation consumed; owner reported exit 0. | One final post-2B run. |
| `python tools/validate_architecture.py` from repository root | 2 | Baseline invocation consumed; owner reported exit 0. | One final post-2B run. |
| `git diff --check` from repository root | 2 | Baseline invocation consumed; owner reported exit 0. | One final post-2B run. |

The owner-run baseline evidence is 4 test files / 29 tests passed, `UI_COPY_AND_RECOVERY_VALID`, typecheck with no diagnostics, and all three validators plus `git diff --check` exiting 0. The owner reports these bytes were identical to commit `3c75b10d`.

### Acceptance criteria

**Checkpoint 2A**

- **2A-AC1:** Fake-fetch tests prove list query encoding and `items`/`next_cursor` pagination, create/read/patch/delete methods and response shapes, required idempotency headers, and no network access.
- **2A-AC2:** Fake-response tests cover pending deletion, `ACTIVE_RUN_EXISTS`, `STALE_REVISION`, role-denied `ACTION_NOT_ALLOWED`, `PARENT_STORE_UNAVAILABLE`, and field errors in supported top-level/nested forms; safe error metadata is retained where present.
- **2A-AC3:** Fake-port tests verify the tomorrow scenario requires a selected lesson pin, maps its IDs/hash exactly, omits legacy consent/profile-revision/context fields, and delegates explicit context confirmation. Drawing-understanding has no added idempotency header.
- **2A-AC4:** `pnpm run test` and `pnpm run typecheck` pass at the post-2A checkpoint. These are the only 2A acceptance checks.
- **2A-AC5:** Only 2A E/N paths change; all common H pins remain byte-identical.

**Checkpoint 2B**

- **2B-AC1:** Parent list pages restore existing synthetic profiles through `next_cursor`; fresh synthetic profile creation is followed by GET-by-ID before the profile is used.
- **2B-AC2:** Profile create/edit/delete UI shows safe field/role/store errors; a 202 deletion request remains visibly pending and is not represented as completed.
- **2B-AC3:** Home receives the selected profile via an explicit prop from `ParentExpoApp`; it does not infer selection from `profiles`.
- **2B-AC4:** The selected lesson pin is required for tomorrow's StoryRun create; the server context is presented and explicitly confirmed. The existing Activity skip is used; `activity-suggestions` is never called.
- **2B-AC5:** `pnpm run test` and `pnpm run typecheck` pass after the UI migration; H pins remain byte-identical; repository validators and `git diff --check` stay within their separate ceilings.
- **2B-AC6 - owner-run pre-Modal acceptance:** Using the scratch/integration service and synthetic profile data, run only these steps: authenticate Parent; list synthetic profiles; restore/read a listed profile or create a synthetic profile and GET it by ID; select a lesson pin; create the StoryRun with that pin; display and confirm the returned context. Stop immediately after successful context confirmation and before `POST /api/parent/v1/ai/drawing-understandings`. No drawing upload/analysis or story revision is allowed while `OWNER_MODAL_CALL_APPROVED=NO`. This is a pre-Modal contract acceptance, not a full Parent story completion.
- **2B-AC7:** No path outside the 2B E paths changes; shared H pins remain byte-identical; no code is staged or published under this plan.

### Additional 2A compatibility requirements

2A may not break the 29 existing tests established by the owner-run baseline. Do not remove `authorization_state`, `authorization_policy_version`, or `authorization_current` from `apps/ui-mobile/src/parent/domain/types.ts`; the Wave 1 fixture in `apps/ui-mobile/tests/catalogViewModel.test.ts` uses those fields.

The post-append Addendum 4 approval-file byte length and SHA-256 are recorded in the status/context checkpoints and command ledger after this append. This addendum approves the plan only; status remains NOT LAUNCHED until a separate 2A launch instruction.
## Addendum 4 correction - ProfileSharingScreen pin

The 2B E-pin for `apps/ui-mobile/src/parent/presentation/screens/ProfileSharingScreen.tsx` in the preceding Addendum 4 table was truncated during transcription. The correct R2 and working-tree pin is 3,771 bytes, SHA-256 `F0BA4F7FA51E887161CFBF88DC1A553540596616B7DAFBE35990FA75E494C1C4`. This append-only correction supersedes only that table cell; all other Addendum 4 entries remain unchanged.
## Addendum 5 - FEAT-081 Wave 2A launch

- Status: LAUNCHED (Wave 2A only).
- Checkpoint 2B: NOT LAUNCHED; it requires its own explicit owner instruction after 2A passes.
- Authority: direct owner launch instruction from Person 2 dated 2026-11-13, under Addendum 4 and `plan/PLAN_REVISION_3.md`.
- Approved plan pin: `plan/PLAN_REVISION_3.md`, 34,224 bytes, SHA-256 `73A5873DB1F37366A7A4C69C97ED2F4A81B565C3777E10C3C0F63341FF41DA1E`.
- Pre-append `TASK_APPROVAL.md` pin: 23,557 bytes, SHA-256 `D6BFFDDC0009A3C02347C65EC74D732D257253EDFFC5F5EBABE068F358D931CE`.
- Scope: implement only the seven 2A E paths and two 2A N tests from Addendum 4. No 2B file, H file, or other application path is authorized for editing.
- Record-keeping scope clarification: exactly one additional Wave 2A record path is authorized, `features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVE2A_20261113.md`, mode N (new documentation file), and no other new path. This is a record-keeping scope clarification, not a widening of the code allowlist. The 2B report path needs its own authorization in the 2B launch instruction.
- The post-append `TASK_APPROVAL.md` byte length and SHA-256 are recorded in the status/context checkpoint and command ledger after this append.

### Owner authorization (verbatim)

```text
OWNER AUTHORIZATION (Person 2, 2026-11-13): I authorize exactly one additional record path for Wave 2A: features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVE2A_20261113.md, mode N (new documentation file), and no other new path. This is a record-keeping scope clarification, not a widening of the code allowlist. Record this authorization verbatim in Addendum 5 and the ledger. The 2B report path needs its own authorization in the 2B launch instruction.
```
### Addendum 5 review reference (append-only continuation)

- Cold review: `tmp/fe081-wave2/REVIEW_R2_ROUND1_20261113.md`; verdict `NEEDS REVISION`.
- Person 2 accepts the review findings and directs their application to Wave 2A within the existing 2A allowlist. The 2B findings remain outside this launch and are reserved for the separate 2B launch addendum.
### Addendum 6 - FEAT-081 Wave 2A post-run rework authorization

Status: Wave 2A remains LAUNCHED while this bounded rework is in progress; Wave 2B remains NOT LAUNCHED and requires its separate owner instruction.

Pre-append approval pin: 25,709 bytes / SHA-256 `773B46FFFB1D30BFE6626A2363EE2EEB2DE9072EBCF16ECA54B3E39A8E4BE0D9`.

The coordinator post-2A run on 2026-11-13 is consumed and showed one failing test plus one unhandled rejection, with the 29 existing tests passing; typecheck reported one error. The test stdout was 1,254 bytes / SHA-256 `73CEF8FD2CEAA89F694F476DE1AFAB3D4EC9556D1C6FD23B4A7DD99D633D2FE8`; typecheck stdout was 460 bytes / SHA-256 `E82F8D4EA4E79C715E3CEC72027BA21D49DFAB72B1490A4352313092675D7071`. The bounded rework corrects the asynchronous lesson-pin assertion/unhandled rejection and introduces a separate nullable active-story-run envelope. It remains within the seven 2A E paths and two 2A N tests; it adds no path and changes no H, 2B, or R file.

### Additional command ceiling (owner wording)

```text
one additional coordinator-run pnpm run test and one additional pnpm run typecheck for this 2A rework only (total test 4, typecheck 4); the single post-2B run of each stays. The post-2A run above is consumed.
```

The extra coordinator run is the third test and third typecheck invocation, reserved for this 2A rework. The fourth invocation of each remains the single post-2B run. Existing validator and `git diff --check` ceilings remain unchanged. Codex is not authorized to run checks, stage, commit, or push.

## Addendum 7 - FEAT-081 Wave 2B launch

- Status: LAUNCHED (Wave 2B only). Wave 2A has passed its coordinator post-run; Wave 1 remains accepted and committed as `3c75b10d` on `feature/fe-mobile-remediation` (not pushed). Wave 2A remains uncommitted. Wave 2 is to be one commit after 2B; nothing is committed now.
- Authority: direct owner launch from Person 2 dated 2026-11-13, under Addendum 4 and `plan/PLAN_REVISION_3.md` (34,224 bytes / SHA-256 `73A5873DB1F37366A7A4C69C97ED2F4A81B565C3777E10C3C0F63341FF41DA1E`). The older plan text describing the `1f5bb0b5` snapshot and Wave 1 as uncommitted/awaiting acceptance is superseded by the accepted Wave 1 records.
- Pre-append `TASK_APPROVAL.md` pin: 27,265 bytes / SHA-256 `64ABD9A8D94B84731965F99324E1E481B14B6005B2E0FF32F2505CACAC7B3E62`.
- The seven 2B E paths remain exactly those in Addendum 4: `useParentController.ts`, `ParentExpoApp.tsx`, `ContextScreen.tsx`, `ProfileFormScreen.tsx`, `ProfileScreen.tsx`, `ProfileSharingScreen.tsx`, and `HomeScreen.tsx` under `apps/ui-mobile/src/parent/presentation/`.
- The owner-approved additional N code/test paths are exactly `apps/ui-mobile/src/parent/presentation/navigation/parentFlowV1.ts` and `apps/ui-mobile/tests/parentFlowV1.test.ts`. The owner-approved additional N record path is exactly `features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVE2B_20261113.md`. No other new path is authorized. The nine shared H paths remain frozen at their Addendum 4 pins; R paths stay read-only. The 2A files remain unchanged unless a 2B defect requires an owner-approved correction.
- Test ceiling: exactly one coordinator-run `pnpm run test` post-2B invocation remains (run 4/4). Typecheck ceiling: exactly one coordinator-run `pnpm run typecheck` post-2B invocation remains (run 4/4). Each validator and `git diff --check` has one owner-run final invocation remaining (2/2).
- No test, typecheck, validator, `git diff --check`, install, Android, or network command is authorized for Codex. No stage, commit, or push is authorized now. `OWNER_MODAL_CALL_APPROVED=NO`; stop the owner-run flow after explicit context confirmation, before drawing-understanding or story-revisions.

### Owner-approved additional paths (verbatim)

```text
AUTHORIZATION (code allowlist additions, owner-approved, recorded verbatim): exactly two NEW paths in addition to the seven 2B E paths: apps/ui-mobile/src/parent/presentation/navigation/parentFlowV1.ts (pure, framework-free helpers) and apps/ui-mobile/tests/parentFlowV1.test.ts (Vitest, fake data only). Reason: the review found no offline test path for 2B-AC1..AC4 and the package has no React renderer, so the testable behavior must be pure functions. One new documentation path: features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVE2B_20261113.md. No other new path.
```

## Addendum 8 - FEAT-081 Wave 2B post-run rework authorization

- Status: Wave 2B remains LAUNCHED; this bounded rework is authorized. Wave 2A remains unchanged. Wave 2 is not accepted and remains uncommitted.
- Pre-append `TASK_APPROVAL.md` pin: 30,117 bytes / SHA-256 `3123895D0E3122500EFAD65A9B93E551ADBBF6CC90F9EC2FA54B45B815CCACAB`.
- Coordinator post-2B result (log `tmp/fe081-impl/coordinator_post2B_20261113T094306/`): `pnpm run test` passed 7 files / 52 tests and printed `UI_COPY_AND_RECOVERY_VALID`; stdout 628 bytes / SHA-256 `3FF0E0E8F869264D2C37971F5957EE54BBF980CA4596E2B40D874E236A222D93`. `pnpm run typecheck` reported one TS2322 at `ProfileScreen.tsx(67,13)` because `SecondaryButton` does not accept `busy`; stdout 462 bytes / SHA-256 `65F77633BF2A331072B35FA76618B5A56C6895D70C64EC00E3DBA75467597358`. The owner reports all 20 pins matched.
- Fix only the `ProfileScreen.tsx` shared-button prop mismatch within the existing 2B allowlist. Recheck other shared-component prop usages against the declarations in the frozen `components/ui.tsx`; do not edit that H file.
- Copy-only authorization is limited to text in `apps/ui-mobile/src/parent/presentation/screens/TopicScreen.tsx`: remove copy saying a photo is required or that the next step is photo capture. Make no logic, prop, or layout changes. Its pre-edit pin was recorded in the command ledger. Read `scripts/validate-ui-copy.mjs` and preserve its copy rules; Codex must not run it.
- No H, R, or 2A file may be edited. Scope is limited to the existing 2B allowlist, the two already-authorized 2B helper/test paths, TopicScreen text only, and the already-authorized 2B report/status/context/ledger records.

### Owner command-ceiling direction (verbatim)

```text
one additional coordinator-run pnpm run test and one additional pnpm run typecheck for this 2B rework only (total 5 each); the final validators and git diff --check stay at one owner-run final run each.
```

This consumes the original post-2B run as invocation 4/5 and authorizes one coordinator rework invocation 5/5 for both test and typecheck. The single owner final invocation for each validator and `git diff --check` remains unchanged. Codex is not authorized to run any of these checks or to install, use Android tooling, access the network, stage, commit, or push.

### Owner rework and copy authorization (verbatim)

```text
1) Fix ProfileScreen.tsx only inside the 2B allowlist: remove the busy prop and express the busy state with disabled plus a changed label (for example "Dang gui yeu cau..." with proper Vietnamese diacritics consistent with the other copy). Do NOT edit components/ui.tsx (H pin). Re-check every other use of props that may not exist on shared components in the 2B files (read the prop types in ui.tsx) and fix any similar mismatch now so the next typecheck is clean.
2) Copy-only authorization: you may edit apps/ui-mobile/src/parent/presentation/screens/TopicScreen.tsx for TEXT ONLY, so that it no longer says a photo is required or that the next step is photo capture (the app now routes to the context step). No logic, prop or layout change; re-hash the file first and record its pin before and after; keep UI_COPY_AND_RECOVERY_VALID passing by following the rules of scripts/validate-ui-copy.mjs (read it).
```

## Addendum 9 - FEAT-081 Wave 3 plan approval

- Status: Plan Revision 4 APPROVED; Wave 3 NOT LAUNCHED.
- Authority: direct owner approval from Person 2 dated 2026-11-13. This approves the plan only and does not launch implementation.
- Approved plan pin: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_4.md, 18,717 bytes / SHA-256 `6D3FEF1B2C24595EBC4F6499368330C485471AF59A4E9C974CF1F5C97BD71E0A`.
- Pre-append DECISIONS.md pin: 6,312 bytes / SHA-256 prefix `B1D74778`.
- Post-append DECISIONS.md pin: 9,467 bytes / SHA-256 prefix `B589A16E`.
- Pre-append TASK_APPROVAL.md pin: 33,408 bytes / SHA-256 `DD0AE7A3E219EE4A6FF2DC362F07BDD3E45AADE8BE6EDA1FAE7CCD6A3A20E390`.
- Scope: The complete 10 E paths, 17 H paths, and R path list are exactly those in the pinned plan. Owner-authorized new paths are exactly `apps/ui-mobile/src/parent/presentation/screens/DrawingGuideScreen.tsx`, `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_4.md`, and `features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVE3_20261113.md`. No other new path is authorized.
- Test ceiling: `pnpm run test` from `apps/ui-mobile`, 2 coordinator-run invocations total (baseline and post-implementation). Codex runs none.
- Typecheck ceiling: `pnpm run typecheck` from `apps/ui-mobile`, 2 coordinator-run invocations total (baseline and post-implementation). Codex runs none.
- As in the plan, `python tools/validate_harness.py`, `python tools/validate_repository_security.py`, `python tools/validate_architecture.py`, and `git diff --check` each have a ceiling of 2; Codex runs none.
- OWNER_MODAL_CALL_APPROVED=NO.

A separate explicit launch instruction is still required before Wave 3 implementation. This approval does not authorize implementation, tests, runtime work, staging, commit, or push.

## Addendum 10 - FEAT-081 Wave 3 V1 story-revision read-model clarification

- Status: Plan Revision 4 remains APPROVED; Wave 3 remains LAUNCHED; D-012 clarification recorded.
- Authority: direct owner decision from Person 2 dated 2026-11-13. This clarifies D-011 decision 7 and does not create a new launch.
- Approved plan pin: `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_4.md`, 18,717 bytes / SHA-256 `6D3FEF1B2C24595EBC4F6499368330C485471AF59A4E9C974CF1F5C97BD71E0A`.
- Pre-append `DECISIONS.md` pin: 9,467 bytes / SHA-256 prefix `B589A16E`.
- Post-append `DECISIONS.md` pin: 10,914 bytes / SHA-256 prefix `5AD97606`.
- Pre-append `TASK_APPROVAL.md` pin: 35,223 bytes / SHA-256 `17C9036671C2CCB40FE51A9DDD403DF3FB9AB52EED8A2DED6178ED862531D088`.
- Scope: the 10 E paths, 17 H paths, and R path list remain exactly those in Plan Revision 4; no path or allowlist change is authorized. The runtime-validated story read model may live only in `apps/ui-mobile/src/parent/presentation/navigation/parentFlowV1.ts`. No H path is authorized for edit.
- Test ceiling: `pnpm run test` from `apps/ui-mobile`, 2 coordinator-run invocations total (baseline and post-implementation). Codex runs none.
- Typecheck ceiling: `pnpm run typecheck` from `apps/ui-mobile`, 2 coordinator-run invocations total (baseline and post-implementation). Codex runs none.
- As in the plan, `python tools/validate_harness.py`, `python tools/validate_repository_security.py`, `python tools/validate_architecture.py`, and `git diff --check` each have a ceiling of 2; Codex runs none.
- OWNER_MODAL_CALL_APPROVED=NO.

This clarification does not change the existing Wave 3 launch status.

## Addendum 11 - FEAT-081 Wave V plan approval

- Status: Plan Revision 5 APPROVED; Wave V NOT LAUNCHED.
- Authority: Direct owner approval from Person 2 dated 2026-11-13. This approves the plan only and does not launch implementation.
- Approved plan pin: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_5.md, 49,834 bytes / SHA-256 73A706C2A241AC2CF4F8A48946672F1B9549FE44023DEA8FBC4A12E0E089FE67.
- Pre-append DECISIONS.md pin: 10,914 bytes / SHA-256 prefix 5AD97606.
- Post-append DECISIONS.md pin: 13613 bytes / SHA-256 prefix 4FC79E32.
- Pre-append TASK_APPROVAL.md pin: 36896 bytes / SHA-256 7D83589D3E70650C6620E3EFEDB1EE58290365070ED6E79EE3989FEA1D7D8554.
- Scope: The 25 E paths, six N paths, 35 H paths and 17 R paths are exactly those pinned in features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_5.md. ui.tsx is the only H path opened as E in V0; every other H path, package.json and pnpm-lock.yaml remain byte-identical. No route, filter, detail view, state, behavior, test, contract, package, lockfile, dependency or copied asset change is authorized. No copy changes are authorized except text strictly required by layout with owner approval; because apps/ui-mobile/scripts/validate-ui-copy.mjs does not scan Parent screens, compare every edited string before/after. Owner emulator acceptance is per checkpoint; screenshots are not committed and the report records references and the owner result only.
- Test ceiling: pnpm run test from apps/ui-mobile, 2 coordinator-run invocations per checkpoint. Codex runs none.
- Typecheck ceiling: pnpm run typecheck from apps/ui-mobile, 2 coordinator-run invocations per checkpoint. Codex runs none.
- As in the plan, python tools/validate_harness.py, python tools/validate_repository_security.py, python tools/validate_architecture.py, and git diff --check each have a ceiling of 2 owner-run invocations per checkpoint. Codex runs none.
- OWNER_MODAL_CALL_APPROVED=NO.

A separate explicit launch instruction is required for each checkpoint V0-V4. This approval does not authorize implementation, tests, runtime work, staging, commit or push.

## Addendum 12 - FEAT-081 Wave R Plan Revision 7 approval

- Status: Plan Revision 7 APPROVED; Wave R NOT LAUNCHED.
- Authority: Direct owner approval from Person 2 dated 2026-11-13. This approves the plan only and does not launch implementation.
- Approved plan pin: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_7.md, 70,512 bytes / SHA-256 7979A7A990C36F159303F3B011D56626CCAA1AB998A6C7C9C7CB25F47ED024C9.
- Pre-append DECISIONS.md pin: 13,613 bytes / SHA-256 4FC79E32E838C5A07E01CA601F28AED35B437334FE4D73493E84BB5DF4F94FB3.
- Post-append DECISIONS.md pin: 25,930 bytes / SHA-256 EAB5F1F30B08CCB50E3A081FE85C0D4F5E6A453BE68E320A78C6E17D2DBE43C8.
- Pre-append TASK_APPROVAL.md pin: 39,015 bytes / SHA-256 2F5D9304F3555A9DC28B7A8EB87DB9958A890EA161F5E39486811DD755C8380C.
- Scope: The 43 E paths, eight N paths, 17 H paths and 24 R paths, including their byte counts and full SHA-256 pins, are exactly those listed in Section 11 of features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_7.md. The plan's eight N rows are the only checkpoint paths authorized for creation if their checkpoint is separately launched:
  - apps/ui-mobile/src/parent/application/ports/ParentCapabilityPorts.ts
  - apps/ui-mobile/src/parent/infrastructure/unavailable/ParentUnavailableCapabilityAdapter.ts
  - apps/ui-mobile/tests/parentSrsBehavior.test.ts
  - features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R0_20261113.md
  - features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R1_20261113.md
  - features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R2_20261113.md
  - features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R3_20261113.md
  - features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R4_20261113.md
  The exact 18 former-H paths reclassified E are those listed with rationale in Plan Revision 7 Section 12 and D-014. All other H paths remain frozen, including the package manifest and repository lockfile. No other checkpoint path is authorized. Visual gate: OI-17 sign-off is deferred until the owner reviews R0 emulator screenshots; screenshots remain local and synthetic. Backend boundary: only routes listed in the BE handoff may use real adapters; absent routes use typed unavailable ports in the normal app and fakes only in tests; never show fake success. No package, dependency, lockfile, copied-asset, provider, Modal, or absent-route wiring change is authorized.
- Test ceiling: pnpm run test from apps/ui-mobile, at most two coordinator-run invocations per checkpoint, one baseline and one post-implementation. Codex runs none.
- Typecheck ceiling: pnpm run typecheck from apps/ui-mobile, at most two coordinator-run invocations per checkpoint, one baseline and one post-implementation. Codex runs none.
- As in the plan, validate_harness, validate_repository_security, validate_architecture, and git diff --check each have a ceiling of two owner-run invocations per checkpoint, plus one owner emulator review. Codex runs none. No install, network, backend, or Modal command is authorized.
- OWNER_MODAL_CALL_APPROVED=NO.

A separate explicit launch instruction is required for each checkpoint R0, R1, R2, R3 and R4. This approval does not authorize implementation, tests, runtime work, staging, commit or push.

## Addendum 13 - FEAT-081 Wave R backend-boundary clarification

- Status: Plan Revision 7 remains APPROVED; checkpoints R1-R4 launched by the owner in this run; route clarification recorded in D-015; no scope, allowlist, pin, ceiling or checkpoint change.
- Authority: Direct owner clarification from Person 2 dated 2026-11-13. This records the route boundary and implementation clarifications without changing scope, allowlist, pins, command ceilings or checkpoint sequence.
- Approved plan pin: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_7.md, 70,512 bytes / SHA-256 7979A7A990C36F159303F3B011D56626CCAA1AB998A6C7C9C7CB25F47ED024C9.
- Pre-append DECISIONS.md pin: 25,930 bytes / SHA-256 EAB5F1F30B08CCB50E3A081FE85C0D4F5E6A453BE68E320A78C6E17D2DBE43C8.
- Post-append DECISIONS.md pin: 31,797 bytes / SHA-256 5FD6A07D52A29018D4FC841BBB59FE74329A88B0AC642B316D290A1B4C7A172E.
- Pre-append TASK_APPROVAL.md pin: 42,374 bytes / SHA-256 647B9891CEB65DF652CC00D887E3B4D652DEB8EB3D5E2F107F6D49E195F0A007.
- Scope: D-015 records the owner-authorized REAL and ABSENT route table, runtime-verification status, frozen-H rule and R0-path and regression-test clarifications. Plan Revision 7, its E/H/R/N allowlist, pins, per-checkpoint ceilings and R1-R4 sequence remain unchanged. The BE handoff note remains unchanged.
- Test ceiling: pnpm run test from apps/ui-mobile, at most two coordinator-run invocations per checkpoint, one baseline and one post-implementation. Codex runs none.
- Typecheck ceiling: pnpm run typecheck from apps/ui-mobile, at most two coordinator-run invocations per checkpoint, one baseline and one post-implementation. Codex runs none.
- As in the plan, validate_harness, validate_repository_security and validate_architecture, plus git diff --check, each have a ceiling of two owner-run invocations per checkpoint, plus one owner emulator review. Codex runs none. No install, network, backend or Modal command is authorized.
- OWNER_MODAL_CALL_APPROVED=NO.

This clarification records the route boundary for the already-launched R1-R4 sequence. It does not alter checkpoint scope, allowlist, pins, ceilings, or launch status.
## Addendum 14 - FEAT-081 Wave R owner clarification (consent non-blocking, no-preset unavailable)

- Status: Plan Revision 7 remains APPROVED; the owner clarification is recorded in D-016; no scope, allowlist, pin, ceiling or checkpoint change.
- Authority: Direct owner clarification from Person 2 dated 2026-11-13 in tmp/fe081-waveR2/GOAL_RESUME_ADDENDUM_1.md. Consent-unavailable state is informational and non-blocking; confirmed denial or revocation remains blocking. No-preset without an exact lesson pin is NOT AVAILABLE pending an approved backend contract.
- Approved plan pin: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_7.md, 70,512 bytes / SHA-256 7979A7A990C36F159303F3B011D56626CCAA1AB998A6C7C9C7CB25F47ED024C9.
- Pre-append DECISIONS.md pin: 31,797 bytes / SHA-256 5FD6A07D52A29018D4FC841BBB59FE74329A88B0AC642B316D290A1B4C7A172E.
- Post-append DECISIONS.md pin: 33,745 bytes / SHA-256 B89A61951B304EE28AF41DBDF3348B57B9E54FB0E98638975B952205BBCF604F.
- Pre-append TASK_APPROVAL.md pin: 44,535 bytes / SHA-256 6A2D2C54414884752253A15E15BE288104829DC14AADDA27EB5EA44CFFEED2D4.
- Scope: D-016 records the consent and no-preset behavior plus the accepted typed-unavailable boundaries for personal-copy lineage and Parent-group invitation decline. Plan Revision 7, its file allowlist, pins, per-checkpoint ceilings and R1-R4 sequence remain unchanged. No absent route is treated as success.
- Test ceiling: pnpm run test from apps/ui-mobile, at most two coordinator-run invocations per checkpoint, one baseline and one post-implementation. Codex runs none.
- Typecheck ceiling: pnpm run typecheck from apps/ui-mobile, at most two coordinator-run invocations per checkpoint, one baseline and one post-implementation. Codex runs none.
- As in the plan, validate_harness, validate_repository_security and validate_architecture, plus git diff --check, each have a ceiling of two owner-run invocations per checkpoint, plus one owner emulator review. Codex runs none. No install, network, backend or Modal command is authorized.
- OWNER_MODAL_CALL_APPROVED=NO.

This clarification does not alter the checkpoint scope, allowlist, pins, ceilings or launch status. No post-append TASK_APPROVAL.md pin is recorded.

Addendum 15 - FEAT-081 Wave R owner clarification (R3/R4 backend-boundary rule, O1-O3)

- Status: Plan Revision 7 remains APPROVED; the owner clarification is recorded in D-017; no scope, allowlist, pin, ceiling or checkpoint sequence change.
- Authority: Direct owner clarification from Person 2 dated 2026-11-13 in tmp/fe081-waveR2/GOAL_RESUME_ADDENDUM_2.md. Missing backend operations and fields remain typed unavailable in the normal app; tests may use fakes only; no fake success is allowed. The owner’s O1 activity exception is an explicit deviation from SRS BR-15 and FR-P-05, not SRS conformance.
- Approved plan pin: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_7.md, 70,512 bytes / SHA-256 7979A7A990C36F159303F3B011D56626CCAA1AB998A6C7C9C7CB25F47ED024C9.
- Pre-append DECISIONS.md pin: 33,745 bytes / SHA-256 B89A61951B304EE28AF41DBDF3348B57B9E54FB0E98638975B952205BBCF604F.
- Post-append DECISIONS.md pin: 37,125 bytes / SHA-256 D08056B7F07E07AB4D5DE8861126338E66E532094745B81CE214F0F6235EE833.
- Pre-append TASK_APPROVAL.md pin: 46,767 bytes / SHA-256 B47A3B98DA89F24A8AE786747517E9BEEB0805E0B6EBA55E7D379F9010404AFC.
- Scope: D-017 records owner decisions O1-O3 and the typed-unavailable rule for routes and fields absent from the D-015 route table. R3 mismatch inference is unavailable; adult subject correction remains revision-bound; activity is informational and is not sent to story revision; story generation is not blocked by activity selection; only resume-active-run is offered. Plan Revision 7, its allowlist, pins, checkpoint sequence and backend route set remain unchanged. No fake success is shown.
- Test ceiling: pnpm run test from apps/ui-mobile, at most two coordinator-run invocations per checkpoint, one baseline and one post-implementation. Codex runs none.
- Typecheck ceiling: pnpm run typecheck from apps/ui-mobile, at most two coordinator-run invocations per checkpoint, one baseline and one post-implementation. Codex runs none.
- As in the plan, validate_harness, validate_repository_security and validate_architecture, plus git diff --check, each have a ceiling of two owner-run invocations per checkpoint, plus one owner emulator review. Codex runs none. No install, network, backend, provider or Modal command is authorized.
- OWNER_MODAL_CALL_APPROVED=NO.

This clarification does not alter the checkpoint scope, allowlist, pins, ceilings or launch status. No post-append TASK_APPROVAL.md pin is recorded.

Addendum 16 - FEAT-081 Wave R post-emulator correction PE1 (top bar background and double status-bar inset)

- Status: Plan Revision 7 remains APPROVED; the owner-requested PE1 correction is recorded in D-018; the existing plan allowlist, other file pins, and checkpoint sequence do not change.
- Authority: Direct owner task from Person 2 dated 2026-11-14 after emulator review of the Home screen top bar. The observed light-blue status-bar band and redundant cream inset are addressed only within the existing approved E/N scope.
- Approved plan pin: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_7.md, 70,512 bytes / SHA-256 7979A7A990C36F159303F3B011D56626CCAA1AB998A6C7C9C7CB25F47ED024C9.
- Pre-append DECISIONS.md pin: 37,125 bytes / SHA-256 D08056B7F07E07AB4D5DE8861126338E66E532094745B81CE214F0F6235EE833.
- Post-append DECISIONS.md pin: 39,150 bytes / SHA-256 A0CA10FDA558EF8024028E17507CCD1C87947F122E6E1C3045C05AAE52C7498D.
- Pre-append TASK_APPROVAL.md pin: 49,234 bytes / SHA-256 5B52EA77CF22525D59F3AD175F99A3DD30FF0CD2476C04C9DD2A767DB931923E.
- Scope: PE1 is limited to apps/ui-mobile/src/parent/presentation/components/ui.tsx, apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx, and apps/ui-mobile/tests/parentSrsBehavior.test.ts, all existing Plan Revision 7 E/N paths, plus the R0 evidence report and tmp/fe081-waveR2/run_state/RUN_STATE.md. Android native files, app.json, package files, and every H row remain untouched. The plan, allowlist, pins of other files, and checkpoint sequence do not change.
- Test ceiling: ONE additional coordinator pnpm run test run for PE1. Codex runs none.
- Typecheck ceiling: ONE additional coordinator pnpm run typecheck run for PE1. Codex runs none.
- Validator ceiling: ONE additional owner run of validate_harness, validate_repository_security, validate_architecture, and git diff --check for PE1. Codex runs none.
- Emulator review: ONE owner re-check, limited to the top bar area and the Home, Lessons, Start, and Profiles tabs. Codex runs no emulator command or review.
- OWNER_MODAL_CALL_APPROVED=NO.

This correction does not change the checkpoint sequence. No post-append TASK_APPROVAL.md pin is recorded.

Addendum 17 - FEAT-081 Wave R post-emulator correction PE2 (age-band absence is non-blocking)

- Status: Plan Revision 7 remains APPROVED; the owner-requested PE2 correction is recorded in D-019; the existing plan allowlist, other file pins, and checkpoint sequence do not change.
- Authority: Direct owner task from Person 2 dated 2026-11-14 after emulator review. PE2 follows PE1 and is completed before the shared coordinator post-run set.
- Approved plan pin: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_7.md, 70,512 bytes / SHA-256 7979A7A990C36F159303F3B011D56626CCAA1AB998A6C7C9C7CB25F47ED024C9.
- Pre-append DECISIONS.md pin: 39,150 bytes / SHA-256 A0CA10FDA558EF8024028E17507CCD1C87947F122E6E1C3045C05AAE52C7498D.
- Post-append DECISIONS.md pin: 41,836 bytes / SHA-256 73915C90B13A5A53B1A44D66B078EA041D0C0307070333466F959EE9DAC7E1E1.
- Pre-append TASK_APPROVAL.md pin: 51,425 bytes / SHA-256 4FD887AD73C71B8A632078B8F581A37367A53C137AB7077FC1516BA45EB1F641.
- Scope: PE2 is limited to apps/ui-mobile/src/parent/presentation/navigation/workflowTypes.ts, apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts, apps/ui-mobile/src/parent/presentation/screens/ProfileScreen.tsx, apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx only if needed, apps/ui-mobile/tests/parentFlowV1.test.ts, and apps/ui-mobile/tests/parentSrsBehavior.test.ts, all existing Plan Revision 7 E/N paths, plus the R1 evidence report and tmp/fe081-waveR2/run_state/RUN_STATE.md. No H row, native file, package file, plan, or allowlist is changed.
- Test ceiling: ONE additional coordinator pnpm run test run, shared by PE1 and PE2. Codex runs none.
- Typecheck ceiling: ONE additional coordinator pnpm run typecheck run, shared by PE1 and PE2. Codex runs none.
- Validator ceiling: ONE additional owner run of validate_harness, validate_repository_security, validate_architecture, and git diff --check, shared by PE1 and PE2. Codex runs none.
- Emulator review: ONE owner re-check, covering the PE1 top bar area and Home, Lessons, Start, and Profiles tabs, now including the profile card and Start flow. Codex runs no emulator command or review.
- OWNER_MODAL_CALL_APPROVED=NO.

PE2 adds no command runs and does not change the checkpoint sequence. No post-append TASK_APPROVAL.md pin is recorded.

Addendum 18 - FEAT-081 Wave L plan approval and merged L0-L3 launch authorization (not launched)

- Status: Plan Revision 8 APPROVED; Wave L NOT LAUNCHED. This authorizes one merged L0-L3 goal, which begins only when the owner sends its goal text.
- Authority: Direct owner approval from Person 2 dated 2026-11-14; owner answers and the merged execution model are recorded in D-020. For Wave L, unsigned Rev67 is the canonical working SRS and Rev60 is historical; FEAT-063 D-203 is being written on the backend line.
- Approved plan pin: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_8.md, 46,506 bytes / SHA-256 8CC56B627FF08B80FBCEC5D8ED71ABEC85E2A1FF33CC7FD494287ACBD0EBBCBD.
- Screen map appendix pin: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_8_SCREEN_MAP.md, 21,220 bytes / SHA-256 99A5E04F292B5D2995E50059AE2587759ABACC98FFE0E68669E99B0F318985A5.
- Pre-append features/FEAT-081-parent-ui-mobile-port/DECISIONS.md pin: 41,836 bytes / SHA-256 73915C90B13A5A53B1A44D66B078EA041D0C0307070333466F959EE9DAC7E1E1.
- Post-append features/FEAT-081-parent-ui-mobile-port/DECISIONS.md pin: 47,830 bytes / SHA-256 178523EC18BE254610F7905A9431A03D7F844C4470DA2580857825FC3546EBC4.
- Pre-append features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md pin: 53,749 bytes / SHA-256 F764C3FFF7BABECE29CE087300124CC73A3814DBB7B5B8694F0E783CDC88635C.
- Scope: The merged goal may edit only the L0-L3 E rows and the conditional apps/ui-mobile/src/parent/presentation/ParentVisualPreviewHarness.tsx N row in the approved Plan Revision 8 manifest, checkpoint by checkpoint. It may append checkpoint sections only to features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVEL_20261114.md, maintain tmp/fe081-waveL/run_state/WAVEL_RUN_STATE.md, and create snapshots under tmp/fe081-waveL/snapshots/. All R and H rows, package files, Plan Revision 7, existing Wave R records/reports, and owner-local CONTEXT.md and status/STATUS.md stay untouched. The seven visible-copy edits are exactly those in Plan Revision 8 section 4.2.
- Test ceiling: At most two coordinator pnpm run test runs total for the merged goal: one after L3 and one correction run. Codex runs none. The completed Wave R verification set is used and is not a Wave L baseline run.
- Typecheck ceiling: At most two coordinator pnpm run typecheck runs total for the merged goal: one after L3 and one correction run. Codex runs none.
- Validator ceiling: At most two owner runs each of validate_harness, validate_repository_security, validate_architecture, and git diff --check. Codex runs none.
- Emulator review: At most two owner emulator reviews total for the merged goal. Codex runs no emulator command or review.
- Baseline commit: 8f1fef7dafa5c374b2cc2e80562b6a0a78d75288.
- OWNER_MODAL_CALL_APPROVED=NO.

The goal runs L0, L1, L2, and L3 sequentially without a pause. The owner may interrupt with stop-and-save. Plan approval and this addendum do not launch the goal; the goal starts only when the owner sends the goal text. No post-append features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md pin is recorded.

Addendum 19 - FEAT-081 Wave L allowlist amendment (L3 E row, copy edit 7 only)

- Status: Plan Revision 8 APPROVED; L3 scope amendment only. This resolves the existing merged goal's L3 allowlist conflict and authorizes no work beyond that goal.
- Authority: Direct owner decision from Person 2 dated 2026-11-14, recorded as D-021. Plan Revision 8, D-020, and Addendum 18 are not edited.
- Approved plan pin: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_8.md, 46,506 bytes / SHA-256 8CC56B627FF08B80FBCEC5D8ED71ABEC85E2A1FF33CC7FD494287ACBD0EBBCBD.
- Screen map appendix pin: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_8_SCREEN_MAP.md, 21,220 bytes / SHA-256 99A5E04F292B5D2995E50059AE2587759ABACC98FFE0E68669E99B0F318985A5.
- Pre-append features/FEAT-081-parent-ui-mobile-port/DECISIONS.md pin: 47,830 bytes / SHA-256 178523EC18BE254610F7905A9431A03D7F844C4470DA2580857825FC3546EBC4.
- Post-append features/FEAT-081-parent-ui-mobile-port/DECISIONS.md pin: 49,312 bytes / SHA-256 827684531C21CFF606A891194363E0419ADD01AE3B12FD4AE7CAF61BCFD8630B.
- Pre-append features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md pin: 56,885 bytes / SHA-256 83C8823C38C7263FE6BFFC57E9C1E5FAC65529DBF68D2997B8C78AD1CCE8C627.
- Scope: Add apps/ui-mobile/src/parent/presentation/screens/TranscriptReviewScreen.tsx to L3 E using its accepted L2 after-pin, 2,854 bytes / SHA-256 4F2380190A9CD6B0F4D815A4FBB7102F39613E2D53AF1A107DCB352299D67DFB. Its sole L3 change is copy edit 7, “Whisper · tiếng Việt” to “Bản ghi lời nói · tiếng Việt”; preserve the existing L2 restyle and every other byte. Keep all previously approved L3 E paths, R/H rows, route order, and behavior unchanged. No other plan or allowlist change is authorized.
- Test ceiling: At most two coordinator pnpm run test runs total for the merged goal: one after L3 and one correction run. Codex runs none. The completed Wave R verification set is used and is not a Wave L baseline run.
- Typecheck ceiling: At most two coordinator pnpm run typecheck runs total: one after L3 and one correction run. Codex runs none.
- Validator ceiling: At most two owner runs each of validate_harness, validate_repository_security, validate_architecture, and git diff --check. Codex runs none.
- Emulator review: At most two owner emulator reviews total for the merged goal. Codex runs no emulator command or review.
- Baseline commit: 8f1fef7dafa5c374b2cc2e80562b6a0a78d75288.
- OWNER_MODAL_CALL_APPROVED=NO.

This amendment does not change the seven approved copy edits or Addendum 18 command/emulator ceilings. It approves no additional command, test, typecheck, validator, diff-check, emulator review, checkpoint, or Modal call. The resumed merged goal continues at L3 under the amended file scope. No post-append features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md pin is recorded.

Addendum 20 - FEAT-081 Wave M plan approval and launch (Plan Revision 9)

- Status: Plan Revision 9 APPROVED; launched by the owner's goal text of 2026-11-14
- Authority: direct owner instruction in the goal text; plan review delegated to the executing session and recorded in the record file
- Approved plan pin: `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_9.md`, 77,730 bytes / SHA-256 `74986A371929A724C8713257407BC0EBEF38CCAF117F2C157343FED276D63859`.
- Concept specification pin: `tmp/fe081-waveM/WAVEM_CONCEPT_SPEC.md`, 56,693 bytes / SHA-256 `31265CCBB7EC06172A1387BA992386F90204FFC69FEA6EACAFAA045467BA451A`; `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_9_CONCEPT_SPEC.md` is byte-identical.
- Pre-append `features/FEAT-081-parent-ui-mobile-port/DECISIONS.md` pin: 49,312 bytes / SHA-256 `827684531C21CFF606A891194363E0419ADD01AE3B12FD4AE7CAF61BCFD8630B`.
- Post-append `features/FEAT-081-parent-ui-mobile-port/DECISIONS.md` pin: 51,809 bytes / SHA-256 `774CAE834E76C6F2CEDCA1496A40D5BBED3BE597DB6A7207E0612839111BE7DF`.
- Pre-append `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md` pin: 59,779 bytes / SHA-256 `AC9823ECA60A202EC21FC88FFAAF39A8116EADE9E3996A2CD6A164081C0EB3E0`.
- Post-append `TASK_APPROVAL.md` full-file pin: recorded after append in `tmp/fe081-waveM/records/WAVEM_PHASE_A_RECORD.md`. This append-only file cannot embed its own final SHA-256 without changing that digest.
- Scope: only the E rows in Plan Revision 9 §§7.2-7.5 may change in their named checkpoint; the plan has no N rows. R/H rows remain frozen. The only non-H test allowed to change is `apps/ui-mobile/tests/parentSrsBehavior.test.ts`, and only affected presentation assertions may be revised. M0, M1, M2, M3 run sequentially.
- Ceilings: coordinator at most three `pnpm run test` and three `pnpm run typecheck` runs total for Wave M. Owner at most three runs each of `validate_harness`, `validate_repository_security`, `validate_architecture`, and `git diff --check`, and at most three emulator reviews. Codex runs none. A Modal call is not approved.
- Baseline commit: `a0b382f8c21de0dc66f23c5aa752a3a67388a093` plus the accepted uncommitted Wave L working state.
- The unsigned Rev67 task pin and its conflict with the repository-wide Rev60 authority register are reported for coordinator resolution. Existing D-017 O1 is preserved as a deviation from Rev67, not described as SRS conformance.
- OWNER_MODAL_CALL_APPROVED=NO.

This approval launches the owner-directed M0-M3 run only within the scope, frozen-flow rules, ceilings, records, snapshots, and stop conditions above and in the Wave M instructions. No stage, commit, or push is authorized.
Addendum 21 - FEAT-081 Wave M M3 Capture preview harness scope amendment (Plan Revision 9)

- Status: M3 scope amendment approved; continuation authorized by the owner's message of 2026-11-14
- Authority: direct owner instruction in the current goal conversation on 2026-11-14, approving the addition of ParentVisualPreviewHarness.tsx to the M3 allowlist only to add deterministic Capture previews for permission-denied and selected-photo states
- Plan before amendment: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_9.md, 77,730 bytes / SHA-256 74986A371929A724C8713257407BC0EBEF38CCAF117F2C157343FED276D63859
- Amended Plan Revision 9: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_9.md, 78,915 bytes / SHA-256 F117FA0428E3768DD94A34824F55E58BA41483073FE9AE82A4BD2CE76EF819CC
- M3 incoming harness pin: apps/ui-mobile/src/parent/presentation/ParentVisualPreviewHarness.tsx, 20,075 bytes / SHA-256 0E56EABCC599FEECB498BD9C51737E0BB3ECD417E034863F053FC7605F9B995C, equal to the recorded M0 after/snapshot pin
- TASK_APPROVAL.md pre-append pin: 62,478 bytes / SHA-256 71F34469F3F1F4259D49B583A0B569117115EB04EE755A7D0B13548784291138
- TASK_APPROVAL.md post-append full-file pin: recorded after the append in tmp/fe081-waveM/records/WAVEM_M3_SCOPE_AMENDMENT_RECORD.md; this file does not contain a self-referential digest
- Scope: add ParentVisualPreviewHarness.tsx as an M3 E row in Plan Revision 9 §7.5, using its M0 after-pin as the M3 incoming pin. The harness may add selectable empty, camera-permission-denied, and selected-photo Capture previews using deterministic harness-only composition and code-drawn simulated artwork. Capture preview controls are inert and the preview invokes no ImagePicker, controller, application API, or network. The existing already-allowlisted parentSrsBehavior.test.ts may receive only source assertions for these preview states and their inert behavior. No production CaptureScreen, flow, route, controller, payload, other source file, package, font, or image asset is authorized by this amendment. Stop if additional source outside this scope is required.
- Production product flow, step order, transitions, callbacks, and navigation remain unchanged. M0-M2 status and evidence are unchanged.
- Existing Addendum 20 ceilings and all no-test/no-validator/no-diff-check/no-install/no-network/no-backend/no-Android/no-emulator/no-Modal/no-stage/no-commit/no-push restrictions remain in force. OWNER_MODAL_CALL_APPROVED=NO.
- Baseline remains a0b382f8c21de0dc66f23c5aa752a3a67388a093 plus the accepted uncommitted Wave L working tree.
Addendum 22 - FEAT-081 Wave M M3 scope-amendment plan-pin correction

- Status: Documentation correction to Addendum 21; the previously approved M3 scope is unchanged
- Authority: direct owner approval of the M3 ParentVisualPreviewHarness.tsx scope amendment on 2026-11-14. This addendum corrects manifest pin presentation before any harness edit and does not expand the approved source scope.
- Plan pin previously recorded by Addendum 21: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_9.md, 78,915 bytes / SHA-256 F117FA0428E3768DD94A34824F55E58BA41483073FE9AE82A4BD2CE76EF819CC
- Corrected amended plan pin: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_9.md, 79,202 bytes / SHA-256 FDA7CE1620BA7B354F492430C52CC446599E6D694F446EB37760F4B174E0ED42
- Correction: §7.5 continues to list Wave M launch pins and separately records the M3 incoming pins for earlier-edited files. ParentVisualPreviewHarness.tsx launch pin is 11,033 bytes / SHA-256 5FE38D9D768715FD8DFC2AEBD53BA65385DCE034075463A36E1FC7D4ACE01DB6; M3 incoming is its M0 after/snapshot pin, 20,075 bytes / SHA-256 0E56EABCC599FEECB498BD9C51737E0BB3ECD417E034863F053FC7605F9B995C. parentSrsBehavior.test.ts launch pin is 41,464 bytes / SHA-256 BB91D5746913B4F84F35C350B3410C02AA71CB92D6AC209352F76CA95E12C3A3; M3 incoming is its M2 after/snapshot pin, 51,352 bytes / SHA-256 9D3A636D3C237BF1C552FE60C63CA3376499C889B7D6665689BA3B59E063C3DE.
- The ParentVisualPreviewHarness.tsx scope remains limited to deterministic, inert Capture empty/permission-denied/selected-photo previews. No production file or behavior is authorized by this correction.
- TASK_APPROVAL.md pre-append pin: 65,074 bytes / SHA-256 8A503572559F6997177BFBABBE2B4F210D016BC1CD1A281DF56E6A3D3D78556D
- TASK_APPROVAL.md post-append full-file pin: recorded after append in tmp/fe081-waveM/records/WAVEM_M3_SCOPE_AMENDMENT_RECORD.md; no self-referential digest is included
- Existing Addendum 20 ceilings and restrictions remain unchanged. OWNER_MODAL_CALL_APPROVED=NO.

Addendum 23 - FEAT-081 bounded post-run remediation after Wave M

- Status: bounded remediation approved by the owner's direct instruction dated 2026-11-14; Wave M completion remains recorded and this addendum authorizes only the listed corrections.
- Authority: direct owner instruction in the current conversation. The coordinator-supplied logs report 89/91 tests passed with two assertion failures in apps/ui-mobile/tests/parentSrsBehavior.test.ts and three typecheck errors in components/ui.tsx, HomeScreen.tsx, and ProfileSharingScreen.tsx.
- Plan Revision 9 before remediation amendment: 79,202 bytes / SHA-256 FDA7CE1620BA7B354F492430C52CC446599E6D694F446EB37760F4B174E0ED42.
- Approved amended Plan Revision 9: 83,152 bytes / SHA-256 47C55BE1AEE330F3C6F39DCF1F7EFDDF7398AF4EEBF3200467EEC6CD6FFCC599.
- TASK_APPROVAL.md before this append: 67,098 bytes / SHA-256 3335F5A4209E3E33D8A6BFD89D7915019F5E53A3C1D7BA7ADF785E59D7F5325C.
- Source/test incoming and planned post-edit pins:
  - apps/ui-mobile/src/parent/presentation/components/ui.tsx: before 23,872 / 2C5637C50D71BE4779E27862C35DF7FF24EF4A71DE4DE9311109BE221D6036C9; planned after 23,875 / 0BB724D1934F0A96F694F67AE5B5AFE8833DCCAF131C560BD486B49F62D07D61.
  - apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx: before 6,960 / 58D88EB3B4E4A8A9AD55296036A080C01950D315F1F7202DB406DAD1B7B84E9A; planned after 6,963 / A502E72387370A9EDEAE5A836941D64B05F777E81D65DFDBE33C16113C8454A4.
  - apps/ui-mobile/src/parent/presentation/screens/ProfileSharingScreen.tsx: before 6,219 / AE1CAE845858E8D87B69DA3D19B3BB02F1CDF349AD3290D5D1E0E714CA089BDD; planned after 6,175 / 14691E21B24D2819742602221481A511DA6A40E290D39E1DFACFBF129FD17511.
  - apps/ui-mobile/src/parent/presentation/screens/CaptureScreen.tsx: before 7,755 / D61FBF7F3F24115CEED8F6971A4A58309242C2B38F61B102803EAAF2D7637664; planned after 7,735 / F53CF3C8E5FD67AFA9817F4D0B94CA8CF2F4251AB8E7743D16556B10E34852F7.
  - apps/ui-mobile/tests/parentSrsBehavior.test.ts: before 55,558 / B912CE440C9873F34F1C06D58F63D78AC14D6C3048352AEAB520259A667BD064; planned after 55,568 / 96ABB2469BA65A14FE0A0F6076C8F821A72A20649B7AC4813C1F909111FB0DB8.
- Authorized scope: only the five source/test paths above. In ui.tsx and HomeScreen.tsx replace palette.line with the existing palette.outline at the two reported errors. In CaptureScreen.tsx and its matching test assertion, use the exact Plan Revision 9 required-photo sentence. In parentSrsBehavior.test.ts, assert both bottom-bar minWidth 0 and minHeight 52. In ProfileSharingScreen.tsx remove only the redundant unavailable-state check from the submit button disabled expression inside its available-only branch. Preserve all existing handlers, disabled behavior, photo gates, and product flow.
- No controller, domain, route, payload, step order, product flow, H/R file, package, asset, additional source path, or product decision is authorized. Do not edit DECISIONS.md. Stop if another source file is needed.
- Verification limits: Codex reads all five final files, checks the exact source/assertion correspondence with read-only search, records before/after pins, and updates report, snapshots/evidence, and run state. Codex runs no test, typecheck, validator, diff-check, install, network, backend, Android, emulator, or Modal command; no stage, commit, or push.
- The owner-supplied test and typecheck logs each count as a consumed run. Addendum 20's total ceiling of three coordinator runs per command remains unchanged and counters are not reset. Any coordinator rerun must fit the remaining cumulative count.
- OWNER_MODAL_CALL_APPROVED=NO.

Addendum 24 - FEAT-081 post-run exact-copy assertion pin clarification

- Status: documentation and expected-pin clarification to Addendum 23; the approved five-path remediation scope is unchanged.
- Authority: the owner's direct post-run remediation instruction dated 2026-11-14 requires the Capture assertion and production copy to match the complete Plan Revision 9 sentence. Static review found that the existing preview source-order assertion checked only the sentence prefix. This clarification makes the same already-authorized correction measurable; it adds no source path and changes no production behavior.
- Plan Revision 9 before this clarification: 83,152 bytes / SHA-256 47C55BE1AEE330F3C6F39DCF1F7EFDDF7398AF4EEBF3200467EEC6CD6FFCC599.
- Clarified Plan Revision 9: 84,346 bytes / SHA-256 974A3267FA66C54D17278EAB03EA40F853ED3A750CBEB58FF1C91FE093624B97.
- TASK_APPROVAL.md before this append: 70,717 bytes / SHA-256 126E443A88E485A97BF3CD7AB3F81D35279AF18FE2C0181E44E59070083BDB62.
- Authorized follow-up path and pins: apps/ui-mobile/tests/parentSrsBehavior.test.ts incoming 55,568 bytes / SHA-256 96ABB2469BA65A14FE0A0F6076C8F821A72A20649B7AC4813C1F909111FB0DB8; expected after 55,756 bytes / SHA-256 08D1C0BF4AC260E5E4FD26602A92E66CCDE2ECC387F29A36FE33AA0B4778A7D2.
- Correction: assert the entire required-photo sentence in production CaptureScreen source and locate the entire same sentence in the harness preview source-order assertion. The sentence is: Chỉ tiếp tục sau khi có một ảnh tranh hợp lệ. Chưa mở buổi học trước ảnh.
- The only permitted source/test paths remain the exact five in Addendum 23. No handler, controller, domain, route, payload, step order, product flow, H/R file, package, asset, or other source path is authorized. Do not edit DECISIONS.md.
- Verification limits, consumed-run accounting, Addendum 20 ceilings, and all no-test/no-typecheck/no-validator/no-diff-check/no-install/no-network/no-backend/no-Android/no-emulator/no-Modal/no-stage/no-commit/no-push restrictions remain unchanged. OWNER_MODAL_CALL_APPROVED=NO.

Addendum 25 - FEAT-081 Family tab and Home resume placement

- Status: APPROVED and launched by the owner's direct instruction to apply the supplied mobile screenshots and the owner's reply authorizing Plan Revision 10 and this addendum, dated 2026-11-15.
- Approved plan pin: `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_10.md`, 4,749 bytes / SHA-256 `E43CCDBD0B9962735FAA10017B76C409A4F6B42A4BEBA419A5727CB9582A0A41`.
- TASK_APPROVAL.md pre-append pin: 72,812 bytes / SHA-256 `AF5B092841F0A648F38E8FF3A447D29267D39206EFD73DEB71A99812F299DC5C`.
- Authorized implementation paths are exactly the four presentation files and the existing assertion file listed below, plus this plan and approval record. Incoming pins are recorded in Plan Revision 10.
- Scope: rename the fourth tab's visible label to `Gia đình` while retaining its internal tab ID and callback; move the entire existing family-space menu and sign-out from Home into the existing profile tab content; retain child profile list, selection, consent/data status, pending-deletion handling, and existing create/edit/delete actions; remove the active-run resume warning/button from the family/profile screen while keeping the existing resume card and callback on Home; route family management child screens back to and visually select the family tab; update only the existing source assertion block to match the new placement.
- No new test case, asset, dependency, route, API, backend, controller, domain, payload, run state, or product behavior is authorized. Preserve all existing family menu handlers and guards. Do not edit `CONTEXT.md` or `DECISIONS.md`, which remain protected by the owner's earlier instruction.
- Verification: static source review only. No tests, typecheck, validators, diff-check, installs, network, backend, Android/emulator, or Modal commands. No staging, commit, or push.
- This addendum supersedes only the prior presentation placement constraints for the fourth tab, Home family-space menu, profile-screen resume CTA, and related existing source assertions. All other FEAT-081 and Wave M constraints remain unchanged. OWNER_MODAL_CALL_APPROVED=NO.

Addendum 26 - FEAT-081 unselected-profile family actions and offline preview

- Status: APPROVED and launched by the owner's direct instruction dated 2026-11-15 to fix the no-profile family-menu behavior and apply the state in the API-disconnected preview.
- Approved plan pin: `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_11.md`, 3,781 bytes / SHA-256 `DCC23BC60EFC8872A77C4E57DBF3DEACD73693060FAFAE86A6C1DB58929391DB`.
- TASK_APPROVAL.md pre-append pin: 74,970 bytes / SHA-256 `F7FF23F4B80FED201E1C57D5DE5BCB604526F920BDD0AB8419BEA063ED197C5B`.
- Authorized paths and incoming pins:
  - `apps/ui-mobile/src/parent/presentation/screens/ProfileScreen.tsx`: 10,748 bytes / SHA-256 `1563E0F020E59C0C795F22D1195565D726C6C0801E5E5A0DFEF75834BC7BA610`.
  - `apps/ui-mobile/src/parent/presentation/ParentVisualPreviewHarness.tsx`: 24,232 bytes / SHA-256 `FA0A77FEDF790EE349B9D6AB42D95C9C938867AC75EB904D01210C9F85DAD481`.
  - `apps/ui-mobile/tests/parentSrsBehavior.test.ts`: 56,685 bytes / SHA-256 `36EA2F9723BD674809A1718DF5148C0A6CE03C0B69D4A793ABB1F23CF97B456A`.
  - `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_11.md` and this approval record.
- Scope: when no profile is selected, visibly disable the Family hub's sharing and delivered-lesson rows and explain that profile selection is required; retain their callbacks when a profile is selected. Keep Home's existing active-run resume action independent of selected profile. Extend the offline visual harness with deterministic Home open-run/no-selection, Home new-run, and Family unselected-profile previews; keep all preview actions inert and make no API/network/controller calls. Rename the preview tab to `Gia đình` and update only the existing source assertion block; add no test case.
- No cancellation API, backend, route, controller, domain, payload, product-flow, asset, or dependency change is authorized. The user's planned API cancellation work remains separate. Do not edit `CONTEXT.md` or `DECISIONS.md` under the owner's earlier instruction.
- Verification: static source review only. No tests, typecheck, validators, diff-check, install, network, backend, Android/emulator, or Modal commands. No staging, commit, or push.
- This addendum extends Addendum 25 only for the three listed source/test paths. All other FEAT-081 and Wave M constraints remain unchanged. OWNER_MODAL_CALL_APPROVED=NO.

Addendum 27 - FEAT-081 Home no-selection card copy alignment

- Status: APPROVED and launched by the owner's direct 2026-11-15 instruction to fix visible issues found in the supplied Home screenshot and keep the disconnected preview aligned.
- Approved plan pin: `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_12.md`, 2,925 bytes / SHA-256 `1E1E636E98A60059EE32ECBCB99A4F4B56EDFEED3D3EB05EC4183F3B9FFD3F23`.
- TASK_APPROVAL.md pre-append pin: 77,363 bytes / SHA-256 `48EF1B2B2632A9F0B890F2A49B17FF65261E016DA6CF7FE41FA68416D1483677`.
- Authorized paths and incoming pins:
  - `apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx`: 5,971 bytes / SHA-256 `0986358D257FC55438412A9DC721A945A31F04E8F492F8A27666463E3DBC958D`.
  - `apps/ui-mobile/tests/parentSrsBehavior.test.ts`: 57,374 bytes / SHA-256 `725595B2AAB2ED545868F41E5A6A6BC42A5738E571CAB44025D3B7C2B00D6825`.
  - `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_12.md` and this approval record.
- Scope: remove only the redundant profile-count/creation sentence from the Home selected-profile card when no profile is selected. Retain the no-selection message, management action, active-run UI, and existing callbacks. The connected app and offline preview share `HomeScreen`; no harness edit is needed. Update only the existing source assertion; add no test case.
- No API, controller, route, backend, domain, payload, cancellation, product-flow, asset, or dependency change is authorized. Do not edit `CONTEXT.md` or `DECISIONS.md` under the owner's earlier instruction.
- Verification: static source review only. No tests, typecheck, validators, diff-check, install, network, backend, Android/emulator, or Modal commands. No staging, commit, or push.
- This addendum extends Addendum 26 only for the two listed source/test paths. All other FEAT-081 and Wave M constraints remain unchanged. OWNER_MODAL_CALL_APPROVED=NO.

Addendum 28 - FEAT-081 Parent mobile logo and Expo app icon

- Status: APPROVED and launched by the owner's direct 2026-11-15 request to replace the mobile and app logo with the supplied image. That direct request is also the visual approval for this exact image.
- Approved plan pin: `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_13.md`, 3,837 bytes / SHA-256 `7D116DA9C37F058D5AD77273D943849E717D75A7E49F673B7077295E0C9907C6`.
- TASK_APPROVAL.md pre-append pin: 79,277 bytes / SHA-256 `88BCDB7A09A0F7635ED1ACC0F751BA8C28240B47539C305B87EE31DFD5A64688`.
- Authorized source inputs:
  - `apps/ui-mobile/src/parent/presentation/components/ui.tsx`: 23,875 bytes / SHA-256 `0BB724D1934F0A96F694F67AE5B5AFE8833DCCAF131C560BD486B49F62D07D61`.
  - `apps/ui-mobile/app.json`: 1,560 bytes / SHA-256 `9489E92A02306F6F0C1F575F3FF1C1FB9331BCB58ED2FD52E49880781F2D0651`.
  - `apps/ui-mobile/tests/parentSrsBehavior.test.ts`: 57,711 bytes / SHA-256 `FB8BB036EEC5EEE72256030D120103EDDF5DB44CD9F22B6334A77460E620DE91`.
  - Owner attachment `codex-clipboard-c198b23f-1b29-42d6-8f85-d450e80ca81e.png`: 1,191,659 bytes / SHA-256 `E5910593FDD6AAF42B38A208A2B32A1F94B769670A37BC9BCA553E976822399A`.
- Authorized additions: `features/FEAT-081-parent-ui-mobile-port/assets/generated/sketch2life-logo.png`, `assets/sketch2life-logo.asset.json`, `assets/REVIEW.md`, `assets/approved/sketch2life-logo.png`, and `apps/ui-mobile/assets/applied/sketch2life-logo.png`.
- Scope: copy the owner-provided 1254×1254 transparent PNG unchanged through the generated and approved asset records; record provenance and the direct owner visual approval; reference the applied copy from the active Parent `ScreenFrame`, Expo `icon`, and web `favicon`. Retain existing splash artwork and legacy demo screens. Update only the existing source assertion; add no test case.
- Do not edit `CONTEXT.md` or `DECISIONS.md`. No API, backend, route, domain, product-flow, dependency, or app behavior change is authorized. Do not run tests, typecheck, validators, install, network, backend, Android build/prebuild, emulator, or Modal commands. Do not stage, commit, or push.
- Existing generated native Android launcher images and the installed app are not rebuilt in this task; Expo configuration points future native icon generation at the new applied asset. OWNER_MODAL_CALL_APPROVED=NO.

Addendum 29 - FEAT-081 sync generated Android launcher images

- Status: APPROVED under the owner's direct 2026-11-15 request to replace the app logo; this addendum authorizes only synchronizing the generated Android launcher images to the already approved Expo icon asset.
- Approved plan pin: `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_14.md`, 3,580 bytes / SHA-256 `ABAA3C999E4EB733C93405FBA96975EB90D5DB16FC5855FEEC565151368464A2`.
- TASK_APPROVAL.md pre-append pin: 81,632 bytes / SHA-256 `A87D1AD9CF3CA2CC9B0753C4FC25DC7AFE0B38CD764C64AE1C126B048FBC946B`.
- Scope: run only the local Expo Android prebuild with `--no-install` using the approved applied logo, updating the ten pinned `ic_launcher.webp` and `ic_launcher_foreground.webp` resources listed in Plan Revision 14. Stop if unrelated native files change. No APK build, package installation, emulator, tests, typecheck, validator, diff-check, network, backend, or Modal command. No staging, commit, or push.
- This addendum supersedes only Plan Revision 13's prohibition on Android prebuild for these ten launcher resources. All other FEAT-081 and Wave M constraints remain unchanged. OWNER_MODAL_CALL_APPROVED=NO.

Addendum 30 - FEAT-081 center Start action, Activity destination, and publication

- Status: APPROVED and launched by the owner's direct 2026-11-15 instruction to make Start a large center action, replace its existing tab with a useful destination, check the completed changes, consolidate the current worktree changes into one commit, and push the branch including its two already-unpushed commits.
- Approved plan pin: `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_15.md`, 3,381 bytes / SHA-256 `ACBBC9D52430534E4F6677DD7CEA818906D3DCEF0583A6981549BDED1F7415F7`.
- TASK_APPROVAL.md pre-append pin: 82,828 bytes / SHA-256 `CD50940ACE8560F8C355AA1BB9BDB324DBA0A18C14A37714B718F456308401FC`.
- Authorized implementation paths: `apps/ui-mobile/src/parent/presentation/screens/ParentBottomBar.tsx`, `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx`, the existing assertion block in `apps/ui-mobile/tests/parentSrsBehavior.test.ts`, this plan, and this approval record. Incoming pins are in Plan Revision 15.
- Scope: four tab destinations (`Trang chủ`, `Bài giảng`, `Hoạt động`, `Gia đình`) plus a raised center Start action. Route `Hoạt động` to existing `StoryHistoryScreen`. Keep the center action on the current resume/continue/profile path and show `Tiếp tục` for an open run. Keep history return paths accurate.
- Verification authorized: `pnpm run test`, `pnpm run typecheck`, `python tools/validate_harness.py`, `python tools/validate_repository_security.py`, `python tools/validate_architecture.py`, and `git diff --check`; do not run backend, install, network, Android build/prebuild, emulator, or Modal commands as part of this addendum.
- Commit/push: stage only reviewed FEAT-081 task files by explicit path. Create one new commit containing the current intended FEAT-081 worktree changes, preserving the current content of `CONTEXT.md` and `DECISIONS.md` without editing it. Do not rewrite or squash the two existing unpushed commits. Push `feature/fe-mobile-remediation` to `origin`; one branch push will publish the new commit and both existing unpushed commits.
- No cancellation API, backend, domain, route contract, or API payload change is authorized. OWNER_MODAL_CALL_APPROVED=NO.

Addendum 31 - FEAT-081 offline preview integration for center Start action

- Status: APPROVED under the owner's direct 2026-11-15 request for the center Start action; the existing visual preview call site must receive the new inert props.
- Approved plan pin: `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_16.md`, 1,728 bytes / SHA-256 `14F168A6CA568472CE8AEF05ACD22809998A0503EBD93ADEAE2139173F5053DF`.
- TASK_APPROVAL.md pre-append pin: 85,072 bytes / SHA-256 `0926F44F8CA483FA486DB91AA4E2A597C5F94C0618913DD3709FCB68481F2D9B`.
- Authorized paths: `apps/ui-mobile/src/parent/presentation/ParentVisualPreviewHarness.tsx`, the existing `bottom-bar` source assertion in `apps/ui-mobile/tests/parentSrsBehavior.test.ts`, this plan, and this approval record.
- Scope: pass `ignoreAction` and the `Bắt đầu` label to the preview's `ParentBottomBar`; assert the new call shape in the existing source assertion block. No new test case or behavior change.
- Verification and commit/push limits remain exactly as authorized in Addendum 30. OWNER_MODAL_CALL_APPROVED=NO.

Addendum 32 - FEAT-081 Parent UI alignment to owner-supplied SRS Rev67

- Status: APPROVED and launched under the owner's direct 2026-11-15 instruction to use the supplied SRS file, recheck the Parent UI, and correct FE mismatches where possible.
- SRS input pin: owner-supplied `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 634,291 bytes / SHA-256 `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996`.
- Approved plan: `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_17.md`, 5,277 bytes / SHA-256 `1E166E3D6DE16F5D784626C03715E59F1C4B0281150755EF91F5446632B523D2`.
- TASK_APPROVAL.md pre-append pin: 86,154 bytes / SHA-256 `6E3AC7929D2EC3BA9641488695C3F8AB983158D2C36717F701A72F83C67ED694`.
- Authorized paths: `workflowTypes.ts`, `ActivityScreen.tsx`, `StoryScreen.tsx`, `ParentExpoApp.tsx`, `ParentVisualPreviewHarness.tsx`, existing assertions in `parentFlowV1.test.ts` and `parentSrsBehavior.test.ts`, `status/STATUS.md`, Plan Revision 17, and `evidence/IMPLEMENTATION_REPORT_SRS_REV67_UI_ALIGNMENT_20261115.md`.
- Scope: pending/unavailable consent blocks learning; unavailable main-activity selection cannot be bypassed into story generation or confirmation; story actions remain disabled until an explicit confirmed-selection state is available. Keep pinned activities read-only. Add no fake selection, success, or API payload.
- This addendum supersedes only the prior FEAT-081 non-blocking unavailable-consent behavior and the story-without-main-activity bypass for this owner-directed Rev67 alignment. No-preset support remains unavailable pending exact service-contract confirmation.
- No backend, domain, API contract/payload, network, install, emulator, tests, typecheck, validators, Android build, or Modal work is authorized in this addendum. No staging, commit, or push. Do not edit `CONTEXT.md`, `DECISIONS.md`, the SRS file, or the repository-wide authority register. OWNER_MODAL_CALL_APPROVED=NO.

Addendum 33 - FEAT-081 publish completed SRS Rev67 Parent UI alignment

- Status: APPROVED and launched by the owner's direct 2026-11-15 instruction: “Th đẩy lên đi có gì vừa làm BE sửa tiếp”. This addendum authorizes publishing the completed Rev67 UI alignment scope so backend follow-up can proceed.
- Approved plan pin: `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_18.md`, 2,585 bytes / SHA-256 `4453F1C7FD45117420969F9D7BD2E7A93BBA4F61BFF1D2073E9522EFDABB6BB8`.
- `TASK_APPROVAL.md` pre-append pin: 88,094 bytes / SHA-256 `69357AB7E419D607612CDE41879222C405E7C53B96CD6E26F1131F5C78EE7E3A`.
- Authorized publication paths are exactly the allowlist in Plan Revision 18, including this plan and approval record. Do not stage any other file; preserve `CONTEXT.md` and `DECISIONS.md` unchanged.
- Run only `python tools/validate_repository_security.py` as the repository-mandated pre-commit/pre-push check. Do not run tests, typecheck, other validators, diff-check, install, backend, Android build, emulator, Modal, or network inspection/fetch.
- Create one new commit `fix(FEAT-081): enforce Rev67 Parent flow gates` on `feature/fe-mobile-remediation`, then push that branch to `origin` without force. Do not amend, rebase, squash, or rewrite existing commits. The Git push is the only authorized network action.
- This addendum supersedes Addendum 32 only for its exact publication allowlist and the security validator authorization above. It authorizes no further implementation or API/backend changes. OWNER_MODAL_CALL_APPROVED=NO.

## Addendum 34 — merge latest dev into feature/fe-mobile-remediation

- Status: APPROVED and launched by the owner's direct request on 2026-11-19 (Asia/Saigon) to merge the newest dev commits into this branch.
- Approved plan: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_19.md, revision 19, 2729 bytes, SHA-256 DBB87D404631265B0A3DF03E2C9E8CD195B5ABE6A11DCB5324EE31C7F3164302.
- Exact source: fetched origin/dev at ba295f1113129fa233ddc762ef29fadd92b996e8; target starts at 5aa9443a772462d247a6018a62aab4e37d2092ae. The branches diverge from 1c9148e88600a101887e477541c4c4893ba1c7df; 16 dev-only and 7 feature-only commits were present.
- Approved scope: merge that exact dev tip into feature/fe-mobile-remediation; preserve all branch-only FEAT-081 files; resolve the sole merge-tree conflict in .gitattributes by retaining both the complete incoming dev rules and FEAT-081 byte-preservation rules for Plan Revisions 5 and 7; add this plan, approval, one merge evidence note, and a status update.
- Required verification: repository security validator before commit; inspect merge ancestry, unmerged paths, preservation attributes, and pre-merge/post-merge hashes for Plan Revisions 5 and 7.
- Not authorized: push, rebase/reset/squash, product code edits outside Git's merge result, tests, API/AI/runtime calls, Docker/DB/Firebase/Modal operations, secret/env changes, or changes to historical SRS decisions. No tests are part of this merge task.
- This addendum supersedes Addendum 33 only for fetching origin/dev and merging the exact fetched tip above, with the documentation and verification listed here. All other restrictions remain in effect.
## Addendum 35 — implement Parent Expo real E2E integration plan

- Status: APPROVED and launched by the owner's direct instruction “implement” on 2026-11-19.
- Approved plan: plan/PLAN_REVISION_20_PARENT_UI_E2E_INTEGRATION_20261119.md, revision 20, 31625 bytes, SHA-256 C049A32458598D4F8C1A9C0D07834D6F37C81D6EEFB6DF3D1CAB642E96AF18D8.
- TASK_APPROVAL.md pre-append pin: 91332 bytes / SHA-256 641378288CA9AE1AEE3ED4B991193ACCC77EAA652F8068ECC8138940C7F55A64.
- Scope: implement Plan Rev20 in the current feature worktree. This includes the M0 API/SRS contract reconciliation, Parent Expo UI and API integration, Parent-specific backend contracts/routes/persistence, SVG topic/object suggestions, photo/VLM, activity selection persistence, story/revision, platform support surfaces, and E2E evidence, subject to the dependencies and gates in Rev20.
- Authorized source scope: apps/ui-mobile/src/parent/**, apps/ui-mobile/src/App.tsx when required for composition, apps/ui-mobile/tests/**; Parent-specific backend code under backend/src/sketch2life/application, contracts, interfaces/http, infrastructure/ai and infrastructure/persistence; backend OpenAPI contract mapping and focused tests; deployment/modal/** only when required by the Parent workloads; backend/alembic/versions/** only when M0 demonstrates a persistence gap and the matching Data Table Register mapping is updated; FEAT-063 canonical SRS/DECISIONS and FEAT-081 plan/status/evidence records.
- Excluded scope: billing, quota, purchases, subscription/payment, Teacher UI and unrelated routes/features. Do not implement or modify quota/payment contracts. Do not use the legacy session video route as a Parent StoryRun API.
- SRS amendment: record the owner's two-stage topic/object suggestion direction and resolve the current SRS no-preselected-subject wording explicitly. Keep SRS unsigned and identify this as an owner amendment; do not imply formal SRS sign-off.
- Data/privacy: synthetic Parent account/profile and synthetic/generated artwork only. No real child data, fake consent, fake UI success, preview harness, or fixture-backed E2E. Preserve Firebase Auth as the only Firebase service used.
- Verification authorized: focused FE/backend contract and unit checks, typecheck/build as needed, local Docker/backend API checks, Android emulator E2E, and the real Modal non-video inference needed for the approved flow. Use a bounded run: at most one live inference per required workload per end-to-end path before reviewing results; no automatic repeat loops or GPU warming. Video inference is not authorized until real quota admission is handed off and a separate bounded video budget is recorded.
- No migration may be run against a shared or production database. Any migration must be additive, documented in the matching data register, and run only against disposable local dev data.
- No staging, commit, push, branch switch, rebase, reset, or history rewrite is authorized.
- OWNER_MODAL_CALL_APPROVED=YES for the bounded non-video Parent E2E calls above; OWNER_VIDEO_INFERENCE_APPROVED=NO pending quota admission handoff.
## Addendum 36 — typecheck root-cause fix and second bounded Parent E2E path

- Status: APPROVED by the owner's direct answers on 2026-11-19 (Asia/Saigon): "Cho sửa" for the typecheck fix and "Cho phép, bạn điều khiển máy" for one more bounded live Parent E2E path driven by the assistant through computer use.
- TASK_APPROVAL.md pre-append pin: 94440 bytes / SHA-256 A55B7F77F74C4B785D0F38C61C4DF36E79B0CEB827AA930D94E33BC2C2788BE8.
- Typecheck scope: add React type path mappings to `apps/ui-mobile/tsconfig.typecheck.json` only (not `tsconfig.json`: Expo CLI 0.22 enables `experiments.tsconfigPaths` by default, so a `react` path in `tsconfig.json` would also redirect Metro's runtime resolution to the types-only package). Root cause: pnpm hoists `@types/react@19.2.18` into `node_modules/.pnpm/node_modules`, so Expo libraries (`@expo/vector-icons`, `expo-linear-gradient`, `react-native-svg`) resolve React 19 types while the app pins React 18.3.1 / `@types/react` ~18.3.12. No dependency, lockfile, or install change. Verify with `pnpm --dir apps/ui-mobile typecheck` (or the equivalent local tsc invocation) and the existing mobile tests.
- Live scope: one new end-to-end Parent path on the existing synthetic Parent account/profile and synthetic artwork, with at most one live inference per required non-video workload (drawing VLM, activity selection, story) before reviewing results. No automatic repeats, GPU warming, video inference, quota/payment changes, real child data, preview harness, or fixtures. Stop task-local Docker and the Modal non-video apps used after the run; leave the Modal video app untouched.
- All Addendum 35 limits otherwise remain: no staging, commit, push, branch switch, rebase, reset, history rewrite, or migration against shared/production data. OWNER_MODAL_CALL_APPROVED=YES (bounded, non-video, this path only); OWNER_VIDEO_INFERENCE_APPROVED=NO.

## Addendum 37 — one bounded rerun after drawing parser fix

- Status: APPROVED and launched by the owner's direct request on 2026-11-19 (Asia/Saigon): “chạy lại thử đi, đã fix r”.
- Scope: verify the byte-fragment/EOS parser fix in the existing FEAT-081 local Android workflow using synthetic Parent data and the generated synthetic turtle artwork. Run the focused offline parser tests first. If those pass, permit one fresh non-video Parent path with at most one live drawing VLM inference, then at most one activity-suggestion inference and one story-generation inference only if all preceding steps pass. No automatic retries or repeat calls.
- Do not call video, narration, quota, payment, or use real child data, fixtures, preview harness, or direct database edits. If the existing run/profile or authentication state prevents a genuine UI path, stop and report it; do not bypass it.
- Stop only the task-local Docker stack, task Metro, and Modal non-video apps used by this run afterward. Leave the deployed Modal video app untouched.
- No migration against shared/production data, stage, commit, push, branch switch, rebase, reset, or history rewrite is authorized. This addendum records the owner's new one-shot test authorization; OWNER_MODAL_CALL_APPROVED=YES for this bounded non-video rerun only; OWNER_VIDEO_INFERENCE_APPROVED=NO.

## Addendum 38 — align Parent drawing confidence contract

- Status: APPROVED by the owner's direct instruction on 2026-11-19 (Asia/Saigon): “fix cái đó đi”.
- Approved plan: `plan/PLAN_REVISION_21_DRAWING_CONFIDENCE_CONTRACT_20261119.md`, 4,528 bytes, SHA-256 `9C32A46DAF4095741A7D54B7051E7CEE847F913C0FB564D5F02FBBDD9E168822`.
- TASK_APPROVAL.md pre-append pin: 97,705 bytes, SHA-256 `1838B4510A650EB9DBBC533588B09DC05DC858E470263C7C2F4314F92FA33807`.
- Authorized implementation paths: `deployment/modal/srs_v23/drawing_vlm_app.py`; this plan and approval record; FEAT-081 `CONTEXT.md` and `status/STATUS.md`.
- Scope: add the advisory drawing-subject confidence required by SRS AT-14 and the existing backend contract to the Qwen worker's constrained JSON schema, prompt, strict parser, and returned result. Keep the value finite and within [0,1], retain mandatory adult confirmation, and do not claim calibration or create a fallback score. Backend contract remains unchanged.
- No tests, typecheck, deployment, Modal inference, Docker, database, migration, SRS change, staging, commit, push, branch switch, rebase, reset, or history rewrite is authorized by this addendum. Source review only; runtime verification remains pending.
- This addendum does not renew the consumed one-shot Modal inference authorization in Addendum 37 and does not alter the prohibition on video/quota/payment work. OWNER_MODAL_CALL_APPROVED=NO for new live calls; OWNER_VIDEO_INFERENCE_APPROVED=NO.

## Addendum 39 — record FEAT-081 source-fix evidence path

- Status: Scope clarification recorded under the owner's existing Addendum 38 instruction to fix the drawing confidence contract. This adds the repository-required feature-local evidence note to Plan Revision 21's authorized paths; it does not claim a new owner decision or expand code, test, deployment, inference, or publication scope.
- Updated plan pin: `plan/PLAN_REVISION_21_DRAWING_CONFIDENCE_CONTRACT_20261119.md`, 4,585 bytes, SHA-256 `3B132715CA6948677080D040313621A8DE81774058C4207DB7D86D5D93CCA163`.
- TASK_APPROVAL.md pre-append pin: 99,200 bytes, SHA-256 `B82943D3BD9DF6B0472DBED15257CAB0732AFCB29B433390717ED1D4A50B203E`.
- Added authorized documentation path: `evidence/DRAWING_CONFIDENCE_CONTRACT_FIX_20261119.md`. All other Addendum 38 boundaries remain unchanged.

## Addendum 40 — one bounded Android UI verification of drawing confidence

- Status: APPROVED by the owner's direct instruction on 2026-11-19 (Asia/Saigon): “sửa r thì test lại trên UI đi, lựa ảnh nào phù hợp vs trẻ”.
- Approved plan: `plan/PLAN_REVISION_22_DRAWING_CONFIDENCE_ANDROID_UI_VERIFICATION_20261119.md`, 3,783 bytes, SHA-256 `E166064D5FE7A155DD92B6032513A4C3DC677C0EF3A0D892550CB3A274BC1023`.
- TASK_APPROVAL.md pre-append pin: 100,046 bytes, SHA-256 `4E2139195B33D34D34877D007B6642E81C636AC2CCD1EB39E2EB04B0BDC4680C`.
- Scope: run the focused `test_drawing_lmfe_byte_fragments.py` regression file; deploy only `drawing_vlm_app.py` to Modal dev; use the real Parent Android UI and one fresh synthetic turtle drawing inference to verify HTTP/API acceptance and visible confidence/adult-confirmation UI. Use synthetic data only and no preview harness/fixture. A fresh synthetic Parent/profile may be created through the UI if the prior failed StoryRun blocks a new run.
- No retries, second inference, activity/story/narration/video/quota/payment calls, direct database edits/migrations, unrelated Modal deployment, commit, push, branch switch, rebase, reset, or history rewrite.
- Stop task-local Docker/Metro, the Modal drawing app, and the emulator started for this test. Leave Modal video and unrelated services untouched. This addendum supersedes Addendum 38 only for this bounded deploy/test scope; Addendum 37's consumed inference is not reused.
- OWNER_MODAL_CALL_APPROVED=YES for this single drawing inference only. OWNER_VIDEO_INFERENCE_APPROVED=NO.

## Addendum 41 — Parent activity, story, and video E2E

- Status: APPROVED by the owner's direct instruction on 2026-11-19 (Asia/Saigon): “bước chọn hoạt động, video đồ nữa thì sao, chạy full luồng end to end đi, đừng quan tâm quota”.
- Approved plan: `plan/PLAN_REVISION_23_PARENT_ACTIVITY_STORY_VIDEO_E2E_20261119.md`, SHA-256 `5896253DBC2AE4484B2DE57FCF9A0377E987570241EC9BCC8BAE0C82B5C12EEA`.
- TASK_APPROVAL.md pre-append pin: 101,641 bytes, SHA-256 `3E7363BFCCBD15E51F358952B1723F452E1F39F06E941F674CC5DF794ADF80BE`.
- Authorized scope: resume the existing synthetic Parent Android run after adult subject review; complete catalog-first activity selection and persisted receipt, story generation/review/confirmation, and a real silent LTX-2.5 Modal video request; add only the Parent API/UI/worker wiring and local synthetic no-quota guard needed to make that real vertical slice executable; run one bounded live request per AI stage and capture sanitized evidence.
- Quota bypass is authorized only for local development with a synthetic Parent/profile, must default OFF, be server-guarded and auditable, and must not change non-local/product quota enforcement. Preserve subject, activity, script, schema, and fail-closed video safety gates.
- Use SRS target LTX-2.5. No Wan or legacy session-video substitution. No fixture/mock, direct DB edits, real child data, narration, payment/quota test, shared/production migration, commit, or push. Stop before substituting another model if the existing Modal environment cannot access/run the pinned LTX target.
- Authorized paths are exactly those listed in Plan Revision 23 §6. Modal activity/story/video inference is approved within the plan's one-call-per-stage bound; no duplicate taps/retries. OWNER_MODAL_CALL_APPROVED=YES (bounded); OWNER_VIDEO_INFERENCE_APPROVED=YES (one video request, scenes only as required by the confirmed storyboard, no scene retries).

## Addendum 42 — continue the real Parent E2E under the newly registered account

- Status: APPROVED by the owner's direct request to run the complete workflow end to end, followed by “đăng ký đi” when the real Android app required authentication.
- Updated plan: `plan/PLAN_REVISION_23_PARENT_ACTIVITY_STORY_VIDEO_E2E_20261119.md`, 12,127 bytes, SHA-256 `1C55B8AFC862D48B2C761FD25FFA11923826E213A89A9251F566122B1A0DD392`.
- TASK_APPROVAL.md pre-append pin: 103,593 bytes, SHA-256 `01A49C547A377C6DBA990DD140280E1676F4D2B49F107E875337425467E0814B`.
- The synthetic Parent account was created through the real Android UI and is a different principal from the owner of the earlier Rev22 run. Do not impersonate or transfer that run. Create one synthetic profile and a fresh run through the UI, reusing only the existing generated synthetic turtle drawing as input.
- Newly authorized live-call bound: one Drawing VLM inference, one catalog-first activity suggestion inference, one story inference, and one silent LTX-2.5 video request. No retries, warmups, duplicate submissions, or per-scene retries. All calls must be reached through the real UI and authenticated backend; outputs must be actual model results.
- Scope additions are limited to creating the synthetic profile/run and performing the one fresh drawing inference needed to complete the requested full workflow. Synthetic-only local quota bypass and Rev23 safety/quality gates remain mandatory. Stop before the next inference if a preceding contract or gate fails.
- This addendum supersedes Addendum 41 only for the existing-run ownership, one-repeat drawing prohibition, and the corresponding starting-state acceptance criterion. All remaining Rev23 restrictions remain in force: no real child data, consent relaxation, direct DB edits, production deployment, payment test, fixture/mock output, commit, push, or unrelated service changes. Do not store credentials or Firebase tokens. OWNER_MODAL_CALL_APPROVED=YES (bounded four-stage flow); OWNER_VIDEO_INFERENCE_APPROVED=YES (one request, scenes only as required by the confirmed storyboard, no retries).

## Addendum 43 — recover from the real pre-dispatch drawing failure

- Status: APPROVED under the owner's direct instruction to run the complete Parent flow end to end and continue fixing failures; this records the narrow recovery needed after the current test encountered a confirmed pre-dispatch failure.
- Evidence: API call failed at `function_spawn` with Modal `NotFoundError`, no Modal call ID, while the expected drawing app was stopped. The app was subsequently deployed from the pinned source. No model inference was dispatched by the failed request.
- Approved: expose the existing authenticated Parent StoryRun cancellation route in the real mobile UI for the unresolved synthetic photo run; add the narrow backend classification for `NotFoundError` specifically at spawn as terminal `MODAL_FUNCTION_NOT_DEPLOYED`; add focused regression coverage; create one new UI StoryRun with the same approved synthetic artwork and allow one actual drawing inference, followed by the already-approved at-most-one activity suggestion, story, and silent LTX-2.5 request only when prior gates pass.
- Cancellation records `DELETE_PENDING`; it is not represented as stopping a Modal task. No direct DB access/edit, fixture, duplicate model inference, auto-retry, model warm-up, quota/payment change, real child data, commit, push, or non-Rev23 work is authorized.
- The prior 504 attempt is recorded as a failed pre-dispatch request and not as an inference. All other Addendum 42 limits and cleanup boundaries remain in force. OWNER_MODAL_CALL_APPROVED=YES (one actual model call per workload); OWNER_VIDEO_INFERENCE_APPROVED=YES (one request, storyboard scenes only, no scene retries).

## Addendum 44 — synchronize the active Parent branch with dev

- Status: APPROVED by the owner's direct instruction on 2026-11-19 (Asia/Saigon): “CHECK DEV XEM CÓ CÁI J THÌ PULL VỀ, SÀI ĐI”.
- Plan: `plan/PLAN_REVISION_23_PARENT_ACTIVITY_STORY_VIDEO_E2E_20261119.md`, Execution Amendment A3.
- Source snapshot: merge the fetched `origin/dev` at `a43c2aee71160926b3d7979a0235f39d735ead1c`, whose last shared base with the feature branch is `ba295f1113129fa233ddc762ef29fadd92b996e8`.
- Approved: merge the complete dev delta into `feature/fe-mobile-remediation` with history preserved; a single merge commit is allowed as the integration record. No push. Existing dirty and untracked work must be preserved and restored; inspect/resolve all overlapping Parent, backend, SRS, and approval files before continuing the Rev23 E2E.
- Run focused integration checks and `python tools/validate_repository_security.py` before the merge commit; record results and conflict resolutions in FEAT-081 evidence/status. This addendum does not authorize additional AI calls beyond Addenda 42–43, production changes, real child data, direct database edits, or unrelated implementation.

## Addendum 45 — diagnose Parent signup and run the Parent API workflow

- Status: APPROVED and launched by the owner's direct instruction on 2026-11-19 (Asia/Saigon) to diagnose the supplied registration error, check/fix Parent APIs, and run the Parent workflows through the UI; product quota must not block this local test.
- Approved plan: `plan/PLAN_REVISION_24_PARENT_API_AUTH_E2E_20261119.md`, 6,744 bytes, SHA-256 `9916DAA363597DB6CD20982223AEB6279296D1377BC331B71571CD9CDCEC768A`.
- Scope: correct repository-owned Expo/Firebase/API config and Parent API/UI/backend/worker defects within the existing Rev23 boundaries; compare the live served OpenAPI with Parent UI/SRS; run one fresh synthetic Android Parent flow through the APIs/workers available.
- Reauthorization: after offline contract/code fixes and readiness checks, this addendum permits one fresh live request for each of drawing understanding, activity suggestions, story generation, and silent LTX-2.5 video. The prior failed drawing attempt is not replayed. No retry, duplicate submission, warmup, per-scene retry, real child data, fixture/mock output, direct DB mutation, production change, or provider substitution.
- Quota/payment endpoints are not tested. A no-product-quota video request remains local-only, synthetic-only, server-guarded, auditable, and disabled by default. Existing SRS subject/activity/story/safety gates stay mandatory.
- Evidence goes only in `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/`. Do not record credentials, Firebase API/admin secrets, or ID/refresh tokens. Stop only services started/used by this task; do not stop unrelated apps.
- Authorized paths: Plan Revision 24 §7. No commit, push, branch switch, rebase, reset, history rewrite, `.env` edit, quota/payment implementation, or Teacher work.
- OWNER_MODAL_CALL_APPROVED=YES for the bounded one-fresh-path calls above; OWNER_VIDEO_INFERENCE_APPROVED=YES for one silent LTX-2.5 request with no scene retry.

## Addendum 46 — one fresh emulator run after dev-seed inspection

- Status: APPROVED and launched by the owner's direct instruction on 2026-11-20 (Asia/Saigon): inspect the new dev seed, use it if it is a usable Parent login, and rerun the full Parent flow on the Android emulator.
- Finding that narrows execution: the dev seed added in `origin/dev` creates development-mode PostgreSQL principals and content, not Firebase Auth login accounts. Its guard requires development auth and disabled AI, while this local API uses Firebase Auth and Modal. Do not bypass the seed guard or inject seed principals into the Firebase-backed database.
- Execution amendment to Plan Revision 24 §4: run one fresh real Android Parent path with a newly registered synthetic Firebase Parent and synthetic profile/artwork. Permit at most one live request each for drawing understanding, activity suggestion, story generation, and silent LTX-2.5 video, only as prior business gates pass. No fixture, replay of an uncertain registration, automatic retry, duplicate inference, warm-up, real child data, quota/payment work, or direct DB mutation.
- Preserve all remaining Plan Revision 24 and Addenda 42–45 boundaries, evidence location, and task-owned-service cleanup rules. No commit, push, environment-file edit, or unrelated service shutdown.
- OWNER_MODAL_CALL_APPROVED=YES for this fresh bounded path; OWNER_VIDEO_INFERENCE_APPROVED=YES for at most one silent request, with no scene retry.

## Addendum 47 — recover the Parent activity worker contract gate

- Status: APPROVED under the owner's active 2026-11-20 instruction to run the real Parent flow on the emulator and fix blockers until the flow can proceed.
- Evidence: the only dispatched `parent.activity.suggest` call failed at worker `input_envelope` with `MODAL_WORKLOAD_NOT_ALLOWED`; Modal logs show no model-load or inference phase. The deterministic contract allowlist omitted a workload implemented by the deployed `suggest-parent-activities` function.
- Authorized: add `parent.activity.suggest` to the L4 worker-envelope allowlist, add a focused offline regression test, redeploy the task-used language/audio app, then allow exactly one UI-driven recovery request for this workload. No further activity request if that recovery fails.
- All other Plan Revision 24 and Addendum 46 boundaries remain: synthetic-only, no fixture, no direct DB mutation, no quota/payment, no automatic retry, no commit/push, evidence in the existing FEAT-081 folder, and stop only task-used services after recording results.
- OWNER_MODAL_CALL_APPROVED=YES for one recovery call after the pre-model contract failure; OWNER_VIDEO_INFERENCE_APPROVED=YES remains capped at one silent request with no scene retry.

## Addendum 48 — recover Qwen3.5 activity inference and continue Parent E2E

- Status: APPROVED by the owner's direct instruction on 2026-11-20 (Asia/Saigon): “fix tiếp đi, nào nó chạy đc hết thig dùng”.
- Approved plan: `plan/PLAN_REVISION_25_QWEN35_ACTIVITY_INFERENCE_RECOVERY_20261120.md`, SHA-256 `780975555258CBA8314AAFAF3228543612DC440A0EE15467CDB4A31185A96229`.
- Evidence from the previous real Android run: activity worker passed request/model preparation and then stalled in Qwen3.5 `model_inference` for 1,800 seconds without token progress or terminal output. Modal warned that optional FLA and causal-conv1d fast kernels were missing. This is the issue to fix; no SRS quality/safety gate may be weakened.
- Authorized: pin compatible fast-kernel dependencies in the shared Qwen Modal image; add safe runtime readiness/fail-fast checks and token-count-only inference progress for Parent activity/story; cap activity request duration at 8 minutes; test offline and verify CPU health/readiness without loading weights or issuing a warm-up inference; deploy the task language/audio app; perform up to two real activity attempts via the authenticated Android UI, only when the prior attempt yielded an actionable defect and a code/deploy fix was made. No model/provider substitution.
- If activity succeeds, continue via the real UI with one activity-selection persistence, one Qwen3.5 story request/review, and at most one silent LTX-2.5 request if the exact API/worker and all gates are executable. Reuse the prior successful drawing/context result when the supported workflow permits; do not replay a successful inference. No direct worker call or synthetic result fabrication.
- Preserve all other Plan Revision 24/Addenda 42–46 restrictions: synthetic-only, no fixture/mock, no direct DB mutation, no real child data, no quota/payment test, no secret or `.env` edit, no auto-retry, no scene retry, no commit/push, and stop only task-owned services after evidence capture. Evidence remains in `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/`.
- OWNER_MODAL_CALL_APPROVED=YES for up to two bounded post-fix activity calls (8 minutes each), one story call after activity selection, and at most one silent LTX-2.5 call after story confirmation. OWNER_VIDEO_INFERENCE_APPROVED=YES remains limited to the single silent request with no scene retries.

## Addendum 49 — fix Parent custom-topic canonicalization from real UI evidence

- Status: APPROVED by the owner's direct instruction on 2026-11-20 (Asia/Saigon) to keep fixing the real Parent workflow until it runs.
- Approved plan: `plan/PLAN_REVISION_26_TOPIC_CANONICALIZATION_FIX_20261120.md`.
- Evidence: the authenticated topic-subject catalog request returned HTTP 200 and three cards for the Vietnamese `Động vật` catalog entry, but the UI rejected the response because it compared the canonical accented label to the user's unaccented `Dong vat` input with exact string equality. No Modal worker was called by that request.
- Authorized: add a pure Vietnamese-aware topic-label normalizer, use it only to validate the server's canonical topic response, preserve canonical server ID/label on success, add a safe topic-flow-specific contract error message, and focused regression coverage. Verify by one real emulator catalog-only request after rebuilding/reloading the app.
- This does not grant any additional AI inference. Plan Revision 25's existing limits remain: up to two post-fix activity calls at 8 minutes each only when justified by an actionable fix, one story call after a persisted activity receipt, and at most one silent LTX-2.5 video request after all gates pass. No topic-subject AI call, retry, warm-up, fixture, real child data, direct DB mutation, `.env`/secret edit, quota/payment work, migration, commit, push, or unrelated service shutdown.
- Authorized paths are exactly those in Plan Revision 26 §5, in addition to Plan Revision 25. Preserve all other active FEAT-081 boundaries and the existing task-local evidence folder.
- OWNER_MODAL_CALL_APPROVED remains as bounded by Addendum 48; this addendum does not renew it. OWNER_VIDEO_INFERENCE_APPROVED remains capped at one silent request, no scene retries.

## Addendum 50 — recover the bounded Parent E2E after Android bundle reload

- Status: APPROVED under the owner's active direct instruction on 2026-11-20 to keep fixing and run the Parent workflow through to completion.
- Approved plan: `plan/PLAN_REVISION_27_REAUTH_AFTER_BUNDLE_RELOAD_20261120.md`.
- Evidence: after restarting the Expo dev app to ensure the updated topic-normalization bundle was loaded, Android returned to the Firebase Parent sign-in screen and did not restore the prior in-memory test session. The previous synthetic account/profile/run are left untouched; no credentials are available in evidence.
- Authorized: create one additional synthetic Firebase Parent account and profile via the actual Android UI, with generated credentials held only transiently and never logged, stored, or captured; continue the real UI workflow from that new profile.
- No AI inference allowance is renewed. Plan Revision 25's existing drawing-if-required, activity, story, and silent-video caps remain in force. No account enumeration/password reset, direct DB mutation, deletion of prior data, fixture, real child data, `.env`/secret edit, quota/payment change, retry, warm-up, commit, push, or unrelated service shutdown.
- Preserve Addenda 48–49 and all other FEAT-081 boundaries. Evidence stays in `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/`; do not stop the emulator.
- OWNER_MODAL_CALL_APPROVED and OWNER_VIDEO_INFERENCE_APPROVED remain only as bounded by Addendum 48; this addendum does not expand them.

## Addendum 51 — correct custom-topic resolution and isolate the remaining UI rejection

- Status: APPROVED under the owner's active direct instruction on 2026-11-20 to continue fixing the real Parent workflow until it runs.
- Approved plan: `plan/PLAN_REVISION_28_CUSTOM_TOPIC_RESOLUTION_DIAGNOSTICS_20261120.md`.
- Evidence: the live API returned 200 for the custom topic request and the backend resolved it to the canonical animals topic with three curated cards, yet the emulator remained on the topic screen with a misleading account message after the first normalization patch. The remaining rejected-contract field has not yet been proven.
- Authorized: compare ID + normalized label for selected catalog cards; for custom text, accept the backend-resolved canonical topic ID/label when the three-card contract is valid; emit only development-time boolean/count diagnostics on rejection; add/update focused regression cases; and perform one catalog-only UI request after the code update.
- If the UI still fails, stop before AI and report the sanitized contract flags. No repeated catalog request, topic-subject AI request, drawing/activity/story/video inference, retry, quota/payment change, real child data, fixture, account enumeration/reset, direct DB mutation, `.env`/secret edit, migration, commit, push, or unrelated service stop is authorized by this addendum.
- All prior Plan Revision 25 call limits remain unchanged and are not renewed here. Evidence remains in `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/`.

## Addendum 52 — show topic-specific errors after the final catalog verification

- Status: APPROVED under the owner's active 2026-11-20 direct instruction to keep fixing the Parent flow until it works.
- Approved plan: `plan/PLAN_REVISION_29_TOPIC_ERROR_CLASSIFICATION_FIX_20261120.md`.
- Evidence: the emulator still showed “Chưa thể hoàn tất thao tác tài khoản” after the canonical-topic fix, although the subject endpoint returned HTTP 200. A topic error handler uses `instanceof ParentApplicationError`, which may fail across Expo Fast Refresh module instances and route the error to the unrelated account message. This is a plausible error-message cause; it does not by itself explain why navigation did not advance.
- Authorized: classify topic errors by structural safe code, provide topic-specific fallback copy, retain the Revision 28 backend-canonical custom-topic behavior and boolean/count-only diagnostics, add focused coverage, and make one final catalog-only UI request after the update.
- No AI inference, repeat request after this final catalog attempt, real child data, fixture, direct DB mutation, account enumeration/reset, `.env`/secret edit, quota/payment, migration, commit, push, or unrelated shutdown. If the final UI attempt fails, stop and report the exact safe failure boundary rather than submitting another request.
- Plan Revision 25 AI limits remain unchanged; this addendum does not renew any Modal call. Evidence remains in `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/`.

## Addendum 53 — continue the same Parent E2E through the curated animal topic

- Status: APPROVED under the owner's active 2026-11-20 request to continue fixing the Parent flow and run it when it works.
- Approved plan: `plan/PLAN_REVISION_30_CONTINUE_VIA_CATALOG_TOPIC_20261120.md`.
- Starting state: the same authenticated synthetic Parent UI remains on topic choice with the curated `Động vật` topic card visible; the current profile is synthetic and has not been run through drawing/activity/story/video in this continuation.
- Authorized: select that curated card and make one catalog-only subject-suggestion request. If the UI advances with three cards, continue the Android E2E under Plan Revision 25's existing per-workload limits. Do not make another custom-topic request.
- If this curated path fails, stop before Modal inference and report the exact sanitized failure. No extra account/profile creation, app restart, direct DB mutation, fixture, real child data, quota/payment, `.env`/secret edit, retry, warm-up, commit, push, or unrelated service shutdown.
- Plan Revision 25 inference limits remain unchanged and are not renewed. Evidence stays in `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/`.

## Addendum 54 — restore the absent drawing Modal deployment

- Status: APPROVED under the owner's active 2026-11-20 direct instruction: “fix tiếp đi, nào nó chạy đc hết thig dùng”.
- Approved plan: `plan/PLAN_REVISION_31_RESTORE_DRAWING_MODAL_DEPLOYMENT_20261120.md`.
- Evidence: the current real Parent UI request failed before Modal worker execution with `MODAL_FUNCTION_UNAVAILABLE` / `NotFoundError` at `function_spawn`; Modal `dev` inventory confirms the drawing app is absent, while the pinned Qwen checkpoint directory and existing HF Secret are present.
- Authorized: deploy the existing drawing worker to Modal `dev` without changing its code/model/secret; verify function registration and checkpoint presence without GPU warm-up; reconcile the unresolved run through supported UI/API; if required, create one new real UI run on the existing synthetic profile/artwork and submit exactly one actual drawing inference. The previous pre-worker dispatch rejection is not a model inference. If the actual inference fails, do not resend the drawing.
- If drawing succeeds, continue only under Plan Revision 25's existing caps: activity up to two calls only after actionable fix (8-minute hard cap), one story after persisted activity selection, and at most one silent LTX-2.5 call after all gates pass. No extra activity/story/video allowance is added.
- All other restrictions remain: synthetic-only, no fixtures/mocks/direct worker or DB, no real child data, quota/payment change or bypass, secret/`.env` edit, model download/warm-up, migration, commit/push, and no unrelated shutdown. Keep emulator online; clean up only task-used services after evidence capture.
- OWNER_MODAL_CALL_APPROVED=YES for one UI-driven actual drawing inference after deployment; subsequent workload limits and OWNER_VIDEO_INFERENCE_APPROVED remain exactly as in Addendum 48.

## Addendum 55 — recover the Parent E2E after transient sign-in values were rejected

- Status: APPROVED under the owner's active 2026-11-20 direct instruction to keep fixing and run the Parent flow until it works.
- Approved plan: `plan/PLAN_REVISION_32_RECOVER_PARENT_AUTH_FOR_REAL_E2E_20261120.md`.
- Evidence: Android system Back returned the app to auth; the transient account values still visible in the form were rejected by Firebase sign-in. Credentials were not recorded. The original account/profile remain untouched.
- Authorized: create exactly one new synthetic Parent account through real Expo signup, with a generated unique email/password held only transiently and never logged, captured, or persisted; create one synthetic profile through the same UI after signup success; continue the workflow. No second attempt if account or profile creation fails.
- The newly deployed Modal drawing app and Revision 31's one real UI-driven drawing inference allowance remain active. No additional AI-call allowance is added; Revision 25 activity/story/silent-video caps remain unchanged.
- All other restrictions remain: no account enumeration/reset/delete/transfer, backend/admin account creation, real child data, fixture/mock, direct DB write, `.env`/secret edit, quota/payment, migration, commit/push or branch/history operation. Use in-app navigation only, keep emulator online, and stop only task-used services after evidence capture.

## Addendum 56 — diagnose Firebase ID-token rejection after successful signup

- Status: APPROVED under the owner's active 2026-11-20 instruction to keep fixing and run the Parent workflow until it works.
- Approved plan amendment: Plan Revision 32 §1.1.
- Evidence: the one authorized Expo signup returned HTTP 201; the following `/api/auth/v1/me` request returned 401 and Firebase Admin reported `InvalidIdTokenError`. Public Firebase configuration and Admin credential project IDs match `sketch2life-dev`; no credentials or identity values were recorded.
- Authorized: add backend-only, sanitized claim diagnostics that log booleans for token structure, audience/project match, issuer/project match, subject presence and expiration; add focused regression coverage; rebuild only the task-local API container; then sign in once through the actual Expo UI using the already-created account. Do not log token/claim values, email, UID, password, provider message, or any credential.
- This addendum authorizes no additional signup/account/profile, account lookup/reset/deletion, `.env` or secret change, direct DB operation, new AI inference, quota/payment change, migration, commit, push, or shutdown of unrelated services. All Rev25 inference limits, Rev31 drawing limit, synthetic-only use, evidence and cleanup constraints remain in force.

## Addendum 57 — fix text-only Parent activity inference throughput

- **Status:** APPROVED under the owner's direct 2026-11-20 instruction to keep fixing the Parent workflow until it runs.
- **Approved plan:** `plan/PLAN_REVISION_33_PARENT_ACTIVITY_TEXT_ONLY_INFERENCE_20261120.md`.
- **Evidence:** after the first recovery call exposed missing `StoppingCriteriaList` and an unbound progress object, both were fixed and focused checks passed. The second real emulator call used the deployed fast-kernel build, loaded Qwen3.5-9B successfully, but emitted only 104/1,000 tokens in 424.778 seconds. The API ended with `FunctionTimeoutError`/502 and Modal logged `KeyboardInterrupt`; no result or activity receipt was produced. Runtime evidence lacked selected GPU name, module placement, cache state, and LMFE callback timing.
- **Authorized:** change the language/audio worker to the official Qwen3.5 text-only model class while retaining the exact model/revision; add privacy-safe placement and callback timing diagnostics; update CPU readiness and focused tests; redeploy the task language/audio app; and make exactly one additional real UI-driven activity attempt with an 8-minute hard cap and no retry. Existing fast-kernel checks, schema/quality/safety gates, synthetic-only restrictions, and catalog-first business rules stay in force.
- If activity succeeds, continue through one persisted UI activity selection, one story request/review/confirmation, and at most one silent LTX-2.5 request only if all earlier gates pass. Quota/payment are not tested or modified.
- If the bounded activity request fails, stop activity inference under this amendment. No additional drawing call, account/profile, direct DB change, fixtures/mocks, real child data, `.env`/secret edit, quota/payment change, migration, model/provider substitution, scene retry, commit, push, or unrelated service stop is authorized. Keep the emulator online; clean up only task-owned services after evidence capture.

## Addendum 58 — fix Qwen3.5 text processor/model input mismatch

- **Status:** APPROVED under the owner's direct continuing instruction on 2026-11-20 to keep fixing the Parent flow until it runs.
- **Approved plan:** `plan/PLAN_REVISION_34_QWEN35_TEXT_INPUT_COMPAT_20261120.md`.
- **Evidence:** Revision 33's single UI-driven activity request loaded the pinned text-only Qwen3.5 model successfully, then failed before token generation because the processor passed unsupported `mm_token_type_ids` to `Qwen3_5ForCausalLM.generate()`. Worker event: `WORKER_VALUE_ERROR`; Modal call `fc-01M7V6B8Z31YNHR5SPSERRMTHE`; no activity response was persisted.
- **Authorized:** filter only the multimodal-only metadata from text-generation kwargs across text workloads, add focused tests, redeploy the language/audio Modal app, run CPU readiness, then make at most two additional real UI-driven activity requests total, each only after a distinct code fix when needed and each capped at eight minutes. Stop on the first successful response or after the second distinct failure. No repeated call with the same build/input.
- On activity success, continue one UI activity selection/persistence and one story request plus adult review/confirmation; a silent video remains conditional under prior limits. Synthetic-only; existing schema, quality, safety, age, catalog and consent rules remain enforced. No drawing inference, new account/profile, fixture/mock, direct DB change, quota/payment mutation or bypass, secrets/`.env` edit, migration, commit, push or unrelated service shutdown. Keep the emulator online and clean up only task-owned services after evidence capture.

## Addendum 59 — optimize the remaining LMFE activity text path

- **Status:** APPROVED under the owner's continuing direct 2026-11-20 instruction to keep fixing the Parent flow until it works.
- **Approved plan:** `plan/PLAN_REVISION_35_LMFE_PARENT_ACTIVITY_DECODER_PERFORMANCE_20261120.md`.
- **Evidence:** the Rev34 activity call passed the text-model input fix but emitted only 100 tokens in about 195 seconds. Safe LMFE telemetry showed two callbacks taking ~50 seconds each while allowing ~246.5K tokens; the Modal GPU call was cancelled to limit further GPU usage. The affected activity schema uses bounded regex patterns for prose even though the post-generation parser already validates required fields, exact length limits and terminal punctuation.
- **Authorized:** change only the LMFE generation schema for bounded prose fields to min/max string bounds; retain and test post-generation punctuation/length/schema validation; run focused offline tests; redeploy the language/audio app; perform CPU-only readiness; then use exactly one remaining real UI-driven activity request, capped at eight minutes, with no retry.
- On success, continue one activity selection/persistence, one story generation/adult confirmation, and at most one silent video request under existing approvals. No quota/payment mutation or bypass, drawing inference, new accounts/profiles, fixture/mock, direct DB mutation, secret/`.env` change, migration, commit/push, or unrelated shutdown. Preserve existing catalog, safety, age, consent and quality rules; keep emulator online and clean up only task-owned services.

## Addendum 60 — prevent non-Latin escapes in Parent activity output

- **Status:** APPROVED under the owner's continuing direct instruction on 2026-11-20: “fix tiếp đi, nào nó chạy đc hết thig dùng”.
- **Approved plan:** `plan/PLAN_REVISION_36_PARENT_ACTIVITY_VIETNAMESE_OUTPUT_GATE_20261120.md`, 5,932 bytes, SHA-256 `6C3218AFD710117C574CF34C93709A2B07F0526FC8505B2ECD60AB2F71A38375`.
- **TASK_APPROVAL.md pre-append pin:** 133,296 bytes, SHA-256 `65F9B7FF6AC0CFF5916E11BA0073AC30755229703E492387AD855E5A367B6776`.
- **Evidence:** Rev35 call `fc-01M7V7JFVH0RWAMH38VB7G4E74` completed model generation in 99.573s and failed the non-Latin output gate. LMFE 0.11.3 admits `\\uXXXX` escapes inside otherwise alphabet-limited prose; generated text itself was not retained. Parser coverage also omits the catalog reason fields.
- **Authorized:** implement only the M1/M2 changes and exact file boundary in Plan Revision 36; run focused offline tests; deploy only the dev language/audio Modal app; perform CPU-only health/readiness without a warm-up call; then make exactly one fresh, real Parent Android UI activity-suggestion request capped at eight minutes, after the distinct decoder fix passes offline checks.
- On success, continue one activity selection/persistence and one story generation/adult confirmation under existing approvals. One silent LTX-2.5 request remains conditional on all prior gates and its existing exact authorization. On failure, stop inference and prepare another amendment before any further call. No repeat or direct worker request.
- Synthetic-only and reuse the existing authenticated Parent/profile/run/artwork. Keep language, schema, quality, safety, age, consent, catalog, activity-selection, story-review and video-safety gates unchanged. No output repair/translation, model substitution, new account/profile/run, drawing inference, fixture, direct DB edit/migration, quota/payment mutation or bypass, `.env`/secret change, SRS change, commit/push, or unrelated service shutdown. Keep emulator online; stop only task-used services.
- **OWNER_MODAL_CALL_APPROVED=YES** for exactly one real activity-suggestion request via the UI after the code/deploy/readiness gates; **OWNER_VIDEO_INFERENCE_APPROVED=YES** remains limited to the already approved single silent request if all existing gates pass.

## Addendum 61 — block direct non-Latin Parent activity tokens

- **Status:** APPROVED under the owner's continuing direct instruction on 2026-11-20 to keep fixing the Parent flow until it runs.
- **Approved plan:** `plan/PLAN_REVISION_37_PARENT_ACTIVITY_UNICODE_TOKEN_FILTER_20261120.md`, 6,153 bytes, SHA-256 `860F6CF419C21A64B797B6EA04E5F9AD57786D87B3DFB6093A92BFB076B97ACD`.
- **TASK_APPROVAL.md pre-append pin:** 135,643 bytes, SHA-256 `CCBC93C5C3BF8D90DCAE5B32C909CFF0020DD463902BBB157CF473296202E746`.
- **Evidence:** Revision 36 call `fc-01M7V8T2VAQ488YP3GP9ENJEVM` generated 682 tokens but failed the existing language gate with one non-Latin letter in `no_match_reason`. The API container's current `ModalJsonFunctionClient` has no timeout override and the activity worker allows 450 seconds; the logs do not establish a 120-second timeout. No timeout increase is approved.
- **Authorized:** implement only the M1/M2 changes and exact file boundary in Plan Revision 37; run focused offline tests; deploy only the dev language/audio Modal app; run CPU-only readiness without loading weights or warming GPU; then make exactly one fresh Parent Android UI activity-suggestion request, capped at eight minutes, with no retry or direct worker/API request.
- If that request succeeds, continue one UI activity selection/persistence and one story generation/adult review under the existing approved limits; one silent LTX-2.5 request remains conditional on all existing gates and its exact prior authorization. If the activity request fails, stop inference and prepare another amendment before any further AI request.
- Synthetic-only; reuse the authenticated Parent/profile/run/artwork. Keep all language, schema, quality, safety, age, consent, catalog, activity-selection, story-review, and video-safety gates. No output repair/translation, model substitution, new account/profile/run, drawing inference, fixture in the live flow, DB edit/migration, quota/payment mutation or bypass, `.env`/secret change, SRS change, commit/push, or unrelated service shutdown. Keep the emulator online; stop only task-used services after evidence capture.
- **OWNER_MODAL_CALL_APPROVED=YES** for exactly one fresh real activity-suggestion request via the UI after the code/deploy/readiness gates. Existing story and silent-video authorizations remain only as previously bounded; this addendum does not renew them.

## Addendum 62 — preserve punctuation quality and diagnose the failing field

- **Status:** APPROVED under the owner's continuing direct instruction on 2026-11-20 to keep fixing the Parent flow until it runs.
- **Approved plan:** `plan/PLAN_REVISION_38_PARENT_ACTIVITY_PUNCTUATION_DIAGNOSTICS_20261120.md`, 5,939 bytes, SHA-256 `0D36D94F762BE6B294ACC6DA6EB978BF4A4AE2E510D6E081AD037684B63D60EB`.
- **TASK_APPROVAL.md pre-append pin:** 138,049 bytes, SHA-256 `8E081D7F8F4C87CD5FE1A2C4B71E066F41AAEA58A98C95678AB8A5927623FB5A`.
- **Evidence:** Rev37 call `fc-01M7V9SVGD1WXFXD4FS07TSYA2` generated 746 tokens; JSON completion and EOS checks passed, but the unchanged punctuation gate returned `MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT`. The exact field path was not logged. The API did not time out; the current activity wait limit is 450 seconds.
- **Authorized:** implement only M1/M2 and the exact file boundary in Plan Revision 38; run focused offline tests; deploy only the dev language/audio Modal app; run CPU-only readiness without loading weights or warming GPU; then make exactly one fresh Parent Android UI activity request capped at eight minutes, with no retry or direct worker/API request.
- On success, continue one UI activity selection/persistence and one story generation/adult review under existing approvals; one silent LTX-2.5 call remains conditional on all existing gates and its exact prior authorization. On failure, stop inference until another amendment is approved.
- Reuse the authenticated synthetic Parent/profile/run/artwork. Preserve the punctuation, language, schema, quality, safety, age, consent, catalog, activity-selection, story-review, and video-safety gates. No output repair/translation, regex decoder constraint, token-limit/timeout increase, model substitution, new account/profile/run, drawing inference, live fixture, DB edit/migration, quota/payment mutation or bypass, `.env`/secret change, SRS edit, commit/push, or unrelated service shutdown. Keep the emulator online; stop only task-used services after final evidence capture.
- **OWNER_MODAL_CALL_APPROVED=YES** for exactly one new real activity-suggestion request via the UI after the code/deploy/readiness gates. Existing story/video authorizations remain only as previously bounded; this addendum does not renew them.

## Addendum 63 — constrain Parent activity sentence-ending tokens

- **Status:** APPROVED under the owner's continuing direct instruction on 2026-11-20 to keep fixing the real Parent workflow until it runs.
- **Approved plan:** `plan/PLAN_REVISION_39_PARENT_ACTIVITY_PUNCTUATION_TOKEN_FILTER_20261120.md`, 7,032 bytes, SHA-256 `EF4CA4A5545B7C674CA939C3BFE3504AD89966F2EC946A82560C6E759FDED3F5`.
- **TASK_APPROVAL.md pre-append pin:** 140,366 bytes, SHA-256 `A6D4BF296C95F1E1B03AFF96B526B473213684551B459A3470512EB1D6571501`.
- **Evidence:** Rev38 call `fc-01M7VAJFS2C69SNHZSZA3J0FQ1` generated 693 tokens in 112.178 seconds and completed JSON/EOS, but the unchanged punctuation gate rejected `fallback_activities[0].objective`. The API did not time out. LMFE 0.11.3's free-text fast path includes tokens ending in a quote, so removing the quote from parser characters alone would not enforce punctuation.
- **Authorized:** implement only Plan Revision 39 M1/M2 and its exact file boundary; reuse the existing tokenizer scan and activity-only candidate filtering to block quote-ending tokens in the four required prose fields until their existing punctuation rule is met; retain every existing post-generation, language, schema, quality, age, consent, safety and catalog gate. Run focused offline tests, compilation and `git diff --check`; deploy only the dev language/audio Modal app; run CPU-only readiness; then make exactly one fresh real activity-suggestion request through the authenticated Parent Android UI, capped at eight minutes with no retry.
- On success, continue one UI activity selection/persistence and one story generation/adult review under existing unconsumed approvals. A single silent LTX-2.5 call remains conditional on its exact prior authorization and every gate; this addendum grants no video request. If a gate is not executable, stop before the call. On activity failure, capture sanitized evidence and stop AI calls until a new bounded amendment is recorded.
- Reuse the existing synthetic Parent/profile/drawing/context/StoryRun `ec455bbb-8211-49d5-8cef-9889df809de2`. No new accounts/profiles/runs, drawing inference, real child data, fixture, direct API/worker request, retry, regex constraint, output repair, prompt/schema/limit/timeout change, direct DB mutation/migration, quota/payment bypass or change, `.env`/secret edit, SRS edit, commit/push, or unrelated service shutdown. Keep emulator online; clean up only task-owned services after evidence capture.
- **OWNER_MODAL_CALL_APPROVED=YES** for exactly one fresh activity-suggestion inference via the UI after implementation, offline checks, deployment and CPU readiness. Existing story and silent-video permissions remain only within their prior unconsumed limits; this addendum does not renew them.

## Addendum 64 — type Parent activity sentence endings and log catalog counts

- **Status:** APPROVED under the owner's continuing direct instruction on 2026-11-20: “fix tiếp đi, nào nó chạy đc hết thig dùng”.
- **Approved plan:** `plan/PLAN_REVISION_40_PARENT_ACTIVITY_TYPED_SENTENCES_AND_CATALOG_COUNTS_20261120.md`, 9,731 bytes, SHA-256 `FC7CE36DB3DB41518CD82A2A74C99115E95F8636B514A0BBB88C4495EA33B1FE`.
- **TASK_APPROVAL.md pre-append pin:** 143,158 bytes, SHA-256 `9E0BE0B9B1066EA0D02A4DE52EF337E1EEE8EE5F7BB705514F5583365B3C9AD8`.
- **Evidence:** Rev39's one real Android UI request (`fc-01M7VC15RQPD9XKX454Y9ZJ3RH`) generated 681 tokens in 91.015s, completed JSON/EOS, and failed the unchanged punctuation gate at `fallback_activities[0].objective`. The quote-ending-token filter blocked 46,644 candidates but did not guarantee a sentence terminator. It was not a timeout; no suggestion set was persisted. The catalog-backed path ran, but exact lesson/candidate counts were absent from logs.
- **Authorized:** implement only Plan Revision 40 M1–M3 and its exact file boundary: use typed sentence bodies plus an explicit ASCII-period enum in the worker's internal output, compose the existing normalized response fields before applying unchanged validators, remove the ineffective Rev39 punctuation-token filter, and add privacy-safe integer counts at the documented catalog-filter stages and worker boundary. Run the focused worker/backend tests, Python compilation and `git diff --check`.
- Then deploy only `sketch2life-srs23-language-audio-dev` to Modal `dev`, run CPU-only readiness without weight loading/GPU warm-up, and make exactly one fresh Parent activity-suggestion attempt through the existing authenticated synthetic Parent UI on `emulator-5554`, reusing StoryRun `ec455bbb-8211-49d5-8cef-9889df809de2`; hard cap eight minutes, no retry or duplicate tap. Pass requires a valid persisted response rendered in the real UI. If no catalog activity is relevant, the trace must show zero relevance matches before the worker returns three quality-gated fallbacks.
- On activity success, continue one real UI activity selection/persistence and one story generation/adult review only under already active, unconsumed approvals. One silent LTX-2.5 call remains conditional on the exact pre-existing video authorization being verifiably unconsumed and all prior gates passing; this addendum grants no video allowance. If the activity call fails, stop AI calls until a new amendment is recorded.
- Keep model/checkpoint/provider, prompt policy, token/timeout limits, catalog access, top-12 cap, language/schema/quality/age/consent/safety rules, quota/admission behavior and API/persistence contracts unchanged. No fixture in the live flow, direct API/worker call, new account/profile/run, drawing inference, real child data, database edit/migration, quota/payment mutation or bypass, `.env`/secret/SRS edit, commit/push, or unrelated service shutdown. Preserve pre-existing dirty/staged changes; keep the emulator online and clean up only task-owned services.
- **OWNER_MODAL_CALL_APPROVED=YES** for exactly one fresh activity inference through the real Parent UI after offline checks, deploy and CPU readiness. Existing story/video allowances remain only within their prior unconsumed limits; this addendum does not renew them.

## Addendum 65 — rebuild only the task-local API container

- **Status:** APPROVED under the owner's continuing 2026-11-20 instruction to fix and run the real Parent flow.
- **Approved plan:** `plan/PLAN_REVISION_40A_PARENT_API_RUNTIME_REFRESH_20261120.md`, 2,334 bytes, SHA-256 `BD319DBCCEE73BF83D14B59E1B5AC07221125D733749DF5FE8E4D479CBE74727`.
- **TASK_APPROVAL.md pre-append pin:** 146,516 bytes, SHA-256 `ABDB188B1B87E263825E505B63AD8CE0A5BF595783139A34B7CD930B35C0831F`.
- **Evidence:** `s2l-feat081-rev23-api-1` is healthy but has no source bind mount; its Compose labels point to the existing task Compose files and the shared local `.env`. Backend source edits are therefore not active in this container.
- **Authorized:** using the existing Compose files/overrides and external volumes, rebuild/recreate only service `api` in project `s2l-feat081-rev23` with `--no-deps`, then verify container health and `/health` at `127.0.0.1:58100`. Use the existing `.env` without reading its values into output or changing it. This is a runtime refresh only and does not expand the code boundary.
- Do not restart other services, change Compose/env/secrets, run migration/seed, delete containers/volumes, or add an AI call. The one activity inference remains exactly the call already authorized by Addendum 64. No commit/push.

## Addendum 66 — remove internal catalog wording from fallback UI

- **Status:** APPROVED under the owner's continuing 2026-11-20 request to keep fixing the real Parent workflow.
- **Approved plan:** `plan/PLAN_REVISION_40B_PARENT_ACTIVITY_FALLBACK_COPY_20261120.md`, 3,176 bytes, SHA-256 `94860CB3D5F892BD3F4D719CFFFF79E0D8E71B4FF7931FB39E49BDBBA74B44D1`.
- **TASK_APPROVAL.md pre-append pin:** 147,845 bytes, SHA-256 `1CE631CFD8B4D6BD70567493159CAFECE4FEA190CADDB908584C9C08C6FC416C`.
- **Evidence:** the Rev40 activity inference succeeded and persisted three fallback drafts; the UI displayed the worker's `no_match_reason` verbatim, including the internal key `candidate_activities`.
- **Authorized:** change only the Parent Activity screen fallback copy so drafts show one stable, plain Vietnamese explanation and the per-card raw AI `match_reason` is hidden for `AI_GENERATED_DRAFT`. Preserve catalog reasons, APIs, saved data and all business/quality/safety rules. Run the mobile test suite and typecheck; verify the already-persisted response via Expo Fast Refresh on `emulator-5554` without another activity inference.
- After the copy fix, one real activity selection/persistence and one story generation/adult review remain authorized only under Plan Revision 40's prior unconsumed allowance. This addendum adds no inference allowance. Stop at story review; video remains conditional on exact earlier authorization and all gates.
- No fixtures/mocks, new inference, direct API/worker request, DB edit/migration, quota/payment change, secret/`.env`/SRS edit, unrelated service shutdown, commit or push. Preserve dirty/staged work and keep the emulator online.

## Addendum 67 — refresh Parent screens and add the real video path

- **Status:** APPROVED by the owner's direct 2026-11-20 instruction: “fix các phần chưa phải UI bản mới và thêm luồng vid vào đi”.
- **Approved plan:** `plan/PLAN_REVISION_41_PARENT_UI_REFRESH_AND_VIDEO_FLOW_20261120.md`, 15,842 bytes, SHA-256 `697C841A5D45A61E8CD98A7FD729834F17BD1CA06776053B5984B087F0B90137`.
- **TASK_APPROVAL.md pre-append pin:** 149,518 bytes, SHA-256 `43217EACEB1379033C2E1E9168BB1C74AB67161804F64622BD9FC0A362D7D43A`.
- **Evidence basis:** the real Android Expo story screen displays model-generated character-count/numeric fragments in story prose; the UI now shows an adult-confirmed badge, but server-owned confirmation/hash still must be verified before video dispatch. The last fallback-copy edit was not verified after a real app reload. Parent video capability is unavailable in the client, and Modal `video_app.py` remains a fail-closed scaffold. Existing video-call authority in Addendum 41/42 has not been consumed; the latest Addendum 66 still requires its exact earlier limit and all gates.
- **Authorized:** implement Plan Revision 41 within its §6 path families; audit/fix only active Parent screens that are stale relative to the current UI; fix story-output contamination and worker terminal-log consistency at source; wire the authenticated Parent video API, persistence/admission, LTX-2.5 Modal worker, silent composition, automated validation, and current-style progress/result UI; run focused checks and real Android UI verification; save sanitized evidence.
- **Bounded live calls:** reuse the existing synthetic Parent/profile, source artwork, and saved primary activity. No drawing or activity inference. At most one Qwen story rewrite to correct the visible text defect after offline checks, then stop at the adult review screen. Do not confirm a story on the owner's behalf. After the adult explicitly confirms the exact story hash in the real UI and the backend accepts real quota/compute admission, at most one LTX-2.5 video request is authorized, for only the scenes in that confirmed storyboard. No retries, duplicate tap, warm-up, direct worker/API request, or scene retry. This reaffirms—but does not expand—the one-request video ceiling from Addendum 41/42. `OWNER_VIDEO_INFERENCE_APPROVED=YES` only within these exact conditions.
- **Admission and safety:** no quota/payment mutation or bypass. Rejected admission must stop before Modal. Keep model, schema, age, consent, content, activity, and safety gates fail-closed. No playback before technical, consistency, and automatic safety checks pass. Use silent video only; no TTS/audio in this slice.
- **Data and runtime:** synthetic data only; use the real Expo UI and authenticated backend. Any migration must be additive and applied only after verifying the target is a task-local disposable database. Do not read or edit `.env`/secrets or expose credential/token values. Preserve all pre-existing staged, unstaged, and untracked changes. No commit/push, branch/history operation, or unrelated service shutdown.

## Addendum 68 — connect the existing Modal LTX worker to Parent

- **Status:** APPROVED by the owner's direct 2026-11-20 instruction: “nối cái đó vào đi”. This records the owner's earlier instruction to leave quota management to the other workstream and temporarily allow the button to run.
- **Approved plan:** `plan/PLAN_REVISION_42_PARENT_MODAL_VIDEO_CANDIDATE_INTEGRATION_20261120.md`, 11,000 bytes, SHA-256 `F7BDDCBD1C6C3928096ACFA96CA748A574DEE974658B9333AF4BCEFE1356F9C1`.
- **TASK_APPROVAL.md pre-append pin:** 152,636 bytes, SHA-256 `BC51B28305DC7F8E91532001F5D5CB74BB67B750703364B6D195B1A82E96A923`.
- **Evidence basis:** Modal `dev` app `sketch2life-srs23-dev-video` is deployed with LTX-2.5/L40S functions and FEAT-067 contains real video candidates. FEAT-067 Parent routes currently fail closed before worker dispatch; FEAT-081 has no Parent video UI operations.
- **Authorized:** implement the dev candidate integration using the already deployed worker; server-owned exact confirmed story/drawing input; durable idempotent job/status; private MinIO candidate; authenticated local/test technical-preview stream; current Expo Parent UI progress/resume/preview. A no-quota path is allowed only when `SKETCH2LIFE_ENV` is local/test, an explicit default-off flag is enabled, `ai_provider=modal_dev`, synthetic pilot is enabled, the server-resolved profile is synthetic, and the caller is an authenticated Parent. Production/staging remain fail-closed. The result is `CANDIDATE_READY`, never product `VIDEO_READY`; no safety gate or ordinary product playback is bypassed.
- **Live-call limit:** no Modal warm-up or blind retry. At most one inference through the real Parent UI, and only if a clean, exact confirmed synthetic story is available and all guards pass. This addendum does not authorize story/activity/drawing inference, quota changes, or reusing a previously generated MP4 as a UI fixture.
- **Data/runtime:** do not read or edit the user's `.env` or Modal secrets. Add placeholders and Compose wiring only. Migrations, if needed, must be additive and applied only to the verified task-local disposable database. Preserve all existing worktree changes. No commit/push, broad merge, Modal app stop, or unrelated service shutdown.

## Addendum 69 — include API contract verification for the Parent Modal candidate

- **Status:** APPROVED under the owner's direct 2026-11-20 instruction: “nối cái đó vào đi”. This records the narrow test maintenance required to verify the newly exposed Parent video request/status/preview routes.
- **Approved plan:** `plan/PLAN_REVISION_42_PARENT_MODAL_VIDEO_CANDIDATE_INTEGRATION_20261120.md`, 11,349 bytes, SHA-256 `A6C823A82ED018D53E0227B9D49753D7F61D3BDC623B056083143BB159D95702`.
- **TASK_APPROVAL.md pre-append pin:** 154,901 bytes, SHA-256 `FE48E0FD8291D7BB4C1C120FFCECDF1A3CDA4ACA44A4642517984869C36B4BFA`.
- **Authorized test boundary:** `backend/tests/unit/test_parent_video_candidate_manifest.py`, `backend/tests/unit/test_modal_silent_story_video_adapter.py`, and `backend/tests/contract/test_openapi_contract_catalog.py`. The focused contract check may update the expected mounted operation count for the seven current Parent additions (three topic/subject routes and four video candidate routes). Mobile API contract tests remain within `apps/ui-mobile/**`.
- **Verification only:** run offline unit/mobile/OpenAPI checks. No Modal request, test media, DB migration, account/profile/story creation, quota change, environment/secret access, SRS change, commit/push, or service shutdown is authorized by this addendum.
- All other Addendum 68 guards and its single conditional, UI-only LTX inference limit remain unchanged.

## Addendum 70 — run one real Parent-to-Modal candidate E2E

- **Status:** APPROVED by the owner's direct 2026-11-20 instruction: “chạy thử đi, end to end, ko cần quota”.
- **Approved plan:** `plan/PLAN_REVISION_43_PARENT_VIDEO_CANDIDATE_E2E_20261120.md`, 7,511 bytes, SHA-256 `1FB81813CDE482D736B90E133578B846FACFEF56C29A24BA4855E3D1C2E01F0C`.
- **TASK_APPROVAL.md pre-append pin:** 156,353 bytes, SHA-256 `0111E85C1E0BA3C172E6B7DE3A693B399CDAC4CEF2E98F3C7BC61A30B5939C33`.
- **Preflight:** `emulator-5554` is online at Parent sign-in; task API `127.0.0.1:58100` is healthy but stale and lacks video routes; task Postgres is the local `s2l-feat081-rev23` container using its existing persistent FEAT-081 test volume; Modal `dev` lists the existing LTX video app deployed with zero tasks.
- **Authorized:** refresh only the task API service from the approved worktree source; inspect and apply only necessary additive migrations to the verified task-local database; use the actual Expo Parent UI and synthetic-only data; create a local synthetic Parent account if needed; run at most one inference per required Parent stage and at most one LTX candidate request; skip quota only via the existing local/test synthetic candidate guard. Capture sanitized evidence and correlate API and Modal results.
- **Hard limits:** never use real child data or fixture/provider responses; no legal-consent fabrication; no direct DB business-data inserts, no product `VIDEO_READY` claim, no safety/age/catalog/story gate weakening, no quota-ledger mutation, no retries or duplicate video request, no Modal deployment/warm-up/stop, no unrelated service shutdown, no `.env`/secret access or change, no commit/push.
- If a stage fails, stop downstream inference and record its exact safe failure diagnostics. If adult review finds the story unsuitable or malformed, do not confirm it to force video generation.

## Addendum 71 — load the configured root `.env` for task Compose

- **Status:** APPROVED by the owner's 2026-11-20 clarification: “t có để trong /capstone cái .env r mà?”
- **Approved plan:** `plan/PLAN_REVISION_43_PARENT_VIDEO_CANDIDATE_E2E_20261120.md`, 8,525 bytes, SHA-256 `2BC86D09CAA05DCC462B70EDBDFA8130BCB3AF6F8D66AC08E02BA28AEAEEF560`.
- **TASK_APPROVAL.md pre-append pin:** 158,259 bytes, SHA-256 `F251ACCE5B3C545B3C323F2B6D0143DDA506099D3C970138E9571F4331C9A521`.
- **Finding:** required Firebase/Admin and Modal keys are non-empty in `<local-machine-path>; no `.env` exists in the active worktree root `<local-machine-path> Compose had been started from the worktree without the root file, explaining the missing runtime values.
- **Authorized:** recreate only `api` in `s2l-feat081-rev23` using `docker compose --env-file <local-machine-path> plus the existing task Compose files; keep provider `modal_dev` and the local synthetic candidate gates enabled only for this task. Verify presence/status using booleans only. The Compose process may load the root values, but must not print, copy, or edit them.
- **All other Addendum 70 limits remain:** synthetic data only; no direct secret output; no real child data or fixture responses; at most one inference per required stage and one LTX call; no retry/warm-up/quota mutation; no product-ready claim; no unrelated service shutdown, commit, or push.

## Addendum 72 — deploy missing Parent activity Modal app

- **Status:** APPROVED by the owner's direct 2026-11-20 instruction: “sao lại thiếu, thiếu thì tự chạy thêm powershell up lên đi”.
- **Approved plan:** `plan/PLAN_REVISION_44_LANGUAGE_AUDIO_MODAL_DEPLOYMENT_20261120.md`, 2,393 bytes, SHA-256 `0CA53B3595B75DF0F9E6BB3EDA63737B3EE5CA91CB86CB1A6FB0C65506C28B7F`.
- **TASK_APPROVAL.md pre-append pin:** 159,716 bytes, SHA-256 `9FFF809175CC6D71A5CE47DCFEB3177DBA00CA3517D7E574F07F25A0F3B3F7DC`.
- **Finding:** Rev43's single Parent activity-suggestion attempt failed with `NotFoundError` before a Modal call ID existed. The configured Modal `dev` inventory omitted `sketch2life-srs23-language-audio-dev`, which defines `suggest-parent-activities`.
- **Authorized:** deploy only `deployment/modal/srs_v23/language_audio_app.py` to Modal environment `dev`, then verify the app appears in inventory and record sanitized evidence.
- **Not authorized by this addendum:** invoking any Modal function or inference, readiness/model-load/warm-up calls, reattempting Parent activity suggestion, continuing story/video E2E, changing `.env`/secrets/Volumes/database/quota, or modifying any other Modal app. All other Rev43 limits remain in force.

## Addendum 73 — one UTF-8-corrected deploy retry

- **Status:** APPROVED as a narrow continuation of the owner's direct Addendum 72 instruction to deploy the missing app.
- **Approved plan:** `plan/PLAN_REVISION_44_LANGUAGE_AUDIO_MODAL_DEPLOYMENT_20261120.md`, 2,583 bytes, SHA-256 `36FCBAF5C2404DDFFD6D25634316A51164115894AAE7F50BB50DB9DFA7D9F43E`.
- **TASK_APPROVAL.md pre-append pin:** 160,976 bytes, SHA-256 `CF8E275D289A285FA7BA2105582688F9277BBC3921134DF4AA4DC20D1C37A97E`.
- **Reason:** first deploy command exited because the Windows console could not encode Modal's `✓` output; the app record was created but appeared `stopped` in the read-only inventory check.
- **Authorized correction:** set `PYTHONUTF8=1` for the Modal CLI and repeat the deployment exactly once for `deployment/modal/srs_v23/language_audio_app.py` in `dev`.
- **All other Addendum 72 boundaries remain:** no Modal function invocation, readiness call, model load, GPU warm-up, AI request, E2E continuation, or other app/resource change.

## Addendum 74 — resume the approved Parent E2E after deployment

- **Status:** APPROVED under the owner's still-active direct request to run the Parent workflow end to end without quota, with the follow-up instruction to deploy the missing worker.
- **Approved plan:** `plan/PLAN_REVISION_45_RESUME_PARENT_E2E_AFTER_MODAL_DEPLOY_20261120.md`, 3,676 bytes, SHA-256 `441BB0AC6FA5BDB0401E6AA62EBC9A199982840D90EF5AD3EB6AEF0BA607FF72`.
- **TASK_APPROVAL.md pre-append pin:** 161,999 bytes, SHA-256 `1DC4E796333F7125A3028D775AAA586442FA6E5B12A98FA12B83DEC6CB112005`.
- **Deployment status:** `sketch2life-srs23-language-audio-dev` is now deployed in Modal `dev`, with zero tasks. Rev43's activity request failed before Modal accepted a call ID, so it performed no model inference.
- **Authorized continuation:** reuse only the existing synthetic Parent/profile/StoryRun/drawing; one actual activity suggestion inference through the real UI, one story inference if activity persists and is selected, and at most one private silent LTX candidate if story review/hash confirmation and all existing local/test synthetic gates pass. No drawing re-inference. The adult test operator must inspect the exact story and not confirm an unsuitable/malformed/mismatched result.
- **This addendum supersedes only the deployment-only/no-E2E boundary of Addenda 72–73 after successful deploy.** No additional deployment retry, readiness/warm-up/model-load call, activity retry after this one actual inference, story/video retry, quota access/mutation, gate bypass, other app/resource change, commit, or push is authorized.

## Addendum 75 — one fresh synthetic Parent account and video E2E

- **Status:** APPROVED by the owner's direct 2026-11-20 instruction: “tự đký và ấy đi”.
- **Approved plan:** `plan/PLAN_REVISION_46_FRESH_PARENT_ACCOUNT_VIDEO_E2E_20261120.md`, 3,485 bytes, SHA-256 `027B53B8AA50C0E341EB578CCB378AE15EE4E852FFA298216A5DC7841CCB7245`.
- **TASK_APPROVAL.md pre-append pin:** 163,607 bytes, SHA-256 `8366D6641C599DE190FC8F734303BF6D09EFBD5FFEFB28F7084F4B588B02644B`.
- **Reason:** after the Expo app was restarted, the previous Parent session was unavailable. The prior confirmed run belongs to that Firebase UID; the task database has no Parent seed identity, so a new account cannot access that run.
- **Authorized:** register exactly one new synthetic Parent through the real Expo UI, create one synthetic 60-month profile and one fresh StoryRun, reuse the existing generated synthetic turtle artwork via Android Photo Picker, perform at most one inference each for drawing understanding, activity suggestion, and story generation, then at most one silent LTX candidate request after exact-story adult review/confirmation. Stream the authenticated private preview if a candidate is ready.
- **Hard limits:** credentials remain ephemeral and are never printed or committed; the Firebase test account remains after the run. No real child data, fabricated consent, direct API/worker bypass, direct business DB writes, quota/billing read or mutation, payment, quota bypass, repeated inference, retry, warm-up, extra deployment, other app/resource change, `.env`/secret/SRS change, commit, or push. Failure or unsuitable story stops downstream calls.
- **OWNER_MODAL_CALL_APPROVED=YES** for one fresh drawing call, one activity call, one story call, and at most one silent LTX candidate, only through the real UI and the existing local/test synthetic-only guard. No product `VIDEO_READY` claim.

## Addendum 76 — correct Firebase token clock-skew rejection and resume the same E2E

- **Status:** APPROVED as the narrow runtime repair required by the owner's active 2026-11-20 instruction to register and complete the real Parent flow: “tự đký và ấy đi”.
- **Approved plan:** `plan/PLAN_REVISION_47_FIREBASE_IAT_SKEW_FIX_20261120.md`, 3,300 bytes, SHA-256 `796F278FBBF514D99B0310C2CEF926AC721B02CE19EECE4F4FBD68DB46296E29`.
- **TASK_APPROVAL.md pre-append pin:** 165,511 bytes, SHA-256 `E2745E261CD41B41A23C5F688606413CFFB4EAD5C093CDFA2D74DD1B6E3BAFB4`.
- **Evidence:** Firebase accepted the synthetic account's credentials. An immediate `/api/auth/v1/me` call failed with `INVALID_TOKEN` when token `iat` was 11 seconds ahead of the API clock and verifier tolerance was 10 seconds; the same token returned 200 after 3 seconds when measured skew was 7 seconds. No credentials or token material are included in evidence.
- **Authorized:** change only `FIREBASE_AUTH_CLOCK_SKEW_SECONDS` from 10 to 30 in `backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py`; add a focused verifier regression test in `backend/tests/unit/test_firebase_token_verifier.py`; run focused auth checks and repository security validation; rebuild/recreate only `s2l-feat081-rev23-api-1`; sign in through the real Expo UI with the already-created account; continue Addendum 75's existing synthetic Parent flow and bounded Modal/video request limits.
- **All other Addendum 75 boundaries remain:** no second account/profile/run, real child data, consent fabrication, direct API/worker bypass for product flow, quota/billing read or mutation, payment, quota bypass, repeated inference, AI/video retry, warm-up, extra deployment, unrelated app/resource change, `.env`/secret/SRS change, commit, or push.

## Addendum 77 — corrected Plan Revision 47 pin

- This correction is documentation-only. The first Plan Revision 47 draft included an absolute local worktree path, which the repository security validator rejects. That path was removed; scope and acceptance criteria are unchanged.
- **Corrected approved plan:** `plan/PLAN_REVISION_47_FIREBASE_IAT_SKEW_FIX_20261120.md`, 3,257 bytes, SHA-256 `D0E6AD4CB1DBA33FAE361DDCE5C05C1289B9562A072DDFF488F9A99F050AFB12`.
- **TASK_APPROVAL.md pre-append pin:** 167,326 bytes, SHA-256 `3F0A5DB3D67C086C296DDB6198957D24A60AA85875A58DDC00065D2940A10EC6`.
- Addendum 76's approved scope and all Addendum 75 runtime limits remain unchanged.

## Addendum 78 — diagnose and recover one Parent profile-create DB failure

- **Status:** APPROVED as a bounded continuation of the owner's active 2026-11-20 request to register and complete the real Parent flow.
- **Approved plan:** `plan/PLAN_REVISION_48_PARENT_PROFILE_DB_ERROR_RECOVERY_20261120.md`, 2,463 bytes, SHA-256 `AFBBD774289E1154B98226420701C6888BCC5B4CF4B7019683C799D2BEF9B9E8`.
- **TASK_APPROVAL.md pre-append pin:** 168,004 bytes, SHA-256 `92D70A35BE39F3489CC114F7989B1520EA10375217B8A3253417F79FCD33136C`.
- **Evidence:** the real UI's single Parent profile-create call returned 503 `PARENT_STORE_UNAVAILABLE`; sanitized API log identifies SQLAlchemy `DataError` but does not identify the driver exception/SQLSTATE. No AI inference was sent and no profile was returned.
- **Authorized:** add safe underlying exception type/module/SQLSTATE to the Parent DB failure log in `backend/src/sketch2life/interfaces/http/parent_runtime.py`; inspect task schema read-only; make at most one localized correction in Parent profile repository/runtime if the sanitized diagnosis isolates a cause; rebuild only `s2l-feat081-rev23-api-1`; verify the profile list remains empty in the authenticated app; replay the same UI command at most once using retained idempotency; continue Rev46 only after create + read-back pass.
- **No migration or direct DB business-data edit is authorized.** No AI/video request is authorized until the profile is active and read back. All remaining Addendum 75 limits remain unchanged.

## Addendum 79 — clarify Parent video loading and make one owner-directed LTX attempt

- **Status:** APPROVED by the owner's direct 2026-11-20 instruction: “gọi thửu vid đi” and “fix nào gọi đc nhé, ngoài ra thì thêm loading state rõ hơn cho cái này dùm”.
- **Approved plan:** `plan/PLAN_REVISION_49_VIDEO_LOADING_AND_ONE_CANDIDATE_TEST_20261120.md`, 9,137 bytes, SHA-256 `0F60012C7191461C30DBFE1D5C963370FC971E77CD659E8F7EC70C6D2B567D94`.
- **TASK_APPROVAL.md pre-append pin:** 169,524 bytes, SHA-256 `6B39C810A4718B8D6F2E0D91366251C757D65F57BD77FBD048A24FE0AC758CB5`.
- **Known review issue:** the current synthetic story revision contains mixed-script text and awkward age phrasing, as recorded in the Rev46 evidence. The owner explicitly directs one technical video test anyway.
- **Authorized:** improve the Parent video loading state using actual candidate states and the existing mobile design tokens; run focused checks; confirm the exact displayed story revision through the real UI solely to advance this one owner-directed synthetic technical test; submit at most one Parent UI candidate request for StoryRun `ff1021f5-e9e6-4343-9da3-ced08ad9de69`; poll status through the UI; open its authenticated technical preview only if ready. A narrow pre-dispatch code fix is allowed only if required to make this request work and must preserve every existing security/configuration guard.
- This addendum supersedes Addendum 75's “unsuitable story stops downstream” condition **only for the single synthetic candidate attempt named above**. It does not mark the story acceptable or change SRS/product quality, consistency, safety, or playback gates.
- **Hard limits:** no story/image regeneration, no second account/profile/run, no second candidate submit, no LTX retry after a Modal call is accepted or its outcome is uncertain, no direct API/worker bypass, no guard/quality/safety relaxation in code, no quota/billing access, no `.env`/secret/SRS/migration change, no extra Modal deploy/warm-up/app stop, and no commit/push. If the one candidate is rejected or fails, record the safe reason and stop.
- **OWNER_MODAL_CALL_APPROVED=YES** for at most one real LTX-2.5 inference through the existing local/test synthetic-only Parent UI path for this run. This is a technical experiment only; no claim of product readiness or story quality is authorized.

## Addendum 80 — one fresh synthetic Parent signup and UI video test

- **Status:** APPROVED by the owner's direct 2026-11-20 instruction: “thì m đký đi, chạy đi, nào nối đc, test đc trên UI thì ngừng”. This supersedes Addendum 79's prohibition on creating a new account/profile/run only for the single synthetic flow below.
- **Approved plan:** `plan/PLAN_REVISION_50_PARENT_SYNTHETIC_REGISTRATION_AND_VIDEO_UI_E2E_20261120.md`, 7,160 bytes, SHA-256 `74CE8AD21191B58BFC8D98405C493E78F730652123498F0DC9A315D542844E87`.
- **TASK_APPROVAL.md pre-append pin:** 171,913 bytes, SHA-256 `65482D624B51DDBB70DBF85E3D99EFAC8DE1983CE540DDDDA0F14F4C4E854CA5`.
- **Authorized:** register exactly one fresh synthetic Parent via the real Expo UI; create at most one synthetic profile and one StoryRun through that UI; reuse the existing synthetic turtle artwork; run each needed drawing/activity/story inference at most once; if the story passes normal Vietnamese, age-fit, contract, and safety review, submit at most one silent video candidate via the real UI. Stop at the first terminal blocker or after the UI shows the candidate result. No new story-quality override is granted by this addendum.
- **Candidate flag:** the owner authorizes setting only `SKETCH2LIFE_PARENT_VIDEO_DEV_CANDIDATE_ENABLED=true` in the task API process environment for the single request, while `SKETCH2LIFE_ENV=local`, `SKETCH2LIFE_AI_PROVIDER=modal_dev`, and existing synthetic-pilot/identity/ownership guards remain unchanged. Do not edit `.env` or secrets; restore the effective candidate flag to `false` immediately after the result or before stopping.
- **Hard limits:** no real child data, fabricated consent, fixture/preview-harness result, direct API/worker bypass, direct business DB edits, quota/billing read/write, payment, quota bypass, more than one new account/profile/run, any AI retry, a second candidate submission, or LTX retry after accepted/uncertain dispatch. No password reset/account deletion, extra Modal deployment/warm-up/stop, unrelated service shutdown, SRS/migration change, commit, or push. If signup requires accepting legal terms, stop before acceptance and hand control to the owner.
- The earlier Addendum 79 single-run test exception is not carried over. The new story must pass the existing adult review before the candidate request. A technical candidate does not imply product-quality, safety, or playback approval.

## Addendum 81 — repair Parent Firebase/backend auth, preserve seeds, and rerun Android E2E

- **Status:** APPROVED by the owner's direct 2026-11-21 instruction to inspect and fix Firebase plus backend account synchronization, Google continuation, audit seed accounts, remove only test accounts created by this agent, and rerun the Parent flow.
- **Approved plan:** `plan/PLAN_REVISION_51_PARENT_FIREBASE_BACKEND_GOOGLE_E2E_20261121.md`, 12,031 bytes, SHA-256 `3D5A4452D7E6892A7A138130964DAE1D0EA83D7911562CFE1687A509E76F745D`.
- **TASK_APPROVAL.md pre-append pin:** 174,358 bytes, SHA-256 `8282D399858801F1436868F615928A4EFF583FDCF8AD426CEF99B8E15FF175F5`.
- **Authorized backend/mobile scope:** diagnose the prior one-shot signup's HTTP 503 before any retry; implement safe Firebase↔BE1 registration recovery and diagnostics; support server-controlled first-time Google Parent provisioning; correct UI success/cancel/failure routing; add focused backend and mobile coverage; and continue one real ADB-driven Parent E2E. Backend role assignment must derive subject/issuer from a verified Firebase token; clients may not send role or UID. Preserve generic cross-scope errors and all SRS identity/security gates.
- **Seed boundary:** inventory Docker and Firebase seed data read-only. Preserve every existing seed identity and entity. Cleanup is authorized only for the exact synthetic account created by this agent for this task, after matching its Firebase identity to its BE1 subject; purge this run's own generated profile/story/media through supported lifecycle operations first. If safe correlation or cleanup is unavailable, stop cleanup and leave unrelated data untouched. No seed user may be removed merely because it looks synthetic or test-like.
- **E2E limit:** use `emulator-5554` and ADB, the actual Expo UI, and the existing synthetic artwork. Reuse the exact identity from the prior 503 if it exists; create no more than one new account if it is proven absent. At most one profile/run, one inference per required AI workload, and one video candidate request under Rev50/Addendum 80's approved local synthetic-only flag and gates. No quota/payment access, mutation, or bypass; no direct API/worker bypass; no real child data or fabricated consent; no fixture/preview harness; no Modal deploy/warm/stop; no `.env` or SRS edit; no unrelated service changes; no commit/push.
- Parent self-registration email-verification behavior is not silently changed; follow the canonical FEAT-063 SRS and record the open requirement if implementation needs an owner decision.

## Addendum 82 — extend Rev51 to the BE1 database preflight

- **Status:** APPROVED by the owner's explicit 2026-11-21 direction: “check cả backend để xem có bug hay ko đấy, check cả backend và fix, ko chỉ sửa frontend”.
- **Supplemental plan:** `plan/PLAN_REVISION_51A_BE1_DATABASE_FAILURE_DIAGNOSTICS_20261121.md`, 2,702 bytes, SHA-256 `FC78A950AAFA9314ED6FFA3E5593E25E651B58C9765860A0CC90FFD82EDBA9AB`.
- **TASK_APPROVAL.md pre-append pin:** 176,938 bytes, SHA-256 `CA2D697D63E1BE2F3AE8EF1C71F3E1E730A29D88AC0D5DDC96E823C35B7158B8`.
- **Authorized addition:** inspect/fix the DB connectivity diagnostic in `backend/src/sketch2life/interfaces/http/be1_runtime.py`; add focused tests for its existing safe 503 behavior; use the already existing task-local PostgreSQL container and volume for this E2E. It may be started and checked, but must not be recreated, reset, migrated, reseeded, or cleared under this addendum.
- All Addendum 81 limits apply. Seeds and all pre-existing accounts/entities remain untouched.

## Addendum 83 — include Parent identity synchronization in the OpenAPI contract

- **Status:** APPROVED by the owner's direct 2026-11-21 request to fix backend registration/login and Google authentication, not only the UI.
- **Supplemental plan:** `plan/PLAN_REVISION_51B_AUTH_SYNC_OPENAPI_CONTRACT_20261121.md`, 1,692 bytes, SHA-256 `DC9CB3F5C919225963E8C9684D36EF85DA0BD31C877DBF2C3104B249C11FA03D`.
- **TASK_APPROVAL.md pre-append pin:** 177,976 bytes, SHA-256 `FA28E4A0AA85709F3A6AE775B8EC8C6D38B19A53209DECA4FE9C535D2A9DBADF`.
- **Authorized addition:** publish `POST /api/auth/v1/registrations/complete` in the explicit OpenAPI projection and add focused contract assertions for authentication, response schema/statuses, and no client-controlled role/UID fields.
- Plans 51/51A and Addenda 81/82 remain in force, including the seed preservation and exact-own-account-only cleanup boundary.

## Addendum 84 — Parent SVG guide backend contract and optional-flow recovery

- **Status:** APPROVED by the owner's direct 2026-11-21 instruction to check and fix backend defects as well as frontend behavior.
- **Supplemental plan:** plan/PLAN_REVISION_51C_PARENT_SVG_GUIDE_BACKEND_E2E_20261121.md; SHA-256 $planHash.
- **TASK_APPROVAL.md pre-append SHA-256:** $approvalHash.
- **Authorized:** add safe correlation/diagnostics and focused contract tests for the mounted Parent SVG-guide endpoint; preserve its typed no-match response; make missing optional guide non-blocking in the real Parent UI; resume the same ADB E2E and inspect subsequent backend/API results.
- **Limits:** no reactivation/dispatch of retired guide workload, no new Modal deployment/lifecycle operation, no seed/account mutation, migration/reseed, quota/payment, secret/.env/SRS edits, unrelated route changes, commit or push. Existing Addendum 81 E2E and account-preservation limits continue.

## Addendum 85 — exact Parent sea-turtle source alias

- **Status:** APPROVED under the owner's direct 2026-11-21 instruction to check and fix backend defects, including the catalog resolution found during the real Parent flow.
- **Supplemental plan:** plan/PLAN_REVISION_51D_PARENT_SEA_TURTLE_GUIDE_ALIAS_20261121.md; SHA-256 $planHash.
- **TASK_APPROVAL.md pre-append SHA-256:** $approvalHash.
- **Authorized:** add exact sea-turtle aliases to the existing OpenMoji turtle manifest, refresh its integrity pin, add focused backend resolution tests, verify the real Parent API route, and resume the same UI flow.
- **Limits:** do not broaden matching to arbitrary substring heuristics; do not alter SVG geometry/license or invoke AI/Modal for a catalog hit. No other asset, route, migration, seed, quota, secret/.env/SRS change, commit or push. Addenda 81 and 84 remain in force.

## Addendum 86 — restore the pinned OpenMoji license bytes

- **Status:** APPROVED under the owner's direct 2026-11-21 instruction to check and fix backend defects.
- **Supplemental plan:** plan/PLAN_REVISION_51E_OPENMOJI_LICENSE_SOURCE_INTEGRITY_20261121.md; SHA-256 $planHash.
- **TASK_APPROVAL.md pre-append SHA-256:** $approvalHash.
- **Authorized:** restore the one missing final LF to the bundled OpenMoji CC BY-SA 4.0 legal-code file and verify it matches the existing official SHA pin; then run focused SVG tests and continue the same real Parent run.
- **Limits:** do not replace/reformat license contents or change pins/metadata; no other dataset/source edits, Modal dispatch, seed/account mutation, migration, quota, secret/.env/SRS edit, commit or push. Addenda 81, 84 and 85 remain in force.

## Addendum 87 — recover a proven pre-dispatch Parent drawing failure

- **Status:** APPROVED by the owner's direct 2026-11-21 instruction to inspect and fix backend behavior, not only frontend behavior, and continue the Parent flow.
- **Supplemental plan:** `plan/PLAN_REVISION_51F_PARENT_DRAWING_PRE_DISPATCH_RECOVERY_20261121.md`, 6,128 bytes, SHA-256 `ccb13c6f18a1530264dcedac113719237c897d3f7f0015e483cc758bd920c1d5`.
- **TASK_APPROVAL.md pre-append bytes/SHA-256:** 181,542 / `d14d04557d65fed3c2ae3bff9a9eb5fbe24991285be3d19719dea7fad9d73e20`.
- **Authorized:** add safe typed diagnostics for Parent drawing-analysis failures; distinguish explicitly allowlisted failures proven to occur before upload/AI dispatch; make the real Parent UI offer at most one manual retry of the same selected image on the same StoryRun, and only after a read-back confirms `current_input_revision == 1`; add focused backend/mobile tests; restart only this task's API when needed; use the existing task-local MinIO/PostgreSQL/ClamAV services and existing root `.env` via explicit Compose `--env-file`; resume the current ADB-driven synthetic flow.
- **Failure boundary:** do not retry generic network errors, timeouts, uncertain/accepted Modal outcomes, worker/model errors, or any run whose input revision advanced. Do not create another account, profile or StoryRun. The previously observed drawing 503 left revision 1 and no upload session; after MinIO restoration, exactly one UI recovery attempt is authorized. Existing Addenda 80/81 per-workload AI and one-video-candidate limits remain in force; story adult review and every existing safety/quality gate remain mandatory before any candidate request.
- **Data/security boundary:** preserve all seeds and pre-existing entities; no direct API/worker bypass, business DB mutation, migration/reset/reseed, quota/payment access, fabricated consent, real child data, or gate relaxation. `.env` values may be consumed by Compose but must not be printed, copied or edited. No Modal deploy/warm/stop, unrelated service change, commit or push. Addendum 81's exact-own-test-account cleanup rule remains unchanged.

## Addendum 88 — reject incomplete Parent activity suggestions

- **Status:** APPROVED by the owner's direct 2026-11-21 instruction: “check cả backend và fix, ko chỉ sửa frontend”.
- **Supplemental plan:** `plan/PLAN_REVISION_52_PARENT_ACTIVITY_SENTENCE_COMPLETENESS_20261121.md`, 4,279 bytes, SHA-256 `E9C91BD4258A2E8032F71AE3654B1AAA6717C44D7BAF2A6C80BCF0289AF13B0F`.
- **TASK_APPROVAL.md pre-append bytes/SHA-256:** 183,691 / `0327763CEBB9ECBD693E6215A8E99A3E18870655A04A943876D64DA18BB6449D`.
- **Authorized:** add conservative Vietnamese sentence-tail validation to the Parent activity fallback worker parser and matching backend quality gate; add focused offline worker/backend tests; preserve and report the current malformed result without selecting it or proceeding to story generation.
- **Limits:** the current activity inference has already completed: no activity retry/regeneration and no second Modal request; no Modal deploy/warm/stop; no mutation/deletion of the saved activity snapshot; no API/worker bypass, migration/reset/reseed, new account/profile/run, quota/payment, consent/security/safety gate relaxation, `.env`/secret/SRS change, unrelated service shutdown, commit or push. Addenda 80–87 remain in force.

## Addendum 89 — prominent Parent AI loading and bounded real E2E continuation

- **Status:** APPROVED by the owner's direct 2026-11-21 request to continue instead of stopping at the activity failure, make AI loading states clear, fix the backend as well as frontend, and run the Parent flow end to end without quota management.
- **Supplemental plan:** `plan/PLAN_REVISION_53_PARENT_LOADING_BACKEND_E2E_20261121.md`, 10,728 bytes, SHA-256 `03D810556A5EC1E082E0125E6166D93EBF25C1C295224CCA894AD756D6B53F90`.
- **TASK_APPROVAL.md pre-append bytes/SHA-256:** 184,939 / `A8B45EB7C8215D5A22F66223A5632985DD6D7CEED98C65CBB7DAE06AA85C6DBA`.
- **Authorized UI work:** make the Parent drawing-analysis, activity-suggestion and story-generation waits prominently visible with honest elapsed time, clear Vietnamese copy and disabled duplicate actions; retain video progress based on server states and improve request-dispatch visibility if needed; map quality-gate failure to an explicit safe message; add focused tests. No fake percentage or invented backend phase.
- **Authorized backend/Modal work:** apply the already documented Vietnamese incomplete-sentence checks to the worker and backend fallback gate, add focused tests, deploy only `sketch2life-srs23-language-audio-dev` in Modal `dev`, and rebuild only the task API service without touching its database/volume. Check health and route readiness before live requests.
- **Authorized E2E:** use the real Expo app on `emulator-5554` through ADB; reuse the existing synthetic Parent identity, profile and synthetic turtle drawing source; create at most one new StoryRun. Preserve the prior malformed run/suggestion snapshot. One drawing inference; up to two activity fallback inferences total, where request two is allowed only after a definite quality-gate rejection and never after timeout/uncertain dispatch; one story inference with no rewrite; at most one silent video candidate after adult review/confirmation and existing gates. No fixture/preview-harness result or direct API/worker bypass.
- **Quota:** do not call/read/mutate quota or payment APIs. For the candidate only, reuse the existing local/test synthetic-only configuration already authorized by Addendum 80; do not weaken identity, admission, safety, or production quota rules. Stop if existing guards cannot admit the technical candidate without a new policy change.
- **Limits carried forward:** no real child data, fabricated consent, new account/profile, account/seed deletion, direct business-DB edits, migration/reseed/reset, secret or `.env` access/output/edit, SRS edit, unrelated service shutdown, AI retry beyond the exact caps above, story rewrite, video retry, or commit/push. After the run, stop only the task Modal apps used here if they have no other active task. Addendum 89 supersedes Addendum 88 only as to deploying the fix and making the bounded new activity request; other Addenda 80–87 constraints remain in force unless expressly bounded above.

## Addendum 90 — pass story operation into loading UI

- **Status:** APPROVED as a narrow implementation detail of Addendum 89, whose owner-approved objective is to make each Parent AI loading state clearly describe the actual operation.
- **Updated plan:** `plan/PLAN_REVISION_53_PARENT_LOADING_BACKEND_E2E_20261121.md`, 11,004 bytes, SHA-256 `6E1225374E8F84EA91F95602D5F82E4A96FEF776B171FDBB6F0FD0E32189CE00`; this replaces the plan hash recorded in Addendum 89.
- **TASK_APPROVAL.md pre-append bytes/SHA-256:** 187,929 / `12B9398CC3942935D11164B0A5A4E844899B239A479F94EB717DB7BC12D32FEC`.
- **Added allowed file:** `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx`, only to pass the existing `story`, `rewrite`, or `confirm-story` busy operation to `StoryScreen` for truthful loading copy. No workflow/API behavior changes are authorized by this addendum.
- All Addendum 89 run, deployment, quota, data, safety, security and publication limits continue unchanged.

## Addendum 91 — release the exact malformed synthetic run lock through Parent UI

- **Status:** APPROVED as necessary to carry out the owner's direct request to continue fixing and run the Parent flow end to end. This supplements Addenda 89–90 and does not authorize a second profile or account.
- **Approved plan:** `plan/PLAN_REVISION_53_PARENT_LOADING_BACKEND_E2E_20261121.md`, 11,462 bytes, SHA-256 `B342CE7FCD25809E6B1E81C7212BE42ADAFD505CABCC365FB6944AC87DF2A43E`.
- **TASK_APPROVAL.md pre-append bytes/SHA-256:** 188,908 / `FFF4D6BCCC7C7F8F55A9DA39C609CCC79E43A5C513217D417622D3AEB4189C6B`.
- **Authorized:** only if the exact previously reported synthetic run `5d7eae48-19e5-4568-8c36-69f82a381f90` still prevents the approved new run, close that run using its authenticated Parent UI lifecycle action. Preserve its StoryRun record, activity suggestion snapshot, assets, and receipts. Verify the UI/API reports the retained terminal/pending state and the owner/profile lock is released before proceeding.
- **Stop conditions:** if the UI action would delete data immediately, if run identity cannot be confirmed, if authentication/ownership is uncertain, or if the lock remains held, stop and report. No direct API call, database write, row edit, or deletion is authorized by this addendum.
- All other Addendum 89 limits remain unchanged: the bounded inference budget, existing safety/admission gates, no quota/payment access, no new account/profile, no real-child data, no unrelated service shutdown, and no commit/push.

## Addendum 92 — recover activity worker quality failure and continue the bounded UI flow

- **Status:** APPROVED by the owner's direct 2026-11-21 instruction to keep fixing the Parent flow, make loading states clear, and continue until the real end-to-end flow works without quota/payment blocking.
- **Updated plan:** `plan/PLAN_REVISION_53_PARENT_LOADING_BACKEND_E2E_20261121.md`, 14,228 bytes, SHA-256 `C6C2AFC343BD726DE7A004C685657C1591014ABD5D9E6A35D520D0ED6119BFE8`.
- **TASK_APPROVAL.md pre-append bytes/SHA-256:** 190,446 / `7543D9F651EF217339AFFF256415DC7841B1A310B0C15694CB4E6E17D2D9C25E`.
- **Observed failure:** the first activity inference on synthetic StoryRun `08657e31-ebd7-4a07-8f9b-5929b4dff23b` ended definitively with worker code `MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT` at `fallback_activities[0].objective`; no generated text was retained. This is a quality rejection, not an unknown dispatch.
- **Authorized:** shorten fallback sentence schema bounds while retaining all quality/safety gates; clarify the worker prompt with concise complete-sentence patterns; collect terminal Modal logs for at most three seconds after a definite failed `call.get()` for `parent.activity.suggest`; preserve allowlisted typed output-quality worker errors; map the exact incomplete-text error to safe API code `PARENT_ACTIVITY_QUALITY_GATE_REJECTED` and diagnostic `ACTIVITY_TEXT_INCOMPLETE`; add focused tests; deploy only `sketch2life-srs23-language-audio-dev`; rebuild only task API without database/volume changes; after health checks, make at most the one remaining activity inference from the real Android UI on that same StoryRun.
- **Boundaries:** do not loosen/skip/repair the quality gate, fabricate activities, retry after timeout or uncertain dispatch, or send a third activity inference. Continue to one story inference and at most one silent video candidate only if activity selection and adult story review pass, within Addendum 89's existing limits. Do not access quota/payment APIs, create accounts/profiles/runs, change consent/safety/admission, edit DB or `.env`, expose secrets or raw model text, stop unrelated Modal apps/services, commit, or push. Addenda 89–91 remain in force except for this narrowly authorized quality/logging fix and the one bounded activity continuation.
## Addendum 93 — continue until the Parent flow completes after repeated quality-gate rejection

- **Status:** APPROVED under the owner's direct 2026-11-21 instruction: “fix tiếp ... nào chạy được end to end ... không quota thì tính”; the owner specifically directs continued repair and full UI E2E, with quota/payment management excluded as a blocker.
- **Updated plan:** `plan/PLAN_REVISION_53_PARENT_LOADING_BACKEND_E2E_20261121.md`, 15,882 bytes, SHA-256 `DD2C84603D27D154F10933A3AC122D0B2C9E3F3835F78C3ACA610ABED05132D4`.
- **TASK_APPROVAL.md pre-append bytes/SHA-256:** 192,751 / `F0D36802182C9592C21D996A5E7C82A553533E37247B189A72172E59633154ED`.
- **Observed evidence:** two UI-dispatched activity fallback calls on the same synthetic run ended definitively with `MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT` at `fallback_activities[0].objective`, after 104,741 ms and 116,124 ms. Neither timed out or had uncertain dispatch; neither raw generated text nor input content is retained.
- **Authorized:** make a substantive prompt/schema correction using concise complete Vietnamese sentence forms and tighter bounds (objective <=36 characters including period; preparation, each instruction sentence, and safety <=46); retain every completeness, age, topic, language, quality, consent, and safety gate; extend only `parent.activity.suggest` terminal-log collection to a bounded 10 seconds after a definite failed wait; preserve allowlisted typed worker error codes and the safe UI/API mapping; update and run focused tests; deploy only the language-audio Modal app and rebuild only task API; continue the real Android UI flow on the same StoryRun.
- **Inference cap:** up to three further activity fallback inferences (five total including the two already consumed), each only after a substantive source fix, focused test pass, and healthy deploy. Dispatch only via an explicit adult action in the UI. Stop after the first accepted activity set, or immediately on a timeout, unknown outcome, or any different failure. If activities pass, continue with one UI-selected activity, one story inference and adult review, then at most one silent video candidate under existing gates. No automatic retry, story rewrite, or video retry.
- **Boundaries:** no quota/payment API calls; no safety, consent, or admission bypass; no direct API/worker inference, database edits, migration, account/profile/run creation, seed deletion, raw text/image/secret output, unrelated Modal/service shutdown, commit, or push. Preserve all failed suggestion sets and snapshots. Addenda 89–92 remain in force except the narrow continuation cap superseded here.
## Addendum 94 — classify incomplete activity sentence tails safely

- **Status:** APPROVED under the owner's direct 2026-11-21 instruction to keep fixing and continue the real Parent flow until end-to-end completion.
- **Updated plan:** `plan/PLAN_REVISION_53_PARENT_LOADING_BACKEND_E2E_20261121.md`, 16,247 bytes, SHA-256 `F7F902597E1F2E14CCB48DF4CE9BD39C21F3A8CF2E4253932576F5A1F23FCA91`.
- **TASK_APPROVAL.md pre-append bytes/SHA-256:** 195,402 / `BFC58817D1DC0469CED73D8FDE3027293B6E97588D2E43526184D1E986A7FE05`.
- **New evidence:** the third activity call also ended definitively with `MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT`, now at `fallback_activities[1].instructions_text.first_sentence` after 70,607 ms. The API surfaced `PARENT_ACTIVITY_QUALITY_GATE_REJECTED` and diagnostic `ACTIVITY_TEXT_INCOMPLETE` correctly.
- **Authorized:** tighten sentence bounds (objective <=32, preparation <=42, each instruction sentence <=32, safety <=42 characters including punctuation); add short complete Vietnamese instruction examples; add safe worker diagnostics limited to known field path, character count, and one of the enumerated tail/terminator reason categories; parse these Modal events into backend structured logs without retaining generated text; add focused tests; deploy only the language-audio Modal app; rebuild only task API; run one more explicit activity request from the real UI on the same StoryRun after tests and health checks.
- **Inference limits:** Addendum 93's cap remains at three further activity calls total; one was consumed by the third attempt, so at most two further calls remain. Each requires a substantive fix and tests first. Stop after the first accepted set or immediately on timeout, uncertain dispatch, or any different error. If accepted, continue with the previously authorized one story inference/review and at most one silent video candidate under existing gates.
- **Boundaries:** no raw generated text/image, quota/payment API, quality-gate relaxation, direct inference, DB edit, migration, new account/profile/run, seed deletion, consent/safety/admission bypass, unrelated service shutdown, commit, or push. All other Addenda 89–93 limits remain in force.
## Addendum 95 — reject malformed Parent story prose and allow one UI rewrite

- **Status:** APPROVED under the owner's active 2026-11-21 instruction to continue fixing the Parent flow, make loading states visible, and complete the real end-to-end path without quota/payment management.
- **Supplemental plan:** `plan/PLAN_REVISION_54_PARENT_STORY_OUTPUT_REPAIR_20261121.md`, 5,843 bytes, SHA-256 `434CE407C6511D836D0B705E96859ED99D89B04A9A4A66E9514504881278AAAF`.
- **TASK_APPROVAL.md pre-append pin:** 197,606 bytes / `CDAAFDCFEC34F55AD6FEA61A4DF098E19EC8EEE132EAA3C9E7B17BD77F24CE34`.
- **Observed defect:** the first story call on synthetic StoryRun `08657e31-ebd7-4a07-8f9b-5929b4dff23b` completed but the real UI showed mixed CJK characters and incomplete Vietnamese paragraphs; the backend persisted this output. The owner has not confirmed that draft.
- **Authorized:** add worker- and backend-boundary checks for user-facing Vietnamese script and complete prose, strengthen drawing/activity grounding instructions, add focused tests, deploy only the existing language-audio Modal app and rebuild only the task API, then submit exactly one adult-directed story rewrite from the real Parent UI on this same run after tests and health checks.
- **Conditional continuation:** if that exact revision passes the existing adult story review, confirm it through UI and submit at most one silent video candidate through UI under existing synthetic-dev identity, admission and safety gates. Do not access quota/payment APIs. If the synthetic candidate path requires bypassing a gate, stop.
- **Boundaries:** no new account/profile/run; no drawing/activity inference; no direct API/worker inference or DB edits; no extra story generation, rewrite or automatic retry after this one; no second video request; no quality/safety/consent/admission relaxation; no quota/payment access; no `.env`/secret/SRS or migration change; no unrelated Modal app/service change; no raw generated text/prompt/image/credentials in logs; no commit or push. Addenda 89–94 remain in force except that this addendum authorizes one UI rewrite and a narrowly scoped story-output validator/prompt repair.
## Addendum 96 — repair story failure persistence and resume Parent E2E

- **Status:** APPROVED under the owner's direct 2026-11-21 request to make the loading state clear, continue fixing the Parent flow, and run it end to end without quota/payment management.
- **Plan:** `plan/PLAN_REVISION_55_PARENT_END_TO_END_REPAIR_20261121.md`, 7,047 bytes, SHA-256 `E7373D3DA39A89DEC05E0F2A2720A83CE8E2B260BB6AF8D20DBF3E969AC53E32`.
- **TASK_APPROVAL.md pre-append pin:** 199,786 bytes / `F1CA1C30F7FEDD88120B7D084A34C396BF00C4438BF2D024E0FC37365BEBE730`.
- **Observed:** the one Addendum 95 rewrite completed inference but was rejected as `STORY_TEXT_INCOMPLETE`; the backend then failed its terminal-state transaction because it writes a nonexistent `story_revisions.updated_at` column, leaving revision 2 and its receipt pending and the run in `SCRIPT_GENERATING`.
- **Authorized:** fix the story failure transaction and add regression coverage; tighten the worker generation-only text limits and prompt while retaining every quality/safety/consent/admission rule; align visual-prompt punctuation with the backend contract; make the UI clearly report terminal story errors and prevent confirming stale drafts; deploy only the existing language-audio Modal app and task API.
- **Live continuation:** use authenticated UI cancellation only for the stuck run and only if the service says it is cancelable; reuse the existing synthetic Parent account/profile and existing synthetic turtle artwork. Complete at most one fresh UI-driven pass: one drawing inference, catalog-first activity selection with one fallback inference only if no eligible activity exists, one story generation and at most one adult-directed rewrite after a substantive fix, then one silent video candidate only after a valid adult-reviewed and confirmed story. No direct API/worker inference, fixture harness, automatic retry, or second video request.
- **Limits:** no quota/payment access or bypass; no safety/consent/quality-gate relaxation; no DB edits/migrations, account/profile creation/deletion, seed deletion, `.env`/secret access/change, raw prompt/text/image in logs, unrelated service shutdown, commit or push. Stop after timeout, uncertain dispatch, unavailable artwork, or any unexpected failure and preserve the evidence.
- Addenda 89–95 remain in force except this amendment explicitly authorizes the scoped persistence repair, UI recovery, and one fresh bounded Parent run described above.

## Addendum 97 — resume pending story visibly and recover only through UI

- **Status:** APPROVED under the owner's direct 2026-11-21 request to keep fixing the Parent flow, make the loading state easy to see, and continue through a real end-to-end run without quota/payment management.
- **Plan pin:** `plan/PLAN_REVISION_55_PARENT_END_TO_END_REPAIR_20261121.md`, 8,126 bytes, SHA-256 `70F59C1B5D14DA2CA9A471B3CD66438885C1F36A95FC8D5AEAEC6EE582253B0B`.
- **TASK_APPROVAL.md pre-append pin:** 202,262 bytes / `081D71A726E6F794541A59E851B09E5633BF6678F5B02B8E5E8D54B7E41B8729`.
- **Authorized:** fix Parent UI resume routing for server-pending story work; visibly block duplicate activity/story actions while pending; expose the existing history route from the pending screen; keep server `can_cancel` as the only cancellation authority; add focused tests; reload the real emulator UI; inspect and, only if eligible, cancel the already-stuck run through the authenticated UI; then continue within Addendum 96's single fresh synthetic UI pass and inference limits.
- **Files:** only the Parent controller, `ParentExpoApp.tsx`, `StoryScreen.tsx`, their focused tests, and feature-local plan/context/status/evidence files already listed in Revision 55.
- **Boundaries:** no new accounts/profiles/runs, no fixture or direct AI API/worker call, no database write/migration, no quota/payment call or bypass, no safety/consent/quality-gate relaxation, no secrets or `.env` access/change, no unrelated service shutdown, no commit/push. Addendum 96's inference limits and stop conditions remain unchanged.

## Addendum 98 — make Parent AI loading state unmistakable

- **Status:** APPROVED under the owner's direct 2026-11-21 request that the Parent loading state be easy to see while completing the real end-to-end workflow. This narrows no existing inference or safety limits.
- **Plan pin:** `plan/PLAN_REVISION_55_PARENT_END_TO_END_REPAIR_20261121.md`, 8,205 bytes, SHA-256 `277D52CADBCF59FA0B12BEB4091BAE7D1B34F93FAD0865865AC0A74BECCF754B`.
- **TASK_APPROVAL.md pre-append pin:** 203,861 bytes / `64372BEEF5B5F9B985EFB406FED3BB2C97CE0008595F4936B3C67FACA7AD80A0`.
- **Authorized:** add an optional high-contrast emphasis mode to the shared `ParentAiLoadingState`, enable it while Parent story processing is active, and cover its visibility contract in focused mobile tests.
- **Additional allowed file:** `apps/ui-mobile/src/parent/presentation/components/ParentAiLoadingState.tsx`. The component remains reusable; default styling for unrelated loading states is unchanged.
- **Boundaries:** no API or AI call is authorized by this addendum. All Addenda 96–97 boundaries and inference limits remain unchanged.

## Addendum 99 — sign into the existing synthetic Parent account for real UI E2E

- **Status:** APPROVED under the owner's explicit instructions to use existing seed accounts and run the Parent flow end to end. This addendum supersedes only prior `.env` read restrictions that would prevent signing into the already-existing synthetic Parent account.
- **Plan pin:** `plan/PLAN_REVISION_55_PARENT_END_TO_END_REPAIR_20261121.md`, 8,442 bytes, SHA-256 `AD746B1311CCC4584D37223DE10E40B19B3355F14C880960DDEB8EE66B728CA6`.
- **TASK_APPROVAL.md pre-append pin:** 204,974 bytes / `96E0D5613FFB680BADD386F51DD84E3DB203E3E3C6E3F964E7E7C0069D50B081`.
- **Authorized:** read only the existing synthetic Parent sign-in credential from `<local-machine-path> in process memory and enter it into the emulator's real login UI. Do not create/delete accounts or change the credential.
- **Handling:** never print the credential, place it in a command transcript, write it to a file, include it in evidence, or use it for any other account/service. The only network auth requests are those caused by submitting the UI login and the owner's requested real Parent workflow.
- **Boundaries:** no quota/payment access or bypass; no DB edits/migrations; all prior inference caps, stop conditions, safety/consent gates and no-commit boundary remain in force.

## Addendum 100 — apply the missing Parent lifecycle schema revision

- **Status:** APPROVED under the owner's direct request to fix the Parent backend and continue the full real E2E flow. This supersedes Addenda 96–99 only for the one migration named below.
- **Plan pin:** `plan/PLAN_REVISION_55_PARENT_END_TO_END_REPAIR_20261121.md`, 9,376 bytes, SHA-256 `FE484123CFD845822E92A29A648335CC6BC331B2E061613AC33E0D47F2619367`.
- **TASK_APPROVAL.md pre-append pin:** 206,316 bytes / `BC86E9E0AAEF9493251BE35BDAE428D0FE4440DFA9356CFDBBAD7D8DCF62EEE9`.
- **Observed blocker:** the real Parent UI's authorized cancellation returned HTTP 503. Read-only Alembic inspection found the `s2l-feat081-rev23` DB missing `20261119_frc08_lifecycle_scope`, while the deployed repository and migration require its owner-scope columns.
- **Authorized:** apply exactly `20261119_frc08_lifecycle_scope` to only the isolated `s2l-feat081-rev23` database, after the read-only current-revision check. Do not apply the unrelated pending lesson-library head. Do not run downgrade. Then recheck schema/API health and retry the already-authorized cancellation once through UI.
- **Boundaries:** no DB edits outside this migration, no new accounts/profiles/runs until the existing stuck run is canceled; no quota/payment, gate bypass, secrets output, unrelated services, commit or push. The single fresh E2E inference limits and stop conditions in Addendum 96 remain unchanged.

## Addendum 101 — preserve existing Parent activity receipts in lifecycle migration

- **Status:** APPROVED under the owner's direct request to fix the failed backend lifecycle path and finish Parent E2E.
- **Plan pin:** `plan/PLAN_REVISION_55_PARENT_END_TO_END_REPAIR_20261121.md`, 10,099 bytes, SHA-256 `00E14170A05711171BDD79275F792DCDA1B877406C55F5B386303CCB6194B5B4`.
- **TASK_APPROVAL.md pre-append pin:** 207,771 bytes / `6CD1BCA34FA441DFEEE5F4EB6080B35979773188F40126C1C34D5E9E56385F4F`.
- **Observed failure:** the first exact migration attempt rolled back transactionally because its receipt operation CHECK omitted two valid existing values: `GENERATE_ACTIVITY_SET` and `SELECT_ACTIVITY`. Read-only verification shows the lifecycle columns remain absent and the DB revision was not advanced.
- **Authorized:** update only `backend/alembic/versions/20261119_frc08_lifecycle_scope.py` so both upgrade and downgrade operation CHECKs match the current runtime's pre-`DELETE_RUN` operations; add focused tests comparing migration and runtime contracts; add safe SQLAlchemy diagnostics to the existing lifecycle repository failure path; run focused tests; rebuild only the task API; apply the single approved `20261119_frc08_lifecycle_scope` migration to the task DB; then retry the same UI cancellation once.
- **Boundaries:** preserve all receipts and rows; no manual DB edits or data deletion, no other migration/downgrade, no quota/payment access or bypass, no additional account/profile/run creation before the stuck run is canceled, no unrelated service shutdown, no commit/push. Addenda 96 and 100's remaining E2E limits still apply.

## Addendum 102 — process the exact canceled run and resume real Parent E2E

- **Status:** APPROVED by the owner's direct reply: “Cho phép worker xử lý đúng run này”.
- **Approved plan:** `plan/PLAN_REVISION_55_PARENT_END_TO_END_REPAIR_20261121.md`, 13,049 bytes, SHA-256 `E5CD721CF5678FD080F186885C4FAF859BB11EDF70DC20E616D43EC36BCFE841`.
- **TASK_APPROVAL.md pre-append pin:** 209,420 bytes / `8F07CAEE30FBE7DFAAFC75EA99D503EF90D0BB69624185A1B512519AF0A95141`.
- **Authorized lifecycle effect:** implement/use a safe one-shot path through the existing `Be1LifecycleConsumer`, restricted to StoryRun `08657e31-ebd7-4a07-8f9b-5929b4dff23b` and its one `StoryRunCancellationRequestedV1` event. The normal lifecycle purge may remove this run's story content and run-owned assets/objects that are not referenced elsewhere, finalize `DELETED`, and retain tombstone/receipts. Account, profile, seeds, and unrelated events/data must remain untouched.
- **Required safeguards:** preflight the isolated task Docker target, exact owner scope and `DELETE_PENDING` state, released lock, and exactly one eligible event. Claim only that aggregate/event. Verify event delivery, completed lifecycle receipt, `DELETED`, and no unrelated event mutation. Stop on mismatch or partial/unknown outcome; no direct SQL edits.
- **Authorized continuation:** after purge completion, continue one fresh bounded Parent UI run on `emulator-5554` using the existing synthetic identity/profile and synthetic artwork; at most one drawing inference, one catalog-first activity fallback if needed, one story inference without rewrite, and one silent video candidate only after adult story review/confirmation. No quota/payment calls or bypass; existing admission, safety, consent, ownership and quality gates remain enforced.
- **Additional allowed files:** `backend/src/sketch2life/application/ports/core_foundation.py`, `backend/src/sketch2life/infrastructure/persistence/outbox.py`, `backend/src/sketch2life/infrastructure/persistence/be1_lifecycle_consumer.py`, new `backend/tools/run_parent_lifecycle_once.py`, focused tests for aggregate filtering and one-shot preflight, plus the plan/context/status/evidence paths already listed in Rev55.
- All other Addendum 96–101 inference, identity, data, safety, quota, and no-publication limits remain in force.

## Addendum 103 — story output recovery and one bounded UI retest

- **Status:** APPROVED by the owner's direct reply: “Duyệt sửa + 1 lần story (Recommended)”.
- **Approved plan:** `plan/PLAN_REVISION_56_STORY_OUTPUT_RECOVERY_20261121.md`.
- **Authorized scope:** completion-aware structured prose contract, focused worker/backend/mobile tests, clearer truthful loading and terminal UI actions, and at most one adult-directed story rewrite from the real Android UI on the same existing synthetic run after read-only eligibility checks.
- **Conditional video:** only if the story passes unchanged hard gates and an adult reviews/confirms it; at most one silent video candidate via the real UI, subject to all existing consent/admission/safety/ownership checks.
- **Limits:** no drawing/activity inference repeat, no new run/account/profile, no quota/payment access or bypass, no fixture/preview/direct inference, no data or gate-policy weakening, no commit/push. Stop on first failure. Stop only task-used Modal apps after verifying no live tasks.

## Addendum 104 — resolve terminal story-failure recovery before further inference

- **Status:** APPROVED by owner reply: “Approve Plan Rev57 (Recommended)” on 2026-11-21.
- **Approved plan:** `plan/PLAN_REVISION_57_FAILED_STORY_REWRITE_RECOVERY_20261121.md`, SHA-256 `97A9AECFF7E170FDC1C0D2228CF889FACDFD31912EFFA45BCB74D2D62E7C5A7B`.
- **Observed blocker:** the exact synthetic run from Addendum 103 is `FAILED` with `STORY_OUTPUT_INVALID`; revision 1 is `FAILED`, while one activity selection is persisted. Backend reservation accepts only `PREPARATION_REVIEW`/`SCRIPT_REVIEW`; the canonical SRS currently marks `FAILED` terminal and does not define recovery for a quality-rejected story. The Parent UI also has no route from Home/history back to that failed run.
- **Authorized:** amend the current SRS to permit an adult-directed, fresh-key rewrite only for this deterministic `STORY_OUTPUT_INVALID` case, with server-side context/activity/drawing validation, atomic active-owner lock reacquisition, immutable failed revisions, the existing three-rewrite cap, and no automatic retry. All other failures remain terminal. Implement the necessary Parent repository/service/port/route and Home/story recovery path, focused tests, then send at most one rewrite from the real Android UI on the existing run.
- **Conditional video:** unchanged from Addendum 103: only after the story passes all existing gates and an adult reviews/confirms it; at most one silent candidate via real UI, with no quota/payment call or bypass.
- **Limits:** no new run/account/profile, repeated drawing/activity inference, database migration/direct edits, gate weakening, direct AI inference, unrelated app/service change, commit or push. Stop on the first failure. Addenda 89–103 remain unchanged except for this narrow state-transition and same-run rewrite authorization.

## Addendum 105 — continue Parent E2E until a silent LTX video plays

- **Status:** APPROVED by owner’s direct instruction “fix nếu có bug, nào chạy đc vid thì mới dừng” on 2026-11-21.
- **Approved plan:** `plan/PLAN_REVISION_58_PARENT_SILENT_VIDEO_E2E_20261121.md`, SHA-256 `570A47B98C963BB39F7D12EF7E0C920BA9A9B97EA542D3E029093790664F129D`.
- **Observed blocker:** the Rev57 same-run story rewrite returned `SCRIPT_GENERATION_UNKNOWN` with no Modal call ID; its run/revision is awaiting reconciliation and holds the active-owner lock. Current FEAT-081 Modal video source is only a scaffold; the task API candidate flag is false, and no video app is deployed in the current Modal environment.
- **Authorized:** diagnose the old story call without replaying it; fix safe Modal dispatch logging; port and verify the pinned LTX-2.5 Modal worker; enable the existing local synthetic-only Parent candidate route; fix any defects in the real Parent Android path; continue diagnosis-guided synthetic UI/API/Modal inference until one valid silent LTX-2.5 MP4 candidate is authenticated and played in the Parent UI.
- **Boundaries:** keep the old unknown run immutable and unreplayed; use a distinct synthetic profile/account if required; no real-child data, direct inference, blind retry, model/GPU substitution, audio, quota/payment mutation or bypass, production-safety/admission bypass, public playback, or product-ready claim. Candidate metadata must retain `product_playable=false` and `safety_validation=NOT_RUN`. No commit/push. Stop task-used Modal apps after verifying zero tasks.

## Addendum 106 — pin the Rev58 source-dependent file list before implementation

- **Status:** APPROVED under the same owner instruction recorded in Addendum 105; no code implementation had begun when this correction was made.
- **Plan:** `plan/PLAN_REVISION_58_PARENT_SILENT_VIDEO_E2E_20261121.md`, revised SHA-256 `32EBEE6E4C41A6B00AFC9D55B69F252085445633CACF8F320146F7066EB6C23B`.
- **Correction:** M0 source review identified required LTX worker dependencies (`contracts.py`, `workloads.json`, `story_image_guides.py`, `story_visual_plan.py`, and their focused tests) and the actual UI component name `VideoCandidateScreen.tsx`. These exact paths and their reason were added to the plan allowlist before implementation.
- **Scope effect:** no behavioral scope changed; Addendum 106 supersedes only the earlier Rev58 plan hash in Addendum 105. All safety, synthetic-only, no-blind-retry, no-quota-bypass, candidate-only, and no-commit boundaries remain in force.

## Addendum 107 — repair the diagnosed Parent activity prompt mismatch

- **Status:** APPROVED under the owner's direct 2026-11-21 instruction to fix defects and continue until a video is produced, and the explicit Rev58 plan rule permitting concrete-defect files to be added to §6 before edit.
- **Plan pin:** `plan/PLAN_REVISION_58_PARENT_SILENT_VIDEO_E2E_20261121.md`, SHA-256 `FD6A8455A4D33A15BC92FD9AD8F28C19EE462E45F1AB58E89BB1F3A6DFAAD956`.
- **Observed blocker:** live Qwen3.5 activity inference completed successfully, but backend quality validation rejected all three drafts with `SAFETY_NOTE_MISSING`. The worker prompt bounds safety-note length without requiring the explicit precaution wording that the unchanged backend gate checks.
- **Authorized files:** `deployment/modal/srs_v23/language_audio_app.py` and `backend/tests/unit/test_parent_activity_worker_contract.py`, added to the Rev58 allowlist before editing.
- **Authorized repair:** make the worker prompt require a short, topic-appropriate precaution containing an explicit safety marker accepted by the existing gate; add focused prompt-contract coverage. Keep response schema, parser, backend quality/safety gates, age/ownership checks and all other policy unchanged. Redeploy only the existing language/audio Modal app, then retry the current activity suggestion once from the real Android UI after the repair and tests pass.
- **Limits:** no direct worker/API inference, no gate relaxation, no extra account/profile/run, no quota/payment access or bypass, no video request until an adult-confirmed story exists, no unrelated app shutdown, no commit or push. Addenda 89–106 remain in force; this addendum only records the specific activity-output repair needed by Rev58's approved E2E acceptance criteria.

## Addendum 108 — correct the diagnosed incomplete safety sentence

- **Status:** APPROVED under the owner's continuing direct instruction to fix concrete defects and proceed until the video plays; the inference is separately bounded by the recorded defect and repair.
- **Plan pin:** `plan/PLAN_REVISION_58_PARENT_SILENT_VIDEO_E2E_20261121.md`, SHA-256 `C4DCEF134D42DA4CCDC7C4661040A26CB0C120F35654F89F7FCB3A077B87DF3C`.
- **Observed:** the Addendum 107 UI retry completed Qwen3.5 inference (794 tokens, 88,846 ms) but the worker parser rejected the first fallback safety note as `MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT` / `dangling_word`; nothing was persisted.
- **Authorized:** shorten the prompt target for safety-note bodies to 40 characters while preserving the schema ceiling and explicit safety marker; add a focused assertion to the already-allowed worker contract test; run offline tests; redeploy only the language/audio app; then perform one UI-triggered activity inference for this specific corrected defect.
- **Limits:** no direct worker/API request, no parser or backend gate relaxation, no new account/profile/run, no quota/payment access or bypass, no video until the adult-confirmed story exists, and no commit/push. All other Rev58 boundaries remain unchanged.

## Addendum 109 — normalize duplicate terminal punctuation in activity prose

- **Status:** APPROVED under the owner's direct instruction to keep fixing concrete defects and continue through video generation.
- **Plan pin:** `plan/PLAN_REVISION_58_PARENT_SILENT_VIDEO_E2E_20261121.md`, SHA-256 `FFB7361EFA70063A9348EEB53EE23584C508A0FEA66CC764DB543D8CAD0E4851`.
- **Observed:** the Addendum 108 UI inference completed 888 Qwen3.5 tokens in 139,489 ms but failed output validation at `fallback_activities[0].objective` with `terminator_invalid`; no activity was persisted.
- **Authorized:** in the already-allowed worker, when the JSON terminator is exactly `.`, strip terminal sentence punctuation from the body and append one canonical period. Keep rejecting wrong terminator values, empty/incomplete sentences, unsafe content and all backend quality/safety failures. Add focused regression coverage, run offline tests, redeploy the language/audio app, then perform one UI-triggered activity inference for this specific defect.
- **Limits:** no direct worker/API inference, no backend gate changes, no new identity/run, no quota/payment access or bypass, and no commit/push. Existing Rev58 invariants remain unchanged.

## Addendum 110 — recover the terminal incomplete-story revision

- **Status:** APPROVED under the owner's direct instruction to fix concrete failures and continue through a playable video, using the story recovery already authorized in SRS v2.7-draft Rev73.
- **Plan pin:** `plan/PLAN_REVISION_58_PARENT_SILENT_VIDEO_E2E_20261121.md`, SHA-256 `7DC133568E02EF5A7D8AF3726F66D4E010B6FB7BF468E00A6BF3A05E72532453`.
- **Observed:** live story call `fc-01M7Z27C3S4QATFJZGHCCZ45TP` ended in a proven worker terminal failure `STORY_TEXT_INCOMPLETE`; only `scenes[4].action` was flagged incomplete, with body length 57/60 and no token-limit hit. Backend classified it as `STORY_OUTPUT_INVALID`. The run is on the UI's Rev73-permitted quality-rewrite screen; three rewrites remain.
- **Authorized files:** `deployment/modal/srs_v23/language_audio_app.py` and `deployment/modal/srs_v23/tests/test_parent_story_output_contract.py` (added to Rev58 §6 before editing).
- **Authorized repair and retest:** shorten only the prompt target for each scene `action` body to 24–40 characters; preserve the 60-character schema ceiling, five-scene contract, subject/activity/story rules and all validators. Add focused prompt-contract coverage, run the story worker tests, redeploy only the existing language/audio app, then submit one adult-directed story rewrite through the real UI with a fresh idempotency key. Keep the failed revision immutable and recheck input hashes.
- **Limits:** no direct API/worker inference, no repeat of the failed provider call, no schema or quality/safety-gate relaxation, no quota/payment access or bypass, no changed identity/run, and no commit/push. Unknown outcome or any error other than the SRS-permitted `STORY_OUTPUT_INVALID` remains non-retryable.

## Addendum 111 — shorten all story prose targets after same-run rewrite rejection

- **Status:** APPROVED under the owner's continuing direct instruction to fix concrete bugs and continue until a real silent video candidate runs and plays; this is a diagnosis-guided continuation of Rev58 and SRS Rev73, not a new run or an inference retry without a code fix.
- **Approved plan:** `plan/PLAN_REVISION_58_PARENT_SILENT_VIDEO_E2E_20261121.md`, 23,464 bytes, SHA-256 `A8D453484600607BBFE8D640C7A0ED8322636D25D989E6D99DAEA92AFEADC4CE`.
- **TASK_APPROVAL.md pre-append:** 223,327 bytes, SHA-256 `BCF350311168C679C3E5902A8EA39DC9A960760220EC72DC97A8C2F53C1022C3`.
- **Observed blocker:** the one approved UI rewrite (`fc-01M7Z301MEVNSV4T796KZZAPCG`) completed inference and JSON parsing but failed the unchanged sentence gate at `scenes[2].narration`, classified `STORY_TEXT_INCOMPLETE` / `STORY_OUTPUT_INVALID`; 49-character field, model EOS allowed, token ceiling not reached.
- **Authorized files and repair:** only `deployment/modal/srs_v23/language_audio_app.py` and `deployment/modal/srs_v23/tests/test_parent_story_output_contract.py`. Shorten prompt targets for story sentence bodies (35–50 chars), scene actions (20–32), and narration (20–35), requiring one simple complete sentence with external terminator and no trailing conjunction. Keep schema maxima, parser and every hard/quality/safety/ownership gate unchanged. Add focused assertions and run the story-worker tests.
- **One bounded UI retest:** after tests pass and only the language/audio Modal app is redeployed/readiness checked, confirm same-run eligibility and unchanged input hashes, then submit at most one fresh-key rewrite from the real Android UI. Do not replay either prior Modal call and do not invoke the API/worker directly.
- **Conditional continuation:** only a valid revision reviewed and confirmed by the adult may proceed to the existing single silent candidate, with all consent/admission/ownership/safety gates intact; no quota/payment calls or bypass. Candidate remains private with `product_playable=false` and `safety_validation=NOT_RUN`.
- **Limits:** unknown outcomes, errors other than SRS-permitted `STORY_OUTPUT_INVALID`, changed hashes, exhausted three-rewrite cap, or any safety/consent/admission failure stop this continuation. No DB edits, new identity/run, gate weakening, raw content logging, unrelated service shutdown, commit or push.
## Addendum 112 — recover the successful LTX output rejected by a redundant metadata contract

- **Status:** APPROVED by the owner's direct 2026-11-21 instruction to fix concrete defects and continue until the video runs. This is a one-time recovery of the already-completed Modal call, not authorization for another GPU inference.
- **Approved plan:** `plan/PLAN_REVISION_58_PARENT_SILENT_VIDEO_E2E_20261121.md`, 27,193 bytes, SHA-256 `BD51BDBE14665D4E253EA800C3F03DF966A816A58784DD4A33D9EEA93DCEC105`.
- **TASK_APPROVAL.md pre-append:** 225,770 bytes, SHA-256 `DB881AEE687092AEA9AAEC3D3697A2D968670845EEAD715EDFF6C01BDFD5E0B0`.
- **Observed defect:** Modal call `fc-01M7Z3S0AAJ89HCJ6Q8CM2STT0` succeeded after five scene inferences, silent assembly and worker MP4 validation (474,757 ms). The Android UI then showed `VIDEO_WORKER_OUTPUT_INVALID`. The worker writes width/height/fps/codec to its SHA-256-bound manifest but omits those redundant fields from its returned JSON; backend validation requires them in both locations. The completed video, manifest and call remain available for the same candidate.
- **Authorized files:** only paths in the approved Rev58 §6 allowlist, with `backend/src/sketch2life/application/ports/parent_video_candidates.py` and `backend/src/sketch2life/infrastructure/persistence/parent_video_candidate_repository.py` added in the plan amendment for a guarded recovery transition.
- **Authorized repair:** add those four metadata values to future Modal results; accept the existing v2 result only by taking omitted redundant media fields from the hash-verified manifest and rejecting any supplied mismatch; preserve every other integrity, model pin, lineage, media, safety, ownership and admission check. On authenticated current-status polling, recover at most once only if the exact existing record is FAILED with `VIDEO_WORKER_OUTPUT_INVALID`, has its prior Modal call and attempt references, and has no recovery marker. Mark recovery in progress before collecting the same completed call, persist only the exact validated output, and record sanitized recovery provenance. A failed recovery becomes terminal and cannot loop. No new call, attempt, candidate, run, direct DB edit, quota/payment access, gate bypass, commit or push.
- **Verification:** run focused offline tests; deploy the corrected Modal video app without invoking video generation; rebuild only the task API; let the Android UI's authenticated status polling recover and play the same MP4 through its private preview. Stop if IDs/hashes do not match, the output is unavailable, validation fails, or recovery was already consumed.

## Addendum 113 — provide root Firebase/Modal configuration to the task API

- **Status:** APPROVED under the owner's direct instruction to continue fixing diagnosed blockers until the video works; this is an operational correction required to resume the same authenticated Android run.
- **Approved plan:** `plan/PLAN_REVISION_58_PARENT_SILENT_VIDEO_E2E_20261121.md`, 29,195 bytes, SHA-256 `515922365AFF3845044D45A7170D1D99C6EA101CBF2BBE574862236ACA821B15`.
- **TASK_APPROVAL.md pre-append:** 228,406 bytes, SHA-256 `3ED5CA4EA38A579EC60544DEA7B08323A6E3CFF7AA75A501B246BE3AFF40D618`.
- **Observed:** Android Firebase sign-in completed, but `/api/auth/v1/me` returned `503 IDENTITY_PROVIDER_UNAVAILABLE`. The task API was composed from `.codex-worktrees/fe` without the root `.env`, so its effective settings fell back to `auth_provider=development`, no Firebase Admin credential/project, and `ai_provider=disabled`.
- **Authorized action:** recreate only `s2l-feat081-rev23-api-1` using the same Compose files and `--env-file <local-machine-path> Do not edit or print the env file. Preserve the project, API port, task database and all volumes; do not restart other services, migrate, seed, change accounts/profiles, submit AI/video work, or touch quota/payment.
- **Validation:** confirm only redacted booleans and provider names inside the API container; verify Firebase Admin initialization and API health; sign into the same synthetic account and use the Android UI to refresh/recover the same completed Modal video call. Addendum 112's exact-call/hash and one-shot conditions remain mandatory.
- **Limits:** no new inference, run, account, profile, database mutation, gate bypass, secret disclosure, commit, or push.

## Addendum 114 — show unresolved story outcomes as reconciliation, not live loading

- **Status:** APPROVED as a narrow continuation of the owner's active instruction to fix the Parent E2E until video works, and the loading-state scope in Addenda 89/90/98. No new AI or video inference is authorized by this addendum.
- **Approved plan:** `plan/PLAN_REVISION_58_PARENT_SILENT_VIDEO_E2E_20261121.md`, SHA-256 `D734ECCEF0E9044B08E46A9C6AC96B24531C22C85A96A9ED2970239510B5E52D`.
- **TASK_APPROVAL.md pre-append:** 230,139 bytes, SHA-256 `E69FA4BC1679E8F1AD2739EAB633AA3ACC86FE5E068CB5E95B0ED75393E6045B`.
- **Observed defect:** the Android story screen maps `SCRIPT_GENERATION_UNKNOWN` to the same animated spinner and elapsed timer as active inference. The displayed timer is local to the component mount and resets when the screen opens; it is not provider execution time. Modal function history has no story call in the recorded dispatch window, while backend state remains unknown and must retain its lock.
- **Authorized files:** `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx`, `apps/ui-mobile/src/parent/presentation/screens/StoryScreen.tsx`, `apps/ui-mobile/src/parent/presentation/components/ParentAiLoadingState.tsx`, and `apps/ui-mobile/tests/parentSrsBehavior.test.ts`, all added to Rev58 §6 before editing.
- **Authorized repair:** render unknown/reconciliation states as static, truthful status; remove the local timer and active spinner for those states; explain that provider acceptance/result is unconfirmed; keep duplicate submissions blocked. Known active inference retains its loading UI. Add focused UI contract assertions and run mobile typecheck/focused tests.
- **Limits:** no run/revision mutation, lock release, retry/replay, new identity, Modal deploy, AI/video request, quota access/bypass, safety/ownership change, commit, or push. The old run remains `AWAITING_RECONCILIATION` until an approved provider reconciliation path resolves it.

## Addendum 115 — make Parent activity fallback prose reliable without weakening gates

- **Status:** APPROVED by the owner's direct 2026-11-21 request to inspect generated content/parsers and reduce avoidable failures across the AI path, while continuing the approved Parent E2E until video.
- **Approved plan:** `plan/PLAN_REVISION_58_PARENT_SILENT_VIDEO_E2E_20261121.md`, SHA-256 `1009C829865825ABC364B7EA6409085C3C201488015B424AB18D66114A09B6B4`.
- **TASK_APPROVAL.md pre-append:** 232,119 bytes, SHA-256 `095CFF1A7FC3CB3235ED9619A39D16BE6B9AD841D2998708D7CCD610B1659A5C`.
- **Observed defect:** two real UI-triggered Parent activity calls reached Qwen3.5 and returned the same `MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT` failure at `fallback_activities[0].objective` (`dangling_word`, 47 characters; 827 tokens, no token-limit hit). The raw generated text is not persisted; the worker logs only the bounded field/reason diagnostics. Retrying unchanged reproduced the same failure.
- **Authorized files:** `deployment/modal/srs_v23/language_audio_app.py`, `deployment/modal/srs_v23/tests/test_qwen35_lesson_suggestion_contract.py`, and `backend/tests/unit/test_parent_activity_worker_contract.py`; all are listed in Rev58 §6 before edits.
- **Authorized repair:** replace model-authored objective/preparation/safety prose with position-specific internal markers and deterministic, subject-aware Vietnamese templates; keep the external Parent API schema unchanged. Preserve the existing backend and worker safety, age, outdoor, context, catalog, Montessori, sentence, duplication, PII and adult-review gates. Add tests for all templates, bounds, and invalid markers.
- **Verification:** run the focused worker/backend contract tests; deploy only the language/audio Modal app; verify CPU readiness without warming weights; then submit at most one corrected fallback request through the real Android UI on the same synthetic run. If any other field fails, stop and inspect its safe diagnostic before another inference.
- **Limits:** no raw model text in logs/evidence, gate bypass, quota/payment access, new account/profile/run, direct API/worker inference, blind retry, video request until the story is confirmed, or commit/push.

## Addendum 116 — harden Parent activity parser against Vietnamese false rejects

- **Status:** APPROVED under the owner's direct 2026-11-21 instruction to inspect and fix content/parser failures across the system so valid flows stop failing on avoidable checks.
- **Approved plan:** `plan/PLAN_REVISION_58_PARENT_SILENT_VIDEO_E2E_20261121.md`, SHA-256 `7AF311CBCFAABCC65F34665E92D3C125FA356F3EE1D45305F3E1F5ECEF6B5241`.
- **TASK_APPROVAL.md pre-append:** 234,348 bytes, SHA-256 `35F271DB3D91EB3A600F9CD94222D2564C39517660A0E79C20B277E5B232CEEB`.
- **Authorized scope:** in the already-allowlisted Parent activity worker/backend parser path, preserve Vietnamese diacritics while checking incomplete tails so valid nouns do not collide with conjunctions; keep detection for genuine incomplete tails; reject duplicate JSON keys rather than silently accepting the last value. Add focused regressions in the two newly allowlisted backend files and existing Modal contract test.
- **Limits:** do not relax any safety, age, topic/context, Montessori, catalog, PII, uniqueness, output-shape or adult-review gate. Do not retain/log raw model text. Run only the focused offline contract suites, then at most one already-authorized UI-triggered fallback request after deployment. No direct inference, blind retries, new run/account, quota/payment action, video request before adult-confirmed story, commit or push.

## Addendum 117 — prevent accepted truncated activity text and harden AI JSON parsing

- **Status:** APPROVED by the owner's direct 2026-11-21 instruction to check content and parsers across the system and fix avoidable AI errors.
- **Approved plan:** `plan/PLAN_REVISION_58_PARENT_SILENT_VIDEO_E2E_20261121.md`, SHA-256 `318AB88AEF3D04AA78782C4D78568E923AFEFDB6525D6A09566CCF25F3D76922`.
- **TASK_APPROVAL.md pre-append:** 235756 bytes, SHA-256 `4D89E9490E0DC429CCFF6F995239E4FB54ACF7A50CC9DCD8E7CC6B0807688BA8`.
- **Scope and acceptance:** as defined in Addendum 117 of the approved plan. One live Parent UI activity inference already completed and returned three activities; no further model inference is authorized here.
- **Implementation checkpoint:** pending; no files beyond the existing allowlist have been modified for Addendum 117.
## Addendum 117 plan clarification

- Before implementation, clarified the backend finding: the slicing applies to catalog lesson fields being prepared as Modal context, not model output. The authorized fix is a bounded word-boundary excerpt that leaves the stored lesson unchanged and records only an aggregate safe diagnostic.
- **Current approved plan SHA-256:** `9F29FBD3F1F36F81DBEA3D1E4700CA3DACFCE9898EFC90516E2027B8BBA294D0`.
## Addendum 117 allowlist clarification

- Before implementation, add ackend/src/sketch2life/interfaces/http/routers/parent_ai.py to the allowlist so the already-existing sanitized catalog-context truncation count can be included in its catalog-prepared event. No route or API contract change is authorized.
- **Current approved plan SHA-256:** `FD3A2564EE0434DB07B252107B015BD61DB2652A3966741BDAC3C90936D0DA6C`.
## Addendum 117 test-scope clarification

- Direct owner request continues to authorize this diagnosis-only fixture update; no video worker implementation or inference is included.
- Add deployment/modal/srs_v23/tests/test_silent_story_contract.py to the allowlist solely for supplying the required width/height/FPS/codec fields in its existing payload-contract test.
- **Current approved plan SHA-256:** `BB90EEA9B529BCA7DA6218FDD08641F1F720799BAACEAF22D57B976224A7FA5C`.
## Addendum 117 implementation checkpoint — 2026-11-22

- Status: implementation and offline verification complete within the approved scope.
- Plan pin: plan/PLAN_REVISION_58_PARENT_SILENT_VIDEO_E2E_20261121.md, SHA-256 BB90EEA9B529BCA7DA6218FDD08641F1F720799BAACEAF22D57B976224A7FA5C.
- Verification: 184 Modal output-contract tests and 278 backend parser/service tests passed; Python compilation and scoped diff checks passed. API container health is ok; Modal language/audio CPU readiness is ready_for_gpu_worker_validation; no active Modal tasks were present.
- Live-inference boundary: the single approved Parent UI activity call had already completed before the repair and exposed one accepted truncated materials field. No post-repair inference was sent, consistent with the one-call limit. Live validation of the repaired wording remains outstanding.
- Audit note: silent-video worker input manifests use ordinary json.loads but are backend-produced, not model-authored. No change was made because video_app.py is outside this addendum's approved allowlist.
- Evidence: evidence/PARENT_AI_PARSER_AUDIT_REV117_20261122/PARSER_AUDIT_REPORT.md.
- No new video request, quota/payment action, gate bypass, account/run mutation, commit, or push.

## Addendum 118 — expose persisted Parent video candidate metadata through the public contract

- **Status:** APPROVED by the owner's 2026-11-22 bug report and the active instruction to fix the Parent end-to-end flow.
- **Approved plan:** `plan/PLAN_REVISION_59_PARENT_VIDEO_READY_METADATA_RESPONSE_20261122.md`, SHA-256 `49CF7B00465B6A0A45B9CFB4FDDD1911D5D9ADFEDBAA84B82243531AE27C593D`.
- **Observed:** the existing synthetic candidate is `CANDIDATE_READY`, has a Modal call reference and a 4,289,168-byte MP4. Fourteen status polls failed at `ParentVideoCandidateMetadataV1.model_validate`: persisted metadata included internal `output_sha256`, `output_size_bytes`, and `output_manifest_sha256`, which the strict public contract correctly rejects. The response mapper was passing the full persistence object instead of projecting public fields.
- **Authorized repair:** explicitly project the public metadata fields in `parent_video_candidates.py`; preserve internal hashes, storage size, asset lineage, and strict response schema. Add a regression to `backend/tests/contract/test_parent_video_candidate_api.py`.
- **Verification:** focused offline tests, then rebuild only the API and read the existing ready candidate from the real Android UI. Previewing the already stored candidate is permitted. Do not replay POST or create a new run/video.
- **Limits:** no new inference, Modal GPU call, database mutation/migration, quota/payment call, feature-gate change, gate bypass, commit, or push.

### Addendum 118 implementation checkpoint — 2026-11-22

- **Result:** implemented the approved public-field projection in the Parent video candidate response mapper and added a ready-candidate regression test containing internal hash/size fields.
- **Verification:** 14 focused backend tests passed; Python compilation and scoped diff checks passed. API container was rebuilt and `/health` returned `ok`.
- **Live UI check:** the existing synthetic candidate remained `CANDIDATE_READY`; Android status polling showed the ready screen and opened the existing private preview. No generation request was sent.
- **Post-rebuild logs:** zero occurrences of the reported `ParentVideoCandidateMetadataV1` validation failure in the inspected window.
- **Evidence:** `evidence/PARENT_VIDEO_CANDIDATE_RESPONSE_FIX_REV59_20261122/RUN_REPORT.md` and its two screenshots.
- **Limits honored:** no inference, DB mutation/migration, quota/payment operation, gate bypass, commit, or push. Safety/consistency remain `NOT_RUN`; the preview is not product-playable.

## Addendum 119 — make Parent video preview playable and simplify the screen

- **Status:** APPROVED by the owner's direct 2026-11-22 request to fix the non-working Play action and make the existing screen friendlier with less text.
- **Approved plan:** `plan/PLAN_REVISION_60_PARENT_VIDEO_PLAYER_AND_COPY_20261122.md`, SHA-256 `0EDC499FF5FA58A4A5285F5F5825B58432469E3D46596DB7254620218DF968E5`.
- **TASK_APPROVAL.md pre-append:** 241,727 bytes, SHA-256 `12EF6C1F69AF7BE151B5013F9F917CEF9CF206F2A2F2B16587FFF482C5A1F6D6`.
- **Observed:** the authenticated preview endpoint returned HTTP 200 and rendered the first frame on Android, but the native control remained “Play” at 00:00 after tapping. The screen's `onError` handler discards player errors. The ready card repeats long notices and technical metadata.
- **Authorized files:** `apps/ui-mobile/src/parent/presentation/screens/VideoCandidateScreen.tsx` and this FEAT-081 plan/approval/status/context/evidence record.
- **Authorized repair:** use explicit accessible Play/Pause/Replay actions and playback status; display safe playback errors and retry the existing preview; reduce the screen to one concise experimental/safety notice, compact duration/scene details, and a prominent player.
- **Acceptance:** use the already stored synthetic candidate on Android; verify elapsed time advances on Play and pauses/resumes. Typecheck and save feature-local screenshots/report. Do not send another generation request.
- **Limits:** no backend/SRS/dependency change, new inference, Modal deploy/warmup, DB mutation, quota/payment call, gate bypass, safety-status or product-playable change, commit, or push.

### Addendum 119 implementation checkpoint — 2026-11-22

- **Implemented:** `VideoCandidateScreen.tsx` now uses explicit accessible Play/Pause/Replay calls, reports playback errors with reload, shows elapsed/duration, and presents shorter copy with one concise experimental/safety notice.
- **Verification:** mobile TypeScript typecheck passed. Before the change, Android reproduced the reported issue: the preview endpoint returned HTTP 200 and rendered a frame, but Play remained at `00:00`; the screen had swallowed player errors.
- **Runtime limit:** after bundle reload the in-memory Parent session was lost. Reauthentication resumed at activity selection; history has no action to reopen the existing ready candidate. Reaching video from that state would require an activity inference, which this addendum excludes. Therefore post-change playback is **not yet confirmed on-device**.
- **Evidence:** `evidence/PARENT_VIDEO_PLAYER_UI_REV60_20261122/RUN_REPORT.md` and screenshots.
- **No inference, video request, DB mutation, quota/payment action, gate bypass, commit, or push.** Keep this task partial until the existing ready candidate can be reopened through an approved route and Play/Pause is verified.

## Addendum 120 — bounded Parent AI and playback verification

- **Status:** APPROVED by the owner's direct 2026-11-22 instruction: “kiểm tra đi, cho chạy AI”.
- **Approved plan:** `plan/PLAN_REVISION_61_BOUNDED_PARENT_AI_VIDEO_PLAYBACK_E2E_20261122.md`, SHA-256 `6F65B12A5B62D55312C0733582B503AB4727CA6ACC942DC5DDCBE23D163E873D`.
- **Scope:** reuse the existing synthetic Parent profile/run; inspect first; on the real Android UI, send at most one request for each missing activity/story/video workload, no blind retry, and verify Play/Pause/Resume on Android.
- **Boundaries:** no real-child data, new account or seed rewrite; no quota/payment action or bypass; no consent/age/ownership/safety/quality gate bypass; no DB mutation; no video retry; no product-code change; no commit/push. Stop only Modal apps started for this check after confirming no active tasks.
- **Allowed records:** this plan, this approval file, FEAT-081 status/context, and the revision-specific evidence folder.

## Addendum 121 — cold-resume story and existing video candidate

- **Status:** APPROVED by the owner's direct 2026-11-22 instruction: “chạy fix đi”.
- **Approved plan:** `plan/PLAN_REVISION_62_PARENT_COLD_RESUME_AND_CANDIDATE_HYDRATION_20261122.md`, SHA-256 `4F5D90063B1C92AB2F212F588048C12F02A28E8D2891CFA00A77FDE0045D5F3D`.
- **TASK_APPROVAL.md pre-approval hash:** `A5AB083B5E123B04DEB7EC2FD821F35E856282DB8E9942720251EEE0CEE3D806`.
- **Approved scope:** distinguish initial client hydration from a true stale revision; GET the current video candidate when opening the video step so a saved candidate is shown before any POST; verify the existing candidate's authenticated preview and Play/Pause/Resume on Android.
- **Limits:** existing synthetic run/candidate only; no new inference/video request, account/run/data mutation, quota/payment operation, gate bypass, Modal deployment, commit, or push. Full file allowlist and acceptance criteria are in the plan.

## Addendum 122 — owner authorization to commit and push completed Parent workflow

- **Date:** 2026-11-23.
- **Status:** APPROVED by the owner's direct instruction: “commit và push”.
- **Scope:** Publish the completed Parent mobile/backend/Modal implementation and its FEAT-081/FEAT-082 plans, decisions, status, and synthetic E2E evidence currently present in this feature worktree, including related FEAT-063 SRS/register updates.
- **Supersedes:** The earlier “no commit/push” operational limit in Addenda 120–121 for this publication only.
- **Publication safeguards:** Exclude credentials, environment files, seed accounts, pytest basetemp/model-fixture outputs, and deployment-local pytest artifacts. Preserve the finding that FEAT-082's video remains a technical preview without demonstrated safety clearance; this authorization does not change product acceptance.
- **Validation:** Run the repository security validator before commit and again before push. Do not send additional inference requests as part of publication.
