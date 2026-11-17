# Academic report Markdown plan

- Status: DONE
- Plan revision: 2
- Implementation status: COMPLETE

## Goal

Produce three detailed, ready-to-review Vietnamese Markdown artifacts aligned with the supplied academic report forms while remaining truthful to the current Sketch2Life repository and harness. Revision 2 adds report-grade diagrams, stakeholder/requirement detail, traceability, quality gates, change control, and a more complete WBS/schedule view.

## Scope

1. `artifacts/Report1_Project_Introduction.md`: project information, background, existing systems, business opportunity, product vision, scope, features, limitations, and change log.
2. `artifacts/Report2_Project_Management_Plan.md`: scope/estimation, objectives and metrics, risks, management approach, quality, training, deliverables, responsibilities, communications, and configuration management.
3. `artifacts/Report2_Sample_Project_Schedule.md`: an adapted schedule with relative weeks, dependencies, resources, milestones, Sprint 1 independence, and a separately approved Integration Sprint.
4. Mermaid diagrams embedded in the reports and reusable diagram source files under `artifacts/diagrams/`.

## Acceptance criteria

- [x] All three artifacts preserve the intent and major sections of the supplied report templates.
- [x] Placeholder instructions and stale sample values are not presented as Sketch2Life facts.
- [x] The artifacts use the current product objective, SRS v1.6 target scope, accepted architecture, four-person Sprint 1 allocation, and repository security rules.
- [x] The artifacts distinguish target behavior from current implementation, fixture-only evidence, open decisions, and out-of-scope work.
- [x] Report 2 includes a traceable 240 person-day planning estimate, risks, responsibilities, quality gates, deliverables, and communication/configuration practices.
- [x] The schedule uses relative weeks and does not invent an approved calendar start date; it includes predecessor IDs and resource roles.
- [x] No credentials, real child data, external handbook/workbook originals, or private contact details are copied into the artifacts.
- [x] Feature-local evidence records the source boundary, generation inputs, verification commands, and limitations.
- [x] Each report contains diagrams with captions, purpose, and traceable source context.
- [x] Report 1 includes stakeholder model, problem-to-solution traceability, target journey, system context, trust boundaries, and measurable success criteria.
- [x] Report 2 includes WBS/effort rationale, quality-gate workflow, change-control flow, decision/escalation model, resource-loading view, and expanded responsibility/communication detail.
- [x] The schedule includes a diagrammatic dependency view, stage gates, workstream lanes, and a detailed relative-week baseline.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Academic template wording is mistaken for repository authority | Record the source boundary and follow direct owner request, approved decisions, current evidence, then references. |
| Target SRS is mistaken for completed implementation | Label maturity/status in each report and cite the current-system baseline. |
| The schedule appears to be a committed calendar plan | Use relative weeks, mark it as a planning baseline, and require separate approval for Integration Sprint allocation. |
| Missing academic names or contact details are invented | Use role labels and `TBD` only where an owner must fill a field. |

## Verification plan

1. Review the three artifacts for section coverage, internal consistency, and source/status labels.
2. Search the feature artifacts for forbidden secrets and stale sample values.
3. Run repository harness, architecture, and security validators after writing the artifacts.
4. Record outputs and limitations in feature-local evidence.

## Evidence plan

- `evidence/README.md`: evidence index.
- `evidence/notes/SOURCE_BOUNDARY.md`: distinction between user request, attached-template instructions, sample schedule content, and repository/SRS authority.
- `evidence/notes/GENERATION_RECORD.md`: inputs, output paths, assumptions, timestamp, and interpretation.
- `status/STATUS.md`: final completion status and verification summary.

Implementation is authorized by `approvals/TASK_APPROVAL.md` for plan revision 2 only.
