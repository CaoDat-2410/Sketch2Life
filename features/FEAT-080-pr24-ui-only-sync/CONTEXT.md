# FEAT-080 context — PR #24 selective UI sync

PR #24 proposes dev as source and feature/fe-ui-full-remediation as base. The owner requested a selective UI snapshot transfer to the existing feature branch rather than updating dev or merging the full dev history.

The approved mobile choice is to take both apps/mobile and apps/ui-mobile from dev. The target branch FEAT-079 record and former apps/mobile implementation are excluded from the resulting tree. Commit 4f5d7f5f remains in the target branch ancestry, so its content remains recoverable from Git history.

The apps/ui-mobile tree is pinned to dev commit 34b92194867e915040aae1a1178dee0e526a60c3. The requested exclusion and recovery note is also recorded under FEAT-067. The full PR is not merged by this task.