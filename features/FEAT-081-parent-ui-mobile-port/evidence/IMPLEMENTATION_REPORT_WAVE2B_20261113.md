# FEAT-081 Wave 2B implementation report

**Status:** Bounded 2B rework complete; awaiting coordinator rework post-run. Wave 2B is launched but not accepted. 2A passed its coordinator post-run; Wave 2 remains uncommitted.
**Date:** 2026-11-13
**Branch / HEAD:** `feature/fe-mobile-remediation` / `3c75b10d602d6262dc428706c8bdae92c7a0a8ff` before 2B edits.
**Authority:** Addendum 7 of `approvals/TASK_APPROVAL.md`; approved `plan/PLAN_REVISION_3.md` (34,224 bytes, SHA-256 `73A5873DB1F37366A7A4C69C97ED2F4A81B565C3777E10C3C0F63341FF41DA1E`). The owner authorized the two new pure-helper/test paths and this report path in Addendum 7.

## Scope and implementation

The seven approved 2B E paths were updated, and the owner-authorized `parentFlowV1.ts` / `parentFlowV1.test.ts` paths were added. The helper module is framework-free and contains the decisions for profile-page merging/cursor handling, explicit-ID selection, pending-deletion reconciliation, lesson-pin gating, and safe profile/error messages. Its Vitest tests use synthetic records only.

The controller now loads all V1 profile pages by following `next_cursor`, creates a profile and reads it by ID before selecting it, and patches with the V1 revision contract. Deletion requests remain visibly pending after 202 and reconcile through GET-by-ID. Action identities are retained for retries of the same profile/run/context action. The Home screen receives the selected profile explicitly from `ParentExpoApp`; it does not derive the selected child from the profile array.

The topic continuation enters the pre-drawing context path without requiring a photo or consent policy. StoryRun creation uses the V1 profile, topic, adult idea, and complete lesson-version pin; the returned server context is displayed and requires an explicit adult confirmation. A retry after a failed create uses the retained action identity. The confirmed context screen offers a separate continue control; the owner-run acceptance path must stop immediately after successful confirmation per 2B-AC6. Activity suggestions are a no-op and the existing Activity skip remains wired. This path does not automatically call drawing-understandings or story-revisions. `OWNER_MODAL_CALL_APPROVED=NO` remains in force.

Profile create/edit displays only localized safe field errors. The controller maps role/store/stale/state-transition/active-run errors to safe messages and does not display raw service messages or child payloads. Consent-policy and data-authorization requests/actions were removed from the controller and the migrated profile screens. The Wave 1 home profile count/title/action copy remains in place, with the active-child label coming only from the explicit selected-profile prop.

The owner subsequently authorized a text-only update to `TopicScreen.tsx` in Addendum 8. Its text now describes continuing to context and reflects that a lesson is required. No logic, prop, or layout was changed in that file.

## 2B code/test file pins

The before pins are the approved 2B E rows in Revision 3, rechecked during launch preflight. The two N rows were absent before this launch. After values below are from the final source review for this report.

