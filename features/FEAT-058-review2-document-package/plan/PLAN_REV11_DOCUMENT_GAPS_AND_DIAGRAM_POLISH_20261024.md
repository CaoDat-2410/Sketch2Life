# Plan Rev11 — Review 2 documentation, diagrams, and final baseline

- Date: 2026-10-24
- Status: APPROVED by the project owner's direct replies on 2026-10-24; see `approvals/TASK_APPROVAL.md`.
- Base package: Rev10, source commit `d0a754a2`.
- Feature: FEAT-058-review2-document-package.

## Owner request and authority

The owner asked to fix the findings in the supplied peer review, inspect and redraw authored diagrams with crowded arrows, omit source attribution from diagram canvases, and deliver the four Review 2 dossier categories as DOCX/PDF pairs. The owner also authorized a dependency-based near-term plan with unknowns stated plainly, CI preparation and Iteration 1 checks, and creation of the official `review-2` tag plus a BM02 run only after the final baseline passes its gates. Suggested owners and dates are proposals for owner/team confirmation, not accepted assignments.

The peer review is an input to verify against the course guide and repository. Its statements do not override current repository evidence, approved SRS, or owner instructions.

## Scope

1. Inspect all 22 authored Mermaid lifecycle/activity models and their editable Draw.io pages. Redraw pages where transitions, labels, nodes, or notes collide, overlap, or clip. Preserve behavioral meaning and supplied original Draw.io inputs. Each page title must state its diagram type (for example, “State Machine Diagram — Session Lifecycle” or “Activity Diagram — WF-02”).
2. Do not show source/provenance attribution inside any diagram canvas. Keep source hashes and derivation records in the repository source register and feature evidence.
3. Use project identifier `FA26SE225` from the owner-selected registration filename and course/class identifier `SWP490` from the official Review 2 guide. Label these as administrative identifiers; preserve all other blank registration fields unless an authoritative value is present.
4. Correct the duplicate `Project code` metadata label in BM02 and BM03; use `Class` for the second field.
5. Expand each of the eight BM01 demo scenarios to include preconditions and synthetic data, reproducible steps, and observable expected results.
6. Replace BM01 Appendix A3's `TBD` arithmetic with one proposed, reproducible test target. Provide a transition crosswalk for each main entity, include rejected/illegal-transition coverage, and state that this is a planned target rather than a measured suite or instructor-approved commitment.
7. Make Reports 1–5/Tracking, BM01, BM02, and BM03 consistent with SRS v3.3/B28 and current committed code/evidence. Keep implementation, design target, partial work, and unknowns distinct.
8. Fill each proposed BM02 `Planned` response with a proposed owner and proposed due date derived from current ownership/source history and dependencies. Mark each as awaiting owner/team confirmation. Include planned High findings in BM01 Known Gaps; do not claim `Fixed` or `Kept` without evidence/decision.
9. Standardize output names to `SWP490_FA26SE225_R2_<Dossier>.{docx,pdf}` within a new local `submission_r2_rev11/` directory. Preserve Rev10 outputs as historical.
10. Incorporate FEAT-060's approved CI setup and the Iteration 1 readiness results once verified. No result may overstate test evidence as deployed or end-to-end acceptance.
11. After all report source artifacts are frozen, the package passes document/diagram QA, CI and Iteration 1 gates pass, the repository is clean, and the security validator passes: create annotated tag `review-2` at the final source baseline, push the normal `dev` commit and tag, and run the official BM02 prompt against that exact tag. Keep a record of the tag SHA, exact prompt, command/environment, output/hash, and limitations. Do not move or force-update an existing tag.
12. Produce exactly four dossier categories as four DOCX/PDF pairs (eight files); render and visually inspect every final PDF page. Preserve private Registration+BM03 output, PDFs, and page renders locally under the security policy.

## Out of scope

