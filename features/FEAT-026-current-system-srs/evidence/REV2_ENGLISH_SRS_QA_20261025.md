# English SRS Rev2 QA

Date: 2026-10-26 (Asia/Saigon)

## Changes

- Created a separate English-only derivative with an ASCII-only filename; the original Vietnamese source DOCX remains byte-identical.
- Added the four registered team members and responsibilities to the introduction, with ASCII-transliterated names. The supervisor is also listed using ASCII transliteration.
- Centered the two-line project title, including “AI for Children”.
- Standardized every editable text run to Arial 10 pt, including cover title, headings, body paragraphs, tables, captions, header and footer. Bold, color, alignment and spacing establish the hierarchy.
- Corrected the remaining “Session init” shorthand to “Session initialization”. Requirement identifiers, diagrams, maturity labels, source references and sign-off fields were retained.

## Verification

- The original source hash is 08f43d867cdb6a30c05440223b9f015a02f5c3f3c2adacd1ede9f29b28b151a6.
- DOCX SHA-256: cfaf85fa4923a0b26228ee95a2980c31beedae085c167567f82ce4c2c53df037. PDF SHA-256: 88ee851cd8b5688c3b10ee0ec3b64e913bdcdaa430dea17d204c938abc559dc0. The PDF contains 13 pages.
- DOCX ZIP integrity passed. Font/style audits found Arial only and a single 10 pt run size. OOXML proofing tags are en-US. Extracted DOCX/PDF text contains no Latin diacritics.
- The PDF has no page without extractable text, no visually blank pages, and no out-of-bounds text. An initial 14-page export had a footer-only page before Appendix A; the page break was removed, fields refreshed and the PDF regenerated. Appendix A and Appendix B now fit on page 13. All 13 pages were rendered and reviewed in contact sheets; the cover, introduction/team, repaired tables, route/state model, requirements, security, traceability, sign-off and appendix pages were additionally inspected at full size.
- The state-machine table's State column was widened so the full UNDERSTANDING_PROPOSED identifier remains on one line on page 7. The transition and control columns remain within the page width. The uniform Arial 10 pt revision fits in 13 pages, including the appendices, without a footer-only page.
- Word spelling review produced 57 flags across 38 unique terms. Every candidate was checked in context. They are API and contract identifiers, product/framework names, proper names, file-path terms or domain vocabulary; no ordinary English spelling error remains. Word COM reports LanguageID 9999999 (mixed), while the OOXML run audit reports en-US tags. Both observations are recorded in evidence/metrics/rev2_english_spelling_review.json.

## Evidence and authority boundary

The machine-readable receipts are evidence/metrics/rev2_english_qa.json and evidence/metrics/rev2_english_spelling_review.json. Rendered pages are in evidence/screenshots/rev2_english/. Source and output attribution is in SOURCE_REGISTER.md. This is a local documentation derivative only; it does not replace the canonical FEAT-039/FEAT-029 SRS or claim product implementation.
