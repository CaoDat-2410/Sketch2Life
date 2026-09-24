# PixiJS fullscreen intro and direct hotspot discovery

Status: `IMPLEMENTED — OFFLINE VERIFIED; LIVE LIGHTNING SMOKE TEST OWNER-RUN`

Date: 2026-09-23
Feature: `FEAT-018-live-image-canvas-flow`
Target branch: `codex/feat-018-pixi-exploration`
Scope: PixiJS only; video implementation remains excluded.

## 1. Owner decisions

- Add a bounded localization step after Qwen semantic understanding so the app can identify
  normalized subject regions for direct tap interaction.
- Keep a non-interactive Pixi intro first. Direct image interaction becomes available only after
  the intro reaches `DISCOVERY_READY`.
- Use immersive landscape fullscreen: hide Android status/navigation bars while Pixi is active and
  restore them with portrait orientation on Back, Continue, unmount or error recovery.
- The interaction model is:
  - tap a validated subject hotspot -> discover/focus that subject;
  - tap empty canvas -> show/hide the chrome controls;
  - controls auto-hide after an idle timeout.

## 2. Current defect

The current screen renders native discovery chips above the WebView instead of making the image
itself interactive. The live renderer commonly has `FALLBACK_REQUIRED`, so the whole-image sprite
has no validated hit region and cannot emit a subject discovery event. The screen also permanently
spends space on a header and timeline, leaves Android system bars visible, and exposes `0:00 / 0:00`
while the renderer is still loading. This makes the landscape scene look small, blank and inactive.

## 3. Target runtime flow

```text
Gate B approved
  -> lock landscape + immersive system UI
  -> load source image and localization plan
  -> INTRO_LOADING
  -> INTRO_PLAYING
       whole drawing reveal
       selected subject focus
       related-object/learning bridge beat when available
  -> INTRO_COMPLETED
  -> DISCOVERY_READY
       direct subject hotspot taps enabled
       chrome controls hidden after idle
  -> DISCOVERY_FOCUSED
  -> Continue -> existing video placeholder/handoff seam
  -> restore portrait + Android system bars
```

Hotspots are disabled during `INTRO_LOADING` and `INTRO_PLAYING`; the intro must be experienced
before the child can explore the image. A fallback intro may still finish and expose Continue, but
must not claim that subject separation succeeded.

## 4. Contract changes

### 4.0 Subject-first Gate A selection (approved addendum)

The normal mobile path no longer renders three precomputed topic-direction cards. After image
understanding, the backend returns a bounded set of confirmed subject candidates plus their
localized source regions. The child/parent taps the actual subject in the artwork; that stable
candidate id becomes the sole primary claim for the next request. The backend then creates one
short Vietnamese sentence/topic from the selected subject and the preserved image/narration
evidence. Gate A is shown only after this selection response succeeds.

Changing the tapped subject is an explicit `SELECT_SUBJECT` request. It is not a client-side label
swap: the backend re-queries the grounded evidence, replaces the selected claim and sentence, and
returns a fresh localization/exploration projection for that subject. The mobile UI may keep the
adult evidence accordion, but it must not show the old three direction cards in the normal flow.

Localization is requested once after semantic understanding and again after a changed subject
selection. A provider failure leaves the original image intact and shows a friendly retry state;
it must never fabricate a hitbox. When a valid region exists, the same region identity is reused
by the Gate-A artwork picker and the later Pixi discovery scene.

### 4.1 Localization boundary

Add a backend application port for bounded localization after semantic understanding and after a
changed subject selection. The port returns only typed, bounded normalized regions for confirmed
subjects. The live implementation uses the backend-only Lightning `/v2/localize` operation; offline
tests inject a deterministic port double. It must not widen the frozen Qwen/FEAT-003 semantic
contract.

Required checks:

- target ref belongs to a confirmed subject candidate;
- region is inside `[0,1]` source coordinates;
- confidence and extraction version are present;
- source artifact hash, session and ExperienceSpec identity match;
- at most three targets;
- invalid/unavailable localization becomes `FALLBACK_REQUIRED`.

### 4.2 Renderer interaction protocol

Extend the additive FEAT-018 renderer protocol with:

- `INTRO_COMPLETED` lifecycle event;
- `DISCOVERY_READY` lifecycle event;
- `CANVAS_TAPPED` event for empty-canvas chrome toggling;
- existing `FOCUS_CHANGED` and `DISCOVERED_ENTITY` events for validated hotspots;
- an interaction phase in renderer playback state, bounded to
  `INTRO_LOADING | INTRO_PLAYING | DISCOVERY_READY | DISCOVERY_FOCUSED | FALLBACK`.

