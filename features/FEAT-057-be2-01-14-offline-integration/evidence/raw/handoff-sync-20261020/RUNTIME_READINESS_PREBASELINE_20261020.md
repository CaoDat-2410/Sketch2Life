# BE2-01–14 runtime readiness and command runbook — 2026-10-20

## Current offline evidence annotation — 2026-10-20

The runtime gates and approved entrypoint audit below remain open. Offline counts
in the original card-by-card table are historical merge-time results. Current
recorded recheck results and the single subsequent test delta are as follows.
Publication/authentication was not rechecked in this follow-up.

Source HEAD: `d35f035f87fddfc87b0d72d8929f5b1b843fce0e`, branch
`feature/be2-backend-ai-integration`. The 08–14 recheck receipts describe
the source **before** the uncommitted F057-H01 integration-test fix. No product
module changed. Only `backend/tests/integration/ai_jobs/test_migrations.py` changed after those runs
(`f3e907442ee228ac45c25834ddc91ee7f27678b2178487062b6d4e331df15d22` → `9b507b7f342a8c863062ed4ff6865a6e5012a804c41b360199f7cadaf3c03d46`).
The recorded `source_unchanged=true` applies during each recorded run; its full
source hash map is historical after this single-file change. Those suites were
not rerun on the new test snapshot. Fresh evidence covers the three affected
offline migration nodes and four guard-probe scenarios only.

| Task | Latest recorded owned result | Regression | SQL in that recheck | Runner state |
|---|---|---|---|---|
| 08 | PIL collection blocked; 446 inventory, no pass count | 1,435 PASS | 11 collection-only | FAIL_ENVIRONMENT_BLOCKED |
| 09 | 458 PASS | PIL collection blocked; 1,881 inventory | 21 collection-only | FAIL_ENVIRONMENT_BLOCKED |
| 10 | 253 PASS | PIL collection blocked; 2,339 inventory | 14 collection-only | FAIL_ENVIRONMENT_BLOCKED |
| 11 | 219 PASS + 25 legacy PASS | PIL collection blocked; 2,592 inventory | 17 collection-only | FAIL_ENVIRONMENT_BLOCKED |
| 12 | 476 PASS, 1 SKIP of 477; skip requires Pillow | Incomplete | NOT_RUN | NOT_RUN |
| 13 | 194 PASS | PIL collection blocked; 2,836 inventory | 11 collection-only | FAIL_ENVIRONMENT_BLOCKED |
| 14 | 1,061 PASS + 114 foundation PASS | Delegated task 12 NOT_RUN | NOT_RUN_BY_THIS_PACK | FAIL_DEPENDENT_REGRESSION_NOT_RUN |

Pillow/PIL and multipart are absent from the existing backend environment.
The latest observed collection failures and task-12 skip specifically concern
Pillow; do not relabel that skip as the older multipart startup failure. No
dependency was installed or copied in this follow-up. Available alternative
environments do not supply an equivalent complete test environment. Collection
inventories are not executed PASS counts; overlapping regressions are not summed.

Separate historical card-owned PostgreSQL receipts report 08=11, 09=21, 10=14,
11=17, 12=33, 13=11, 14=104 actual cases PASS. They remain separate evidence;
this recheck and follow-up did not run PostgreSQL or a shared 01–14 schema.

The fresh follow-up has 3 migration-graph nodes PASS, 0 SKIP, four guard scenarios
PASS, and Ruff/strict mypy PASS. It is an offline integration-test correction,
not runtime proof or a rerun of the component packs. The frozen foundation
worktree/package are unchanged. Current handoff:
`PRIMARY_SESSION_HANDOFF_20261020.md`.

The older fresh-install suggestion below is historical, not a current
instruction or installation approval. The next executable pack check requires
an authorized existing environment with both Pillow and multipart; while those
dependencies remain unavailable, keep the blocked states and do not install.

## Historical runtime-readiness analysis body — preserved below


## Result

There is **no safe, executable one-shot runtime command for all 14 cards** in the
current candidate. Restoring Lightning supplies a host; it does not supply the
missing owner adapters, adopted policies, HTTP/database composition, selected
providers, or cross-card delivery fences. The only exact remote-runtime package
currently prepared for execution is the frozen BE2-01 A17-fix01 Studio
checkpoint. It is isolated to its named Studio and old foundation base; it is
not the merged BE2-01–14 branch.

This document prepares future commands and gates. Nothing in this analysis
started a Studio, service, database, model, or provider.

