# Review 2 four-dossier package context

## Current Rev12 checkpoint — 2026-10-24

- Status: Rev12 diagrams and four local DOCX/PDF dossier pairs have been regenerated, rendered and visually checked. Project-security publication checks and the separate CI/Iteration 1 release gate remain open; the `review-2` tag has not been created.
- Outputs: `artifacts/submission_r2_rev12/` has four dossier categories as DOCX/PDF pairs. Current PDF counts are Design Brief 6, Registration+BM03 10, Reports 1–5+Tracking 100, and Self-Review 6. Registration+BM03 and all PDFs remain local.
- Diagram package: 46 editable Draw.io pages combine 22 supplied-derived pages and 24 authored pages (20 state-machine, 4 activity). The five supplied originals are unchanged; 16 source-attribution cells were removed only from the derived master and rendered figure copies. Each report figure has a diagram-type caption and no source caption.
- Layout QA: all 24 authored canvases were individually reviewed at full size. Label-label, label-node, node-node, route-node, route-label, and route-crossing counts are zero. Session terminal, device grant-revocation, and Data Request cancellation/external-purge paths are separated into focused companion state machines without dropping transitions. Receipts: `evidence/diagram-qa-rev12.json`, `evidence/render/rev12/diagrams/layout-qa.json`, and `evidence/diagram-master-qa-rev12.json`.
- Report PDF: all 46 gallery figures are on pages 52–97, each with a diagram-type caption. The Appendix D TOC points to page 51 and Appendix E to page 98. Every PDF page is rendered; no blank pages or source captions were found.
- Near-term proposal remains Keep N1–N4 and N7; Defer N5, N6, N8 (rewind disabled), and N9; omit none from registered scope. Unknowns and proposed owners/dates are detailed in the report and await owner/team confirmation.
- Current Git baseline used in the dossier: `dev@d0a754a2` (source snapshot). CI/P4 gate remains failed, so no `review-2` tag or tag-specific BM02 run is claimed. Normal commit/push remains separately authorized after security validation.
- Output and source hashes are in `evidence/metrics/rev12-package-qa.json`, `evidence/diagram-master-qa-rev12.json`, and `SOURCE_REGISTER.md`.

## Historical Rev11 checkpoint — 2026-10-24

- Status: Rev11 DOCX/PDF pairs have been regenerated and page-rendered; diagram structure and image sanitization passed. FEAT-060 CI/Iteration 1, repository security, publication, and conditional tag gates are still in progress.
- Outputs: `artifacts/submission_r2_rev11/` has four dossier categories as DOCX/PDF pairs. Current PDF counts are Design Brief 6, Registration+BM03 10, Reports 1–5+Tracking 98, and Self-Review 6. Registration+BM03 and all PDFs remain local.
- Diagram package: 44 editable Draw.io pages combine 22 supplied pages and 22 authored pages (18 state-machine, 4 activity). The five supplied originals are unchanged; 16 source-attribution cells were removed only from the derived master and rendered figure copies. Each report figure has a diagram-type caption and no source caption.
- Layout QA: all 22 authored canvases reviewed at page size. Label-label, label-node, node-node, route-node and route-label collision counts are zero. Data Request has one explicitly bridged route crossing, encoded as a line jump in Draw.io; it is the only crossing and is not presented as a junction. Receipt: `evidence/diagram-qa-rev11.json`.
- Near-term proposal remains Keep N1–N4 and N7; Defer N5, N6, N8 (rewind disabled), and N9; omit none from registered scope. Unknowns and proposed owners/dates are detailed in the report and await owner/team confirmation.
- Current Git baseline used in the dossier: `dev@d0a754a2` (source snapshot). Package publication commit, CI run, and final clean baseline are not yet established. `review-2` has not been created.
- Output and source hashes are in `evidence/metrics/rev11-package-qa.json`, `evidence/diagram-master-qa-rev11.json`, and `SOURCE_REGISTER.md`.

## Current Rev10 package snapshot — 2026-10-24

- Status: four dossier categories authored as DOCX/PDF pairs and rendered; publication checks and Git publication are in progress.
- Authority: owner-selected registration v1.2, canonical SRS v3.3/B28, Review 2 guide, current FEAT-057/FEAT-060 evidence, and the five owner-supplied Draw.io files.
- Outputs: `artifacts/submission_r2_rev10/` contains the four local pairs. PDF pages: Design Brief 4, Registration+BM03 9, Reports 1–5+Project Tracking 99, BM02 Self-Review 5. BM01 sections 0–8 occupy pages 1–3; Appendix A fits on page 4.
- Diagram set: supplied Draw.io sources remain unchanged. The report reproduces their 22 pages and adds 22 editable Mermaid-to-Draw.io imports: eighteen focused state views covering all fifteen B19.4 lifecycle registries and four WF-01–WF-04 activity pages. Diagrams are target designs, not runtime evidence.
- Planning proposal: Keep N1–N4 and N7; Defer N5, N6, N8 (rewind disabled) and N9; omit none. Owners, dates, contract/runtime settings, workload and acceptance thresholds remain TBD.
- Review limits: WF-01/WF-02 have local paths and separate historical checks but no PostgreSQL-backed FE-to-BE or device acceptance. WF-03/WF-04 remain gated. The 40-child target is unmeasured, not a hard join cap. BM02 remains an untagged draft because `review-2` is absent.
- Publication boundary: PDFs remain local because the repository validator excludes `.pdf`. Registration DOCX files contain team phone/email details and remain local because the GitHub repository is publicly readable. Other safe current changes may be committed after the validator passes.
- Final QA receipts and local renders are indexed in `evidence/README.md` and `evidence/metrics/final_package_qa_20261024_rev10.json`.

