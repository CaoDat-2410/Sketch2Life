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

## Post-hoc record 2026-11-26 - fixes from 012800df to abbd07cf

- Status: APPROVED (post-hoc record)
- Approver: Project owner.
- Recorded at: 2026-11-26 16:34 +07:00 by the coordinator session, on the owner's instruction in chat after the owner
  was shown the record including the known web parser defect.
- Nature: written after the work. No plan file or plan hash existed before these changes; consent was
  given step by step during the day. This is not a pre-change approval.
- Scope of this record: the eight pushed commits below on `feature/backend-srs-api-and-fe-integration`.
  The two tab-icon commits are web-only and are listed here as well. It approves no further change,
  commit, push, merge or provider call.

### Commits covered

| Commit | Change | Checks recorded | Not verified |
| --- | --- | --- | --- |
| `012800df` | New migration `20261126_as_0003` allows the activity-set receipt operation on PostgreSQL; related DDL tests updated | Migration applied on the local E2E database; API healthy; constraint lists the operation | PostgreSQL acceptance gate |
| `313142a9` | Remove regex `pattern` fields from the Parent activity schema (speed) | Modal worker tests passed except 2 known `lmfe` failures | Broke 4 backend tests in `test_parent_activity_worker_contract.py`; found later, fixed in `abbd07cf` |
| `4db0824a` | Keep the activity suggestion tied to the drawing subject | Modal worker tests passed except 2 known | No real call before commit |
| `f95f46dd` | Slide SVG draft: server sets the view box and repairs shapes the decoder cannot forbid | Modal tests 203 passed, 2 known; one real draft call succeeded (161 s) on the deployed worker | Drawing quality over many subjects |
| `82de8424` | Parent activity drafts accepted without a topic; selection receipt accepts its stored JSON | One real suggestion call succeeded (241 s); ruff and mypy clean; Parent test files had the same 9 failures as the unchanged base | Selection has a unit test only |
| `cc38fccc` | Browser tab icon uses the logo; title "Sketch2Life" | Security, harness, architecture validators | - |
| `db90d4b7` | Tab icon with transparent background (new PNG) | Same validators and skeleton | - |
| `abbd07cf` | Lesson and Parent text trimmed to whole sentences; Teacher drawing guidance 4 to 8 steps (SRS AC-34, FR-T-18); Modal speech transcriber for Parent voice ideas (FR-P-03) | Modal 204 passed, 2 known; changed backend tests passed; web 7 tests and type check; validators; real lesson (293 s, 8 steps) and Sketch Deck (166 s, 8 steps) calls on the deployed worker | **Known defect: the web Sketch Deck parser still accepts only 3 to 5 steps, so a deck with 6 to 8 steps is not shown on the web** (the deck call was checked through the API only; fix assigned, not committed); **speech transcriber never verified with a real call**; full backend suite and PostgreSQL gate not run; 9 mypy errors in `app.py` exist before and after |

### Paid provider use

Modal deploys and calls for these items were approved by the owner per step, each with a budget, in the
AI session. Exact spend is not recorded here.

### Not covered

- The commits of the regrouped goal v4 history before `012800df`.
- Uncommitted work in progress: five web UI fixes, four Teacher flow fixes, Fable UI plan tasks.
- The FLUX drawing-guide picture (parked on `fix/flux-visual`).
- A folder `features/FEAT-085-teacher-ai-navigation-continuity` that a Codex run created with an
  approval record written by itself. It is **not** an approval, was never committed, and is kept outside
  the source tree under `.worktrees/ui-navload/tmp/ai-nav-status/stray/` for the owner to inspect.
