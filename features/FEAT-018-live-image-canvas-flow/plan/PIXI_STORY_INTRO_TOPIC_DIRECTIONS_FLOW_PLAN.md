# Pixi story intro, topic directions and staged activity flow plan

Status: `IMPLEMENTED — OFFLINE VERIFIED — OWNER LIVE SMOKE PENDING`

Date: 2026-09-23
Feature: `FEAT-018-live-image-canvas-flow`
Target branch: `codex/feat-018-contract-plan`
Base commit inspected: `5530214c11499b04b29521e71d2da2df4253fa50`

## 1. Owner-confirmed outcome

The demo must make the child's original drawing feel like the beginning of a story rather than a
small static preview inside the activity instructions. The confirmed journey is:

```text
required drawing + optional narration
  -> staged understanding/loading
  -> up to three grounded Vietnamese topic directions
  -> adult Gate A confirmation or one changed-direction re-query
  -> up to three strict-fit reviewed activity options
  -> exact ExperienceSpec and adult Gate B approval
  -> full-screen landscape Pixi story intro
  -> main-video placeholder (real video remains a future integration)
  -> restore portrait orientation
  -> outdoor/off-screen activity instructions
  -> feedback
```

Gate B keeps its frozen meaning: the adult approves the exact activity, objective, template and
ExperienceSpec before downstream media runs. It is not redefined as activity-completion feedback.

The Pixi segment should resemble a short presentation opening: begin with the source drawing,
bring it to life through a bounded sequence of movement and reveal beats, show short Vietnamese
captions derived from confirmed evidence, and hand off naturally to the future main video. This
iteration implements an honest video placeholder only.

## 2. Read-only diagnosis

### 2.1 Why Pixi currently appears static

- The live backend emits one `WHOLE_DRAWING` object and a whole-image fallback/reveal plan.
- The browser player can execute motions, but the live plan normally contains only
  `DRAW_REVEAL`, which is visually equivalent to a brief fade.
- The player API exposes only `load`, `play` and `destroy`; it has no pause, replay, seek, duration
  or progress surface.
- The WebView is embedded at the bottom of the portrait activity-detail screen, after long
  instructions, so the available canvas is small and the transition is easy to miss.
- The current mobile state calls activity handoff before showing Pixi and combines Gate B,
  off-screen instructions, renderer and feedback navigation in one screen.
- The HTML itself states that the current mode is a whole-image reveal with no supplemental sprite.

### 2.2 Why topic suggestions remain weak

- The UI displays low-level claims as selectable topic cards, so objects, actions and contexts are
  presented as independent ideas rather than coherent directions.
- Unknown ASCII labels are collapsed to `chi tiết trong tranh`; this avoids leaked English but
  loses useful meaning.
- `compose_topic_vi` picks one primary claim and at most one action/context. It does not create a
  small set of distinct, complete narratives or score image/narration coverage.
- Generic model labels such as `bird picture`, `detail`, scenery, duplicate leaves and partial
  action phrases can survive long enough to weaken the final topic.

### 2.3 Why loading can look frozen

- Several backend operations are synchronous while the mobile screen has sparse stage feedback.
- A percentage can stay at zero while model loading/inference is active, which implies a stalled
  request even though work is progressing.
- Renderer bootstrap, source fetch, plan load and first playback are currently represented by one
  short status line with no stage timeout or recovery affordance.

## 3. Frozen invariants and scope boundaries

- Image remains required. Narration remains optional: none, typed Vietnamese text or recorded
  audio/ASR.
- Gate A confirms meaning. Gate B approves the exact immutable ExperienceSpec and strict-fit
  activity identity. Neither gate may be silently auto-approved.
- Recommendations remain reviewed-catalog only, maximum three, and must pass the unchanged age,
  readiness, material, supervision, safety and strict semantic-continuity checks.
- The original drawing and source SHA-256 remain authoritative. Pixi may transform its display but
  may not replace or destructively overwrite it.
