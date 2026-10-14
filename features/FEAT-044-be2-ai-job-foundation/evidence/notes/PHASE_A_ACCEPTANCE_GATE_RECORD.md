# BE2-01 Phase A — acceptance gate record (Q00)

- Date: 2026-10-14, Asia/Saigon. Prepared by Claude (executor) for owner review; **not** an
  approval or sign-off. No message was sent to any owner; no decision is inferred from fixture
  passes or from reviewer agents.
- Scope: BE2-01 Phase A revision 1 (A1–A9) candidate/fixture checkpoint only. Phase B, production
  adoption, live registry, FE/BE1/P4 implementation and production retry/poll numbers are out of
  scope here (A9/A-20 needs cross-review/handoff, not production adoption).
- Code state: final code review PASS at fake/contract scope; R01–R11 and R03a/R04a/A18a CLOSED
  (`PHASE_A_Q00_FINAL_CODE_REVIEW_20261014.md`, sha256 `0dd3e3b7…0dc1fd4`). All 24 source files
  frozen by that review re-hashed unchanged on 2026-10-14 23:25 +07:00.
- Existing decisions searched: FEAT-044 CONTEXT/DECISIONS/tracker/roadmap, project context and
  source register. Found only process decisions (DECISIONS 31–32: owner *may* accept the
  candidate checkpoint with production adoption deferred). **No consumer or owner adoption /
  acceptance decision exists** → every decision cell below is `PENDING_OWNER_DECISION`.
- Named owners: FEAT-044 records P1/FE, P2/BE1, P3/BE2, P4/integration as role owners; actual
  team members are unspecified, so rows name the role. The task owner who approved Phase A
  (approval record) decides overall checkpoint acceptance.

## Evidence anchors (sha256, full values)

| Artefact | Path | sha256 |
|---|---|---|
| DATA-25/CMD-44 schemas | `backend/src/sketch2life/contracts/schemas/ai_jobs.py` | `15025b1386ba2781204ad41655c1dec135b28672845bac1a3744d1b8ad1e9c5f` |
| DATA-24 / copy report / shape specs | `backend/src/sketch2life/contracts/schemas/ai_contract_candidates.py` | `7bbe68aae583f2bf30b62a94108940aa5374ffe2be4a2dbb1d3500331615426c` |
| Ports | `backend/src/sketch2life/application/ports/ai_jobs.py` | `de806e0cc19a275dd584e5a6f1250d8d53c2a899597a07b5b5a2f32dc7a6cbcb` |
| Job service | `backend/src/sketch2life/application/services/ai_jobs.py` | `c6b4f1e1693f4ff87acd933e9b09df1c16100c47734f6890a2b3e931066ef512` |
| Copy lifecycle service | `backend/src/sketch2life/application/services/provider_copy_lifecycle.py` | `c45ad24934b848ce1f4a6357daec925a2e70543d66d5bb8b85cae75a0201d73e` |
| CMD-44 router / fixture app | `.../interfaces/http/routers/ai_jobs.py`, `.../interfaces/http/ai_jobs_fixture_app.py` | `8f90789f…bbc7641b6`, `7ee82e3c…85e6d1d03` |
| Fixture manifest (90 files) | `fixtures/MANIFEST.json` | `245e8b21de0a31d093080056414c880e7cbe279174ee8ec9a524777366360c51` |
| Error catalogue | `fixtures/error_catalogue.json` | `7523377b6f365453de29117bd5594bcb4620193c99e4e13fba9625fdceea057a` |
| P1 consumer example | `fixtures/consumer_examples/p1_job_poll_sequence.json` | `540a618ba41a808143478b61e88f075595aca17633bd96df8498e8c7adea41c9` |
| Candidate spec | `plan/PHASE_A_CANDIDATE_SPEC.md` | `13a0c11ac5c4b82d5ad1c5b26711982a598c31d4b6938c4db43eee8d8deca2b2` |
| Handoff (synced) | `evidence/notes/PHASE_A_HANDOFF.md` | `3f2cd7f19ce941d0d64902fd18f22f10e20bcbd43615bfd9ba97092f9c984a69` |
| Final review runner report | `evidence/raw/codex_q00a_final_runner_report.json` (222 checks, 0 failed, results `d17f58a3…f41f68`) | `b814eb7a68a0da8a04d973bf7236cc2666130fba5599268a3f551d64eeffda19` |
| Final review pytest | `evidence/raw/codex_q00a_final_pytest.txt` (255 passed, 1 skipped) | `2df81e675ff7d5adeb1e55e28393c1e0be6ce38f6d98f96ce2806d209b58cee3` |
| Live-route attempt | `evidence/raw/q00_accept_live_route_attempt.txt`, `metrics/q00_accept_live_route_attempt.json` | see metrics (1 skipped) |

