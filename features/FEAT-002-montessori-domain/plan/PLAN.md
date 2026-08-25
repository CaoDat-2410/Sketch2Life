# FEAT-002 Montessori domain plan

- Status: AWAITING_APPROVAL
- Plan revision: 3
- Implementation status: NOT_STARTED
- Owner: Person 1
- Prepared at: 2026-08-25
- Branch: `plan/person-1-montessori-sprint-1`

Implementation is blocked until the owner approves this exact revision and resolves the decisions in `APPROVAL_PACKET.md`.

## Goal

Produce an independently reviewable BA/Montessori package that makes later recommendation and Gate B implementation testable without implementing either runtime in Sprint 1.

## In scope

- Canonical glossary and ID/version conventions.
- Activity, Concept, LearningObjective, Prerequisite, SafetyRule, MaterialOption, and TaskVariant specifications.
- A reviewed MVP activity catalog: 20 required activities; activities 21-30 are stretch only.
- An initial Learning Objective taxonomy: 15-20 objectives.
- Deterministic age/readiness, prerequisite, safety, material, active-status, and policy rule matrix.
- At least 20 fixture cases with explicit expected allowed/blocked IDs and reason codes.
- A standalone data-driven validation harness.
- Gate B and ActivityHandoff acceptance specifications.
- Requirements-to-artifact-to-fixture traceability and review checklist.

## Explicitly out of scope

- Recommendation retrieval, ranking, scoring, model selection, or runtime API.
- Gate B screen, API, persistence, authorization, or state transitions.
- Android, Firebase, database, object storage, queue, worker, deployment, or E2E wiring.
- Real child data, production seed data, psychological/personality inference, or unreviewed activity promotion.
- Any rule that silently relaxes safety/prerequisite constraints to force a recommendation.

## Planned output locations

```text
packages/domain-montessori/
  spec/                         glossary, entities, IDs/versions, rule semantics
  schemas/                      versioned JSON Schemas
  README.md                     standalone review/run guide

data/activity-catalog/mvp/
  activities.v1.json            reviewed fixture catalog
  learning-objectives.v1.json   initial taxonomy
  provenance.v1.json            source/reviewer/status ledger

tests/fixtures/montessori/
  inputs/                       canonical-understanding/readiness/material fixtures
  expected/                     allowed/blocked/no-result decisions
  manifest.v1.json              fixture IDs, versions, checksums, coverage tags

tools/validate_montessori_domain.py
                                standalone deterministic schema/rule fixture harness

features/FEAT-002-montessori-domain/evidence/
                                feature-local reports, logs, reviews, and metrics
```

These paths are proposed by this plan and do not exist merely because they are listed here.

## Phase plan

| Phase | Scope | Tasks | Estimate | Entry gate | Exit gate |
|---|---|---|---:|---|---|
| Phase 0 - Approval and fixture freeze | Resolve owner decisions; freeze source IDs and local input fixture shapes | Planning only | 0 h | Plan ready | Revision 3 approved and approval file complete |
| Phase 1 - Domain foundation | Folder conventions, glossary, ID/version rules, Activity schema, objective taxonomy | P1-01..P1-04 | 11 h / 2.75 SP | Phase 0 approved | Schema examples and taxonomy review pass |
| Phase 2 - Catalog and hard rules | Curate catalog and rule matrix with provenance/review state | P1-05..P1-06 | 12 h / 3.0 SP | Phase 1 contracts frozen | >=20 complete activities; hard-rule review pass |
| Phase 3 - Standalone harness | Harness shape, positive cases, blocked/no-result cases | P1-07..P1-09 | 9 h / 2.25 SP | Phase 2 catalog/rules versioned | All fixtures deterministic; coverage and repeatability pass |
| Phase 4 - Acceptance and handoff | Gate B criteria, ActivityHandoff template, traceability/review pack | P1-10..P1-12 | 8 h / 2.0 SP | Phase 3 results available | Traceability complete; owner/domain review ready |
| Total | 12 tasks | P1-01..P1-12 | 40 h / 10 SP | - | Definition of Done satisfied |

