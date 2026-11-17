# C3c2 — exact request pin / held current-use policy lease

2026-10-17 Asia/Saigon, feature/be2-08-14 parent f66ec54. Approved P2/P3;
preimplementation plan/C3C2_USE_ELIGIBILITY.md. Executor self-review, not actual
owner integration or durable SQL/fence verification.

## Implemented

Strict backend request context (id/revision/input hash/purpose/feature/explicit
profile) and immutable policy pin (exact policy/version/hash, original activation
epoch/registry revision). No new public endpoint, CMD action or migration.
PolicyUseLeases.begin selects effective published pin for initial request;
continue_use retains original pin at dispatch/retry/completion/exposure, never
silently swaps to newer version. Context and pin are not bearer authorization.

Held owner use/review/registry guard -> feature SHARE -> record SHARE. Check current
scope/pin, published exact policy/body hash, two exact effective publication proofs,
current governance/registry/profile and authoritative exact request/phase use
decision. Native strict validation rejects malformed constructed instances (e.g.
allowed=1 or boolean revision). Owner echoes exact scoped canonical binding digest;
wrong digest/principal/org denied. No capability/role name implies AI usage.

Continuation checks immutable activation history matches original policy pin at
its origin epoch. Any intervening stop revokes that old pin even after reviewed
reactivation. Ordinary policy replacement can preserve old request provenance only
while exact old policy and all current use decisions remain valid. Wrong selected
profile denied, no auto provider selection. Callback exception releases guard with
safe error, not raw adapter/caller text. Lease snapshot outside context is metadata;
actual budget reservation and worker/provider authorization still separate.

No production use-authorizer, registry adapter, current session/consent/source/
terminal-state fence supplied. Port obligations state those checks explicitly;
assumed fixture is not cross-owner sign-off or real revocation proof. Consumer
must persist the original request pin and hold adopted guard through nested work/
commit. No foreign job/session writes or hidden callback atomicity claim.

## Actual local tests and checks

Existing backend venv, selected BE2-14 suites including new test_ai_policy_use.py:
336 PASS/0 fail/error/skip, 2.10s. 53 new cases; ignored receipt:
.runtime/be2-14-c3c2/component-junit.xml. Exact suite counts: 78 contract/46 domain/
26 persistence/11 runner/59 registry/29 command/3 activation/31 stop/53 use.
Memory UoW/assumed-use boundary only. No failed behavioral run for this checkpoint;
initial Ruff path typo/line length and Mypy TypeAdapter annotation fixed. Final
focused Ruff PASS; strict focused Mypy four source files PASS (transitive imported
typecheck excluded, not whole-repo proof).

Warnings retained: existing Alembic offline path_separator deprecation; Pydantic
unexpected bool serialization warning in deliberately malformed allowed=1 test.
That case is rejected, not coerced into permission. No validator weakened.

Root existing FEAT048 run_component_checks.py actual receipt:
.runtime/learning-content-component/20261017-160042-827552 summary/JUnit/logs:
477 selected regression cases PASS, 4.41s, source unchanged; all defined static
checks exit0. Together813 distinct local cases, not813 new tests or runtime proof.
Own integration test formatting changed afterward only; source pin rechecked
before commit for the regression pack's declared source scope.

Key SHA256:

- application/ai_policy_use.py:
  cc20da8afede4601d6aa1e330232463ad7e12e3b017d47a5551c311c5fb94d01
- infrastructure/ai_policy/activation_sql.py:
  27b5320cf28185e3cc5cb31eb4ee99305b413d93c3cce51428eb5e22cd7f41f9

## PostgreSQL still NOT_RUN

15 lifecycle +10 activation/stop/use cases prepared;10 activation cases collected
successfully (0.34s). Three new PG cases: prior pin survives ordinary replacement,
stop history/forged origin epoch deny resurrection, actual feature SHARE lease
blocks concurrent stop until exit. Lock assertion uses pg_stat_activity Lock wait
in autocommit observation, not merely sleep/future state. No actual run has proved
those SQL conditions yet. Runner source manifest includes new fixture dependency
test_ai_policy_use.py; inventory unit test expects10 activation nodes.

No AP environment provisioning approval received. No server/download/install/DB
or provider used. Old BE2-12 authorization/proof not reused. Runtime commands and
logs to return: artifacts/C2_SQL_RUNTIME.md.

## Remaining

C3c3 atomic budget/concurrency/reserve/consume/release/reconcile, provider-copy
verification/adapters, C5 public error translation and safe composition/projections,
consolidated acceptance and actual SQL all remain. Numeric limits/units/windows/
TTL/provider choices not invented. Real BE1/P4 wiring deferred to teammates.
No actual provider deletion/stop/cost/load, production-ready or full-card DONE
claim. No push/merge/deploy. Original reviewed plan and migrations unchanged.
