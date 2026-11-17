# C5b reproducible selected component handoff — 2026-10-17

Parent 296a73f; feature/be2-12-content-publication. Approved goal requires safe
repeatable commands/evidence and clear component/runtime/integration boundaries.
This checkpoint supplies that pack, not another business task or final closure.

## Actual final run

Existing backend virtualenv -> src/run_component_checks.py from repository root:

- Exact selected inventory: **454 collected and 454 PASS / 0 skip, 4.59s**.
- 16 new runner classification/manifest checks included (438 prior cases retained).
- JUnit full classname/test identities match collection; unknown/duplicate/missing/
  skipped/failing cases cannot be reported PASS.
- Source hashes before/after match for 330 source/config/fixture/migration files.
- Ruff owned source/tests PASS using backend working directory/config.
- Strict Mypy 14 owned production files PASS.
- Architecture, harness, repository security and whitespace checks PASS.
- All child exits 0; outer exit 0; receipt scope SELECTED_COMPONENT_HANDOFF_ONLY.

Final raw ignored receipt:
.runtime/learning-content-component/20261017-074727-462756/
{collection.log,pytest.log,junit.xml,ruff.log,mypy.log,architecture.log,harness.log,
security.log,whitespace.log,summary.json}.

Final runner SHA256:
f9b0bb6d3c96620f6de36e9fcf671bbdefa4a3e2ef003af2b7cd0c02e2d7a8f4
Runner-test SHA256:
e4643f5ebdc93eaacf6350fe2c87662c5d13b79e7d6f0fc88ffde419622532ac

## Failed/earlier attempts preserved honestly

- 20261017-074504-735979: 453 tests PASS but Ruff FAIL. Runner incorrectly included
  foundation regression files in lint scope and ran with repo-root import context.
- 20261017-074602-868925: same 453 tests PASS, Ruff FAIL due incorrect project
  working directory/import grouping despite explicit backend config.
- Corrected runner to preserve 110 regression tests but lint only owned BE2-12
  files from backend cwd, exactly the focused scope used previously. Did NOT
  modify foundation source or weaken test inventory/source pinning. These were
  runner configuration failures, not adopted findings against another owner's code.
- 20261017-074647-962873: 453-case pack PASS. Added one extra-inventory negative
  test and corrected collection parser to retain unexpected tests for rejection;
  final source then passed the 454-case run above.

Original receipts were not overwritten/relabelled. Classification fixture XML
tests are not themselves runtime evidence; actual final subprocess run above is.

## Limits / no unnecessary service work

Selected pack is not the whole repo suite. It starts no service, installs nothing,
does not use GPU/provider/network and does not run SQL. Prior C4c PostgreSQL 24
PASS remains separately source-bound; no fresh SQL/adoption/delivery claim.
Default app mount, final semantic owner schemas/real authority/source/review/sink
and integrated session consistency still pending. Summary full_goal_complete=false
and real_owner_integration=NOT_RUN are intentional, not waived acceptance.

RECEIVER_CHECKPOINT.md is the concise current handoff entrypoint; older snapshots
remain historical. No push/merge/deploy or new-card implementation authorized.
