# Activity preparation classification evidence — 2026-09-23

## Scope

The active runtime view was classified without creating printable artwork:

- 100 MVP activities from `data/activity-catalog/mvp/activities.v1.json`;
- 200 curated variants from `data/activity-catalog/curated/v2/activity-families.v2.part*.json`;
- active catalog revision: `catalog-2026-09-expansion-1`;
- preparation contract revision: `ActivityPreparationCatalogV1@1.0`;
- classification rule revision: `1`.

## Result

| Classification | Count | Meaning |
| --- | ---: | --- |
| `PRINT_REQUIRED` | 96 | The authored child work depends on a fixed card, sequence, label, board or worksheet-like aid. |
| `PRINT_RECOMMENDED` | 152 | The activity can run with a household/real-object substitute, but a reviewed printable aid improves clarity or self-checking. |
| `NO_PRINTABLE_ASSET` | 52 | The cataloged physical materials and guide steps are sufficient without a prepared print pack. |
| **Total** | **300** | Exactly one profile per active `activity_id + version`. |

Representative classifications:

- `ACT-0102` — “Ghép con vật với nơi sống” — `PRINT_REQUIRED`, `MATCHING_CARD_SET` and `PICTURE_CARD_SET`.
- `ACT-0012` — “Ghép đồ vật với hình ảnh” — `PRINT_REQUIRED`, matching and picture cards.
- `ACT-0056` — “Phân loại động vật” — `PRINT_REQUIRED`, picture cards and a classification worksheet/board.
- `ACT-0009` — “Gọi tên người trong ảnh gia đình” — `PRINT_RECOMMENDED`, picture cards can improve repeatability but family-provided photos remain a valid path.
- Activities with only real objects, movement markers or household materials are classified as `NO_PRINTABLE_ASSET` when no authored printable aid is required.

## Runtime contract guarantees

- Profiles are loaded by `load_activity_preparation_catalog` and joined by `(activity_id, version)`.
- The loader rejects malformed profiles, duplicate references and missing coverage in the merged 300-activity view.
- `NO_PRINTABLE_ASSET` cannot contain planned kinds, asset references, or print defaults.
- A printable activity always contains a Vietnamese guide note, planned kind, `A4/PDF` defaults and `PLANNED` status in this slice.
- Asset references are rejected until a later reviewed `READY`/`APPROVED` asset-pack flow exists.
- Recommendation ordering and activity matching are unchanged; preparation metadata is additive.

## Verification

- `backend/tests/contract/test_activity_preparation_catalog.py`: contract invariants, coverage and negative cases.
- `backend/tests/unit/test_workflow_dependencies.py`: existing catalog composition regression.
- `backend/tests/contract/test_live_image_demo_api.py`: existing workflow/API regression.
- Manifest SHA-256: `d857ecc4f10a58b0402d99a504e324e3716d78845adbece87f230faab12d4758`.

No PDF, SVG or PNG was created or marked `READY`. The next approved follow-up can use the report
matrix to author the first high-impact printable packs, starting with the required matching and
classification sets.
