# FEAT-030 Original-derived Pixi auto-rig plan

- Status: REVISION 4 IMPLEMENTATION IN PROGRESS — LIVE ACTIVATION BENCHMARK-GATED
- Plan revision: 4
- Implementation status: REVISION 3 PART-AWARE LOCAL BASELINE IMPLEMENTED; REVISION 4 SAM2.1 CONTRACT/ADAPTER/WORKER PATH IMPLEMENTED; GPU BENCHMARK PENDING
- Supersedes: no approved feature; it expands beyond the draft FEAT-018 visual-quality plan
- Planning date: 2026-09-25 (Asia/Saigon)

## 1. Outcome

Build an optional preparation and rendering path that preserves the child's exact drawing while creating visible, subject-specific 2D motion. The system will localize the already-confirmed subject, derive a validated mask and rig, choose a bounded motion profile, and load it in PixiJS through versioned contracts. If any stage is uncertain, slow, unsupported, or invalid, the flow degrades deterministically and remains usable.

The target journey is:

```text
OriginalDrawing + CanonicalUnderstanding + approved experience
  -> subject target
  -> spatial grounding
  -> segmentation and mask cleanup
  -> archetype and keypoints
  -> mesh + skeleton + weights
  -> rig validation
  -> bounded motion profile
  -> RiggedArtworkPackageV1
  -> VisualAnimationPlanV2
  -> RendererLoadCommandV2
  -> PixiJS CPU mesh deformation
```

This feature does not redraw the image or replace the future educational video. The planned sequence remains Pixi exploration → video when available → off-screen activity.

## 2. Product invariants

1. `OriginalDrawing` is immutable and always recoverable.
2. Gate A owns meaning; the rig pipeline cannot select a contradictory subject.
3. Gate B owns the approved experience; motion planning cannot replace the activity or learning objective.
4. Derived pixels may come only from the original drawing through recorded deterministic/model-assisted transformations.
5. No model/provider call originates from mobile or the renderer.
6. No failure in preparation, package fetch, validation, or playback may fail the supervised session.
7. Unsupported or uncertain actions fall back; the system does not invent flight, walking, speech, or object interaction.
8. Old clients and V1 launch commands continue to work during migration.
9. Supplemental catalog assets are optional decoration and remain subject to FEAT-028 approval. They are never merged into the child-authored subject texture.
10. Retry is idempotent and never creates an unbounded job/model loop.

## 3. Current end-to-end call graph

```text
ExperienceReviewScreen.approveAndContinue
  -> AppContext.approveActivity
  -> POST approve Gate B
  -> supervised_flow.approve_gate_b
  -> P1ExperienceCompiler.approve_gate_b
  -> session = EXPERIENCE_READY
  -> navigate pixi_intro

PixiIntroScreen
  -> AppContext.prepareRendererIntro
  -> demo API POST /renderer/launch
  -> supervised_flow.prepare_renderer
     -> load ExperienceSpec + RawUnderstanding + AnchorSet
     -> build_subject_candidates
     -> build_scene_exploration_plan
     -> build_scene_focus_plan (normally fallback; localizer disabled)
     -> issue original-source capability
     -> create ArtAnimationPlanV1 + PixiArtAssetManifestV1
     -> return PixiRendererLaunchV1
  -> WebView /renderer/mobile.html
  -> RendererLoadCommandV1 via postMessage
  -> fetch original source with capability
  -> createBrowserArtPlayer
  -> Pixi Sprite(s) + GSAP V1 motion
  -> INTRO_COMPLETED bridge event
  -> future video placeholder
  -> completeActivityHandoff
```

## 4. Target call graph

The owner-approved design separates preparation from business state and starts safe preprocessing after Gate A:

```text
Gate A confirmed
  -> enqueue spatial-preparation job early
     -> target derived from CanonicalUnderstanding
     -> grounding + segmentation + cleanup
     -> store ORIGINAL_DERIVED artifacts and provenance

Gate B approved
  -> compile exact motion context from ExperienceSpec
  -> continue/start AutoRigJobV1
     -> archetype -> keypoints -> mesh -> bones -> weights
     -> validate -> choose tier/fallback
     -> store RiggedArtworkPackageV1

Pixi intro opens
  -> GET job status / bounded wait with progress labels
  -> POST /renderer/launch-v2
     -> if valid rig ready: issue package/source capabilities
     -> if partial: issue cutout or bbox V2 plan
     -> if timeout/failure/old client: return/use V1 launch
  -> RendererLoadCommandV2 via bridge (references only)
  -> renderer fetches package/artifacts by short-lived capability
  -> validate hashes/schema/bounds
  -> build Pixi Mesh + bone graph
  -> GSAP updates bone parameters; CPU skinning updates vertices
  -> semantic events/progress
  -> completion remains local until user continues
```

Gate A preprocessing may produce only spatial and original-derived artifacts. It cannot publish a renderer launch, select activity-specific motion, or bypass Gate B.

## 5. Gap analysis

| Concern | Classification | Current state | Planned change |
|---|---|---|---|
| Gate A/B authority | REUSE | Established in supervised flow | Consume only; add no competing semantic decision |
| Session state | REUSE | `EXPERIENCE_READY` after Gate B | Keep state; expose independent media job status |
| Job protocol/store | EXTEND | Generic `WorkflowJobV1` and `JobStore` exist | Add typed `AutoRigJobV1`, stage/progress/failure metadata, retry/idempotency |
| Original artifact storage | EXTEND | Artifact store and source capability exist | Add typed derived artifacts and package grants |
| Target selection | NEW MODULE | Candidate subjects exist, no rig target policy | Deterministic selection from selected canonical subject and confidence |
| Spatial grounding | REPLACE/NEW ADAPTER | Optional unstable Qwen localization, disabled | Replaceable grounding port; never automatic semantic rerun |
| Segmentation | NEW MODULE | None | Replaceable adapter plus benchmark gate |
| Mask cleanup/quality | NEW MODULE | None | Pure validation/cleanup stages and typed reasons |
| Archetype classifier | NEW MODULE | None | Rule/registry-first classifier, bounded allowlist |
| Skeleton/keypoints | NEW MODULE | None | Archetype templates fitted to validated geometry |
| Mesh generation | NEW MODULE | None | Bounded triangulation with deterministic limits |
| Skin weights | NEW MODULE | None | Deterministic distance/region weighting, normalization checks |
| Rig validation | NEW MODULE | None | Geometry, weights, deformation and semantic safety gates |
| Motion DSL | EXTEND | Sprite V1 operations | V2 semantic bone/parameter tracks; V1 unchanged |
| Renderer package | NEW CONTRACT | Original/crop V1 manifests | Capability-referenced rig package and artifacts |
| Pixi runtime | EXTEND | Sprite + GSAP | V2 mesh scene, CPU skinning, progress, disposal, fallback |
| Mobile WebView | EXTEND | V1 command/events | Discriminated V1/V2 command, preparation states, retry/fallback UX |
| Bridge size | REPLACE V2 STRATEGY | 4096-byte command envelope | Keep command small; fetch package out-of-band |
| Asset governance | EXTEND | Approved generated/supplemental assets | Add `ORIGINAL_DERIVED` provenance/integrity policy |
| Cache | NEW MODULE | No rig cache | Source+target+pipeline-version keyed result cache |
| Golden corpus | NEW MODULE | V1 golden scenes only | Authorized drawings, masks, expected tier, motion and negative cases |
| Exact model/library | UNKNOWN | Not installed/frozen | ADR after benchmark; no domain coupling |

