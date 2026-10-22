# Mermaid source review — 2026-10-22

## Authority and approval

- Owner: Khoa. Direct request: create Mermaid equivalents from the current Draw.io and carefully review all three assigned diagrams.
- Plan: FEAT-048 plan revision 8; explicit scope approval is recorded as revision 9 in `approvals/TASK_APPROVAL.md`.
- Canonical requirement source: `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md`, source-register ID `collaborative-srs-v3-20261010`; relevant sections B5, B7/B7.1, B8, B21, and B21.5.
- Repository architecture rules: interfaces/adapters -> application -> domain; infrastructure implements inward ports; cross-feature behavior uses versioned contracts.

## Source files

- `src/diagrams/logical-erd.mmd`
- `src/diagrams/system-overview.mmd`
- `src/diagrams/package-diagram.mmd`
- `src/diagrams/README.md`

The existing Draw.io document remains the editable visual companion. The Mermaid files are repository source counterparts; no SQL script, runtime/schema change, or SRS edit was made.

## Review results

### Logical ERD

- The source has 17 entities: the 16 entities in B7.1 plus `OrganizationScope`.
- It has 22 relationship lines: the exact 16 B7.1 relationships and labels, plus six selected B21.5 references (OrganizationScope–Class, StudentProfile–ChildParticipant, shared/personal CanvasDocument ownership, optional contributor attribution, and TeacherReview reviewer reference).
- A one-off structural comparison found all 16 B7.1 endpoint/name pairs, no missing endpoints, and no unknown entity references. Both Enrollment relationship labels visibly say `cardinality TBD` while preserving the B7.1 names.
- PK/FK/reference fields are included as a logical mapping aid. The schema remains proposed; this does not assert a physical migration.
- Caveats are recorded in source comments and `src/diagrams/README.md`: Enrollment cardinality remains TBD; `membershipId` is a proposed episode key; shared-group and personal-participant canvas ownership are mutually exclusive; purposes are multi-valued with storage normalization TBD; TeacherReview has generic targets under DATA-24.

### System Overview / Architecture

- Confirms the Android/React Native TypeScript client and FastAPI/Python backend; Teacher and Super Admin surfaces remain confirmed with their frontend frameworks marked TBD.
- Includes all nine proposed B8 contexts, Application use cases, outbound ports, and separate candidate infrastructure adapters.
- Makes principal requests and data paths explicit: client requests/responses, validated backend requests, domain operations, persistence/artifact access, bounded async jobs/results, adult identity checks, AI jobs/results, and proposed realtime events.
- External providers and infrastructure use capability-level names only. Vendor choices and exact transmitted payloads remain TBD; the AI provider is backend-only and the mobile client has no provider credentials/endpoints.
- Request/data-flow edges are distinguished in labels from dashed port-implementation and proposed realtime edges.

### Package Diagram

- Uses five package namespaces: presentation, inbound adapters, application, domain, and proposed infrastructure adapters.
- Contains all nine proposed B8 domain contexts, six application-owned outbound ports, and six infrastructure adapter realizations.
- Client-to-backend edges are labeled as runtime protocols. Backend dependencies point inward from inbound adapters to use cases to domain; use cases use ports; infrastructure realizes ports. No direct use-case-to-infrastructure dependency is present.
- Versioned contracts remain the cross-feature boundary.

## Verification and limitations

- Static source comparison: 17 ERD entities; 22 relationships; 16/16 B7.1 relationships exact; zero unresolved ERD endpoints; 9/9 B8 contexts; 6/6 adapter-to-port realizations; no direct application-to-infrastructure package edge.
- Reviewed Mermaid ERD attribute key/comment/cardinality syntax and class-diagram namespace/realization syntax against the [official Mermaid ERD reference](https://mermaid.js.org/syntax/entityRelationshipDiagram.html) and [class-diagram reference](https://mermaid.js.org/syntax/classDiagram.html).
- No Mermaid CLI or PlantUML renderer is installed in the worktree. The source has not been rendered, so no visual or renderer-level pass is claimed.
- `python tools/validate_harness.py --feature features/FEAT-048-srs-diagram-pack` still returns `HARNESS_INVALID` because FEAT-045, FEAT-046, and FEAT-047 lack required `evidence/screenshots` and `evidence/metrics` paths. FEAT-048's required evidence paths were added and are no longer reported missing; other feature folders were left unchanged.
- No state-machine or activity/flowchart source was added because Khoa's current assignment remains ERD, System Architecture, and Package Diagram.
- This revision is local to FEAT-048. The Draw.io Drive file was not changed, and the branch was not committed or pushed.