## Historical revision 7 baseline

- Date: 2026-10-23
- Status: COMPLETE for approved documentation scope, plan revision 7.
- Authority: supplied registration v1.2 controls scope. The Review 2 guide and BM01/BM02/BM03 templates control dossier form. Canonical SRS v3.1 supplies broader requirements context; gaps against registration and actual code are identified in the report.
- Source baseline documented: local `dev@0a7ce768c153f2104cff930569c3eda6e484532c`, including refreshed Child UI source `origin/FE_UI_Child@ca3779869dfc1385cbbc7b8ca730f780386af7b2`. The checkout was dirty and was not treated as a clean/tagged release.
- Current output: four submission categories, each with DOCX and PDF in `artifacts/submission_r2_rev7/`: Registration+BM03 (9 pages), Reports 1–5+Project Tracking with integrated PM Plan (50 pages), BM02 Self-Review (3 pages), and BM01 Design Brief+Appendix A (4 pages).
- BM01 sections 0–8 fit in pages 1–3 at 11 pt with A4/2 cm margins; Appendix A begins on page 4. Report includes detailed system specification and design, 38 use cases, 66 FRs, diagrams, implementation-versus-target distinctions, test strategy, PM schedule and tracking.
- PM assumptions: feature-based Agile with weekly review/CI; 15 relative weeks; preliminary 252 person-days from WBS; calendar dates/capacity remain proposals pending confirmation. Modal is selected, deployment values TBD.
- Ownership supplied by user: Đạt full-stack, Bảo FE, Hiếu BE2, Khoa BE1. `FA26SE225` is inferred from the registration filename; class was blank in the supplied registration and is identified for confirmation.
- BM02 retains the official prompt and includes evidence-based proposed responses. The required `review-2` tag is missing; BM02 is clearly a draft against the dirty local source snapshot and does not meet the tagged-baseline run gate.
- Revision 7 layout correction: explicit table grid widths now match header and data-cell widths; wide report tables fit the printable area and all requirement IDs remain visible. Verification: final DOCX package integrity/parse checks passed; all 66 revision 7 PDF pages rendered and visually inspected. Horizontal text/drawing-object bounds have no violations at an 18 pt minimum page-edge clearance. BM01 form constraints and BM02 prompt/tag caveat are in `evidence/metrics/final_package_qa_20261023_rev7.json`.
- No app tests, new runtime code, live AI/provider calls, commit, push, tag, deployment, or claim of team/supervisor acceptance occurred in this documentation task. Runtime integration and cleanup files in the dirty workspace were left untouched.
- Source hashes and evidence locations are indexed in `SOURCE_REGISTER.md` and `evidence/README.md`. Revision 6 remains historical; revision 7 is the current output set.

## Revision 8 planning checkpoint — 2026-10-24

- The owner requested a refresh to the four Review 2 dossier categories using SRS v3.3/B28, current FEAT-060 status, the Review 2 PDF, and five supplied Draw.io files. Each dossier is to have a DOCX and PDF; the user clarified this as eight final files total.
- The four categories remain Registration+BM03, Reports 1–5+Project Tracking, BM02 Self-Review, and BM01 Design Brief. BM04 is completed after the Review 2 meeting and is not part of these four pre-review dossiers.
- Final authoring is waiting for the owner to filter candidate next-work items and provide or waive the missing state-machine/activity-diagram sources. No DOCX/PDF revision 8 file has been authored yet; revision 7 remains the latest completed package.
- Current source: `dev@0a7ce768c153f2104cff930569c3eda6e484532c` with a dirty working tree. FEAT-060 status dated 2026-10-24 reports local Child/Teacher/BE1 integration with separate checks, but no PostgreSQL-backed FE-to-BE acceptance run. WF-03/WF-04 remain gated.
- SRS v3.3/B28 is owner-approved requirements text. It does not establish that the corresponding API/schema/migration details or end-to-end behavior have been accepted or deployed.
- Source inventory, hashes, diagram pages and the source-form ambiguity are recorded in `SOURCE_REGISTER.md` and `evidence/notes/OWNER_FILTER_CANDIDATES_20261024.md`.

## Revision 9 active refresh — 2026-10-24

- The owner selected the exact registration path `[Downloads]/Phieu_FA26SE225_v1.2.docx`; its SHA-256 is identical to the previously registered `v1.2 (1)` copy. Blank registration metadata remains unknown.
- The owner authorized exactly two new guide-required diagram types: a state machine and a main-workflow activity diagram. Mermaid sources were converted/imported and curated into an editable seven-page Draw.io master: six state-machine pages for session progression, pause/recovery, early termination, participant admission, device connection and grant revocation, plus one Teacher lobby/session-start activity page. Conversion provenance and visual renders are feature-local. These are design models, not implementation evidence; the five supplied originals remain unmodified.
- The candidate inventory now states evidence, unknowns, dependencies and a proposed order for N1–N9. The owner asked for unknowns to be explicit and has not selected which items to keep/defer/omit from the near-term plan. The suggested order is not a commitment; final dossier authoring remains gated on the owner filter.
- Current deliverables remain revision 7. Rev9 adds no claims of application implementation or runtime verification. Current status, output hashes and historical package are preserved in `status/STATUS.md`, `SOURCE_REGISTER.md` and `evidence/README.md`.
