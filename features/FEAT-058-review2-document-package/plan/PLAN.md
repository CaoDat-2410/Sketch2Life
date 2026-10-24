# Review 2 four-dossier submission package

## Active refresh — Plan Rev9 (2026-10-24)

- **Plan:** `PLAN_REV9_CURRENT_STATE_AND_DIAGRAMS_20261024.md`
- **SHA-256:** `E9DB08673E88B54D8B63EE2267146D3296C73F0A79B659F4B3E7D66A9598A809`
- **Scope:** refresh the four Review 2 dossiers from current SRS/evidence, use the owner-selected registration path, create the two missing state/activity diagram types from Mermaid and convert them to Draw.io, and produce a detailed unknown-aware candidate list.
- **Gate:** final DOCX/PDF authoring waits for owner filtering of the candidate implementation list. The 2026-10-24 owner direction and direct authorization are recorded in `approvals/TASK_APPROVAL.md`.

- Revision: 6 (completed)
- Date: 2026-10-23 Asia/Saigon
- Scope: owner-authorized local source review and four Review 2 submission dossiers, each in DOCX and PDF. The Report 2 Project Management Plan and time plan are integrated in the consolidated Report 1–5/Project Tracking dossier. No runtime source changes were made for this feature.

## Request and authority

The owner requests an editable English consolidated course report covering Reports 1–5 and Project Tracking, plus a separate BM01 Design Brief. Align both with the supplied local registration v1.2, the collaborative classroom direction, the merged codebase and the Review 2 school templates. The owner has assigned Bảo FE, Đạt fullstack, Hiếu BE2 and Khoa BE1; asked that diagrams be derived from the SRS; selected the classroom durable runtime as target composition and Modal as the AI host; and directed that deployment values and the `review-2` tag be marked TBD. After a new Child UI push was reported, the owner directed fetching and merging that branch before authoring.

## Source baseline

Use local `dev@0a7ce768c153f2104cff930569c3eda6e484532c`, including refreshed Child UI source `ca3779869dfc1385cbbc7b8ca730f780386af7b2`. Preserve the older Child no-op and `32d8bc7` baseline as superseded history. Use registration v1.2 as scope authority and canonical SRS v3.1 as the broad requirements source; explain mismatches against actual mounted routes, ORM models, migrations and UI services. The required Git tag is not created. `FA26SE225` is inferred from the registration filename because the form body has no project-code or class value; label this clearly and retain Class as TBD.

## Steps

1. Read project governance/context/source register, exact registration, official Report7/BM01 templates and Review 2 guidance; preserve source hashes and local originals.
2. Refresh and pin final branch/source SHAs. Review the Child UI package and relevant backend, migration, Admin and Teacher integration evidence. Distinguish UI source, mounted routes, historical verification and open runtime work.
3. Build registration-to-requirement-to-design-to-test traceability. Create Mermaid context, use case, sequence, screen-flow, class, workflow, ERD, architecture and package diagrams; state diagrams for session, membership, AI job and video review. Mark target links and actual database foreign keys separately.
4. Author one English consolidated Report1–5/Tracking DOCX using Report7's cover/style and Report3/4/5 required sections, plus a separate English BM01 DOCX from the BM01 template. Keep Report6 out of the Review2 consolidated deliverable.
5. In BM01 provide sections 0–8 within four A4 pages, 11 pt, 2 cm margins, exactly 5 decisions, 3 risks, no more than 6 measurable candidate NFRs, testable mandatory features, one row/member, at least four owner workflows and main/exception demo scenarios in Appendix A.
6. Render both DOCX files to PDFs and page images using the available Word/Poppler fallback. Inspect every page, iterate on layout, verify BM01 page limit and DOCX structure, and record input/output hashes.
7. Update context, decisions, source register, evidence index and lifecycle status. Do not invent official code/class, application test outcomes, deployment, reviewer approval or production readiness.

## Revision 4: form-aligned Project Management Plan and time plan

The owner asked to correct the report form and provide a separate project-management report. The school source set includes `Report2_Project Management Plan.docx` and its sample high-level schedule; the Review 2 guide separately requires a consolidated Report 1–5 plus Project Tracking submission. Preserve the consolidated report and BM01 deliverables, improve the consolidated PM chapter so it agrees with the standalone plan, and add a standalone Report 2 generated from the official Report 2 template. Owner answers: use the relative 15-week SEP490 phase schedule; include preliminary person-day estimates derived from the WBS and mark them for group confirmation; describe feature-based Agile with weekly review and CI (not formal Scrum). Use the registration's September 2026–March 2027 period as the project envelope. Exact school milestone dates and team capacity are not supplied; relative weeks, effort values and the plan remain proposals, not commitments or historical actuals. The sample schedule's 2021 calendar dates are illustrative only.

