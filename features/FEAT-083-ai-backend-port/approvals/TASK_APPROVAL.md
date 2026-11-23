# FEAT-083 task approval

## FEAT-083 Plan Rev1 — AI backend port under Phase A

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: Project owner (Person 2, AI Understanding lane), direct instruction on 2026-11-23 to take the AI part of CaoDat's branch under the Phase A routes and to record this approval.
- Approved plan: `features/FEAT-083-ai-backend-port/plan/PLAN.md`.
- Plan SHA-256: `86F8198686931EDE75482C910ED1BB221EC90B4243D6FA285D36F93C9D83A418`.
- Scope: the four ordered items in the plan — Modal workloads, Modal client and story contracts, SVG engine and catalog (with the layering fix and migration re-parenting), and Parent topic suggestions — implemented in worktree `.worktrees/aiport1` on branch `codex/aiport1-backend-ai-20261123`, based on `origin/feature/backend-srs-api-and-fe-integration` at `4b961c27`.
- Decision recorded: Phase A routes, `story.activity_selections` and migrations `20261123_as_0001` / `20261123_rv_0001` win over the duplicate activity-selection and video-generation designs on the source branch; those duplicates are not ported.
- Exclusions: everything under "Out of scope" in the plan, including Parent activity selection tables/routes/migration, the Parent video candidate, registration completion, Firebase changes, all mobile code, all source-branch evidence, SRS and SRS-authority edits, real provider/Firebase/paid calls, PostgreSQL on ports 5432/5433 or `sketch2life_m2_s1a`, reading secrets, commit and push.
- Approval basis: this record is the pre-change approval for the bounded task; it does not approve the unsigned SRS, any SRS revision, or any commit. A change to the plan hash requires a new amendment.

## FEAT-083 Amendment 1 — replace the legacy sketch-guides route

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: Project owner (Person 2, AI Understanding lane), direct instruction on 2026-11-23, answering the implementation question raised during the run.
- Amended plan: `features/FEAT-083-ai-backend-port/plan/PLAN.md`.
- Amended plan SHA-256: `F9354BEFF35D1A34A70C5457C5846007ECCDD905DC78323D18562B4DBF073D80`. This supersedes the Plan Rev1 hash above for the same plan file.
- Change: the existing legacy AI route `POST /api/parent/v1/ai/sketch-guides` is replaced by the catalog-first SVG guide route from the source commit (same path and method, new request/response contract, unknown topic returns 404 with no AI fallback). It is not a Phase A route. Acceptance criterion 6 and the SVG-catalog scope item are adjusted accordingly.
- Limits: only this one `parent_ai.py` route may change; every activity route and every other out-of-scope item stays excluded. Mobile adaptation to the new contract is a separate follow-up task. No commit or push is approved.

## FEAT-083 Amendment 2 — narrow the Modal scope to additive changes

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: Project owner (Person 2, AI Understanding lane), direct instruction on 2026-11-23, answering the compatibility problem found during the run.
- Amended plan: `features/FEAT-083-ai-backend-port/plan/PLAN.md`.
- Amended plan SHA-256: `59F4DF52728275F707616A1FCCBD9D9204BAADFEC06017BBF2A434E9AA8C5287`. This supersedes the Amendment 1 hash for the same plan file.
- Change: scope items 1 and 2 (Modal workloads, Modal client, story contracts) are narrowed to additive changes. The existing Parent activity worker contract, the Story v1 worker input/output, the existing story/activity model pin and `parent_activity_suggestions.py` stay unchanged. The Qwen3.8-FP8 move for story and activity, the v3 story input, the stricter story-draft validation and ADR-0024 are deferred to a follow-up task. A new acceptance criterion requires the existing activity-worker, Story v1 and Modal story/activity tests to pass unchanged.
- Limits: all other exclusions of Plan Rev1 and Amendment 1 stay. No commit or push is approved.

## FEAT-083 Amendment 3 — allow minimal test edits for the replaced sketch-guides route

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: Project owner (Person 2, AI Understanding lane), direct instruction on 2026-11-23, answering the test-handling question raised during the run.
- Amended plan: `features/FEAT-083-ai-backend-port/plan/PLAN.md`.
- Amended plan SHA-256: `B1D2AF0BE53DC56927E15F27FE77CDC3EB41A30772A4FF640BB4848F9861CCBB`. This supersedes the Amendment 2 hash for the same plan file.
- Change: acceptance criterion 7 allows minimal edits to the existing tests that assert the behaviour of the one replaced legacy route `POST /api/parent/v1/ai/sketch-guides` (the route-surface and provider-gate tests), limited to that route's assertions and listed by name in the evidence notes. All other existing passing tests must pass unchanged.
- Limits: all other exclusions of Plan Rev1 and Amendments 1-2 stay. No commit or push is approved.