The existing play/pause/replay/seek controls remain compatible. No video state, MP4 field, TTS,
worker or encoder contract is added here.

## 5. PixiJS implementation

### 5.1 Intro mode

- Keep the original drawing as the immutable backplate.
- Compile the current `SceneExplorationPlanV1` beats into the intro timeline.
- Do not attach hotspot listeners until the intro completes.
- Emit `INTRO_COMPLETED` exactly once per load/replay cycle.
- Keep a short caption overlay during the intro; after completion replace it with the discovery
  hint `Chạm vào chi tiết trong tranh`.

### 5.2 Direct image hotspots

- Convert each validated `SourceRegionV1` into a Pixi hit area using the actual texture/stage
  transform, including bounded hit slop.
- Tap on a hotspot emits `FOCUS_CHANGED` then `DISCOVERED_ENTITY` with the stable target ref and
  short Vietnamese label.
- Apply a gentle outline/glow, scale/focus and short caption; do not replace or redraw the source.
- Resolve overlapping hotspots deterministically by depth layer, confidence, then target order.
- Remove the current native subject-chip panel from the normal discovery path. It may remain only
  as an adult-readable fallback indicator when no localization is available.
- Reuse/cache the original source texture. Crop loaders must use image dimensions before releasing
  `ImageBitmap` and must never expose source bytes through the native bridge.

### 5.3 Chrome controls

- Render controls as an overlay above the canvas, not as a permanent bottom layout row.
- Chrome is visible at entry, after an empty-canvas tap and after a control action.
- Start an idle timer after each interaction; hide chrome after 3 seconds by default.
- Hotspot taps focus the subject and show a compact discovery label without forcing the full chrome
  bar open.
- Empty-canvas taps toggle chrome visibility.
- Continue is disabled until the intro is ready; it remains available in fallback mode.

## 6. Android fullscreen implementation

- Lock landscape on Pixi entry.
- Hide status and navigation bars using the Expo Android system UI capability (adding the minimal
  approved dependency if needed).
- Use a safe-area-aware canvas so the artwork fills the usable display without being clipped.
- Restore system bars and `PORTRAIT_UP` on Back, Continue, unmount, WebView error and retry.
- Keep the future video placeholder on the same landscape/system-UI seam.

## 7. Loading and failure UX

Visible states:

- `Đang mở bức vẽ…`
- `Đang tìm chi tiết…`
- `Đang chuẩn bị phần khám phá…`
- `Chạm vào chi tiết để khám phá`
- `Một vài chi tiết chưa tách được. Bức vẽ gốc vẫn an toàn.`

Rules:

- no blank canvas without a state message;
- no `0:00 / 0:00` presented as completed playback;
- disable seek/replay until renderer duration is known;
- source failure shows the original native preview and a friendly modal/action;
- never show contract names, raw provider errors, paths or error codes to the child.

The subject picker uses the same friendly modal pattern for localization/selection failures. A
failed selection keeps the previous confirmed subject and sentence, so the user can retry without
losing the Gate-A review state.

## 8. Acceptance criteria

1. Pixi opens landscape immersive fullscreen and uses the majority of the display for the artwork.
2. Intro plays before any hotspot is tappable and ends in an explicit `DISCOVERY_READY` state.
3. A localized confirmed subject can be tapped directly on the drawing and produces focus,
   highlight, short label and sanitized lifecycle events.
4. Tapping empty canvas toggles chrome; chrome auto-hides after 3 seconds of inactivity.
5. Controls remain usable when visible; Continue preserves the existing video placeholder seam.
6. Back/Continue/error/unmount restore portrait orientation and system bars.
7. Localization fallback never invents a region and still offers an original-image/Continue path.
8. Loading never presents a blank or falsely completed `0:00 / 0:00` renderer state.
9. No video generation/playback/TTS/encoder/worker/auth/persistence/FEAT-003 change is included.

## 9. Verification evidence

- TypeScript renderer contract/player tests: intro gating, hotspot hit testing, empty-canvas chrome,
  event ordering, timer cleanup, replay and reload.
- Backend contract tests: localized region identity, bounded coordinates, fallback and max-three
  target policy.
- Android emulator evidence: fullscreen landscape, intro, direct subject tap, chrome hide/show,
  fallback, Back/Continue orientation restore and no blank loading state.