The standalone Report 2 must complete every official template section: Record of Changes; Scope & Estimation with software-product WBS, complexity and person-day estimates; Project Objectives with quality/time/effort targets; Project Risks; Process; Quality Management; Training Plan; Project Deliverables with a dependency-aware schedule; Responsibility Assignments using the template's D/R/S/I legend; Project Communications; and Configuration Management covering documents, source code, tools and infrastructure. Preserve registered member names/codes and the owner's FE/full-stack/BE2/BE1 responsibility mapping. Explain that four parallel product work packages and member sprint allocation are separate planning views. Distinguish current repository evidence from planned work, and include explicit gates for contracts, migrations, staging E2E, child-safety/privacy review and the Modal profile.

Web research may inform a proposed iterative approach and GitHub Project tracking only. Use primary references (the official Scrum Guide, Agile Manifesto principles and GitHub Projects documentation), describe the chosen process only at the level confirmed by the owner, and cite sources in the report. Do not claim a formal Scrum adoption unless the owner confirms it.

## Revision 5: align Report 2 visual form with the consolidated report — complete

The owner asked to normalize Report 2's layout so it matches the other Review 2 reports; images will be added later. Use the consolidated Reports 1–5/Project Tracking document as the visual reference for cover hierarchy, heading levels, typography, table colors, page numbers, and running header/footer. Keep the official Report 2 content, section sequence, estimates, schedule, ownership and references intact. Do not add new photos or diagrams in this pass; retain the existing feature-process diagram and keep the layout suitable for later image insertion. Render and inspect the DOCX/PDF after formatting changes.

## Acceptance criteria

- AC01: Registration v1.2 controls the included scope; divergences from canonical SRS and code are explicit.
- AC02: Consolidated report includes project introduction, project management, SRS, SDD, test documentation/plan and Project Tracking with stable IDs and substantive content.
- AC03: Include context/use-case/sequence/screen-flow/class/workflow/ERD/system-architecture/package diagrams plus main-entity state diagrams. Keep editable Mermaid source.
- AC04: ERD reflects actual migrated tables and actual foreign keys; proposed logical links and cross-schema opaque references are labelled.
- AC05: Tech, provider, source-control, CI, deployment and AI-tool declarations distinguish implemented, selected, proposed and TBD.
- AC06: Branch audit records exact refs/SHAs and source evidence, including refreshed Child UI and relevant BE2/Admin/Teacher/AI branches; merged local `dev` is the document baseline.
- AC07: BM01 has exactly 5 design decisions, 3 top risks, at most 6 candidate NFR rows with metric/threshold/method, mandatory feature pass/fail criteria, all 4 owner rows, and Appendix A workflows/scenarios/test-target arithmetic.
- AC08: Neither document claims unrun tests, deployment, approved review, measured pilot capacity, or full end-to-end product integration. Historical receipts are labelled as historical and bounded.
- AC09: Both DOCX documents are structurally valid; BM01 sections 0–8 fit within 4 A4 pages at 11 pt and 2 cm margins, excluding Appendix A; every rendered page is visually reviewed.
- AC10: Original registration/templates, canonical SRS, dirty user files and runtime implementation remain unmodified. No push/tag/deployment/provider call is made.
- AC11: The standalone Report 2 DOCX uses the supplied official Report 2 template, removes instructional placeholders/examples, and fills all sections and tables required by that template.
- AC12: Report 2 contains a WBS with complexity and clearly labelled planning person-day estimates, measurable quality/time/effort objectives, a risk register, process/quality/training approach, deliverables, member responsibilities, communications, and configuration management.
- AC13: The Project Management time plan includes stage/week or date window, duration, dependencies, owner, outputs and status. It uses the registered September 2026–March 2027 period as its envelope; unknown calendar deadlines are TBD, and proposed windows/estimates are visibly marked for confirmation.
- AC14: Standalone Report 2 and the consolidated PM chapter agree on source baseline, ownership, target scope, schedule assumptions, project risks, Modal TBD status and verification limits.
- AC15: Process and tool recommendations are grounded in the supplied SEP490 Report 2 template/sample and cited primary web sources; references do not silently convert a proposal into an adopted team practice.
- AC16: Both revised consolidated report PDF and new standalone Report 2 PDF render without clipping, orphaned template instructions, broken tables or inconsistent page fields; all pages are visually inspected and output/template/source hashes recorded.
- AC17: Report 2 retains every official Report 2 section and the current approved content while adopting the consolidated report's visual form for cover, typography, heading hierarchy, table treatment, page numbering and running header/footer.
- AC18: No new photos or diagrams are added in this formatting pass; the existing feature-process diagram remains and future images can be inserted without reworking the report's structure.
- AC19: The final DOCX and PDF are rendered and every page is visually inspected after this layout revision; hashes and page count are recorded.