## 6. Contract design

All contracts are additive, versioned, bounded, and mirrored in Python/Zod. Free-form executable expressions are forbidden.

### 6.1 `RigPreparationRequestV1`

Required fields:

- `sessionId`, `requestId`, `sourceArtifactRef`, `sourceSha256`.
- `canonicalUnderstandingRef` and `experienceSpecRef` or immutable snapshots/hashes.
- `target`: canonical entity ID, normalized label, confidence, optional relation/action hints.
- `learningObjectiveId`, `selectedActivityId`, `maxMotionLevel`.
- `pipelineVersion`, `requestedTiers`, deadline and idempotency key.

Validation:

- target must exist in the approved canonical result;
- experience hash must match the approved Gate B record before motion compilation;
- no raw image bytes, model credentials, prompt, or arbitrary motion code.

### 6.2 `AutoRigJobV1`

- Status: `QUEUED | RUNNING | SUCCEEDED | PARTIAL_SUCCESS | FAILED | EXPIRED`.
- Stage: `TARGETING | GROUNDING | SEGMENTING | CLEANING | ARCHETYPE | RIGGING | VALIDATING | PACKAGING`.
- Progress is monotonic and accompanied by a child/parent-safe display key.
- Attempt count is bounded; each failure contains internal reason code, retryability, and public message key.
- Result is a package reference/tier, never inline artifact bytes.

### 6.3 `SegmentationArtifactV1`

- source and target hashes;
- normalized region/bbox;
- mask artifact reference, dimensions, encoding, alpha semantics;
- confidence plus quality metrics: area ratio, connected components, boundary score, clipping flags;
- grounding/segmentation/cleanup adapter and version provenance;
- validation status and rejection reasons.

### 6.4 `RigDefinitionV1`

- coordinate system and source dimensions;
- bounded vertices, triangles, UVs;
- bones with stable IDs, parent relation, rest transform and constraints;
- normalized per-vertex influences with a small maximum count;
- archetype, pivots, semantic regions and allowed parameters;
- no scripts, shaders, URLs, or arbitrary expressions.

Initial hard limits are provisional and benchmarked before approval: vertex/triangle count, bones, influences per vertex, texture dimensions, serialized bytes, and coordinate range.

### 6.5 `RigValidationResultV1`

- geometry integrity: bounds, duplicate/degenerate triangles, winding, disconnected regions;
- weights: finite, normalized, allowed bone IDs;
- deformation probes: fold-over, stretch, clipping, edge preservation;
- semantic safety: profile allowed for subject/archetype/context;
- selected delivery tier and fallback reason;
- validator version and metrics.

### 6.6 `RiggedArtworkPackageV1`

- package/schema version, source hash and derivation graph;
- selected tier: `FULL_AUTO_RIG | CUTOUT_MICRO_MOTION | BBOX_VISUAL_FOCUS | WHOLE_DRAWING_V1`;
- references and hashes for texture/mask/optional background patch;
- optional validated `RigDefinitionV1`;
- capabilities required, byte sizes, expiry/cache metadata;
- provenance for every derived artifact;
- package is immutable and content-addressed.

### 6.7 `VisualAnimationPlanV2`

- semantic timeline of intro, focus, motion, settle and learning bridge beats;
- typed tracks target bone IDs or allowlisted parameters such as bend, breathe, flutter and sway;
- duration/easing/amplitude/repetition are bounded;
- each motion records evidence source: observed action, relation, archetype-safe idle, or learning bridge;
- unsupported profile results in a lower tier, never guessed custom motion;
- no narration/video coupling is introduced here.

### 6.8 `RendererLoadCommandV2`

Keep the WebView message small:

- command/version, session/launch IDs;
- package read endpoint + short-lived capability;
- original-source endpoint/capability for recovery;
- expected package/source hashes;
- compact animation plan or plan endpoint, depending measured size;
- fallback V1 launch reference or enough data to request it;
- expiration, renderer compatibility range and correlation ID.

Mesh data, masks and textures are not inlined in the bridge message.

### 6.9 Events

Add typed events while retaining V1 events:

- `RIG_PREPARATION_PROGRESS`, `RIG_TIER_SELECTED`, `RIG_PACKAGE_LOADED`.
- `RIG_VALIDATION_REJECTED`, `RIG_FALLBACK_APPLIED`.
- `V2_PLAYBACK_STARTED`, `V2_PLAYBACK_COMPLETED`, `V2_PLAYBACK_FAILED`.

Public payloads contain safe message keys. Internal reasons and stack traces stay in structured backend/renderer logs.

## 7. Architecture and module boundaries

### 7.1 Domain/application

Pure policy and orchestration, with no FastAPI, Pixi, SAM, Torch, Redis, or provider imports:

- target selection and confidence policy;
- motion safety and archetype profile registry;
- mask/rig validation interfaces and deterministic rules;
- fallback tier selection;
- derivation/provenance records;
- auto-rig job orchestration and idempotency.

### 7.2 Ports

Introduce replaceable ports for:

- `SpatialGroundingPort`;
- `SegmentationPort`;
- `GeometryRiggingPort` only if numerical implementation cannot remain pure application code;
- `DerivedArtifactStore`/capability issuer;
- `AutoRigJobStore`/executor;
- clock, metrics and tracing.

Adapters return normalized local contracts. Provider-specific output never crosses into domain policy.

### 7.3 Infrastructure

- model adapters and preprocessing;
- optional L4 worker/queue;
- image/mask encoders;
- numerical geometry implementation;
- content-addressed storage and TTL grants;
- cache keyed by source hash + target + pipeline/config versions.

### 7.4 Renderer

- package loader and integrity validator;
- V2 scene graph and mesh builder;
- bone transforms and CPU skinning;
- motion profile executor driven by GSAP parameters;
- resize/orientation/disposal support;
- debug overlay available only in development;
- V1 player remains untouched behind command discrimination.

## 8. Candidate pipeline

### 8.1 Target selection