- No generated replacement artwork, unreviewed supplemental image, video generation, real video
  provider, auth implementation or durable persistence is added.
- The video screen must state that it is a placeholder. It may not present a mock file as generated
  or completed media.
- Mobile contains no Lightning/provider token or endpoint. Codex performs no paid/live provider
  request; the owner retains the existing manual synthetic-image test authority.
- FEAT-003 Vision V2 remains consume-only. Its frozen schema is not widened for topic directions.
- Unrelated FEAT-026 files remain untouched.

## 4. Target state and navigation design

### 4.1 Screens

1. `scene_understanding`
   - Show at most three complete topic-direction cards, not raw claims.
   - Keep a compact expandable evidence area for the adult to inspect detected details.
   - Selecting the primary direction uses the current result.
   - Selecting another direction invokes the existing bounded changed-direction re-query once.
   - Gate A confirms the final returned direction and its source claim IDs.

2. `activity_recommend`
   - Keep at most three strict-fit reviewed activities with priority and concise rationale.
   - Selecting an option prepares that exact ExperienceSpec without another Vision request.

3. `experience_review`
   - New focused adult review screen containing the selected activity summary, materials, safety,
     approximate duration and exact Gate B action.
   - Gate B approval changes the session to `EXPERIENCE_READY`.
   - This screen does not claim that the outdoor activity has already occurred.

4. `pixi_intro`
   - New immersive screen entered only from approved `EXPERIENCE_READY` state.
   - Lock device to landscape before rendering; hide normal portrait chrome.
   - Prepare renderer while preserving the exact spec/source identity.
   - Auto-play only after source, plan and WebView handshake are all ready.
   - Show play/pause, replay, seek backward, seek forward, progress/time and continue controls.
   - Continue is enabled after the intro is ready; completion is recommended but not mandatory so
     an accessibility/user recovery path is always available.
   - Back, error and unmount paths restore portrait orientation deterministically.

5. `video_placeholder`
   - Remain landscape to make the seam match the future video player.
   - Show the confirmed story/activity title, a clear `Video chính sẽ được thêm sau` message and a
     primary `Tiếp tục hoạt động ngoài trời` action.
   - Do not display fake playback time, generated-video status or fabricated media.
   - On continue, complete the existing exact `ActivityHandoffV1`, restore portrait and navigate to
     the activity instructions.

6. `outdoor_activity`
   - Portrait-only activity instructions, materials checklist, steps and collapsed adult safety.
   - No embedded Pixi/WebView and no Gate B action.
   - Finishing the real-world activity proceeds to feedback.

7. `feedback`
   - Existing session-only feedback behavior remains; no durable-save claim.

### 4.2 Backend state mapping

```text
CANDIDATES_READY
  -> PREPARE_EXPERIENCE
GATE_B_PENDING
  -> APPROVE_GATE_B
EXPERIENCE_READY
  -> PREPARE_RENDERER (read-only for session version)
  -> Pixi intro
  -> video placeholder
  -> COMPLETE_HANDOFF
HANDOFF_READY
  -> outdoor activity
  -> RECORD_FEEDBACK
FEEDBACK_RECORDED
```

No backend state is invented for the local video placeholder. Mobile navigation state and renderer
playback state are separate from domain/session state. A reload reconstructs the furthest safe
screen from the backend state without claiming that media or the physical activity completed.

## 5. Topic-direction design

### 5.1 Additive application projection

Add a mobile-facing `topic_directions` projection without changing FEAT-003 Vision V2. Each item
contains:

- stable direction ID and priority `1..3`;
- complete Vietnamese `title_vi` of roughly 8–22 words;
- one short child-facing `summary_vi`;
- one primary subject, optional action and optional context;
- exact source claim IDs;
- image/narration coverage flags;
- bounded confidence band (`HIGH`, `MEDIUM`, `LOW`) derived from available numeric evidence rather
  than a fabricated percentage;