## Risks and constraints

- Preserve local source originals and personal contact details; only include names/student codes required by the template.
- Child, Teacher and Admin surfaces currently rely on stubs/fixtures; UI source inclusion is not service integration.
- Database migrations have independent schema roots/heads. Do not invent a production migration order or SQL relationships absent from migrations.
- Modal is selected but its app/environment/model/GPU/endpoint/region/scaling/timeout/secret and measured latency are TBD.
- Class is blank in the supplied registration; `FA26SE225` is inferred from its filename and must be identified as such.
- No runtime implementation, post-merge build/test run, push, pull request, live provider test, tag creation or deployment is in scope.

## Revision 6: complete four Review 2 dossier set and expand system detail

The owner says the current 10-page plan/report is too short, requests a fuller account of the system, and asks for all four dossier categories in the supplied Review 2 guide. Deliver four submission dossiers, each with an editable DOCX and a submission PDF: (1) the supplied registration form plus BM03 Record of Changes; (2) one consolidated Report 1–5 and Project Tracking file, with the full Project Management Plan integrated as Report 2; (3) BM02 Self-Review; and (4) BM01 Design Brief plus Appendix A. Do not count the earlier standalone Report 2 working draft as a fifth submission dossier. Preserve its approved schedule, WBS assumptions and management content inside the consolidated report.

Expand the consolidated report by documenting the registered product end-to-end: actors and authorization boundaries; functional requirements and acceptance criteria; classroom and group behavior; drawing, AI review, gallery, knowledge/video, off-screen activity and reflection; consent/privacy/retention; component and data boundaries; current implementation and runtime composition; API/persistence/migration constraints; state machines; recovery/error paths; test strategy/cases; project schedule, estimates, ownership, risks, communications, configuration and current tracking. Distinguish registered requirement, implemented source, fixture/stub, selected design, proposal and TBD. Keep all claims anchored to registration/SRS, repository source or explicitly marked proposal. Do not inflate page count by repeating the same prose.

BM02 must preserve the course's standard prompt byte-for-byte and keep its findings in the required one-table format with an added Team response column. The requested `review-2` tag does not exist and the active `dev` checkout contains uncommitted changes. Therefore report the exact branch/commit and whether the working tree was read; label the result as a draft self-review that does not satisfy the course's tagged-baseline execution gate. Do not fabricate a tag, clean-tree state, commit links, reviewer response, or completed fixes. Include evidence-based proposed responses and owners/dates as pending confirmation. Every High finding left Kept or Planned must appear in BM01 Known Gaps.

The owner selected evidence-based proposed BM02 responses and both PDF and DOCX deliverables. No new code, test, provider call, tag, commit, push, deployment, external publication or supervisor approval is authorized. Preserve personal registration data only in the intended registration dossier. No images are required; keep the report image-ready for later additions.

### Revision 6 acceptance criteria

- AC20: The output package contains exactly four dossier categories, each represented by one editable DOCX and one PDF. The Report 1–5/Tracking dossier includes the detailed Report 2 PM Plan; no fifth standalone PM Plan is part of the submission package.
- AC21: Report content is materially expanded beyond the prior 25-page consolidated file and documents the complete registered system and current code structure without repeated filler. Report 3/4 include stable requirements, actors, testable criteria, measurable candidate NFRs, architecture, logical ERD/database alignment, main-entity state machines, whole-system activity diagrams, technology declarations, service/data flow and explicit current-versus-target labels.
- AC22: Report 2 includes the approved 15-week relative time plan, WBS/person-day proposal, owners, dependencies, outputs, risks, communications, quality, training, configuration and TBD calendar/capacity assumptions.
- AC23: BM02 uses the exact official prompt, lists the run tool/date/form/source context, preserves all generated findings and adds an evidence-based Team response. It clearly records that no `review-2` tag exists and this is not the required tagged-source execution.
- AC24: BM01 sections 0–8 follow BM01 order and limits (four A4 pages, 11 pt, 2 cm margins), contain no more than six NFR rows, exactly five design decisions and three top risks, and repeat every High Kept/Planned BM02 finding in Known Gaps. Appendix A includes at least four owned workflows, main and exception demo cases, case-count formula and explicit proposed targets.
- AC25: Registration source remains unchanged; BM03 either records the confirmed changes or states No changes without inventing edits. Any absent code/class/supervisor data remains labeled or blank as in the supplied authority source.
- AC26: Current code, proposed target, stubs/fixtures, historical test receipts, current uncommitted state and unverified deployment are distinguished throughout. No production readiness, connected UI flow, Modal GPU endpoint, performance result, team commitment or review approval is inferred.
- AC27: All four DOCX files pass package/structure checks; four final PDFs are rendered from them; every page is visually inspected; BM01 page limit/geometry and BM02 prompt integrity are verified; hashes, source baseline, source limitations and QA are recorded in feature-local evidence.
- AC28: Update this feature's context, decisions, source register, evidence index and status. Keep all originals and the existing dirty workspace unmodified outside the four derived dossier sources and feature-local governance/evidence.

