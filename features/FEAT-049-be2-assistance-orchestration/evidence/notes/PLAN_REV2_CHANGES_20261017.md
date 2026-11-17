# BE2-03 plan revision 2 — finding map and checks, 2026-10-17

Planning-only correction requested by the user after `PLAN_CODEX_REVIEW_20261017.md`
(NEEDS_REVISION, 1 P1 / 4 P2). That review record and its metrics are unchanged.

| Item | Value |
|---|---|
| Worktree / branch / HEAD | `.worktrees/be2-03-assistance-orchestration`, `feature/be2-03-assistance-orchestration`, f120c4fce8f7853e5ab5e061eff4bf916d45603c, staged 0 |
| Revision 1 | SHA256 bb072cf54cc9012f05fcee984b8aae7b6bec2d53dc21a70f446c33cf9c0afe5e, 32784 bytes; byte-identical copy (same SHA256 verified) in ignored `../local/planning-rev2-20261017/PLAN_REV1_bb072cf5_HISTORICAL_DRAFT.md`; historical draft, never approved |
| Revision 2 | `../../plan/PLAN.md`, SHA256 0894c39b286ca7d52335bc8e55a39e13aa7f1e0d53d8dc0623c631df9ab95d2e, 48409 bytes |
| Approval / implementation | AWAITING_APPROVAL / NOT_STARTED; D1–D11 recommendations only |

## Finding → revision-2 text → cases

| Finding | Prerequisite code checked (paths under `backend/src/sketch2life/`) | Revision-2 resolution | Cases |
|---|---|---|---|
| A1-PR01 P1 late create escapes cancel/budget | `application/services/ai_jobs.py` create 342–446 (eligibility 389, fence 406, independent commit 418–445), dispatch 566–582, start 662–681, completion 762, retry 900–913; `infrastructure/ai_jobs/fakes.py` FakeEligibility 564–596, FakeOwnerFences 79–98 | Plan §8.2: retained create key/principal/RequestRef; request-aware fenced `EligibilityPort` decorator (new adapter) denies create/dispatch/start/retry after a cancel/stale commit; scheduler outcome table incl. losing link CAS with cleanup record; read-only job reader; settlement axis (§6); no release without settlement (§9.1) | R09, R10, R11, R14, P05 |
| A1-PR02 P2 dedup omits resolved pin | service semantic key 364–374/387/404; C2 `strict_canonical_sha256` | Plan §8.3: `assistance_context_digest` over exact owner facts + resolved source; `semantic_identity` incl. input_hash, audience, purpose, policy, digest; excluded operation ids; fact-change supersession instead of dedup | N23, N24, N25, P04 |
| A1-PR03 P2 queued retry refunds spent stage | `domain/ai_jobs/model.py` Attempt 186–193, attempts 203, active `started_at` 231, record_failure 311–334, requeue 390–408 | Plan §9.1: monotonic held→consumed/released; evidence = any attempt `started_at` in history via reader; unknown → hold; release only when settled with no started attempt | R06, R12, R13, P05 |
| A1-PR04 P2 terminal vs cancel-wins | — (plan-internal contradiction) | Plan §6/§8.4: linearization at BE2-03 handoff commit; separate rows for observation accepted before handoff vs handoff committed; post-handoff cancel 409; withdrawal belongs downstream; pending D11 with versioned-withdrawal alternative | R03a, R03b, N14 |
| A1-PR05 P2 wrong queue boundary | service `_publish` 595–607 (only QueueUnavailable site) | Plan §8.2: boundary 1 lost reply/crash before link → same command replay; boundary 2 broker down after link → `scheduled`, job queued, foundation outbox retry; failure injected only into the fake queue | R08a, R08b |
| Clarification: cache "replay" | `application/services/vision_analysis.py` 304–317 (`record_observation` lineage guard), 828, 853; `domain/vision_analysis.py` 411–412 | Plan §9.2: supported current-read gate (`analysis_record` + `downstream_meaning` + exact bindings + current member facts); `record_observation` never called; `cache_hit_of` keeps original provenance | P08, N17 |
| Clarification: CMD-33 idempotency | — | Plan §5 field map and §8.1: scope `(org, principal, AssistanceRequestCancelV1, assistance_id, key)`, fingerprint, missing key/If-Match, replay after bump/turn close, mismatch, revoked disclosure | N14, N16, N20, N21, N22 |

Other notes from the review kept as stated: D3/D5/D9 remain explicit owner choices; the
teammate-branch FEAT-048 number collision is a separate integration concern; FEAT-049 is not
renamed.

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

Raw logs: ignored `../local/planning-rev2-20261017/`. These checks were run before this table
was filled in; the note itself was rescanned for whitespace afterwards.

No application code, tests, services, installs, network/provider/Studio execution or Git
staging/commit/push in this correction. A1 tests do not exist and were not run.
