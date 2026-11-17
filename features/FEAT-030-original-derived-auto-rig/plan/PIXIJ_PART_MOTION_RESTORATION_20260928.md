# Pixi part-motion restoration and fallback choreography

- Status: APPROVED
- Plan revision: 1
- Implementation status: FOLLOW_UP_IMPLEMENTED_LOCALLY; RENDERER_CHECKS_PASS; FRESH_ANDROID_FLOW_PENDING
- Feature: FEAT-030 original-derived auto-rig; FEAT-018 mobile Pixi playback consumer
- Approval source: project owner direct request to fix the short zoom/rotation-only Pixi result,
  clarified to target 15–30 seconds, try image-processing part separation if AI does not provide
  usable parts, and use the established Pixi fallback if both fail; owner selected multiple action
  beats followed by rest with a fixed camera.

## Goal

Make the Pixi experience visibly animate independently validated parts of the child's drawing,
without substituting whole-image camera zoom/rotation for rigging. Deliver a bounded 15–30 second
choreography (20 seconds by default) with several distinct subject-action beats and a calm, still
ending. Use SAM 2.1 part masks first, deterministic image-processing segmentation as the next
option, and the established Pixi original-art fallback only when neither can safely form a part rig.

## Runtime findings

1. `AutoRigService.start_gate_a_preparation()` currently hardcodes `has_renderable_parts = False`.
   Even when the subject segmentation adapter returns a mask, `prepare_template_package()` chooses
   `CUTOUT_MICRO_MOTION` (or a safer lower tier); `FULL_AUTO_RIG` is unreachable.
2. The port has a `parts` result shape and the Lightning request accepts `requested_part_roles`,
   but the SAM response schema, worker and adapter currently carry only one subject mask. No
   independent part-mask artifacts reach the renderer.
3. Pixi's `CUTOUT_MICRO_MOTION` branch puts the entire subject cutout on one `cutoutSprite` and
   transforms it using the root pose. This is not wing/body/leaf articulation.
4. If V2 startup fails, `v2FallbackPlan()` runs the V1 whole-image fallback for 1.2 + 1.8 + 1.2 =
   4.2 seconds, including a 1.04 scale and rotation. That matches the reported short zoom/rotate
   behavior. The V2 player's completion callback also starts an unbounded root-motion idle loop.
5. The V2 plan schema already caps duration at 30 seconds; archetype tracks currently end at 12
   seconds. Part masks are not currently part of the package-to-WebView artifact capability flow.

## Approved scope

- Extend the existing additive auto-rig contracts and bounded artifact handoff to carry independent,
  source-hash-bound part masks (part id, role/bone, region, confidence and derivation provenance).
- Extend the already-approved SAM 2.1 segmentation path to request a small bounded set of
  archetype-relevant part masks in the same request/model session. Do not add a Qwen generation,
  automatic retry, provider activation, or change the live SAM activation/benchmark gate.
- When SAM supplies no valid independent masks, attempt deterministic image-processing separation
  within the verified subject mask. Accept only bounded, non-empty parts that satisfy source and
  parent-mask containment, coverage, overlap and provenance checks. Do not infer/fabricate a missing
  part when confidence is insufficient.
- Render actual part masks as separate Pixi textures/meshes bound to the matching validated bones;
  remove hard-coded rectangular butterfly slices and root transforms that make a whole cutout look
  like a rig.
- Use the legacy Pixi/original-art fallback only after AI and image processing cannot safely produce
  a part rig. Keep the viewport/camera fixed: no full-art `SCALE`, `ROTATE`, camera pan/zoom, or
  unbounded after-completion idle motion. Preserve the exact original drawing and show only modest
  source-art reveal/local subject motion supported by the fallback tier.
- Produce a deterministic 20-second V2 plan by default, constrained to 15–30 seconds, with a
  settling/reveal phase, multiple subject-specific action beats, and a final still/rest phase.
  Playback, pause, seek, replay and progress use this exact plan duration.
