# FEAT-018 live image + canvas full-flow plan

- Status: AWAITING_APPROVAL
- Plan revision: 1
- Implementation status: PLANNED

## Goal

Run the complete supervised Sketch2Life flow from one non-sensitive real image selected on the emulator: image capture/import, image validation, Qwen3-VL understanding through the backend-only Lightning adapter, Gate A, P1 activity mapping, Gate B, PixiJS canvas playback, activity handoff, and feedback.

## Scope

1. Add a real image input path using the Android picker/camera-compatible source reference. Preserve the original bytes and provenance; create a bounded working copy only when validation requires it.
2. Add image-quality validation before AI: decodability, dimensions, orientation, luminance/contrast, blur/crop signals, and stable recapture reasons.
3. Replace the CSS-only drawing preview with the approved PixiJS + GSAP controlled WebView/bridge canvas. Render the original image as an immutable source layer and a derived reveal layer without overwriting the source.
4. Extend the backend request contract with a local development image reference/upload handoff. The mobile app sends no provider URL, token, or model credential. The backend sends the image to the existing Qwen3-VL-8B-Instruct adapter and maps the result to VisionUnderstandingResultV1.
5. Preserve ASR as optional for this image-only run; when no narration is supplied, the fusion contract must record truthful missing-source provenance and still require Gate A.
6. Complete Gate A, P1, Gate B, P3/P4 fixture activity selection, Pixi canvas reveal, fallback, handoff, and feedback. Keep fixture mode and deterministic rollback available.
7. Capture sanitized evidence: source hash, image dimensions/type, validation decision, request/model/config IDs, contract status, Gate A/B decisions, renderer events, latency, and screenshot. Never store raw image bytes, prompts, tokens, or provider responses in evidence.

## Acceptance criteria

- [ ] A non-sensitive real JPG/PNG can be selected on the emulator and displayed on the canvas.
- [ ] Original image is immutable, hash-linked, and never replaced by a derived render.
- [ ] Invalid/oversized/unsupported/blurred/dark/cropped input returns stable recapture reasons without an AI call.
- [ ] Valid image reaches backend-only Qwen3-VL-8B-Instruct and returns schema-valid VisionUnderstandingResultV1 with source/model provenance.
- [ ] Mobile bundle contains no provider endpoint, token, or SDK credential.
- [ ] Missing narration is represented truthfully; no fabricated transcript enters fusion.
- [ ] Gate A cannot be bypassed; P1 and Gate B remain versioned and auditable.
- [ ] PixiJS + GSAP canvas renders the original and bounded reveal, preserves the source, and emits renderer lifecycle events.
- [ ] P4 cache hit and safe fallback both complete without breaking handoff/feedback.
- [ ] Fixture mode remains a one-action rollback and all existing FEAT-015/016/017 checks stay green.
- [ ] Evidence and screenshots are stored only under this feature and pass repository security validation.

## Explicit exclusions

Production API/cloud deployment, Runpod, Android release signing, live P3/TTS/video generation, real child data, and any provider credential in mobile or Git.

## Required input for the run

One user-provided or otherwise explicitly approved non-sensitive JPG/PNG (for example a cup, tree, or toy). Do not use a child photo or personal data.

## Detailed person plans

- [Person 1 — Catalog/domain](PERSON_1_DOMAIN.md)
- [Person 2 — AI/image understanding](PERSON_2_AI.md)
- [Person 3 — PixiJS/GSAP canvas](PERSON_3_PIXI.md)
- [Person 4 — Cache/fallback/device evidence](PERSON_4_MEDIA_INTEGRATION.md)
- [Full activity pilot matrix](ACTIVITY_PILOT_MATRIX.md)

The 20 golden activities are the complete first device/integration pilot. The matrix also lists all 100 MVP catalog records for schema/rule/provenance coverage. No record becomes production-eligible through this plan.

## Contract freeze gate

All four person plans are blocked until `CONTRACT_FREEZE.md` is reviewed together. The shared review must approve:

1. contract registry and exact versions;
2. source/provenance/hash semantics;
3. field names and status/error enums;
4. session-version/idempotency behavior;
5. Gate A/B identity rules;
6. renderer/media identity propagation;
7. fixture manifest reconciliation (`VisionUnderstandingResultV1` vs `V2`, and the ACT-0004 objective mismatch);
8. JSON Schema plus positive/negative fixtures for every handoff.

A person may implement only after their upstream contract fixtures are frozen. Contract changes require a versioned change record and updates to every producer, consumer, fixture, and evidence checklist.
