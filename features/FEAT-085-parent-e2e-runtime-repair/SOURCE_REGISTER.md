# FEAT-085 source register

## Product authority
- docs/context/SRS_AUTHORITY.md
- features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md — canonical v2.7-draft, unsigned, Rev57 baseline with local amendments through Rev67, per `docs/context/SRS_AUTHORITY.md`.

## Requirements relevant to this task
- SRS §5.1 and BR-42: Parent may choose lesson or topic/object intent before drawing; image capture remains required; actual subject is analyzed and adult-confirmed after capture. Lesson activities and topic path stay distinct.
- SRS Parent flow requirements: profile/context eligibility, story review before video, persisted session state and authorized data scope.
- SRS BR-38: video requires normal admission and idempotent accounting. This test uses eligible synthetic/dev quota; it must not bypass or falsify admission.
- SRS child-data and AI safety requirements: no real-child data; preserve consent, access, schema and safety gates.
- Canonical AI deployment / worker contracts in FEAT-063; runtime status must be reported separately from target requirements.

## Implementation evidence reviewed before changes
- features/FEAT-084-parent-mobile-ui-polish/evidence/ANDROID_UI_SCREENSHOTS_20261123.md
- features/FEAT-084-parent-mobile-ui-polish/plan/PLAN_REV3_EXISTING_SYNTHETIC_LOGIN_SCREENSHOTS_20261123.md
- Parent Expo auth, Parent controller and API adapter sources.
- Root .env key names/config wiring only; secret values are never written here.
- Docker/backend and Modal runtime health/logs captured during this task.

## Evidence to add
- evidence/PARENT_ANDROID_E2E_REPORT_20261123.md
- evidence/screenshots/ and evidence/generated/ for genuine UI and AI outputs; omit credentials, tokens, private child data and raw provider prompts that contain sensitive input.
- Added: `evidence/RESULTS_PARENT_E2E_AFTER_HF_TOKEN_UPDATE_20261123.md` and runtime screenshots/logs under `evidence/runtime/`; the report explicitly separates candidate readiness from unverified player playback.
- Added: `evidence/ANDROID_HMR_RUNTIME_FIX_20261124.md` and `evidence/runtime/root-parent-app-20261124.png` for the root Metro helper-resolution repair. The separate 16 KB native-library notice is documented as unresolved.
- Added: `evidence/PARENT_POST_LOGIN_SAFE_AREA_FIX_20261124.md`, `evidence/runtime/parent-after-login-safe-area-fix-20261124.png`, sanitized auth log, and accessibility hierarchy for the post-login SafeAreaProvider crash and its emulator verification.

## 2026-11-25 drawing failure evidence
- Canonical requirement source: features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md (current authority per docs/context/SRS_AUTHORITY.md).
- Approved scope: plan/PLAN_REV9_DRAWING_CONTRACT_AND_RESUME_FIX_20261125.md and Addendum 15 in approvals/TASK_APPROVAL.md.
- Real worker/UI/DB evidence and offline test results: evidence/DRAWING_BOX_AND_RESUME_RECOVERY_20261125.md.
- Synthetic Android input drawings: evidence/ANDROID_PARENT_TWO_E2E_20261125/drawing-1-butterfly-synthetic.png and drawing-2-bicycle-synthetic.png.
- 2026-11-25 Modal dispatch diagnosis after Addendum 19: `evidence/ANDROID_PARENT_TWO_E2E_20261125/REPORT.md`. This is a failed/blocked real UI attempt, not a completed E2E. It records safe `ACCOUNT_QUOTA_OR_LIMIT` classification, zero Modal inputs/containers, API health and focused test results, and the second drawing that was deliberately not submitted.
- 2026-11-25 Addendum 20 outcome: the second-topic synthetic butterfly run reached UI topic/subject selection and drawing attachment, then Modal rejected both bounded spawn attempts before a call ID. Catalog alias validation resolved `butterfly` to `con bướm` without AI. No activities, script, or video were produced; report and screenshots are in `evidence/ANDROID_PARENT_TWO_E2E_20261125/REPORT.md`.
- Owner-pasted older Modal call log: accepted Qwen3.8-27B-FP8 drawing inference ended with `BOX_INVALID`; local strict box prompt/validator test passes, but live deployment is unverified. This is separate from the pre-call resource rejection.
- Rev17 activity handoff and post-`.env` real retry evidence: `plan/PLAN_REV17_SUBJECT_CONFIRMATION_PROJECTION_AND_ACTIVITY_HANDOFF_20261125.md`, Addendum 23, and `evidence/ANDROID_PARENT_TWO_E2E_20261125/REPORT.md`. The run's real Qwen3.8 drawing analysis passed; GET run/activity returned 200 after API-only rebuild; the isolated Lesson Library had zero items/versions, so story/video were not reached.
