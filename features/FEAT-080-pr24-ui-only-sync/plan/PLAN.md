# FEAT-080 Plan — PR #24 selective UI sync

**Status:** APPROVED / IN PROGRESS
**Recorded date:** 2026-11-12, Asia/Saigon

## Objective

Bring the selected UI app snapshots from dev into feature/fe-ui-full-remediation without merging the full dev history or changing dev. Build the result on a local-only temporary branch, update only the existing target branch, then delete the temporary branch and checkout.

## Pinned source and target

- Repository: CaoDat-2410/Sketch2Life.
- Target branch: feature/fe-ui-full-remediation at 39321d1787b58969bb99f864d680bcc2fcb2f4b9.
- Source branch: dev at 1f5bb0b5b1ab501a7120598a7e6e0de75217ddb3.
- apps/ui-mobile is taken from the latest dev tree, whose latest app commit is 34b92194867e915040aae1a1178dee0e526a60c3.
- The target branch history contains 4f5d7f5f27b612efc7b6424f1cc939b124703250, "fix(mobile): rebuild Expo base for emulator compatibility".

## Approved scope

- Create and use a local-only temporary branch based on the pinned target SHA.
- Transfer the dev snapshots of apps/admin-ui, apps/teacher-ui, apps/mobile, and apps/ui-mobile, plus the dev mobile workspace lock metadata.
- Replace the target branch version of apps/mobile with the dev version and remove the target-only FEAT-079-mobile-expo-migration record from the result tree.
- Keep apps/ui-mobile exactly at its latest dev snapshot from commit 34b92194867e915040aae1a1178dee0e526a60c3.
- Preserve target-only UI app trees that dev deletes, including apps/parent-ui, apps/platform-admin-ui, apps/school-manager-ui, and apps/shared.
- Add the task plan, approval, evidence, and status under FEAT-080. Add the requested mobile recovery record to the existing FEAT-067 Parent iPad feature record.
- Record that commit 4f5d7f5f and FEAT-079 are absent from the new result tree while remaining reachable in feature/fe-ui-full-remediation history for recovery. Do not rewrite or discard that history.
- Update only the existing remote feature/fe-ui-full-remediation branch with a fast-forward guarded by the pinned expected SHA. Leave dev unchanged. Do not merge PR #24.
- Delete the temporary local branch and isolated checkout after remote verification.

## Exclusions

- Backend/server/database/migration/deployment/provider/credential changes.
- Applying source-side deletions of target-only UI app trees.
- Updating dev, force-pushing, rewriting history, creating a remote branch, or merging PR #24.
- Running automated tests or builds.

## Acceptance criteria

- AC1: dev remains at 1f5bb0b5b1ab501a7120598a7e6e0de75217ddb3.
- AC2: apps/mobile, apps/ui-mobile, pnpm-lock.yaml, and pnpm-workspace.yaml match their approved dev snapshots; FEAT-079 and the old target apps/mobile tree are absent from the result tree.
- AC3: apps/admin-ui and apps/teacher-ui are transferred from dev; only the whitespace-only trailing blank line in apps/teacher-ui/src/index.css may be normalized to satisfy diff --check.
- AC4: commit 4f5d7f5f remains an ancestor of the updated target branch, so its former files can be recovered from branch history.
- AC5: target-only UI app trees remain present and there are no unresolved conflict markers.
- AC6: required repository validators and git diff --check pass before publication; tests and builds are not run.
- AC7: the existing target branch advances from the pinned SHA without force; PR #24 is re-read and not merged.
- AC8: the temporary local branch and checkout are deleted after verification.