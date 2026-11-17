# Plan Rev9 — Current-state Review 2 refresh and Draw.io diagram completion

- **Date:** 2026-10-24 (Asia/Saigon)
- **Status:** Authorized documentation work; final four-dossier authoring waits for owner filtering of the detailed candidate list.
- **Feature:** FEAT-058-review2-document-package
- **Revision:** 9 (amends Rev8)

## Owner direction and scope

The owner requests four Review 2 pre-review dossiers, each as editable Word and PDF (eight files total), refreshed to the project state evidenced on 2026-10-24. The four categories are Registration+BM03, consolidated Reports 1–5+Project Tracking, BM02 Self-Review, and BM01 Design Brief+Appendix A. BM04 is post-review and excluded.

Use `[Downloads]/Phieu_FA26SE225_v1.2.docx` as the registration source. Its SHA-256 matches the previously registered `v1.2 (1)` copy; the owner-selected path is now authoritative for this refresh. Use approved SRS v3.3/B28, the school Review 2 guide and templates, supplied project reports/tracking, and the five supplied Draw.io files.

The owner directs that the two missing guide-required diagram types (state machine and main-workflow activity) be authored from Mermaid source and converted/imported to editable Draw.io pages to match the supplied diagram format. The state-machine set has separate readable pages for session progression, pause/recovery, early termination, participant admission, device connection, and grant revocation; the activity type has one Teacher lobby/session-start page. These are six pages of one requested diagram type, not additional diagram types. Final reports will use the Draw.io artifacts; Mermaid source and CLI-imported intermediates are retained as provenance. Do not replace or silently edit the five supplied Draw.io originals.

The owner asked for a detailed, evidence-backed list of current work, proposed next implementation, and unknowns so they can filter it before those priorities/statuses are finalized in the four dossiers. Keep the owner-filter gate. Do not infer priorities, owners, delivery dates, completed behavior, course metadata, or scope removal from silence.

## Status and authority boundaries

- Use FEAT-060 status and dated raw receipts as evidence for local code and checks. Current Child/Teacher checks and focused backend checks are separate; four PostgreSQL cases were skipped because `BE1_TEST_DATABASE_URL` is unset. No database-backed FE-to-BE acceptance, live Firebase login, device QR/deep-link acceptance, or Modal call is evidenced.
- The workspace has nine Alembic heads. A single clean-install/upgrade/rollback path is not approved. Do not imply schema consolidation or production migration readiness.
- WF-01/WF-02 are implemented locally in parts and checked separately; their persistence and multi-device behavior are not end-to-end verified. WF-03/WF-04 remain gated for cross-lane adoption and provider/storage configuration. Preserve all four registered workflows in the SRS unless a separately approved scope change is recorded.
- The required `review-2` tag is absent and the checkout is dirty. BM02 is a draft and cannot claim the tagged-source gate. Do not create a tag.
- The form's project/class identifier fields are blank. `FA26SE225` is present in the filename but is not confirmed by the form body. Calendar milestone dates, confirmed team availability, final effort allocations, and which candidate items the owner will retain/defer are unknown.

## Work sequence

1. Amend the FEAT-058 approval/plan records, verify the exact selected registration file hash, and update the detailed owner-filter inventory with known evidence, unknowns, dependencies, and proposed sequencing.
2. Create the missing diagram sources (Mermaid state-machine set and main-workflow activity) and convert/import them to editable Draw.io. Preserve source and conversion provenance; visually inspect all seven final Draw.io pages and record page names/hashes.
3. Present the detailed candidate list to the owner. Keep final dossier authoring blocked until the owner marks what to retain, defer, or omit from the proposed implementation plan. A filter may sequence work but may not remove registered product scope or change historical status.
4. Author the four English dossier DOCX files against the selected work list and current evidence. Use supplied Draw.io diagrams and the two converted Draw.io diagrams, all with source/page captions and an explicit design-versus-runtime boundary.
5. Export matching four PDFs, render every page, visually inspect every page, check DOCX structure and BM01 form constraints, and record hashes/page counts/limitations in feature-local evidence.
6. Update FEAT-058 context, decisions, source register, evidence index, and status. Preserve revision 7 outputs as historical and do not modify external originals.

## Acceptance criteria

- **AC41:** Registration provenance points to the exact owner-selected `Phieu_FA26SE225_v1.2.docx`; its hash and relationship to the earlier duplicate are explicit.
- **AC42:** The owner-filter inventory provides detailed current status, evidence, unknowns, dependencies, and proposed default order for each candidate, without inventing owners, dates, or completion.
- **AC43:** Exactly two new diagram types are authored from retained Mermaid source and converted to editable Draw.io: a state-machine set with six focused pages (session progression, pause/recovery, early termination, participant admission, device connection, grant revocation) and one main-workflow activity page. No other diagram type is added.
- **AC44:** Final documents embed/use Draw.io diagrams only; original user-provided diagram sources remain unmodified. Every figure has file/page provenance and is explicitly labelled as design input, not implementation proof.
- **AC45:** Four dossier categories each have a DOCX and matching PDF; BM04 is excluded. Final authoring begins only after the owner has filtered the candidate implementation list.
- **AC46:** Current implementation, checks, persistence integration, fixtures/stubs, target design, gated workflows, and unknown configuration are consistently distinguished across all four dossiers.
- **AC47:** BM02 retains the official prompt and says the dirty local snapshot plus missing `review-2` tag does not satisfy the tagged-source gate.
- **AC48:** BM01 meets the guide's order, four-page sections 0–8 limit, A4/11pt/2cm layout, exactly five decisions, three risks, at most six measurable NFRs, and Appendix A requirements.
- **AC49:** All eight outputs validate; every PDF page is rendered and visually inspected; source/output hashes, page counts, and renderer limitations are recorded in FEAT-058 evidence.
- **AC50:** Context, decisions, source register, evidence index, and status identify Rev9 and keep Rev7 output/evidence as historical.

## Risks and constraints

- The generated state-machine set and activity page are design artifacts based on SRS v3.3 and must not be read as verification evidence.
- Mermaid-to-Draw.io conversion/rendering depends on the available desktop/CLI version. If conversion cannot retain editable Draw.io geometry, preserve the Mermaid source and report the exact limitation rather than replacing it with an image-only figure.
- Supplied ERDs and architecture pages have earlier-version labels. Preserve provenance and identify version boundaries; do not assert exact match with current migrations without evidence.
- Final selection of the proposed implementation order, official class/project code, schedule dates/capacity, and approval of the required tag/run remain unknown until the owner or course authority confirms them.
- No product code edits, application tests, migration changes, live provider calls, tag/commit/push, deployment, external publication, or claim of team/reviewer approval are in scope.