- Feature-local evidence note with sanitized logs and screenshots only.

## 10. Approval gate

Implementation starts only after explicit owner approval of this plan. The implementation will stay
on `codex/feat-018-pixi-exploration` and will not touch the video task or unrelated FEAT-026 files.

## 11. Detailed implementation breakdown

### Task A — Freeze the current baseline

Before changing behavior:

1. Record the current branch, commit, dirty files and running app configuration in the feature
   evidence directory.
2. Run the existing renderer, backend and mobile contract tests without modification.
3. Capture the current Pixi screen in both loading and ready/fallback states so the before/after
   comparison is traceable.
4. Confirm that the source image remains available as the immutable fallback at every stage.

This task is read-only except for feature-local evidence files.

### Task B — Define the localization seam

Add a versioned application-level port rather than letting the mobile app call a provider directly.
The port receives:

- `session_id`;
- `experience_spec_ref`;
- source artifact identity/hash;
- confirmed target refs selected from the understanding result;
- the original image reference needed by the localizer;
- a bounded attempt id for retry/idempotency.

The port returns either a valid localization result or a typed fallback decision. The backend must
validate the result before it reaches Pixi:

- target ref must exist in the confirmed understanding candidates;
- target label must be sanitized Vietnamese display text or a safe fallback label;
- `x`, `y`, `width`, `height` must be normalized numbers in `[0,1]`;
- width and height must be greater than zero and below the configured maximum;
- confidence must be in `[0,1]`;
- source hash, session id and spec ref must match the request;
- target count must be `1..3`;
- duplicate target refs and overlapping invalid regions are rejected or deterministically
  normalized;
- a localization model/provider failure must not produce a fabricated region.

The first implementation may use the existing local/runtime adapter and supervised hints. A future
Lightning adapter can implement the same port without changing the mobile or renderer contract.

### Task C — Produce the bounded Pixi payload

The backend maps the validated localization result and existing exploration plan into a single
renderer payload. The payload must be stable for one load/replay cycle and must not expose provider
credentials, local filesystem paths, raw model output or internal error codes.

Proposed payload shape:

```json
{
  "protocol_version": "pixi-exploration-v2",
  "session_id": "uuid",
  "source": {
    "artifact_ref": "safe-ref",
    "content_hash": "sha256",
    "uri": "runtime-safe-uri"
  },
  "intro": {
    "duration_ms": 6500,
    "beats": [
      {
        "id": "canvas-reveal",
        "kind": "reveal",
        "target_ref": null,
        "caption": "Bức vẽ của con đang mở ra."
      },
      {
        "id": "subject-focus-1",
        "kind": "focus",
        "target_ref": "entity-1",
        "caption": "Con đã vẽ một chú chim."
      }
    ]
  },
  "targets": [
    {
      "target_ref": "entity-1",
      "label": "con chim",
      "role": "subject",
      "region": { "x": 0.22, "y": 0.18, "width": 0.31, "height": 0.36 },
      "confidence": 0.91,
      "z_index": 2
    }
  ],
  "learning_bridge": {
    "text": "Chú chim đang ở đâu nhỉ?",
    "next_concept_ref": "safe-ref"
  },
  "fallback": {
    "mode": "NONE",
    "reason_public": null
  }
}
```

The exact field names must be aligned with the existing FEAT-018 TypeScript/Python types before
implementation; the example is a contract direction, not permission to introduce duplicate
schemas.

### Task D — Implement the Pixi state machine

The renderer and React Native screen must use the same bounded phases:

```text
INTRO_LOADING
    -> INTRO_PLAYING
    -> INTRO_COMPLETED
    -> DISCOVERY_READY
    -> DISCOVERY_FOCUSED
    -> CONTINUE_PENDING

Any phase may -> FALLBACK, except a validated focus event must never silently become a fake focus.
```

Rules per phase:

| Phase | Canvas | Hotspots | Chrome | Main action |
|---|---|---|---|---|
| `INTRO_LOADING` | loading shell/source preview | disabled | visible | none |
| `INTRO_PLAYING` | reveal/focus timeline | disabled | auto-hide allowed | pause/replay |
| `INTRO_COMPLETED` | final intro frame | still disabled until ready event | visible briefly | prepare discovery |
| `DISCOVERY_READY` | full drawing | enabled | hidden after idle | tap subject / continue |
| `DISCOVERY_FOCUSED` | focused subject + label | enabled | compact label | tap another / continue |
| `FALLBACK` | original drawing/preview | disabled unless region is valid | visible | retry/back/continue |
| `CONTINUE_PENDING` | stable frame | disabled | visible | handoff |

