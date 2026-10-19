# Feature decisions

## 2026-10-19 — owner acceptance of offline component checkpoint

- Person 2 accepted `SKETCH_REVIEW_COMPONENT_OFFLINE` based on Codex
  `CODEX_REREVIEW_PASS_WITH_NOTES` (0 P1 / 0 P2; RV-CR01–05 closed); verbatim instruction is in
  `approvals/COMPONENT_ACCEPTANCE.md`.
- Acceptance is limited to the offline component. BE2-05 remains IN_PROGRESS / NOT_DONE; runtime,
  production, durable persistence/SQL, BE1 authority/ticket, BE2-14 policy and integration gates
  remain open.
- Request a publication inventory and plan with 20 explicit commit groups. This records no
  authorization to stage, commit, push, merge, deploy or start another card.

## 2026-10-19 — publication and shared-branch authorization

- Person 2 approved execution of `evidence/notes/BE205_PUBLICATION_PLAN_20261019.md`, SHA256
  `0ad3c5a32e9ba1f032c51c13711bc3c1e0506ee30b0843c18ace69810a725d18`: stage and create its 20
  exact commits on `feature/be2-05-sketch-review`, then fast-forward `feature/be2-01-07` and push
  that shared branch to `origin`, after verifying the actual remote tip. No force push.
- Verbatim instruction:

  > OK lên plan commit cho tôi đi nếu ok r thì commit xong đẩy qua nhánh gộp kia sau đó lên plan làm task 6

- This authorizes publication of the already accepted offline checkpoint and the shared-branch
  fast-forward only. It does not close BE2-05 runtime/integration gates or authorize BE2-06 code.
  After publication, prepare a BE2-06 plan draft only.

## 2026-10-19 — Codex implementation review (review finding, not owner approval)

- NEEDS_CHANGES: RV-CR01(P1), RV-CR02–05(P2). Independent99+175+405 tests pass, but source-bound
  diagnostic probes reproduce five correctness defects. Report: evidence/notes/BE205_CODEX_REVIEW_20261019.md.
- Fixes remain inside approved K1–K7. Approval, frozen/working plan, original implementation
  evidence and source/test/fixture bytes are unchanged by review. No owner acceptance or Git
  publication inferred; task05 remains ACTIVE, IN_PROGRESS/NOT_DONE, WIP1; task07 PARKED.

## 2026-10-19 — approval and allocation (owner direction, Person 2)

- Approved scope: SKETCH_REVIEW_COMPONENT_OFFLINE on plan candidate R2 (SHA256 ab295305…),
  selections OD-01 A (owner-adjusted), OD-03/04/05/06/07 A, OD-16 accepted, non-blocking
  defaults (verbatim in `approvals/TASK_APPROVAL.md`).
- Feature number: **FEAT-052-be2-sketch-review is the owner's own allocation decision.** Fresh
  inventory after `git fetch` found no FEAT-052 on any branch; the separate confirmation from lane
  08–14 was waived by the owner and is **not** claimed. Collisions, if any, are mapped by the
  owner at integration.
- Workflow (supersedes "code tasks 02–07 directly on the shared branch"): one branch per task;
  the reviewed, accepted checkpoint is merged into `feature/be2-01-07` only by a separate owner
  Git decision (ancestor check, `merge --no-ff --no-commit`, security before merge commit/push).
  Order 05 → 06 → 07; WIP1; BE2-07 PARKED.
- Substitution: BE2-05 becomes ACTIVE while BE2-01 is WAITING_STUDIO and BE2-04 live is not
  available; BE2-05 claims only the offline component checkpoint; runtime 01/04, BE1, BE2-14
  policy, database fencing and integration gates stay open.
- OD-04 deviation: CMD-35 If-Match uses the 05-issued composite ETag instead of SRS "target
  review_revision"; CR-01 to BE2-04 not sent.
- OD-07: A — reject/request_changes terminal for the exact version (immutable marker, D-1 global
  revoke, D-3 current-entry projection). Option B not adopted.

## 2026-10-19 — review-fix round 1 (same approved K1–K7 scope)

- RV-CR01: moderation assessments are append-only and selected by complete identity (exact
  content, pinned ref hashes, moderation policy); only the current-policy assessment admits
  approval/access. Older assessments stay as history.
- RV-CR02: early authority/policy checks are preliminary; decisive authority, policy and the 05
  invalidation generation are read after the decision token and verified by the final hold.
- RV-CR03: the fixture Child cache reauthorizes every hit through 05 eligibility.
- RV-CR04: each review entry pins a monotonic 05 invalidation generation (review-policy and
  review-context epochs); a moved generation makes the entry permanently unusable (no revival on
  value restoration); a fresh decision replaces it. Fail-closed residual: any such publication in
  the organization/session invalidates older approvals.
- RV-CR05: the receipt fingerprint uses the normalized semantic command (NFC/trim reason, sorted
  set-valued fields).
- Evidence: `evidence/notes/BE205_REVIEW_FIX_EVIDENCE_20261019.md`; handover to Codex
  `evidence/notes/BE205_CLAUDE_TO_CODEX_HANDOVER_20261019.md`.

## 2026-10-19 — Codex independent re-review (review finding, not owner acceptance)

- CODEX_REREVIEW_PASS_WITH_NOTES: RV-CR01..05 closed, 0 P1/P2 remaining. Independent
  focused05 117, SK1 175, contract 400/3 skips, BE2-02/03 405; Ruff, both mypy modes,
  validators, diff-check and all 25 pinned hashes pass. JUnit comparison: no baseline case
  lost or changed; 104 added cases pass; baseline failures/errors/skips are unchanged.
- Component remains NOT_ACCEPTED pending owner acceptance; BE2-05 stays IN_PROGRESS /
  NOT_DONE. Runtime/production/integration gates stay open. Report/metrics:
  evidence/notes/BE205_CODEX_REREVIEW_20261019.md and matching metrics.
