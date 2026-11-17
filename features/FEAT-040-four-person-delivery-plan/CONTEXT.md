# Four-person delivery planning context

- Status: DONE — documentation only; proposed runtime cards NOT_STARTED.
- Date: 2026-10-10, Asia/Saigon.
- Owner: Sketch2Life project owner.
- Direct request: “lên task cho 4 người, 1 người fe, 2 người be, 1 người tổng hợp”.
- Goal: actionable Vietnamese allocation/backlog for the replacement collaborative-learning SRS v3.1, covering all modules and integration responsibilities.
- Confirmed staffing: one FE, two BE, one technical integrator. Owner explicitly says the fourth person connects all other parts; actual names are not supplied.
- Sources: canonical SRS v3.1, FEAT-039 reuse audit/ADR-0014, ADR-0006 and existing FEAT-001/012 allocation records, project context/source register/governance.
- Constraints: keep FastAPI and React Native; preserve scope and originals; four independently runnable fixture/contract Sprint 1 streams; roadmap and sprint staffing separate; per-feature approval/visual/evidence/security gates.
- Change boundary: current owner role split supersedes historical discipline labels for the new scope. It does not grant runtime implementation, all-stack adoption, provider execution or deployment.
- Non-goals: changing existing runtime, upgrading packages, creating real accounts/data, assigning names not provided, messaging other people, creating new user chats, commit/push.
- Risk: one FE has Android plus Teacher/Admin surfaces; task scope and staged integration must keep this workload explicit. Coordinator does not inherit backend/infrastructure or all E2E by default.

Owner answered: “chia theo tasks thường thôi, ko cần ngày” and “sẽ chịu trách nhiệm nối lại tất cả các thứ khác”. Deliver task cards/dependencies/acceptance only, with no dates, calendar, duration or hours estimates. Fourth person owns technical composition/integration and combined validation coordination; component logic and component tests remain with their FE/BE owner. Fixture-first independence remains a technical delivery gate, not a calendar sprint schedule.

Delivered artifacts/TEAM_TASK_BREAKDOWN.md: 57 cards, 14 handoffs, complete M/FR/CMD/DATA/UI ownership and dependency views. ADR-0015 records role/integration authority, project context/source register point to it, old staffing documents retain their contents with a current-allocation notice. Independent review and own static checks PASS; repository architecture PASS, global harness/security retain unrelated existing findings recorded under this feature evidence. Canonical SRS unchanged; no runtime/provider/deployment/commit/push work performed.
