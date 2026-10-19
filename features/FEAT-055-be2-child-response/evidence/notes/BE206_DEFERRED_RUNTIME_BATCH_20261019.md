# BE2-01–06 deferred runtime batch — 2026-10-19

Status: **CHECKLIST_ONLY / NOT_RUN**. Lightning is unavailable. This records future gates under
FEAT-055's approved offline execution; it does not approve runtime implementation, model/provider
use, environment changes, integration, or closure. No A17 package, runtime or model was run or changed.

## Snapshot and execution order

1. Finish and review the 06 offline component on base
   `818ec0778ffb044a77d95c425193f4f02fc3aa44`; record the actual source/test SHA256 manifest,
   interpreter, command, JUnit and exits in FEAT-055. Owner acceptance is still outstanding.
2. When the named Studio returns, inventory it and execute **the frozen A17 package on its own
   accepted base**, following the existing README below. Review the source-bound receipt before
   considering B6-CR01 closure. Cloud PASS does not substitute for this Studio run.
3. Only after the separately approved runtime implementations/adapters and owner contract/policy
   decisions below exist, freeze a **new, separately named shared-runtime snapshot/package**.
   Record its actual commit/dirty-tree manifest, per-feature accepted source hashes, test inventory,
   dependency/environment versions, synthetic fixtures, plan/approval references and package hash.
   Do not put the shared branch into the frozen A17 runner or replace that runner's manifests.
4. Run one source-pinned shared batch in dependency order **01 durable foundation → 02 Vision
   context → 03 orchestration → 04 generation → 05 review/access → 06 response/receipt/Teacher**.
   Independent checks may share the environment, but each stage retains its source identity,
   producer/log exits and raw results. Later stages cannot claim an unadopted prerequisite.
5. Review failures, skips, missing implementation and evidence separately; update each owning
   feature's component/runtime/integration status. A combined green command alone closes no card.

Source: `approvals/TASK_APPROVAL.md`; frozen Rev5 §§2–3, 6–9; FEAT-044
`plan/BE2_ROADMAP.md` §§3–5; FEAT-052 `approvals/COMPONENT_ACCEPTANCE.md`.

## Frozen A17 prerequisite — preserve these bytes

The existing instructions live in the foundation worktree at
`.worktrees/be2-01-ai-job-foundation/features/FEAT-044-be2-ai-job-foundation/evidence/local/a17fix01-studio-package-20261016/README_STUDIO_RUN.md`.
The owning tracked provenance is FEAT-044
`evidence/notes/PHASE_B_B6_A17FIX01_CLOUD_RECEIPT_REVIEW_20261016.md` §§Local validation and next checkpoint / Environment and evidence limits.

| Artifact | Exact SHA256 |
|---|---|
| `be2-a17fix01-studio-20261016.zip` | `e6ce0192dc4299d08dda84ce3ec4c270334d98490246d226097ccc817b40307d` |
| `run_a17fix01_on_studio.sh` | `184584274f24b2e1754f8c521c1854a08a4132c69948a75fd53dc6568567fea6` |
| Final 46-file source manifest | `5b76868d8993284eed548a9db72d3a668b51ff0857aa875697cd2c450e9835d0` |
| Existing environment rebuild script, only under the README procedure | `28950e637d27883bd4df8e5a92a6fc0b6d03284cec0a619a2ca9ce578c4b79d8` |

- Named Studio: `sketch2life-backend-test`; branch `feature/be2-01-ai-job-foundation`;
  exact Studio HEAD `993a26cae78c0a4fe983033f03881838c886b176`; clean index and only
  the permitted source paths. The published Windows/cloud HEAD is not this runner's base.
- Permitted source states: `90724453…` → R2 → A17, `cb527d7f…` → A17, or final
  `5b76868d…` verify-only; verify all 46 hashes. Other bases/states must be refused.
- Inventory existing `sketch2life-be2-pg`, `sketch2life-be2-redis`, `sketch2life-be2-net`,
  `sketch2life-be2-venv312` and the nonempty local password file without disclosing it.
  Use the exact reviewed rebuild procedure only if its hash and existing password prerequisites
  hold; missing resources are not authority to recreate credentials, change DB privileges,
  install dependencies, pull images, delete volumes or create another Studio.
- The ZIP has six flat members; keep the existing ZIP/script unchanged. `--preflight-only`
  changes source before environment checks and ends NOT_RUN/exit 2: it is not a read-only check
  or a runtime PASS. Use the README's full command only in the future authorized execution.
- Expected inventory is 221 B2–B6 cases and 224 Phase A cases, no failure/error/skip;
  fixture 20 PASS / 215 checks / digest `d17f58a3`; G-01–G-04, W01–W12, B-01–B-11 and
  43/43 required durable items PASS. These are expectations, not new results.
- Require source/host identity PASS and every suite/log/outer/Studio exit 0. Preserve raw JUnit,
  reports, logs, source provenance and failed attempts under the foundation's feature-local
  `evidence/local/a17fix01-studio-runtime-20261016/`. A-18 remains DEFERRED;
  A-02/A-19/A-20 NOT_APPLICABLE; B-12 HANDOFF; OwnerFence ASSUMED_CONTRACT.

## Shared-runtime gates, with implementation distinguished from execution

