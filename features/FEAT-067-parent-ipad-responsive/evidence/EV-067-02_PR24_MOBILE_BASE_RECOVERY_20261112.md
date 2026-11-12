# FEAT-067 evidence — PR #24 mobile base exclusion and recovery

The owner instructed that PR #24 take apps/mobile and apps/ui-mobile from dev, with apps/ui-mobile at dev commit 34b92194867e915040aae1a1178dee0e526a60c3.

The updated feature/fe-ui-full-remediation tree does not carry commit 4f5d7f5f27b612efc7b6424f1cc939b124703250 or the FEAT-079 feature files. The update is a descendant of the existing target baseline 39321d1787b58969bb99f864d680bcc2fcb2f4b9, so the commit and FEAT-079 files remain recoverable from branch history. No history rewrite is used.

To restore the prior apps/mobile tree:
git restore --source=4f5d7f5f27b612efc7b6424f1cc939b124703250 -- apps/mobile

To restore FEAT-079:
git restore --source=39321d1787b58969bb99f864d680bcc2fcb2f4b9 -- features/FEAT-079-mobile-expo-migration