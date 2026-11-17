# Feature context

- Current (2026-10-19): Person 2 accepted `SKETCH_REVIEW_COMPONENT_OFFLINE` based on Codex
  `CODEX_REREVIEW_PASS_WITH_NOTES`; RV-CR01–05 closed, 0 P1/P2 remaining. Card remains
  IN_PROGRESS / NOT_DONE. Runtime, production, persistence/SQL, BE1, BE2-14 and integration gates
  remain open. Person 2 authorized the exact 20-commit publication plan and fast-forward to
  `feature/be2-01-07`; execution receipts hold the resulting SHAs. See
  `approvals/COMPONENT_ACCEPTANCE.md`, `DECISIONS.md` and the Codex re-review note.
- Status: plan candidate R2 and K1–K7 implementation remain the approved scope. BE2-05 is the
  single ACTIVE slot (WIP1); BE2-07 PARKED. Runtime/production/integration gates remain open.
- Owner: Person 2 executor lane BE2-01–07 (card BE2-05); BE2-08–14 belong to the second executor.
- Goal: BE2-05 moderation and per-Sketch Teacher exact review (FEAT-040 card), first as the
  offline component checkpoint SKETCH_REVIEW_COMPONENT_OFFLINE: DATA-24 CMD-35 for
  `sketch_proposal`, moderation fixture, approved-only Child eligibility.
- Scope: plan/PLAN.md (approved bytes plan/PLAN_R2_APPROVED.md) — 05-owned review store and
  composed DATA-23 projection, composite ETag, Sketch binder over DATA-24 V1, ReviewTarget from
  BE2-04 public `revalidate()`, shared-coordinator decision unit, terminal marker (OD-07-A),
  eligibility/child payload, fake ticket/dispatcher/cache, quarantine intent after commit.
- Non-goals: real moderation/provider, adopted moderation/reviewer policy, BE1 ticket/gateway,
  SQL/durable fencing, routes/UI, BE2-06 Child response, BE2-09/12 reviews, changes to SK1 or to
  DATA-24 V1 bytes.
- Dependencies: BE2-04 SK1 (accepted offline; public service API), BE2-01 foundation fakes,
  BE2-03 A1 coordinator (`AssistanceCommitCoordinator`), BE1 facts as fixtures.
- Risks: fake coordinator proves single-process behaviour only; unbumped owner facts (DI-18) are
  caught only at the next pull read; FEAT number allocated by the owner without cross-lane
  confirmation (mapping at integration).

## Context snapshot

- 2026-10-19 (owner acceptance): offline component accepted on Codex re-review PASS_WITH_NOTES;
  no runtime/integration acceptance and no next card opened. See `approvals/COMPONENT_ACCEPTANCE.md`.
- 2026-10-19 (Codex independent implementation review): focused05 99/99, SK1 175/175 and
  BE2-02/03 405/405 pass,0 skip; correct-backend Ruff, strict mypy and validators pass.
  Diagnostic probes reproduce stale moderation reuse, pre-token authority/policy races,
  warmed-cache exposure, old-approval revival and noncanonical receipt fingerprints.
  Existing approval covers same-scope fixes; no acceptance/publication or next card opened.

- 2026-10-19: owner approved candidate R2 (verbatim approvals/TASK_APPROVAL.md) and allocated
  FEAT-052. Branch `feature/be2-05-sketch-review` created from shared tip 58293f1 in worktree
  `.worktrees/be2-05-sketch-review`. Planning inputs (draft, Rev2, Rev3, candidates, packages,
  Codex reviews, probe) copied to ignored `evidence/local/approval-inputs/`.
- Mapping: card BE2-05 → `features/FEAT-052-be2-sketch-review`, branch above, base 58293f1.