- `requires_requery` for non-primary directions.

### 5.2 Composition rules

- Produce no more than three semantically distinct directions.
- Prefer a concrete subject plus action/context supported by the image and narration.
- Fuse image and narration when they agree; preserve a conflict instead of forcing agreement.
- Remove aggregate/generic labels, English display text, duplicate singular/plural forms and
  directions that differ only by word order.
- Never use `chi tiết trong tranh` as a direction title. Sparse evidence falls back to one honest
  complete sentence based on the strongest concrete claim.
- Typed narration may contribute wording but may not fabricate visual confidence.
- A selected non-primary direction uses the existing one-requery budget. The previous valid result
  remains visible if re-query fails, and the UI explains the recovery without raw codes.

### 5.3 Tests

- Bird/branch/leaves/perching becomes distinct Vietnamese directions such as a bird perched on a
  branch, not five raw cards.
- Unknown English labels do not leak and do not become a generic selectable direction.
- Image-only, text+image agreement, audio transcript agreement, conflict, sparse evidence and
  duplicate-label fixtures are covered.
- Three is a hard maximum; one grounded direction is acceptable when evidence is sparse.
- Selecting the primary direction does not call Vision again; changing direction calls it at most
  once and preserves the previous proposal on failure.

## 6. Pixi story-intro design

### 6.1 Source-preserving storyboard

Create a deterministic `PixiIntroStoryboardV1` companion projection bound to session,
ExperienceSpec, source artifact and plan identity. It contains 3–5 bounded beats:

1. original drawing appears intact;
2. camera gently pushes toward the confirmed subject;
3. drawing pans/scales/tilts or floats according to a reviewed motion profile;
4. one or two short grounded Vietnamese captions appear in sequence;
5. the image settles and the transition to the future video is announced.

For this demo, the guaranteed path animates the original whole drawing with a cinematic sequence
(`DRAW_REVEAL`, `SCALE`, `MOVE_TO`, optional small `ROTATE`) plus procedural Pixi decoration such
as light particles or focus rings. Procedural shapes are code-rendered and do not replace the
drawing. They must remain subtle and child-friendly.

An optional future extraction seam may animate a source-derived crop/mask only when provenance,
coordinates and source hash are valid. Extraction is not required for this iteration and failure
must fall back to the whole-image cinematic sequence, never to a static blank canvas.

### 6.2 Renderer controls

Extend the renderer bridge additively while retaining existing protocol-1 load and lifecycle
messages:

- control message: `PLAY`, `PAUSE`, `REPLAY`, `SEEK_RELATIVE_SECONDS`, `SEEK_TO_SECONDS`;
- state/progress message: position, duration, playing/completed state and active beat ID;
- clamp every seek to `[0, duration]`;
- reject wrong instance/session/spec, oversized, replayed or malformed commands;
- player API adds pause/replay/seek/get-state without exposing the GSAP timeline outside the
  renderer package;
- ticker/progress listeners are removed on replay, reload, completion and destroy.

Native controls remain outside the WebView so labels, touch targets and accessibility are
consistent. The WebView receives strict commands and emits strict progress events only.

### 6.3 Landscape lifecycle

- Add the supported Expo orientation dependency explicitly.
- Lock landscape on `pixi_intro` mount and retain it for `video_placeholder`.
- Restore portrait before `outdoor_activity`, on back navigation, modal recovery, renderer failure
  exit and component cleanup.
- Prevent stale async orientation calls from relocking a screen after navigation.
- Provide a portrait-safe error surface if the orientation API is unavailable on an emulator.

### 6.4 Renderer failure behavior

- Source fetch or plan validation failure shows the original drawing and a friendly modal.
- Actions: retry renderer, continue with the original drawing, or return to review.
- Continuing with the source still reaches the honest video placeholder and outdoor activity;
  renderer failure never falsifies a successful playback event.