`INTRO_COMPLETED` and `DISCOVERY_READY` are separate events. The first means the intro timeline
ended; the second means the hit regions were validated and listeners are attached. This prevents a
race where the child can tap before localization is ready.

### Task E — Direct hotspot interaction

1. Transform normalized source regions through the same scale/crop matrix used to render the
   texture.
2. Add bounded hit slop for child-friendly tapping without allowing a hotspot to cover most of the
   canvas.
3. Make the hit area invisible or subtly outlined until tapped; do not draw debug rectangles in
   the child-facing build.
4. On tap, resolve overlaps by `z_index`, then confidence, then stable target order.
5. Emit exactly one focus event followed by one discovery event per accepted tap.
6. Show a short label and gentle outline/zoom. Do not rewrite the source image.
7. Keep the native chip list only in the adult/fallback diagnostic path.
8. Ignore taps while a focus animation is running or debounce duplicate taps within the same
   target.

### Task F — Intro timeline and visual treatment

The intro is not a passive loading screen. It must communicate a short visual story:

1. Fit the entire original drawing into the landscape canvas.
2. Reveal the drawing with a soft mask/wipe or progressive opacity, preserving original pixels.
3. Move the camera gently toward the selected target.
4. Apply a non-destructive outline/glow around the target and optionally its related anchor.
5. Return to a wider view and show the discovery hint.
6. Never invent motion that contradicts the drawing, such as making a stationary bird fly.

Animation must remain deterministic and offline-testable. No generated video, video encoder, TTS,
network fetch inside Pixi, or new AI call from the renderer is allowed.

### Task G — Fullscreen and control chrome

On entry to `PixiIntroScreen`:

1. save the current orientation/system UI state;
2. lock landscape;
3. enter immersive mode;
4. measure the safe drawing viewport after system bars are hidden;
5. load the source and start the intro.

The control overlay consists of Back, play/pause, replay, seek and Continue. It is visible when
entering, after an empty-canvas tap, after a control action and after an error. It hides after the
idle timeout only when the renderer is ready. A subject tap shows the compact subject label but
does not permanently reopen the full control row. Tapping the canvas while chrome is hidden shows
it; tapping the empty canvas while it is visible hides it.

Every exit path must restore the saved state in a `finally`-equivalent cleanup:

- Android Back;
- Continue;
- source error;
- retry;
- React unmount;
- WebView/player crash.

If the Expo project lacks the required navigation-bar capability, add only the minimal dependency
and record the package/version decision in the feature ADR/decision log. Do not leave the app in
landscape or immersive mode after leaving Pixi.

### Task H — Loading, fallback and error presentation

The screen must distinguish these states:

- opening the source image;
- running localization;
- preparing the intro;
- intro ready;
- discovery ready;
- fallback with original image;
- retrying;
- handoff to the next flow.

The UI copy is short and child-friendly. Parent/guide detail can appear in an expandable adult
area, but raw strings such as `VISION_SCHEMA_INVALID`, `NO_LOCALIZER`, `FALLBACK_REQUIRED`, model
paths, URLs or stack traces must never be rendered in the child-facing view. Errors should be
shown through the existing modal/toast pattern and provide a safe action: retry, use original
drawing, or go back.

The seek bar is disabled until a positive duration is received. While duration is unknown, show a
loading track or no time labels instead of `0:00 / 0:00`. A blank canvas must always have a visible
state message or the original preview.

## 12. File and module impact map

Expected implementation surface, subject to the current repository layout:

- `packages/art-renderer/src/browserPlayer.ts`: intro phases, hit areas, canvas taps, chrome
  events, cleanup and event ordering.
- `packages/art-renderer/src/contracts.ts` or the existing renderer contract module: additive
  event/state/payload types and protocol version.
- `packages/art-renderer/demo/mobile.ts`: source texture/crop lifecycle, including reading bitmap
  dimensions before `ImageBitmap.close()`.
- `apps/ui-mobile/src/screens/Flow2Screens.tsx`: fullscreen lifecycle, intro gating, chrome overlay,
  fallback modal, sanitized user copy and navigation cleanup.
- `apps/ui-mobile/src/context/AppContext.tsx` or the existing API adapter: consume the bounded Pixi
  payload without provider-specific logic.
- `apps/ui-mobile/package.json` and lockfile only if the system UI capability is not already
  available.
