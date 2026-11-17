# Personalized Drawing Exploration: tap-to-discover and 2.5D cut-out plan

Status: `IMPLEMENTED — OFFLINE VERIFIED — OWNER LIVE SMOKE PENDING`

Date: 2026-09-23
Feature: `FEAT-018-live-image-canvas-flow`
Target branch: `codex/feat-018-pixi-exploration`
Plan revision: `3 — Pixi-only implementation`
Supersedes for the Pixi/topic slice: the whole-image-only sections of
`PIXI_STORY_INTRO_TOPIC_DIRECTIONS_FLOW_PLAN.md`. It does not undo the already-approved
Gate A, Gate B, video-placeholder, orientation, auth/save seam or Lightning boundaries.

## 1. Outcome to approve

Change the post-Gate-B experience from a generic sentence plus a weak whole-image animation to
an interactive, source-preserving drawing exploration:

```text
image + optional narration
  -> grounded subject candidates (short labels only)
  -> adult confirms one subject/meaning at Gate A
  -> strict-fit activity selection and Gate B
  -> landscape Personalized Drawing Exploration
       -> original drawing as backplate
       -> 2.5D source-derived layers when extraction passes
       -> tap-to-discover hotspots for confirmed entities
       -> guided focus beats and short captions
   -> existing video placeholder/handoff seam (video implementation owned by another task)
  -> portrait outdoor activity
```

The experience must feel like the child’s drawing is being explored, not replaced by generated
art. The selected subject remains the central visual anchor. Supporting objects such as a branch
or leaf may become secondary layers only when they are grounded by the same confirmed result.

This is intentionally a change in product language and planning, not a renderer replacement:

```text
old: understanding -> motion plan -> object moves
new: understanding -> learning thread -> visual exploration plan
     -> focus / relation / discovery / depth -> activity bridge
```

`SceneExplorationPlanV1` becomes the source-of-truth application projection. It explains why each
visual beat exists and which confirmed claim it teaches. The existing `ArtAnimationPlanV1` remains
the deterministic PixiJS/GSAP execution payload compiled from that higher-level plan.

## Owner rollback addendum — 2026-09-25

Status: `APPROVED — IMPLEMENTATION AUTHORIZED`

The owner requested that the direct image-tap/localization slice be removed from the normal live
demo because the extra Qwen/Lightning geometry request adds latency and currently falls back too
often. The Gate-A runtime therefore returns to the previously approved topic-direction flow:

- `/v2/vision` is the only provider request during initial image understanding.
- The mobile screen renders up to three grounded Vietnamese `topic_directions` and does not place
  tappable regions or require a subject tap before Gate A.
- The first deterministic direction is selected by default; the adult may edit the topic text
  before confirming Gate A.
- The runtime does not call `/v2/localize`; Pixi keeps the original-art/whole-drawing fallback
  until a separate localization decision is approved again.
- The localization adapter and endpoint remain isolated for future work, but they are not part of
  this user-facing request path.

Acceptance: one initial understanding request produces the topic screen without a localization
request, no `FALLBACK_REQUIRED` localization state is shown, and Gate A can continue without a
tap on the artwork.

## 2. Owner decisions captured by this plan

- Gate A cards use short Vietnamese subject labels, not complete sentences. Examples: `Con chim`,
  `Cành cây`, `Chiếc lá`.
- A complete sentence may appear only as optional downstream narration/bridge copy, never as the
  selectable subject identity.
- Both features are in scope for this increment: tap-to-discover and 2.5D cut-out.
- The Pixi experience is called `Personalized Drawing Exploration`, not `Personalized Art
  Animation`; animation is an implementation detail of the exploration.
- The exploration is organized around one `learning_thread`: selected subject, direct visual
  relation and the reviewed activity concept. Pixi may reveal that thread but may not invent a new
  story.
- PixiJS 8 + GSAP remains the renderer baseline. No renderer replacement is proposed.
- The original image remains the immutable backplate and source of truth. Cut-outs are derived
  views with provenance, never replacements.
