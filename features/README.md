# Feature isolation

Each feature has its own folder: `features/FEAT-<number>-<slug>/`.

Use this minimum structure:

```text
FEAT-000-example/
├─ CONTEXT.md
├─ DECISIONS.md
├─ plan/PLAN.md
├─ approvals/TASK_APPROVAL.md
├─ evidence/
│  ├─ README.md or INDEX.md
│  ├─ raw/
│  ├─ screenshots/
│  ├─ metrics/
│  └─ notes/
├─ assets/
│  ├─ generated/
│  ├─ approved/
│  ├─ applied/
│  └─ REVIEW.md
└─ src/              # feature code only after approval
```

Do not put evidence, screenshots, or feature-specific notes in a shared catch-all folder.

For the full rules, read `docs/context/CONTEXT_MANAGEMENT.md` and `docs/governance/EVIDENCE_MANAGEMENT.md`.