| Mode | Path | Before bytes / SHA-256 | After bytes / SHA-256 |
|---|---|---|---|
| E | `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts` | 26,476 / `E9626384DC22C9F8A2F74E9F5683D9F53DACE6596DF8FE16A80CE49CCDC3ABEF` | 31,132 / `F3F0A76ABBEF26C901554129D947B04C51BAE3EF2C486EC3497E26928901CDE9` |
| E | `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx` | 15,960 / `7319EFF269ED8C714E7AC1AD5F5BB91277E4F3ECB022E59473169C20F9D84C12` | 16,092 / `9A3CF7D23371323B33CB7ABAC806A354973C0CEDC4ED9567F16160168E046D77` |
| E | `apps/ui-mobile/src/parent/presentation/screens/ContextScreen.tsx` | 2,499 / `B1E96B75C4E2396CDE249A4D7B191D22F50F673A6490A3CDDF0C6F5B715758B2` | 2,765 / `94B1EE1C22BB4F51256A7BF297F4211279A3578D0D030368BF53481316394C38` |
| E | `apps/ui-mobile/src/parent/presentation/screens/ProfileFormScreen.tsx` | 4,780 / `99EC05ABBE0C0460668CEE8418B3CF071945580ADC28311EE72A54EC12BA59E6` | 3,169 / `C20BDE89B47BFF70F7389E9D8694952FE648B45B0A70ED36540D9B4CF5D6630F` |
| E | `apps/ui-mobile/src/parent/presentation/screens/ProfileScreen.tsx` | 3,928 / `36C7C0732AF25DFAC7911C9B44E55253C2A358EB05CC1BDB03CCF5A869139773` | 4,019 / `66E39128D43B3D5E4F497785B4E986C82E23BFC4D1CC91771F6F43B8422D4CA4` |
| E | `apps/ui-mobile/src/parent/presentation/screens/ProfileSharingScreen.tsx` | 3,771 / `F0BA4F7FA51E887161CFBF88DC1A553540596616B7DAFBE35990FA75E494C1C4` | 3,529 / `A9EB79B7BC2C5E1EEFF8304299F37C251BF285DD5500F673194C67064773CA29` |
| E | `apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx` | 4,349 / `A09E8BC37C30DCFB293B68172119DB62C06DF93D1201C068BCC79958433B28E3` | 4,838 / `A4A29FCA5B3EF090A22779214939A0DE6165F96276C9AEA58E0C2E6CD4632B9F` |
| N | `apps/ui-mobile/src/parent/presentation/navigation/parentFlowV1.ts` | Absent | 6,010 / `7D6BB96BCFC7FB47706A8A10B4DED73FD8D3BE313B0E3AD61253DEDC855012DB` |
| N | `apps/ui-mobile/tests/parentFlowV1.test.ts` | Absent | 5,902 / `9BB4835948ECDF8A6C6BFCD637E902410AB64D2656A07CB78BC2EE19FCB8DF26` |
| E (Addendum 8 text-only) | `apps/ui-mobile/src/parent/presentation/screens/TopicScreen.tsx` | 6,533 / `A479B3D5F22E4E68133EB02CA419AE6D3BD7104E1E10BB342BCD7C37267CDC5F` | 6,509 / `EA17130D3CB1FF397446820B22AEA8A9E32841DE81820009FF5BD90AD3D7F183` |

## H-pin and 2A preservation review

All nine shared H pins were re-hashed after the 2B source edits and match the approved Revision 3 values:

| Path | Bytes | SHA-256 |
|---|---:|---|
| `apps/ui-mobile/package.json` | 2,081 | `AC8C5AB17D61B4DD126D28D9918CB4E4EB5C40EEFD3B4C965D9597294B9CD9FF` |
| `pnpm-lock.yaml` | 470,780 | `5D778524730134CAFE360564408CBF45030B476C99A69CCD32897BAB55559A72` |
| `apps/ui-mobile/app.json` | 1,560 | `9489E92A02306F6F0C1F575F3FF1C1FB9331BCB58ED2FD52E49880781F2D0651` |
| `apps/ui-mobile/app.config.js` | 1,578 | `8D78BFAE71EF705299603BD4F6FBE74388756BBEEE93A1C6F1C4D99341ED1F43` |
| `apps/ui-mobile/metro.config.js` | 2,145 | `068C704CC6F14F15178424B584DF4FD36169C221A57C534FD39D59C209E7B5A1` |
| `apps/ui-mobile/tsconfig.json` | 147 | `B16D29C183DA613864125B17F2C6EC4E19419EF3E47E7C207FD8E7622F941130` |
| `apps/ui-mobile/src/parent/presentation/components/ui.tsx` | 11,444 | `722636038EE8CBDFA36A90F6D102ABB4F69A43DC5B6848978EEC8795DFFDB773` |
| `apps/ui-mobile/src/parent/infrastructure/config.ts` | 1,049 | `F0C1E0198460E9A432E81D9E8724BCC35CD030CA8C411F2050503F1C87C0FF07` |
| `apps/ui-mobile/src/parent/infrastructure/auth/ParentAuth.ts` | 10,305 | `BBFEEF77C3CABD2632AFE7EE96D6996509C809BB8521FBD80326223961DD6077` |

The seven 2A E files and two 2A N tests retain the post-rework hashes recorded in `IMPLEMENTATION_REPORT_WAVE2A_20261113.md`. No 2A, H, R, or pinned FEAT-081 record was edited during 2B implementation. `PLAN_REVISION_3.md` remains 34,224 bytes / SHA-256 `73A5873DB1F37366A7A4C69C97ED2F4A81B565C3777E10C3C0F63341FF41DA1E`.

## Acceptance criteria and verification

