# Pixi visual quality and approved asset integration plan

Status: `DRAFT — AWAITING_OWNER_APPROVAL`

Date: 2026-09-25
Feature: `FEAT-018-live-image-canvas-flow`
Target branch: `codex/feat-018-pixi-exploration`

## 1. Problem statement

The current Pixi screen is technically connected to the renderer WebView, but the live launch
normally contains only one `WHOLE_DRAWING` object. Its timeline is limited to a fade, a small scale
change, a very small translation and a small rotation. The source image therefore looks almost
static, and the existing local SVG library is not visible at runtime.

The visual asset gap is intentional rather than a missing import: the existing FEAT-020 Pixi SVGs
are still `GENERATED_PENDING_REVIEW`, while the repository asset gate allows runtime references
only from approved/applied assets. The fix must therefore connect a reviewed local asset selection
through the renderer contract instead of bypassing the gate or loading arbitrary files.

The screenshot also shows a separate presentation problem: white title text and controls are laid
over a mostly white drawing, so the Pixi stage loses hierarchy and the user cannot tell which part
is moving or interactive.

## 2. Desired outcome

After Gate B, the child sees a short, visibly animated drawing exploration rather than a static
image preview:

```text
intro card / paper frame
  -> drawing appears with ink-like reveal
  -> gentle camera push with parallax background
  -> grounded topic label and visual focus ring
  -> approved local accents enter (sparkles/path/grass/topic accent)
  -> relation cue travels across the drawing
  -> drawing settles and hands off to the video placeholder
```

The child's drawing remains the identity and source of truth. Supplemental art is a compatible
decorative/context layer only; it never replaces, recolors or edits the source drawing.

## 3. Verified current gaps

1. `SupervisedFlowService` emits `original-art` as the only renderer object on the normal
   no-localizer path.
2. The live normal path deliberately does not call `/v2/localize`, so no source-derived crop or
   mask is available. The renderer consequently uses its whole-image fallback.
3. `packages/art-renderer/src/browserPlayer.ts` only loads objects from `animationPlan.objects`;
   it has no approved supplemental-asset loader or layer stack.
4. `mobile.html` has only CSS dots/border decoration. It does not load the repository's SVG asset
   candidates, and its white overlay chrome has weak contrast on the source artwork.
5. The current fallback motions operate on the same full-image sprite. A transform technically
   runs, but there is no depth contrast or independent moving element that makes the motion legible.
6. The existing FEAT-020 asset catalog and SVGs are generated candidates, not runtime-approved
   assets. They must pass visual/rights review before they can be copied to an applied runtime path.

## 4. Scope

### Included

- Review and select a minimal local asset set from the existing hand-authored Pixi candidates.
- Record provenance, hashes, visual review and rights status in the governed feature asset records.
- Add a typed, allowlisted supplemental-asset selection to the Pixi launch contract.
- Copy only approved/applied local SVGs into the renderer build output; no runtime network fetch and
  no provider generation.
- Add a layered Pixi scene with:
  - immutable original-art backplate;
  - low-amplitude camera/world movement;
  - independent foreground/support decoration layers;
  - visible focus ring/spotlight and relation path;
  - bounded particle/sparkle motion;
  - topic-aware but deterministic asset selection.
- Make motion states visually legible: intro, reveal, focus, relation cue, settle and ready.
- Improve landscape Pixi chrome contrast, caption placement, loading copy and control affordance.
- Preserve the current fast topic-first flow: no `/v2/localize` request and no second AI request.
- Add contract, renderer, backend, TypeScript and Android smoke evidence.

### Excluded

- Reintroducing image tapping/localization into the normal understanding path.
- Generative image/video assets, remote asset URLs or runtime provider calls.
- Changing Gate A, Gate B, ExperienceSpec identity, activity matching or the future video worker.
- Replacing the original drawing with a catalog sprite or generated reconstruction.
- Claiming that a crop/mask exists when localization is unavailable.

## 5. Proposed implementation

### 5.1 Asset review and selection

The first runtime-approved set should be small and visually safe:

- `pixi.motion.sparkle` — reveal/emphasis;
- `pixi.motion.path-dots` — relation/direction cue;
- `pixi.scene.grass` — foreground grounding;
- `pixi.scene.sun` — background framing when compatible;
- `pixi.scene.flower` and `pixi.scene.butterfly` — only when the confirmed topic/context makes
  them semantically appropriate, never as a generic replacement for the child's subject.

