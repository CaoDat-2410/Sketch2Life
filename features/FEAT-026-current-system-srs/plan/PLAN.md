# Current system SRS document plan

- Status: APPROVED
- Plan revision: 1
- Implementation status: PLANNED

## Goal

Produce an editable Vietnamese Word SRS form for Sketch2Life that can be used by the project team as a baseline requirements document and review form.

## Planned scope

1. Distill the current product purpose, actor model, invariants, architecture, and repository boundaries.
2. Separate requirements by maturity: implemented boundary, offline/fixture-only, accepted architecture, planned, and open/blocked.
3. Include a system topology diagram, end-to-end flow, session state machine, and qualitative maturity chart.
4. Add functional requirements, non-functional requirements, data/provenance rules, security constraints, contract expectations, acceptance criteria, traceability, and sign-off fields.
5. Render the DOCX to page PNGs, inspect every page, fix layout issues, and record evidence under this feature.

## Acceptance criteria

- [ ] Output is an editable `.docx` file in the feature artifacts folder.
- [ ] The document identifies Sketch2Life and its current maturity without presenting fixture work as production readiness.
- [ ] The document includes at least one status chart, one architecture/topology diagram, one end-to-end flow, and one state transition diagram.
- [ ] Functional and non-functional requirements are traceable to current repository sources or explicitly marked as planned/open.
- [ ] Security rules include Firebase Authentication-only, backend-owned storage, no provider credentials/endpoints in mobile, synthetic-only development data, and provenance/retention expectations.
- [ ] The form includes review/sign-off fields and an acceptance checklist.
- [ ] Rendered page images exist in feature-local evidence and every page has been visually inspected.
- [ ] No secrets, real child data, raw external handbook/workbook content, or untraceable evidence dump is included.
