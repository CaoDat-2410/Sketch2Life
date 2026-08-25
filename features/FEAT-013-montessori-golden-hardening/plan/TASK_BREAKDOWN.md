# Person 1 Golden Catalog task breakdown

- Plan revision: 1
- Total: 10 tasks, 55-73 hours, 13.75-17.75 story points
- Cross-person runtime dependency: none
- Implementation status: `BLOCKED_BY_TASK_APPROVAL`

| Task | Depends only on | Parallel-safe output | Required evidence |
|---|---|---|---|
| G1-01 | FEAT-002 local files | Frozen selection/baseline manifest | Hash report and selection review |
| G1-02 | G1-01 | Versioned schema/spec | Valid/invalid contract tests |
| G1-03 | G1-02 | Local registries/rules | Reference and semantic review |
| G1-04 | G1-01..03 | Five 0-3 candidate records | Record checklist and fixture mapping |
| G1-05 | G1-01..03 | Five 3-6 candidate records | Record checklist and fixture mapping |
| G1-06 | G1-01..03 | Five 6-9 candidate records | Record checklist and fixture mapping |
| G1-07 | G1-01..03 | Five 9-12 candidate records | Record checklist and fixture mapping |
| G1-08 | G1-04..07 | Standalone validator and fixtures | Pass/fail/mutation/repeatability logs |
| G1-09 | G1-04..08 | Owner packet and traceability | Review ledger and metrics |
| G1-10 | G1-01..09 | Final handoff | Architecture/security/limitations evidence |

G1-04 through G1-07 are content batches that can be worked independently by Person 1 but must share the frozen schema/registries. No task calls or waits for another person's service.