- No raw protocol, absolute path, contract ID or exception appears in child-facing UI.

## 7. Video placeholder and future integration seam

- Introduce a dedicated mobile route/component, not the existing hard-coded mock video screen.
- Consume only confirmed session/spec/story display data.
- Expose a future `LearningVideoPresentation` adapter boundary with states
  `UNAVAILABLE_PLACEHOLDER`, `READY` and `FAILED`; instantiate only the placeholder adapter now.
- Do not call a video API, create a fake asset, reuse an unrelated bundled video image or emit a
  media-completed event.
- The future real-video implementation can replace the adapter and screen body without changing
  Gate B, Pixi or outdoor-activity navigation.

## 8. Loading and perceived-performance design

### 8.1 Understanding screen

Replace the frozen percentage with stage-based progress:

- `Đang kiểm tra ảnh`;
- `Đang nghe/đọc lời kể` when narration exists;
- `Đang tìm nhân vật và hành động`;
- `Đang ghép thành các hướng câu chuyện`;
- `Sắp xong rồi`.

Use actual backend `understanding_progress` stages where available. For synchronous inference, show
an indeterminate animated indicator and elapsed-time reassurance rather than inventing progress.
After a bounded threshold, show `Bước này có thể mất thêm một chút` and a safe cancel/back action;
after timeout, show the global retry modal.

### 8.2 Renderer screen

Show distinct phases: orientation, renderer connection, source loading, motion-plan loading and
ready/playback. Disable seek until duration is known. If no bootstrap/progress event arrives within
the bounded timeout, offer retry/source fallback rather than leaving a spinner indefinitely.

### 8.3 Activity preparation

Use one visible request lock and stage labels for context loading, strict-fit selection and exact
experience preparation. Existing results reopen without another request.

## 9. Implementation slices

### Slice A — Contracts and topic directions

- Add the mobile projection schemas and deterministic topic-direction service.
- Preserve raw claims/provenance and current Qwen generation budget.
- Return directions from understanding/re-query endpoints.
- Update mobile mapping and Gate A selection.
- Add unit and HTTP contract regressions.

### Slice B — Renderer timeline and storyboard

- Add source-preserving multi-motion live plan generation.
- Add storyboard captions bound to source claims and ExperienceSpec.
- Add player pause/replay/seek/state support and strict bridge messages.
- Update standalone/mobile renderer UI and protocol tests.

### Slice C — Mobile flow split and orientation

- Add `experience_review`, `pixi_intro`, `video_placeholder` and `outdoor_activity` routes.
- Move Gate B, Pixi and outdoor instructions into their correct screens.
- Add landscape lock/restore and native playback controls.
- Keep global recovery modal and source-image fallback.

### Slice D — Loading/UX and verification

- Replace misleading percentages and long silent waits with stage-aware loading.
- Perform a focused child/adult copy, accessibility and navigation pass on changed screens.
- Run emulator orientation/back/reload/error smoke tests and capture feature-local evidence.

## 10. Expected implementation areas

- `backend/src/sketch2life/application/services/topic_semantics.py`
- `backend/src/sketch2life/application/services/supervised_flow.py`
- renderer/mobile workflow contracts under `backend/src/sketch2life/contracts/schemas/`
- focused backend unit/contract tests
- `packages/art-renderer/src/browserPlayer.ts`
- `packages/art-renderer/src/contracts.ts` and bridge/protocol exports
- `packages/art-renderer/demo/mobile.ts` and `mobile.html`
- renderer tests and fixtures
- `apps/ui-mobile/src/context/AppContext.tsx`
- `apps/ui-mobile/src/screens/Flow1Screens.tsx`
- `apps/ui-mobile/src/screens/Flow2Screens.tsx`
- `apps/ui-mobile/BaoApp.tsx`, screen types/exports and package dependencies
- this feature's context, decisions, approval and evidence records

No FEAT-026 path may be staged or modified.

## 11. Acceptance criteria

