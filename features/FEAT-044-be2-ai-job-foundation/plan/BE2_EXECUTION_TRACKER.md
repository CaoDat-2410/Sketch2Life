# BE2 execution tracker

- Roadmap: BE2_ROADMAP.md revision 2
- Updated: 2026-10-15, Asia/Saigon
- Executor: Claude; owner: P3/BE2; Codex planning/review
- ACTIVE slot: Q00 — BE2-01 Phase A acceptance gates; code corrections closed
- Authorized code scope: FEAT-044 plan/PLAN.md revision 1 Phase A A1–A9 only
- Current review: PASS at Phase A fake/contract scope — R01–R11 original cases and R03a/R04a/A18a independently CLOSED. Actual combined checks: 255 tests passed/1 Pillow skip; runner 222 checks/0 failures. Overall Phase A acceptance remains PENDING adoption/environment gates. Latest: evidence/notes/PHASE_A_Q00_FINAL_CODE_REVIEW_20261014.md; earlier reviews preserved as history.
- Phase B plan review: revision3 PASS at design-review scope; PB-C01/PB-C02 CLOSED, original PB-R01–PB-R06 closure retained. Latest evidence/notes/PHASE_B_PLAN_FINAL_REVIEW_20261015.md. Next B1 docs/gate prompt: CLAUDE_PHASE_B_B1_GATE_PROMPT.md; owner/approval/environment gates remain.
- Implementation WIP: 1 card/chặng; other rows below are queue, not implementation authorization

## Current work order

| Field | Value |
|---|---|
| Goal | Resolve remaining Phase A acceptance gates and record the handoff |
| Allowed outputs | Adoption/compatibility decisions, existing skipped-check receipts or explicit checkpoint deviation, handoff/tracker/evidence |
| Required corrections | None from the latest code review; all original and follow-up findings CLOSED |
| Verification | Code checks already reproduced; execute the remaining live-app route check in a compatible existing environment and record named consumer review/adoption |
| Exit | P1/P2/P4 candidate cross-review/handoff decision and skipped-check disposition recorded; explicit Phase A checkpoint acceptance. Production adoption may remain deferred; full BE2-01 completion separate |
| Excluded | Phase B/database/broker, new business card, real provider/model, dependency install, broad legacy refactor, UI, commit/push/deploy |
| Prompt | CLAUDE_Q00_ACCEPTANCE_PROMPT.md; fix prompts retained as history |
| Next default | Q01 only when own plan/approval/ADR prerequisites are present; otherwise explicit candidate-only substitution |

No new bugfix card is created. These rows are the frozen review corrections inside Q00:

| Finding | Status | Closure evidence |
|---|---|---|
| R01 foreign artifact quarantine | CLOSED_ORIGINAL_CASE | Codex Q00 closure review; independent original repro/tests |
| R02 semantic scope dedup | CLOSED_ORIGINAL_CASE | Codex Q00 closure review; independent original repro/tests |
| R03 completion receipt poisoning | CLOSED_ORIGINAL_CASE; R03a CLOSED | Codex Q00 final code review; independent original/follow-up repro/tests |
| R04 malformed failure polling | CLOSED_ORIGINAL_CASE; R04a CLOSED | Codex Q00 final code review; independent original/follow-up repro/tests |
| R05 concurrent purge idempotency | CLOSED_ORIGINAL_CASE | Codex Q00 closure review; independent original repro/tests |
| R06 old purge receipt replay | CLOSED_ORIGINAL_CASE | Codex Q00 closure review; independent original repro/tests |
| R07 enum shape validation | CLOSED_ORIGINAL_CASE | Codex Q00 closure review; independent original repro/tests |
| R08 non-success result refs | CLOSED_ORIGINAL_CASE | Codex Q00 closure review; independent original repro/tests |
| R09 dispatch eligibility | CLOSED_ORIGINAL_CASE | Codex Q00 closure review; independent original repro/tests |
| R10 polling hint/ETag | CLOSED_ORIGINAL_CASE | Codex Q00 closure review; independent original repro/tests |
| R11 Child schema consistency | CLOSED_ORIGINAL_CASE | Codex Q00 closure review; independent original repro/tests |


### Focused follow-ups within Q00

These are corrections to existing Phase A invariants, not new business cards:

| Item | Origin | Status | Exact exit |
|---|---|---|---|
| R03a accepted output still quarantined | Directly enabled by corrected-completion fix | CLOSED (independent final code review) | Coherent artifact availability verified; unsafe/revoked/foreign quarantine retained |
| R04a list/dict provider code crash | Residual malformed-input handling in new normalizer | CLOSED (independent final code review) | Safe typed outcomes and later valid completion/redaction verified |
| A18a stale cancel overwrites purge | Pre-existing gap, not introduced by Q00; existing A-18 invariant | CLOSED (independent final code review) | Event-controlled cancel/purge/register interleavings preserve state/receipt; R05/R06 retained |

## Default queue and checkpoint levels

Component/runtime/integration refer to roadmap definitions. NOT_STARTED means no new-scope completion claimed; legacy code/shape fixtures do not complete these cards. Each owning feature must supply the approved plan, exact checkpoint scope and evidence when work starts.

| Slot | Card/chặng | Component checkpoint | Runtime checkpoint | Integration checkpoint | Current authorization / next prerequisite |
|---|---|---|---|---|---|
| Q00 | BE2-01 A | CODE_REVIEW_PASS; ACCEPTANCE_GATES_PENDING (record prepared; owner decisions + live-route test outstanding) | N/A for Phase A | Candidate adoption PENDING | APPROVED Phase A rev1; all findings CLOSED; adoption/Pillow disposition outstanding |
| Q01 | BE2-01 B | PLAN_REVIEW_PASS_WAITING_GATES — rev3; all review corrections CLOSED; implementation NOT_STARTED/UNAPPROVED | NOT_STARTED | NOT_STARTED | B1 decisions using CLAUDE_PHASE_B_B1_GATE_PROMPT.md; G1 disposition + G2 separate approval + D1–D7/Q1–Q8/env before B2–B6 code |
| Q02 | BE2-12 | NOT_STARTED | NOT_STARTED | NOT_STARTED | Own plan/approval; shared DATA-24; publication/recall policy |
| Q03 | BE2-14 | NOT_STARTED | NOT_STARTED | NOT_STARTED | Own plan/approval; DATA-33/CMD-48; Admin/policy/copy lifecycle decisions |
| Q04 | BE2-02 | NOT_STARTED | NOT_STARTED | NOT_STARTED | Own plan/approval; accepted foundation; snapshot/context; real profile gate |
| Q05 | BE2-03 | NOT_STARTED | NOT_STARTED | NOT_STARTED | Own plan/approval; 01/02, turn/scope/budget contracts |
| Q06 | BE2-04 | NOT_STARTED | NOT_STARTED | NOT_STARTED | Own plan/approval; 01/02/03; selected Sketch profile and actual generation |
| Q07 | BE2-05 | NOT_STARTED (shared shape exists) | NOT_STARTED | NOT_STARTED | Own plan/approval; 04 runtime, teaching/moderation/access contracts |
| Q08 | BE2-06 | NOT_STARTED | NOT_STARTED | NOT_STARTED | Own plan/approval; 05 + current turn/grant |
| Q09 | BE2-07 | NOT_STARTED | NOT_STARTED | NOT_STARTED | Own plan/approval; source/content/confirmed-context contracts |
| Q10 | BE2-08 | NOT_STARTED | NOT_STARTED; library/generation separately tracked when opened | NOT_STARTED | Own plan/approval; 01/07; library rights/profile; selected real generation gate |
| Q11 | BE2-09 | NOT_STARTED | NOT_STARTED | NOT_STARTED | Own plan/approval; 08 path + shared review + BE1 access/session ports |
| Q12 | BE2-10 | NOT_STARTED | NOT_STARTED | NOT_STARTED | Own plan/approval; 01/08; adopted retry/budget + BE1 receipts |
| Q13 | BE2-11 | NOT_STARTED | NOT_STARTED | NOT_STARTED | Own plan/approval; 01/12; activity age/safety/preparation policy |
| Q14 | BE2-13 | NOT_STARTED | NOT_STARTED | NOT_STARTED | Own plan/approval; 01/12; adopted preset/condition/override contracts |

Whole-card counts remain **14**, full-card DONE **0** in this register. 01 has two delivery checkpoints, not two business cards; only Phase A is currently approved. No percentages/task-effort estimates.

## Pending gates and outstanding work

