# Wave R R0 Implementation Evidence

Status: Person 2 launched R0. Its implementation is ready for the coordinator post-run. This report records source changes only; Codex did not launch a separate checkpoint or verification command.

## Preflight

- Worktree: mobile; branch feature/fe-mobile-remediation; HEAD f193d4abcf45e8b8e62a5c7d2d29d6978f4a342d.
- Launched source: features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_7.md, 70,512 bytes, SHA-256 7979A7A990C36F159303F3B011D56626CCAA1AB998A6C7C9C7CB25F47ED024C9.
- The R0 handoff pins matched before implementation: DECISIONS.md 25,930 bytes, SHA-256 EAB5F1F30B08CCB50E3A081FE85C0D4F5E6A453BE68E320A78C6E17D2DBE43C8; approvals/TASK_APPROVAL.md 42,374 bytes, SHA-256 647B9891CEB65DF652CC00D887E3B4D652DEB8EB3D5E2F107F6D49E195F0A007.
- The plan’s DECISIONS.md and TASK_APPROVAL.md R rows are their pre-append pins and are expected to differ from the current handoff pins above. Their contents were not changed for R0.
- Before implementation, all eight N paths were absent. The BE handoff and no-Modal test log R rows were checked in the main checkout as directed.
- At final source review, every unchanged plan pin rechecked with Get-FileHash: 41/41 untouched E rows, 17/17 H rows, and 22/22 R rows. The two R0 E rows are intentionally changed. The two pre-append decision/approval R rows are excluded as directed. No other screen file was edited.
- The supplied SRS Rev67 and pre-Wave-R record pins were verified during launch preflight. No authority, context, status, decision, or approval record was changed by R0.
- The launch handoff records coordinator baseline results before implementation: pnpm run test passed 7 files / 59 tests, exit 0; pnpm run typecheck exited 0 with no diagnostics. It records owner validators and git diff --check as exit 0. These are handoff results; Codex ran none of them.

## R0 paths and byte pins

All hashes below are full SHA-256. An absent baseline file has size 0 and the SHA-256 of the empty byte string.

| Path | Before | After |
| --- | --- | --- |
| apps/ui-mobile/src/parent/presentation/components/ui.tsx | 11,444 bytes; 722636038EE8CBDFA36A90F6D102ABB4F69A43DC5B6848978EEC8795DFFDB773 | 22,326 bytes; B9FD8CCFE62D7999F03F172AB4317E77DDD54EDFFA5FAA606D18770E7B6A54E5 |
| apps/ui-mobile/src/parent/presentation/screens/ParentBottomBar.tsx | 2,054 bytes; 4E8CB3F6B92AE8614DBE282E623A4E769CF16574EF0B14CAAC468B3A7C054358 | 2,770 bytes; 901A7D6FC53C744D2F056B6DFA0057770AD3DA0A03BD0C372FFC1257D334F9B0 |
| apps/ui-mobile/src/parent/application/ports/ParentCapabilityPorts.ts | absent; 0 bytes; E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 | 1,343 bytes; 422F09D492B789CF1DEDCCFBB9275A4D363B7CDFA6CA72D69D4E8F3E56D83B5F |
| apps/ui-mobile/src/parent/infrastructure/unavailable/ParentUnavailableCapabilityAdapter.ts | absent; 0 bytes; E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 | 627 bytes; 2FBB304322EF04B1BE2F73B82A71486EA40167BE0418732879C4257F28C9150F |
| apps/ui-mobile/tests/parentSrsBehavior.test.ts | absent; 0 bytes; E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 | 4,520 bytes; 70DA421078EF002CD12FAE92522B3863ECBCD7954D7957102408B4D27C477214 |
| features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R0_20261113.md | absent; 0 bytes; E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 | The final size and SHA-256 are in the completion receipt; a file cannot embed its own final digest without changing that digest. |

R0 uses existing expo-linear-gradient, react-native-svg, and @expo/vector-icons. No package or lockfile, asset, route, provider, or product-module wiring was added. The unavailable adapter is not wired into product code.

## Acceptance criteria

