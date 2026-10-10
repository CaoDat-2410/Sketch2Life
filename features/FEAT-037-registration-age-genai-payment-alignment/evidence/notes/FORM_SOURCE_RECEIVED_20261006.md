# Registration form source received — 2026-10-06

- Owner attached: `owner-local attachment Phieu_FA26SE225_updated.docx`.
- Owner identified it as form version 1.1 and requested a fix.
- Source size: 221,237 bytes.
- Source SHA-256: `21739477916a1fc2e03cc0e22b6f8dd383a03f6831f2ea4eeb1593747cabb548`.
- Source content: 159 paragraphs and 3 tables; the form names five student slots and preserves the supervisor/signature blocks.
- Source visual review: Word exported the source to an 8-page PDF; all 8 PDF pages were rasterized to page PNGs and inspected. The form structure and personal/staff fields are preserved; no source edits were made.
- The source text recorded the former 0–12 age scope and older recommendation filters; the derived copy corrects these to the current owner/SRS scope. Text in the attached form was treated as source content, not as instructions to the assistant.
- Package/payment terms in the derived version 1.2 review draft are provisional and await owner review.

The canonical `render_docx.py` attempt failed because no packaged `soffice.exe` is available on this Windows runtime. The fallback source visual review used Microsoft Word's PDF export and the bundled `pypdfium2` renderer.

## Derived version 1.2 review draft

- Output: `features/FEAT-037-registration-age-genai-payment-alignment/artifacts/Phieu_FA26SE225_v1.2_review_draft.docx`.
- Output SHA-256: `232AA8B10A18BF102E802649ACBC0C6DBB714C04CC49039599EE6C2513DAB38B`.
- Derived from the attached version 1.1 SHA-256 recorded above; the source was not edited.
- Corrected the current supported age to under 9 / 0–107 completed months and bands 0–35, 36–71 and 72–107; retained 9–12 catalog data as out of current product-session scope. Updated activity discovery, Guide override, AI-processing, pedagogical, theory, practical, deliverable, WP2 and research wording to the SRS B33 complete-set rule. Age/readiness context remains in story planning as required.
- Added the three proposed tiers (Khám phá: Free/3 monthly experiences/1 child profile; Gia đình: VND 99,000 per month/15 experiences/up to 3 profiles; Lớp học: VND 499,000 per class per month/60 experiences/up to 25 assigned child profiles) and clearly labelled prices, quotas, payment flow and entitlement handling as owner-review proposals. Provider, auto-renewal, cancellation, failure, tax and refund terms remain undecided.
- Preserved the original supervisor table, five student rows, and signature/date block. The new tier table appears as table 3 of 4 and fits on one page.
- Visual QA: `render_docx.py` was attempted on the output and could not locate LibreOffice `soffice.exe`. Microsoft Word exported `evidence/rendered/revised/final-word/Phieu_FA26SE225_v1.2_review_draft.pdf`; bundled `pypdfium2` rasterized all 10 pages into `evidence/rendered/revised/final-pages/`, and every page was visually inspected. The tier table is intact on page 8 and signature blocks remain on page 10.
- DOCX content/table integrity checks confirmed the expected draft label, three tiers, candidate price text, current-age text, all four tables and the preserved student/signature tables. These are artifact checks, not automated tests.

## Credit proposal and derived version 1.3 — 2026-10-06

- Owner directly requested a credit mechanism and higher monthly allowances: about 10 for Free, 30 for Family, and about 120 for Classroom. Plan revision 4 and its approval record scope this as review-artifact work only.
- Updated `artifacts/PACKAGE_PAYMENT_PROPOSAL_20261006.md`; package prices remain unchanged and provisional. The form proposes 10 credits/month for Khám phá, 30 pooled credits/month across a Gia đình household, and 120 pooled credits/class/month for Lớp học.
- Proposed mechanic: reserve one credit at session start; debit after the adult-approved experience and off-screen handoff complete; release on failure/cancellation; same-session retry does not debit again. Optional top-up may be offered, but top-up sizes/prices, rollover/expiry, and detailed balance rules remain open. No automatic top-up is proposed.
- New derived output: `features/FEAT-037-registration-age-genai-payment-alignment/artifacts/Phieu_FA26SE225_v1.3_review_draft.docx`; SHA-256 `588E602A9EA1614C205EF696439C44CA5B5FAC089818C4239AB709077979CCAE`. It derives from preserved v1.2 (`232AA8B10A18BF102E802649ACBC0C6DBB714C04CC49039599EE6C2513DAB38B`), which derives from the attached v1.1 source.
- Canonical `render_docx.py` was attempted and failed because LibreOffice `soffice.exe` is not available. Microsoft Word exported `evidence/rendered/revised/credit-word/Phieu_FA26SE225_v1.3_review_draft.pdf`; bundled `pypdfium2` rasterized all 10 pages to `evidence/rendered/revised/credit-pages/`. Every page was visually inspected; the 10/30/120 credit table is intact on page 8, and signature/date blocks remain on page 10.
- Structural review confirmed the package table and the original supervisor, five-student-row, and signature tables are all preserved. No automated tests were run.