| Stage | Required evidence and prerequisite | Present disposition / authority source |
|---|---|---|
| 01 foundation | Frozen A17 Studio receipt/review first; then source-bound durable migration, restart/recovery, capability, dispatch/outbox and complete collected-case inventory for the new shared snapshot. Real owner fence/audit/artifact integration needs its own adopted contracts. | A17 implementation/package exists; **Studio NOT_RUN**, B6-CR01 open, B-12 HANDOFF. FEAT-044 current CONTEXT/status and A17 receipt review. |
| 02 Vision | Implement/review an adopted serving contract for typed context and its real transport, prompt/model/profile/privacy/quality evidence; real BE1 context/consent/age/purpose/revision adapters and persistence/invalidation evidence. Reject unsupported capability before image load/call; verify serialized minimized fields and source/context/digest/correlation echoes and changed/revoked facts after a call. | C1/C2 accepted **offline**. Typed-context server/real transport are **NOT_IMPLEMENTED**, real serving/model checks **NOT_RUN**. FEAT-048 approved C2 plan §§2–4, 7–9 and C2 acceptance. |
| 03 orchestration | Implement/review durable request/receipt/budget/outbox/settlement and real request-aware fences; wire adopted BE1 identity/device-turn/grant/roster/render/consent and BE2-14 policy/limits/kill switch. Exercise cancel-before/after-create/start/completion, late result, retry and cleanup through durable 01/02; then actual scheduling/API/auth/read-model handoffs. | A1 accepted offline; SQL/RQ/real owner adapters and deployed wiring are **outside implemented A1 scope**, runtime **NOT_RUN**. FEAT-049 approved plan §§8–9, 14; A1 acceptance. |
| 04 generation | Approve/adopt actual model/license/cost/quality/deadline/retry policy; implement real provider/decoder and durable stage integration. Demonstrate actual A1 post-commit callback → `SketchStageAdapter`, exact provenance/negative-case paths, cancellation, unsafe-output quarantine and no source-canvas mutation. | SK1 accepted offline; live adapter/decoder SK-NI01 **NOT_IMPLEMENTED / NOT_RUN**. Preserve **PARTIAL** N04/N08/N11 chain and C03/C03b contract; callback end to end **NOT_RUN**. FEAT-050 SK1 acceptance residual table; FEAT-044 roadmap §4 BE2-04. |
| 05 review/access | Adopt real BE2-14 moderation/reviewer policy/model; wire BE1 Teacher authority/consent and CMD-60 ticket/gateway. Implement/review SQL transaction/fencing/outbox and cross-owner boundary; demonstrate pending/rejected/stale/unsafe/revoked/subset-audience denial and exact proposal/version/hash/review on every content/ticket access after real generation. | Review component accepted offline; real policy/model, authority/ticket, SQL/fence/outbox **not supplied by the component**; runtime/integration **open / NOT_RUN**. FEAT-052 approved plan §§3, 4.10, 6, 8, 11 and component acceptance. |
| 06 response | Adopt real DEVICE grant/participant/current-turn authority and a separate current-disclosure adapter for old-turn receipts; implement CMD-36 HTTP/auth/Idempotency-Key/If-Match mapping, durable viewer CAS/initialization/terminal marker/history/receipt/audit/outbox. Demonstrate new-operation turn checks versus accepted immutable replay after turn closure, current exact05 denial after revoke/rebind/version replacement, viewer isolation, hidden re-view/terminal decline and no canvas/job/provider side effects. Wire real Teacher assignments, delivery/consumer deduplication and current class/session visibility; reauthorize every future content/ticket read. | 06 offline implementation/review in progress; route, durable store, real BE1/P2 authority/disclosure, Teacher broker/assignment/delivery and tickets **NOT_IMPLEMENTED in this scope / NOT_RUN**. No 05→06 or BE1 distributed fence is claimed. FEAT-055 frozen Rev5 §§3–7, OD-04/05/07/08/09. |

### Actual endpoint boundary

`tools/lightning_vision_v2_server.py` exposes **`/v2/vision`** (line 499). Its
`LightningVisionRequestV2` (lines 384–391) and nested
`VisionUnderstandingRequestV2` (`backend/src/sketch2life/contracts/schemas/vision_v2.py:241`)
use **extra="forbid"**. The V2 wire wrapper has its existing optional `narration_context`;
that does not authorize typed context or child context fields.

C2's **`/v1/vision/context`** is a candidate offline client path, not a deployed route.
`contracts/schemas/vision_context.py` explicitly preserves V2 and forbids extras; the
`OfflineVisionContextAdapter` rejects `UrllibJsonTransport` and reports `offline_injected`
capability (`infrastructure/vision_analysis/context_adapter.py:171–193`). Do not insert
`typed_context`, ages, identity, consent or another context envelope into `/v2/vision`,
enable a live transport by removing this refusal, or call a request echo proof of model use.
New serving support and adoption must precede runtime execution.

No executable shared-runtime command is invented here: the required runtime implementations,
adopted contracts and source-bound package do not yet exist. Failed checks stay FAIL;
missing/skipped/unexecuted checks stay NOT_RUN with reasons; missing code stays
NOT_IMPLEMENTED. Offline acceptance does not become runtime/integration acceptance.