Use the one adult-confirmed canonical subject. If no single subject is approved, choose no rig target and fall back. Do not use a full descriptive sentence as the target and do not run another semantic candidate-selection prompt.

### 8.2 Grounding

Ground the canonical label and optional relation hints against the source. The adapter must return normalized boxes/points with confidence and image dimensions. Multiple conflicting regions, tiny regions, out-of-bounds coordinates, or low confidence are rejected.

### 8.3 Segmentation and cleanup

Segmentation consumes the source plus validated spatial prompts. Cleanup is bounded: threshold, hole handling, connected-component filtering, small edge smoothing and alpha feathering. It cannot paint a new subject.

Quality gates include plausible area, border clipping, fragmentation, target-point containment, and optional agreement across prompts. The unmodified raw mask is retained alongside cleaned derivatives for evidence.

### 8.4 Archetype and rig fitting

Start with template rigs rather than unconstrained skeleton inference. The first production registry covers `butterfly`, `bird`, `flower`, `tree_branch`, `fish`, `biped`, `rigid`, `generic_organic`, and `unknown`. Each archetype declares expected parts, minimum geometry, permitted bones, pivots, motion profiles and rejection rules. Unknown or poor-fit subjects select a lower tier.

The registry is open for versioned expansion, while runtime resolution is closed and deterministic. Canonical labels and aliases map to the nearest supported family only when confidence and geometry agree. Otherwise:

- deformable living or natural forms use `generic_organic` with subtle bounded motion;
- hard or man-made forms use `rigid` with focus/camera motion;
- unclassifiable forms use `unknown` and downgrade to bbox or whole-drawing presentation.

This supplies a safe result for all topics without inventing anatomy or claiming a specialized rig where none is justified.

### 8.5 Mesh and weights

Generate a bounded interior mesh from the validated mask, preserving silhouette samples and reducing interior density. Fit bones to stable keypoints/pivots. Calculate deterministic normalized weights with a maximum influence count. Reject NaN, degenerate geometry, extreme stretch or fold-over in probe poses.

### 8.6 Background handling

- For internal deformation and subtle pivot motion, keep the source image behind the subject and limit displacement to avoid obvious duplication.
- For larger translation, require a validated deterministic background patch derived from surrounding source pixels.
- No generative inpainting in this feature revision.
- If ghosting remains visible, downgrade to bbox focus or whole-drawing V1.

### 8.7 Motion planning

Motion profiles are allowlisted by archetype and evidence. Examples for MVP:

- butterfly: subtle paired-wing flutter and body bob only when the butterfly is the selected subject;
- bird: breathing/head tilt/perch sway; flight requires explicit observed or approved narrative evidence and is outside default level 2;
- flower: stem/leaf sway and bloom emphasis, not invented growth;
- generic organic: tiny breathe/sway;
- rigid: camera/focus only.

Amplitude, speed, repetitions and total duration are bounded. Final pose settles close to the source composition.

## 9. API and orchestration plan

Additive endpoints proposed for review:

- `POST /v1/sessions/{session_id}/auto-rig/jobs` — idempotent enqueue/continue.
- `GET /v1/sessions/{session_id}/auto-rig/jobs/{job_id}` — bounded status/progress.
- `POST /v1/sessions/{session_id}/renderer/launch-v2` — returns a V2 launch when compatible/ready or a typed fallback instruction.
- `GET /v1/renderer/rig-package` and derived artifact endpoints — capability protected, hash checked, session scoped, limited reads and TTL.

The existing `/renderer/launch` V1 endpoint remains unchanged for old clients and rollback. A later approved migration may return a discriminated union from one endpoint only after compatibility evidence.

Retry rules:

- same idempotency key returns the same active/completed job;
- one automatic retry only for explicitly retryable infrastructure errors;
- model/quality rejection immediately downgrades instead of looping;
- parent retry creates a new bounded attempt linked to the original;
- app loading has a maximum wait budget, after which it offers/uses fallback without exposing technical codes.

## 10. Mobile and UX plan

The landscape full-screen Pixi screen remains the playback surface. Loading becomes meaningful rather than a frozen player:

- stage labels such as “Đang tìm nhân vật trong tranh”, “Đang chuẩn bị chuyển động”, and “Sắp sẵn sàng”; no provider/model terminology;
- progress reflects backend stages but does not promise exact completion time;
- controls auto-hide during playback and reappear on tap;
- retry appears only for retryable failures;
- “Xem tranh theo cách nhẹ nhàng” or equivalent fallback continues with V1 rather than blocking;
- the user never sees internal codes, model names, mask/mesh terms or stack traces;
- accessibility/reduced-motion mode selects bbox/whole-drawing focus.

The flow does not require tapping the picture to choose a subject. The selected topic from Gate A drives the target.

## 11. File-level implementation map

Exact names may be adjusted by an approved ADR, but ownership must remain clear.

### Backend contracts

- Add `backend/src/sketch2life/contracts/schemas/auto_rig.py`.
- Add `backend/src/sketch2life/contracts/schemas/renderer_v2.py`.
- Extend contract exports and create canonical JSON fixtures.
- Do not mutate V1 schemas incompatibly.

### Application/domain

- Add `backend/src/sketch2life/application/ports/spatial_grounding.py`.
- Add `backend/src/sketch2life/application/ports/segmentation.py`.
- Add derived artifact/job capability ports as required.
- Add `backend/src/sketch2life/application/services/auto_rig/` modules for target selection, cleanup policy, archetypes, geometry orchestration, validation, motion planning, packaging and fallback.
- Extend supervised-flow composition only through the approved job/launch boundary.

### Infrastructure

- Add an in-memory deterministic adapter for tests/fixtures first.
- Add a benchmark-only segmentation/grounding adapter behind optional dependencies.
- Add content-addressed derived artifact storage/grants and cache.
- Add worker/queue composition only after deployment ADR approval.

### HTTP

- Add a dedicated auto-rig router and request/response mapping.
- Add V2 package/artifact read endpoints with capability validation.
- Keep technical errors out of public messages.

### Renderer

- Add mirrored V2 schemas in `packages/art-renderer/src/`.
- Add package loader, mesh scene, bone graph, CPU skinning, V2 timeline and fallback adapter.
- Update `demo/mobile.ts` to discriminate V1/V2 commands.
- Preserve V1 browser player and its regression suite.

### Mobile

- Extend demo API types for job status/V2 launch.
- Add preparation state to context without changing canonical session authority.
- Update Pixi screen loading, timeout, retry, fallback and event handling.
- Retain landscape/full-screen behavior and next-step sequence.

### Governance/evidence

- Add an ADR for timing/deployment/model boundaries.
- Add an `ORIGINAL_DERIVED` artifact policy and provenance schema.
- Add feature-local fixtures, metrics, logs, screenshots and recordings.
- Do not copy generated creative assets to approved/applied folders as part of this feature.

