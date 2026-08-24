# Context management guide

## Where context lives

```text
docs/context/
├─ PROJECT_CONTEXT.md             # stable project truth and current phase
├─ SOURCE_REGISTER.md             # reference sources and authority boundary
└─ CONTEXT_MANAGEMENT.md          # this operating guide

features/FEAT-xxx/
├─ CONTEXT.md                     # feature snapshot and assumptions
├─ DECISIONS.md                   # feature-local decisions
├─ plan/PLAN.md                   # scope, acceptance, verification
├─ approvals/TASK_APPROVAL.md     # explicit implementation permission
└─ evidence/                      # proof belonging only to this feature
```

## Update rules

- Update project context only for cross-feature truth or phase changes.
- Update feature context when assumptions, dependencies, risks, or status change.
- Put reversible/local choices in feature `DECISIONS.md`.
- Put cross-feature or irreversible choices in `docs/adr/`.
- Never rewrite history silently; append a dated decision or evidence entry when meaning changes.
- Link evidence IDs from plans and decisions so a reviewer can trace claims to proof.

## Context snapshot format

Every feature context should answer: goal, scope, non-goals, owner, dependencies, source references, assumptions, risks, current status, and next review gate.

## What is not context

Do not use chat transcripts, untracked screenshots, unversioned local files, or model output without provenance as project context. Summarize them into a feature record and preserve the auditable artifact where needed.