## Gate table

| consumer | contract/port + candidate/version | điểm cần review | compatibility delta | evidence path/hash | quyết định + nguồn/ngày | trạng thái |
|---|---|---|---|---|---|---|
| P1 / FE | `AsyncJobView` + `AsyncJobChildView` `0.1-candidate` (DATA-25 full / Device projection), `CollaborationError` `1.0-proposed`, CMD-44 `GET {prefix}/jobs/{job_id}` | 7 states incl. `succeeded` ≠ Teacher approval/playback/session complete; progress `unknown` value null; refs only `succeeded`+`accepted` (Teacher, current eligibility), never Device; error codes + shared 404 for missing/forbidden; `poll_after_ms` (min 2000 / max 10000 PROPOSED, null = stop); ETag variant incl. role, exposure and poll hint → 304 only when unchanged | Additive; legacy `WorkflowJobV1` and mobile workflow contracts untouched. New fields/codes only under candidate names | Schemas `15025b13…`; P1 example `540a618b…`; error catalogue `7523377b…`; handoff §3 | PENDING_OWNER_DECISION — P1/FE: “Is the candidate payload/state/progress/poll/ETag/error shape acceptable as the Phase A consumer fixture? (production adoption may be deferred)” | PENDING |
| P2 / BE1 | `AuthorizationPort`, `EligibilityPort`, `CancellationNotice`, `ArtifactPort`/`ArtifactDescriptor`, `AuditPort` (ports `0.1-candidate`); `AiJobRepository` boundary requirements | Auth on every command/replay/read before ETag; eligibility reasons and recheck points (create/dispatch/start/retry/completion/exposure); notice idempotency; artifact org + producer lineage (`producer_job_id`/`producer_attempt_id`) + `quarantine_reason`; foreign/unowned never mutated; immutable command and authoritative completion receipts (non-authoritative guard rejections not stored); copy registry `scope_lock` for cancel/register/purge; Phase B unit-of-work needs (jobs CAS, receipts, semantic index, outbox, notices) — **requirements only, no adapter** | New descriptor fields are optional on the candidate DTO; require P2 artifact port to supply lineage/quarantine state. No DB coupling; CMD-59/60 remain BE1 | Ports `de806e0c…`; service `c6b4f1e1…`; copy service `c45ad249…`; handoff §4 | PENDING_OWNER_DECISION — P2/BE1: “Accept these port semantics and required lineage/quarantine fields as Phase A candidates? Record missing BE1/runtime capabilities as Phase B port-review questions; no durable implementation commitment is required for this fixture checkpoint.” | PENDING |
| P4 / integration | Names `AsyncJobView`≙`JobStatusV1`, `CancellationNotice`≙`CancellationNoticeV1`, versions `0.1-candidate`, namespace `/api/collaboration/v1` (B22.1 candidate); `AiJobDependencies` composition pack; runner command | Name/version/namespace compatibility with registry plans; fixture app isolated (`app.py` untouched, AST-checked; live route check pending below); worker path internal, no completion route; one offline runner `run_fixture_contracts.py [--with-http]` | No router mounted in live app; no registry entry written; fakes marked `FIXTURE_ONLY_NOT_DURABLE` | Router `8f90789f…`, fixture app `7ee82e3c…`; runner report `b814eb7a…`; handoff §5–6 | PENDING_OWNER_DECISION — P4: “Accept names/versions/namespace and composition pack as candidates for integration planning; registry adoption deferred?” | PENDING |
| BE2-05 (DATA-24 owner) | `ExactContentReviewCommandV1`/`RecordV1` `0.1-candidate` shape + fixtures | Discriminated session/library context, reason rules, owner retained | Shape only; no review runtime | Contracts `7bbe68aa…`; `fixtures/data24/*` (manifest `245e8b21…`) | Not a Phase A acceptance prerequisite; owner card decides at its own plan. Recorded so ownership stays with BE2-05 | DEFERRED_TO_OWNING_CARD |
| BE2-14 (ProviderCopyLifecycle owner) | `ProviderCopyLifecycleReportV1` `0.1-candidate` + fake support | Fixture deletion never actual (`fixture_deleted_not_actual`), Pending/Unsupported/Exception, scope lock, replay | Fake only; no provider hook | Contracts `7bbe68aa…`; copy service `c45ad249…`; `fixtures/provider_copy/*` | Not a Phase A acceptance prerequisite; owner card decides at its own plan | DEFERRED_TO_OWNING_CARD |
| Live-app route test | `test_live_app_routes_have_no_candidate_job_route` | Must show **1 passed, 0 skipped**, exit 0 | — | `raw/q00_accept_live_route_attempt.txt`; `metrics/q00_accept_live_route_attempt.json`: exit 0, **1 skipped** (Pillow), module origin = worktree, interpreter `<backend-venv>` 3.12.10; no existing interpreter has pytest+FastAPI+Pillow | No owner deviation decision exists → `REQUIRES_LIGHTNINGAI_TEST` (or any existing env with full backend deps). Optional owner question: “Accept a checkpoint deviation (scope: live-route negative check only; risk: candidate route accidentally wired into live app, mitigated by AST check; re-run condition: first env with Pillow)?” | NOT_RUN |
| Phase A checkpoint (task owner) | BE2-01 Phase A rev 1 candidate/fixture checkpoint | A1–A9 candidate implementation/pack delivered; runner A-01..A-20 fixture checks PASS; actual A9/A-20 consumer cross-review remains PENDING in the rows above; code review PASS | Production adoption DEFERRED allowed by DECISIONS 32 | This record; final review `0dd3e3b7…` | PENDING_OWNER_DECISION — task owner: “Accept Phase A at candidate/fixture checkpoint with production adoption deferred, once P1/P2/P4 rows and the live-route row are resolved (or deviated)?” | PENDING |

## What is needed to close Q00

1. P1/FE, P2/BE1, P4 answers to the three questions above (accept / request change), each with
   name, date and source location.
2. Live-route test executed as **1 passed, 0 skipped** in an existing environment that has
   pytest + FastAPI + Pillow (exact command in `metrics/q00_accept_live_route_attempt.json`), or a
   genuine owner deviation decision with scope/risk/re-run condition.
3. Task-owner checkpoint decision. Until then: ACTIVE Q00, Phase A acceptance PENDING, whole
   BE2-01 IN_PROGRESS.

## Codex documentation review clarification — 2026-10-14

Evidence/source hashes independently verified. Candidate consumer review remains pending; the runner's A-20 fixture PASS does not supply an owner sign-off. P2's checkpoint question only asks whether candidate boundary semantics are acceptable; BE1 durable capability/adoption is evaluated separately before Phase B implementation. Handoff wording now distinguishes owned-ref quarantine from stricter output admission (including hash/no-quarantine checks); its evidence hash above was refreshed. No backend source, approval or approved Phase A plan changed; no consumer/owner decision was recorded by this clarification.
