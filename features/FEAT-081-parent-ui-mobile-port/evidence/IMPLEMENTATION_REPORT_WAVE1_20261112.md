# FEAT-081 Wave 1 implementation report

- Date: 2026-11-12, Asia/Saigon
- Status: IMPLEMENTED / AWAITING OWNER ACCEPTANCE
- Worktree: `D:\GitHub\Sketch2Life\.worktrees\mobile`
- Branch / HEAD: `feature/fe-mobile-remediation` / `1f5bb0b5b1ab501a7120598a7e6e0de75217ddb3`
- Plan: Revision 2, SHA-256 `DA807873F2AFEA2BC9A86457AE9BB13A3C4CE90F5E9388B816A5676EEACE3ECC`
- Command ledger: ignored `tmp/fe081-impl/COMMAND_LEDGER.md`

## What changed

- Added a pure catalog view-model over the existing `LessonSummary` and `ParentProfile` types. It keeps the existing home profile-summary copy in one place, builds topic filters, sorts matching lessons by title, and derives the empty-catalog state.
- Updated HomeScreen and LessonGalleryScreen with native React Native presentation. Home retains its current profile-summary copy and callbacks. The gallery adds topic chips, sorted lesson rows, and clearer native lesson-detail sections while keeping invitation, loading, selection, and back actions.
- Added Vitest tests with synthetic profile and lesson fixtures. They cover the existing home copy, topic options/filtering, title sorting, empty catalog, and stale topic fallback. No active-child label is asserted.
- Added no dependencies, API changes, assets, CSS, React DOM, Expo imports, or sample files. Props and the `ParentExpoApp.tsx` call site remain unchanged.

## Owner-directed deviation

The sample P01 shows an active-child selector; HomeScreen has no selected-child input and does not receive the controller's profile. Adding it needs ParentExpoApp.tsx, which is outside the Wave 1 allowlist. Owner chose Option A on 2026-11-12: label deferred. The item moves to a later wave that is separately approved to touch ParentExpoApp.tsx (together with useParentController.ts / workflowTypes.ts if that wave needs them). The active-child label is not applicable to Wave 1 and is not marked passed.

## Changed code files

| Mode | File | Before | After |
|---|---|---|---|
| E | `apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx` | 3,485 bytes; SHA-256 `A48B96CBEE051329EDDDCD557948D0141DF82670E4F54B2ACBC7D14FCA19F277` | 4,349 bytes; SHA-256 `A09E8BC37C30DCFB293B68172119DB62C06DF93D1201C068BCC79958433B28E3` |
| E | `apps/ui-mobile/src/parent/presentation/screens/LessonGalleryScreen.tsx` | 5,529 bytes; SHA-256 `7E49888CAE0F908C5399D05BB6DDE4246184DEB7C3E157869369BC08476BCDDF` | 9,876 bytes; SHA-256 `35D75628DF9220FABA787010E5E40A895FA99AE3A3A34F325E7B752DDFB04003` |
| N | `apps/ui-mobile/src/parent/presentation/screens/catalogViewModel.ts` | Absent | 1,962 bytes; SHA-256 `5BE1210C95C9F1CEBABADEE7DAD2169620B5B438BA85DE24941236DF018630F0` |
| N | `apps/ui-mobile/tests/catalogViewModel.test.ts` | Absent | 3,254 bytes; SHA-256 `8FAA29A92BD4D750C27E2109256611BA3DA8ECFE1BE72044127A81B78699C978` |

The three H pins remain unchanged: `ParentApi.ts` 16,805 bytes / `B448B9F13A153D2F90E1BAD6A284488117B4458223C1239FC2865F850438B918`; `apps/ui-mobile/package.json` 2,081 bytes / `AC8C5AB17D61B4DD126D28D9918CB4E4EB5C40EEFD3B4C965D9597294B9CD9FF`; root `pnpm-lock.yaml` 470,780 bytes / `5D778524730134CAFE360564408CBF45030B476C99A69CCD32897BAB55559A72`. Shared `components/ui.tsx` and `ParentExpoApp.tsx` also remain byte-identical to HEAD.

## Command results and accounting

The coordinator ran both baseline commands outside the sandbox on 2026-11-12 at 21:34 from `apps/ui-mobile`. Codex verified the supplied log hashes.