The per-card approval and entrypoint audit is also in
`evidence/metrics/BE2_01_14_RUNTIME_READINESS_20261020.json` under
`approved_runtime_entrypoints`: only task 01 has an approved Lightning/Studio
entrypoint; tasks 02–07 have none approved, and tasks 08–14 have approved offline
component runners only. The latter must not be reported as Lightning acceptance.

## Source and authority snapshot

- Integration branch: `feature/be2-backend-ai-integration`.
- Source at the start of this analysis: `d981a248900284c7765c4a179a92c22e4e6feaf4`;
  the merge of the task-7 and task-8–14 histories is
  `abe3c357e2c40c694317ead6cf9a1b7c479e3f6e`.
- The branch is local and has no published cloud checkout. Any future shared
  runtime package must be re-pinned to the final reviewed commit/tree and made
  available to the selected Studio before running it.
- `feature/be2-01-07` equals the task-7 source tip, so task-7 → that branch has
  no reviewable diff.
- BE2-07's owner acceptance is limited to `KNOWLEDGE_SCRIPT_COMPONENT_OFFLINE`.
  It does not accept runtime, provider use, HTTP/SQL adapters, BE2-08 adoption,
  or the BE2-07 card as DONE.
- Current card status, not historical test counts, remains authoritative. All
  BE2 cards retain their existing `IN_PROGRESS` / `IN_PROGRESS_PENDING_EXTERNAL`
  status and open external/runtime gates.

### Stale planning record to reconcile

`features/FEAT-056-be2-knowledge-script/plan/BE2_01_07_RUNTIME_CAMPAIGN_PLAN.md`
still describes BE2-07 as plan-only/no component tests and refers to an older
shared source. Those statements predate the reviewed and owner-accepted offline
BE2-07 checkpoint and this merged candidate. Its warnings about missing runtime
adapters and the frozen A17 boundary remain valid. Before a future shared
campaign is approved, the owner should refresh its source/status rows rather
than treating its old commit pointer or task-07 row as current.

## Card-by-card readiness

