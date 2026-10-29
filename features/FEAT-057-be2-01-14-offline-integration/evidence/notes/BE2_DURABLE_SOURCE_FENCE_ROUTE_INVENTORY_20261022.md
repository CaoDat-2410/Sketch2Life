# BE2 durable source-fence route inventory — read-only

- Date: 2026-10-22 (Asia/Saigon)
- Evidence ID: `E057-SF-INV-20261022-01`
- Prepared by: Codex
- Review status: **NOT_INDEPENDENTLY_COLD_REVIEWED**. The separate Rev5 plan review covered the plan, not this inventory or its companion `BE2_07_01_08_PERSISTED_FLOW_HANDOFF_REV5_DRAFT_20261022.md`.

Scope: BE2-07 → BE2-01 → BE2-08 source-currentness handoff. This inventory separates (1) source-store choices A/B/C, (2) SRS HTTP paths CMD-38–44, and (3) internal persisted lifecycle boundaries A/S/B. A route name, router factory, pin, or row lock does not by itself establish a durable BE2-07 source fence. The route criteria and current lock-path facts needed to read this inventory are summarized below; FEAT-057 Rev5 is cited by hash as provenance only, not as a required attachment. The companion handoff is `features/FEAT-057-be2-01-14-offline-integration/evidence/notes/BE2_07_01_08_PERSISTED_FLOW_HANDOFF_REV5_DRAFT_20261022.md`; its review prompt will pin the final bytes of both documents. Rev5 cold review did not independently review this inventory or the companion handoff.

## Finding

**No durable BE2-07 source-fence route is selected or evidenced end to end in this checkout.** The 9/9 PostgreSQL receipt is bounded evidence for its recorded persisted A/S/B composition. It does not prove that the finalizer holds an authoritative BE2-07 source row through commit. X01 remains `PARTIAL` and the BE1 handoff remains `NOT_SENT / NOT_READY_FOR_BE1_INTEGRATION`.

## Source-store route choices — standalone summary of Rev5 §4

The source-plan path is `features/FEAT-057-be2-01-14-offline-integration/plan/BE2_CROSS_BAND_COMPLETION_PLAN_REV5_DRAFT_20261022.md`, SHA256 `C3B78CD7FA429DD89FE0E46E873A7211D3D85594727467CE224D92057E95A756`; it is a local-only provenance reference, not included in the proposed three-file publication set. The decision criteria below summarize the evidence needed to distinguish the routes.

| Route | Current evidence | Status / gate |
|---|---|---|
| **A — new BE2-07-owned SQL source store** | FEAT-056 currently has an in-memory accepted component; its frozen scope excludes SQL, migrations, HTTP, and durable storage. The knowledge-video migration creates `knowledge_video.run` and `knowledge_video.receipt`, not an authoritative knowledge-source store. | **No implementation evidence for this route.** Required before implementation: producer-owned revised FEAT-056 scope and exact files; additive schema/migration approval if needed; exact BE2-01/08/FEAT-057 scopes and approvals; an owner-approved producer-published function/port/contract or a separately approved architecture exception; same-connection/UoW serialization against invalidation; fail-closed and stale/error outcomes; named adapter owner; exact PostgreSQL 17 least-privilege grants for the selected SQL (including any UPDATE privilege needed by `FOR SHARE`); race evidence. Producer ownership of source writes must remain explicit. If any required decision/evidence is absent, stop without creating the store. |
| **B — existing BE1-owned authoritative store** | The current source register documents BE1 runtime ownership but identifies no store/contract for BE2-07 knowledge-source validity. No producer-published BE1 function/port and same-UoW connection proof for this source fence was found in the reviewed checkout. | **Unidentified here; not disproven in other owner-controlled systems.** Required before implementation: source owner identifies the exact authoritative store and version fields, every invalidation writer, a versioned producer-published function/port/contract that serializes check and invalidation on the exact same finalizer transaction connection/UoW, stale-versus-infrastructure outcomes and fail-closed behavior, accountable adapter owner, exact least-privilege PostgreSQL 17 grants, and evidence/approvals for the exact adapter/test scope. Direct consumer access to BE1-owned tables needs a separately approved architecture exception. A different database or independently managed connection fails the gate. |
| **C — stop at the existing A/S/B composition** | FEAT-057's pinned PostgreSQL 17.11 receipt records 9 passed, 0 failed, 0 errors, 0 skipped for its exact scope/test/log/JUnit. Its source harness is in-memory and its owner fences are fakes; the fence factory ignores the SQL connection. | **This is the only route for which the checkout currently contains evidence; that fact is descriptive, not a recommendation or owner decision.** If the owner selects C, stop durable source-fence work, preserve X01 as `PARTIAL` and BE1 as `NOT_READY`. The receipt is bounded A/S/B composition evidence only; do not call it a durable source fence or a completed BE2-07 → BE2-08 source-currentness seam. |

