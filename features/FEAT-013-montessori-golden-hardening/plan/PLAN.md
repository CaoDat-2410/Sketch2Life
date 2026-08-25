# FEAT-013 Montessori Golden Catalog hardening plan

- Status: AWAITING_APPROVAL
- Plan revision: 1
- Implementation status: NOT_STARTED
- Owner: Person 1
- Prepared at: 2026-08-25
- Branch: `plan/person-1-montessori-golden-hardening`

Implementation remains blocked until revision 1 is explicitly approved in `approvals/TASK_APPROVAL.md`.

## Goal

Create a deeply curated, independently testable 20-activity golden subset suitable for capstone integration fixtures while preserving the 100-activity FEAT-002 catalog as the immutable baseline and keeping all output provisional/non-production.

## Golden selection

Five records per age band are proposed to cover home feasibility, safety, objective diversity, progression, and demo usefulness:

| Band | Proposed base activities |
|---|---|
| 0-3 | `ACT-0004`, `ACT-0016`, `ACT-0019`, `ACT-0020`, `ACT-0023` |
| 3-6 | `ACT-0026`, `ACT-0030`, `ACT-0033`, `ACT-0039`, `ACT-0046` |
| 6-9 | `ACT-0055`, `ACT-0058`, `ACT-0061`, `ACT-0067`, `ACT-0074` |
| 9-12 | `ACT-0085`, `ACT-0087`, `ACT-0091`, `ACT-0097`, `ACT-0099` |

Changing this selection after approval requires revision 2 because fixtures, review workload, and evidence coverage change materially.

## In scope

- Golden Activity v2 schema and complete record field dictionary.
- Selection manifest linking each golden candidate to FEAT-002 base ID/version/checksum.
- 20 full candidate-version-2 activity records with specific `vi-VN` content.
- Narrower age guidance and activity-specific observable readiness criteria.
- Concrete material registry, household substitutes, suitability constraints, and availability groups.
- Activity-specific environment/setup, ordered presentation, child work cycle, restoration, control-of-error, and completion observation.
- Activity-specific hazards, supervision, stop conditions, and prohibited substitutions.
- Primary/secondary objective mappings and prerequisite/progression edges.
- Support/standard/extension variants that preserve activity/objective identity and never bypass hard constraints.
- Deterministic hardening validator and at least 60 golden fixtures.
- Owner review packet, traceability, reproducibility, security, and limitations evidence.

## Explicitly out of scope

- New image/drawing ontology, multimodal understanding, AI/model calls, or observation-to-objective mapping.
- Recommendation retrieval/ranking/scoring or changing hard-rule precedence.
- Gate B UI/API/state, Android, backend, auth, DB, S3, queue, deployment, or E2E.
- Expanding the catalog above 100 records.
- Real child data, classroom observations, medical/accessibility diagnoses, or psychological/personality inference.
- Qualified Montessori or production approval.
- Silent mutation or replacement of FEAT-002 v1 artifacts.

## Planned output locations

```text
packages/domain-montessori/
  schemas/golden-activity.v2.schema.json
  schemas/golden-fixture-case.v1.schema.json
  spec/GOLDEN_ACTIVITY_FIELD_GUIDE.md
  spec/GOLDEN_REVIEW_RULES.md

data/activity-catalog/golden/v1/
  selection-manifest.v1.json
  activities.v2.json
  material-registry.v1.json
  progression-edges.v1.json
  provenance.v1.json

tests/fixtures/montessori-golden/
  cases/
  manifest.v1.json

tools/validate_montessori_golden.py

features/FEAT-013-montessori-golden-hardening/
  src/                      deterministic builders after approval
  evidence/                 feature-local raw/metrics/notes
```

These are planned paths and do not exist merely because the plan lists them.

## Record hardening requirements

Every candidate v2 record must include:

- immutable base ID/version/checksum and candidate version;
- localized title, concise purpose, direct aim, and indirect aims;
- narrower inclusive age-month guidance with an explanation of boundaries;
- observable readiness criteria and non-readiness examples;
- prerequisite activities/skills and progression successors;
- prepared-environment and setup requirements;
- concrete primary materials and concrete substitutes with allowed/prohibited conditions;
- adult presentation steps, child independent-work steps, and restoration steps;
- isolation of difficulty and control of error;
- activity-specific duration range and repeatability guidance;
- supervision level, hazards, stop conditions, allergy/choking/tool/heat/water constraints when applicable;
- primary objective plus optional secondary objectives;
- support/standard/extension variants that keep identity locked;
- non-evaluative completion observations;
- source references, author/reviewer state, and production eligibility.

## Acceptance criteria