## 12. Dependency and model selection

No exact segmentation or geometry stack is frozen in revision 2.

### Candidates to benchmark

- dedicated segmentation model with box/point prompts, including a SAM2 Tiny/Small-class candidate;
- deterministic geometry libraries or a small maintained triangulation implementation;
- image/mask operations through the smallest dependency set that passes reproducibility, license, size and runtime checks.

### Selection criteria

- license and redistribution fit;
- L4 VRAM/latency alongside Qwen;
- cold/warm startup and memory release;
- children's crayon/pencil/low-contrast drawing quality;
- deterministic output and version pinning;
- Android package size impact (should be zero for backend-only model code);
- maintenance and security posture;
- graceful CPU/test fixture adapter availability.

Owner-approved deployment direction: a separate auto-rig worker/service on the same Lightning L4 host. Before activation, record Qwen-only, auto-rig-only, sequential, and attempted-concurrent VRAM/latency measurements. Default to serialized GPU admission until evidence proves safe concurrency. Keep both model lifecycles process-scoped; loading segmentation inside each request or reloading Qwen per stage is prohibited.

## 13. Delivery milestones and approval gates

### M0 — contracts, ADR and golden corpus

- Record the three resolved owner decisions in an ADR.
- Approve contracts, hard limits, artifact policy and deployment ADR.
- Create authorized synthetic/demo corpus and expected tier labels.
- No live model.

Exit: Python/Zod fixtures and architecture import checks pass; owner approves M1.

### M1 — deterministic job/package vertical slice

- Job lifecycle, idempotency, progress, content-addressed derived artifacts and grants.
- Fixture adapter returns known masks/rig packages.
- V2 command/package fetch and V1 fallback skeleton.
- No provider/model dependency.

Exit: complete deterministic E2E on Android plus failure/expiry/retry evidence.

### M2 — grounding, segmentation and cutout tiers

- Benchmark adapters and choose via ADR.
- Mask cleanup/validation.
- Deliver `CUTOUT_MICRO_MOTION` and `BBOX_VISUAL_FOCUS` before full rig.

Exit: corpus quality/latency thresholds met; no duplicate semantic Qwen request.

### M3 — complete initial archetype registry

- Implement and validate `butterfly`, `bird`, `flower`, `tree_branch`, `fish`, `biped`, `rigid`, `generic_organic`, and `unknown` profiles.
- Mesh, bones, weights, validation and motion profiles.
- `RiggedArtworkPackageV1` produced on suitable fixtures.

Exit: every golden topic resolves to either a validated specialized rig or an explicit generic/rigid/unknown fallback; deformation and semantic-safety thresholds pass with rejection evidence.

### M4 — renderer/mobile V2 integration

- CPU skinning and semantic V2 timeline.
- full-screen loading/playback/retry/fallback UX;
- feature flag and instant rollback to V1.

Exit: supported devices meet crash, FPS, memory and responsiveness budgets.

### M5 — shadow rollout and quality hardening

- V2 preparation in shadow for demo fixtures/users without changing visible output.
- compare tier yield, latency, failure, visual review and fallback.
- limited activation only after owner review.

### M6 — topic and archetype refinement

- split broad families into more specialized profiles only when corpus evidence shows a quality benefit;
- add aliases/topics without changing existing resolution semantics;
- version every registry change and retain old-package compatibility.

Each milestone requires its own approval update. Later approval is not implied by earlier completion.

## 14. Acceptance criteria

### Contracts and architecture

- AC-030-01: V1 contracts and existing V1 tests remain unchanged and passing.
- AC-030-02: Python and TypeScript accept/reject the same V2 golden fixtures.
- AC-030-03: model/provider packages exist only in infrastructure/worker composition.
- AC-030-04: no command crosses the WebView bridge with inline mesh/mask/texture bytes.
- AC-030-05: every artifact and package is source-hash bound, session scoped and versioned.

### Product correctness

- AC-030-06: rig target equals the adult-confirmed canonical subject; no new subject is invented.
- AC-030-07: motion is explainable by an allowlisted profile and recorded evidence source.
- AC-030-08: the original remains available and visually recoverable at every tier.
- AC-030-09: a failed/slow/rejected rig reaches a lower tier and does not block continuation.
- AC-030-10: future video and off-screen activity ordering remains intact.

### Geometry and quality

- AC-030-11: invalid masks, geometry, weights and probe deformations are rejected before renderer delivery.
- AC-030-12: a full rig package has finite bounded vertices, valid triangles, normalized weights and known bones.
- AC-030-13: background ghosting beyond the approved threshold forces downgrade.
- AC-030-14: each initial-registry archetype has positive, low-confidence, malformed and unsupported golden cases.
- AC-030-14A: every admitted canonical topic resolves deterministically to a specialized archetype, `generic_organic`, `rigid`, or `unknown`; no topic silently disappears.

### Runtime and UX

- AC-030-15: the same job request is idempotent and does not duplicate model execution.
- AC-030-16: public UI shows friendly progress/fallback/retry messages and no internal error code.
- AC-030-17: V2 renderer releases textures, meshes, listeners and timelines on replay/unmount.
- AC-030-18: old clients continue through V1; feature flag rollback requires no data migration.
- AC-030-19: reduced-motion mode avoids full deformation.

### Security/privacy

- AC-030-20: capabilities expire, have bounded reads and cannot access another session's artifact.
- AC-030-21: logs contain IDs/hashes and metrics, not raw child images, tokens or full model output.
- AC-030-22: artifact deletion follows session deletion/retention policy.
- AC-030-23: repository security validation passes before every commit/push.

## 15. Verification matrix

| Layer | Required verification |
|---|---|
| Contracts | schema unit tests, cross-language golden fixtures, fuzz/property checks for bounds |
| Target/motion policy | table tests for confidence, relation, learning objective and forbidden motions |
| Mask pipeline | fixture tests for empty/full/tiny/fragmented/clipped/noisy masks |
| Geometry | degenerate contours, holes, multiple components, NaN, winding, weight sums, probe poses |
| Jobs | idempotency, concurrent request, timeout, retry, cancellation/expiry, stale pipeline version |
| Capabilities | expiry, replay/read limit, hash mismatch, cross-session denial, deleted artifact |
| Renderer | V1 regression, V2 package rejection, CPU skinning snapshots, resize/orientation, cleanup |
| Mobile | loading, background/resume, WebView reload, retry, fallback, reduced motion, next step |
| E2E | Gate A/B → job → V2/Fallback → Pixi completion → future video placeholder → activity |
| Security | repository validator, dependency audit, secret scan, malicious package/URI fixtures |

## 16. Metrics and provisional budgets

Final thresholds require M0/M2 measurement. Record at minimum:

