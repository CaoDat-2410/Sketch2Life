# FEAT-085 source register

## Product authority
- docs/context/SRS_AUTHORITY.md
- features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md — canonical v2.7-draft, unsigned, current through local Rev75.

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
