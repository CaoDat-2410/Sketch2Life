# Phase B B1 decision record — scoped Codex review

- Date: 2026-10-15, Asia/Saigon. Branch: feature/be2-01-ai-job-foundation.
- Result: **VALID_PENDING_OWNER_DECISIONS after two documentation clarifications**.
- Review: Codex primary + independent phase_b_persistence_review, read-only peer.
- Input: decision record rev1 sha256
  `8950807d7f72b66579dd85c34e4d47b6f2c932b8171ec63b85b037b68b4ca994`.
- Plan rev3 remains design-review PASS. No new code finding, business card or plan revision.

## Clarifications applied in record revision 2

1. G3-D7 said P2 role-owner acceptance was mandatory, but §6 allowed a project-owner directive
   for Q1–Q8. Both now use the same explicit-decision rule. A real directive must adopt/assign
   the versioned component contract and accept ASSUMED_CONTRACT proof; merely picking preferred
   D7 is insufficient. It never proves P2 concurrence, actual adapter/adoption or integration.
   Those remain separate B-12 evidence. No decision has been supplied by this correction.
2. Diagrams were deferred until D3/D7 choices. The plan requires adopted decisions for B1 exit,
   but proposed diagrams can be drafted from the reviewed preferred design now. Their current
   state is still NOT_STARTED. The next Claude prompt prepares the seven existing flows and
   crash-window table in one evidence file. Reconcile them after actual choices; no automatic
   B1 completion or B2 implementation.

The fixture profile is consistent with the proposal: 40s worker capability TTL =5+30+5;
three publishes per attempt are separate from three policy attempts; notice bound100 covers
normal multi-page volume and explicit oversize failure. No production policy is adopted.

## Independently verified evidence

- Current HEAD and local origin tracking ref resolve to `882e904ef103ef1c702ac14a9927420909fea423`.
  This verifies local Git refs; no network fetch/push was performed.
- All three plan/ADR/port rev3 hashes and the five bound inputs match the B1 summary.
- All24 Phase A historical hashes match HEAD. Working tree differs only at
  `backend/tests/unit/test_ai_job_q00_followups.py`: exactly one trailing newline removed,
  old sha256 `ecc9638cf84d7ea41f6888c6d14bc6fccd075e1174cb722f511d474a74d05269`, new sha256
  `9a1f5ad64c00ba7298fb107c38d79043dabafb512e4e311b86a036570e654b4b`.
  The other session's EOF disposition is retained. This review verifies the byte change;
  the separate session's approval claim is not new approval given in this chat.
- Backend/tests/fixtures/Phase A approval/approved plan and publication .gitignore were not
  changed by this review. Historical B1 rev1 checks remain a dated snapshot, not overwritten.
- Runtime/live-route tests NOT_RUN in this review. Owner inputs and G1–G5 remain pending;
  ACTIVE Q00; Phase B implementation NOT_STARTED/UNAPPROVED.

Actual docs checks and current hashes: `metrics/PHASE_B_B1_CODEX_REVIEW_CHECKS_20261015.json`.
Repeated receipts live only in `local/phase-b-b1-codex-review-20261015/` under the existing ignore.