- preparation queue/warm/cold latency by stage and percentile;
- segmentation acceptance rate and tier yield by archetype;
- package size and fetch/decode time;
- renderer first-motion time, median/min FPS, long-frame count and peak memory;
- validation rejection/fallback reason distribution;
- cache hit rate and duplicate-execution count;
- visual reviewer score for source fidelity, visible motion, ghosting and learning relevance;
- session completion and retry rate.

Provisional safety caps, not approval thresholds:

- hard application wait budget with immediate V1 fallback after expiry;
- one automatic infrastructure retry;
- bounded package size and texture dimensions;
- target 30 FPS floor on the supported Android baseline;
- no unbounded vertex, bone, timeline or event count.

## 17. Rollout and rollback

1. Ship V2 contracts and deterministic fixture path behind backend and mobile flags.
2. Keep V1 endpoint/player as control.
3. Run model pipeline in shadow mode; store metrics and approved demo artifacts only.
4. Enable V2 for an allowlisted demo corpus/device set.
5. Increase coverage only after owner review of visual and behavioral evidence.
6. Roll back by disabling launch V2; existing sessions use V1 without migration.

Cache entries include pipeline/config version so rollback does not reinterpret incompatible packages.

## 18. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Segmentation fails on crayon/low contrast | spatial prompts, quality gates, corpus benchmark, cutout/bbox/V1 fallback |
| Qwen runs twice or reloads | dedicated ports/worker, no semantic rerun, process-level model lifecycle, idempotency evidence |
| GPU OOM/contention | isolated worker, default serialized GPU admission, measure Qwen lazy-load plus auto-rig residency, documented unload policy, timeout fallback |
| Subject leaves a hole/ghost | small deformations, validated source-derived patch, no translation without patch, downgrade |
| Mesh folds or stretches | bounded topology, probe poses, fold-over/stretch validator |
| Motion contradicts drawing | allowlisted profiles tied to canonical subject/action/relation/objective |
| Large bridge payload | capability-referenced package, strict byte/hash checks |
| Slow intro feels frozen | stage-based loading, maximum wait, early preprocessing decision, fallback |
| Derived artifact confused with new art | `ORIGINAL_DERIVED` category and source/operation provenance |
| Scope becomes a research project | milestone approvals, template-based registry, generic fallbacks, measurable exit criteria |
| V2 breaks demo | feature flag, V1 endpoint/player, old-client tests, shadow rollout |

## 19. Evidence deliverables

- `E-030-CONTRACT-*`: Python/Zod fixture parity and limits.
- `E-030-ARCH-*`: dependency/import scan and ADR review.
- `E-030-MODEL-*`: benchmark manifest, model/config/license, masks, metrics and rejected cases.
- `E-030-RIG-*`: mesh/weights/probe validation results and package hashes.
- `E-030-RENDER-*`: Android recordings, frame/memory metrics and V1/V2 comparison.
- `E-030-FALLBACK-*`: every fallback reason and continuation proof.
- `E-030-SEC-*`: capability isolation/expiry and repository security output.
- `E-030-UX-*`: loading/retry/fallback/reduced-motion visual review.

No evidence may include real child data, provider secrets, or unapproved creative assets.

## 20. Owner decisions and approval status

Resolved on 2026-09-25:

1. Grounding/segmentation starts after Gate A; final motion compilation waits for Gate B.
2. The initial implementation covers the full named archetype registry and routes every other topic through explicit generic/rigid/unknown behavior.
3. Auto-rig runs as an isolated worker/service on the same Lightning L4 host, with measured and initially serialized GPU admission.

Revision 2 was approved and its deterministic baseline is implemented. Revision 3 below is a material runtime-quality extension and remains blocked until the owner explicitly approves its exact scope/hash.

## 21. Revision 3 — functional playback and segmented natural motion

### 21.1 Runtime findings that trigger this revision

1. `AutoRigPlayer` creates its GSAP timeline only inside the first `play()` call. Before that call it publishes `duration=0`; mobile consequently disables pause, seek backward, seek forward, replay and the progress surface.
2. The progress bar is display-only. It has no press/drag seek behavior or control acknowledgement.
3. The current default composition has no production segmentation adapter. Its template mesh covers normalized region `(0,0,1,1)`, so the butterfly demo deforms the whole source image instead of independently moving wings/body.
4. A single regular grid plus one broad archetype deformation cannot create plausible articulation. Natural motion requires subject mask, semantic parts, pivots, per-part meshes and a bounded coordinated timeline.
5. The generic fallback message hides whether the downgrade came from mask, part decomposition, rig validation, package load or playback. Public UI must remain friendly, but technical logs/evidence need typed reason codes.

### 21.2 Approved-direction target experience

The default playback is a 12–15 second guided intro followed by a subtle idle loop until the adult continues:

```text
0.0–2.0s   original drawing reveal and camera settle
2.0–4.0s   subject focus; background remains recognizably the original
4.0–11.0s  articulated subject motion with two or three natural micro-beats
11–15s     learning bridge and gentle settle
after intro deterministic low-amplitude idle loop; no automatic navigation
```

For a butterfly, the minimum accepted full rig is `body + left_wing + right_wing`, with optional antennae. Wings rotate around thorax-side pivots with slightly offset phase and bounded amplitude; the body may bob subtly; antennae may sway only when valid parts exist. The full image is never scaled or stretched to simulate wing motion.

Equivalent allowlisted profiles are required for bird, flower, branch/tree, fish and biped. `rigid`, `generic_organic` and `unknown` use lower-motion profiles rather than invented articulation.

### 21.3 Workstream A — playback-control repair

1. Compile and validate the complete GSAP timeline during `load()`, not lazily during `play()`.
2. Publish `READY` with a finite non-zero duration before autoplay so mobile controls are enabled immediately.
3. Keep a single authoritative playback clock. Every play, pause, seek, replay and completion publishes position, duration, state and interaction phase with monotonic sequence.
4. Pause freezes the timeline and deformation updates. Resume continues from the same timestamp.
5. Add visible controls for seek back 3 seconds, play/pause, seek forward 3 seconds and replay from zero.
6. Make the progress track pressable and draggable; seeking clamps to `[0,duration]` and updates the mesh before acknowledgement.
7. Auto-hide controls only while actively playing. Keep controls visible while paused, seeking, completed, failed or waiting. A stage tap toggles them without changing playback.
8. Add renderer unit tests and Android bridge tests for pre-play duration, pause stability, seek clamp, replay, completion and duplicate/out-of-order commands.

### 21.4 Workstream B — real subject and part extraction

The runtime must implement the existing `SegmentationPort`; it must not restore an unconditional second semantic Qwen request.

