# BE2-03 source audit — 2026-10-17

Read at base f120c4fce8f7853e5ab5e061eff4bf916d45603c (paths relative to the worktree). Later
real approvals/acceptances/push receipts override older dated ledger lines; prompts are not
approvals.

## Workspace identity

| Check | Result |
|---|---|
| Source worktree `.worktrees/be2-02-vision-correction` | branch `feature/be2-02-vision-correction`, HEAD f120c4f = `origin/...` tracking, clean, staged 0 |
| C2 push receipt (ignored, source worktree `evidence/local/c2-publication-exec-20261017/push.json`) | `98876fe..f120c4f`, remote = local head, no force/merge/deploy |
| Target branch/directory before creation | absent |
| Created | `git worktree add --no-track -b feature/be2-03-assistance-orchestration ... f120c4f` (per-command safe.directory); new HEAD f120c4f, clean, staged 0 |
| Feature ID | FEAT-049 free on all local branches/worktrees and `origin/*` refs (last fetch; no fetch run) |
| Observation | `origin/feature/be2-08-14` (b358bc7) has `FEAT-048-be2-content-publication` — same number as FEAT-048 here; reported, not changed |

## Sources

| Source | Sections used |
|---|---|
| AGENTS.md; docs/governance/WORKFLOW.md | Gates, records, evidence, architecture/security rules |
| docs/context/PROJECT_CONTEXT.md | BE2-02 current state; BE2 7/7 split; product scope v3.1; environment policy |
| docs/context/SOURCE_REGISTER.md | Authority rows for BE2-02 C1/C2 |
| FEAT-040 TEAM_TASK_BREAKDOWN.md | H-* ledger 126–147; DAG 187–200; BE2-01/02/03/04 cards 510–552; BE2-14 666–676; FR rows 1008–1038 |
| FEAT-029 Master SRS | FR024–030 400–406, FR054 459; B19.2 752–790; B19.6 870–884; B19.10/CS-026 948–974; B19.11 976–993; UC-019 1276–1285; UC-032 1419–1428; DATA-21 1648, DATA-22/23 1650–1652, DATA-25 1660; B22.1 1706–1734; B22.2 1737–1777 |
| FEAT-044 plan/BE2_ROADMAP.md | Routing amendment 3–37; §3 queue/§3.1 substitution 86–122; §3.2 DAG; §4 BE2-03 163–168, BE2-14 240–245; §5–§6 247–327 |
| FEAT-044 plan/BE2_EXECUTION_TRACKER.md | Current states, branch workflow, queue Q05, gates, change log |
| FEAT-044 evidence/notes/PHASE_B_B6_HANDOFF_20261016.md; PHASE_B_B6_A17FIX01_CLOUD_RECEIPT_REVIEW_20261016.md | B-12 deferred items; WAITING_STUDIO status |
| FEAT-044 artifacts/BE2_08_14_TEAMMATE_HANDOFF.md (+ teammate ref, read-only) | BE2-14 owns budgets/limits; no policy port published yet |
| FEAT-048 status/STATUS.md, CONTEXT, DECISIONS (D04 ports, C2 Q1–Q5), approvals C1/C2, plans, H_AI_REVIEW_HANDOFF.md, C2_CODEX_REVIEW_20261017.md | Pin/input_hash/job scope contract; typed context digest semantics; non-blocking limits |
| Code | `domain/vision_analysis.py` (CheckpointBinding…AssistancePin, lineage), `domain/vision_context.py` (C2 enums, per-member gate), `contracts/schemas/ai_contract_candidates.py` (DATA-21 ShapeSpec), `application/ports/ai_jobs.py`, `application/services/ai_jobs.py` (create/cancel, receipts, semantic key, public messages), `application/ports/vision_analysis.py`, `application/services/vision_analysis.py` (typed current/status), `infrastructure/vision_analysis/job_lineage.py`, `application/ports/core_foundation.py`, `tools/validate_architecture.py`, interfaces/http fixture-app pattern |

## Protected bytes (unchanged; SHA256 at base)

| File | SHA256 |
|---|---|
| FEAT-048 plan/PLAN_REV1_APPROVED.md | f4733c88797edbcce225ecd63700634f929ca75789362c7f3a58a2b57f19df30 |
| FEAT-048 plan/C2_TYPED_CONTEXT_PLAN_REV2_APPROVED.md | 4b339514d3d5bf01b9a8c23f0a15ea5e71b4d2f1389db9e141e31aa322cd57c2 |
| FEAT-048 approvals/C2_TASK_APPROVAL.md | 16af8a94c1de2430745ba213d7e183ffa28305de33856a153e9b49d836d294df |
| FEAT-048 approvals/C2_COMPONENT_ACCEPTANCE.md | 35962b02864f84cb4532897efc63e94cc297f23359c4a9b287f5a16b49fd6ad5 |

## Source gaps carried into the plan

- DATA-21 `checkpoint_ref.server_sequence` has no field in BE2-02 `CheckpointBinding`; resolved
  through a BE2-03 source port without changing the C1 type.
- DATA-21 `request_reason`/`requested_level` vs C2-local `RequestReason`/`RequestedLevel` (D9).
- `AnalysisScope` requires a contributor in the audience; DATA-21 defines the contributor only
  for Child requests (D5).
- DATA-21 `status` values and `request_revision` bump rules are unspecified (TC-01, D2).
- No versioned BE1 turn/roster/region/consent/context-revision handoff and no BE2-14 policy port.