- The flow remains landscape for Pixi and the future video seam, then portrait for the outdoor
  activity.
- Whiteboard MP4 generation, TTS, encoding and video-worker implementation are owned by another
  task/person. This branch preserves only the placeholder/handoff seam and does not implement video.
- Real video, generated replacement artwork, auth, durable save and Codex-triggered Lightning
  requests remain out of scope.

## 3. Current gap verified in the repository

1. `build_topic_directions()` creates complete titles and the mobile screen renders those titles
   as the primary selectable concepts. This allows relation/action text to masquerade as a subject.
2. `claims_from_raw()` currently discards actor/object relation identity after ranking. The
   renderer therefore cannot reliably distinguish `bird`, `branch` and `leaf` as stable targets.
3. The live renderer launch currently validates exactly one original whole-drawing object and one
   original manifest asset. `CROP`, `TRANSPARENT_PNG` and `MASK` are defined but unreachable from
   the live launch path.
4. The current Pixi storyboard contains captions and whole-image motion, but no interaction
   targets, focus regions, depth layers or discovery events.
5. Qwen semantic understanding intentionally does not emit geometry. Geometry/cut-out must be a
   separate, typed post-understanding stage; it must not be smuggled into the frozen FEAT-003 V2
   semantic contract.

## 4. Scope and non-goals

### Included

- A new mobile-facing subject-candidate projection derived from confirmed raw claims and relations.
- Short Vietnamese labels, stable entity/claim references, confidence bands and provenance.
- One bounded region-localization/extraction stage after Gate A/Gate B, behind application ports.
- Source-derived crops/masks for up to three grounded entities, with SHA-256 and versioned
  provenance.
- A 2.5D Pixi scene composed of the original backplate plus optional foreground/supporting layers.
- Tap-to-discover hotspots, focus state, highlight/outline, short caption and replay-safe events.
- Guided beats: whole picture, selected subject, related object, learning bridge.
- UI copy, child/adult accessibility, loading and friendly fallback states.
- Offline fixtures, contract tests, renderer tests, mobile tests and Android emulator evidence.

### Excluded

- New generated visual assets or external stock assets.
- Video generation, video playback integration or provider-generated animations.
- Arbitrary LLM-generated activity instructions; activity selection remains reviewed-catalog only.
- Automatic provider retries. A localization failure falls back deterministically.
- Raw model output, image bytes, credentials, child data or absolute paths in logs/evidence.
- Any FEAT-003 schema/adapter modification.
- Auth, durable persistence or a claim that the process-local demo is saved.
- Changes to unrelated `FEAT-026-current-system-srs` files.

## 5. Contract design

### 5.1 Subject candidate projection

Add `SubjectCandidateSetV1` as a FEAT-018 application/mobile projection. It is additive and
does not widen `VisionUnderstandingResultV2`.

```json
{
  "contract_name": "SubjectCandidateSetV1",
  "contract_version": "1.0",
  "session_id": "...",
  "source_artifact_sha256": "...",
  "items": [
    {
      "subject_ref": "entity-1",
      "label_vi": "Con chim",
      "semantic_kind": "SUBJECT",
      "priority": 1,
      "confidence_band": "HIGH",
      "source_claim_ids": ["entity-1", "relation-1"],
      "related_subject_refs": ["entity-2"],
      "image_covered": true,
      "narration_covered": false
    }
  ],
  "max_items": 3
}
```

Rules:

- Maximum three items; preserve deterministic priority.
- `label_vi` is a short noun phrase, 1–5 Vietnamese words, with a closed translation/normalizer.
- No English leakage, complete sentence, raw `chi tiết trong tranh`, duplicate canonical label or
  relation-only item may be selectable.
- The primary subject is selected from a concrete entity. Actions/relations support it but are not
  rendered as independent subjects unless the contract explicitly marks them `SUBJECT`.