- `backend/src/.../scene_exploration.py`, localization application service/port, and supervised
  flow mapper: validation, bounded regions, fallback and payload mapping.
- `backend/tests/...` and `packages/art-renderer/...` tests: contract and state-machine coverage.
- `features/FEAT-018-live-image-canvas-flow/evidence/...`: sanitized logs, screenshots and test
  results.

No changes are planned to video generation/playback, MP4 contracts, TTS, authentication,
persistence, Firebase, S3/Lightning credentials in mobile, or unrelated FEAT-026/FEAT-029 work.

## 13. Test and evidence matrix

### Automated tests

- localization accepts valid normalized regions;
- rejects wrong session/spec/source identity;
- rejects out-of-range, zero-size, duplicate or more-than-three regions;
- maps provider failure to public fallback without leaking provider detail;
- intro cannot emit discovery before `DISCOVERY_READY`;
- intro emits completion once per cycle;
- direct tap maps correctly under contain/cover scaling and device rotation;
- overlap resolution is deterministic;
- empty canvas toggles chrome and the timer is cancelled on unmount/replay;
- control actions reset the idle timer;
- replay resets phase and does not duplicate listeners;
- bitmap dimensions are read before release;
- React Native restores orientation/system bars on every exit path.

### Manual Android evidence

On the configured emulator:

1. enter from Gate B and verify landscape immersive mode;
2. observe non-blank intro loading and the complete intro sequence;
3. confirm no hotspot reacts during intro;
4. tap the actual bird/object on the image after `DISCOVERY_READY`;
5. tap empty canvas to show/hide controls;
6. wait for auto-hide and confirm the artwork remains large;
7. test play/pause/replay/seek after duration is known;
8. test localization fallback and retry;
9. press Back and Continue and verify portrait/system bars are restored;
10. collect screenshots and sanitized logs under the feature evidence directory.

### Exit criteria

The task is complete only when all automated tests pass, the emulator matrix passes, no raw error
codes are visible, and the feature-local evidence note links each acceptance criterion to a test or
screenshot. A live Lightning smoke test is optional for this Pixi-only task; it must use the same
validated payload and must not be required to prove renderer behavior.

## 14. Delivery sequence and commits

Implementation should be delivered in small reviewable commits:

1. `docs(feat-018): finalize pixi fullscreen hotspot contract` — approved plan/ADR/evidence setup.
2. `feat(feat-018): add bounded localization mapping` — backend port, validation and tests.
3. `feat(feat-018): gate pixi intro before hotspot discovery` — renderer state machine/events.
4. `feat(feat-018): add direct image hotspot interaction` — hit testing, focus and captions.
5. `feat(feat-018): add immersive mobile chrome` — landscape/system UI and auto-hide controls.
6. `fix(feat-018): harden pixi loading and fallback UX` — duration/loading/modal/crop cleanup.
7. `test(feat-018): record android exploration evidence` — feature-local evidence only.

Before every commit:

- run the repository security validator;
- verify no `.env`, token, model path, child data or provider credential is staged;
- inspect the staged diff and preserve unrelated dirty worktree changes.

## 15. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Localization is unavailable or inaccurate | bounded confidence/identity validation; original-image fallback; no invented hotspot |
| Hitbox does not align after scaling | use one shared source-to-stage transform and test contain/cover layouts |
| Fullscreen state leaks into other screens | snapshot/restore in cleanup for every exit path |
| Intro feels like a blank loading screen | explicit staged copy, deterministic reveal and progress state |
| Children tap controls accidentally | hide chrome after idle, reserve safe control hit zones and debounce |
| WebView/player reload duplicates events | dispose listeners, generation id per load, exactly-once lifecycle events |
| Large image causes memory pressure | cache one source texture, release only after dimensions/crops are complete |
| Future video integration conflicts | preserve Continue/handoff seam and keep video out of this scope |

## 16. Approval and status transition

Owner approval was given in the current conversation on 2026-09-23. The plan was approved and the
Pixi implementation is now complete for the offline/demo slice:

1. record the approval in `features/FEAT-018-live-image-canvas-flow/approvals/TASK_APPROVAL.md`;
2. implement in the sequence above;
3. update context/decisions/evidence after each meaningful step;
4. run security validation before commit/push.

Implementation status:

- renderer contracts, intro gating, direct hotspot event path, chrome auto-hide, source lifecycle,
  Android fullscreen seam and friendly fallback are implemented;
- backend localization is exposed through `SceneLocalizationPort`, strict `SceneFocusPlanV1`
  validation and the backend-only Lightning `/v2/localize` adapter; unavailable localization still
  stays in the honest whole-image fallback;
