# System Architecture v2 icon rendering fix — 2026-10-23

## Report

Khoa's screenshot shows the icon cells in the Child, Teacher, and client cards as broken-image placeholders. The fault is in the Draw.io image style generated for the embedded SVGs, not in the dark/light theme or the Lucide asset files.

## Root cause

The builder wrote `shape=image;image=data:image/svg+xml;base64,<payload>;...`. Draw.io separates style entries with literal semicolons. As a result, it parsed `image=data:image/svg+xml` as the image source and treated `base64,<payload>` as a separate style token, so the browser attempted to load an invalid image URL. The official Draw.io file-format reference specifies that image data URIs in style values must omit `;base64` and shows a non-base64 data URI; see [Shapes and Stencils — Image shapes](https://github.com/jgraph/drawio/wiki/Shapes-and-Stencils#image-shapes).

## Correction

- Replaced base64 encoding with `urllib.parse.quote(svg, safe="")`, yielding a self-contained `data:image/svg+xml,<percent-encoded-payload>` URI with no literal semicolon or equals sign in the payload.
- Updated the builder's structural validation to parse the style token, require a local SVG data URI, URL-decode it, and parse the decoded XML as an SVG root element for every Lucide image cell.
- Documented the encoding rule in `ARCHITECTURE_DRAWING_RULES.md` and added AC-27 under plan revision 15. The correction is within the already approved icon scope; approval record revision 16 documents Khoa's screenshot and follow-up instruction.

## Local validation

- Ran `python features/FEAT-048-srs-diagram-pack/src/add_system_architecture_v2.py` successfully. The builder generated four pages: ERD (168 cells), System Architecture (36), Package Diagram (38), and System Architecture v2 (107). Original page fingerprints are unchanged.
- The builder's new per-icon check passed all 20 cells: each uses `data:image/svg+xml,`, each payload decodes to SVG XML, and no icon relies on a remote URL. All 24 v2 edges resolve.
- No diagrams.net editor or renderer is installed in this environment, so visual confirmation inside the application is not claimed.

## Drive update/readback

The same Drive file ID and folder were retained. A fresh metadata check before upload showed ID `1j-_R792jh-I1nC5B7FHwGDm3-yixPB6x`, parent folder `18K0jfiBfl1nfG3-9HvfQXzVMoQcjTZF0`, 130,669 bytes, modified `2026-10-22T17:05:18.037Z`.

After updating in place, Drive returned the same file ID and folder, size 134,056 bytes, modified `2026-10-22T17:14:24.595Z`. Raw readback confirmed all four page names and 107 `mxCell` elements on v2 (81 vertices, 24 edges, two roots). All 20 image cells use a non-base64 `data:image/svg+xml,` URI; each URL-decoded payload contains an SVG root/closing tag, with zero malformed or base64 URIs. The three original page fingerprints were unchanged by the builder. Exact metadata and extracted checks are in `evidence/raw/DRIVE_READBACK_SYSTEM_ARCHITECTURE_V2_ICON_RENDER_FIX_20261023.txt`.

This readback verifies the repaired encoding is present in the Drive file. Pixel-level inspection in diagrams.net remains unavailable in this execution; Khoa can refresh/reopen the same Drive file to confirm the icons render in the editor.
