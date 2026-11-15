# EV-063-93 — SVG engine M1/M2 source implementation record

**Date:** 2026-11-13<br>
**Plan:** Rev83.4, approved for M1/M2 only<br>
**SRS:** FEAT-063 v2.7-draft Rev69, unsigned<br>
**Worktree baseline:** `codex/feat063-parent-docker-modal-seed-20261111` at `1f5bb0b5b1ab501a7120598a7e6e0de75217ddb3`<br>
**State:** Source edits present; all runtime and acceptance claims remain unverified.

## Scope implemented in source

### Backend M1

- Added a framework-independent `SketchStrokeGuideV3` validator with the approved 4–8 stage limit, exact source hash binding, existing path ID coverage, stage order, part references and dependency-cycle checks.
- Added SVG input allowlist parsing and canonical structured `SvgDocumentV1` serialization. Source strings are not injected into HTML or fetched remotely by the client.
- Added source/canonical hashes, provenance and license metadata, structural readiness facts, Core Asset lineage, and object-storage persistence through the existing storage port. The lineage record carries the sanitizer source-file SHA-256, distinct from its version label.
- Added authenticated SVG catalog routes and strict contracts for Parent approved-guide lookup, Teacher organization asset intake/listing, Platform Admin asset intake/curation, guide revisions, and educator source/guide reviews.
- Added `20261113_svg_catalog_review.py` for the Core platform-scope/catalog/review persistence gap. The migration defines database guards for immutable guide/review rows and refuses downgrade while catalog assets or `PLATFORM` Core Asset rows remain. The migration file exists but was **not run**.
- Kept reusable source-bound catalog guide revisions distinct from each lesson's immutable presentation snapshot. Lesson Library versions preserve a guide when pinned to a lesson; they do not provide a reusable source catalog/review record that can exist independently of a lesson. Platform curator approval gates catalog visibility; `grouping_allowed` is reserved for future automatic grouping and is not required for a manually authored guide.
- Mounted the router in the main API composition and added the routes to static OpenAPI metadata. Generated OpenAPI was **not checked**.

### Lesson Library and Parent M2

- Lesson presentation input accepts versioned drawing-guide slides with catalog asset version/hash and stable path references. Lesson writes validate the guide against the stored canonical source; Parent lesson detail resolves canonical SVG only after the existing lesson access path returns the lesson.
- Parent now requests real approved SVG catalog entries or uses the SVG guide already pinned in an accessible lesson. Its renderer reveals cumulative paths progressively in the guide's `animation_order`: previous paths are solid and paths introduced in the current step are dashed. Teacher preview/presentation uses the same ordering rule.
- Empty/unavailable catalog remains a skip/capture path. No fixture, canned guide, AI result, Modal call or fallback was added.

### Teacher Web M2

- Added the authenticated `/library/svg-guides` editor route and navigation entry.
- The editor loads actual organization lessons and SVG catalog assets, accepts provenance-bearing SVG uploads, assigns existing path IDs to semantic parts and 4–8 stages, edits Vietnamese instructions, and previews the same structured guide used by Parent.
- Guide revisions are persisted with exact source/guide hashes; educator review controls are independent of the author. Platform curation remains role-gated at the API and is not represented as a Teacher approval.
- Lesson autosave uses a 1.5-second debounce and `If-Match`. A stale lesson revision preserves the local browser draft and offers server reload, reapplication to the latest version, or a separate private draft. Local Undo/Redo changes only editor state, not source geometry. Save errors stop automatic retries and retain local recovery data.
- Added a large-screen SVG guide presentation view that uses the same renderer.

## API surfaces added

All routes are under `/api/svg-catalog/v1` and are source-only; they have not been called.

| Method and path | Purpose |
|---|---|
| `GET /parent/guides` | Return only eligible platform guides for Parent catalog lookup. |
| `GET /organizations/{organization_id}/assets` | List platform and same-organization SVG sources for Teacher authoring. |
| `POST /organizations/{organization_id}/assets` | Sanitize and persist a provenance-bearing school SVG source. |
| `POST /platform/assets` | Sanitize and persist a platform-owned SVG source. |
| `POST /organizations/{organization_id}/assets/{catalog_entry_id}/guide-revisions` | Create an immutable Teacher-scope guide revision. |
| `GET /organizations/{organization_id}/assets/{catalog_entry_id}/guide-revisions` | List visible guide revisions for independent educator review. |
| `POST /platform/assets/{catalog_entry_id}/guide-revisions` | Create a platform guide revision. |
| `POST /organizations/{organization_id}/assets/{catalog_entry_id}/source-reviews` | Record independent educator review of an exact organization source hash. |
| `POST /platform/assets/{catalog_entry_id}/source-reviews` | Record independent educator review of an exact platform source hash. |
| `POST /organizations/{organization_id}/assets/{catalog_entry_id}/guide-revisions/{guide_revision_id}/educator-reviews` | Record educator review of an exact organization guide/source hash pair. |
| `POST /platform/assets/{catalog_entry_id}/guide-revisions/{guide_revision_id}/educator-reviews` | Record educator review of an exact platform guide/source hash pair. |
| `POST /platform/assets/{catalog_entry_id}/curation` | Record separate Platform Admin curation and grouping authorization. |

## Verification and limits

- No test, typecheck, build, database connection, migration, API request, browser session, Android emulator session, Modal inference/deployment/warmup, renderer benchmark, or repository security validator was run for this implementation turn. This is **not** a pass result; the accepted plan and current task boundary explicitly leave those actions unverified.
- The migration, PostgreSQL constraints (including immutable-row guards and the downgrade guard for retained catalog/platform assets), object-store adapter, auth/org boundaries, request/response schemas, route composition, autosave race handling and `409` recovery have not been executed.
- The approved file manifest excludes `ParentApplicationModule.ts`, whose `learning` type does not yet expose `listSvgGuides`; the Parent controller currently narrows that existing runtime use-case method locally. Runtime wiring is source-plausible but unverified; removing this type-level seam requires a separate manifest amendment.
- No catalog item was imported, curated, or educator-approved. Parent has no approved catalog guide to display until a real source with provenance receives the required independent decisions. The real lesson path can display a guide only when an accessible lesson version contains one.
- Renderer targets (≥30 FPS, p95 first render ≤500 ms after decode, p95 transition ≤150 ms, ≤64 MiB growth) are **not measured**. M3-A/M3-B, AI flags, Modal, video, FLUX removal and complete Parent/Teacher E2E remain separately gated.
- The companion Data Table Register remains unsigned and older than Rev69. The Rev68 crosswalk is a task-local implementation mapping, not physical ERD sign-off.
- The checkout was already dirty before this implementation. Pre-existing files and unrelated changes were preserved; nothing was committed or pushed.

## Follow-up needed for acceptance

1. Review the source diff and resolve any static findings.
2. Run focused backend/frontend checks and generated OpenAPI review under a separate verification authorization.
3. Apply and inspect the additive migration in a disposable PostgreSQL database; verify upgrade/downgrade and object-store behavior.
4. Import a real licensed SVG only after provenance and independent-review workflow is ready; do not use a fixture to claim catalog success.
5. Exercise Teacher authoring/review and Parent lesson/catalog playback on the named browser and low-end Android emulator; measure the approved performance targets.
6. Align the full Data Table Register and physical ERD before treating the implementation mapping as a final physical model.
