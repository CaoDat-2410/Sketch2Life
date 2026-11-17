# FEAT-022 — Activity preparation and printable-asset classification plan

Status: `IMPLEMENTED — CLASSIFICATION VERIFIED; PRINTABLE PACKS DEFERRED`

Date: 2026-09-23  
Feature: `FEAT-022-catalog-coverage-expansion`  
Scope: classify catalog preparation needs first; do not create printable files or UI in this task.

## 1. Owner decisions recorded

- Activities that need prepared printable material must be explicitly marked in the catalog.
- The first delivery classifies every current activity as needing or not needing a printable asset.
- Printable files will be prepared later, starting with the highest-impact required activities and
  expanding incrementally.
- The canonical parent/guide print format is PDF on A4 paper.
- An editable source format may also be retained for future revisions, but it is not the primary
  parent/guide download.

## 2. Problem and current gap

The catalog currently exposes material IDs and material labels, but that is not enough to answer:

- whether the activity can be completed without a prepared file;
- whether a card, matching board, worksheet or sequence set must be printed;
- which printable pack will eventually be needed;
- whether the pack is planned, ready, blocked or not applicable;
- what the guide must do before starting the activity.

`material_option_ids` must remain the source for physical materials and safe substitutes. Printable
activity packs are a separate preparation concern and must not be inferred from a free-text material
label at runtime.

## 3. Scope for this task

### In scope

1. Define a versioned preparation-profile contract.
2. Classify all current selectable activity variants, including the 200 curated variants and the
   merged 300-activity runtime view, as:
   - `NO_PRINTABLE_ASSET` — no printed material is needed;
   - `PRINT_RECOMMENDED` — the activity works without printing, but a printed aid improves the
     intended presentation;
   - `PRINT_REQUIRED` — the activity is incomplete or cannot be run as authored without the
     printed asset.
3. Record why the classification was made in Vietnamese for guide-facing use.
4. Identify the expected printable pack kind without creating the file yet.
5. Add catalog validation and coverage reports for missing/contradictory classifications.
6. Preserve activity identity, age variant, material registry and recommendation matching behavior.

### Explicitly out of scope for this task

- creating PDFs, SVGs, PNGs or editable source artwork;
- generating visual assets with AI;
- parent/guide UI changes;
- download/print endpoints;
- storage, signed URLs, authentication or durable asset persistence;
- changing activity ranking or filtering solely because a printable file is not ready;
- changing the PixiJS, video or Lightning contracts.

Those items require a follow-up approved implementation plan after the classification report is
reviewed.

## 4. Proposed contract

Add a provider-neutral `ActivityPreparationProfileV1` projection per `activity_id + version`.
It is separate from the activity content record so the catalog can classify preparation without
duplicating materials, steps or safety data.

```json
{
  "contract_name": "ActivityPreparationProfileV1",
  "contract_version": "1.0",
  "activity_ref": {"id": "ACT-XXXX", "version": 1},
  "catalog_revision": "catalog-2026-09",
  "print_requirement": "PRINT_REQUIRED",
  "guide_note_vi": "Cần in bộ thẻ trước khi bắt đầu hoạt động.",
  "planned_asset_kinds": ["MATCHING_CARD_SET"],
  "asset_set_status": "PLANNED",
  "asset_set_refs": [],
  "print_defaults": {
    "paper_size": "A4",
    "preferred_format": "PDF",
    "editable_source_formats": ["SVG", "PNG"],
    "color_mode": "COLOR",
    "cut_required": true,
    "lamination": "OPTIONAL"
  },
  "provenance": {
    "source": "AUTHORED_CATALOG",
    "review_status": "PENDING_OWNER_REVIEW",
    "classification_version": "1"
  }
}
```

### 4.1 Enumerations

`print_requirement`:

- `NO_PRINTABLE_ASSET`
- `PRINT_RECOMMENDED`
- `PRINT_REQUIRED`

`planned_asset_kinds`:

- `MATCHING_CARD_SET`
- `SEQUENCE_CARD_SET`
- `PICTURE_CARD_SET`
- `SORTING_BOARD`
- `WORKSHEET`
- `LABEL_SET`
- `OBSERVATION_RECORD_SHEET`
- `REFERENCE_SHEET`
- `OTHER_REVIEWED_PRINTABLE`

`asset_set_status`:

- `NOT_APPLICABLE`
- `PLANNED`
- `READY`
- `BLOCKED`
- `DEPRECATED`

During this task, only `PLANNED` and `NOT_APPLICABLE` are expected. `READY` is reserved for the
follow-up task after the PDF has been authored, hashed and reviewed.

### 4.2 Classification rules

Mark `PRINT_REQUIRED` when the activity's authored child work depends on one or more of:

- a matching/sequence/classification card set;
- a board, grid or worksheet whose layout is part of the intended control of error;
- labels, symbol cards or answer cards that cannot be safely recreated from the guide text;
- a fixed visual reference pack required to keep the activity consistent across guides.

Mark `PRINT_RECOMMENDED` when the activity can be completed with household substitutes or real
objects, but the authored printed aid improves clarity, repeatability or self-checking.

Mark `NO_PRINTABLE_ASSET` when the activity can be performed with the cataloged physical materials
and guide steps without a printed aid.

The classifier must use authored materials, action, challenge, control-of-error/pedagogical
alignment and age variant—not only keywords such as “thẻ” or “giấy”.

## 5. Catalog placement

Use a separate versioned manifest initially:

