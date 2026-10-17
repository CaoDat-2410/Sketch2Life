# FEAT-048 / BE2-12 status

- Status: IN_PROGRESS
- Plan revision: 1
- Implementation status: IN_PROGRESS — C1/C2/C3 component + owned PostgreSQL checks PASS
- Updated: 2026-10-17 (Asia/Saigon).
- Branch: feature/be2-12-content-publication
- Base: 6dcc57ee0b3d053f071c8c92e72aaaee2e98d899
- Completed: owner-goal/source inspection, clean-checkout/base verification,
  feature mapping, revision-1 scope/contract/field/API/persistence/test plan.
- Component checks: 79 new domain/contract tests PASS; selected combined
  foundation regressions 189 PASS; focused Ruff/Mypy PASS.
- C2: owned SQL repository, frozen forward migration and runtime test pack ready.
- Combined selected checks: 211 passed / 0 skipped, including 9 real PostgreSQL cases.
- C2 runner: PASS, PostgreSQL 17.11 with restricted role; child-process restart
  proof; portable cluster/server/credentials cleaned after the tests.
- C3a: 44 new eligibility tests PASS; 136 selected component tests PASS;
  current-source C2 SQL 9 PASS + published-version projection SQL 1 PASS.
- C3a SQL proves published v1 remains selectable with draft v2, recall removes v1
  from new resolution, and immutable history remains. Runtime removed afterwards.
- C3b: all eight content actions wired in application; shared DATA-24 response,
  record/review CAS, guarded duplicate replay and atomic receipts/events/outbox.
- Historical C3b local suite: 293 PASS / 0 skip (183 content, 110 foundation).
- Historical C3b PostgreSQL: 9 C2 + 1 C3a + 8 C3b PASS; C3b includes actual SQL unique
  winner recovery, rollback and edit/review/publish/recall CAS cases.
- C4a: candidate content-only HTTP seam 33 tests PASS; 326 selected local cases
  PASS / 0 skip. All eight content actions, safe errors, strict If-Match/body
  admission and inline OpenAPI verified with injected synthetic identity.
- Full closed CMD-48 dispatcher/delegates and real cross-owner integration:
  INCOMPLETE / NOT_RUN. Candidate content router is not mounted in default app.
- SQL owner ports remain ASSUMED; C4a does not supersede C3 runtime source evidence.
- Planning checks: harness, architecture, security and static AC/action inventory
  PASS; these are not implementation acceptance tests.
- Approval: actual owner accepted revision 1/P1–P4 and continued implementation.
- Remaining: C4 full typed dispatcher/owner delegates/real consumer adoption, C5 audit/handoff,
  and external authority/review/source adapter adoption/runtime gates.
- Next: C5 traceability/handoff audit and owner contract review; do not invent
  preset/AI/core-policy payloads to conceal CR-C4-01.
- C5a audit/handoff prepared against 89426fd: AC01–14 reviewed; full-card NOT
  COMPLETE. Open findings F01–05 tracked in artifacts/ACCEPTANCE_AUDIT_20261017.md.
- F03 local projection CLOSED_COMPONENT_AND_OWNED_SQL: current READ-authorized,
  paginated immutable-proof history with explicit derived stale reasons; owner
  revocation-cause/fencing/adoption remains F02, not fabricated by a boolean port.
- Latest selected local suite: 354 PASS / 0 skip (244 content, 110 foundation).
- Latest PostgreSQL: 9 C2 + 1 projection + 13 command/history PASS; source-pinned
  history/resubmit/edit/recall/pagination tests; temporary runtime cleaned.
- Next: resolve/review remaining F01/F02/F04/F05 gates, including full dispatcher,
  real owner adapters/consumers and integrated acceptance. P3 reintroduction now
  matches approval: new draft version/fresh review, never restore retired version.
- Revalidation: 326 selected local PASS / 0 skip (5.42s), Mypy 8 source files
  PASS, focused Ruff PASS, all 15 latest C3b runtime dependency hashes still match.
- Evidence: evidence/notes/C2_LOCAL_POSTGRES_20261017.md; first runtime FAIL
  retained separately from final PASS and does not override it.
- C3a evidence: evidence/notes/C3A_ELIGIBILITY_20261017.md and matching metrics.
- C3b evidence: evidence/notes/C3B_COMMANDS_20261017.md and matching metrics.
- C4a evidence: evidence/notes/C4A_HTTP_20261017.md; artifacts/CONTENT_HTTP_CANDIDATE.md;
  artifacts/CR_C4_OWNER_DELEGATES.md (OPEN, no owner sign-off inferred).
- C5a handoff: artifacts/BE2_12_HANDOFF_20261017.md; five remaining work packages
  are not five new backlog cards, and handoff is not acceptance closure.
- F03 evidence: evidence/notes/F03_REVIEW_HISTORY_20261017.md and matching metrics;
  artifacts/REVIEW_HISTORY_CANDIDATE.md documents projection semantics/limits.
- P3 correction: evidence/notes/P3_REINTRODUCTION_20261017.md; all current guards
  retained, old exact refs/receipts denied after new version publishes.
- Git: planning commit allowed by active goal; no push/merge/deploy.