1. Start the idempotent extraction job after Gate A using the adult-confirmed canonical subject and the immutable source hash.
2. Benchmark two prompt paths against the authorized child-drawing corpus:
   - spatial hints emitted as part of the existing first VLM understanding response, never a second VLM inference;
   - a dedicated grounding adapter using the canonical label, followed by SAM 2.1 Hiera Small mask extraction.
3. Run the selected grounding/segmentation adapter in the isolated Lightning worker already approved for FEAT-030. Default GPU admission is serialized with Qwen until VRAM evidence permits overlap.
4. Produce a validated subject mask and archetype-specific part masks. Part decomposition may combine model masks with deterministic contour, symmetry, connected-component and color-boundary analysis.
5. Preserve raw mask, cleaned mask and every accepted part mask as `ORIGINAL_DERIVED` artifacts with source hash, model/config version and operation provenance.
6. Reject empty, full-frame, tiny, fragmented, border-clipped, target-missing and semantically inconsistent masks. Never treat a full-frame mask as a successful subject cutout.
7. If subject extraction succeeds but parts do not, use whole-subject cutout micro-motion. If subject extraction fails, use bbox focus or V1 without pretending that a full rig was produced.

### 21.5 Workstream C — part-aware rig and 2.5D composition

1. Replace the single full-frame mesh with one bounded mesh per accepted part and a root subject transform.
2. Derive pivots from mask geometry and archetype constraints; validate pivots lie near expected joints/boundaries.
3. Generate independent bones/weights for parts. A vertex cannot be influenced by a bone from another disconnected part unless the archetype explicitly allows it.
4. Keep the original drawing as the visual authority. Build a source-derived background plate only when deterministic paper/background reconstruction passes seam and color-difference thresholds; otherwise constrain motion so no obvious hole or duplicate subject appears.
5. Add edge feathering and one-pixel dilation/erosion probes to reduce white halos while preserving the child's stroke silhouette.
6. Generate deterministic motion variation from package seed: bounded timing offsets, easing and amplitude variation make motion less mechanical without changing semantics.
7. Use coordinated profiles rather than whole-object scaling:
   - butterfly: opposing wing pivots, small phase offset, body bob, optional antenna sway;
   - bird: wing/tail/head micro-motion only when those parts are valid;
   - fish: body curve and tail oscillation;
   - flower: petal/stem breeze with anchored roots;
   - branch/tree: low-amplitude branch/leaf sway;
   - biped: breathing/head/arm idle only, no walking unless supported by approved context;
   - rigid: camera/parallax/focus, no rubber deformation.

### 21.6 Workstream D — package and renderer contracts

Add a backward-compatible package revision carrying:

- subject mask and part artifact descriptors;
- part IDs, semantic role, region, pivot and z-order;
- per-part mesh/bones/weights;
- background-plate descriptor and validation status when present;
- timeline beats, idle-loop range, easing and deterministic seed;
- typed preparation and downgrade reason codes;
- model/adapter/config provenance without prompts, credentials or raw provider output.

Renderer V2 continues accepting revision-2 packages. Mobile still receives only short-lived package/artifact capabilities; no mask, texture or mesh bytes cross the React Native bridge.

### 21.7 Workstream E — loading, observability and fallback UX

1. Show stage-specific child-friendly loading copy while extraction is running; never display internal model or error names.
2. Distinguish `PREPARING_SUBJECT`, `SEPARATING_PARTS`, `BUILDING_MOTION`, `VALIDATING`, `READY`, `DOWNGRADED` and `FAILED_RETRYABLE` in backend telemetry.
3. Record first-ready duration, mask/part tier, fallback reason, package bytes, first motion, FPS and long-frame count without raw image data.
4. Permit one explicit retry for retryable infrastructure failure. Invalid geometry/mask is a deterministic downgrade, not an automatic model loop.
5. Keep video-placeholder and off-screen activity ordering unchanged.

### 21.8 Revision-3 acceptance criteria

- AC-030-24: duration is greater than zero before autoplay and remains stable across play/pause/seek.
- AC-030-25: pause freezes visual pose and playback time; resume continues without restarting.
- AC-030-26: seek backward, seek forward, progress-track scrub and replay work on Android and clamp safely.
- AC-030-27: controls remain visible when paused and auto-hide only during active playback.
- AC-030-28: no `FULL_AUTO_RIG` package may use a full-frame subject mask or a mesh that deforms the entire source drawing.
- AC-030-29: butterfly full-rig evidence shows independently articulated left/right wings around validated pivots; body/background do not stretch with the wings.
- AC-030-30: intro duration is 12–15 seconds and transitions to a bounded idle loop without blocking Continue.
- AC-030-31: every specialized profile has golden positive, malformed-mask, missing-part and downgrade cases.
- AC-030-32: source fidelity, halo, ghosting, fold-over and motion-naturalness pass named visual-review thresholds before activation.
- AC-030-33: Qwen is not called a second time solely for Pixi segmentation; model execution count is evidenced per session.
- AC-030-34: the Lightning worker records cold/warm latency and Qwen-only, segmentation-only and serialized combined VRAM before live activation.
- AC-030-35: technical logs identify the exact failing stage/reason while mobile displays bounded Vietnamese guidance without internal codes.

### 21.9 Verification and evidence required

1. Renderer clock/control tests using fake time plus Android WebView integration evidence.
2. Golden corpus masks and part overlays for every initial archetype, including rejection samples.
3. Butterfly frame sequence proving independent wing articulation and unchanged body/background bounds.
4. Geometry probes for NaN, fold-over, extreme stretch, disconnected weights and invalid pivots.
5. Android recording showing loading, 12–15 second intro, pause, ±3 second seek, scrub, replay, auto-hide and Continue.
6. Lightning metrics for model revision, VRAM, cold/warm latency, queue time, tier yield and failures.
7. V1/revision-2 compatibility, capability isolation, repository security and no-real-child-data checks.

### 21.10 Delivery sequence

1. Fix playback clock and controls independently of model work.
2. Build golden corpus and benchmark grounding/SAM paths; record the selected adapter in an ADR before dependency activation.
3. Implement subject masks, then part masks and downgrade rules.
4. Implement part-aware package/rig/compositor and natural motion profiles.
5. Integrate Lightning worker with serialized GPU admission and loading/progress.
6. Run Android visual review and activate only accepted archetypes; unsupported topics remain on explicit lower tiers.

Revision 3 does not authorize a model solely by name. The benchmark/ADR must record exact revision, license, package footprint, child-drawing quality, latency and L4 VRAM before the selected adapter is made the default.

## 22. Revision 4 — single-L4 AI-assisted semantic part rigging

### 22.1 Recommendation and boundary

Add AI only at the perception boundary: identify the already-approved subject, segment it, and separate visible semantic parts. Keep skeleton fitting, pivots, mesh generation, skin weights, motion selection, limits, and PixiJS playback deterministic.

