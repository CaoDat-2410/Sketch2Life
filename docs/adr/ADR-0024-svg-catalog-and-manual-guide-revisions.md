# ADR-0024 — SVG catalog, review gates, and manual guide revisions

- **Status:** Accepted for M1/M2 implementation; AI and later milestones remain gated.
- **Date:** 2026-11-13
- **Decision owner:** Project owner, response “Approve these defaults and M1/M2 (Recommended)”.
- **Requirements source:** FEAT-063 v2.7-draft SRS Rev68; unsigned.
- **Plan:** FEAT-063 Plan Rev83.4.

## Context

Sketch2Life needs one deterministic SVG pipeline for Parent progressive drawing guides and Teacher guide authoring. Existing raster FLUX outputs do not provide stable path identities or cumulative stroke progression. The existing Core Asset metadata supports asset versions and hashes but lacks platform-owned catalog scope, license/source fields, readiness facts and separate review decisions. The Lesson Library already stores immutable version rows with a structured hash and a JSONB content body.

## Decisions

1. Use a backend-owned sanitizer, canonical vector contract and deterministic serializer. Web and Android render structured path data through native SVG elements; they do not inject arbitrary SVG markup or fetch remote resources.
2. Use 4–8 cumulative stages. A minimum of four independent drawable paths is a structural threshold only; a human educator reviews the exact source revision for teaching suitability.
3. Platform Admin curation is a distinct decision from educator review. A curator approval controls platform catalog visibility; `grouping_allowed` is a separate permission for future automatic grouping and is not required for a manually authored, independently reviewed guide. No AI/classifier can approve pedagogy or enable curator permissions.
4. Use immutable Lesson Library versions for the lesson's pinned presentation snapshot: its JSONB body and structured hash already provide copy-on-write lesson revisions. Keep the reusable, source-bound catalog guide lifecycle separate because Parent discovery and independent guide review must work without requiring a lesson to exist. `core_svg_catalog_guide_revisions` stores that reusable artifact; a lesson version stores its own immutable snapshot and is not the catalog's current-version pointer.
5. Add only the Core catalog/provenance/review persistence missing from the existing Core Asset contract, including the reusable catalog-guide revision lifecycle. Keep original and canonical object bytes in the existing private object-storage adapter; do not create a second byte store. The migration downgrade refuses to restore the old owner-scope constraint while any Core `PLATFORM` assets remain.
6. Keep topic-to-guide, path grouping and static SVG AI capabilities independent and OFF by default. M1/M2 makes no Modal calls and does not use FLUX as fallback.
7. Apply autosave after a 1.5-second debounce with expected revision. On `409`, keep the local edits intact and let the Teacher reload, resolve, or create a separate draft.
8. Treat the approved render limits as targets to measure later, not as already proven results.

## Consequences

- Catalog items without complete provenance or exact-revision review remain unavailable to Parent product reads.
- SVG assets may be visible to a Teacher authoring flow only within their organization and source permissions; public catalog availability requires the separate review sequence.
- The M1/M2 API and physical crosswalk are recorded in the feature folder. The companion DTR remains unsigned and not fully aligned to Rev68.
- No dataset item, generated illustration, Modal deployment, migration run, or workflow acceptance is implied by this ADR.
- M3-A/M3-B, AI activation, Parent/Teacher full E2E, video, and FLUX retirement require separate approval.
