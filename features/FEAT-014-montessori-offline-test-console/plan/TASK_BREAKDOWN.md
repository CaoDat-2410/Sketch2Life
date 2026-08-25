# FEAT-014 task breakdown

- Revision: 1
- Status: BLOCKED_BY_TASK_APPROVAL
- Owner: Person 1
- Total: 6 tasks, 12-16 hours, 3-4 story points
- Cross-person runtime dependency: none

| Task | Depends only on | Deliverable | Evidence |
|---|---|---|---|
| C1-01 | Approved/passing FEAT-013 portability correction | frozen console contract and canonical hashes | contract/baseline review |
| C1-02 | C1-01 | shared pure evaluator and loader | 74-case parity report |
| C1-03 | C1-02 | list/evaluate/replay CLI | subprocess snapshots |
| C1-04 | C1-02..03 | guided prompts and safe evidence writer | interactive/path-security tests |
| C1-05 | C1-02..04 | complete positive/negative suite and examples | test and mutation logs |
| C1-06 | C1-01..05 | final docs, traceability, handoff | final gate report |

No task calls or waits for Person 2, 3, or 4. C1-03 and C1-04 may proceed in parallel after the shared contract/evaluator is frozen.