The choices above are not owner decisions. No route was selected by this review. `OwnerFenceV1/0.1-candidate` remains `ASSUMED_CONTRACT` until the accountable producer/consumer owners adopt it.

## SRS HTTP path inventory

The canonical SRS labels these routes proposed contracts. The default FastAPI composition in `backend/src/sketch2life/interfaces/http/app.py` does not register the candidate router factories below.

| Contract | SRS path | Current route evidence | Durable source-fence evidence |
|---|---|---|---|
| CMD-38 | `POST /knowledge-bundles` | SRS B22.2 proposes the command. No HTTP route for this path was found under `backend/src/sketch2life/interfaces/http`; FEAT-056 exposes a synchronous application service with an in-memory fixture repository. | **None durable.** The fixture coordinator serializes only within one process. |
| CMD-39 | `PATCH /knowledge-bundles/{bundle_id}` | SRS B22.2 proposes versioned edits. No matching HTTP path was found under `backend/src/sketch2life/interfaces/http`; current service/fake persistence is the same FEAT-056 offline component. | **None durable.** Edit/currentness behavior in the accepted component is not a SQL source-owner fence. |
| CMD-40 | `POST /knowledge-videos` | `build_knowledge_video_router` in `backend/src/sketch2life/interfaces/http/routers/knowledge_video.py` defines candidate `/api/collaboration/v1/knowledge-videos`; that module says the production app does not register it. `VideoCreateService` in `backend/src/sketch2life/application/knowledge_video_create.py` validates the exact pin and calls `lease.assert_current()` before and after submission; its code states that the atomic adapter must enforce the guards before commit. | **No durable BE2-07 fence.** The current BE2-07 resolver uses the process-local coordinator; the post-submit check cannot repair a bad durable commit. |
| CMD-41 | `POST /knowledge-videos/{video_id}/reviews` | Candidate factory exists in `backend/src/sketch2life/interfaces/http/routers/video_review.py`; it is not mounted by the default app. | Adjacent exact-review boundary, not evidence of a BE2-07 source fence. X05d remains `BLOCKED`. |
| CMD-42 | `POST /knowledge-videos/{video_id}/playback` | Candidate factory exists in `backend/src/sketch2life/interfaces/http/routers/video_review.py`; it is not mounted by the default app. | Adjacent playback boundary, not evidence of a BE2-07 source fence. X05d remains `BLOCKED`. |
| CMD-43 | `POST /knowledge-videos/{video_id}/failure-dispositions` | Candidate factory exists in `backend/src/sketch2life/interfaces/http/routers/video_failure.py`; it is not mounted by the default app. | F is outside the adopted A/S/B scope; no full-lifecycle fence claim follows. |
| CMD-44 | `GET /jobs/{job_id}` | Candidate factory exists in `backend/src/sketch2life/interfaces/http/routers/ai_jobs.py`; the only registration found is `backend/src/sketch2life/interfaces/http/ai_jobs_fixture_app.py`. | A scoped job-status read does not check/hold the authoritative knowledge source through video finalization. |