| Task | Current offline evidence | Runtime readiness and dependency | Executable next command |
|---|---|---|---|
| 01 — AI job foundation (`FEAT-044`) | Earlier B6 Studio evidence exists; the newer frozen A17-fix01 package has reviewed code/receipt checks. | **A17-fix01 Studio run is NOT_RUN.** Exact named Studio, base HEAD, index/source allowlist, existing PG/Redis/network/venv, and package hashes must match. Real OwnerFence/audit/artifact adoption remains open; a green A17 run closes only its defined checkpoint. | Run only the frozen package procedure in § “BE2-01 A17”. |
| 02 — vision correction (`FEAT-048-be2-vision-correction`) | C1/C2 offline component scope was accepted. | Typed-context serving route/transport and real BE1 context, consent, age, purpose, and revision adapters are **NOT_IMPLEMENTED**. Existing `/v2/vision` forbids extra fields; candidate `/v1/vision/context` is not deployed. | No live BE2-02 command. Do not send typed/child context to `/v2/vision`. |
| 03 — assistance orchestration (`FEAT-049-be2-assistance-orchestration`) | A1 deterministic/offline component evidence exists. | Durable request/receipt/budget/outbox/settlement and real BE1 turn/grant/roster/render plus BE2-14 policy wiring are **NOT_IMPLEMENTED/adoption open**. | No live command until real adapters and durable route are implemented/reviewed. |
| 04 — sketch generation (`FEAT-050-be2-sketch-generation`) | SK1 offline component scope accepted. | Actual provider, model revision, license/cost/profile, decoder, durable staging, cancellation, and post-commit A1 callback path are unselected or **NOT_IMPLEMENTED**. | No provider/GPU command until the runtime decision sheet and implementation are approved. |
| 05 — sketch review (`FEAT-052-be2-sketch-review`) | Review component tests passed offline. | Real moderation/policy, Teacher/consent authority, CMD-60 ticket/gateway, SQL fences and outbox adoption are open. | No integrated review/access command yet. |
| 06 — child response (`FEAT-055-be2-child-response`) | Offline implementation and review evidence exists; integration limits are explicit in its deferred runtime batch. | Real device grant/current-turn/current-disclosure authority, CMD-36 HTTP/auth, durable viewer CAS/history/receipt/terminal marker/outbox, and Teacher delivery are **NOT_IMPLEMENTED/adoption open**. | No live command until the actual adapters and receipt/consumer path exist. |
| 07 — knowledge script (`FEAT-056`) | Owner accepted `KNOWLEDGE_SCRIPT_COMPONENT_OFFLINE`; the final independent review and offline receipts are recorded in FEAT-056. | Real catalog/basis/audience/purpose/Teacher adapters, SQL/outbox, actual 07→08/09 handoff and held fence are open. | No live provider call; source invalidation needs adopted 08/09 consumers and an owned cross-lane checkpoint. |
| 08 — knowledge video (`FEAT-050-be2-knowledge-video`) | Integrated runner: 459 owned + 1,435 regression PASS; 11 SQL cases were collection-only. Its separate owned PostgreSQL receipt reports 11 actual cases PASS. | Actual provider/model/revision/license, profile/encoding/decoder/resource budget, durable staging/copy journal, and real source/consent/policy fences are unselected or open. | Offline command: `python features/FEAT-050-be2-knowledge-video/src/run_component_checks.py`. Live generation remains blocked by the runtime decision sheet and approval. |
| 09 — video review/playback (`FEAT-051-be2-video-review-playback`) | Integrated runner: 458 owned + 1,894 regression PASS; 21 SQL cases collection-only. Separate owned PostgreSQL receipt: 21 actual cases PASS. | Real source invalidation, current access/review/consent, storage gateway/range/resume, 08 producer, and BE1/07/14 adopters remain open. Lightning/provider/BE1/P4 integration is NOT_RUN. | Offline command: `python features/FEAT-051-be2-video-review-playback/src/run_component_checks.py`. No actual playback/consumer proof yet. |
| 10 — video failure disposition (`FEAT-052-be2-video-failure-disposition`) | Integrated runner: 253 owned + 2,352 regression PASS; 14 SQL cases collection-only. Separate owned PostgreSQL receipt: 14 actual cases PASS. | Current authority/session/budget/checkpoint fences, real retry/new lifecycle, and late-result adoption across 01/08/14 remain open. A controlled failed 08 result is needed for the integrated effect path; no provider is required to exercise the local component. | Offline command: `python features/FEAT-052-be2-video-failure-disposition/src/run_component_checks.py`. Actual cross-owner effects remain NOT_RUN. |
| 11 — activity execution (`FEAT-053-be2-activity-execution`) | Integrated runner: 219 owned + 2,605 regression + 25 legacy PASS; 17 SQL cases collection-only. Separate owned PostgreSQL receipt: 17 actual cases PASS. | Real published source/policy/readiness, current BE1 authority, adaptation, outcome sink, event dedup/ACK, and delivery/recovery remain open. No hidden scheduler or auto-achievement is allowed. | Offline command: `python features/FEAT-053-be2-activity-execution/src/run_component_checks.py`. Actual adopter conformance is not implemented. |
| 12 — content publication (`FEAT-048-be2-content-publication`) | Integrated runner collected 477 cases; 476 passed and one route test failed because the current environment lacked declared `python-multipart`. Its separate owned PostgreSQL handoff reports 33 actual SQL cases PASS. | Real BE1 authority/source/review, fixed durable consumer/ACK/dedup, one-router app composition and session-start consistency remain open; default app is not mounted. | Offline command: `python features/FEAT-048-be2-content-publication/src/run_component_checks.py`. Re-run on the final source after the approved environment includes declared dependencies; do not count the old failure as PASS. |
| 13 — preset automation (`FEAT-054-be2-preset-automation`) | Integrated runner: 194 owned + 2,849 regression PASS; 11 SQL cases collection-only. Separate owned PostgreSQL receipt: 11 actual cases PASS; a separately approved 10/11/13 combined SQL run reported 42 PASS. | Real BE1 command/session/receipt, current policy/limits and scheduler dispatch/queue adoption remain open. The handoff says provider/GPU/live-video generation is not required to verify task 13. | Offline command: `python features/FEAT-054-be2-preset-automation/src/run_component_checks.py`. Actual scheduler adoption remains NOT_RUN. |
| 14 — AI policy (`FEAT-049-be2-ai-policy`) | Integrated runner: 1,061 owned + 114 foundation cases PASS; its delegated 477-case regression inherited task-12's environment failure. Separate owned PostgreSQL receipt: 104 actual cases PASS. | Real current-owner/worker/provider dispatch, policy-generation stop fence, kill confirmation, copy lifecycle evidence/adoption, and telemetry source/privacy/expiry adapters remain open. Owned SQL does not need GPU/Lightning. | Offline command: `python features/FEAT-049-be2-ai-policy/src/run_component_checks.py`. No real provider, kill, or copy deletion command is currently authorized/implemented. |

