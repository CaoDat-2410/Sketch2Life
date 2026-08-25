# Person 1 phase gates

## Status model

```text
PLANNED
  -> AWAITING_TASK_APPROVAL
  -> APPROVED
  -> PHASE_1_DOMAIN_FOUNDATION
  -> PHASE_2_CATALOG_RULES
  -> PHASE_3_HARNESS_FIXTURES
  -> PHASE_4_ACCEPTANCE_TRACEABILITY
  -> REVIEW
  -> DONE
```

Current state: `AWAITING_TASK_APPROVAL`.

## Phase 0 - approval and input freeze

Entry: plan revision 4 prepared.

Required exit evidence:

- owner approval recorded against revision 4;
- under-13 scope recorded as 0-3, 3-6, 6-9, and 9-12;
- English machine IDs/schema keys plus `vi-VN` reviewer-facing content recorded;
- owner-only provisional review and non-production status recorded;
- 100-required/+100-stretch catalog target and 72-112 hour estimate acknowledged;
- fixed fixture/source register IDs recorded.

No implementation command may run before this gate closes.

## Phase 1 - domain foundation

Tasks: P1-01 through P1-04.

Exit evidence:

- artifact tree review;
- glossary/ID/version review;
- schema validation report for two examples;
- taxonomy count and broken-reference scan;
- reviewer comments and unresolved issues.

Material schema changes after exit require a version increment and downstream fixture review.

## Phase 2 - catalog and hard rules

Tasks: P1-05 and P1-06.

Exit evidence:

- catalog completeness and unique ID/version report;
- age-band coverage report with at least 25 required records per band;
- source/reviewer/status ledger;
- objective/reference integrity report;
- hard-rule and reason-code review;
- explicit no-rule-relaxation confirmation.

Schema-valid but unreviewed activities remain `DRAFT`. Owner-reviewed activities become `PROVISIONAL_OWNER_REVIEWED`, never production-approved.

## Phase 3 - harness and fixtures

Tasks: P1-07 through P1-09.

Exit evidence:

- standalone command and environment record;
- passing positive/negative/no-result fixture log;
- deliberate mutation test proving mismatches fail;
- category coverage metrics;
- deterministic rerun result.

## Phase 4 - acceptance and traceability

Tasks: P1-10 through P1-12.

Exit evidence:

- Gate B Given/When/Then review;
- ActivityHandoff completeness and identity-lock review;
- requirement traceability report;
- architecture/security/harness validation;
- known-limitations register and owner review decision.

Completion closes only this standalone workstream. Runtime recommendation, Gate B UI/API, and integration remain separately gated.
