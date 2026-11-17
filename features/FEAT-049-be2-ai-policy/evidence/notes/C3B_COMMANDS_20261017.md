# C3b — real application handlers / atomic effective scope, SQL pending

2026-10-17 Asia/Saigon, feature/be2-08-14, parent 2bc7ec2. Approved P1/P2/P5;
preimplementation plan/C3B_COMMAND_ACTIVATION.md. Executor self-review, no external
owner sign-off. Original reviewed plan and published migrations preserved.

## Implementation

AiPolicyCommands implements eight actions with native strict command revalidation,
current scoped capability/separation, exact version/hash/record/review CAS,
registry compatibility and current review-policy/proof decisions. Guard retained
outside entire UoW through commit. Newly proposed proofs also checked for current
effectiveness; no fabricated remote review persistence. Negative review/retire
can remediate withdrawn definitions. Record feature cannot silently move on edit.

Deterministic scoped IDs/fingerprint/receipt, recheck after scope lock, safe replay
of recorded metadata with current revision/state. Replays do not repeat publication
or scope changes; missing/revoked/currently disabled publication denied. Unique
conflict rolls back whole candidate, then one fresh receipt read, no blind write retry.

Forward ap_0002 adds separate own activation metadata: one org/feature scope pin,
epoch and immutable pending scope-transition intent. Publish atomic with lifecycle/
receipt/events/outbox; recall/archive disables only exact active pin, not replacement.
Scope UPDATE lock precedes record UPDATE. Initial discovery revalidated after locks.
Epoch0/null pin unusable even if disabled=false. No actual cancellation or worker/
provider stop acknowledgement follows from writing an intent. Late old scope intent
must not cancel newer pin blindly. Emergency pre-publication kill/atomic accounting
still C3c, not falsely called implemented here. C5 safe HTTP error translation and
default composition remain pending; positive typed existing dispatcher binding tested.

## Actual component checks

Existing backend venv, cwd backend:

```powershell
.venv/Scripts/python.exe -m pytest -o addopts= tests/contract/test_ai_policy_contracts.py tests/unit/test_ai_policy_domain.py tests/unit/test_ai_policy_persistence_shape.py tests/unit/test_ai_policy_sql_runner.py tests/unit/test_ai_policy_compatibility.py tests/unit/test_ai_policy_commands_service.py tests/unit/test_ai_policy_activation_shape.py -q --tb=short
.venv/Scripts/python.exe -m mypy --follow-imports=silent src/sketch2life/application/ai_policy_commands.py src/sketch2life/infrastructure/ai_policy src/sketch2life/application/ports/ai_policy.py src/sketch2life/application/ports/ai_policy_registry.py
```

Final .runtime/be2-14-c3b/component-junit.xml: 252 PASS/0 fail/error/skip, 1.38s.
78 contracts +46 domain +26 persistence +11 runner +59 registry +29 service
+3 activation shape. 33 new cases relative to C3a, not 252 newly implemented cases.
Assumed owner/registry/review boundary and transactional MEMORY UoW are labelled
fixtures, not durable rollback/race/authorization fence proof. Tests exercise all
eight actions/replay, self-publish, withdrawn definitions, scope replacement,
failure before receipt/commit, old-pin retirement and typed real handler binding.
One dispatcher-test fixture constructor failure corrected (ComponentStore requires
its own boundary); initial failure not counted PASS. Ruff import/format/redundant
cast findings corrected. No test/security validator weakened. Alembic offline
path_separator warnings retained. Focused Ruff PASS; strict Mypy eight source
files PASS (imported dependency checking excluded for that focused invocation).

Existing root FEAT048 selected regression command, final receipt:
.runtime/learning-content-component/20261017-140715-115460/summary.json/JUnit/logs.
477 PASS, no skip, source unchanged, all defined lint/type/architecture/harness/
security/diff checks 0. Earlier receipt before final port documentation superseded.
Together 729 local cases over distinct inventories, not SQL/real integration PASS.

Key SHA256:

- application/ai_policy_commands.py:
  8ecbe0cf4556898bf6ce1a0aa8c1da73c3d95c0dd3bf6f7eaa3952dbf3efb161
- infrastructure/ai_policy/activation_sql.py:
  f01643b53e497584f4e02244e8bff87242aeeadfd22a99ad8a472c60847bf07e
- alembic/versions/20261017_ap_0002_effective_scope.py:
  35dbaa33a4f41ec69a01e03d688af9b9238145ee0006d54ca67c115d0987cde7

## Actual PostgreSQL NOT_RUN

15 lifecycle cases remain pinned explicitly to ap_0001 (not changed old migration).
4 activation cases collected: actual command publish/disable/restart, receipt
failure atomic rollback, concurrent publications single effective pin, old recall
racing replacement must not disable new. New --activation runner inventory and
source pin includes fixture/transitive imports; exact JUnit matching, missing/
skip/duplicate/extra/failure never PASS. Separate environment-specific opt-in and
owner provisioning approval still absent. No server/download/DB/model/provider
started. Reproduce approved-profile commands via artifacts/C2_SQL_RUNTIME.md.

Do not describe migration triggers, row locks, recovery or actual guard revocation
as durable-verified until PostgreSQL/owner packs execute. BE1/P4 wiring remains
deferred to teammates. Real definitions, values, budgets/windows, providers,
copy deletion, cost/load and cancellation completion not proven. Full BE2-14 not DONE.
