# Plan Rev87.8 — Real Android Parent full flow through story approval

**Feature:** FEAT-063 — system architecture rearchitecture<br>
**Date:** 2026-11-13<br>
**Status:** APPROVED by the owner's direct instruction “chạy full flow đi”.<br>
**Requirements:** FEAT-063 SRS v2.7-draft Rev69, unsigned. Keep §§1–31 unchanged; append environment-specific evidence to §32 only.

## 1. Objective and scope

Run the real Parent Android workflow from signup/profile authorization through optional line-sketch, drawing intake, image understanding, activity selection, story draft and adult script confirmation. Stop before video generation. No fixture or canned AI response is allowed.

Rev87.6 found that the existing synthetic Parent account has an incomplete active StoryRun that the UI cannot restore. Do not repair, delete or reuse it. Create exactly one uniquely named synthetic Parent account through the real signup UI, one synthetic profile and local synthetic consent in the existing Firebase Auth Emulator/PostgreSQL stack. This is a local test identity, not a real child or legal-consent record; retain it and its test run for evidence.

Use one newly generated, non-personal child-style chicken drawing as the actual gallery/camera input. The AI workload sequence is limited to one request each: Qwen3.5 SVG topic stroke guide (`gà`), Qwen3.5-VL drawing understanding, catalog-first activity suggestion, and Qwen3.5 story generation. Use the real Android UI and current-worktree API for every Parent step. No direct worker/API bypass of a UI step.

The SVG guide uses the pinned Arcadia Science `Gallus gallus` visual reference plus the whiteboard-animation authoring skill. It must be new line geometry with 4–8 progressive stages and pass the current strict sanitizer/schema/topic/anatomy/reference gates. The guide is optional and is enabled for this run. Parent activity selection follows the approved catalog-first rule: send eligible published/shared catalog candidates and the synthetic profile/topic/recognized subject to Qwen, select one main activity before script, and let the adult request a replacement only if the first choice is unsuitable. No replacement inference is allowed under this plan; if requested or required, stop and record it.

## 2. Real UI workflow

1. Use the existing Android emulator or start the installed Pixel_10 AVD. Start Expo Android from this worktree and connect only to the temporary local API and existing Firebase Auth Emulator; do not edit the root `.env`.
2. Sign up one unique synthetic Parent account in the app. Create one synthetic profile in the supported 3–10 age band and accept the configured local synthetic-data notice. Do not use any actual child's name, photo, audio or profile.
3. In Parent UI, choose topic `gà`, enable the optional line-sketch guide, load the catalog first, and request one real AI guide only if no approved catalog guide is returned. View and advance through its stages.
4. Add the generated chicken drawing through the actual Parent camera/gallery UI. Continue through analysis, adult subject confirmation, one catalog-first activity recommendation and selection of one main activity, then generate and confirm the story/script. Capture each meaningful screen and the actual outputs.
5. Stop before any video action. No LTX, FLUX, TTS, Whisper, SAM2 or other optional workload is part of this run.

## 3. Data and runtime boundaries

- Reuse existing shared Rev79 PostgreSQL and Firebase Auth Emulator only. No migration, reseed, seed-script run, profile reuse, existing StoryRun mutation, shared service replacement, volume reset, or deletion.
- Keep the single new test account/profile/run clearly synthetic. Record no email, password, Firebase ID token, service credential, or secret in evidence.
- Use a temporary API container built from this worktree on host port 8001 and the existing Docker network. Enable the needed development capability only in this container environment. No `.env` edit.
- Reuse the Modal apps for Qwen3.5 language/SVG/story/activity and Qwen3.5-VL drawing analysis. Read-only list first. At most one deploy per required app if needed for the current source; one CPU health check per deployed app at most; no warmup or minimum-container changes.
- GPU cap: at most four authenticated UI-triggered inferences total, one per workload (guide, drawing understanding, activity selection, story). Hard cap 1,800 seconds each. No retry, replacement activity, second topic, or second sample. If a stage fails, preserve actual diagnostics and stop dependent stages.
- Keep outputs private, review-required where applicable, and un-published. The SVG guide must report `persisted=false`. The script can only be confirmed by the synthetic test adult in the test account.
- Stop/remove only task-started temporary API, Metro and emulator. Leave shared Docker services and shared Modal Apps deployed; do not delete local volumes or test records.

## 4. Acceptance criteria

- The Android UI completes signup, local synthetic profile/authorization, topic, optional SVG guide, drawing intake, image understanding, adult subject confirmation, activity choice, story draft and adult script confirmation.
- The guide is a real Qwen3.5 Modal response with Arcadia provenance, a sanitized recognizable chicken line drawing, 4–8 coherent cumulative stages, and all current hard gates passed. No filled block collage or canned response.
- Drawing understanding matches the synthetic drawing and selected topic, or the UI correctly stops at its mismatch/retake gate. The activity result is based on eligible catalog entries and the test profile/context; one main activity is selected before story. Story is generated and reviewed in the UI.
- No video inference occurs. Actual API/Modal timings, model revisions, request/call IDs, gate outcomes, screenshots, and cleanup state are recorded without credentials.

## 5. Exact path manifest

1. This plan file.
2. `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` (append owner approval, hash and outcome).
3. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md`.
4. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-5.json`.
5. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/input-generated-chicken-drawing.png`.
6. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/generated-guide-draft.json` and `generated-guide.svg` (actual response only).
7. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/generated-guide-preview.png` (actual response render only).
8. Actual response JSON for drawing analysis, activity selection and story draft under the same EV-063-101 evidence directory, only if returned.
9. Actual Android screenshots for the Rev87.8 Parent flow under `EV-063-101_ARCADIA_STROKE_SKILL_20261113/screenshots/`.
10. `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (append §32 only).
11. `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`.
12. `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`.
13. `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`.
14. `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`.
15. `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`.

No other repository path may change under Rev87.8.
