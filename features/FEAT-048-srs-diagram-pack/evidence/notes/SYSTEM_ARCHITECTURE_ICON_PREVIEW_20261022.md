# System Architecture icon preview — 2026-10-22

## Scope

Khoa requested an image demo of the current System Architecture with SVG icons, then said the first image looked AI-generated. Visual revision 11 keeps the same SRS v3.1 content and `system-overview.mmd` structure while following conventional Draw.io diagram styling. It is a visual concept for review, not an update to the Draw.io page or Mermaid source.

## Preview files

- `../rendered/system_architecture_icon_preview.svg` — editable vector preview with inline SVG pictograms.
- `../rendered/system_architecture_icon_preview.png` — 1840×1210 PNG rendered from the revised SVG for visual review.

## SRS alignment

- Android / React Native / TypeScript and FastAPI / Python are marked `CONFIRMED`.
- Teacher Desktop and Super Admin remain product surfaces; their UI frameworks are `TBD`.
- The nine B8 context groupings remain proposed and framework-independent.
- Database, object storage, queue, identity provider, AI API, and realtime transport use generic symbols and retain `PROPOSED` / `TBD` labels.
- The API, application, domain, outbound ports, infrastructure adapter direction, client request flows, and asynchronous candidate flow remain visible.

## Visual review

- The SVG parsed as XML and rendered to PNG through headless Chrome.
- Opened the revised PNG at high detail and visually checked layout, labels, SVG icon visibility, and status distinctions; the B8 list no longer overlaps and the external-service area no longer occupies the unused top half of the canvas.
- The revised preview uses a plain white background, square component/system boundaries, no shadows, fewer icon marks, and solid versus dashed connectors for current versus proposed flows.
- Connector directions preserve both views: runtime calls travel from outbound ports to adapters; the dashed implementation dependency points from adapters back to the port contract.
- It uses a consistent set of neutral inline SVG pictograms, not vendor logos. It does not imply a new stack decision.
- The diagram content sources were not changed, and no Drive write or GitHub publication occurred.

## Limits

- This is not a Mermaid-rendered image and not an export from diagrams.net. Mermaid and official Draw.io rendered QA remain pending.
- Review against all SRS requirements and architecture constraints is recorded in `MERMAID_SOURCE_REVIEW_20261022.md` and `SYSTEM_ARCHITECTURE_REVIEW_20261021.md`.
