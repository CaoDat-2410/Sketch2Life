<!-- SRS-AUTHORITY-REV67 -->
> **Historical SRS context — not current product authority.** Current product requirements and target architecture are defined only by `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (v2.7-draft; Rev57 baseline, local amendments through Rev67; unsigned). Treat older SRS versions and authority claims in this feature context as dated snapshots; use this file for feature-local status/provenance only. See `docs/context/SRS_AUTHORITY.md`.
# Review 2 four-dossier package context

## Rev28 BM04 Sections 6–8 — current local copy (2026-11-09)

- Source: the newly supplied `SWP490_R2_BM04_Review2_Commitment_1.docx`, SHA-256 `FC8293411F8F79BEAACE0149F248A11E7AD8D05C756ACFFE76E161B02E055D20`; output is a separate Rev28 copy, SHA-256 `0FD7DEFA1BA3CE5BE9ABCD42227AA19235E4BFC002151A69ACB452D323ADAE9D`.
- Only Sections 6–8 changed. The four workflow leads are temporary planning assignments; Section 7 is one broad responsibility row per person. All 11 cases are temporary design only, unrun, not team-committed and not mapped to CI. The misplaced CI/CD workflow content was removed.
- BM01–BM03 Rev26 were cross-checked and left unchanged. A contradiction outside the authorized section boundary remains in BM04 Section 2: it says the FA v1.3 form is attached as updated, while BM01–BM03 say its update is pending. BM02's `38-table mapping/backfill` phrase also needs scope clarification; it may refer to the 38 retained/refactored mappings.
- The canonical SRS §28.2 now explicitly labels the no-eligible WF-03 case as a temporary test assumption, not an eligibility/consent policy decision. The SRS remains v2.5-draft and unsigned.
- Structural checks passed: only `word/document.xml` differs; body blocks outside Sections 6–8 are identical; 11 unique IDs, four workflow headings, four Section 7 member rows, and no empty cells. Visual page review remains incomplete because the bundled renderer could not find `soffice.exe`.
- Evidence: `evidence/REV28_BM04_FORMAT_AND_CROSS_DOCUMENT_REVIEW_20261109.md`; plan approval and hash are recorded in `approvals/TASK_APPROVAL.md`.

## Rev27 BM04 Sections 6–8 — historical; superseded by Rev28 (2026-11-09)

- Rev27 is a separate copy of the owner-edited Rev26 BM04. Source SHA-256 `1246E9698FA37FD33CAE6C5D40FDA2900372258FCE80EB90EC05541232155F98`; output SHA-256 `CBB6573D3815734BDEB03D00DA73AC8A2BADCEF85AFEC601E488EDE39FA56A9C`.
- Only Sections 6–8 changed. Rev26, BM01–BM03 and BM04 content outside those sections remain untouched. The new workflow leads are temporary role-based planning entries; the 11 cases are design-only and 0/11 are mapped to current CI.
- The canonical SRS v2.5-draft was aligned under FEAT-063 Plan Rev58. No CD workflow, CI run, test execution or deployment is claimed.
- Structural QA confirms the DOCX package is valid, only `word/document.xml` differs, the 68 non-target body blocks are identical, and no Section 6–8 table cells are empty. Visual pagination was not verified because the bundled DOCX renderer and a connected Word session were unavailable.
- Evidence: `evidence/REV27_BM04_SECTIONS_6_8_QA_20261109.md`. Plan Rev27 and direct owner authorization are recorded in `approvals/TASK_APPROVAL.md`.

## Rev26 completed — owner-supplied BM01–BM04 documents — 2026-11-09

- Rev26 is a separate local four-DOCX copy based on the owner-edited Rev25 files in Downloads. The Rev25 source hashes and preliminary audit are recorded in `evidence/REV25_BM01_BM04_PRELIMINARY_AUDIT_20261109.md`; final output hashes and QA are in `evidence/REV26_BM01_BM04_FINAL_QA_20261109.md`.
- The edits explain each out-of-scope rationale, provide 11 detailed design-only test cases, remove the requested placeholder wording from the Rev26 documents, and align shared facts across BM01–BM04. Existing prompts and owner edits were retained; owner assignment cells remain blank.
- Product requirements reference only the canonical unsigned FEAT-063 SRS v2.5-draft. Review 2 occurred on 2026-10-26; the owner confirmed all six BM03 changes were accepted, while the FA v1.3 registration form itself still awaits those edits.
- Word displayed and all 32 pages were visually reviewed: BM01 10, BM02 4, BM03 2 and BM04 16. No application tests were run and no PDF, product code, runtime, Git publication or deployment was produced. The repository submission-artifact package remains Rev22; Rev26 is not that package.

## Current Rev22 FPT cover correction — 2026-10-26

- The owner asked to restore the FPT logo and match `<LOCAL_ROOT>/Downloads/Document/Document`. Rev22 uses the exact FPT University lockup image extracted from `Report1_Project Introduction.docx`; source document and prior Rev21 package remain preserved.
- The report cover now follows the reference hierarchy: centered FPT lockup, capstone report heading, report-scope subtitle, centered Sketch2Life title with `AI for Children`, and city/date. Its official logo artwork contains the Vietnamese university name; editable report text stays English/ASCII. The separately approved FEAT-026 English SRS is unchanged.
- Rev22 has four DOCX/PDF pairs at 6/9/102/4 pages. Three non-report pairs match Rev21 byte-for-byte. Report pages 2–102 are pixel and text identical to Rev21. Hashes and comparison evidence are in `evidence/metrics/rev22-cover-qa.json` and `evidence/REV22_FPT_COVER_QA_20261026.md`.
- Rev21 pricing, SRS v3.5, restored BM03, D01/D02 treatment, page flow, PROPOSED prices and NOT IMPLEMENTED billing boundary remain unchanged.

## Historical Rev21 pricing update — 2026-10-26

- The owner supplied the "School plans and billing" image and directed this price/package update. Rev21 is built from preserved Rev20; the three non-report dossier DOCX/PDF pairs remain byte-identical.
- The report billing table on PDF p38 now shows Free Trial: 14 days, 1 active class, 3 shared AI credits, no payment method; Plus: 999,000 VND/month, 5 classes, 10 Teacher seats, 100 shared credits; class add-on 99,000 VND/month; Teacher seat add-on 49,000 VND/month; one-time 15/45/80-credit packs at 149,000/399,000/799,000 VND. Every money amount is PROPOSED.
- Billing flow is Teacher with `billing:manage` → Teacher Desktop checkout → MoMo/VNPay/participating-bank VietQR → server verifies payment → school entitlement and shared quota update. Child Android has no checkout or purchase prompts; billing remains NOT IMPLEMENTED.
- Current Master SRS is v3.5 and the FEAT-039 copy is byte-identical. Registration has no price figures; the BM03 Record of Changes is restored. D01 Business Context remains; D02 C4 System Context is omitted.
- Full package: artifacts/submission_r2_rev21/, PDF counts 6/9/102/4, 121 pages total. Render, hashes, figure mapping and pair comparison are in evidence/metrics/rev21-package-qa.json and evidence/REV21_PRICING_AND_PACKAGE_QA_20261026.md.
- The English current-system SRS derivative is also finalized at 13 pages. It uses an ASCII filename, English-only text, all four team members, centered “AI for Children” title and Arial 10 pt for all editable text; its Appendix A now starts on page 13 without a footer-only page.

## Historical Rev20 package and format remediation — 2026-10-25

- The owner requested restoration of BM03 Record of Changes, retention of D01 Business Context while removing D02 C4 System Context, repairs to the report content originally on pages 51/66/73, and an English-only SRS filename/body with team names, aligned title, proofreading and consistent typography.
- Approved Rev20 report scope and English SRS derivative plan are recorded in their feature-local plans and TASK_APPROVAL records. Rev20 report outputs are in artifacts/submission_r2_rev20/ with four DOCX/PDF pairs totaling 121 pages (6/9/102/4).
- Registration contains the restored BM03 appendix. The report introduction retains D01 and excludes D02 C4. The title is centered, the team names and responsibilities are listed, and report text uses Arial with the 10/9/12/18 pt hierarchy.
- Former report p51 D24, p66 D29 and p73 D38 are on Rev20 pages 54, 70 and 77. All pages were rendered; unchanged Design Brief, Registration and Self-Review pairs have the same hashes as Rev19. Details are in evidence/REV20_FORMAT_AND_PAGEFLOW_QA_20261025.md and evidence/metrics/rev20-package-qa.json.
- The separate FEAT-026 SRS derivative is features/FEAT-026-current-system-srs/artifacts/Sketch2Life_SRS_Form_English.docx and its PDF. It is English-only with an ASCII filename, lists all four team members in the introduction, uses a centered title containing “AI for Children”, and uses Arial 10 pt for every editable text run. The original Vietnamese source remains unchanged.

## Historical Rev19 format and page-flow remediation — 2026-10-25

- The owner requested that BM03 Record of Changes be restored to the Registration derivative, the attached Review 2 format findings be fixed, D02 C4 System Context be removed while retaining D01 Business Context, and page flow around original report pages 51, 66 and 73 be repaired. Approved scope is Plan Rev19; its content SHA-256 is `502E5CD0ADF6D6848BD632225ED07FA64FD54E753FA9A6873A2CAED310BF9104`.
- Rev19 outputs are in `artifacts/submission_r2_rev19/`, exactly four DOCX/PDF pairs. PDF counts: Design Brief 6, Registration/BM03 9, Report 1–5/Tracking 99, Self-Review 4 (118 pages total). Registration has the BM03 change record restored from the preserved pre-Rev18 derivative; the supplied v1.2 original and Rev18 outputs remain unchanged.
- The report cover is page 1, the complete TOC is pages 2–3, and report content begins on page 4. Section IV headings are sequential 1–11, the TOC includes Section VI item 4, and Arial is used throughout the report (10 pt body, 8.5 pt data tables, 8 pt TOC). D01 remains; D02 is removed.
- Original Rev18 target pages map by content: page 51 D24 is now page 52 with its caption and diagram; page 66 D29 is now page 68; page 73 D38 is now page 75. Each caption/image pair starts cleanly and fits on one page. Rev19 QA and page-level renders are indexed in `evidence/REV19_FORMAT_AND_PAGEFLOW_QA_20261025.md`, `evidence/metrics/rev19-package-qa.json` and `evidence/render/rev19/documents/`.
- All 118 pages were rendered and reviewed in overview sheets. The cover/TOC, dense tables, D01, D24/D29/D38 and restored BM03 were additionally reviewed at full size. No page lacks extractable text or is visually blank; report table-size and font audits pass. No application test, runtime change, commit, push, tag, deployment, provider call or publication was performed.

## Historical Rev18 Registration amendment — 2026-10-25

- The owner requested removal of the BM03 “Registration Form – Record of Changes” appendix from Registration. It is removed from the DOCX/PDF derivative; the supplied v1.2 source remains unchanged. The final PDF remains at `artifacts/submission_r2_rev16/SWP490_FA26SE225_R2_Registration.pdf` and is 8 portrait pages. Its final paragraph remains with the signature fields; no trailing blank page remains.
- The current four pairs total 111 PDF pages: Design Brief 6, Registration 8, Reports 1–5/Tracking 93, Self-Review 4. All pages were rendered, no page is textless or visually blank, and the three non-Registration DOCX/PDF pairs retain their Rev16 hashes. Current hashes and page inventories are in `evidence/metrics/rev18-package-qa.json`; typography/source hashes are in `evidence/metrics/rev18-language-and-typography-audit.json`.
- The pre-Rev18 Registration pair and Rev16 receipts are preserved in `evidence/snapshots/pre_rev18_registration/`. The earlier independent 3.9/5 scorecard applies to that pre-Rev18 state and was not re-scored for the limited appendix removal; QA is in `evidence/REV18_REGISTRATION_RECORD_REMOVAL_QA_20261025.md`.

## Historical Rev16 checkpoint — before Rev18 Registration amendment — 2026-10-25

- Rev16 is the latest local four-pair package. It uses the owner's updated Context, Use Cases and Main Session Sequence Draw.io inputs; the derived editable master is `artifacts/diagrams/rev16/drawio/Sketch2Life-Review2-Diagram-Master.drawio` with D01–D52.
- All visible text in the master and five derived Draw.io sources is Arial 12 pt. The derived THieu diagrams have 95 visible Vietnamese labels translated into English. Supplied originals and Rev15 outputs are preserved; detailed input/output hashes and page mapping are in `evidence/diagram-master-qa-rev16.json`.
- Rev16 includes exactly four DOCX/PDF pairs under `artifacts/submission_r2_rev16/`: Design Brief (6 pages), Registration/BM03 (9), consolidated Reports 1–5/Tracking (93), and Self-Review (4), 112 PDF pages total. All pages were rendered; none lacks extractable text or is visually blank. Detailed page inventory and hashes are in `evidence/metrics/rev16-package-qa.json`.
- All 2,992 visible text cells across the 52-page master and five derived Draw.io files use Arial 12 pt with zero exceptions. The derived THieu diagrams contain 95 English translations. The report's Billing price table is on p35; D47–D52 follow on pp36–38. D43–D46 and other design models remain inline beside related sections. Page and figure mapping is in `evidence/metrics/rev16-figure-page-map.json`.
- Orientation audit: Design Brief and Registration are portrait throughout; Report pages 24–26 (D17 panels), 41 (D19), 42 (D20) and 47 (D18) are landscape only for their wide diagrams and carry their captions in the related section context. The other 87 report pages are portrait. BM02 is landscape across all four pages for its seven-column findings register. The final orientation pass found no arbitrary landscape page.
- Registration's derived Review 2 form displays confirmed class code SWP490 from the official guide; the submitted v1.2 original remains preserved. Its BM03 label now distinguishes that unchanged source form from the approved SRS v3.4 scope amendment. The formal signature area remains available.
- Cross-model item to resolve: B29 requires durable school subscription/payment-attempt/entitlement/credit-ledger records; D50 shows billing persistence at architecture level, while D19/D20 omit those billing entities and relationships. The package marks this model detail open and does not claim implementation. BM02's final page contains the summary plus proposed N1–N9 dependency sequence; owners, dates, environments, policies and thresholds stay TBD. Full QA and remaining zoom-dependent diagram readability limits are in `evidence/REV16_DIAGRAM_STANDARDIZATION_AND_PDF_QA_20261025.md`.
- Billing/payment remains baseline scope in SRS v3.4 but is NOT IMPLEMENTED; monetary prices are PROPOSED. No runtime changes, application tests, commit, push, tag, deployment, provider call, or external publication were made for Rev16/17. The independent reviewer scored the final package 3.9/5; the full scorecard and remaining limitations are in `evidence/REV16_INDEPENDENT_REVIEW_20261025.md`.

## Current Rev15 checkpoint — 2026-10-25

- Rev15 is the current local four-pair package. Plan, approval and output checks are in `plan/PLAN_REV15_REVIEW_COMMENTS_20261025.md`, `approvals/TASK_APPROVAL.md`, `status/STATUS.md` and `evidence/README.md`.
- Page 10 uses a text cross-reference for WF-01–WF-04; it no longer presents an empty figure caption. D44/WF-02 is on report p49, D43/WF-01 on p53, D45/WF-03 on p55 and D46/WF-04 on p57, beside related design subsections.
- Billing still has its full package/add-on table on p36. D47–D52 are on pp37–39. Internal title/type banners were removed from the six derived billing canvases; figure captions above them retain the diagram labels.
- Four PDF page counts are 6, 9, 94 and 6. All 115 pages were rendered and no page is missing extractable text. Affected pages 10, 36–39 and 48–57 were visually reviewed. The five supplied Draw.io originals remain hash-identical; Rev14 outputs remain preserved.
- Billing/payment is baseline scope in SRS v3.4 but NOT IMPLEMENTED; price amounts remain PROPOSED. No runtime change, application test, commit, push, tag, release, provider call, deployment or external publication is claimed.

## Historical Rev14 checkpoint — 2026-10-25

- Rev14 is the current local four-pair package; details and QA are in `status/STATUS.md`, `evidence/README.md` and `evidence/REV14_PRICE_TABLE_AND_LAYOUT_QA_20261025.md`.
- The consolidated report contains the requested price table in Section 10 Billing on PDF page 36, ahead of payment diagrams D47–D52. Only price amounts are PROPOSED; package and quota structure are SRS v3.4 baseline.
- Report figures D18, D23–D25, D28, D35 and D36 are placed alongside Section 3 design subsections; generated captions identify diagram type and do not credit a source on-canvas.
- Four PDF page counts: 6, 9, 92, 6. All 113 pages are rendered; no blank pages. Rev13 inputs and all owner-supplied originals remain preserved.
- Billing is baseline scope and NOT IMPLEMENTED. No runtime change, app test, commit, push, tag, release, provider call, deployment or external publication is claimed.

# Review 2 four-dossier package context

## Historical Rev13 checkpoint — 2026-10-25

- Status: Rev13 four-dossier DOCX/PDF set and derived Draw.io files are regenerated and visually reviewed. Rev13 is local; no new commit, push, tag, or release is claimed. The existing hosted CI/Iteration 1 gates remain open/failed, and `review-2` has not been created.
- Outputs: `artifacts/submission_r2_rev13/` contains exactly four dossier categories as DOCX/PDF pairs: Design Brief 6 pages, Registration/BM03 9 pages, Reports 1–5/Tracking 93 pages, and Self-Review 6 pages. The full Registration/BM03 output contains contact information; PDFs and renders remain local.
- Billing/SRS: Master SRS v3.3 retains approved B28 and appends segregated B29. The school-level Free Trial, Plus at 999,000 VND/month, class/Teacher add-ons, AI top-ups, quotas, MoMo/VNPay/VietQR and requirements are all marked PROPOSED; B29 is not implemented or adopted. The Registration derivative records only the proposed billing/payment capability and contains no price figures.
- Diagrams: the derived master `artifacts/diagrams/rev13/drawio/Sketch2Life-Review2-Diagram-Master.drawio` has 52 editable pages D01–D52. Six payment-design pages D47–D52 are appended to five derived copies and the master. All five supplied Draw.io originals were hash-checked and remain unchanged. D47 context, D48 screen flow, D49 use case, D50 component architecture, D51 payment sequence, and D52 payment-attempt state machine are target designs.
- PDF/layout QA: all final pages were rendered; each dossier has no blank pages and no source-attribution captions. Report figures appear in their related sections; there is no diagram gallery in an appendix. The formerly split Workstream status row now fits wholly on report p88; Section 9 introduction and readable D23 share p54; all references are together on p90 and textual Appendix D starts on p91. Layout notes, hashes and page inventory are in `evidence/metrics/rev13-package-qa.json`.
- Current-state discrepancies are recorded in `artifacts/REV13_CURRENT_STATE_RECONCILIATION.md`: registered age 36–155 months conflicts with a backend guard capped at 107 months; modeled and persisted lifecycle behavior needs contract mapping; WF-01/WF-02 lack PostgreSQL/device acceptance; WF-03/WF-04 are gated; B29 remains proposed; team ownership and release gates remain unconfirmed.
- Approved plan: `plan/PLAN_REV13_FULL_PDF_REVIEW_AND_REPORT_REFLOW_20261025.md`; the owner’s authoring/export scope and pricing clarification are in `approvals/TASK_APPROVAL.md`.
- Supporting receipts: `evidence/diagram-master-qa-rev13.json`, `evidence/metrics/rev13-package-qa.json`, and rendered page images under `evidence/render/rev13/`.

## Historical Rev12 checkpoint — 2026-10-24

- Status: Rev12 diagrams and four local DOCX/PDF dossier pairs have been regenerated, rendered and visually checked. Repository-security validation passed; commit `83695ef1` was pushed to `origin/dev`. Hosted CI/Iteration 1 release gates remain open; the `review-2` tag has not been created.
- Outputs: `artifacts/submission_r2_rev12/` has four dossier categories as DOCX/PDF pairs. Current PDF counts are Design Brief 6, Registration+BM03 10, Reports 1–5+Tracking 100, and Self-Review 6. Registration+BM03 and all PDFs remain local.
- Diagram package: 46 editable Draw.io pages combine 22 supplied-derived pages and 24 authored pages (20 state-machine, 4 activity). The five supplied originals are unchanged; 16 source-attribution cells were removed only from the derived master and rendered figure copies. Each report figure has a diagram-type caption and no source caption.
- Layout QA: all 24 authored canvases were individually reviewed at full size. Label-label, label-node, node-node, route-node, route-label, and route-crossing counts are zero. Session terminal, device grant-revocation, and Data Request cancellation/external-purge paths are separated into focused companion state machines without dropping transitions. Receipts: `evidence/diagram-qa-rev12.json`, `evidence/render/rev12/diagrams/layout-qa.json`, and `evidence/diagram-master-qa-rev12.json`.
- Report PDF: all 46 gallery figures are on pages 52–97, each with a diagram-type caption. The Appendix D TOC points to page 51 and Appendix E to page 98. Every PDF page is rendered; no blank pages or source captions were found.
- Near-term proposal remains Keep N1–N4 and N7; Defer N5, N6, N8 (rewind disabled), and N9; omit none from registered scope. Unknowns and proposed owners/dates are detailed in the report and await owner/team confirmation.
- Git baselines: `dev@d0a754a2` is the source snapshot used in the dossier; `83695ef1` is the published package/diagram commit on `origin/dev`. The worktree is clean. Hosted run `40101108871` failed the repository-policy, Admin UI and Teacher UI jobs; backend and Child UI jobs passed. The local P4 component runner also failed, so no `review-2` tag or tag-specific BM02 run is claimed.
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
