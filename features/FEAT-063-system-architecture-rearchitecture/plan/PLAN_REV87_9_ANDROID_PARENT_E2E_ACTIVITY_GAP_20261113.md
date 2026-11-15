# Plan Rev87.9 — Real Android Parent AI flow and activity-selection gap

**Feature:** FEAT-063 — system architecture rearchitecture<br>
**Date:** 2026-11-13<br>
**Status:** APPROVED by the owner's direct instruction “chạy full flow đi”.<br>
**Requirements:** FEAT-063 SRS v2.7-draft Rev69, unsigned. §§1–31 remain unchanged; append environment-specific evidence to §32 only.

## 1. Why this amendment exists

Rev87.6 stopped because the pre-existing synthetic Parent account's open run cannot be restored. Rev87.7 and Rev87.8 were approved but not executed. A real source review for this full-flow request found another current-code mismatch: `ActivityScreen` renders suggestion cards without selection handlers, while its continue action advances to story; current StoryRun/stories contracts have no selected-main-activity field. The SRS requires a main activity to be selected before story generation.

This amendment runs the actual Android Parent workflow with a clean synthetic account and records this business-rule gap. It will not patch code or manually inject a selection. It may continue through the existing UI's real continue action to verify story generation as currently implemented, but that run is explicitly marked **SRS-nonconformant** because no main activity was selected. It must not be reported as a compliant full flow.

## 2. Objective and exact flow

Exercise the real Parent Android UI and current-worktree backend using one new, uniquely named synthetic Parent account, one synthetic profile with local synthetic authorization, and the new generated non-personal chicken drawing stored at `evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/input-generated-chicken-drawing.png`.

Run these real UI stages in order: signup → synthetic profile/notice → topic `gà` → optional guide enabled → catalog lookup → one real Qwen3.5 guide request if no approved guide exists → advance guide stages → add drawing through the app's gallery/camera picker → confirm context → one Qwen3.5-VL drawing analysis → adult subject confirmation → one catalog-first Qwen activity suggestion → capture the missing activity-selection control/contract as a failed business rule → follow only the actual UI continue button (no manual selection) → one Qwen3.5 story request and adult script confirmation if the API/UI accepts the current state.

Do not generate a video. Skip optional voice recording/transcription. No FLUX, TTS, SAM2, second image, topic mismatch retake, story rewrite, or activity replacement.

## 3. AI/data limits

- Maximum four authenticated UI-triggered GPU inferences: one guide, one drawing analysis, one activity suggestion, one story. One call per workload, hard cap 1,800 seconds each; no retry. If a stage fails, stop dependent stages and preserve the actual diagnostics.
- Guide request is only topic and difficulty; it must use the pinned Arcadia `Gallus gallus` reference and return Qwen3.5 provenance, 4–8 progressive stages, exact sanitized SVG, all current hard gates, `review_required=true`, `persisted=false`.
- Drawing input is synthetic, generated for this test, and contains no real child, face, name, or personal information. No other profile or image is sent to AI.
- Activity suggestion must call the current catalog-first service; do not fabricate or manually choose an activity. The missing main-activity selection is an acceptance failure even if the current app proceeds to story.
- Story can be generated only through the real UI's current route. If API/backend already blocks story without selected activity, stop there; do not bypass it. If it accepts the request, capture and confirm it through the UI but mark the business rule failure clearly.
- No video/FLUX/other workload, warmup, production identity/data, publication, or fixture/canned model result.

## 4. Runtime and cleanup

- Read-only inspect the current worktree, root `.env` key presence (never values), existing local service health, and Modal dev app state. Use existing Rev79 PostgreSQL/Firebase Auth Emulator; never migrate, reseed, replace or stop shared services.
- Start one temporary API built from this worktree on port 8001 in the existing network. Use only process/container-local feature flags; do not edit root `.env`.
- Reuse existing deployed Modal apps; deploy a required app at most once if the current source is not deployed. At most one CPU-only `/health` call per app. No warmup/min-container changes or shared Modal app stop.
- Create exactly one new test Parent identity/profile through the actual UI because the existing seed account is blocked by its incomplete run. Do not record account credentials or ID tokens. Keep the synthetic run and profile for evidence; do not delete anything.
- At completion stop/remove only the task-started temporary API, Metro and emulator. Leave shared containers and volumes running.

## 5. Acceptance and reporting

- Report each real UI/API/Modal stage, exact durations, model revision, request/call identifiers, response contract and gate result. Save only actual AI responses and actual Android screenshots.
- Expected result is a technical end-to-end run up to story confirmation **with an explicit activity-selection business-rule failure** unless the current branch actually presents and persists a selection control. Do not claim SRS compliance if it does not.
- Preserve SVG visual evidence as generated from the actual Modal response. Review whether the stages add coherent chicken strokes rather than filled blocks or disconnected shapes.
- No code changes, SRS target changes, commits or pushes are included.

## 6. Exact path manifest

1. This plan file.
2. `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` (append approval/hash/outcome).
3. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md`.
4. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-4.json`.
5. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/input-generated-chicken-drawing.png`.
6. Actual guide response `generated-guide-draft.json`, extracted `generated-guide.svg`, and rendered `generated-guide-preview.png` under EV-063-101 if returned.
7. Actual drawing-analysis, activity-selection, and story response JSON under EV-063-101 if returned.
8. Actual Parent Android screenshots under `EV-063-101_ARCADIA_STROKE_SKILL_20261113/screenshots/`.
9. `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (append §32 only).
10. `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`.
11. `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`.
12. `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`.
13. `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`.
14. `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`.

No other repository path may change under Rev87.9.