- `AC-G1-01`: Exactly 20 golden records exist, five per approved age band, and every record references an existing FEAT-002 base ID/version/checksum.
- `AC-G1-02`: FEAT-002 v1 file hashes remain unchanged throughout implementation; derived golden artifacts never overwrite baseline files.
- `AC-G1-03`: Every golden record passes the v2 schema and contains all hardening fields with activity-specific content; duplicate generic step/safety blocks fail quality validation.
- `AC-G1-04`: Every readiness criterion is observable, non-diagnostic, and specific enough for a deterministic fixture input.
- `AC-G1-05`: Every material group contains concrete primary/substitute records, suitability constraints, and at least one prohibited-substitution or safety rule where relevant; placeholder-only substitutes fail.
- `AC-G1-06`: Age, prerequisite, readiness, supervision, policy, material, and active-status hard rules remain mandatory and precede any future ranking.
- `AC-G1-07`: Every record has one primary objective, at most two secondary objectives, valid versions, and traceable prerequisite/progression edges without cycles.
- `AC-G1-08`: Support/standard/extension variants cannot change locked activity/objective identity or weaken a hard rule.
- `AC-G1-09`: At least 60 deterministic fixtures exist: primary-material valid, substitute valid, and blocked/no-result coverage for each golden record, plus boundary/multiple-failure cases.
- `AC-G1-10`: The standalone validator runs without network, database, AI, mobile, or another person's output; mismatch and baseline mutation return non-zero.
- `AC-G1-11`: Owner review may set `PROVISIONAL_OWNER_REVIEWED` only; every record remains `production_eligible=false` until qualified review.
- `AC-G1-12`: Evidence maps each golden record and requirement to source, review decision, fixture IDs, commands, metrics, interpretation, and limitations.
- `AC-G1-13`: No real child data, credentials, accounts, external provider payloads, or machine-local paths enter publishable artifacts.

## Task plan and estimate

| ID | Task | Deliverable | Estimate |
|---|---|---|---:|
| G1-01 | Freeze baseline hashes and selection | Selection manifest and immutable-baseline evidence | 2 h / 0.5 SP |
| G1-02 | Define Golden Activity v2 contract | Schema, field guide, valid/invalid examples | 4 h / 1 SP |
| G1-03 | Define materials/readiness/progression semantics | Registries and review rules | 4 h / 1 SP |
| G1-04 | Harden five 0-3 activities | Full v2 records and review sheet | 8-12 h / 2-3 SP |
| G1-05 | Harden five 3-6 activities | Full v2 records and review sheet | 8-12 h / 2-3 SP |
| G1-06 | Harden five 6-9 activities | Full v2 records and review sheet | 8-12 h / 2-3 SP |
| G1-07 | Harden five 9-12 activities | Full v2 records and review sheet | 8-12 h / 2-3 SP |
| G1-08 | Build validator and 60+ fixtures | Offline harness, coverage, mutation tests | 8-10 h / 2-2.5 SP |
| G1-09 | Build owner review and traceability packet | CSV/Markdown review, metrics, requirement matrix | 3 h / 0.75 SP |
| G1-10 | Final architecture/security/reproducibility review | Logs, limitations, handoff | 2 h / 0.5 SP |
| Total | Independent hardening workstream | 10 tasks | 55-73 h / 13.75-17.75 SP |

At a 40-hour capstone sprint allocation, this is approximately 1.5-2 Person 1 sprints. Reducing the set below 20 or weakening fixture depth requires a new revision rather than silently lowering quality.

## Verification strategy

- Baseline SHA-256 freeze and mutation detection.
- JSON/contract completeness, enum, reference, uniqueness, and version checks.
- Duplicate/generic-content heuristics for steps, safety, readiness, and substitute guidance.
- Material registry and prohibited-substitution integrity checks.
- Progression graph reference/cycle scan.
- Per-record primary/substitute/blocked fixture replay with explicit reason codes.
- Age/readiness boundary, multiple-failure, no-valid, and variant identity-lock fixtures.
- Deterministic rebuild and deliberate expected-output/baseline mutation tests.
- Repository harness, architecture, team-allocation, and security validators.

## Risks and mitigations

- False precision in age windows: document them as provisional guidance and keep readiness/safety authoritative.
- Generic generated wording: fail repeated template blocks and require record-level owner review.
- Unsafe household substitutes: model suitability/prohibited constraints explicitly; qualified review remains required.
- Scope pressure: hold at 20 deep records and do not expand count.
- Hidden dependency: use only local FEAT-002 artifacts and standalone fixtures.
- Baseline corruption: freeze hashes and write only versioned derived artifacts.
- Production overclaim: preserve provisional status and `production_eligible=false` in schema, validator, and evidence.

## Definition of Done

- G1-01 through G1-10 meet all acceptance criteria and phase gates.
- Exactly 20 full golden records and at least 60 deterministic fixtures pass.
- FEAT-002 baseline hashes are unchanged.
- Owner provisional review and all evidence are recorded.
- Standalone harness, architecture, team-allocation, and security checks pass.
- Completion does not authorize recommendation runtime, integration, or production use.

## Approval rule

Only revision 1 may be implementation-approved. Selection, record count, fixture minimum, data policy, review authority, estimate, or architecture changes require revision 2 and invalidate prior approval.
