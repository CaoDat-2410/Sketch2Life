# FEAT-084 source register

## Product authority

- `docs/context/SRS_AUTHORITY.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` — v2.7-draft, unsigned; current baseline through Rev75.

## Product requirements used

- §5.1, Parent workflow: optional topic/lesson path, three topic and three drawable-subject suggestions, separate custom input, validation, and later adult/VLM subject confirmation.
- §31.20, Rev70: Parent topic and drawing-subject suggestion UI behavior.
- §31.22, Rev74: 18-topic catalog, nine subjects per topic, rotating cards, and out-of-catalog custom object entry/validation.

## Implementation sources reviewed

- `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx`
- `apps/ui-mobile/src/parent/presentation/components/ui.tsx`
- `apps/ui-mobile/src/parent/presentation/screens/`
- Existing approved artwork under `apps/ui-mobile/assets/topics/`

## Evidence

- Source audit: `evidence/MOBILE_UI_SOURCE_REVIEW_20261123.md`
- Android screenshots and reachability report: `evidence/ANDROID_UI_SCREENSHOTS_20261123.md` (2026-11-23).