Detailed task-level scope is in `TASK_BREAKDOWN.md`; phase transitions and evidence gates are in `PHASES.md`.

## Acceptance criteria

- `AC-P1-01`: Every canonical entity has a definition, stable ID rule, version semantics, and at least one valid example.
- `AC-P1-02`: Activity schema documents required/optional fields, types, meaning, constraints, and review status.
- `AC-P1-03`: Objective taxonomy contains 15-20 versioned objectives mapped to Montessori areas with examples.
- `AC-P1-04`: At least 20 activities pass schema completeness; every record includes objective mapping, age/readiness, steps, materials/substitutes, duration, safety/supervision, status, source provenance, and reviewer state.
- `AC-P1-05`: Every hard rule has a machine-readable reason code, inputs, pass/fail semantics, precedence, and positive/negative examples.
- `AC-P1-06`: A candidate violating any hard rule is absent from allowed results; the harness reports all applicable block reasons.
- `AC-P1-07`: At least 8 positive/multiple-valid and 10 negative/no-result cases exist; total fixture count is at least 20.
- `AC-P1-08`: Fixtures cover inactive, age/readiness, prerequisite, safety, material, multiple-failure, valid, multiple-valid, and no-valid scenarios.
- `AC-P1-09`: The standalone harness runs without network, database, AI, mobile, or another person's output and returns a non-zero exit code on mismatch.
- `AC-P1-10`: `NO_VALID_ACTIVITY` is a valid deterministic result; no rule is relaxed to manufacture a candidate.
- `AC-P1-11`: Gate B criteria cover approve, valid alternative, reject, stale version, and simultaneous activity/objective identity lock.
- `AC-P1-12`: ActivityHandoff specifies locked identities, CTA, materials/substitutes, setup, ordered physical steps, safety/supervision, screen-exit policy, and completion evidence.
- `AC-P1-13`: Traceability maps every approved requirement to a domain field/spec and at least one review or fixture case.
- `AC-P1-14`: No real child data, credentials, seed accounts, runtime recommendation logic, or integration dependency is introduced.

## Verification strategy

- JSON/JSON Schema validation for catalog, taxonomy, rule matrix, and fixture manifests.
- Deterministic fixture replay with stable sorted outputs and explicit reason codes.
- Coverage report by rule category and expected-result class.
- Duplicate ID/version, broken reference, missing provenance, and unreviewed-status checks.
- Manual BA/domain review of glossary, catalog accuracy, Gate B criteria, and ActivityHandoff.
- Repository harness, architecture, team-allocation, and security validators.

## Evidence strategy

Every completed task records an evidence ID, acceptance criterion, exact command/input, environment, output path, timestamp, reviewer, interpretation, and limitation. Planned evidence is indexed in `evidence/EVIDENCE_PLAN.md`.

## Definition of Done

- All 12 tasks meet their acceptance criteria and phase gates.
- Required catalog target, taxonomy target, and fixture coverage pass.
- Standalone harness is reproducible from README instructions.
- Source/reviewer provenance is present; activities not reviewed remain `DRAFT` and cannot be represented as approved.
- Architecture and repository-security validators pass.
- Evidence index contains no `PENDING` required item.
- Owner records final review; completion does not authorize Integration Sprint runtime work.

## Risks and mitigations

- Pedagogical validity: require named Montessori reviewer and per-record review status; do not equate schema validity with pedagogical approval.
- Scope expansion: keep 20 activities as required; treat 21-30 as stretch.
- Ambiguous age/readiness: freeze owner-selected range/bands before catalog work.
- Rule overreach: document deterministic eligibility only; defer ranking/weights/runtime recommendation.
- Fixture bias: include boundary, multiple-failure, and no-result cases and record known gaps.
- Translation drift: use stable machine IDs and an approved locale policy; do not encode business identity in display text.
- Reference authority confusion: cite handbook/workbook as sources while direct owner approval controls execution.

## Approval rule

Only revision 3 may be approved. Any material change to scope, catalog target, age/readiness range, locale, reviewer gate, or acceptance criteria increments the revision and invalidates approval.
