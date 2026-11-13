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
