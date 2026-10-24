# Evidence index

## Revision 10 final package — 2026-10-24

- Plan and approval: `../plan/PLAN_REV10_CURRENT_STATE_DOSSIERS_AND_PUBLICATION_20261024.md`; direct authoring, N1–N9 delegation and commit/push authorization are in `../approvals/TASK_APPROVAL.md` and `../DECISIONS.md`.
- Current sources: owner-selected registration v1.2, SRS v3.3/B28, Review 2 guide, current FEAT-057/FEAT-060 evidence and five supplied Draw.io sources. Absolute workstation paths are represented by the neutral `[Downloads]/` source label.
- Final local outputs: `../artifacts/submission_r2_rev10/`. Four DOCX/PDF dossier pairs; page counts are BM01 4, Registration+BM03 9, consolidated Reports 1–5+Tracking 99, and BM02 5. Exact hashes, byte sizes, Draw.io page names and structural checks are in `metrics/final_package_qa_20261024_rev10.json`.
- All 117 PDF pages were rendered and visually inspected from the numbered PNG pages and twelve contact sheets under `render/rev10/final/`. DOCX ZIP integrity and python-docx parsing passed. BM01 uses A4 with 2 cm margins, has five decisions, three risks, six candidate NFRs, sections 0–8 on pages 1–3, and Appendix A on page 4.
- The report gallery contains 22 pages from the five supplied Draw.io files and 22 authorized editable imports: eighteen lifecycle state views covering all fifteen B19.4 registries plus four WF-01–WF-04 activities. The merged editable source is `../artifacts/diagrams/rev10/drawio/Sketch2Life-Review2-State-and-Activity.drawio`; page list and SHA-256 are in the Rev10 QA receipt. All are design models, not runtime evidence.
- Owner-delegated proposal: Keep N1–N4 and N7; Defer N5, N6, N8 (rewind disabled), and N9; omit none. All open owners, dates, environments, project/class values and thresholds remain TBD.
- Publication boundary: the repository security validator excludes every PDF; the full Registration+BM03 DOCX contains team phone/email details and remains local because the remote is public. Rendered pages, raw Draw.io conversion logs, and FEAT-043 REVIEW_PENDING imagery/archives remain local. Other safe current work is in the authorized publication set.
- Application tests were not run for this documentation/package task. Historical FEAT-060 test receipts are labelled as historical and the four skipped PostgreSQL cases, missing device acceptance, WF-03/WF-04 gates, unmeasured 40-child target and missing `review-2` tag are disclosed in the documents.

## Revision 6 final submission package

Revision 6 has been superseded by revision 7 after the owner reported horizontal overflow. Retain the section below for historical traceability; use revision 7 links/evidence listed next.

## Revision 7 current submission package

- Current editable sources and PDFs: `../artifacts/submission_r2_rev7/`.
- Source inputs and SHA256 values: `../SOURCE_REGISTER.md`.
- Output SHA256 values, page counts, baseline, structure and horizontal bounds audit: `metrics/final_package_qa_20261023_rev7.json`.
- Final Word renders, page PNGs and contact sheets: `render/final/rev7/`; all 66 pages were visually inspected.
- Revision 7 has four DOCX/PDF pairs: Registration+BM03 (9 pages), Reports 1–5+Tracking including PM Plan (50), BM02 (3), BM01+Appendix A (4). BM01 body sections 0–8 use pages 1–3 and Appendix A begins on page 4.
- Table widths in the consolidated report now use the same explicit fixed grid for header and data rows; requirement IDs are intact. The QA audit found no text, image, table rectangle or curve within 18 pt of a horizontal page edge; minimum clearances were 47.00 pt left and 29.88 pt right.
- Document QA used Word COM export, pypdfium2 page rendering, python-docx package checks and pdfplumber horizontal-bounds audit. Application tests were not run for this document-layout amendment.

## Revision 6 historical submission package

- Final editable sources and PDFs at that revision: `../artifacts/submission_r2_rev6/`.
- Source inputs and SHA256 values: `../SOURCE_REGISTER.md`.
- Output SHA256 values, page counts, baseline and structural checks: `metrics/final_package_qa_20261023_rev6.json`.
- Exact integration refs and branch audit: `notes/BRANCH_MERGE_RESULT_20261023.md`, `metrics/merged_branch_snapshot_20261023.json`.
- Final Word renders, page PNGs and contact sheets: `render/final/rev6/`; all 65 pages were visually inspected.
- Revision 6 has four DOCX/PDF pairs: Registration+BM03 (9 pages), Reports 1–5+Tracking including PM Plan (49), BM02 (3), BM01+Appendix A (4). BM01 body sections 0–8 use pages 1–3 and Appendix A begins on page 4.
- Document QA used Word COM export and pypdfium2 rendering. DOCX package ZIP integrity and python-docx parsing passed. Application tests were not run for this documentation task.
- BM02 preserves the official prompt and discloses that no `review-2` tag exists; it is an evidence-based draft and does not meet the tagged-baseline execution gate.

## Historical revisions

- Revision 5 Report 2 formatting receipt: `metrics/final_package_qa_20261023_rev5.json`.
- Revision 4/5 earlier dossier receipts and render paths remain historical evidence. Their deliverable page counts are superseded by the revision 6 four-dossier set.
- The 13 editable Mermaid sources and previous working documents remain under `../artifacts/` for provenance; they are not additional submission dossiers.

Original registration, course guide, BM01/BM02/BM03 templates and canonical SRS were preserved. Registration includes personal contact information only in the intended registration dossier. No external publication, tag, commit, push, provider call, deployment or reviewer approval is claimed.

## Revision 8 planning evidence

- Plan: `../plan/PLAN_REV8_DRAWIO_CURRENT_STATE_REFRESH_20261024.md` (SHA-256 `326FE8D683C335347935404A8AD74C253EABEDB4EFAF10EF28666CFFDD34DD5D`).
- Owner filter draft: `notes/OWNER_FILTER_CANDIDATES_20261024.md`.
- Sources and SHA-256 values: `../SOURCE_REGISTER.md`, revision 8 section.
- The owner confirmed four dossier categories with DOCX and PDF for each. No final revision 8 document has been authored; revision 7 remains the latest completed package.
- Final authoring awaits the owner's filter of next-work candidates and a decision to supply or document the missing state-machine/activity diagrams. No new diagram was created.

## Revision 9 active refresh evidence

- Plan: `../plan/PLAN_REV9_CURRENT_STATE_AND_DIAGRAMS_20261024.md` (SHA-256 `E9DB08673E88B54D8B63EE2267146D3296C73F0A79B659F4B3E7D66A9598A809`); authorization amendment is in `../approvals/TASK_APPROVAL.md`.
- The exact owner-selected registration path `[Downloads]/Phieu_FA26SE225_v1.2.docx` was checked on 2026-10-24; SHA-256 matches the previous `(1)` copy.
- Detailed owner filter inventory: `notes/OWNER_FILTER_CANDIDATES_20261024.md`. Final dossier authoring remains gated until the owner filters the candidate list.
- The owner authorized exactly two missing diagram types from Mermaid source converted/imported to Draw.io. Provenance, hashes, seven page names, Draw.io CLI version, and visual inspection record are in `metrics/rev9_diagram_provenance_20261024.json` and `notes/REV9_DIAGRAM_REVIEW_20261024.md`. CLI import outputs are preserved under `raw/mermaid-import/`.
- No revision 9 DOCX/PDF output has been authored. Revision 7 remains the latest completed package.