## Verification

Validate requirement/diagram/acceptance links, ownership and test-target arithmetic, BM01 page count/geometry, DOCX package integrity, source input hashes and every rendered page. Keep the existing repository security scan as historical merge evidence. This document-only work does not run app tests.

## Revision 6 completion

All four dossier pairs are generated, structurally checked, rendered and visually reviewed page by page. Final page counts are Registration+BM03 9, consolidated Reports 1–5/Tracking 49, BM02 Self-Review 3, and BM01 Design Brief 4 (sections 0–8 on pages 1–3; Appendix A starts on page 4). The final receipt, source hashes, output hashes and render inventory are indexed in `evidence/README.md`. AC20–AC28 are complete. The only course-gate limitation is BM02's missing `review-2` tag: the self-review remains an evidence-based draft against the dirty local `dev` snapshot and is not represented as the official tagged-baseline run. Application tests were not run for this documentation task.

## Revision 7: correct horizontal overflow in rendered dossiers

On 2026-10-23, after reviewing the delivered PDFs, the owner reported that some content extends beyond the left/right page padding. Inspecting the final render confirmed over-wide tables in the consolidated report; the requirements catalog clipped identifier prefixes, and other wide tables approached or crossed the page content bounds. Revise the table-width logic in the document builder so each table and every row, including its header row, share an explicit column grid within the printable width. Keep the prose, source facts, requirement IDs, and table data unchanged. Rebuild and render all four DOCX/PDF pairs, then inspect every page and record new hashes and page counts.

### Revision 7 acceptance criteria

- AC29: No visible text, table border/fill, diagram, or other page content in any of the four final PDFs is clipped or placed outside the page content area. Table grids and row cell widths are explicit and fit within the usable page width; requirement identifiers remain complete. All four final PDFs are regenerated from the corresponding DOCX sources, all pages are rendered and visually inspected, and new output hashes/page counts are recorded.
- AC30: BM01 sections 0–8 remain within four A4 pages at 11 pt with 2 cm margins; all prior revision 6 document content and BM02 tagged-baseline caveat remain unchanged by the layout-only fix.

The owner directly authorized this layout correction. It does not authorize new application behavior, app tests, tag creation, commit, push, deployment, provider calls, or external publication.

### Revision 7 completion

AC29–AC30 are complete. The report table builder now sets a consistent fixed grid and explicit widths on every header and data cell, scaled to a safe printable width. The regenerated report retains complete FR identifiers. All four DOCX/PDF pairs were exported to `artifacts/submission_r2_rev7/`; all 66 pages were rendered and visually reviewed. The QA receipt records no horizontal layout violations, with at least 18 pt page-edge clearance for text and drawing objects; BM01 remains four pages with its sections 0–8 on three pages and Appendix A on page 4. Revision 7 supersedes revision 6 as the current output set.

## Revision 8 plan

The owner requests a refresh against current SRS v3.3, the current FEAT-060 implementation status, and the supplied Draw.io sources. Each of the guide's four dossier categories will have one editable DOCX and one PDF. The owner explicitly requests no new Mermaid or agent-created diagrams and asks to filter the in-progress/next-work list before finalizing. Plan Rev8, acceptance criteria AC31–AC40, source authority, diagram coverage gap, and the draft owner filter list are recorded in `PLAN_REV8_DRAWIO_CURRENT_STATE_REFRESH_20261024.md` and `evidence/notes/OWNER_FILTER_CANDIDATES_20261024.md`. Final document authoring waits for the owner to select the next-work items and either supply the missing state/activity Draw.io pages or accept that those guide requirements remain unsatisfied and are identified as gaps. Revision 7 remains historical until revision 8 passes its gates.
