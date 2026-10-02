# Academic report Markdown decisions

- 2026-09-27: Create a new feature record because the request produces three academic report artifacts and is separate from the already-completed current-system inventory (FEAT-019) and master SRS (FEAT-029).
- 2026-09-27: Use the supplied DOCX files as section/template references only. Placeholder prose, stale sample project names, old team names, old technology choices, and sample dates do not become Sketch2Life requirements.
- 2026-09-27: Use the supplied PDF only for schedule column conventions, hierarchy, dependencies, milestones, and stage presentation. The generated schedule uses relative weeks because no approved project start date exists in current context.
- 2026-09-27: Use the owner-approved master SRS v1.6 and current-system documentation for Sketch2Life scope, roles, architecture, quality gates, security, and target-vs-current status.
- 2026-09-27: Use P1-P4 role labels instead of inventing personal names or contact details. Academic supervisor/contact fields remain explicitly TBD where the repository has no authoritative value.
- 2026-09-27: Treat the 240 person-day estimate and 15-week schedule as a planning baseline, not evidence of completed work, production capacity, or an approved delivery commitment.
- 2026-09-27: Revision 2 adds Mermaid diagrams directly inside the Markdown reports and stores reusable Mermaid sources under `artifacts/diagrams/`; diagrams are explanatory documentation, not runtime architecture authorization.
- 2026-09-27: Expand the reports with academic-report detail while preserving the target/current distinction, relative schedule assumption, P1-P4 independence, and explicit `OPEN_TBD` decisions.
