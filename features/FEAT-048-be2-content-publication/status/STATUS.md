# FEAT-048 / BE2-12 status

- Status: IN_PROGRESS
- Plan revision: 1
- Implementation status: IN_PROGRESS — C1/C2 verified; C3a eligibility projection verified
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
- Application mutation service/HTTP/cross-owner integration: NOT_RUN, not yet wired.
- Planning checks: harness, architecture, security and static AC/action inventory
  PASS; these are not implementation acceptance tests.
- Approval: actual owner accepted revision 1/P1–P4 and continued implementation.
- Remaining: C3 mutation orchestration/receipts, C4/C5 and external integration gates.
- Next: C3b exact-review/publication/recall commands and guarded receipt replay.
- Evidence: evidence/notes/C2_LOCAL_POSTGRES_20261017.md; first runtime FAIL
  retained separately from final PASS and does not override it.
- C3a evidence: evidence/notes/C3A_ELIGIBILITY_20261017.md and matching metrics.
- Git: planning commit allowed by active goal; no push/merge/deploy.
