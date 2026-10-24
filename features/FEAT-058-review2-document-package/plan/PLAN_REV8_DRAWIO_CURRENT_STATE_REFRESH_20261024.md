# Plan Rev8 — Refresh Review 2 documents with current SRS and supplied diagrams

- **Date:** 2026-10-24 (Asia/Saigon)
- **Status:** Plan prepared; final document authoring is waiting for the owner's requested filter of the active/future work list and resolution of the missing diagram inputs.
- **Feature:** FEAT-058-review2-document-package
- **Revision:** 8

## Owner request and approved output shape

The owner asks to update the SRS and the Review 2 documents from the supplied course guide, describe the actual project state, list work still in development or planned for implementation so the owner can filter it before finalizing, use the supplied Draw.io diagrams, and avoid adding Mermaid or newly invented diagrams. The owner clarified that the guide's four dossier categories should each be delivered as an editable Word file and a PDF: eight final files total.

The four submission dossiers remain:

1. Proposed registration form plus BM03 Record of Changes.
2. Consolidated Reports 1–5 and Project Tracking, including SRS and SDD.
3. BM02 Self-Review.
4. BM01 Design Brief with Appendix A.

BM04 Review 2 Commitment is completed after the review meeting and is not one of the four pre-review submission dossiers in the supplied guide. Do not create or fill BM04 for this package.

## Source and status authority

- Use the current owner-approved SRS v3.3, including B28 decisions dated 2026-10-24, as the current requirements text. Preserve v3.2 and v3.1 originals.
- The prior FEAT-058 source register identifies `Phieu_FA26SE225_v1.2 (1).docx` as the registration scope authority. Keep it unless the owner identifies a newer approved registration form. `Phieu_FA26SE225_updated.docx` exists locally but describes a previous parent/guide-focused product scope and conflicts with the current collaborative classroom SRS; it is not substituted silently.
- Use FEAT-060 status and evidence dated 2026-10-24 to distinguish local implementation, separate local checks, database-backed verification, and remaining engineering gates. The repository is on `dev@0a7ce768c153f2104cff930569c3eda6e484532c` with a large dirty working tree. Do not describe uncommitted work as merged or released.
- Keep the missing `review-2` tag caveat in BM02. Do not create a tag or represent a dirty-checkout self-review as the official tagged-baseline run.

## Diagram sources and constraint

Use only diagrams from the owner's five supplied `.drawio` files. Preserve their source files and page contents; add English captions and text that distinguishes target/design diagrams from verified implementation. Do not create Mermaid/PlantUML diagrams or draw new diagrams for this revision.

The inspected sources contain business/system context, use cases, main/detailed session sequence, screen flow, class diagram, logical ERDs, system architecture, and package diagram. No explicit state-machine or business-workflow activity diagram was found in these five files. The Review 2 guide requires state machines for main lifecycle entities and activity diagrams/flowcharts for main workflows. Before authoring the final package, the owner must either provide those missing Draw.io source pages or explicitly accept that those required diagram items will be identified as gaps in the reports.

## Owner filter gate

The candidate inventory is in `evidence/notes/OWNER_FILTER_CANDIDATES_20261024.md`. Before finalizing BM01 mandatory features, Report 2 schedule/priorities, and current-versus-future labels, obtain the owner's selection of which engineering follow-ups to call the next implementation targets. Registered product requirements must not be removed from the SRS by this filter; any proposed scope change must be recorded through BM03 and the required review decision.

## Work steps

1. Preserve hashes for the guide, registered form, current SRS, and all five supplied Draw.io sources; record the current repository baseline and its dirty-state limitation.
2. Resolve the owner filter gate and missing state/activity diagram source decision before final Word/PDF authoring.
3. Update the consolidated Report 1–5/Tracking dossier from SRS v3.3 and the evidence-backed current system status. Label local implementation, fixtures/stubs, verified checks, blocked workflows, proposed follow-ups, and TBD values separately.
4. Reconcile BM03, BM02 and BM01 to the same registration scope, SRS revision, team roles, requirement IDs, workflow statuses, gaps and owner-selected next-work list. Preserve the standard BM02 prompt exactly.
5. Use the supplied Draw.io pages in Report 3/4 with source-file/page provenance. Do not embed the prior Mermaid-generated figures in the new deliverables.
6. Create exactly four final `.docx` files and four corresponding `.pdf` files under `artifacts/submission_r2_rev8/`, with stable Review 2 filenames.
7. Render every PDF page to images, inspect every page, validate DOCX package integrity and BM01's four-page limit, and record source/output hashes, page counts, diagram provenance and limitations in feature-local evidence.
8. Update FEAT-058 context, decisions, source register, evidence index and status; keep user-provided originals unchanged.

## Acceptance criteria

- **AC31:** Exactly four dossier categories are present and each has one editable DOCX and one PDF. No fifth dossier or extra final deliverable is included.
- **AC32:** The consolidated report uses approved SRS v3.3/B28, current registered scope, and the 2026-10-24 FEAT-060 evidence baseline. It clearly distinguishes implemented locally, verified, partially integrated, fixture/demo, planned, blocked and TBD states.
- **AC33:** The owner-filtered implementation list appears consistently in the Report 2 plan/tracking section, BM01 Known Gaps/Mandatory Features, and BM02 team responses. No unapproved date, implementation commitment, reviewer decision or completion claim is invented.
- **AC34:** All included diagrams come from the five supplied Draw.io source files, with file/page provenance and a note that the source diagrams are design inputs rather than proof of runtime implementation. No new Mermaid/PlantUML or agent-created diagram is present.
- **AC35:** The state-machine and activity-diagram requirements are either satisfied by owner-supplied Draw.io pages or explicitly identified as missing at the owner's direction. No diagram is fabricated.
- **AC36:** BM02 preserves the official standard prompt verbatim, reports the current source/working-tree context, and retains the missing `review-2` tagged-baseline limitation.
- **AC37:** BM01 sections 0–8 follow the official order and remain within four A4 pages at 11 pt and 2 cm margins; it has exactly five decisions, three top risks, at most six measurable NFRs, one row per member, and the required workflow/demo/test target content in Appendix A.
- **AC38:** BM03 accurately records the approved registration disposition and does not silently replace the registered form or change scope.
- **AC39:** All four DOCX packages validate; all four PDFs are rendered and every page is visually inspected; hashes and page counts are recorded in FEAT-058 evidence.
- **AC40:** FEAT-058 context, decisions, source register, evidence index and status identify revision 8 and preserve revision 7 as historical output.

## Risks and constraints

- Some supplied diagrams identify themselves as SRS v3.1 and may not include v3.3/B28 updates; preserve them and label the version boundary rather than editing their content without authorization.
- The two supplied ERDs may differ and target entities may not correspond to the current nine-head migration graph. Report that boundary; do not imply DDL/ERD parity without evidence.
- FEAT-060's current UI/backend checks are separate and do not prove a PostgreSQL-backed end-to-end workflow. The isolated database URL is not configured.
- WF-03 AI and WF-04 reviewed-media/activity workflows remain gated by FEAT-057 card adoption and provider configuration. Modal is selected, but no deployment profile/live call is verified.
- The registration body leaves class/project-code fields blank; `FA26SE225` remains inferred from the filename until confirmed.
- The Review 2 guide's official form is English. Keep deliverables in English and preserve Vietnamese labels inside source diagrams, with English captions and explanation.
