# Person 1 detailed task breakdown

- Plan revision: 4
- Total: 12 tasks, 72-112 estimated hours, 18-28 story points
- Cross-person runtime dependency: none
- Status of every task: `BLOCKED_BY_TASK_APPROVAL`

| ID | Task | Deliverable | Estimate | Acceptance/evidence summary |
|---|---|---|---:|---|
| P1-01 | Establish domain artifact structure and conventions | Package/data/fixture layout plus naming README | 2 h / 0.5 SP | Paths and ownership rules documented; no runtime dependency |
| P1-02 | Define glossary and ID/version rules | Entity glossary and versioning examples | 2 h / 0.5 SP | Activity, Concept, LearningObjective, Prerequisite, SafetyRule, MaterialOption, TaskVariant covered |
| P1-03 | Define canonical Activity schema | Versioned JSON Schema, field dictionary, two examples | 4 h / 1.0 SP | Required/optional/type/meaning/constraint/review fields pass schema review |
| P1-04 | Define Learning Objective taxonomy | 15-20 objectives and mapping table | 3 h / 0.75 SP | Stable IDs, areas, descriptions, mappings, versions |
| P1-05 | Curate provisional MVP activity catalog | 100 required activities; up to 100 stretch, capped at 200 | 40-80 h / 10-20 SP | >=25 complete records per age band, objective mapping, provenance, owner-review state; no missing required field |
| P1-06 | Define deterministic hard-rule matrix | Rule definitions, precedence, reason-code registry, examples | 4 h / 1.0 SP | Active/age/readiness/prerequisite/safety/material/policy rules have explicit pass/fail behavior |
| P1-07 | Establish harness contract and runner | Fixture schemas, manifest, comparator, README | 3 h / 0.75 SP | Loads a case, validates references, compares allowed/blocked/reasons, fails on mismatch |
| P1-08 | Create positive fixture cases | 8-10 valid/multiple-valid input/expected pairs | 3 h / 0.75 SP | Deterministic candidate expectations and explanations |
| P1-09 | Create blocked/no-result cases | 10-12 negative/no-result input/expected pairs | 3 h / 0.75 SP | Every hard-rule category, multiple failure, and explicit no-result covered |
| P1-10 | Specify Gate B acceptance criteria | Given/When/Then review pack | 3 h / 0.75 SP | Approve/alternative/reject/stale/identity-lock behavior specified, not implemented |
| P1-11 | Specify ActivityHandoff/Activity Card | Versioned template and one example | 2 h / 0.5 SP | CTA, materials/substitutes, setup, steps, safety, screen exit, completion evidence |
| P1-12 | Build traceability and review pack | Requirement-field-fixture-criterion matrix and checklist | 3 h / 0.75 SP | Every core requirement maps to an artifact and review/test evidence |

## Task sequencing inside Person 1

```text
P1-01 -> P1-02 -> P1-03 -> P1-04
                    |         |
                    +----+----+
                         v
                  P1-05 -> P1-06
                              |
                              v
                  P1-07 -> P1-08 + P1-09
                              |
                              v
                  P1-10 -> P1-11 -> P1-12
```

This is an internal sequence for one owner. It does not create dependencies on Person 2, Person 3, or Person 4.

## Catalog batch structure

| Batch | Age band | Required | Stretch ceiling | Review constraint |
|---|---|---:|---:|---|
| CAT-01 | 0-3 | 25 | 50 | Caregiver-led only; developmental/readiness and supervision fields mandatory |
| CAT-02 | 3-6 | 25 | 50 | Primary/Children's House classification |
| CAT-03 | 6-9 | 25 | 50 | Lower Elementary classification |
| CAT-04 | 9-12 | 25 | 50 | Upper Elementary classification |
| Total | 0-12 | 100 | 200 | Owner review remains provisional/non-production |

The four equal minimums are a planning distribution to guarantee coverage, not a claim that every age band naturally contains the same pedagogical breadth. Distribution may change only through a new approved plan revision while preserving a minimum total of 100 and explicit age-band coverage.

## Estimate impact

Revision 3 used the workbook estimate of 8 hours / 2 SP for 20 activities. Applying the same rate to 100-200 activities yields 40-80 hours / 10-20 SP for P1-05 alone. All other tasks remain 32 hours / 8 SP, so revision 4 totals 72-112 hours / 18-28 SP.
