# Revision 33: Repository stabilization and runtime test preparation

Status: APPROVED_FOR_LOCAL_STABILIZATION, 2026-10-10.
Authority: owner's full repository-cleanup/scoped-commits/LightningAI-setup request.

1. Inventory all staged/unstaged/untracked changes; preserve pre-existing V1 edits,
   rejected/incomplete prototypes and unapproved assets. Verified external backup first.
2. Review dependencies and tests; commit only explicit, independently verified paths.
   Label source tracing, semantic authoring and rig proofs EXPERIMENTAL, never production.
3. Keep valuable artifacts outside Git, without deleting originals. Correct documentation
   privacy leaks, preserve historical metrics and failed visual acceptance.
4. Prepare no-inference local mock / runtime inventory, model-reference interface and
   instructions. Reuse existing Wan adapter; workspace revision remains unverified.
5. Validate security before each commit, regression/lint/types, V1 default/V2 OFF.
6. Treat Windows as code/repository/static-check only. Do not install new
   dependencies there. LightningAI owns dependency installation and GPU
   execution through the real scripts/lightningai setup/verify/test workflow.

Acceptance: audit/backup checksums; scoped local commits with test evidence; complete
remaining-file reasons; setup commands which cannot download models or run inference.
No child upload, paid services, GPU inference, TTS, new story video, push or deployment.
Do not relocate the repository into the private artifact directory without separate approval.

Reports: SKETCH2LIFE_REPOSITORY_STABILIZATION_RESULT.md and
SKETCH2LIFE_LOCAL_LIGHTNINGAI_SETUP.md. Stop after handoff for owner review.