`data/activity-catalog/curated/v2/activity-preparation-profiles.v1.json`

This avoids rewriting every activity-family part while preserving a stable join by
`activity_ref` and `catalog_revision`. The loader must reject:

- duplicate activity references;
- references to unknown activity IDs or versions;
- missing classification for a selectable activity;
- `NO_PRINTABLE_ASSET` records with planned asset kinds;
- `PRINT_REQUIRED` records without a guide note and at least one planned asset kind;
- `NOT_APPLICABLE` status combined with asset refs;
- an asset ref pointing to a file before the follow-up asset review gate.

The current recommendation matcher remains unchanged. Preparation status is metadata for the guide
and later UI; it is not an implicit eligibility filter in this classification task.

## 6. Example classification

For an activity such as “Ghép con vật với nơi sống”:

- `print_requirement`: `PRINT_REQUIRED`;
- `planned_asset_kinds`: `MATCHING_CARD_SET`;
- `asset_set_status`: `PLANNED`;
- `guide_note_vi`: “Cần in bộ thẻ con vật và nơi sống, sau đó cắt theo đường viền.”;
- `print_defaults`: A4, PDF, color, one set, cut required, lamination optional;
- `asset_set_refs`: empty until the printable pack is created and reviewed.

For an activity such as observing a real plant with a household substitute, the classification may
be `PRINT_RECOMMENDED` or `NO_PRINTABLE_ASSET` depending on whether the intended observation record
is essential to the authored activity.

## 7. Implementation tasks after approval

### Phase A — Read-only inventory and classification matrix

1. Load the current curated catalog and merged runtime view.
2. Export one row per selectable `activity_id + version`.
3. Record title, family, age band, action, challenge, materials, safety/supervision and authored
   control-of-error evidence used for classification.
4. Classify each row and record confidence/reviewer note.
5. Produce a report grouped by `PRINT_REQUIRED`, `PRINT_RECOMMENDED` and `NO_PRINTABLE_ASSET`.
6. Do not create or modify printable assets during this phase.

### Phase B — Contract and linting

1. Add Python schema and JSON schema for `ActivityPreparationProfileV1`.
2. Add a typed loader and join validation against the active catalog revision.
3. Add classification lint rules and negative fixtures.
4. Add a machine-readable report listing all activities that need a future asset pack.
5. Expose a provider-neutral metadata port for later guide/API consumption without adding a UI.

### Phase C — Integration-ready metadata

1. Add preparation summary fields to the backend activity metadata projection without changing
   recommendation ordering.
2. Preserve `asset_set_refs=[]` while files are not yet reviewed.
3. Add contract fixtures showing a required pack, optional pack, no pack and missing classification.
4. Record the exact catalog revision and preparation-profile revision in evidence.

## 8. Follow-up asset-pack task

After the classification report is approved, create a separate plan to:

1. author the first PDF A4 packs for the highest-priority `PRINT_REQUIRED` activities;
2. retain SVG/PNG editable sources where useful;
3. hash and version every file;
4. store printable assets under the owning catalog/feature asset lifecycle;
5. review print readability, cut lines, age suitability, safety and copyright/provenance;
6. publish only reviewed `READY` asset refs to the guide/API;
7. add a parent/guide download and print checklist.

## 9. Acceptance criteria

- [x] Every selectable activity in the active catalog has exactly one preparation profile.
- [x] Every profile points to the same activity ID/version and catalog revision.
- [x] Every `PRINT_REQUIRED` profile has a Vietnamese preparation note and at least one planned
  printable asset kind.
- [x] Every `NO_PRINTABLE_ASSET` profile has no planned printable asset kind or asset ref.
- [x] Every `PRINT_RECOMMENDED` profile explains why printing helps but is not mandatory.
- [x] The classification report can list all activities requiring future file preparation.
- [x] No PDF, SVG or PNG is created or exposed as `READY` in this task.
- [x] Existing activity matching, material filtering and activity identity remain unchanged.
- [x] Catalog lint, schema tests, regression tests and repository security validation pass.
- [x] Evidence includes the classification matrix, counts by class, unknown/missing records and
  representative examples.

## 12. Implementation record

Implemented on 2026-09-23:

- `ActivityPreparationCatalogV1` / `ActivityPreparationProfileV1` provider-neutral contracts;
- Pydantic loader with merged 300-activity coverage validation;
- deterministic classification generator and machine-readable matrix;
- additive recommendation metadata projection for guide/API consumers;
- negative contract fixtures and catalog regression tests.

Printable PDF/SVG/PNG authoring, review, `READY` publication, guide UI and download endpoints
remain intentionally deferred to the follow-up asset-pack task.

## 10. Evidence plan

Store evidence under:

`features/FEAT-022-catalog-coverage-expansion/evidence/`

Required evidence:

- `metrics/ACTIVITY_PREPARATION_CLASSIFICATION_*.json`;
- `notes/ACTIVITY_PREPARATION_CLASSIFICATION_*.md`;
- contract fixtures for required/recommended/none/missing cases;
- catalog lint output and catalog revision/hash;
- a review note identifying the first batch for printable asset creation.

No child data, provider credentials, external handbook originals or unreviewed frontend visuals may
be included.

## 11. Approval gate

Owner approval was given in the current conversation on 2026-09-23. The plan is now
`APPROVED — IMPLEMENTATION AUTHORIZED` for the classification/contract/metadata slice only.
Printable file creation, asset review, guide UI and download endpoints remain deferred.
