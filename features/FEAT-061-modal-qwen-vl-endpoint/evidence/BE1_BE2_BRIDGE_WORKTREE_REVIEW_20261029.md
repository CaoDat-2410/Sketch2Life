# Read-only BE1-to-BE2 bridge worktree review — 2026-10-29

## Scope and method

The owner supplied Claude's source review of Child UI → BE1 → AI on dev
`529cbef9`. This follow-up inspected the two suggested BE2 worktrees and the
combined integration candidate. It read their AGENTS/context/source-register,
plans/approvals and actual source, and compared existing Git objects. No fetch,
merge, source edit, import/startup, test, database, provider or Modal operation
was performed. Historical test counts below were not rerun.

| Worktree branch | Inspected committed HEAD | Relationship to cached dev `529cbef9` |
| --- | --- | --- |
| feature/be2-02-vision-correction | f120c4fce8f7853e5ab5e061eff4bf916d45603c | Ancestor; relevant vision/correction source is identical in dev |
| feature/be2-03-assistance-orchestration | 113cdf956a09336a0abf5561bd939f5e13b31ea0 | Ancestor; relevant assistance source is identical in dev |
| feature/be2-backend-ai-integration | aa41ed6f481a6d4a797609e588137c94a7c778d7 | Ancestor; integration records preserve runtime/adoption gaps |

The two individual worktrees had no reported working-tree changes under
`backend/src`. None of these committed tips contains a newer, unmerged bridge
that can simply be pulled into the inspected dev baseline.

## Reusable implementation already present

- BE2-02 has actual source/admission/provenance checking and analysis service
  logic, not just empty contracts. It verifies checkpoint/render derivation,
  lineage and context around observation execution. Relevant paths:
  `domain/vision_analysis.py:274`, `application/services/vision_analysis.py:304`,
  `infrastructure/vision_analysis/job_lineage.py`.
- BE2-03 `application/services/assistance.py:270` implements idempotency,
  eligibility/source validation, semantic deduplication, supersession, debounce,
  budget/cache and completion handling. Scheduling at line 631 delegates to
  vision-analysis jobs; completion/revalidation at 914 and `pin()` at 969
  supply useful lifecycle/lineage behavior.
- `infrastructure/assistance/adapters.py:269`, `:316` and `:361` contain
  adapters for AiJobService, scoped analysis outcomes and assistance pins.
- BE1 already has artifact ingress at
  `interfaces/http/routers/be1_artifacts.py:77`, including content hashing and
  contributor/session metadata. It does not itself establish the missing
  checkpoint-to-render derivation binding and trusted BE2 admission.

## Runtime gaps confirmed by source

1. **Trusted drawing input.** BE1 checkpoints store vector/snapshot JSON;
   inspected Child UI utilities build SVG paths. No production canvas-to-image
   producer was found in the inspected path. BE2's `SYNTHETIC_RENDER` and
   dictionary-backed source/render loaders are fixture input, not a renderer
   connected to the classroom canvas. An existing artifact upload alone does
   not bind a raster image to the exact authoritative checkpoint/revision.
2. **Real owner/lifecycle composition.** BE2 services are composed in synthetic
   harnesses over in-memory repositories and fake authority/source/admission,
   context, owner fences, queues/capabilities and fixture policy. The reusable
   services do not replace those missing real adapters or transaction/fence
   coordination. `infrastructure/vision_analysis/harness.py:248` and
   `infrastructure/assistance/harness.py:370` show the composition.
3. **Explicit provider restriction.** `LegacyVisionV2Bridge` rejects
   `UrllibJsonTransport` at `infrastructure/vision_analysis/legacy_v2.py:125`
   with `LiveTransportForbidden`. `OfflineVisionContextAdapter` has the same
   C2 restriction at `context_adapter.py:178`. Do not remove or bypass these
   guards just to make Modal reachable.
4. **Provider contract/capability.** C1 uses image-only `/v2/vision`; C2's
   typed-context adapter targets `/v1/vision/context` with an echo-validated
   wrapper. The current Modal service supplies only `/health` and `/v2/vision`,
   so it does not implement that C2 endpoint. Which capability is required
   must be established against the adopted policy/context contract.
5. **Runtime routing and UI review.** The real classroom/demo router groups
   do not mount the fixture analysis/assistance apps. The fixture apps use
   synthetic `Authorization: Fixture ...` identity mappings. Child UI's
   guidance notice explicitly says BE2/teacher review is not connected, and
   `useReviewStatus.ts` advances to approved with a timer. Mounting fixture
   routers would not supply real authorization, lifecycle or teacher review.

The historical class names containing Lightning are not by themselves the
missing integration. The demo smoke proved that the existing general Vision V2
transport can consume the Modal URL. The BE2 runtime restrictions, trusted
inputs and contract/composition boundaries are the separate unresolved work.

## Approval/evidence boundaries

BE2-02 C1/C2 and BE2-03 A1 approvals are offline/component scopes and explicitly
defer real provider/BE1/runtime adoption. The combined FEAT-057 evidence includes
bounded persisted-flow tests but retains a BE1 handoff marked
`NOT_READY_FOR_BE1_INTEGRATION` and source-fence/adoption gates. The reviewed
persisted BE2-07 → BE2-01 → BE2-08 seam is a video-related scope: neither its
passing test count nor all of its video-specific blockers should be treated as
proof or automatic prerequisites for a newly scoped image-only integration.

The successful FEAT-061 demo-backend smoke does not close those other owners'
gates. This review grants no change to their approvals or status.

## Recommended next bounded planning task

Prepare a source-traced plan for one Child UI drawing → authoritative BE1
checkpoint → image/render binding and admission → BE2 assistance/analysis →
one approved Vision capability → real teacher-review state handoff.

Reuse the implemented services and artifact ingress. Identify exact missing
ports/composition, the image-rendering owner/choice, supported provider context,
and owning-card manifests/authorization before implementation. Separate the
first Vision slice from video, ASR, SAM and later recommendation/Pixi work.
Do not mix BE1 and demo session IDs or label a demo pass as classroom adoption.

This is a planning recommendation, not a source implementation, new model
budget or runtime acceptance. Both tested processes remain stopped at their
last confirmed checkpoint. Existing one-request probe reservation remains used.
