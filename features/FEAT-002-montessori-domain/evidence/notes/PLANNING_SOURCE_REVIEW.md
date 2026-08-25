# Planning source review

- Review date: 2026-08-25
- Purpose: prepare Person 1 plan revision 4; no implementation authorization.

## Authority order applied

1. Direct project-owner request: create a separate branch and prepare Person 1 task planning/phases/evidence for approval.
2. ADR-0006: Person 1 owns standalone BA/Montessori specifications and harness work, not recommendation runtime.
3. Repository governance and architecture rules.
4. Handbook/workbook as non-authoritative reference evidence.

## Sprint workbook observations

The `Detailed Breakdown` sheet describes 12 Person 1 tasks totaling 40 hours and 10 story points, with no cross-person dependency. It covers structure, glossary/version rules, Activity schema, objective taxonomy, 20-30 activities, hard rules, harness, positive and negative cases, Gate B criteria, ActivityHandoff, and traceability. The owner later expanded the catalog target to 100-200, so revision 4 preserves the task decomposition but recalculates workload instead of preserving an invalid estimate.

## Official age-band observations

AMI identifies 0-3, 3-6, and 6-12 Montessori programme levels. AMS also describes Elementary as 6-9 and 9-12, sometimes combined. Revision 4 therefore uses 0-3, 3-6, 6-9, and 9-12 as catalog review bands. These sources support classification only; they do not pedagogically approve individual activities.

## Handbook observations

Relevant sections identify Activity, Concept, Prerequisite, SafetyRule, MaterialOption, and History fields; require hard filters before scoring; accept no-valid-activity; lock activity/objective versions at Gate B; and require ActivityHandoff fields for the off-screen endpoint. Runtime recommendation and UI/orchestration descriptions are excluded from Person 1 Sprint 1 implementation under the owner's newer allocation decision.

## Limitations

- Individual activity validity still lacks qualified Montessori review; owner review is provisional only.
- The workbook estimates are planning inputs, not guarantees.
- The handbook is an architecture reference, not task approval.
