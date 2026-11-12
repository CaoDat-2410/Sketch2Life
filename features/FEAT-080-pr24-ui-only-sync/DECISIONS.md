# FEAT-080 decisions

## D-080-01 — Use source mobile app snapshots

- Decision: use apps/mobile and apps/ui-mobile from dev, with apps/ui-mobile at commit 34b92194867e915040aae1a1178dee0e526a60c3.
- Rationale: owner instruction.
- Consequence: the target branch version of apps/mobile and the FEAT-079 record are not present in the resulting tree.

## D-080-02 — Preserve recoverability of removed target mobile work

- Decision: do not rewrite target branch history. The update commit is a descendant of 39321d1787b58969bb99f864d680bcc2fcb2f4b9, which contains commit 4f5d7f5f27b612efc7b6424f1cc939b124703250 and FEAT-079.
- Consequence: both are omitted from the result tree but remain recoverable from target branch history. Recovery instructions are recorded in FEAT-067 evidence.