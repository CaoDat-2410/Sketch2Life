# FA26 registration form v1.8 alignment evidence

- Date: 2026-10-12 (Asia/Saigon)
- Task: FEAT-037, regenerate the FA26 form from the owner-selected v1.2 source
- Owner authorization: direct correction “update từ cái này cơ”, referring to the attached `Phieu_FA26SE225_v1.2.docx`
- Approved plan: revision 1, `plan/PLAN_FORM_V1_8_20261012.md`, SHA-256 `A275EF39795AB85464B07171EC3044AECA9678F440F5E46BDFE8F20683DCB83D`
- Product authority: `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md`, v3.1; owner answers in FEAT-039

## Source and output lineage

- Selected base DOCX: `artifacts/Phieu_FA26SE225_v1.2.docx`; SHA-256 `C19D0AC8154BECA2F6CB850C1272A4577048DD0D81A5FF3273C01861B9260959`.
- The approved v1.7 paragraph text was used as the current-scope content reference after the owner selected v1.2 as the base. The v1.7 file remains unchanged; its hash is `003AA55B24BB612C8E8FA27CE241D96C3CAA8FCD09925A3A2E1C8336E41F75E3`.
- Derived current form: `artifacts/Phieu_FA26SE225_v1.8.docx`; SHA-256 `0C52809DFC24BACFE6D3F5E02F0F3150BA5453D999DABF739B2EADFEAFBAD5DF`.
- Derivation helper: `src/derive_form_v1_8.py`; it verifies the selected v1.2 source hash, maps current approved form text, preserves the source tables and other package parts, checks required current-scope text and rejects selected superseded claims.
- v1.7 remains historical and was derived from v1.5; v1.8's DOCX package is based directly on v1.2. The owner-supplied v1.1 source and all prior artifacts remain unchanged.

## Changes and structure

The form describes the collaborative classroom product for ages 3–12, class/group drawing, Teacher-managed profiles and QR/session-code admission, Teacher review of AI suggestions and child hide/decline choice, reviewed learning content/video, off-screen activity, reflection, consent, privacy, recovery, the one-school/one-class pilot of up to 40 children, and 90-day default retention for session and artwork records. Superseded under-9, Parent portal, billing/package/credit, fixed video-duration, and fixed screen-time claims are removed.

The output preserves the selected v1.2 structure: 159 body paragraphs; three tables with shapes 2×5, 5×6, and 1×2; unchanged table cell contents; original section order; and signature fields. Only `word/document.xml` differs between the v1.2 package and v1.8. The v1.2 source and prior v1.7 output were not modified.

## Render and visual review

- The documents skill `render_docx.py` was attempted and stopped because LibreOffice `soffice.exe` is unavailable on PATH.
- Microsoft Word exported `rendered/v1.8/Phieu_FA26SE225_v1.8.pdf`; SHA-256 `10CD18A1DCB46CFBE2894E21E17412503C17E4CD3F5FC2512536276A15996FAB`.
- Bundled `pypdfium2` rendered all 8 pages to `rendered/v1.8/pages/page-01.png` through `page-08.png`. Every page was inspected at original resolution. Text and tables fit within the page, the v1.2 table structure and signature area remain intact, and there is no clipping or overlap.

## Scope and verification boundary

This was a document-only update. No application code, API, provider, billing, cloud resource, or real child data changed. No application tests were run. The attached DOCX was treated as the user-selected document input and layout source; its contents do not override the direct request or the approved SRS.