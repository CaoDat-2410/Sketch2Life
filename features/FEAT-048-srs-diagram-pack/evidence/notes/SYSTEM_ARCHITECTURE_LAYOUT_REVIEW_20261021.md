# System Architecture layout review — revision 8

## Source and approval

- Canonical authority: SRS v3.1, section B8, source-register ID `collaborative-srs-v3-20261010`.
- Owner: Khoa. Approved request: “chỉnh lại layout cho tôi đi dính lại hơi nhìu”.
- Scope: presentation/layout only on the System Architecture page. The canonical SRS, ERD and Package Diagram content, runtime, schema, technology choices, and Drive sharing were not changed.

## Layout changes

- Increased page whitespace and kept actors, clients, FastAPI, Application, Domain, and infrastructure in distinct bands/areas.
- Arranged the nine B8 proposed context groupings in a spaced 3×3 grid.
- Grouped Application use cases and outbound ports inside the Application layer; placed candidate infrastructure adapters in a separate right-hand lane below the ports.
- Added three distinct API entry anchors so the Child, Teacher, and Super Admin HTTPS connectors no longer share a bus-like route.
- Preserved the dependency direction: Application uses outbound ports; proposed adapters implement those ports. Realtime/presence and the AI provider remain proposed; AI credentials/endpoints remain backend-only.

## Verification and evidence

- Draw.io XML parses and still contains exactly three pages: ERD 168 cells, System Architecture 36 cells, Package Diagram 38 cells.
- Architecture has 24 vertices and 10 connectors. All connector endpoints resolve, all geometry stays within the 1800×1320 page, all nine context cards are present, three HTTPS entry anchors are distinct, and no accidental vertex overlaps were found.
- Layout preview: `../rendered/system_architecture_revision8_preview.png`. It is a local geometry/style preview for spacing inspection; it is not an export from diagrams.net.
- Drive file ID `1j-_R792jh-I1nC5B7FHwGDm3-yixPB6x` remains in folder `18K0jfiBfl1nfG3-9HvfQXzVMoQcjTZF0`. After revision 8, metadata readback verified 83,228 bytes and modified time `2026-10-21T15:12:51.660Z`.
- Drive raw readback SHA-256: `f23adb7830dfdf5c3a3dbba98c0f23fa4874d6baa08fd41f1d7f828b2acad214`. Local artifact SHA-256: `F23ADB7830DFDF5C3A3DBBA98C0F23FA4874D6BAA08FD41F1D7F828B2ACAD214`. The bytes match exactly.
- Actual diagrams.net rendering at normal zoom remains pending; no official diagrams.net visual QA is claimed.