- Keep the existing `topic_directions` response temporarily as a compatibility adapter if needed,
  but the BaoVC UI must render `subject_candidates` and must not render long direction titles.

### 5.2 Scene exploration plan — application source of truth

Add `SceneExplorationPlanV1` as the high-level, source-linked plan consumed by the renderer-plan
compiler and mobile presentation. It must be deterministic for a fixed session/spec/source and
must be explainable without inspecting Pixi implementation details.

```json
{
  "contract_name": "SceneExplorationPlanV1",
  "contract_version": "1.0",
  "session_id": "...",
  "experience_spec_ref": {"id": "...", "version": 1},
  "source_artifact_ref": "...",
  "source_artifact_sha256": "...",
  "learning_thread": {
    "subject_ref": "entity-1",
    "subject_label_vi": "Con chim",
    "relation_ref": "relation-1",
    "relation_label_vi": "đậu trên",
    "related_ref": "entity-2",
    "related_label_vi": "Cành cây",
    "activity_concept": "Nơi sống của con vật"
  },
  "beats": [
    {
      "beat_id": "recognition",
      "purpose": "RECOGNIZE_SUBJECT",
      "focus_refs": ["entity-1"],
      "effect": "FOCUS",
      "caption_vi": "Con chim",
      "tap_enabled": true
    },
    {
      "beat_id": "relation",
      "purpose": "SHOW_DIRECT_RELATION",
      "focus_refs": ["entity-1", "entity-2", "relation-1"],
      "effect": "TRACE_RELATION",
      "caption_vi": "Chim đậu trên cành",
      "tap_enabled": true
    },
    {
      "beat_id": "curiosity",
      "purpose": "BRIDGE_TO_ACTIVITY",
      "focus_refs": ["entity-1"],
      "effect": "ZOOM_OUT",
      "caption_vi": "Nơi sống của con vật",
      "tap_enabled": false
    }
  ],
  "activity_bridge_ref": "objective-1",
  "fallback_policy": "WHOLE_DRAWING_GUIDED"
}
```

Rules:

- `learning_thread` must use the Gate-A-confirmed subject and, when available, one direct relation
  or related entity. It cannot be built from every raw claim in the image.
- `purpose`, `focus_refs` and `activity_bridge_ref` are mandatory for every beat. A motion without
  a learning purpose is not emitted.
- Subject cards remain noun phrases. Pixi captions may be short educational phrases, but must be
  derived from the same refs and must not add an unconfirmed action, object or destination.
- Beat order is deterministic: recognition → direct relation → curiosity/activity bridge. A sparse
  scene may omit the relation beat and use whole-drawing guided fallback.
- Tapping a target changes only local exploration state. It cannot alter Gate A confirmation,
  ExperienceSpec, activity identity or the learning thread.

### 5.3 Region and extraction projection

Add `SceneFocusPlanV1` as the geometry/extraction projection generated from the
`SceneExplorationPlanV1` after the selected subject is known and bound to the exact session,
ExperienceSpec and source hash.

```json
{
  "contract_name": "SceneFocusPlanV1",
  "contract_version": "1.0",
  "session_id": "...",
  "experience_spec_ref": {"id": "...", "version": 1},
  "source_artifact_ref": "...",
  "source_artifact_sha256": "...",
  "primary_subject_ref": "entity-1",
  "targets": [
    {
      "target_ref": "entity-1",
      "label_vi": "Con chim",
      "role": "PRIMARY_SUBJECT",
      "region": {"x": 0.42, "y": 0.18, "width": 0.21, "height": 0.31},
      "region_confidence": 0.91,
      "asset": {
        "asset_kind": "MASK",
        "source_asset_id": "entity-1-mask",
        "source_asset_version": "1",
        "crop_version": "1",
        "mask_version": "1",
        "source_sha256": "..."
      },
      "depth_layer": "FOREGROUND",
      "hit_slop": 0.04,
      "status": "READY"
    }
  ],
  "extraction_status": "READY"
}
```

Required validation:

- Coordinates are normalized, finite and inside the source image; minimum/maximum area and aspect
  ratio are bounded to reject model garbage.
- Every target maps to a confirmed claim/entity reference; no free-form target is accepted.
- Every crop/mask retains the original source hash and has explicit crop/mask version provenance.
- Overlapping targets have deterministic priority and hit-slop rules.
- `READY` is permitted only after extraction checks pass. Otherwise the plan is `FALLBACK_REQUIRED`
  and the UI must not claim that 2.5D separation succeeded.
- The extraction adapter may use a bounded localization/segmentation implementation in Lightning,
  but it is hidden behind `SceneRegionLocalizer` and `SubjectCutoutExtractor` ports. The semantic
  understanding contract remains unchanged.

### 5.3 Renderer and bridge additions

Keep renderer protocol version `1` backward-compatible for old whole-image plans while removing
the live-launch-only assumption that there must be exactly one plan object. Additive fields/types:

- allow one `WHOLE_DRAWING` object plus up to three source-derived `CROP`/`TRANSPARENT_PNG`/`MASK`
  objects;
- add a companion `PixiInteractiveSceneV1` containing target refs, hit regions, depth role,
  focus beat IDs and short captions;
- add `DISCOVERED_ENTITY` and `FOCUS_CHANGED` lifecycle events containing only stable refs;
- keep `PLAY`, `PAUSE`, `REPLAY`, seek and progress semantics unchanged;
- reject wrong session/spec/source hash, stale sequence, unknown target, malformed hit region and
  oversized bridge messages;
- preserve the whole-image fallback path and source-only launch compatibility.

2.5D is implemented with existing bounded motion primitives: the backplate moves least, the
subject layer moves slightly more, and the support layer moves between them. No unbounded camera
or physics simulation is added. A tap pauses or gently focuses the selected layer, shows its short
label, then resumes only when the user chooses to continue.

## 6. Backend/application workflow

### Slice A — canonical subject semantics

- Preserve actor/object/relation references in `RankedClaim` and the topic mapper.
- Create `SubjectCandidateSetV1` from concrete entity claims, with relation evidence attached rather
  than flattened into the label.
- Keep confidence/provenance and image/narration coverage separate.
- Update Gate A confirmation to submit subject refs and source claim IDs, not display sentences.
- Ensure activity matching uses the primary subject family plus direct relation/object context; do
  not contaminate a bird anchor with every unrelated leaf/plant tag.

### Slice B — localization and cut-out service

- Add ports for localization and cut-out extraction in the application layer.
- Implement a provider/runtime adapter in Lightning that returns strict normalized regions and
  source-derived masks/crops only.
- Use one bounded localization/extraction attempt per accepted render preparation; no automatic
  retry. Record closed status such as `READY`, `LOCALIZATION_UNAVAILABLE`, `MASK_INVALID` or
  `SOURCE_MISMATCH`.
- Enforce CPU/GPU/time/byte limits and delete temporary derived files after the process-local
  capability expires.
- If the adapter is unavailable or quality gates fail, return a valid whole-image storyboard with
  tap cards still available at the non-canvas Gate A layer. Never show a blank canvas or fake mask.

### Slice C — scene compiler and renderer

- Compile `SceneExplorationPlanV1` first, then compile its visual effects into the existing
  deterministic `ArtAnimationPlanV1` payload. Do not let the renderer infer learning meaning from
  motion names.
- Compile original backplate, foreground subject and up to two support layers.
- Generate guided beats from the selected subject, confirmed direct relation and reviewed activity
  concept, not from arbitrary model text.
- Add target hit-testing, selected/focused state, outline/glow and child-readable labels.
- Add depth-aware parallax and synchronized captions while keeping the source drawing visible.
- Keep controls outside the WebView and retain existing orientation/error cleanup.

### Slice D — mobile flow and UX

