# FEAT-002 requirement traceability

| Requirement | Domain artifact | Verification/evidence |
|---|---|---|
| Stable activity/objective identity and version | `activity.v1.schema.json`, `learning-objective.v1.schema.json`, `ID_VERSION_RULES.md` | Catalog validator duplicate/reference/version checks |
| Under-13 coverage | `age_band`, inclusive `age_months` | 25 activities each for 0-3, 3-6, 6-9, 9-12 |
| 0-3 caregiver-led safety | `DIRECT` supervision + `CAREGIVER_PRESENT` policy | Positive and blocked caregiver fixture cases |
| 100-200 catalog target | `activities.v1.json` | 100 baseline records; stretch not required for minimum gate |
| `vi-VN` content and stable machine IDs | localized title/steps/safety plus ASCII IDs/enums | Validator title/pattern checks and review CSV |
| Provisional owner review | activity `review` object and provenance ledger | All records remain `PENDING_OWNER_REVIEW`, production false |
| Hard constraints before ranking | `hard-rules.v1.json`, `RULE_SEMANTICS.md` | 24 deterministic fixture cases; no ranking code exists |
| No silent rule relaxation | `NO_VALID_ACTIVITY` result | No-valid and multiple-failure fixtures |
| Materials and substitutes | required material groups with `any_of` options | Primary/substitute positive cases and material-block cases |
| Gate B identity lock | `GATE_B_ACCEPTANCE.md` | Acceptance review note |
| Off-screen physical endpoint | `ACTIVITY_HANDOFF.md`, handoff schema | Contract review note |
| No cross-person dependency | standalone Python validator | `network_required=false` and architecture review |
| No real child data or credentials | synthetic fixtures only | repository security validator |

Machine-readable traceability is stored in `features/FEAT-002-montessori-domain/evidence/metrics/traceability.json`.
