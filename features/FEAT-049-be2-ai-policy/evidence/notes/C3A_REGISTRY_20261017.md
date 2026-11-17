# C3a — exact server definition validation, component only

2026-10-17 Asia/Saigon, feature/be2-08-14 parent 8750c56. Revision-1 P2/P5
approval retained. Preimplementation matrix: plan/C3A_REGISTRY_VALIDATION.md.
Executor self-review, not real registry adoption or cross-owner sign-off.

## Implemented and limits

PolicyCompatibility.check holds injected current registry boundary, checks exact
principal/org author capability and strict body, then validates feature availability
and exact definition bindings for model profiles/moderation/retry/budget/concurrency.
Unknown/revoked/incompatible is unavailable; wrong scope/role/ref/snapshot mismatch
denies; changed registry epoch denies. Exceptions use safe codes, no adapter text.
No default registry, endpoint, token, profile/provider/numeric limit selected.
Monitoring scope is not author permission. Result immutable observation only,
not usage/activation grant. Every later mutation/usage must revalidate current
eligibility; mutation retains appropriate real guard through SQL commit.

Registry port requires implementation to resolve only currently adopted compatible
definitions and validate real approved ceilings/units/windows/safety/profiles.
This checkpoint supplies validator and port, NOT that production implementation
or durable owner fence. Tests use explicitly AssumedRegistry fixture. No duplicate
HTTP gateway, command action, new migration or foreign-owner source modifications.

## Failure addressed

First focused run: 1 FAIL/57 PASS. A malformed server binding built using
model_construct(version=True) survived JSON revalidation because serializer
encoded boolean as integer 1. Corrected validation to model_validate(native
model_dump, strict=True), preserving original types. Added malformed body ref
case too. Final 59 PASS, no validator weakened; initial failure not counted PASS.
One test line length corrected. This does not change existing C1 schemas or API.

## Actual checks

From backend, existing .venv/Scripts/python.exe:

```powershell
.venv/Scripts/python.exe -m pytest -o addopts= tests/contract/test_ai_policy_contracts.py tests/unit/test_ai_policy_domain.py tests/unit/test_ai_policy_persistence_shape.py tests/unit/test_ai_policy_sql_runner.py tests/unit/test_ai_policy_compatibility.py -q --tb=short
.venv/Scripts/python.exe -m ruff check src/sketch2life/application/ai_policy_compatibility.py src/sketch2life/application/ports/ai_policy_registry.py tests/unit/test_ai_policy_compatibility.py
.venv/Scripts/python.exe -m mypy --follow-imports=silent src/sketch2life/application/ai_policy_compatibility.py src/sketch2life/application/ports/ai_policy_registry.py
```

219 own cases PASS /0 fail/error/skip, 1.28s; ignored JUnit
.runtime/be2-14-c3a/component-junit.xml. Focused Ruff PASS and strict Mypy two
source files PASS (transitive imported typecheck excluded, not full repo proof).
Existing Alembic offline path_separator deprecation warnings retained.

Root FEAT048 component command: actual receipt
.runtime/learning-content-component/20261017-135028-250325/summary.json/JUnit/logs,
477 existing selected cases PASS, source unchanged, all defined static checks 0.
Together 696 local cases over two distinct inventories; not 696 new tests or SQL.

Source SHA256:

- application/ai_policy_compatibility.py:
  9a00b5b9c14c2530e74015fe3b4d140a83bb31f7a9958890a4e933e48c8a7a75
- application/ports/ai_policy_registry.py:
  6c1248c1c72de9ffed1ebc184838536cb51cc863021deb09b2e834807437922c
- tests/unit/test_ai_policy_compatibility.py:
  ed42a5a3f9885fda4a8c2c91aaf1f60063cac8a4efcd31054d7a03f10aee3b1a

## Still required

C2 15-case PG runtime pack NOT_RUN pending environment-specific authority; no
download/server/database started. C3 actual handlers/activation/atomic budget/
concurrency/kill/cancellation, C4 copy verification, C5 binding/projections and
C6 consolidated review/handoff remain. Real BE1/P4 wiring deferred to teammates,
not silently considered passed. No dependency install/GPU/provider/push/merge/deploy.