- Add offline synthetic fixtures and contract/player regression tests for butterfly and flower
  parts, generic/unsupported subjects, confidence/overlap failures, V2 startup fallback, fixed
  camera, duration, and still completion. Update FEAT-030/018 context and feature-local evidence.

## Exclusions and preserved boundaries

- No live SAM/Qwen/Lightning request by Codex; no automatic model retry or extra Qwen generation.
- No change to SAM activation flags, model ADR/license/L4 benchmark gate, Gate A/B, topic selection,
  learning objective/activity, session persistence, credentials, or FEAT-003 producer contracts.
- No generated/replacement artwork, video/TTS, scene redesign, new external assets, real child data,
  mobile provider calls, or change to the immutable original/source provenance rules.
- A subject-only mask must never be labeled or displayed as a full part rig. If AI and image
  processing both fail quality validation, use the safe legacy Pixi fallback with a fixed camera.

## Acceptance criteria

1. For a synthetic butterfly fixture with valid part masks, left wing, right wing and body are
   separate renderer targets with different poses; the artwork is not represented by one stretched
   full-image sprite or rectangular crop pretending to be a part mask.
2. For a synthetic flower fixture, stem and crown/petals have independent validated targets.
   Other archetypes use only roles supported by accepted masks; unsupported/generic scenes degrade
   honestly without inventing anatomy.
3. Part masks must be source-hash-bound, non-empty, within the verified subject mask, bounded in
   count/size, and pass minimum coverage and maximum overlap checks before `FULL_AUTO_RIG` is
   eligible. Missing/invalid parts must select an explicit lower tier.
4. If AI part masks are missing/invalid, deterministic image processing is attempted. If that also
   fails, the original Pixi fallback remains available, visibly moves only within the artwork, and
   does not zoom/rotate/pan the full artwork or claim auto-rig success.
5. The default choreography lasts 20 seconds; accepted plans are 15–30 seconds and contain at
   least two distinct action beats plus a still ending. The viewport remains fixed. No infinite root
   idle continues after completion.
6. Pause, seek, replay and progress remain synchronized to the full choreography duration in the
   renderer controls.
7. Existing V1/V2 compatibility, original-source integrity, capability/hash checks and safe
   session fallback remain intact. No extra Qwen call or live model activation is introduced.
8. Relevant backend, renderer and mobile offline tests/type/build checks pass. A fresh-session
   Android visual smoke must show part-level motion for a valid part-mask fixture or an honest safe
   fallback; live Lightning acceptance remains owner-run and is not claimed by offline tests.

## Verification

- Backend: unit/contract coverage for SAM part payload normalization, artifact grants, image
  processing, package tier selection and duration/keyframe choreography.
- Renderer: unit/visual-fixture assertions for separate part textures/poses, fallback camera lock,
  no post-completion idle, and exact duration; typecheck and demo build.
- Mobile: TypeScript/UI-copy validation and Android bundle/export if available.
- Runtime: inspect backend logs and a fresh-session emulator run only when an owner-started flow is
  available; do not trigger live AI from Codex.
- Run the repository security validator before any commit/push.

## Approved follow-up — consume the subject-only cutout tier (2026-09-29)

- Owner approval: direct request to fix the persistent fallback and restart the local backend.
- Scope: let the WebView send a validated `CUTOUT_MICRO_MOTION` package, its source image, and
  its verified subject mask to the existing Pixi auto-rig player without demanding independent
  part masks. Keep the `FULL_AUTO_RIG` path fail-closed unless every declared part mask is fetched,
  hash-checked, provenance-checked, and validated. Unsupported tiers continue through the safe
  original-art fallback.
- Acceptance: a subject-only cutout package loads with zero part-mask reads and starts V2 playback;
  a full rig missing part masks still fails safely; an invalid subject mask still falls back;
  focused player tests, renderer checks/build, and backend health after restart pass.
- Boundaries: no provider requests, SAM activation/configuration changes, contract changes, or
  changes to Gate A/B, source provenance, or full-rig quality gates. Backend restart clears only
  its in-memory demo sessions; a new owner-run flow is needed for visual acceptance.
