# Evidence index

- `../HANDOFF_FOR_NEW_SESSION.md`: cross-machine continuation instructions, branch/base and fetch command, deliverable paths, Drive location, corrected icon serialization, verification, and remaining visual QA.
- `raw/PRE_PUBLISH_CHECKS_20261023.txt`: security, architecture, staged-diff, and repository harness results before publication.

- `../artifacts/Khoa_Sketch2Life_SRS_v3.1_Diagrams.drawio`: editable Draw.io source generated from canonical SRS v3.1. The three assigned pages are retained; `System Architecture v2` is the separately named comparison page.
- `notes/DIAGRAM_REVIEW.md`: source trace, structural validation counts, semantic review, and prior Drive/visual-QA record.
- `notes/REVISION_4_VISUAL_REVIEW.md`: owner screenshot observation, local ERD style revision, and current Drive/render-QA state.
- `notes/ERD_NOTATION_REVIEW_20261021.md`: ERD correctness fixes, B7.1/B21.5 mapping, unresolved assumptions, and revision 5–6 verification/readbacks.
- `notes/SYSTEM_ARCHITECTURE_REVIEW_20261021.md`: B8/repository dependency-direction review and revision 7 port/adapters correction.
- `notes/SYSTEM_ARCHITECTURE_LAYOUT_REVIEW_20261021.md`: revision 8 layout rationale, geometry/connector validation, Drive byte readback, and preview limitations.
- `notes/MERMAID_SOURCE_REVIEW_20261022.md`: scope approval, SRS mapping, ERD/package/architecture source review, static comparison counts, and Mermaid-render limitation.
- `../src/diagrams/`: Mermaid source counterparts for the three assigned pages; source files remain local on FEAT-048 and have not been pushed.
- `raw/MERMAID_STATIC_CHECK.txt` and `metrics/MERMAID_SOURCE_COUNTS.json`: one-off source comparison results and diagram counts.
- `raw/HARNESS_CHECK_20261022.txt`: feature-local harness path check; remaining global errors are in FEAT-045–047.
- `screenshots/README.md`: Mermaid rendered-image QA is pending because no renderer is installed in the worktree.
- `rendered/system_architecture_revision8_preview.png`: geometry/style preview used to inspect spacing after revision 8; not a diagrams.net export.
- `rendered/system_architecture_icon_preview.png` and `.svg`: local icon-style demo requested by Khoa on 2026-10-22; the SVG source is editable, the PNG is the visual preview, and neither changes the Draw.io or Mermaid diagram. Review: `notes/SYSTEM_ARCHITECTURE_ICON_PREVIEW_20261022.md`.
- `rendered/lucide_icon_catalog_preview.png` and `.svg`: standalone catalog of 16 individually labeled Lucide icons mapped to System Architecture roles, requested for preview before applying any icon. Review: `notes/LUCIDE_ICON_CATALOG_PREVIEW_20261022.md`.
- `rendered/system_architecture_aws_style_srs_preview.png` and `.svg`: separate AWS-inspired, vendor-neutral architecture concept preview requested by Khoa; SRS mapping and render QA are in `notes/SYSTEM_ARCHITECTURE_AWS_STYLE_PREVIEW_20261022.md`. It does not modify the Draw.io, Mermaid, SRS, or Drive artifacts.
- `../src/diagrams/system-architecture-v2.mmd` and `../ARCHITECTURE_DRAWING_RULES.md`: Mermaid counterpart and explicit symbol, icon, status, connector, boundary, and layout rules for the additive Draw.io v2 page. Implementation history: `notes/SYSTEM_ARCHITECTURE_V2_20261022.md`; icon implementation and readback: `notes/SYSTEM_ARCHITECTURE_V2_ICONS_20261023.md`.
- `../assets/icons/lucide-v1.61.0/`: pinned, local SVG icon sources and `NOTICE.md`, `LICENSES.txt`, and `manifest.json`; the Draw.io page embeds these icons for offline use. Icon application evidence: `notes/SYSTEM_ARCHITECTURE_V2_ICONS_20261023.md`.
- `notes/SYSTEM_ARCHITECTURE_V2_ICON_RENDER_FIX_20261023.md`: root cause and repair for broken icon placeholders; records the Draw.io style delimiter issue, percent-encoded data URI fix, structural validation, and Drive readback. Raw readback summary: `raw/DRIVE_READBACK_SYSTEM_ARCHITECTURE_V2_ICON_RENDER_FIX_20261023.txt`.
- `raw/drive_current_before_architecture_v2.drawio`: latest owner-saved Drive baseline read before appending v2; original page fingerprints were preserved from this baseline.
- Source: `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md`, especially B3, B7, B8, B19, B21, and B22; source-register ID `collaborative-srs-v3-20261010`.
- Drive folder supplied by the user: ID `18K0jfiBfl1nfG3-9HvfQXzVMoQcjTZF0`; file ID `1j-_R792jh-I1nC5B7FHwGDm3-yixPB6x` was updated in place with the four-page artifact and 20 embedded icons on v2. Final metadata/raw readback on 2026-10-23 verified the same ID and parent, 130,669 bytes, four pages, and 20 v2 image cells; see `raw/DRIVE_READBACK_SYSTEM_ARCHITECTURE_V2_ICONS_20261023.txt`.
- Latest icon repair readback: same Drive file ID and folder, 134,056 bytes, modified `2026-10-22T17:14:24.595Z`; four pages and 20 decoded, valid SVG data URIs on v2. See `raw/DRIVE_READBACK_SYSTEM_ARCHITECTURE_V2_ICON_RENDER_FIX_20261023.txt`.
