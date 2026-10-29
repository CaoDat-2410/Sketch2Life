# BE2-03 plan revision 3 — change map and checks, 2026-10-17

Planning-only correction requested by the user after `PLAN_CODEX_REREVIEW_20261017.md`
(NEEDS_REVISION, 0 P1 / 1 P2). That re-review, its metrics and all earlier records are unchanged.

| Item | Value |
|---|---|
| Worktree / branch / HEAD | `.worktrees/be2-03-assistance-orchestration`, `feature/be2-03-assistance-orchestration`, f120c4fce8f7853e5ab5e061eff4bf916d45603c, staged 0 |
| Revision 2 | SHA256 0894c39b286ca7d52335bc8e55a39e13aa7f1e0d53d8dc0623c631df9ab95d2e, 48409 bytes; byte-identical copy (same SHA256 verified) in ignored `../local/planning-rev3-20261017/PLAN_REV2_0894c39b_HISTORICAL_DRAFT.md`; never approved |
| Revision 3 | `../../plan/PLAN.md`, SHA256 e1fce645a5d8c98efe366865f5a8a1b9c81c8a48626723c4e73f0c646979d3e5, 55475 bytes |
| Approval / implementation | AWAITING_APPROVAL / NOT_STARTED; D1–D11 recommendations only |

Prerequisite code re-read (paths under `backend/src/sketch2life/`): `infrastructure/ai_jobs/fakes.py`
`FakeOwnerFences.hold` 94–98, `_UnitOfWork.hold_owner_fences` 230–231,
`InMemoryAiJobStore.transaction` 466–479 (RLock, staged state published at 479,
`fail_next_commit`); `application/services/vision_analysis.py` `_teacher_read` 878–892.
Raw witness read: ignored `../local/codex-plan-rereview-20261017/post_hold_probe.json`.

| Item | Revision-3 change | Cases |
|---|---|---|
| A1-PR01-F1 epoch-only hold leaves post-hold/pre-commit gap | Plan §8.2: `AssistanceCommitCoordinator` shared by a new `CoordinatedAiJobRepository` decorator (whole foundation write transaction through commit), the assistance fake UoW (state + epoch published together) and `AssistanceEligibility` (state + epoch read together); lock order coordinator → store; same-thread deferral until the foundation transaction exits; exceptions publish nothing and release in `finally`; restated fake-level guarantee | R15a (cancel first → hold fails, re-decide, denied), R15b (start first → deferred/blocked cancel, consumed), R16 (exception paths) |
| Test-boundary rule | Plan §8.5 and §11 preamble: hooks inside a coordinated foundation transaction only request publication; orders named by actual commit order | R15b, existing R03a/R06/R09/R10 |
| Note: Vision reader authority | Plan §8.4: injected scoped Teacher reader principal; never from request fields; device disclosure checked independently | P07, P08 |
| Note: monotonic budget | Plan §9.1: consumed stays consumed while cleanup is open; held only if not consumed | R12, R15b |
| Note: D2 validator scope | Plan §13 D2: lineage/If-Match revision only; no conditional GET added | — |

Unchanged on purpose: PR02–PR05 resolutions, scheduler outcome table, settlement, D1–D11.

## Checks (repository root, existing Python 3.12.10, Windows)

| Command | Result |
|---|---|
| `python tools/validate_harness.py` | exit 0, HARNESS_VALID |
| `python tools/validate_repository_security.py` | exit 0, REPOSITORY_SECURITY_VALID |
| `python tools/validate_architecture.py` | exit 0, ARCHITECTURE_VALID |
| `python tools/validate_skeleton.py` | exit 0, SKELETON_VALID |
| `git diff --check` | exit 0, no output (tracked edits) |
| FEAT-049 markdown outside `evidence/local`: trailing-space and CR scan | none found |
| FEAT-048 approved plans/approval/acceptance SHA256 | unchanged (4b339514…, f4733c88…, 16af8a94…, 35962b02…) |

Raw logs: ignored `../local/planning-rev3-20261017/`. No application code/tests, service,
install, network/provider/Studio execution or Git staging/commit/push. A1 tests do not exist and
were not run.
