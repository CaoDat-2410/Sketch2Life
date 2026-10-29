# Evidence index

- Latest owner decision: `approvals/COMPONENT_ACCEPTANCE.md` accepts only
  `SKETCH_REVIEW_COMPONENT_OFFLINE`, based on `notes/BE205_CODEX_REREVIEW_20261019.md` and its
  metrics. BE2-05 remains IN_PROGRESS / NOT_DONE; runtime and integration gates remain open.
- Publication plan: `evidence/notes/BE205_PUBLICATION_PLAN_20261019.md` (20 groups) covers the
  complete publishable inventory exactly once. Person 2 authorized execution and fast-forward to
  `feature/be2-01-07`; the ignored local publication receipt records the actual result.

- Latest (Codex independent re-review): notes/BE205_CODEX_REREVIEW_20261019.md +
  metrics/BE205_CODEX_REREVIEW_20261019.json — RV-CR01..05 closed, 0 P1/P2; independent
  verification and remaining offline/runtime limits. Component still awaits owner acceptance.
  Ignored local/codex-rereview-20261019/ contains Codex logs, JUnit XML and review probes.

- Executor review-fix evidence (Claude, round 1): `notes/BE205_REVIEW_FIX_EVIDENCE_20261019.md` +
  `metrics/BE205_REVIEW_FIX_CHECKS_20261019.json` — RV-CR01..05 fixed, checks, before/after probes;
  handover `notes/BE205_CLAUDE_TO_CODEX_HANDOVER_20261019.md`. Ignored `local/fix-20261019/`
  holds probe before/after outputs, the per-case fence runner, the check runner and all JUnit/logs.

- Initial Codex review: notes/BE205_CODEX_REVIEW_20261019.md + metrics/BE205_CODEX_REVIEW_20261019.json
  — NEEDS_CHANGES,1P1/4P2; independent suites and executable counterexamples; not acceptance.
- Ignored local/codex-review-20261019/ — review checks/JUnit, preserved probe scripts/output,
  baseline XML inventory audit and CLAUDE_BE205_REVIEW_FIX_PROMPT_20261019.md.

- `notes/BE205_IMPLEMENTATION_EVIDENCE_20261019.md` — K1–K7 implementation, acceptance → test
  mapping, checks, interpretations for review, open gates.
- `metrics/BE205_CHECKS_20261019.json` — check results and SHA256 snapshot of the new source,
  tests, fixture, approved plan and approval.
- Ignored `local/approval-inputs/` — byte-exact planning/approval inputs and Codex reviews.
- Ignored `local/checks-20261019/` — raw pytest logs/JUnit, validator logs, baseline comparison.