- Product/runtime, database schema, external service, Firebase, Modal/provider, deployment, real child data, and production changes.
- Claiming full E2E, classroom acceptance, team/supervisor approval, measured pilot capacity, or owner/team confirmation of proposed BM02 responses.
- Modifying any of the five supplied original Draw.io files.
- Adding provenance/source labels inside diagrams (provenance remains in repository records).

## Acceptance criteria

- AC60: All 22 authored figures are visually reviewed at page size; each title states the diagram type; no label overlaps a label or node, and no route passes through a node or unrelated label. The single Data Request outcome-route crossing is shown with a raised bridge and a Draw.io line-jump style so it cannot read as a junction. Transition meaning is preserved.
- AC61: Editable Draw.io pages match their authored Mermaid meaning and are retained in the editable master; supplied originals remain unchanged.
- AC62: Authored canvases contain no source/provenance attribution text; provenance remains in repository records.
- AC63: Metadata uses `FA26SE225` and `SWP490`; BM02/BM03 fields are distinct (`Project code`, `Class`) and other unsupported administrative facts remain explicit unknowns.
- AC64: All eight BM01 scenarios include preconditions/data, steps, and observable expected results, using synthetic data only.
- AC65: BM01 A3 presents one numeric proposed target, a reproducible category breakdown, and a main-entity transition/negative-case crosswalk; it is not presented as measured or formally accepted.
- AC66: Each BM02 finding has an evidence-based Team Response proposal. Planned rows include a named proposed owner and due date plus a clear unconfirmed label; status totals agree with the rows. No false Fixed/Kept claim is made.
- AC67: All four dossiers agree on scope, current implementation and limitations; report language separates requirement/design from runtime evidence.
- AC68: The CI workflow and Iteration 1 results are linked to reproducible evidence; CI excludes provider/live data and does not claim FE-to-BE end-to-end acceptance.
- AC69: The tag points to the final clean, security-validated source baseline only after all required gates pass; BM02 evidence names that exact tag and commit.
- AC70: Four DOCX/PDF dossier pairs exist in Rev11; all DOCX packages parse, every PDF page is rendered and visually inspected, and output hashes/counts are recorded.
- AC71: Repository security validation passes before every commit and push. Contact-bearing Registration+BM03, PDFs, renders, external originals, credentials, and prohibited content remain outside Git.

## Work sequence

1. Record this plan and owner authorization; set FEAT-058 `IN_PROGRESS`.
2. Complete the FEAT-060 CI/Iteration 1 plan, approval, implementation and evidence before relying on those results.
3. Inventory the peer findings, current outputs, all authored diagrams, and administrative identifiers; add an evidence matrix.
4. Redraw only pages with demonstrated layout problems in editable Draw.io; render and inspect all 22 pages; update the report's diagram assets and provenance records.
5. Update all four dossier source documents, BM01 test-target crosswalk, BM02 response proposals, metadata, and filenames.
6. Build the four DOCX outputs and local PDFs in a new Rev11 folder; run structural checks and page-by-page visual QA; fix any defects.
7. Run the repository security validator, commit/push the reviewed source, and wait for the authorized CI gate. Keep the tree clean.
8. Create/push the annotated `review-2` tag at the exact passing commit, then run the official BM02 prompt against that tag and record evidence.
9. Regenerate the local BM02 dossier with the tagged run evidence; inspect it again; update the evidence index, source register, decisions, and status. Preserve the final eight output files locally and report paths/hashes.

## Dependencies and decision boundaries

- Peer recommendations that contradict the current guide or repository must be marked as incorrect/partially resolved, with evidence.
- Proposed team response owners use the latest recorded FE/BE/BE/technical-integration roles and observed commit/file ownership as recommendations only. The owner will confirm through the report.
- Proposed due dates are planning recommendations only; no approved calendar or team availability is inferred.
- `review-2` may be created only after final CI, Iteration 1, document QA, clean-tree and repository-security gates pass. If a gate fails, no tag is created; report the blocker and continue remediation within the approved scope.
- The Review 2 guide requires the BM02 standard prompt to run against the `review-2` tag. A prior draft is not a substitute.