Integrated-runner counts above come from the FEAT-057 matrix. Separate PostgreSQL
counts are the card-owned disposable PG17.11 receipts. They are different scopes:
no shared 01–14 database was run. The current integrated migration graph has nine
heads; do not run a combined migration against a shared/production schema or
invent a merge revision as part of startup recovery.

## BE2-01 A17 — the only prepared remote runtime checkpoint

Use the exact instructions at
`features/FEAT-044-be2-ai-job-foundation/evidence/local/a17fix01-studio-package-20261016/README_STUDIO_RUN.md`
in the task-01 foundation worktree. The local artifact hashes were verified
against that README on 2026-10-20:

- Studio: `sketch2life-backend-test`.
- Studio base: branch `feature/be2-01-ai-job-foundation`, HEAD
  `993a26cae78c0a4fe983033f03881838c886b176`.
- Upload ZIP: `be2-a17fix01-studio-20261016.zip`, SHA256
  `e6ce0192dc4299d08dda84ce3ec4c270334d98490246d226097ccc817b40307d`.
- Entrypoint: `run_a17fix01_on_studio.sh`, SHA256
  `184584274f24b2e1754f8c521c1854a08a4132c69948a75fd53dc6568567fea6`.
- Expected 46-file source manifest SHA256:
  `5b76868d8993284eed548a9db72d3a668b51ff0857aa875697cd2c450e9835d0`.
- Local operator README SHA256:
  `1e921ea7b3d21faca63de59b64379b98c0cf5ff1bba250cc7631c1e1835689ec`.
- The ZIP is available locally under the FEAT-044 ignored `evidence/local/`
  package directory; it is not part of the merged candidate or a published
  branch. The package README, not this summary, is the full operator procedure.

After opening the exact Studio, run only the README's read-only inventory first:

```bash
printf 'studio_home=%s\n' "$HOME"
git -C "$HOME/Sketch2Life" branch --show-current
git -C "$HOME/Sketch2Life" log -1 --oneline
docker ps -a --filter name=sketch2life-be2- --format '{{.Names}} {{.Status}}'
docker network ls --filter name=sketch2life-be2-net --format '{{.Name}}'
docker volume ls --filter name=sketch2life-be2-venv312 --format '{{.Name}}'
test -s "$HOME/.local/share/sketch2life-be2/pg-password" && echo pg_password_file=present
```

If resources are absent, proceed only through the exact reviewed rebuild
procedure in that README, after confirming its script hash and existing password
file. Do not recreate credentials, install packages, pull images, change DB
privileges, or delete volumes. Upload and verify the exact ZIP before extraction;
the script refuses unexpected source states. For the full invocation, preserve
the runner and log exit codes:

```bash
set -o pipefail
bash "$HOME/be2-a17fix01-package/run_a17fix01_on_studio.sh" 2>&1 | tee "$HOME/be2-a17fix01-studio-run.log"
be2_a17_status=("${PIPESTATUS[@]}")
be2_a17_command_exit=${be2_a17_status[0]}
if (( be2_a17_status[1] != 0 )); then be2_a17_command_exit=${be2_a17_status[1]}; fi
printf 'studio_runner_exit=%s\nstudio_log_exit=%s\nstudio_command_exit=%s\n' "${be2_a17_status[0]}" "${be2_a17_status[1]}" "$be2_a17_command_exit"
```

This modifies the frozen Studio source according to its allowlist and runs its
existing Docker/PG/Redis-backed suites. It does **not** test the merged branch or
the missing task-02–14 adopters. Stop on any identity/hash mismatch, missing
prerequisite, failure, skip, missing JUnit/report, or nonzero outer exit; preserve
the attempt and review it before any retry. Keep the complete procedure and
expected case/receipt checks in the linked README.

## Generic Lightning scripts are not a BE2 aggregate runner

- `scripts/lightningai/setup.sh` creates a separate `.runtime/lightning-venv`
  and installs `backend[dev,whiteboard-renderer]`. If this profile is needed,
  it is run on Lightning only and only with the repository's explicit
  `SKETCH2LIFE_ALLOW_INSTALL=1` gate after checking the target environment.
- `scripts/lightningai/verify.sh` checks GPU, existing Wan repo/checkpoint paths,
  runtime inventory, and that V2/video feature flags remain off.
- `scripts/lightningai/run_tests.sh` tests FEAT-018 story-world/whiteboard
  modules. It does **not** run BE2-01–14.