1. Gate B retains exact frozen identity semantics and moves the session to `EXPERIENCE_READY`.
2. The visible order is Gate B → landscape Pixi intro → landscape video placeholder → portrait
   outdoor activity → feedback.
3. Pixi is a dedicated full-screen experience, not embedded in the activity instructions.
4. A valid live launch visibly animates the original drawing through at least three bounded beats
   and shows grounded Vietnamese captions before completion.
5. Play/pause, replay, seek backward, seek forward and progress/time work against the actual GSAP
   timeline and remain synchronized after repeated use.
6. Renderer events/controls reject wrong identity, malformed payloads and out-of-range seeks.
7. Renderer failure preserves the source drawing and provides retry/continue/back recovery.
8. Orientation enters landscape for Pixi/video placeholder and always restores portrait before the
   outdoor activity or after every exit/error path.
9. The video screen is explicitly a placeholder and performs no video/provider/generation call.
10. Continuing from the placeholder creates the exact existing handoff and opens the selected
    strict-fit outdoor activity.
11. The topic screen displays at most three distinct Vietnamese directions containing concrete,
    grounded meaning; raw English, lone words, duplicates and `chi tiết trong tranh` are not
    selectable topics.
12. Image and narration evidence are combined only when supported; confidence is not fabricated.
13. Selecting a changed topic direction performs at most one re-query, while primary selection and
    activity selection perform no extra Vision request.
14. Understanding, activity preparation and renderer startup have visible stage-aware loading,
    bounded waiting guidance and friendly timeout recovery; no frozen fake percentage remains.
15. Image-required, optional narration, strict catalog/safety rules, process-local storage, future
    auth/save seams, original-art provenance and no-real-video boundaries remain intact.
16. Backend/renderer/mobile focused tests, full relevant regression tests, TypeScript, Ruff, mypy,
    architecture, repository security and `git diff --check` pass.
17. Android emulator evidence covers portrait→landscape→landscape→portrait, controls, fallback,
    back navigation and absence of fatal/React Native errors.

## 12. Risks and mitigations

- **Whole-image motion may still feel limited:** use a deliberate multi-beat cinematic sequence,
  synced captions and procedural focus effects; retain an optional source-derived region seam.
- **Orientation race or stuck landscape:** centralize ownership, await lock/unlock, restore on every
  cleanup path and test rapid back/continue actions.
- **Seek leaks duplicate ticker callbacks:** one timeline/progress subscription per player instance,
  with explicit teardown tests.
- **Topic directions overstate sparse evidence:** require exact source claim IDs and emit fewer than
  three directions when evidence is insufficient.
- **Placeholder is mistaken for a real video:** explicit copy and an adapter state that cannot emit
  `READY` in this iteration.
- **Scope drifts into generated assets/video:** stop and request a new approval before adding either.

## 13. Verification and evidence

- Deterministic topic-direction unit and HTTP contract fixtures.
- Renderer schema, timeline-control, replay/seek and teardown tests.
- Mobile TypeScript and copy/recovery guard updates.
- Backend focused and full test collections with configured skips identified.
- Ruff/mypy on changed backend modules.
- Architecture, harness, repository security and diff checks.
- Android emulator screenshots/logs and a short evidence matrix for normal, fallback, orientation,
  loading and navigation paths.
- No live Lightning call by Codex. Owner-run synthetic smoke remains separate.

## 14. Approval gate

Implementation must not start while this status is `AWAITING_APPROVAL`.

After owner approval:

1. compute the exact SHA-256 of this plan;
2. record approver, timestamp, hash, scope and boundaries in `approvals/TASK_APPROVAL.md`;
3. change status to `APPROVED — IMPLEMENTATION AUTHORIZED`;
4. implement in the four slices above, updating context/evidence after meaningful steps;
5. stop for renewed approval if real video, generated visual assets, a breaking frozen-contract
   change, auth/persistence or live-provider execution becomes necessary.
