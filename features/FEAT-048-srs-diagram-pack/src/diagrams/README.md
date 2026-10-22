# FEAT-048 diagram sources

These Mermaid files are the repository source counterparts for the assigned Draw.io diagrams and their approved architecture comparison page:

- `logical-erd.mmd` — proposed logical ERD, based on SRS v3.1 B7.1 and selected B21.5 references.
- `system-overview.mmd` — overall components, external boundaries, and principal request/data flows grounded in B8.
- `system-architecture-v2.mmd` — detailed, vendor-neutral architecture comparison page; uses the SRS-named infrastructure candidates and explicit CONFIRMED/CANDIDATE/PROPOSED/TBD states.
- `package-diagram.mmd` — package namespaces and dependency direction; runtime protocol links are labeled separately.

The `.drawio` file remains the editable visual companion. Page 4 is an alternate `System Architecture v2` view; it does not replace the original page 2. Keep Mermaid sources and Draw.io pages semantically aligned when either changes. The shape, status, and connector conventions are documented in `../ARCHITECTURE_DRAWING_RULES.md`. No SQL script or physical schema migration is part of this diagram deliverable.

Provider names and exact payloads are still unresolved in the SRS. The overview therefore uses capability names and `TBD`/`candidate` labels; Report 4 must declare each selected third-party service, its purpose, and data transmitted once those choices are settled.

ERD review notes to keep with its rendered report figure: Enrollment cardinality is unresolved; `membershipId` is a proposed episode key; a CanvasDocument has either a shared-group owner or a personal-participant owner; consent purposes are multi-valued and their physical normalization is unresolved; TeacherReview can target more than SketchProposal.

State-machine and activity/flowchart diagrams are part of the overall report guidance in the supplied excerpt, but they are outside Khoa's currently assigned three-diagram scope unless the team changes the allocation.