`backend/src/sketch2life/interfaces/http/routers/learning_content.py` supplies a candidate `/governance/records` route; it is not CMD-38/39's `/knowledge-bundles` path. Candidate route declarations are not treated as routes in the current production application.

## Persisted internal lifecycle boundaries

Current lock-path summary: A holds authorization/eligibility admission fences before job/run creation; S locks job → holds eligibility → starts/touches the video run; B locks job → holds eligibility and artifact fences → accepts/touches the video run. None of these paths currently holds an authoritative BE2-07 source-fence row. D1's future job → run → canonically sorted source-fence order is owner direction, not current behavior; the D1 record is `features/FEAT-057-be2-01-14-offline-integration/evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D1_20261021.md`. The aggregate test edge registry is `backend/tests/integration/be2_cross_lane/edge_registry.py`; it is not a runtime registry. F (fail/cancel/timeout/retry/reject) is outside the adopted A/S/B approval and is not claimed as implemented or source-fenced.

| Boundary | Read-only code evidence | What is held today | Source-fence conclusion |
|---|---|---|---|
| **A — submit** | `backend/src/sketch2life/application/services/ai_jobs.py:440`; `backend/src/sketch2life/application/knowledge_video_create.py:98–107`; `features/FEAT-050-be2-knowledge-video/plan/CROSS_LANE_BE2_08_SCOPE_REV3_DRAFT_20261021.md` §3. | BE2-01 holds authorization and eligibility fences before the job/run participant writes. The video creation lease is a separate logical guard outside A. | No BE2-07 source row is shown as held in the BE2-01 UoW. |
| **S — start** | `backend/src/sketch2life/application/services/ai_jobs.py:754–763`. | Job is locked; eligibility fence is held; BE2-08 run is then started in the same transaction. | Held eligibility is not the BE2-07 source-currentness fence. Current order differs from D1's future job → run → source-fence order. |
| **B — accepted finalization** | `backend/src/sketch2life/application/services/ai_jobs.py:844–877`; `backend/src/sketch2life/infrastructure/knowledge_video/foundation_lifecycle.py:accept`. | Job is locked; eligibility and artifact fences are held; the BE2-08 run is accepted and saved in the transaction. | No authoritative BE2-07 source row is held at finalization in the inspected path. The 9/9 receipt does not change this. |
| **F — fail/cancel/timeout/retry/reject** | Owner D1 direction and current `BE2-VIDEO-LIFECYCLE/1` approval records; the approved scope is A/S/B plus identity-failure behavior. | F is outside the adopted A/S/B scope; no full-lifecycle F behavior or source-fence row is claimed here. | No full-lifecycle source-fence claim is available. Separate contract/review/approval required. |

## Fixture-only SQL fence evidence

`backend/src/sketch2life/infrastructure/ai_jobs/sql/owner_fence_fixture.py` contains `FixtureFenceHold` and `OwnerFixture`. It uses a synthetic disposable `owner_fence_fixture` schema; the BE2-side fixture uses `SELECT ... FOR SHARE` on a supplied SQL connection and the owner stand-in changes the row under `FOR UPDATE`. The file labels the contract `ASSUMED_CONTRACT`, states it is not a P2 adapter, live-app binding, or Alembic revision, and restricts fixture DDL to disposable test databases.

This is evidence that a test fixture expresses a same-connection row-lock protocol. It is **not** evidence of a BE2-07-owned authoritative source row, adopted contract, production adapter, or integration into the current 9/9 flow. The latter uses test-local `_FenceHold(FakeOwnerFences)` and an in-memory knowledge harness. No test was run for this inventory.

`backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py` accepts an `owner_fences` factory per SQL transaction, but its class documentation says there is no production binding until the real P2 adapter exists (B-12). The reviewed candidate tree supplied no production binding for BE2-07 source currentness.

