# Plan Rev80 — Parent Android AI run and progressive Teacher sketch guide

**Date:** 2026-11-12 (Asia/Saigon)<br>
**Status:** SUPERSEDED BEFORE SOURCE IMPLEMENTATION by consolidated Plan Rev81 on 2026-11-12, following the owner's explicit request to pause coding and prepare one comprehensive plan. Its Parent verification and Teacher progression requirements are carried forward.<br>
**Authority:** FEAT-063 SRS v2.7-draft Rev60, unsigned; target requirements §§1–31.<br>
**Mode:** Synthetic runtime verification plus a bounded Teacher guide implementation. No publication.

## Objective

Run the Parent app on the already-running Android emulator with a new synthetic turtle drawing, record every AI screen/result and failure, and correct the Teacher Sketch Deck so its drawing guide visibly builds a subject from simple marks to a recognizable finished outline. The attached Teacher slide screenshot is the defect reference: stage 1 has only two dots, stage 2 jumps to a nearly complete butterfly, and later stages mostly change decoration instead of adding construction strokes.

## Approved scope

### A. Teacher progressive drawing guide

- Keep the Teacher lesson/occurrence flow, age context, approved activity content, DRAFT state, and mandatory Teacher review.
- Replace reliance on a single generated multi-panel raster as the step sequence with a versioned, structured construction plan whose strokes are rendered deterministically and progressively. New strokes use a dashed tracing style; each step retains prior strokes and adds meaningful geometry; the last step must form a recognizable subject. The worker output remains untrusted and must pass a strict geometry/order/size validator before display.
- If a valid progressive construction plan is absent or rejected, fail closed to the existing textual instructions and show no misleading raster as if it were a valid step-by-step guide.
- Keep the generic FLUX lesson visual endpoint separate and do not treat a one-shot image as proof of stepwise correctness.
- Add focused contract/renderer tests and a Teacher UI build/test. Use synthetic lesson content only. Do not alter the canonical SRS.

### B. Parent Android synthetic AI verification

- Use the running `Pixel_10_2` emulator and local Compose API, with one clean generated turtle drawing (no name, age, face, or other personal information). Do not use fixture responses.
- Follow the actual Parent UI flow and capture each screen plus every AI result/error: optional line-sketch guide, drawing understanding/subject confirmation, catalog-first activity suggestions (and fallback only if the live catalog provides no eligible candidate), story generation/review, and speech transcription only if the app exposes a usable recording path. Record endpoint/workload, request/call IDs, timings, model/revision and sanitized error codes.
- Check the SRS-target video path and other optional AI surfaces. Make at most one request per available workload. Do not substitute WAN for the SRS LTX-2.5 target. Do not call video generation unless the target worker is deployed/ready and the product API exposes the approved flow; otherwise record the exact missing gate.
- Never retry an ambiguous paid inference automatically. Cap an individual live worker wait at 30 minutes; preserve the run state and error evidence if the cap is reached.

## Acceptance criteria

1. Teacher guide screenshots show cumulative dashed construction: early stages contain only basic forms, later stages add limbs/features/details, and decoration does not replace missing anatomy.
2. Invalid or non-progressive AI geometry is rejected by a focused gate test and cannot be shown as a valid guide.
3. Parent emulator evidence identifies each tested AI result or failure and clearly marks unavailable/unexercised workloads. Every screenshot is stored under this task's evidence directory with no credentials or access tokens.
4. The test drawing is synthetic and differs from a butterfly. Parent results are observed through the real mobile UI and authenticated local API path where available.
5. The report distinguishes a live Modal result from health-only readiness, and a catalog selection from AI-generated fallback.

## Boundaries

- No real child data, production Firebase, provider secrets in logs/screenshots, public publication, destructive DB reset, SRS edits, or changes to account/role/consent policy.
- No source changes outside the Teacher guide implementation/test allowlist and task evidence/plan/approval records. Parent runtime findings are reported for owner follow-up; this task does not silently broaden into unrelated Parent fixes.
- No commit, push, merge, or cleanup of existing user data/containers. Only services/apps started by this test may be stopped after evidence is captured.

## Initial observations

- The provided slide 2 screenshot demonstrates a visual progression defect despite a five-step text deck.
- `teacher.sketch-deck.generate` currently returns text instructions only; `lesson.visual.generate` asks FLUX to create all panels in one image. The UI changes the text step while keeping that composite image static. Existing prompts request progressive strokes but do not validate the generated panel sequence.
- Modal workload registry currently labels all workloads `enabled: false`, and its video candidate is LTX-2.5 contract-only. Runtime calls must first be checked against the actual local API/Modal configuration; a disabled or unavailable workload is a finding, not grounds to bypass the gate.
- ADB is present at `D:\AndroidStudio\platform-tools\adb.exe`; emulator `emulator-5554` is online. The Parent app package is installed. These are preflight observations, not proof that the UI is logged in or that any AI request works.

## Files in implementation allowlist

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/` — focused Teacher guide contract tests
- `backend/src/sketch2life/contracts/schemas/teacher_sketch_deck.py` — versioned geometry contract and untrusted-worker output validation
- `backend/src/sketch2life/interfaces/http/routers/teacher_ai.py` — validate the returned versioned deck before responding
- `backend/tests/unit/test_teacher_sketch_deck_contract.py`
- `apps/teacher-ui/src/components/TeacherDeckPresentation.tsx`
- `apps/teacher-ui/src/components/` — a small reusable SVG construction renderer if required
- `apps/teacher-ui/src/pages/ModalAiLessonFlowPage.tsx` — keep FLUX reference imagery separate from the progressive guide
- `apps/teacher-ui/src/**/__tests__/` — focused component/contract tests
- This plan, `approvals/TASK_APPROVAL.md`, and `evidence/EV-063-89_PARENT_ANDROID_AI_TEACHER_SKETCH_20261112/`

No other source file may be added without recording an explicit plan amendment before editing it.
