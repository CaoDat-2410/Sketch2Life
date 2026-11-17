# FEAT-021 Validation — 2026-09-14

## Implementation checks

| Check | Command | Result |
|---|---|---|
| Compile | `backend\\.venv\\Scripts\\python.exe -m compileall -q backend\\src\\sketch2life` | PASS |
| Targeted semantic/catalog | `python -m pytest backend/tests/unit/test_semantic_personalization_v2.py backend/tests/unit/test_activity_semantics.py -q -p no:cacheprovider --basetemp=tmp/feat021-targeted-final2` | PASS, 15 tests |
| Full backend | `python -m pytest backend/tests -q -p no:cacheprovider --basetemp=tmp/feat021-full-final2` | PASS, exit code 0 |
| Ruff | FEAT-021 source/test files | PASS |
| Strict mypy | FEAT-021 source/test files | PASS, no issues in 6 files |
| Harness | `python tools/validate_harness.py` | PASS |
| Repository security | `python tools/validate_repository_security.py` | PASS |

## Behavior covered

- ASR child-interest concept wins over visual route ordering when narration is strong.
- A shared scene-understanding ID is used by all age bands.
- V2 exposes concept role, child-interest alignment, score breakdown and activity identity.
- Activity profile version is reconciled with the canonical activity template version.
- V1 legacy projection cannot diverge from V2 activity ID/version.
- V2 no longer silently selects an age baseline fallback; missing candidates are `UNAVAILABLE_AGE_BAND`.
- Coverage report measures concept × age candidate gaps without creating runtime activities.

## Catalog baseline disclosure

The committed catalog currently contains 100 reviewed profiles. The new coverage report measured:

```text
profiles=100
unmapped_profiles=48
concept_age_pairs=43
coverage_ratio=0.23255813953488372
gaps=33
```

This is a truthful baseline, not a claim that the catalog has reached the 200–250 target. The remaining catalog work is curated content authoring/review and must be completed as a content expansion milestone before production eligibility is claimed. Runtime AI is not allowed to synthesize those missing activities.

## Runtime acceptance limitation

Real ASR/VLM acceptance remains an opt-in Lightning Studio test because this workstation does not contain the Qwen3-VL and faster-whisper model runtime. The acceptance command is:

```bash
export SKETCH2LIFE_RUN_REAL_AI_E2E=1
python -m pytest backend/tests/e2e/test_lightning_backend_workflow.py -q -p no:cacheprovider --basetemp=tmp/lightning-e2e
```