PostgreSQL 17 documents that `SELECT ... FOR SHARE` needs `SELECT` plus `UPDATE` on at least one column ([Privileges, §5.8](https://www.postgresql.org/docs/17/ddl-priv.html)). If a row-lock route is later selected, the exact least-privilege grant and owner boundary must be reviewed; this turn did not connect to a database or inspect live grants.

## Evidence and captured source hashes

Repository references below were read from branch `feature/be2-backend-ai-integration`, HEAD `af3e28fc402f69e5a10ba55a54631c5d1f995a50`. Hashes bind the inspected bytes for this inventory; they are not production acceptance claims.

| Input | SHA-256 |
|---|---|
| FEAT-057 Rev5 plan (provenance only; not in the proposed three-file publication set) | `C3B78CD7FA429DD89FE0E46E873A7211D3D85594727467CE224D92057E95A756` |
| FEAT-057 PostgreSQL 17 receipt note — `features/FEAT-057-be2-01-14-offline-integration/evidence/notes/BE2_01_07_08_POSTGRESQL17_FLOW_TEST_20261022.md` | `C035D8F951145A2539139CCB8955F6CACAA7B79C56BC2871A5310A3BF624316F` |
| FEAT-057 PostgreSQL 17 metrics — `features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/BE2_01_07_08_POSTGRESQL17_FLOW_TEST_20261022.json` | `AC0B54FBEA0E1DC4CF598D361C6BDE76EDD37B781FC2A40C33B2F227D42C6D5C` |
| FEAT-057 persisted-flow test — `backend/tests/integration/be2_cross_lane/test_persisted_video_worker_flow.py` | `C18D6FD373F83C617B0FF470DC523C99E3A5EDB5B0D2DF1A040ECC0E6F7E67ED` |
| Canonical SRS v3.1 — `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md` | `A95C89589843E3555E967C5E486F3BCAF4BBDF9446CB3BC9C49ED16F672964D9` |
| FEAT-056 task approval — `features/FEAT-056-be2-knowledge-script/approvals/TASK_APPROVAL.md` | `410295D02552A02D98358C122AFD19B3CE4B5A9A006B875EA5F8970A5B7B37C9` |
| FEAT-044 Phase B task approval — `features/FEAT-044-be2-ai-job-foundation/approvals/PHASE_B_TASK_APPROVAL.md` | `885D51F7C80A9EB86A60E3F0FCC415DEF4B72E4FBD49E9C467CFB7F06C42FE44` |
| FEAT-050 task approval — `features/FEAT-050-be2-knowledge-video/approvals/TASK_APPROVAL.md` | `DB7FEC36F5E3EAB9E7CCBA6E2718890A491D9978CA304EF49D988C78E0A476A1` |
| FEAT-057 task approval — `features/FEAT-057-be2-01-14-offline-integration/approvals/TASK_APPROVAL.md` | `10CC6F9F752E80927F98C6418E79201D9B22E740F26BA9BCE5C9FEC699800ABB` |
| FEAT-050 scope Rev3 — `features/FEAT-050-be2-knowledge-video/plan/CROSS_LANE_BE2_08_SCOPE_REV3_DRAFT_20261021.md` | `66C614FF268E418F27FA4923FB7272A845F7BC7DA8BB225B8CD10032D364F801` |
| FEAT-056 component acceptance — `features/FEAT-056-be2-knowledge-script/approvals/COMPONENT_ACCEPTANCE.md` | `54DAE2F93414116C03AA7EFE2E7110B2AB3E20CE409D3E829C876DA62990326A` |
| `backend/src/sketch2life/application/services/ai_jobs.py` | `15DCD532D56EFF811A7DE937938E8D5F942AC7B29CDE26043A3B572DB02E08AE` |
| `backend/src/sketch2life/application/knowledge_video_create.py` | `FE330D4D4CE642515158F36DE9DEC60CADBD9EB8C56F02834C5FBC2AC1F8B347` |
| `backend/src/sketch2life/infrastructure/cross_lane/knowledge_script_video.py` | `0A22E50557B3AC57B9913B80B273D0A672423946277AF3E7CFA9A0829E7F6F42` |
| `backend/src/sketch2life/infrastructure/knowledge_bundle/fakes.py` | `EDEB15A8E25027D8167FA5F9D75C23FB8160318CAE037CDC8476AD41E3CD95FA` |
| `backend/src/sketch2life/infrastructure/knowledge_bundle/coordination.py` | `CBE5467F2463197307EEF7F3BA0616392272CA032A7FDCE1716752E318AC6C53` |
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/owner_fence_fixture.py` | `F12560D8F68EA31C5F76BB10E0452310CFF019C3D2DF5A90D8970889D052EC92` |
| `backend/alembic/versions/20261018_kv_0001_knowledge_video.py` | `E7EFE124ECBFC5D1E280529DBA3B05EB2B00DCE04C24BF9EAC11BCE516B15D87` |
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py` | `07695F0E6817B1057A38482D2D869D871A77CE77594D170642C00EBC2709724A` |
| `backend/src/sketch2life/infrastructure/knowledge_video/foundation_lifecycle.py` | `58BCDFB9E3C009BB4931E61FEAB8E5CE67B74881BAB1F4965CB83CFC0BBB9AAF` |
| `backend/src/sketch2life/interfaces/http/app.py` | `BF1258B20A0086C14612D6A1C358751D2E8EE151676B28FC7C352096AD834A18` |
| `backend/src/sketch2life/interfaces/http/routers/knowledge_video.py` | `E61E30F815E54EEDFBCF4479196B0113F83A9BA3B4505625925DF14474A4E8AE` |
| `backend/src/sketch2life/interfaces/http/routers/ai_jobs.py` | `8F90789FE6BC5ABBD5B1F2D489C201DD99DEF252AD2182D591A2BECBBC7641B6` |
| `backend/src/sketch2life/interfaces/http/routers/video_review.py` | `2E5B1FED880BC804FF45F87F286294DBAB68ABA17BD693AE04418EE498E011B3` |
| `backend/src/sketch2life/interfaces/http/routers/video_failure.py` | `7047BFFC3B9451ABC9241F71D9DE9307772A3CDF53831D84EA076BD17E5D4522` |
| `backend/src/sketch2life/interfaces/http/routers/learning_content.py` | `BAAF4D0A0F9FA56CB4AD9BA96B63EB6396C2B992B58A8B5CE3DF8D7F28CEE4C0` |
| `backend/src/sketch2life/interfaces/http/ai_jobs_fixture_app.py` | `7EE82E3C80D3BA892B9B532961786832F747CF1A627A245CB20C90D85E6D1D03` |

Evidence commands: `git rev-parse HEAD`, `git branch --show-current`, `git status --porcelain=v1`, `git diff --cached --name-only`, `rg -n`, `Select-String`, `Get-Content -Encoding UTF8`, and `Get-FileHash -Algorithm SHA256`. Environment: Windows PowerShell; read-only repository inspection plus read-only access to the linked PostgreSQL documentation. No tests, database, server, provider, or runtime were used.

## Follow-up and authority

Keep X01 `PARTIAL`, X05d `BLOCKED`, X05c/CR09-02 `OPEN`, aggregate X09 `NOT_IMPLEMENTED`, and BE1 `NOT_SENT / NOT_READY_FOR_BE1_INTEGRATION`. Before implementation, the source owner and affected card owners must choose Route A or B (or explicitly stop at C), adopt the versioned producer-published contract, approve exact source/test/migration manifests, resolve PostgreSQL grants, and authorize race evidence. This inventory makes none of those decisions and does not edit source, tests, schemas, migrations, approvals, or card status.

