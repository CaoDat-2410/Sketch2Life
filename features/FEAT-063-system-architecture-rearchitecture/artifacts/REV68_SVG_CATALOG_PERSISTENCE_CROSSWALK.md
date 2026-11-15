# FEAT-063 Rev68 — SVG catalog persistence crosswalk

**Purpose:** Same-checkout source/DTR crosswalk for the approved Rev83.4 M1/M2 scope. This is not a replacement DTR and does not sign off the physical ERD.<br>
**Requirements source:** FEAT-063 SRS v2.7-draft Rev68 (unsigned).<br>
**Plan:** `../plan/PLAN_REV83_4_M1_M2_APPROVED_IMPLEMENTATION_20261113.md`.

## 1. Existing source owners inspected

| Existing owner | Existing capability | M1/M2 fit |
|---|---|---|
| `public.core_asset_metadata` / `CoreAssetMetadataModel` | `(asset_ref, asset_version)` primary key, organization/typed owner fields, content hash, media type, source references and derived ref. The owner-scope check currently permits Parent or Organization only. | Reuse for source/canonical asset metadata and object-storage ownership. Add the `PLATFORM` scope only for platform catalog assets; do not add duplicated hash/media fields to Lesson. |
| `public.core_asset_lineage` | Existing Core source-to-derived references. | Reuse for source SVG → canonical sanitized SVG lineage where both asset versions are present. |
| `lesson.library_versions` | Immutable version number, JSONB content, structured content hash, review state and source document reference. Existing service inserts a new version and updates the lesson's current-version pointer under a revision check. | Store the lesson's pinned `presentation` snapshot, including its selected guide and source hash; every successful lesson save creates a new version. This is sufficient for lesson copy-on-write, but it is not a standalone reusable catalog-guide draft/review lifecycle. |
| `lesson.version_activities` | Activity rows are version-owned and ordered. | Leave unchanged; guide editor must preserve activity list and exact lesson-version pin behavior. |
| FEAT-063 Data Table Register v2.7-draft/Rev57 and nested older copies | Proposed `lesson.sketch_deck_revisions`/`lesson.sketch_deck_steps` describe an older 3–5-step deck target and do not include the approved 4–8 guide/editor fields or a source-review/catalog owner. The DTR itself is not aligned to the current Rev68 SRS. | Historical/target input only; do not repurpose these unimplemented mappings as an existing physical schema or claim the DTR is fully aligned. |

## 2. Demonstrated gaps and minimal additive change

1. Core asset owner scope has no `PLATFORM` representation; a platform-owned catalog item cannot be represented without a false school owner. The Core metadata check constraint must allow `PLATFORM` with no organization owner, while preserving existing `ORGANIZATION` and `PARENT_ACCOUNT` invariants.
2. Existing Core metadata cannot represent item-level source/license evidence, canonicalization version, structural readiness facts, reusable guide revisions independent of a lesson, or exact educator and curator decisions. `lesson.library_versions` can preserve a guide once it is attached to a lesson, but the Parent catalog and independent guide review need reusable source-bound guides before or apart from a lesson occurrence. Add `core_svg_catalog_assets`, `core_svg_catalog_guide_revisions`, and append-only `core_svg_catalog_reviews` in `public`, keyed to the existing Core Asset identity. The catalog revision is the reusable reviewed artifact; a lesson version stores an intentional immutable snapshot for that lesson. They have different owners and lifecycles, not competing current-version pointers. Neither table stores SVG source bytes.
3. Original source SVG and canonical sanitized vector bytes use the existing private S3-compatible object-storage port, keyed by Core `asset_ref/version`. Record the original and canonical hashes and a Core lineage edge. On failed metadata commit, delete only the object written by that request.
4. A lesson's immutable `library_versions.content_json` holds the versioned `presentation` snapshot and canonical guide metadata, and `structured_content_hash` binds the whole JSON contract. Writes use the existing optimistic lesson revision and create a new version; published versions remain immutable. This does not replace the catalog guide-revision record described below: that record is reusable and reviewed by source/guide hash without requiring a lesson to exist.

## 3. Proposed additive catalog tables

These are implementation mapping details for the approved migration, not a claim that the migration has run. The guide-revision table versions reusable catalog guides. A lesson version may carry a copy of the same guide as part of its own immutable presentation snapshot.

### `public.core_svg_catalog_assets`

