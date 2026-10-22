# System Architecture v2 icons — 2026-10-23

## Owner direction and scope

- Khoa pointed out that the discussed icons were absent from the new Draw.io page: “icon đã bàn đâu ?”. This follows the previous icon catalog review and approves applying those icons to the System Architecture v2 page.
- Task plan revision 14 and `approvals/TASK_APPROVAL.md` revision 15 record this scope.
- The original three Draw.io pages remain protected. Icons are added only to the separately named System Architecture v2 page.

## Icon source and mapping

- Source package: `lucide-static@1.61.0`, pinned in `assets/icons/lucide-v1.61.0/manifest.json`.
- The 16 upstream SVG files were fetched from fixed-version URLs. SHA-256 checksums are recorded in the manifest. The Draw.io builder embeds the SVG bytes locally and normalizes `currentColor` to one neutral stroke (`#42566B`); it adds no runtime dependency or CDN requirement.
- Role mapping is in `assets/icons/lucide-v1.61.0/NOTICE.md` and in comments at the top of `src/diagrams/system-architecture-v2.mmd`.
- Lucide source/version information and the applicable ISC/MIT notices are retained in `assets/icons/lucide-v1.61.0/LICENSES.txt`.

## Visual rules applied

- Keep the 16 previously reviewed icon types as simple outline cues on major nodes: actor cards, client surfaces, API, Application, Domain boundary, outbound ports, selected external services, artifact adapter, and the async job band.
- Do not add an icon to each of the nine small B8 context boxes or every adapter row; keep those text-only.
- Use the same dark-slate stroke for every icon. The icon never encodes CONFIRMED, CANDIDATE, PROPOSED, TBD, or policy status; component text and the status color/line remain authoritative.
- Preserve vendor-neutral generic icons for database, object store, queue, identity, AI, and realtime boundaries; no AWS/provider logo is used.

## Local structural check

- The updated builder reports four pages and 107 cells on System Architecture v2. The original ERD, System Architecture, and Package Diagram page fingerprints are unchanged.
- The page contains 24 routed connectors. Its built-in validation confirms every connector source and target exists.
- Draw.io embeds the icons as separate SVG image cells, while the surrounding nodes, boundaries, labels, and connectors remain editable native shapes.
- Mermaid remains a standalone flowchart. It records the same icon-name mapping in source comments without requiring an icon pack.
- Rendered-image inspection of the newly embedded SVG cells in diagrams.net remains pending; this execution has no diagrams.net renderer.

## Drive sync

The existing Drive artifact was updated in place after fresh metadata confirmed the file was unchanged since the previous write. Final raw and metadata readback evidence is recorded after upload in this section and in `evidence/raw/DRIVE_READBACK_SYSTEM_ARCHITECTURE_V2_ICONS_20261023.txt`.

- Readback date: 2026-10-23.
- Drive file ID: `1j-_R792jh-I1nC5B7FHwGDm3-yixPB6x`; parent folder: `18K0jfiBfl1nfG3-9HvfQXzVMoQcjTZF0`.
- Metadata size: 130,669 bytes; modified time: `2026-10-22T17:05:18.037Z`. The fetched raw payload also decodes to 130,669 bytes.
- Four pages are present: `ERD`, `System Architecture`, `Package Diagram`, and `System Architecture v2`.
- Raw v2 extraction: 107 `mxCell` elements (81 vertices, 24 edges, two roots), 20 SVG image cells, zero edges missing a source or target attribute. Original three page fingerprints were preserved by the builder before sync.
- Rendered screenshot/export remains pending; remote XML readback does not establish pixel-level appearance.

## Broken-image report and correction

Khoa's screenshot showed broken-image placeholders on the Child, Teacher, and client cards. The root cause was the image style written as `image=data:image/svg+xml;base64,...`: Draw.io uses semicolons to separate style tokens, so the literal `;base64` split the data URI and left an invalid image value. The updated builder writes a percent-encoded, non-base64 SVG data URI and verifies it by decoding every icon payload and parsing its root SVG element. The corresponding rule is now documented in `ARCHITECTURE_DRAWING_RULES.md`.

The owner authorized correcting the already-approved icon embedding. Plan revision 15 and approval record revision 16 cover this repair; see `evidence/notes/SYSTEM_ARCHITECTURE_V2_ICON_RENDER_FIX_20261023.md` for the source-level check and corrected Drive readback.