- Replace long topic cards with compact subject cards and an adult-only expandable evidence view.
- Make the Pixi screen explicitly `Khám phá bức vẽ`; do not call it a generated animation.
- Show a short onboarding hint: `Chạm vào một chi tiết để khám phá`.
- Play the guided sequence automatically after the scene is ready; tapping is optional and can
  pause/focus a validated target without becoming a required quiz gate.
- Tap a hotspot: focus layer, show the short label, emit a sanitized event, then expose
  `Tiếp tục`/replay. Never change the selected activity from a tap.
- Show 2.5D loading as stages: `Đang tìm chi tiết`, `Đang tách nét vẽ`, `Đang sắp xếp lớp`.
- If extraction fails, modal copy says the original drawing is safe and offers `Xem ảnh gốc`,
  `Thử lại` only when a user explicitly requests it, or `Tiếp tục`.
- Do not show contract names, raw error codes, absolute paths or provider details to the child.
- Preserve landscape Pixi/video, portrait outdoor activity, back/reload/recovery and future
  auth/save seams.

## 7. Activity continuity

- Activity recommendations remain at most three, ranked and strict-fit.
- The selected activity must explicitly reference the confirmed subject/concept family and direct
  relation. An unrelated activity is rejected even if it is age-safe.
- The bridge from Pixi to activity is short and concrete, for example `Con chim — nơi sống`;
  it must not invent a new subject.
- Gate B remains the adult approval point. Pixi starts only after the exact ExperienceSpec is
  approved. Tapping a subject never silently changes the approved activity.
- Changing the subject before Gate B starts the existing bounded re-query path; tapping in Pixi is
  discovery only and does not mutate the approved spec.

## 8. Acceptance criteria

1. Gate A renders 1–3 short Vietnamese subject labels; no English, complete sentence, duplicate or
   relation-only card is selectable.
2. Bird/branch/leaf evidence produces stable refs and a primary subject without flattening every
   detected item into one long topic string.
3. A valid `SceneExplorationPlanV1` contains a learning thread and purposeful beats in the order
   recognition → relation → activity bridge; no motion-only beat is emitted.
4. A confirmed subject exposes at least one tap target when a valid region exists. Tapping it
   visibly focuses/highlights the matching source-derived layer and shows the correct short label.
5. A valid extraction plan renders an original backplate plus at least two depth layers with
   differentiated, bounded parallax; the source drawing remains recognizable and unchanged.
6. Cut-out/crop/mask assets preserve source SHA-256, asset version, extraction status and capability
   provenance. Invalid or stale provenance is rejected before rendering.
7. The guided sequence includes whole-scene reveal, subject focus, related-object focus when
   available, and a short learning bridge before the video placeholder.
8. The renderer supports play/pause/replay/seek and tap focus without duplicate ticker listeners,
   stale commands or orientation leaks.
9. If localization/segmentation fails, the app shows the original drawing, a friendly modal and a
   usable continue path. It never shows a blank canvas or claims successful 2.5D.
10. Activity suggestions remain maximum three and all displayed options pass strict subject/relation
   continuity; the bird example cannot produce an unrelated shaker/bottle activity.
11. The visible order remains Gate B → landscape drawing exploration → landscape video placeholder
    → portrait outdoor activity → feedback.
12. No raw model output, error code, provider secret, absolute path or child data appears in the
    mobile UI, logs or committed evidence.
13. Focused backend/contract/renderer/mobile tests, full relevant offline suites, TypeScript,
    Ruff, mypy, architecture, security and diff checks pass. Android emulator evidence covers
    subject cards, tap focus, 2.5D success, extraction fallback, controls and orientation restore.

## 9. Verification matrix

### Contract/backend

- Subject projection: bird/branch/leaf, duplicates, English labels, sparse image, narration
  agreement/conflict and missing relations.
- Exploration planner: subject-only cards, direct relation selection, deterministic beat order,
  missing-relation fallback, activity bridge identity and rejection of invented actions.
- Region validation: out-of-bounds box, tiny/huge box, stale hash, mismatched subject ref,
  overlapping targets, invalid mask/crop provenance and fallback status.