The selected files remain separate from the child's source. Each runtime item must carry an asset
ID, version, local asset reference, SHA-256, `APPROVED` review status and `CLEARED` rights status.
If the owner does not approve a candidate, the renderer falls back to procedural Pixi shapes and
the original drawing; it must not load the rejected file.

### 5.2 Contract and backend composition

Extend the additive renderer launch contract so the manifest can contain one original asset plus a
bounded list of approved supplemental assets. Keep source-art hash invariants for original-art
objects and use the supplemental file hash/provenance for decorative objects.

Add a deterministic selector in the application boundary:

```text
confirmed subject / relation / activity concept
  -> allowlisted semantic asset candidates
  -> at most 4 approved supplemental assets
  -> renderer manifest + scene layer hints
```

No model call is added. Unknown or weakly matched topics select only generic motion assets. The
backend should emit a short scene recipe, not raw file paths or arbitrary model instructions.

### 5.3 Renderer scene

Refactor the player into explicit containers:

```text
stage
├── background wash / paper frame
├── backplate: original drawing
├── support layer: grass / sun / context accent
├── motion layer: sparkle / path-dots / focus ring
└── caption-safe overlay region
```

The default 6–8 second timeline will contain visible, bounded beats:

1. `0.0–1.0s`: paper frame and source drawing fade/scale in together.
2. `1.0–2.4s`: camera/world push with a noticeable but safe parallax offset.
3. `2.4–3.8s`: topic label appears; focus ring pulses around the declared focal area when a
   validated focus region exists, otherwise it uses a non-specific whole-drawing focus treatment.
4. `3.8–5.4s`: path-dots or sparkle cue travels across the scene; support asset has an
   independent sway/drift motion.
5. `5.4–7.0s`: caption/learning bridge appears and all layers settle into a clear handoff state.

Where no localization exists, the scene must not pretend to isolate a subject. It can still show
real motion through independent approved accents, camera movement and a source-preserving reveal.
When a future valid focus plan is provided, existing crop/mask support remains available and the
focus layer can be upgraded without changing the user flow.

### 5.4 Mobile visual treatment

- Use an opaque dark translucent header and bottom control rail with minimum contrast against both
  white paper and dark stage backgrounds.
- Keep the caption in a dedicated safe band instead of covering the artwork's most important area.
- Show staged loading copy: `Đang mở bức vẽ`, `Đang thêm chuyển động`, `Sẵn sàng khám phá`.
- Keep controls auto-hidden after idle, but show a compact hint on first load so the screen does not
  look frozen.
- Make `Tiếp tục` clearly available after the sequence is ready; do not require a tap on the image.

## 6. Acceptance criteria

1. A normal live launch contains one preserved original-art object and only approved supplemental
   assets; no generated or unreviewed file is loaded.
2. The renderer visibly shows at least three independent visual changes during one playback:
   source reveal/camera motion, an independent decorative motion, and a focus/relation cue.
3. The source drawing remains recognizable, unmodified and present for the entire experience.
4. The scene uses topic/learning context deterministically; a bird topic cannot silently select an
   unrelated activity or decorative story asset.
5. Missing localization remains an honest whole-drawing mode and does not issue another AI request.
6. Header, caption, timeline and continue controls remain readable over light and dark source art.
7. Playback, replay, seek, retry, back and continue still synchronize with the renderer protocol.
8. Asset rejection, load failure or invalid provenance falls back to procedural accents plus the
   original drawing, with a friendly child-facing message and no raw error code.
9. Renderer tests cover asset allowlisting, layer composition, motion timing, fallback and cleanup.
10. Backend contract tests, TypeScript/typecheck, asset-gate validation, repository security and
    Android landscape smoke evidence pass.

## 7. Evidence to capture

- Asset review record with selected/rejected IDs, provenance and hashes.
- Backend launch JSON summary proving original + approved supplemental manifest identity.
- Renderer test output for normal, missing-localization and asset-load-failure cases.
- Android screenshots at intro, mid-motion and settled states showing actual visual differences.
- Metro/backend health checks and no fatal React Native/WebView errors.
- `python tools/validate_repository_security.py`, focused tests and `git diff --check` output.

## 8. Approval gate

Implementation remains blocked until the owner approves this plan and the selected generated SVG
assets pass the frontend visual asset gate. The implementation must then update
`approvals/TASK_APPROVAL.md`, `CONTEXT.md`, `DECISIONS.md` and feature-local evidence as the work
progresses.