| Gate | Affects | Owner / exact remaining work | Resume condition |
|---|---|---|---|
| Phase A code review | Q00 | CLOSED; Codex independently verified original 11 and three follow-ups | PASS recorded in final code review; no further fix requested |
| Candidate cross-review / adoption disposition | 01A handoff; production adoption separately affects runtime consumers | P1 payload, P2 auth/artifact/persistence boundary, P4 compatibility/composition; retain DATA-24/25 and copy lifecycle owners | Named candidate/version cross-review decision; Phase A may be accepted at fixture/candidate scope with production adoption explicitly deferred, not inferred from fixture pass. Questions/evidence prepared in `evidence/notes/PHASE_A_ACCEPTANCE_GATE_RECORD.md`; all PENDING_OWNER_DECISION |
| Live-app route check dependency | Phase A verification | Claude/check runner in existing compatible environment; Pillow missing in tested venv | Run skipped command or explicit checkpoint deviation decision; no automatic install. 2026-10-14 attempt: exit 0, 1 skipped → NOT_RUN (`raw/q00_accept_live_route_attempt.txt`); no local interpreter has pytest+FastAPI+Pillow |
| Phase B plan correctness | Q01 planning | CLOSED / rev3 plan review PASS; no further plan correction requested | Retain closed design; chosen alternatives/scope changes still require amendment/review |
| Runtime persistence decisions | 01-B + live job integration | BE2/P2/P4 review generic ports/transaction/outbox; project owner adopts ADR | Decisions/feature plan/approval and actual adapter evidence |
| Per-card implementation approvals | 01-B/02–14 | Owning feature/task owner | Exact approved scope before code; roadmap itself is not the approval |
| Model/content/policy choices | Future real adapters/library/activity/preset | Relevant owning card + owner/pedagogical/profile review | Required selected profile/policy/rights evidence; no premature full-stack freeze |

Skipped command from current Phase A report:

```text
python -m pytest backend/tests/contract/test_ai_job_polling.py::test_live_app_routes_have_no_candidate_job_route
```

## Read-only preparation while Q00 waits

2026-10-14, owner says “tiếp tục đi”: latest gate-delivery review verified unchanged sources and corrected handoff wording only. Code remains PASS; acceptance remains PENDING. CLAUDE_PHASE_B_PLANNING_PROMPT.md prepares the next reviewable plan/ADR/port questions independently. Planning does not activate Q01 implementation, replace Q00 gate decisions or add a business card. No Phase B implementation substitution occurred.

Phase B rev1 has now been reviewed: NEEDS_REVISION for PB-R01–PB-R06. The next independent documentation step is plan revision2 using CLAUDE_PHASE_B_PLAN_REVISION_PROMPT.md; current plan/ADR/port proposals remain unadopted and unchanged by the review.

## Substitution/change log

| Entry | From → to | Reason/source | Scope/acceptance delta | Owner decision / authorization | Return checkpoint |
|---|---|---|---|---|---|
| Initial | None | No implementation substitution performed | None | None | Q00 remains ACTIVE |

Before switching away from a waiting slot, fill this row and ACTIVE slot, select one already-authorized alternative from roadmap 3.1 and retain original remaining obligations. Do not mark parent card DONE. A scope change needs a recorded decision/approval; already-authorized same-scope fixes do not need repeated permission.

## Later / outside current card

No enhancement has been authorized by this roadmap change. These examples stay outside the card until a concrete requirement/owner decision exists:

| Idea if raised | Destination | Why it stays out |
|---|---|---|
| Generic AI/workflow/rule platform | Later change record | No acceptance caller in current foundation/preset scope |
| Extra model/provider, TTS, SAM/animation prerequisite | Owning 04/08 profile decision/change record | Not automatically in selected generation scope |
| New gallery/portfolio/session/core privacy logic | BE1 owning card | Not BE2 primary ownership |
| Production deployment/full load platform | P4/approved release or measurement scope | Not component bugfix or implicit roadmap approval |

Use one row with trigger/FR/owner/impact/acceptance, not an expanding implementation todo. Required original scope is never moved here merely because it is difficult.

## Routine update after each meaningful step

Update only the active row's behavior/acceptance/evidence/blocker; add a dated decision for actual changes. Do not recount all passed checks or open downstream code. At closure, record component/runtime/integration separately, unresolved source obligations and next authorized slot. Status remains IN_PROGRESS until appropriate gates are actually met.

2026-10-15 rev2 closure: all original plan cases independently addressed; two exact implementation-contract deltas remain in B1–B6. Owner-fence proof is conditional on D7/Q8 adoption with ASSUMED_CONTRACT fixture; no real owner integration claim. Next documentation revision3 preserves current selected mechanisms and 14-card scope. ACTIVE Q00 unchanged.

2026-10-15 final rev3 plan review: PASS, PB-C01/C02 CLOSED. Move independent documentation work to B1 decision/gate preparation; do not repeat plan fixes or activate code. ASSUMED_CONTRACT owner-fence proof/real integration separation retained. ACTIVE Q00 remains pending disposition; no owner sign-off, stack adoption, install or runtime evidence inferred.
