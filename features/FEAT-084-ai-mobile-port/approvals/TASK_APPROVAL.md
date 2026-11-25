# FEAT-084 task approval

## FEAT-084 Plan Rev1 — AI mobile port onto the current mobile line

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: Project owner (Person 2, AI Understanding lane), direct instruction on 2026-11-23 to bring the new Parent AI screens of CaoDat's branch onto the current mobile line and to create this plan and approval.
- Approved plan: `features/FEAT-084-ai-mobile-port/plan/PLAN.md`.
- Plan SHA-256: `BCB2B12BA90BCDBF4486031D3515C3A0817474088E2BFC67AB4B61206B501F49`.
- Scope: the three ordered items in the plan — screens and components, hand-merged additive types/ports/API calls, and tests of the ported pieces — implemented in worktree `.worktrees/aiport2` on branch `codex/aiport2-mobile-ai-20261123`, based on `origin/feature/fe-mobile-remediation` at `d8786b2b`, wired to the FEAT-083 backend contract.
- Decision recorded: the current mobile line is the base and Phase A wiring wins; the source branch's older mobile files are never taken wholesale.
- Exclusions: everything under "Out of scope" in the plan, including the video-candidate screen and wiring, activity suggestion/selection calls, registration completion and auth provisioning changes, app/tsconfig changes, all backend and Modal code, SRS and SRS-authority edits, source-branch evidence, real provider/Firebase/paid calls, network installs, ports 5432/5433, reading secrets, commit and push.
- Approval basis: this record is the pre-change approval for the bounded task; it does not approve the unsigned SRS, any SRS revision, or any commit. A change to the plan hash requires a new amendment.