- `tools/start_lightning_vision_v2.sh` starts the existing V2 service and needs
  Lightning-managed `LIGHTNING_DEV_AUTH` plus the configured model mounts. It
  does not call a provider at startup. Its `/v2/vision` request schema forbids
  extra fields; it cannot stand in for BE2-02's unimplemented typed-context
  serving route. Do not pass child identity, age, consent, or typed context to it.

Use these only for the environment/profile they were designed for. They do not
make BE2 runtime gates ready.

## Shared-source offline command set after final source freeze

After the candidate is published or transferred, reviewed, and pinned to a clean
commit/tree, activate the approved existing backend environment and run the
card-owned component runners from the repository root. On Linux the executable
is typically `backend/.venv/bin/python`; each handoff writes its own ignored
`.runtime/` receipt. Run each command separately and retain its full exit/result:

```bash
python features/FEAT-050-be2-knowledge-video/src/run_component_checks.py
python features/FEAT-051-be2-video-review-playback/src/run_component_checks.py
python features/FEAT-052-be2-video-failure-disposition/src/run_component_checks.py
python features/FEAT-053-be2-activity-execution/src/run_component_checks.py
python features/FEAT-048-be2-content-publication/src/run_component_checks.py
python features/FEAT-054-be2-preset-automation/src/run_component_checks.py
python features/FEAT-049-be2-ai-policy/src/run_component_checks.py
```

These are component/regression checks, not live-provider or cross-owner
acceptance. A fresh install may fix the current missing `python-multipart`
environment error, but only a fresh source-pinned passing run can change that
result. The separate card-owned PostgreSQL handoffs are the only authority for
their disposable SQL suites; they require each feature's exact plan/approval,
private test URL/DDL opt-in, generated own database, cleanup verification and
source/JUnit receipts. Do not combine all nine Alembic heads or point the cards
at one shared Studio/production database.

## Dependency-ordered live campaign once implementation exists

This sequence is inferred from the current task plans and handoffs; refresh it
against the actual adopted adapters before execution:

1. Restore and inventory the named Lightning environment; pin exact Studio,
   source, tree, dependency inventory, GPU/model mounts, and synthetic fixtures.
   Run frozen A17 separately and review its source-bound receipt.
2. Freeze a new shared-source package only after runtime adapters, owner contracts,
   provider/model/license/profile choices, and required feature approvals exist.
   The task-01 package is never repurposed for this source.
3. Verify the real current-owner, consent/source/review/policy, and kill/stop
   fences before allowing provider or worker side effects (cross-cutting 01/14
   and BE1 adopters).
4. Exercise the original workflow in dependency order: 01 durable foundation →
   02 vision context → 03 orchestration → 04 generation → 05 review/access →
   06 response/Teacher receipt. At every stage retain exact producer request,
   attempt, output hash, event/ACK, before/after state, and exit/JUnit evidence.
5. Exercise the content/video lane with adopted 07 source/basis and 12 publication
   feeding 08 generation; test 09 authorization/playback on the resulting or
   reviewed library item; inject bounded 08 failure cases into 10 and confirm
   the exact resulting lifecycle without inventing delivery or retry.
6. Exercise 11 activity completion and 13 preset/automation only with actual
   BE1 current authority/source/policy/scheduler/event consumers. Keep 14 policy,
   provider-copy, kill confirmation and redacted telemetry checks as prerequisites
   for any actual provider work.
7. On any code/config/contract/source change, freeze a new source identity and
   rerun the affected suites plus the final required offline batch. Review each
   card's receipts with its owner; aggregate green does not mark a card DONE.

## Stop conditions and evidence

Stop on wrong Studio/branch/HEAD, dirty or out-of-allowlist source, mismatched
hash/manifest, missing environment or secret reference, unsupported capability,
unimplemented adapter, provider/license/profile not approved, migration graph
change, test skip/missing node, JUnit mismatch, or any nonzero nested/outer exit.
Do not retry to fish for a green run or convert missing implementation to
NOT_RUN/PASS.

Preserve raw A17 files under FEAT-044's feature-local runtime evidence. Preserve
each task's component/SQL/runtime receipts under its own FEAT directory and keep
one source-pinned campaign index under FEAT-057. Use synthetic data only; redact
credentials, URLs and private environment details. Keep these states distinct:

- `PASS`: exact required inventory and assertions passed at the pinned source.
- `FAIL`: an executed assertion failed; keep the failing attempt.
- `NOT_RUN`: an implemented check was not executed or was skipped, with reason.
- `NOT_IMPLEMENTED`: the required route/adapter/consumer/effect does not exist.

Neither Lightning recovery nor a green component command is runtime adoption or
full-card acceptance.
