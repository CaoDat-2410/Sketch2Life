# Lucide icon catalog preview — 2026-10-22

## Scope

Khoa asked to inspect each proposed icon before it is placed in the System Architecture. This feature-local preview presents 16 individual icon tiles and maps each to a B8 component or actor role. It is a visual selection aid; it does not update Draw.io, Mermaid, or Drive.

## Preview files

- `../rendered/lucide_icon_catalog_preview.svg` — editable vector catalog with one named icon per tile.
- `../rendered/lucide_icon_catalog_preview.png` — 1648×1000 PNG rendered from the SVG for review.

## Icon mapping

| Lucide icon | Diagram role |
| --- | --- |
| `user-round` | Child, Teacher, Super Admin |
| `smartphone` | Android / React Native client |
| `monitor` | Teacher and Super Admin desktop surfaces |
| `server` | FastAPI / Python backend |
| `list-checks` | Application use cases |
| `layers` | Proposed B8 domain groupings |
| `plug` | Application-owned outbound ports |
| `database` | Relational database candidate |
| `hard-drive` | Object storage candidate |
| `list-ordered` | Async queue candidate |
| `cpu` | Separate worker process candidate |
| `shield-check` | Adult identity boundary; provider remains TBD |
| `sparkles` | Backend-only AI provider boundary; provider remains TBD |
| `radio-tower` | Proposed realtime/presence transport |
| `package` | Artifact boundary for snapshots and media |
| `workflow` | Async job processing path |

## Verification

- Parsed the SVG as XML and confirmed the PNG dimensions are 1648×1000.
- Rendered the sheet with headless Chrome and visually inspected all 16 tiles, labels, and margins.
- Each tile is a monochrome local SVG rendition following the named Lucide icon geometry. Confirmed technologies remain text labels; proposed/TBD providers keep generic symbols. These glyphs are for visual selection; the eventual diagram should embed SVGs from a pinned Lucide release.
- No Draw.io, Mermaid, canonical SRS, Drive, or GitHub artifact changed. No commit or push was made.

## Source and licensing

- Icon names and outline style reference [Lucide](https://lucide.dev/icons/).
- The current Lucide source license lists ISC for its icon set and separate MIT terms for Feather-derived icons; the list includes `database`, `monitor`, `server`, and `smartphone`. Review the [Lucide license](https://lucide.dev/license) and retain the applicable notices when embedding official assets.
- The preview is a review aid, not a bundled copy of a pinned icon package. Before applying icons to the production diagram, pin a Lucide release and use that release's SVG assets so the icon bytes and notices are traceable.

## Follow-up decision — 2026-10-23

Khoa asked why the discussed icons were missing from System Architecture v2 and directed that the previewed family be applied. The final mapping and release-pinned SVG sources are in `assets/icons/lucide-v1.61.0/`; application details are recorded in `SYSTEM_ARCHITECTURE_V2_ICONS_20261023.md`. Confirmed technologies remain text labels rather than brand marks.

## Limit

This sheet previews the component-icon family; it does not include Android, React Native, or FastAPI brand marks. Those technologies remain identified by their confirmed text labels.