The owner selected **Meta SAM 2.1 Hiera Small** for the MVP. It receives accepted point/box prompts from the existing deterministic component proposal and, when present, optional bounded spatial hints produced during the original Qwen understanding inference. It never triggers another Qwen request. Archetype-aware contour, symmetry, connected-component and color-boundary logic then proposes part prompts and validates the returned masks. **SAM 3 is excluded from the MVP because its gated checkpoint adds access and runtime friction without project-specific L4 evidence.**

This revision does not authorize either model for production merely by naming it. Selection requires the M0/M1 benchmark and a new ADR. It explicitly rejects end-to-end generative animation as the MVP auto-rig mechanism because it can redraw the child's work, invent motion, cost more GPU time, and cannot produce the bounded part/pivot/weight contract required by Renderer V2.

### 22.2 Target architecture on one NVIDIA L4

```text
Gate A confirms canonical subject
  -> AutoRigJobV2 (idempotent by source hash + target + pipeline version)
  -> GPU admission queue on Lightning host
  -> semantic part prompt registry from accepted archetype
  -> selected segmentation adapter
       selected path: deterministic/spatial proposal + SAM 2.1 Small
  -> mask candidate scoring and rejection
  -> deterministic cleanup and part topology checks
  -> archetype template fit (bones, pivots, mesh, weights)
  -> deformation probes and tier selection
  -> content-addressed RiggedArtworkPackage revision
  -> PixiJS part meshes + deterministic natural-motion profile
```

The model worker is backend-only and separate from the mobile/API process. Qwen remains the semantic authority used by the existing understanding flow; the rig worker consumes the approved canonical label and does not make a second Qwen request. The renderer never calls a model.

Because the L4 has 24 GB of GPU memory and the current Qwen3-VL 8B process uses BF16, concurrent residency is not assumed safe. Initial admission is serialized:

1. Qwen understanding completes and releases or idles behind the GPU coordinator.
2. The segmentation worker receives one bounded job.
3. The coordinator records allocated/reserved/peak VRAM before load, after load, after inference, and after release.
4. Concurrent residency may be enabled only if 100-job stress evidence shows no OOM and preserves at least 4 GiB measured headroom at peak.
5. If coexistence fails, use process-level model swapping, not repeated in-request construction. Keep the selected segmentation worker warm for a short bounded lease and cache results by content hash.

### 22.3 Model benchmark matrix

Benchmark exact pinned revisions, not floating model names:

| Candidate | Prompt source | Intended role | Main risk |
|---|---|---|---|
| SAM 2.1 Hiera Small | deterministic region plus point/box prompts; optional spatial hints from the first VLM response | selected subject/part mask refinement | no native open-vocabulary text grounding; depends on prompt quality |
| Current deterministic component scan | no GPU/model | control and emergency fallback | cannot reliably identify semantic parts |

#### 22.3.1 Public benchmark interpretation before the L4 run

Official public numbers narrow the candidates but do not replace the project benchmark:

- The current `Qwen/Qwen3-VL-8B-Instruct` repository is approximately 17.5 GB on disk in four safetensor shards. Disk size is not peak CUDA memory, but it confirms that a BF16 Qwen process leaves limited theoretical space on a 24 GB L4 before activations, allocator reserve and image/token state.
- Meta reports SAM 2.1 Hiera Small at 46M parameters and 84.8 FPS, but that number was measured on an A100 with PyTorch 2.5.1/CUDA 12.4 and describes the official video benchmark path. It is not an L4 single-image latency guarantee and does not include text grounding.
- SAM 3 is excluded from the MVP because its checkpoint is gated and its published benchmarks do not establish a benefit for this single-image L4 workload sufficient to justify the extra access/runtime path.

Therefore the first execution is a ten-fixture L4 smoke benchmark, not full integration. It compares the deterministic control with SAM 2.1 Small under identical 1024-side inputs. SAM 2.1 proceeds to the 54-fixture quality benchmark only if environment startup, mask sanity and memory safety pass.

The authorized benchmark corpus contains no real child data in Git. Use at least 54 synthetic/owner-cleared drawings: six cases for each of the nine registry outcomes (`butterfly`, `bird`, `flower`, `tree_branch`, `fish`, `biped`, `rigid`, `generic_organic`, `unknown`). Include white paper, ruled paper, weak contrast, touching objects, multiple objects, border clipping, incomplete anatomy, and intentionally unsupported cases. At least 27 fixtures receive manually reviewed subject/part masks for quantitative comparison.

Record for every candidate:

- exact repository/model revision, config, dtype, dependency lock and license review;
- checkpoint bytes and cold/warm model-load time;
- subject-mask acceptance, part completeness, false full-frame acceptance, fragmentation and boundary score;
- per-stage P50/P95 latency at the fixed benchmark resolution;
- Qwen-only, segmentation-only, sequential and attempted-concurrent GPU memory;
- full-rig, cutout, bbox and V1 tier yield by archetype;
- reviewer scores for source fidelity, part identity, halo/ghosting and expected articulation.

Provisional go/no-go gates for the selected adapter:

- zero accepted full-frame masks and zero cross-subject masks in the golden rejection set;
- at least 90% usable subject masks and at least 75% required-part completeness on specialized positive fixtures;
- warm P95 segmentation and scoring at or below 4 seconds; hard job timeout 8 seconds after worker readiness;
- no OOM or leaked model state in 100 serialized jobs;
- at least 4 GiB peak headroom before concurrent mode can be considered;
- at least 80% of reviewed specialized positive fixtures score 4/5 or better for source fidelity and motion readiness;
- every failed quality gate deterministically downgrades without blocking the flow.

If SAM 2.1 Small does not pass, retain the revision-3 deterministic baseline and do not label it `FULL_AUTO_RIG`.

### 22.4 Contract changes

Keep `SubjectSegmentationPort` for compatibility and introduce an additive `SubjectPartSegmentationPortV2` rather than widening an existing result ambiguously.

`SubjectPartSegmentationRequestV2`:

- session/request IDs, source artifact reference and SHA-256;
- canonical target ID, normalized label and Gate-A confidence;
- resolved archetype and allowlisted requested part roles;
- source dimensions, deadline, pipeline version and idempotency key;
- optional accepted point/box hints from the original understanding pass;
- no arbitrary prompt, image bytes, provider URL, credentials, or motion instruction.

`SubjectPartSegmentationResultV2`:

- validated subject region and subject-mask artifact descriptor;
- zero or more part descriptors: stable role, mask reference/hash, confidence, bbox, area ratio and quality metrics;
- adapter/model/config revisions and timing/memory summary;
- raw-candidate count, accepted-part count, rejection reason codes and selected extraction tier;
- source hash and derivation graph binding every output to the immutable original.

