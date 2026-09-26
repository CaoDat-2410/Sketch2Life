# FEAT-030 Original-derived Pixi auto-rig plan

- Status: DRAFT — OWNER DECISIONS RESOLVED; AWAITING EXPLICIT APPROVAL
- Plan revision: 2
- Implementation status: BASELINE_IMPLEMENTED; LIVE SEGMENTATION BENCHMARK/ADAPTER PENDING
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

Implementation remains blocked until the owner explicitly approves revision 2, the approval record is updated, and the M0 ADR is written before runtime implementation begins.
