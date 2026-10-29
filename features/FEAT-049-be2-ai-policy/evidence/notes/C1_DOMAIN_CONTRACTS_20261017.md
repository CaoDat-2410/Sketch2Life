# C1 — strict policy contracts / pure lifecycle component

2026-10-17 Asia/Saigon, feature/be2-08-14. Parent da38618 records actual owner
revision-1 P1–P5 approval; reviewed plan SHA256 unchanged. Executor self-review,
not independent owner/provider approval. Preimplementation matrix:
plan/C1_CONTRACT_MATRIX.md. No foundation/shared schema edits.

## Implemented

- Eight CMD-48 policy/ai actions with exact target/review and no surplus/null fields.
- Reference-only profile/moderation/retry/budget/concurrency body; four mandatory
  true safety gates, no numeric value/provider selection/secret settings dictionary.
- Own ai_policy review target and server-owned reviewer/proof/effectiveness, no
  fabricated learning_content DATA-24 target. Existing strict binding accepts the
  concrete command; positive/invalid-before-spy cases exercise all eight actions.
- Stdlib immutable domain with capabilities, author separation, version/hash,
  record/review revision, context invalidation, exact two-review publish set,
  reasoned terminal recall/archive and fresh-version reintroduction.
- Pure domain/storage-independent result is not a runtime effective policy pin,
  kill switch, registry validation, budget reservation or external review fence.

## Failure and correction

First focused run: 8 FAIL / 108 PASS; default serializer inserted unused None
fields, so command serialization failed strict presence validation on read-back.
Fixed wrap serialization to omit absence while retaining rejection of explicit
client null spare fields. Added invalid-before-bound-handler cases. Two initial
Ruff line-length findings corrected. No validators weakened, failure not PASS.

## Actual commands / receipts

From backend, existing .venv/Scripts/python.exe, no install:

```powershell
.venv/Scripts/python.exe -m pytest -o addopts= tests/contract/test_ai_policy_contracts.py tests/unit/test_ai_policy_domain.py -q --tb=short
.venv/Scripts/python.exe -m ruff check src/sketch2life/contracts/schemas/ai_policy.py src/sketch2life/domain/ai_policy tests/contract/test_ai_policy_contracts.py tests/unit/test_ai_policy_domain.py
.venv/Scripts/python.exe -m mypy --follow-imports=silent src/sketch2life/contracts/schemas/ai_policy.py src/sketch2life/domain/ai_policy
```

Final pytest: 124 PASS / 0 fail/error/skip, 0.65s; JUnit verified exact 78 contract
and 46 unit cases. Safe report relocated from unignored backend runtime to ignored
repo .runtime/be2-14-c1/c1-junit.xml; no report staged. Focused Ruff PASS; strict
Mypy three own source files PASS, imported dependency checking excluded for this
focused invocation (not a whole-repo typecheck).

From root, existing FEAT048 run_component_checks.py: 477 selected existing cases
PASS / 0 skip / 8.03s. Receipt .runtime/learning-content-component/20261017-124128-301971
summary/JUnit/logs; source unchanged, Ruff/Mypy/architecture/harness/security/diff
all exit 0 for its defined scope. Total across two distinct inventories 601 PASS,
not 601 newly implemented tests and not BE2-14 runtime proof. No SQL service run.

Source SHA256 (before documentation-only update):

| File | SHA256 |
|---|---|
| contracts/schemas/ai_policy.py | 8b5e5b08cc2ac786e779571ca5625f5e5bbb50f651593c57c17eac2cdf0cda63 |
| domain/ai_policy/model.py | f0870938375de0ce247a6058cfea583971f8f5c0c6cc20ef877b9ab1713552aa |
| tests/contract/test_ai_policy_contracts.py | 6c687beb255525f0f6ec02b0c6cfab8e980c93fa622768468e1d516693151ca7 |
| tests/unit/test_ai_policy_domain.py | 9b0625674b0302365a4fdffd8973e5a1076342e4191eeb693c6e39b2d70be3d2 |

## Remaining scope

C2 own SQL/migration, C3 registry/current eligibility/atomic limits/kill, C4 trusted
copy verification/registry adapters, C5 actual AI-policy handler+operations query,
C6 consolidated proof/handoff remain. Binding spy is not an implemented handler.
Actual profile/policy values unselected, real integration deferred to teammates,
provider deletion/cost/load NOT_RUN. No new packages, cloud/GPU/provider, push,
merge or deployment. Do not mark full BE2-14 DONE from this checkpoint.