| Command | Run / ceiling | Exit | Result and log |
|---|---:|---:|---|
| `pnpm run test` baseline | 1 / 2 | 0 | `Test Files 3 passed (3)`; `Tests 26 passed (26)` (storyDraft 4, mainFlowSafety 19, apiRetryIdentity 3); `UI_COPY_AND_RECOVERY_VALID`. Log: `tmp/fe081-impl/coordinator_baseline_run1_20261112T213414/pnpm-test.stdout.txt` (1,453 bytes; SHA-256 `626564EF41E9E494632DF0D27E5D72A3E036BA3ED3707AAA4DF32EC7DB1E722F`). |
| `pnpm run typecheck` baseline | 1 / 2 | 0 | Coordinator reported no diagnostics. stdout is empty; stderr is `$ tsc --noEmit -p tsconfig.typecheck.json`. Log hashes: stdout `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`; stderr `1E7364545B505ADC6EF70012CE70F69A90A7EB05EBB0A0886A63CCEB701BCB27`. |
| `pnpm run test` post-implementation | 2 / 2 | Coordinator-reported pass; exit receipt not supplied | `Test Files 4 passed (4)`; `Tests 29 passed (29)` (mainFlowSafety 19, storyDraft 4, catalogViewModel 3, apiRetryIdentity 3); `UI_COPY_AND_RECOVERY_VALID`. Log directory: `tmp/fe081-impl/coordinator_post_run2_20261112T222628/`; stdout 604 bytes, SHA-256 `2D97391D1258D42349734C031BD38798B87EF9AEB91094128FA43B8DEB7A71C9`. |
| `pnpm run typecheck` post-implementation | 2 / 2 | Exit receipt unavailable | No diagnostics; stdout 0 bytes. The coordinator's verdict rests on the empty diagnostics output. Log directory: `tmp/fe081-impl/coordinator_post_run2_20261112T222628/`. |
| `python tools/validate_harness.py` | 2 / 2 | 0 | `HARNESS_VALID`; `approval_gate=enabled`; `frontend_asset_gate=enabled`. |
| `python tools/validate_repository_security.py` | 2 / 2 | Not captured | Tool returned no output and no exit code. Result is NOT VERIFIED; the validator ceiling is exhausted, so it was not rerun. |
| `python tools/validate_architecture.py` | 2 / 2 | 0 | `ARCHITECTURE_VALID`; dependency direction, mobile isolation, asset gate, mobile AI boundary valid; Firebase data products absent. |
| `git diff --check` | 2 / 2 | 0 | No output. |

After these checks, a final source review removed an unnecessary result-count badge and raised the topic-chip minimum touch height to 48 points. The post-check read-only scan of the final files found no trailing whitespace, Expo imports, forbidden UI-copy terms, or out-of-allowlist app paths. The `git diff --check` ceiling is exhausted, so it was not rerun after those changes.

The baseline test log shows pnpm v11.19.0 automatically ran the workspace install before the script: 268 packages reused and 0 downloaded. The coordinator reported the lockfile and tracked files unchanged. The post-run used `npm_config_verify_deps_before_run=false`; no install ran, and the three H-pin files were re-hashed unchanged. Codex did not run pnpm, tests, typecheck, installation, Gradle, ADB, emulator, Android, skeleton validation, or the UI-copy validator separately. Both test invocations and both typecheck invocations are now consumed.

## Acceptance criteria

| Criterion | Status | Evidence / remaining owner work |
|---|---|---|
| AC1 | Verified by source review | Pure view-model uses only target domain type imports and derives home summary, topic filter, title sort, and empty-catalog state. The authored unit tests were not run by Codex. |
| AC2 | Owner-run complete | Baseline and post-implementation `pnpm run test` passed. The post-run includes `catalogViewModel.test.ts` and `scripts/validate-ui-copy.mjs`; the focused Vitest command remained optional and was not run. |
| AC3 | Verified | Both screens use the view-model; screen Props, callbacks, and `ParentExpoApp.tsx` call sites are unchanged. No controller, workflow type, navigation, auth, API, native configuration, asset, or shared UI file changed. |
| AC4 | Verified | `ParentApi.ts`, `package.json`, and `pnpm-lock.yaml` hashes match their approved pins. |
| AC5 | Owner-run complete | Baseline and post-implementation typecheck outputs had no diagnostics. The post-run launcher did not provide an exit-code receipt. |
| AC6 | Not verified | Harness and architecture validators passed. The repository-security validator was invoked but returned no captured exit/result; no rerun is available under its ceiling. `validate_skeleton.py` was not run, as directed. |
| AC7 | Owner-run pending | Android manual check remains with the owner. Checklist below includes the active-child label as not applicable to Wave 1 (deferred), not passed. |
| AC8 | Verified | Pinned Plan Revision 2 / D-009 / ADR-0023 continue to target `apps/ui-mobile` for FEAT-081. No `apps/mobile` file changed. |

## Owner Android checklist — not run by Codex

Open a new `cmd.exe` terminal and set the Android Studio JDK and SDK for that terminal:

```bat
set "JAVA_HOME=D:\Android Studio\jbr"
set "ANDROID_HOME=D:\Android\Sdk"
set "ANDROID_AVD_HOME=D:\AndroidData\.android\avd"
"%ANDROID_HOME%\platform-tools\adb.exe" kill-server
"%ANDROID_HOME%\platform-tools\adb.exe" start-server
"%ANDROID_HOME%\platform-tools\adb.exe" devices -l
```

In a separate `cmd.exe` terminal, start the configured emulator and wait for it to boot:

```bat
"%ANDROID_HOME%\emulator\emulator.exe" -avd Pixel_6a
```

Then run the Android dev command from a terminal with the same environment:

```bat
pnpm --dir D:/GitHub/Sketch2Life/.worktrees/mobile/apps/ui-mobile run android:dev
```

Check initial, filtered, and empty lesson states; lesson detail and back behavior; text wrapping and scrolling; Android back behavior; accessibility labels and touch targets. **Active-child label: not applicable to Wave 1 (deferred); not passed.** If a command fails, send the exact command and exit code, the first error and Gradle error section, `java -version`, the three environment values above, `adb devices -l`, and the last approximately 100 output lines. Do not include credentials or tokens.

## Handoff

Wave 1 is implemented but not accepted. Coordinator post-run test and typecheck are complete; no acceptance record was written. The owner Android manual check and owner acceptance remain pending. No files were staged or committed, and nothing was pushed or published.