- PK: `(asset_ref, asset_version)`; FK to `core_asset_metadata(asset_ref, asset_version)`.
- Fields: source identity `(asset_ref, asset_version)`, `catalog_entry_id`, `visibility_scope` (`PLATFORM`/`ORGANIZATION`), nullable `organization_id`, `topic_key`, Vietnamese title/alt text, `canonical_asset_ref/version`, declared source URI, license identifier/URI, source and canonical SHA-256, sanitizer version, readiness class, bounded structural facts JSON, catalog state, creator principal and `created_at`. Review changes are recorded in the append-only review table rather than an `updated_at` field.
- Checks: platform scope has null `organization_id`; organization scope has a nonempty organization ID; only bounded JSON facts and enumerated lifecycle/readiness values are accepted; asset versions and SHA formats are positive/valid.
- Never store a child profile, drawing, photo, raw audio, or Firebase identity in the catalog record.

### `public.core_svg_catalog_guide_revisions`

- PK: `guide_revision_id`; FK `(asset_ref, asset_version)` to `core_svg_catalog_assets`.
- Fields: `guide_ref`, monotonic `guide_revision`, exact `source_sha256`, `guide_sha256`, contract version (`SketchStrokeGuideV3`), bounded canonical guide JSON, author principal and `created_at`; unique `(guide_ref, guide_revision)`. Review state is derived from the append-only exact-hash review records.
- Each stage has 4–8 steps, existing stable path IDs only, cumulative visibility, semantic parts and explicit order/instructions. Geometry is read from the referenced canonical asset and is never copied into or edited through the guide.
- Parent lookup returns the latest source-bound guide revision only when the exact source hash has educator approval and Platform Admin curation approval, and the exact guide/source hash pair has educator approval. `grouping_allowed` is an additional permission for future automatic grouping; a manually authored, independently reviewed guide does not require it. Older revisions remain immutable and auditable.

### `public.core_svg_catalog_reviews`

- PK: `review_id`; FK `(asset_ref, asset_version)` to `core_svg_catalog_assets`; optional FK `guide_revision_id` to `core_svg_catalog_guide_revisions`.
- Fields: `review_subject_kind` (`SOURCE_ASSET`/`GUIDE`), `review_kind` (`EDUCATOR`/`CURATOR`), exact source and optional guide SHA-256, reviewer principal, decision, optional bounded reason, `grouping_allowed` (curator review only), and decision timestamp.
- Reviews are append-only. The active decision is computed for exact source/guide hashes; any changed hash invalidates prior approval. Educator approval and Platform Admin curation remain separate records. `grouping_allowed=true` is valid only for an approved curator decision.

## 4. Lesson JSONB contract mapping

`LessonContentInputV1.presentation` is an optional strict object with a contract version, ordered slides, media/asset references and zero or more `SketchStrokeGuideV3` values. The guide references one exact source asset version and source hash; it stores stable part/path IDs, labels, dependencies, new stroke IDs, animation order and Vietnamese instructions for 4–8 cumulative stages. Geometry remains owned by the canonical SVG asset. Unknown fields, duplicate IDs, invalid stage counts, missing/extra path assignments, dependency cycles, and attempts to modify geometry are rejected before persistence.

An editor save carries `If-Match`/expected lesson revision. The service copies the current validated content, applies the bounded guide/presentation operation, creates a new immutable lesson version/hash and advances the current version only when the revision matches. A stale revision returns `409` and changes no lesson state. No per-stage asset rows or per-lesson guide-revision table are created; standalone catalog guide revisions remain the reusable source-bound authoring/review records described in §3.

## 5. Migration boundary and open proof

- Migration is additive: extend the Core owner-scope constraint and create the three catalog, reusable-guide-revision and review tables with indexes/checks. It does not rewrite legacy asset rows or lesson versions. Downgrade must stop before changing schema if any catalog assets or Core `PLATFORM` asset rows remain; otherwise it would orphan the catalog/object lineage or restore an owner-scope check that rejects retained rows.
- Migration execution, backfill, rollout, rollback rehearsal and live schema validation are outside the current approval.
- Before shipping, the actual source path, all Alembic heads, generated OpenAPI contract, object-key adapter, access-control query and DTR cross-reference must be reviewed against the exact code SHA. The DTR physical ERD remains blocked until full same-baseline alignment and formal review.
- No SVG dataset item is active until its source/license/hash, educator review and required curator action are individually recorded. Existing repository fixture/generated/icon SVG files are excluded.
