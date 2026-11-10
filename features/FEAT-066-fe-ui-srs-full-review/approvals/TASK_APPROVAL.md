# Task approval — FEAT-066 School Manager web remediation

- Status: `APPROVED_FOR_IMPLEMENTATION`
- Approver: User, direct instruction in chat on 2026-11-10 (Asia/Bangkok); no further approval requested or required for this scope.
- Approved scope: FEAT-066 plan revision 4; modify only `apps/school-manager-ui` and FEAT-066 governance/evidence in worktree `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, branch `codex/fe-ui-web-remediation`.
- Plan revision: 4
- Plan SHA-256: `D9780223AB395C1B5A9942F4011B749A2A15E3D66283A178F768AF9E9AC0CCB6`
- Product requirements: canonical FEAT-063 SRS v2.7-draft Rev57, verified SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; still a draft awaiting formal owner sign-off. This task approval does not sign off the SRS.

## Approved work

- Correct M01 approval/change-request counts, notification inbox affordance/state, M02 responsive layout, M01 tab semantics and keyboard behavior, and misleading organization dropdown styling.
- Inspect existing API/contracts for the School Manager flows named in plan revision 4. Implement a flow only when a compatible contract already exists; otherwise show a clear unavailable state and record the missing dependency in FEAT-066 evidence.
- Run the local School Manager preview bound to loopback, manually inspect the requested routes at desktop and 390px, and save traceable before/after screenshots under FEAT-066 evidence.
- Update FEAT-066 context, decisions, evidence, and status as the work progresses.

## Conditions and exclusions

- Parent mobile/UI, Teacher, Admin/Platform Admin, backend, contracts, providers, production services/data, credentials, and real user/child data are excluded.
- Do not invent data, successful transactions, prices, billing policy, subscription policy, or quota-commercial policy. Keep School Manager child-media access denied by default.
- Do not run or add automated tests/builds unless separately requested. Repository security validation is required before commit/push.
- The previous revision 3 read-only audit approval is superseded for this implementation scope only; its audit/evidence remains historical and unchanged.

This approval record and the matching plan hash were written and verified before product code changes.