| Criterion | Status | Evidence / next step |
|---|---|---|
| 2B-AC1 | IMPLEMENTED BY SOURCE; NOT RUN | Controller follows all pages and uses create-then-GET-by-ID. Coordinator test/typecheck run remains. |
| 2B-AC2 | IMPLEMENTED BY SOURCE; NOT RUN | Safe localized profile errors and visible DELETE_PENDING/GET-by-ID reconciliation are wired. Runtime behavior is not yet checked. |
| 2B-AC3 | VERIFIED BY SOURCE REVIEW | ParentExpoApp passes selection by explicit ID; HomeScreen reads only its `selectedProfile` prop for the active-child label. |
| 2B-AC4 | IMPLEMENTED BY SOURCE; NOT RUN | Complete pin gates V1 run creation; ContextScreen displays and explicitly confirms the returned snapshot; Activity suggestions are not called. Coordinator suite remains. |
| 2B-AC5 | REWORK RUN PENDING | Coordinator invocation 4/5 passed tests but typecheck found the ProfileScreen `SecondaryButton` prop mismatch. One test and typecheck rework run remains (5/5); one owner final run for each validator and `git diff --check` remains. |
| 2B-AC6 | OWNER RUN PENDING | Use synthetic profiles and the approved scratch/integration service; stop immediately after successful context confirmation and before drawing-understandings. |
| 2B-AC7 | VERIFIED BY SOURCE/PIN REVIEW | The seven 2B E paths and two owner-authorized N code/test paths were changed/added, plus the TopicScreen text-only exception authorized by Addendum 8. All H hashes match; no path is staged or committed. Authorized report/status/context/ledger records are updated separately. |

## NOT RUN and NOT VERIFIED

Codex did not run tests, typecheck, validators, `git diff --check`, install, Android/ADB/Gradle/emulator commands, or network access. No stage, commit, or push was performed. The final 2B rework test/typecheck run and final validators/diff check remain coordinator/owner actions under the recorded ceilings.

The owner-run scratch/integration flow, route availability, role-store readiness, usable lesson data on that service, and the merged `app.py` error shape are **NOT VERIFIED**. The owner should use only synthetic profiles and stop after context confirmation while `OWNER_MODAL_CALL_APPROVED=NO`. This checkpoint does not claim full Parent story completion or Android runtime acceptance.

## Coordinator post-2B review and bounded rework — 2026-11-13

The coordinator ran the post-2B suite before this rework (invocation 4/5). `pnpm run test` reported 7 files / 52 tests passed and `UI_COPY_AND_RECOVERY_VALID`; stdout was 628 bytes / SHA-256 `3FF0E0E8F869264D2C37971F5957EE54BBF980CA4596E2B40D874E236A222D93`. `pnpm run typecheck` reported one TS2322 at `ProfileScreen.tsx(67,13)` because the call passed `busy` to `SecondaryButton`, whose shared prop type accepts only `label`, `onPress`, and optional `disabled`; stdout was 462 bytes / SHA-256 `65F77633BF2A331072B35FA76618B5A56C6895D70C64EC00E3DBA75467597358`.

The fix removes `busy` and uses a localized changing label plus `disabled` while the GET-by-ID reconciliation is in flight. The shared component prop declarations were reviewed across all 2B screens: the remaining `busy` props are only on `PrimaryButton` or screen component props, and all `SecondaryButton`, `ConfirmButton`, `TextButton`, `Notice`, `Field`, `Card`, `ScreenFrame`, and `ChoiceRow` props match `components/ui.tsx`. `components/ui.tsx` remains byte-identical.

Addendum 8 authorized TopicScreen text-only changes. Its pre-edit pin was 6,533 bytes / SHA-256 `A479B3D5F22E4E68133EB02CA419AE6D3BD7104E1E10BB342BCD7C37267CDC5F`; after text edits it is 6,509 bytes / SHA-256 `EA17130D3CB1FF397446820B22AEA8A9E32841DE81820009FF5BD90AD3D7F183`. Only visible strings changed: photo-required/photo-capture wording is removed, the continuation now says context, and lesson copy no longer says that choosing a lesson is optional. No logic, props, or layout changed. The copy was checked against the rules in `scripts/validate-ui-copy.mjs`, which was read but not run.

The owner authorized one additional coordinator test run and one additional coordinator typecheck run for this 2B rework only, making each ceiling 5 total. The post-2B run above is consumed as 4/5; the rework run is 5/5. The final owner-run validators and `git diff --check` remain one invocation each. Codex ran none of these checks. The test result from invocation 4/5 predates these rework edits and is not a post-rework result.

Addendum 8 was appended to `approvals/TASK_APPROVAL.md` from the recorded pre-append pin 30,117 bytes / SHA-256 `3123895D0E3122500EFAD65A9B93E551ADBBF6CC90F9EC2FA54B45B815CCACAB`; the resulting file is 33,408 bytes / SHA-256 `DD0AE7A3E219EE4A6FF2DC362F07BDD3E45AADE8BE6EDA1FAE7CCD6A3A20E390`.
