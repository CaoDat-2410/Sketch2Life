# Registration form v1.4 finalization — 2026-10-06

This records the earlier v1.4 iteration. The owner later requested the original form presentation; current user-facing version v1.5 and its preservation/render evidence are recorded in `FORM_V1_5_STYLE_CORRECTION_20261006.md`.

## Authorization and source lineage

- The owner approved the capstone-trial proposal and directed that internal review/draft/TBD commentary be removed from the registration form. Approval is recorded in `approvals/TASK_APPROVAL.md`.
- Controlling plan: revision 5, SHA-256 `D53C642A95067FC24F1926F656C61F2E472DA2E122FAC8003025BF676472E83E`.
- User-provided source: `owner-local attachment Phieu_FA26SE225_updated.docx`, version 1.1, SHA-256 `21739477916A1FC2E03CC0E22B6F8DD383A03F6831F2EA4EEB1593747CABB548`.
- Derivation source: preserved `artifacts/Phieu_FA26SE225_v1.3_review_draft.docx`, SHA-256 `588E602A9EA1614C205EF696439C44CA5B5FAC089818C4239AB709077979CCAE`.
- Final derived form: `artifacts/Phieu_FA26SE225_v1.4.docx`, SHA-256 `F2F64A9C07BBA22E7568B1A56955E0806782CA120157E0C059C5236CE47A7534`.
- Source v1.1 and prior derived v1.2/v1.3 files were preserved.

## Final content

The form states the supported age range as under 9 years (0–107 completed months) and includes the owner-approved capstone-trial packages:

| Package | Price | Monthly credits and scope |
|---|---:|---|
| Khám phá (Free) | 0 VND | 10 credits; one child profile |
| Gia đình | 99,000 VND/month | 30 pooled credits; up to 3 child profiles |
| Lớp học | 499,000 VND/class/month | 120 pooled credits; one Guide and up to 25 assigned child profiles |

It lists one-time top-ups of 10 credits/49,000 VND, 30/129,000 VND, and 60/239,000 VND. One credit covers the full adult-approved drawing/story experience through its normal off-screen handoff; the form describes reservation, successful completion, failed/cancelled release, same-session retry handling, manual paid-plan renewal, and backend payment confirmation.

The final form contains no internal review/draft/TBD labels or unresolved provider, refund, tax, or rollover notes. Original supervisor, five-student, and signature sections remain. Provider selection and live payment implementation are not claimed.

## Document review evidence

- The final DOCX has 170 paragraphs and 4 tables; the package content and retained registration sections were checked.
- A scan of extracted document text found none of the internal review/draft/TBD package wording that appeared in the earlier review versions.
- The canonical `render_docx.py` path could not run because `soffice.exe` (LibreOffice) is unavailable in this Windows environment.
- Microsoft Word exported the final DOCX to `evidence/rendered/final-v1.4-5/Phieu_FA26SE225_v1.4.pdf` (SHA-256 `04867E6AF27C0872CFF377128DCA081F2FBC1D2489ABC453D77E9DF845D59C80`). The bundled PDF renderer produced ten page images in `evidence/rendered/final-v1.4-5/pages/`; all ten pages were visually inspected for layout, tables, page breaks, and retained signature sections.
- Automated application tests were not run for this documentation update. No provider calls or live payment transactions were performed.

## Related requirements record

The current master SRS is v2.0 with B35 recording the same trial terms, credit lifecycle, backend payment confirmation, and implementation boundary. Its SHA-256 at finalization is `28EB8B890D8E950FEC6AA0DF87F9B29851A7E41AA871C3DD6EB4205CD807801E`.
