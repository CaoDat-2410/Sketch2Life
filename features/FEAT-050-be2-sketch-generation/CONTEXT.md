# Feature context

- Status: APPROVED (plan revision 5); SK1 component ACCEPTED offline 2026-10-18 with owner
  dispositions (approvals/SK1_COMPONENT_ACCEPTANCE.md), published on milestone branch 04 at
  6ab7abf. Canonical working branch is feature/be2-01-07; six-document routing publication
  authorized 2026-10-19 (DECISIONS). BE2-04 IN_PROGRESS / NOT_DONE; no next ACTIVE card selected.
- Owner: Person 2 executor lane BE2-01–07 (card BE2-04); BE2-08–14 belong to the second executor.
- Goal: BE2-04 real Sketch pipeline (FEAT-040 card), first as the offline component checkpoint
  SKETCH_COMPONENT_OFFLINE (SK1): DATA-23 SketchProposal producer over fakes.
- Scope: plan/PLAN.md (approved bytes plan/PLAN_REV5_APPROVED.md) — domain, DATA-23 contracts,
  ports/service, handoff A resolver over BE2-03/BE2-02 public reads, BE2-01 sketch jobs,
  attempt-keyed staging, decision token, coordinated artifact port, chain builder and router.
- Non-goals: real model/provider/decoding/safety, adopted taxonomy, SQL/queue/durable runtime,
  BE1 artifact admission/delivery, 05 moderation/review, 06 Child response, routes/UI, P4
  composition, BE2-14 adoption, actual provider deletion.
- Dependencies: BE2-01 (WAITING_STUDIO), BE2-02 C1/C2 (accepted components, PARKED), BE2-03 A1
  (accepted component, card IN_PROGRESS); BE1 owner facts ASSUMED_CONTRACT; BE2-14 policy/copy
  seams not merged (user wires later).
- Risks: rebuilt A1 composition can drift (guarded by SK-C11); fake coordination proves no DB
  behaviour. The last recorded inventory of the second lane already duplicates FEAT numbers
  048/049/050 and includes FEAT-051. Shared feature-number allocation and cross-lane mapping
  remain undecided; do not allocate max+1 or rename approved historical evidence.

## Context snapshot

- 2026-10-18: owner approved SK1 on plan revision 5 (verbatim approvals/TASK_APPROVAL.md);
  branch `feature/be2-04-sketch-generation` created from BE2-03 tip 113cdf9 in worktree
  `.worktrees/be2-04-sketch-generation`. Planning inputs (draft 1, revisions 2–5, Codex reviews,
  probes) are in FEAT-049 `evidence/local/be204-preparation/` (ignored, history only).
- Mapping: card BE2-04 → `features/FEAT-050-be2-sketch-generation`, branch above, base 113cdf9.
- Sources: Master SRS DATA-20/21/22/23/24/25, UC-017/019/020, B19.2/B19.10, B21.1/B21.5;
  FEAT-040 BE2-04 card; FEAT-044 BE2 roadmap §3.1/§4/§6.1; FEAT-048 C1/C2; FEAT-049 A1.
- 2026-10-18: Codex addressed Claude findings F-1/F-2/F-4/F-5/F-6 and the R03 test/evidence issue;
  added R11 fault injection, P08/P11 and N23 chain coverage, and C05 registry-report coverage.
  Latest focused SK1 is 166 passed; X01–X03 are 875 passed / 3 skipped. Ruff, strict mypy and
  repository validators pass. R31/R33 and several contract/chain mappings remain partial; the
  F-5 builder deviation needs owner disposition. Await independent Claude re-review; this is not
  owner acceptance and does not close SK1.
- 2026-10-18 (Claude follow-up 3, requested by Person 2): fixed P3 (lost-link orphan cleanup now
  carries the proposal's own reason, fallback SCHEDULE_REFUSED) with regressions; added
  completion-generated R31/R33 variants, P02/P06 chain tests and a producer-built C06 example with
  an equality test; recorded exact mapping for remaining partial rows. Focused 175 passed;
  X01–X03 875 passed / 3 Pillow skips. Evidence `evidence/notes/SK1_CLAUDE_FOLLOWUP3_20261018.md`.
  Awaiting Codex review; F-5, partial rows, A1 callback end-to-end and N16 remain open. Person 2's
  choice of a shared BE2-01–07 working branch is planning only and does not accept F-5 or SK1.
- 2026-10-18 (Claude follow-up 3a): fixed the Codex P2 on R31 (commit-boundary handshake +
  committed-state observation; mutation probe proves a no-coordinator sink fails) and corrected the
  C06/P09 wording. Focused 175 passed. Awaiting Codex review; F-5 and residual decisions open.
- 2026-10-18 (Codex follow-up 3A focused re-review): PASS; F3-R31/N1/N2 closed. Test-only delta
  verified against all 15 source/test/fixture hashes. Independent focused175/0skip, Ruff and strict
  mypy pass; both broken-sink probes rejected. Historical CRLF review metrics remain pinned and
  require byte-preserving publication handling. F-5/residual dispositions and SK1 acceptance remain
  owner decisions; no Git publication or shared branch created.
- 2026-10-18 23:15 +07:00: owner accepted SK1 (offline component) on the snapshot matching the final
  Codex focused review; F-5 accepted as fixture-only deviation; N04/N08/N11 chain and C03/C03b
  contract column remain PARTIAL; A1 callback end to end NOT_RUN (future integration gate); N16
  accepted as fixture residual. Verbatim in approvals/SK1_COMPONENT_ACCEPTANCE.md. Uncommitted;
  commit plan evidence/notes/SK1_PUBLICATION_PLAN_20261018.md awaits review. Next after an
  authorized commit: the shared branch feature/be2-01-07 from that commit (not created).
- 2026-10-19 00:15 +07:00: SK1 (offline component) accepted 2026-10-18 and published: 7 commits ba93c20..6ab7abf pushed to `origin/feature/be2-04-sketch-generation` (no force; receipt in ignored `evidence/local/sk1-publication-20261018/push.json`). Shared working branch `feature/be2-01-07` created 2026-10-19 00:15 +07:00 from exactly 6ab7abf in worktree `.worktrees/be2-01-07` (local only, no upstream, not pushed). Workflow recorded in DECISIONS; WIP1; no next ACTIVE card chosen.