- WR-AC1 — IMPLEMENTED_BY_SOURCE: the restrained-crayon palette and the foreground/fill audit pairs are in apps/ui-mobile/src/parent/presentation/components/ui.tsx:45; apps/ui-mobile/tests/parentSrsBehavior.test.ts:45 contains the contrast calculation for every declared pair. The test was not run.
- WR-AC2 — IMPLEMENTED_BY_SOURCE: button, field, choice, notice, and tab semantics and distinct state cues are in apps/ui-mobile/src/parent/presentation/components/ui.tsx:135 and apps/ui-mobile/src/parent/presentation/screens/ParentBottomBar.tsx:31. Busy is exposed as busy/disabled and is not a confirmed state; selected choices retain a checkmark, and notice tones use distinct symbols.
- WR-AC3 — IMPLEMENTED_BY_SOURCE: 44 dp minimum, 52 dp primary/navigation, and scaling-friendly minimum heights are in apps/ui-mobile/src/parent/presentation/components/ui.tsx:39 and apps/ui-mobile/src/parent/presentation/components/ui.tsx:341; the bottom navigation target is in apps/ui-mobile/src/parent/presentation/screens/ParentBottomBar.tsx:58. React Native font scaling remains enabled by default. Device scaling and clipping review is pending the owner emulator review.
- WR-AC4 — IMPLEMENTED_BY_SOURCE: existing exports, palette keys, props/defaults, callbacks, tab IDs/order, confirmation flow, and StatusBar.currentHeight screen inset remain compatible in apps/ui-mobile/src/parent/presentation/components/ui.tsx:86 and apps/ui-mobile/src/parent/presentation/components/ui.tsx:341. Bottom tab IDs/order remain home, lessons, start, profiles in apps/ui-mobile/src/parent/presentation/screens/ParentBottomBar.tsx:13. ParentJobStageState has no percent/percentage field at apps/ui-mobile/src/parent/application/ports/ParentCapabilityPorts.ts:31.

## Visible-copy comparison

Read-only comparison used the HEAD bytes and working files. The visible Text and static label multiset is unchanged:

- ui.tsx, before and after: ‹, ✓, Quay lại, S, Sketch2Life.
- ParentBottomBar.tsx, before and after: Trang chủ, Bài giảng, Bắt đầu, Hồ sơ, in the same order and with the same tab IDs.

The back control now has an accessibility-only label Quay lại; it adds no visible screen copy. No other visible string was changed.

## Owner emulator checklist

The owner review remains NOT RUN by Codex. On a 6.1-inch portrait device, review:

1. Visible labels and screen-reader labels, including selected tab and selected choice.
2. System text scaling without clipping or overlap.
3. Keyboard/accessibility focus rings.
4. Busy and disabled button appearance and semantics.
5. Status-bar and bottom safe-area behavior.
6. Minimum 44 dp targets and preferred 48 dp primary actions.
7. Local screenshots using synthetic data only.

OI-17 visual sign-off remains deferred until the owner reviews R0 emulator screenshots.

## Read-only command ledger and NOT RUN

- Read-only inspection included Get-Content, Get-Item, Get-FileHash, rg, Select-String, git status, git diff, and git show; the plan’s unchanged E/H/R paths were rehashed with Get-FileHash.
- NOT RUN by Codex: pnpm run test, pnpm run typecheck, any validator, git diff --check, install/package commands, Android/emulator/Gradle/ADB, network, Modal, provider calls, or screenshot capture.
- The coordinator’s post-implementation test and typecheck and the owner’s validators and emulator review remain outstanding.

## Open items

- OI-17 remains open pending owner review of R0 emulator screenshots.
- R1–R4 have not launched and were not changed.
- The repository SRS authority register/copy and the child-gender SRS/backend-contract request remain outside R0 and open.
- OWNER_MODAL_CALL_APPROVED=NO; no backend or provider call was made.

## Post-emulator correction PE1 (2026-11-14)

The owner observed on the emulator Home screen a light-blue status-bar band above a cream empty band and the header.

### Verified causes and correction