- Activity continuity: correct bird habitat options pass; unrelated plant/shaker options fail.
- API idempotency, session/spec identity, no auto-retry and no raw diagnostic leakage.

### Renderer

- Old whole-image plan remains valid.
- Multi-object plan validates and renders with depth ordering.
- Hotspot hit testing, overlapping target priority, focus/replay/seek and event sequence.
- Mask/crop load failure falls back to the original drawing.
- Ticker/listener teardown on reload, back, replay, completion and destroy.

### Mobile/emulator

- Gate A short labels and adult evidence expansion.
- Landscape entry, tap discovery, 2.5D success, friendly failure modal and continue path.
- Landscape video placeholder, portrait restore and outdoor activity handoff.
- Back/reload/race conditions, small screen touch targets and no fatal React Native errors.

## 10. Expected implementation areas

- `backend/src/sketch2life/application/services/topic_semantics.py`
- `backend/src/sketch2life/application/services/supervised_flow.py`
- new FEAT-018 contracts and ports for subjects, `SceneExplorationPlanV1`, focus plans,
  localization and cut-outs
- Lightning/runtime adapter modules and sanitized fixtures
- `backend/src/sketch2life/contracts/schemas/renderer.py`
- `packages/art-renderer/src/contracts.ts`, `browserPlayer.ts`, asset loading and bridge tests
- `packages/art-renderer/demo/mobile.ts` and mobile demo UI
- `apps/ui-mobile/src/context/AppContext.tsx`
- `apps/ui-mobile/src/screens/Flow2Screens.tsx`, `BaoApp.tsx` and related styles/types
- feature-local tests, context/decisions, evidence and approval records

## 10.1 Video boundary — handoff only (out of scope)

This branch does not implement whiteboard MP4 generation. The Pixi flow must keep a typed,
replaceable handoff seam for the separately owned video task:

```text
Gate B / ExperienceSpec
  -> PixiJS Personalized Drawing Exploration
  -> existing video placeholder/handoff seam
  -> portrait outdoor activity
```

The Pixi implementation may expose `video_placeholder`/handoff state and preserve the exact
`ExperienceSpec`, source hash and learning-thread references, but it must not create or mutate
`WhiteboardVideoJob`, TTS, masks/strokes, encoder output or provider video state. Video READY,
retry and MP4 playback are acceptance responsibilities of the other task.

No `FEAT-026` path may be modified or staged.

## 11. Risks and controls

- **Wrong subject localization:** require confirmed refs, confidence/area gates and visible fallback;
  never let geometry redefine semantic identity.
- **Cut-out looks artificial:** keep the original backplate visible, use only subtle depth offsets,
  add a soft edge/outline and reject low-quality masks.
- **Extra Lightning cost/latency:** localization is bounded, user-triggered after the approved
  flow, no automatic retry; offline fixtures cover the normal path.
- **Small/ambiguous drawings:** show tap cards and whole-image guided exploration; do not force
  2.5D when extraction quality is not proven.
- **Contract drift:** use additive FEAT-018 V1 projections and compatibility adapters; do not touch
  FEAT-003 contracts.
- **Orientation/stale commands:** retain centralized lock/restore, session/spec identity checks and
  strict bridge sequence validation.

## 12. Approval gate

This plan is `APPROVED — IMPLEMENTATION AUTHORIZED` for Pixi-only slices A–D on
`codex/feat-018-pixi-exploration`.

Authorized implementation boundaries:

1. implement subject projection, exploration planning, bounded localization/cut-outs, renderer
   bridge, Pixi mobile flow, tests and feature-local evidence;
2. preserve Gate A/Gate B, source/spec identity, auth/save seams and the existing video placeholder;
3. do not implement video generation, video playback, TTS, encoder/worker changes, live Lightning
   calls, auth/persistence, generated assets or FEAT-026 changes;
4. stop for renewed approval if implementation requires a breaking contract migration, an
   unapproved provider, generated assets, auth/persistence or any video scope.