Add package revision fields for part role, mask/cutout descriptor, pivot, parent part, z-order, mesh, bones and validation. Model prompts and raw outputs stay inside the worker and are never persisted in the package or logs.

### 22.5 Archetype-specific part policy

The worker requests only parts declared by the accepted archetype registry:

- butterfly: body, left wing, right wing; antennae optional;
- bird: body, head, visible wing(s), tail; legs optional and never required for idle motion;
- flower: stem plus visible petal group; center/leaves optional;
- tree/branch: trunk or anchor branch plus one or more leaf/branch groups;
- fish: body and tail; fins optional;
- biped: torso, head, visible arms; legs optional for idle-only MVP;
- rigid: whole-object mask only, no anatomical part invention;
- generic/unknown: whole-subject mask only unless deterministic topology proves a safe split.

A requested part that is not visible is omitted, not hallucinated. Left/right assignment uses image coordinates plus archetype topology and is rejected when overlap or ordering is inconsistent. A full rig requires the archetype's minimum visible part set; otherwise the service selects `CUTOUT_MICRO_MOTION`.

### 22.6 Deterministic rig and motion after AI

AI masks are proposals, not executable rigs. The application pipeline must:

1. clean masks with bounded morphology and feathering while retaining raw artifacts;
2. validate containment, overlap, connectedness, area, borders and parent/part topology;
3. derive pivots from shared boundaries and archetype constraints;
4. fit bounded per-part meshes and normalized weights;
5. run rest-pose and extreme-pose probes for fold-over, stretch, seams and ghosting;
6. select an allowlisted motion profile using canonical semantics and learning context;
7. generate only bounded timing/amplitude variation from a deterministic package seed.

For butterfly motion, the accepted minimum remains independent left/right wing meshes rotating around thorax-side pivots, a stable body mesh, slight phase offset, eased acceleration/deceleration, subtle body bob, and settle. No whole-image scale or full-canvas warp is accepted.

### 22.7 Lightning worker and lifecycle

Add a dedicated `/internal/v1/rig-segment` worker route or queue consumer; do not add another public mobile endpoint. Required lifecycle behavior:

- process-scoped model load with readiness distinct from HTTP process health;
- one GPU job at a time initially, bounded queue and deadline propagation;
- cancellation on expired/deleted session and no retry for invalid masks;
- one retry only for typed transient infrastructure failure;
- content-addressed cache keyed by source hash, target/archetype, requested parts, adapter and config revision;
- structured logs containing correlation IDs, stages, durations, memory and reason codes, never raw child pixels or raw model output;
- feature flags for shadow mode, allowlisted archetypes and immediate fallback disablement.

### 22.8 Delivery tasks

1. **R4-T1 — Corpus and benchmark harness:** create a ten-fixture smoke set, then the authorized 54-fixture manifest/reviewed masks for candidates that pass; add a reproducible L4 measurement script.
2. **R4-T2 — Model ADR:** compare SAM 2.1 Small with the deterministic control; record the exact SAM 2.1 revision/license/config and benchmark verdict or a no-activation result.
3. **R4-T3 — V2 part contracts:** add Python/Zod schemas, golden parity fixtures, bounds and malicious-input rejection.
4. **R4-T4 — Worker and GPU coordinator:** implement serialized admission, lifecycle, memory metrics, timeout, cancellation and cache.
5. **R4-T5 — Mask quality pipeline:** scoring, cleanup, topology, stable typed rejection reasons and `ORIGINAL_DERIVED` persistence.
6. **R4-T6 — Part rig builder:** archetype minimum parts, pivots, meshes, bones, weights and deformation probes.
7. **R4-T7 — Package/renderer integration:** capability-referenced part artifacts, independent Pixi meshes and backward-compatible package loading.
8. **R4-T8 — Natural motion profiles:** coordinated 12–15 second intro plus idle for each accepted archetype; no generic rubber warp.
9. **R4-T9 — Shadow and allowlist rollout:** compare tiers/latency/visual evidence before enabling one archetype at a time.
10. **R4-T10 — Android evidence and rollback drill:** loading, timeout, fallback, pause/seek/replay, memory/FPS and feature-flag rollback.

R4-T1 and R4-T2 are approved separately from runtime activation. No model package is added to the default Lightning startup until the ADR is accepted.

### 22.9 Revision-4 acceptance criteria

- AC-030-36: one user flow performs at most one Qwen understanding inference; auto-rig segmentation is a separately counted model job.
- AC-030-37: the exact selected segmentation model revision, license, config, dependency lock and checkpoint hash are recorded in an accepted ADR.
- AC-030-38: subject and part results are source-hash bound, content-addressed and contain no raw prompt/provider output.
- AC-030-39: only registry-allowed visible parts can enter a rig; missing/ambiguous parts downgrade deterministically.
- AC-030-40: all L4 quality, latency, stress and memory gates in 22.3 pass before live activation.
- AC-030-41: `FULL_AUTO_RIG` requires validated independent part meshes and pivots; a subject-only or full-frame mask cannot receive that tier.
- AC-030-42: model failure, timeout, OOM prevention, invalid mask and cache corruption all preserve Continue through a lower tier.
- AC-030-43: renderer motion remains deterministic and bounded for the same package seed, independent of model availability during playback.
- AC-030-44: Android maintains the approved playback controls and reaches the 30 FPS floor on the named baseline device for accepted package limits.
- AC-030-45: disabling the revision-4 feature flag restores the revision-3/V1 path without data migration or app rebuild.

### 22.10 Evidence required for approval and activation

- `E-030-R4-MODEL`: candidate source/license/revision/checkpoint hashes and benchmark report;
- `E-030-R4-CORPUS`: fixture authorization, taxonomy, mask-review method and no-real-child-data attestation;
- `E-030-R4-L4`: `nvidia-smi`/PyTorch cold, warm, peak, sequential and concurrency measurements;
- `E-030-R4-MASK`: accepted/rejected overlays and per-archetype subject/part metrics;
- `E-030-R4-RIG`: pivot/topology/deformation-probe results and butterfly independent-wing frame sequence;
- `E-030-R4-E2E`: one-Qwen-call trace, asynchronous job trace, cache/idempotency and fallback proof;
- `E-030-R4-ANDROID`: recordings and FPS/memory for success, timeout and rollback paths;
- `E-030-R4-SEC`: dependency/license review, capability tests and repository security validation.

### 22.11 Decisions still requiring explicit owner approval

1. SAM 2.1 Hiera Small is owner-selected for the MVP; SAM 3 is excluded.
2. Approve the provisional corpus size and go/no-go thresholds in 22.3.
3. Approve serialized single-L4 GPU admission as the default and forbid concurrency until measured headroom passes.
4. Approve the implementation order R4-T1 through R4-T10; benchmark approval does not automatically authorize runtime activation.