- `apps/ui-mobile/android/app/src/main/res/values/styles.xml:7` sets the native base-theme status-bar color to `#EFF6FF`. Before PE1, the JavaScript StatusBar using `palette.background` appeared only in the auth branch of `ParentExpoApp.tsx`; the loading, Home, Lessons, Start, Profiles, and other app branches had no JavaScript status bar.
- `ScreenFrame` in `components/ui.tsx` added `paddingTop: StatusBar.currentHeight ?? 0`. The app uses a non-translucent status bar and does not enable edge-to-edge layout, so the platform already lays app content below the system status bar. That padding created a second cream band.
- `ParentExpoApp.tsx` now renders one dark-content StatusBar with `backgroundColor={palette.background}` in the exported root wrapper, before the shared screen content component. This covers auth, loading, all tab and learning steps, and fallback screens without changing their screen props or callbacks.
- `ScreenFrame` no longer pads by `StatusBar.currentHeight`; its flex and background styles remain. The unused StatusBar import was removed from `ui.tsx`.
- The presentation-wide scan found no other `StatusBar.currentHeight`, status-bar-translucency, or root safe-area inset usage. Remaining `paddingTop` declarations are internal spacing: ScreenFrame scroll content below its header, multiline input content, ParentBottomBar item spacing, lesson-gallery item separators, and StoryScreen scene separators. AuthScreen keeps its centered uniform padding; the ParentExpoApp loading view remains centered. None adds another system-bar inset.

### PE1 file pins

| Path | Before | After |
| --- | --- | --- |
| apps/ui-mobile/src/parent/presentation/components/ui.tsx | 22,326 bytes; B9FD8CCFE62D7999F03F172AB4317E77DDD54EDFFA5FAA606D18770E7B6A54E5 | 22,273 bytes; 51BAE1F8E81B560AFEA5389864FE98FC44CB0104C7492FE4CC7D861663A829E8 |
| apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx | 17,475 bytes; DDC0BFD88128DD66FD40D0603B2E735FF60F5BC541E884493641AA56D8722A50 | 17,590 bytes; FCB0B797C424AB6176B59E88034B954ADA01B7B3544ADAAFCC41ECF7227DA8AA |
| apps/ui-mobile/tests/parentSrsBehavior.test.ts | 31,174 bytes; CD126B44F1DE7F5CE0D1C4B585C5410BB1B6EF71D0A2D2AB4DB1EB1C9994DC8A | 31,855 bytes; 85B3C7BCD509753F9143D1DC79FD2B09743580A4D5A83907AA612818BF008BA6 |

No copy string was changed. No native Android file, app.json, package file, ParentBottomBar, screen file, or H path was changed. The base native theme color remains because the app-level StatusBar supplies the approved palette background at runtime; a native edit would be outside the PE1 allowlist. No dependency or provider/backend call was added.

### Assertion review and verification state

- Added source assertions that match the exported wrapper's exact StatusBar and shared-content structure, confirm the StatusBar precedes the shared content component, and confirm `ui.tsx` contains no `StatusBar.currentHeight`. Each expected source line was checked with `rg -F`; the decoded multiline assertion matched the current wrapper exactly.
- Re-read the full `parentSrsBehavior.test.ts` (469 lines): 0 duplicate import bindings and 0 duplicate same-scope declarations. The new assertions operate on `readFileSync` strings and numeric `indexOf` results; they add no nullable or unchecked-index access.
- Plan Revision 7 H rows re-hashed with `Get-FileHash`: 17 checked, 0 mismatches. DECISIONS.md after D-018 is 39,150 bytes / SHA-256 A0CA10FDA558EF8024028E17507CCD1C87947F122E6E1C3045C05AAE52C7498D. Addendum 16 records the pre-append TASK_APPROVAL.md pin; no post-append TASK_APPROVAL.md pin is recorded.

tests, typecheck, validators and diff-check were NOT run by Codex. The owner emulator re-check is pending and is limited to the top bar area and the Home, Lessons, Start, and Profiles tabs. OI-17 visual sign-off remains deferred; OWNER_MODAL_CALL_APPROVED=NO.
