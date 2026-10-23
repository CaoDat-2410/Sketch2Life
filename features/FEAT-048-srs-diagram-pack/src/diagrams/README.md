# FEAT-048 diagram sources

## Current GitHub source selection

Publish the editable source and the two Mermaid files requested for the current ERD and System Architecture v2:

- `../../artifacts/Khoa_Sketch2Life_SRS_v3.1_Diagrams.drawio` — editable four-tab Draw.io artifact, with the architecture logos embedded in the file.
- `logical-erd.mmd` — repaired logical ERD source.
- `system-architecture-v2.mmd` — Mermaid counterpart of the current v2 architecture page.

The `.mmd` files render without external image assets. The `.drawio` file embeds its logo marks. Generated PNG/SVG previews, standalone logo SVGs, renderer/build helpers, initial-generation scripts, temporary inputs, and raw Drive baseline/readback copies are not part of this source selection. The combined Markdown wrapper duplicates these `.mmd` sources and is kept as a local convenience copy, outside the GitHub source selection.

Publish the text-only `manifest.json` and `NOTICE.md` files alongside the editable artifact as provenance for the embedded AWS and technology marks; the original standalone SVG files remain excluded.

## Other local diagram sources

- `system-overview.mmd` — overall components, external boundaries, and principal request/data flows grounded in SRS B8.
- `package-diagram.mmd` — package namespaces and dependency direction; runtime protocol links are labeled separately.

These two sources remain unchanged and outside the latest two-diagram GitHub selection. State-machine and activity/flowchart diagrams remain outside Khoa's assigned scope. The architecture drawing rules are documented in `../ARCHITECTURE_DRAWING_RULES.md`.

## Model boundaries

The ERD remains a logical proposal, not a physical schema. Enrollment cardinality is TBD; `membershipId` is a proposed GroupMembership episode key; each CanvasDocument has one owner mode (shared group XOR personal participant), with per-owner document counts still proposed. Historical operation attribution may be absent, but new child-authored operations require a selected, verified bound participant. TeacherReview's SketchProposal link is the sketch-review subset; DATA-24 includes other target kinds.
