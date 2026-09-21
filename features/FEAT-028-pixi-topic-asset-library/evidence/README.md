# FEAT-028 evidence index

Status: implementation in progress; 24 generated atlas sheets (144 sprite frames) exist under assets/generated and await per-frame visual/rights review. No asset is approved/applied or runtime eligible. The backend selector is internal and makes no live provider call.

| Evidence ID | Criterion | Type | Artifact | Status |
|---|---|---|---|---|
| EV-028-PLAN-01 | Plan and task-approval gate | Plan/review | `../plan/PLAN.md`, `../approvals/TASK_APPROVAL.md` | Recorded 2026-09-17 |
| EV-028-PLAN-02 | Feature harness validation | Automated validation | `notes/PLAN_RECORD_VALIDATION_20260917.md` | FEAT-028 has no missing harness paths; repository check is blocked by pre-existing FEAT-026 paths |
| EV-028-ASSET-01 | Starter asset generation/provenance | ImageGen/catalog validation | `../assets/generated/GENERATION_MANIFEST.md`, `../assets/generated/asset-catalog.v1.json`, `notes/ASSET_GENERATION_VALIDATION_20260917.md` | 12 atlases / 72 frames; REVIEW_PENDING |
| EV-028-ASSET-02 | Revision-2 topic expansion and semantic descriptors | Catalog/hash/frame validation | `../assets/generated/asset-catalog.v2.json`, `../assets/generated/REV2_ASSET_ROWS.tsv`, `../assets/generated/GENERATION_MANIFEST.md`, `notes/ASSET_CATALOG_VALIDATION_20260917.md` | 24 atlases / 144 IDs; REVIEW_PENDING |
| EV-028-AI-01 | Approved-only AI shortlist and output allowlist | Unit tests/static checks | `../../../backend/src/sketch2life/application/services/pixi_topic_asset_candidates.py`, `../../../backend/src/sketch2life/infrastructure/ai/pixi_topic_asset_prompt.py`, `../../../backend/tests/unit/test_pixi_topic_asset_candidates.py`, `notes/AI_ASSET_SELECTOR_VALIDATION_20260917.md` | 16 targeted tests pass; Ruff and mypy pass; no provider call or FEAT-018 wiring |

Add reproducible evidence for each implementation criterion, including exact command/input, output path, environment, timestamp, reviewer, interpretation, and limitations. Use synthetic data only.
