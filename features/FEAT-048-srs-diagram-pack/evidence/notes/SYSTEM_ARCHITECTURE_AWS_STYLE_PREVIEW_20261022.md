# AWS-inspired System Architecture preview — 2026-10-22

## Scope

Khoa requested a visual demo based on the SRS after asking whether an AWS-style diagram fits the project. This is a separate local concept preview. It borrows the familiar system-boundary, colored service-tile, and labeled-flow conventions while keeping every icon and capability label vendor-neutral. It does not assert an AWS deployment.

## Preview files

- `../rendered/system_architecture_aws_style_srs_preview.svg` — editable SVG source.
- `../rendered/system_architecture_aws_style_srs_preview.png` — 1920×1260 rendered preview.

## SRS mapping

- Child Android app with React Native / TypeScript and the FastAPI / Python backend are marked `CONFIRMED`.
- Teacher Desktop and Super Admin are shown as confirmed product surfaces; their frameworks remain `TBD`.
- Application use cases and framework-independent domain rules are separated. The nine B8 context groupings are explicitly marked proposed.
- Outbound ports are separated from their proposed infrastructure adapters. A left-pointing dashed dependency arrow shows that adapters implement the application-facing port contracts.
- Relational database, object storage, async queue, identity provider, AI API, and realtime transport are shown as generic capabilities with candidate / `PROPOSED` / `TBD` labels.
- The async flow shows queue → separate worker → AI adapter/provider → result/status back to the job adapter; exact provider payloads remain TBD.

## Visual QA and limits

- SVG parsed as XML and rendered with headless Chrome at 1920×1260. Opened the PNG and checked legibility, flow direction, group spacing, status labels, and connector crossings.
- The diagram uses generic inline pictograms, not official AWS icons. It is not a deployment topology or a replacement for the current Draw.io or Mermaid diagram.
- No Draw.io, Mermaid, SRS, or Drive content was modified. No Git commit or push was made.
