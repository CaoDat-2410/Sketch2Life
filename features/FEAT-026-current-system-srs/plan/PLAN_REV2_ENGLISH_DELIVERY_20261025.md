# Plan Rev2 English SRS Delivery

- Date: 2026-10-25 (Asia/Saigon)
- Status: APPROVED BY DIRECT OWNER REQUEST
- Feature: FEAT-026-current-system-srs

## Objective

Create an English-only, consistently formatted derivative of the current-system SRS form for submission and review, preserving the existing Vietnamese source document unchanged.

## Authority and inputs

- The owner's direct instruction in the current chat requires the SRS file to contain no Vietnamese-language text or accented Vietnamese names, include the team in the introduction, and use consistent title/font/size/formatting.
- Input: `artifacts/Sketch2Life_SRS_Form.docx`; preserve it byte-for-byte.
- Use current SRS facts and current-system evidence already recorded in FEAT-026, FEAT-039 and FEAT-058. Use FEAT-058 decision D06 and registered project records for team names and responsibilities.
- The canonical FEAT-039/FEAT-029 SRS source is not replaced or rewritten by this derivative.

## Scope

1. Produce `artifacts/Sketch2Life_SRS_Form_English.docx` and a local PDF, plus feature-local page renders and QA evidence.
2. Translate all visible Vietnamese prose, headings, table labels, footers and cover text into English. Transliterate personal names to ASCII; remove any image or artwork that visibly contains Vietnamese text while retaining English institutional/project identification.
3. Add the four registered team members and their documented responsibilities to the Project Introduction; retain the supervisor with an ASCII name.
4. Use a centered English project title containing “AI for Children” on the cover. Standardize every editable text run on Arial 10 pt, including body, headings, tables, captions, header/footer and cover title. Use bold, color, alignment and spacing for hierarchy without varying font size.
5. Proofread the English text, correct definite typographical errors, preserve SRS meaning, requirement IDs, maturity distinctions, source references and all diagrams. Refresh page fields after export.

## Acceptance criteria

- AC1: The Vietnamese source DOCX remains byte-identical. The new English DOCX/PDF are separate derived artifacts with ASCII-only filenames.
- AC2: All extractable report text is English and contains no non-ASCII Latin letters. No image on the cover contains Vietnamese wording.
- AC3: The English Project Introduction identifies Do Cao Dat, Pham Tan Hieu, Vu Chi Bao and Ly Anh Khoa, their recorded responsibilities, and supervisor Lam Huu Khanh Phuong.
- AC4: The cover title is centered and includes the “AI for Children” phrase with intentional line breaks and alignment.
- AC5: All editable text uses Arial at a uniform 10 pt; headings and the centered cover title use weight/alignment/spacing for emphasis. Requirements, diagrams, maturity labels and review fields remain present and legible.
- AC6: A spelling review is recorded; definite errors are corrected and remaining dictionary flags are reviewed as technical terms, proper names, identifiers or accepted English variants.
- AC7: Every PDF page is rendered and visually inspected; no page is blank, clipped, overlapped or split in a way that obscures meaning. Hashes, page count, language/font/size checks and limitations are recorded in FEAT-026 evidence.

## Verification plan

- Compare source hash before/after and verify output filenames are ASCII-only.
- Audit DOCX/PDF text for Vietnamese diacritics, team entries, title text, requirement identifiers and content retention.
- Audit font families, size distribution, DOCX ZIP integrity and PDF page count.
- Proofread the English output and record candidate-word dispositions.
- Render all PDF pages to `evidence/screenshots/rev2_english/`, review page overviews and full-size changed pages, then document the results.

## Approval

The owner's direct instruction on 2026-10-25 to make the SRS English-only, use unaccented names, add the team to the introduction, align the “AI for Children” title, and review typography authorizes this local derivative and QA scope.

## Owner clarification — 2026-10-26

The owner clarified that editable text must use one font size with no large/small size variation. This plan is amended to require Arial 10 pt for every editable text run, including the cover title, headings, body, tables, captions, header and footer. Bold, color, alignment and spacing may establish hierarchy without changing text size. This clarification supersedes the earlier multiple-size hierarchy and authorizes rebuilding and rerendering the English derivative. The original Vietnamese source remains preserved.

## Owner clarification — 2026-10-26

Visual inspection of the latest 14-page export found that page 13 contains only the running header/footer while Appendix A starts on page 14. Remove the page-break artifact causing the footer-only page, rebuild the PDF, and update the QA page count, hashes, renders and evidence. The document remains an English-only derivative with the same content and uniform Arial 10 pt requirement.