- the Gate-A screen uses direct subject hitboxes and `SELECT_SUBJECT`; topic-direction cards are
  retained only as a compatibility read model and are not rendered in the normal flow;
- video/MP4 and provider execution remain excluded as approved.

## 17. Proposed fix — Lightning `/v2/localize` 422 contract mismatch

Status: `IMPLEMENTED — OFFLINE VERIFIED; LIVE LIGHTNING SMOKE TEST OWNER-RUN`

### 17.1 Diagnosis

The Lightning log shows `POST /v2/localize 422 Unprocessable Entity`. The failure occurs at
FastAPI/Pydantic request validation, before `localize_v2` executes. The backend adapter currently
sends this `source_image` shape:

```json
{
  "artifact_ref": "...",
  "sha256": "...",
  "content_base64": "..."
}
```

The Lightning `_SourceImageV1` contract requires one additional field:
`content_type: "image/png" | "image/jpeg"`. The adapter already has the original bytes, so it
can derive and validate this value before making the provider request. This is a client/provider
contract mismatch, not a Qwen model failure and not an image-localization quality failure.

### 17.2 Fix scope

1. Fix `LightningSceneLocalizationAdapter` to detect the MIME type from admitted image bytes and
   include `source_image.content_type` in every `/v2/localize` request.
2. Fail closed before transport for an unsupported or unrecognized image signature; do not send a
   guessed extension or a fabricated content type.
3. Keep the existing hash, byte-size, target identity, max-three-target and normalized-region
   checks unchanged.
4. Add a sanitized request-validation log path on the Lightning service so future 422 contract
   failures identify the rejected field/operation without logging image bytes, prompts, tokens or
   child data.
5. Keep the public mobile contract unchanged. The content type is derived at the backend adapter
   boundary and credentials remain backend-only.

### 17.3 Contract acceptance criteria

- A valid PNG localization request reaches `localize_v2` and no longer fails with 422 due to a
  missing field.
- A valid JPEG request carries `content_type: "image/jpeg"` and follows the same path.
- A mismatched signature, unsupported image or digest mismatch is rejected locally/fail-closed;
  it must not call Lightning with an invented MIME type.
- The provider response remains `SceneLocalizationResultV1@1.0` and is mapped to the same bounded
  `subject_regions` projection used by the UI and Pixi.
- Provider/runtime failure remains a friendly `FALLBACK_REQUIRED` state; no raw HTTP status or
  Pydantic error is shown to the child.
- The existing `/v2/vision` path, subject picker, Gate A confirmation and Pixi fallback behavior
  remain regression-free.

### 17.4 Verification plan

- Unit-test the adapter payload for both PNG and JPEG, including exact `content_type` and no secret
  or raw image logging.
- Unit-test unsupported-signature and hash-mismatch fail-closed behavior with a transport spy.
- Add a request-contract regression test proving the adapter payload validates against the Lightning
  `_LocalizationRequestV1` model.
- Run the focused backend contract suite, Ruff, compileall, mobile TypeScript/UI validation and
  Pixi renderer tests.
- Run one owner-controlled Lightning smoke test: image analysis `POST /v2/vision` succeeds, then
  localization `POST /v2/localize` returns 200 and the app receives at least one validated
  `subject_region` when Qwen finds a target. If Qwen returns no usable region, the expected result
  is the explicit fallback state, not a 422.

### 17.5 Implementation result

- `LightningSceneLocalizationAdapter` now derives `image/png` or `image/jpeg` from the admitted
  byte signature and sends the required `source_image.content_type` field.
- Unsupported signatures and digest mismatches fail closed before the provider transport is called.
- Regression coverage validates the exact request against `_LocalizationRequestV1` for both image
  types and covers unsupported signatures and digest mismatch.
- The localization parser now tolerates a fenced JSON response and the previously documented
  nested `region` projection, then normalizes both into the same strict bounded region model.
- 503 diagnostics are now closed reason tokens (`MODEL_OUTPUT_JSON_INVALID`,
  `MODEL_OUTPUT_SCHEMA_INVALID`, `MODEL_OUTPUT_REGION_INVALID`, `MODEL_RUNTIME_TIMEOUT`,
  `MODEL_UNAVAILABLE` or `MODEL_RUNTIME_FAILURE`) without logging model output.
- The live owner-run smoke test remains pending; it requires restarting the Lightning service with
  this commit and consumes the owner-controlled quota.
