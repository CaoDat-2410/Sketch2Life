# FEAT-086 — Parent video quality

## Goal

Improve the Parent silent-video result so its motion follows the adult-confirmed story, the supplied drawing remains the visual anchor, and the video card has no redundant metadata row beneath the player.

## Status

`APPROVED` for Plan Rev1 by the project owner's direct request on 2026-11-24 to fix the story JSON, generated video, source-art choice, and text below the video. Implementation follows the scoped plan and approval record.

## Current evidence and diagnosis

- The latest generated candidate used `synthetic-sea-turtle-drawing.png`, a polished, clean vector-like synthetic turtle. The generated cartoon appearance follows that input; it is not evidence that LTX can infer authentic child crayon texture from a clean vector source.
- The repository already has a synthetic crayon house-and-sun drawing with visible wax texture and uneven child-like strokes. Its provenance explicitly says it is AI-generated synthetic art, not an authentic child's drawing. It is suitable for a safe style-validation input.
- At the FEAT-086 baseline, the video worker composited a full-frame copy of its conditioning image with an SVG prop and sent it as a second, mid-scene image guide. This could cause the model to interpret the image as an in-scene card/inset. The attached output shows a duplicate miniature-artifact symptom; the redundant guide was removed as the first controlled fix.
- At baseline, the Qwen storyboard returned five fields per scene, including a short visual prompt capped at 280 characters. The video compiler repeated identity, continuity, prop, and negative constraints, which could bury the scene's physical action and result.
- At baseline, `VideoCandidateScreen.tsx` showed duration, scene count, and “Không có âm thanh” below the player. This was UI metadata, not text burned into the MP4; the row is now removed.

## Constraints

- Use only the FEAT-063 v2.7-draft Rev67 SRS as product authority. It remains unsigned. This work changes implementation quality and UI presentation, not product requirements, so the SRS will not be rewritten.
- Keep the current story revision JSON keys and adult-confirmation gate. Do not change quota/admission, safety, auth, consent, or persistence contracts.
- The source drawing is authoritative. Never modify or replace it in place. Preserve its provenance/hash and do not claim synthetic art is a real child's artwork.
- Keep the video silent as already directed by the owner for this implementation. Do not add narration, captions, or overlays to the MP4.
- Do not bypass any hard gate, create real-child data, or retry a failed live video request.
- Preserve all pre-existing worktree changes and do not commit or push.

## Dependencies

- Canonical working SRS: `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`.
- Prior real Parent candidate/playback evidence: FEAT-085, run `c8ab4140-739e-496f-8b11-1c58e4a857a3` (synthetic; five-scene silent candidate).
- Synthetic child-like input and provenance: FEAT-061 `assets/generated/crayon-controls-v1/03-house-and-sun.png` and `evidence/CRAYON_CONTROLS_PROVENANCE_20261029.json`.

## Implementation record — 2026-11-24

- Rev1 initially capped `visual_prompt` at 420 characters and used `story-i2v-v6`. Rev2 below supersedes those prompt details; it preserves the public contract.
- The video worker no longer renders or submits the second full-frame SVG guide. Each scene receives one I2V conditioning image; the existing first-image and prior-scene continuity path remains.
- The Parent ready-player screen no longer renders the duration/scene-count/no-audio footer.
- Real output quality has **not** been validated on this revision. The last bounded runtime check reported an inaccessible Docker daemon pipe and a Modal app listing that did not return. No new Modal inference was sent, and no video was produced for FEAT-086.
- See `evidence/RESULTS_REV1_20261124.md` for Rev1 history and `evidence/RESULTS_REV2_20261124.md` for the current implementation/test results and limitations.

## Rev2 implementation record — 2026-11-24

- Researched the official LTX I2V and prompting guides. The source image supplies visual appearance; the prompt should direct the motion/action after that frame, with chronological physical verbs and relevant camera behavior. A single-shot prompt can be expressed as a focused 4–8 sentence passage. The reviewed community skill was not installed because it is an agent-side creative aid, not a model adapter, and its cinematic embellishments conflict with source-art preservation.
- Qwen's existing `visual_prompt` field now requests 3–4 concise English sentences in present tense and allows up to 900 characters. The sentences specify the opening pose, one approved action's movement/direction/speed/range, contact or reaction when relevant, approved prop placement, and a visible settled/end pose. It forbids unrelated events, entities, scenery, text, or restyling. Public schema version and keys remain unchanged.
- During implementation review, the backend-to-Modal adapter and visual-plan validator were found to cap `model_action_instruction` at 400 characters. Both limits are now 900, aligned with the existing public story field maximum; inputs above 900 remain rejected.
- The LTX compiler is now `story-i2v-v7`. It composes a natural-language paragraph rather than a checklist: shot/framing and initial state; source-art preservation and approved action; chronological action detail; approved prop/entity placement and restrained movement; visible end pose and camera/audio/overlay constraints. With the 3–4 sentence Qwen direction, the intended prompt totals 7–8 sentences. One I2V conditioning image per scene remains.
- Focused verification passed: 98 tests passed and 4 optional LMFE-dependent cases skipped. This verifies prompt/schema/adapter/worker contracts, not generated pixels or video quality.
- Live video remains unverified. No inference was issued because the bounded runtime check did not establish reachable Docker/Modal prerequisites. The only child-like validation asset identified here is the provenance-labeled synthetic crayon drawing; it is not authentic child artwork.
