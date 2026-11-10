# FEAT-076 Context — Native React Native Parent flow

- Current implementation: Android-only React Native + TypeScript app in apps/mobile.
- Existing composition: AppRoot -> ParentFlowScreen -> ParentWorkflowPort -> ParentDemoWorkflowAdapter. The Fixture lab remains a separate route.
- User objective: add a native version of the Parent story/video demo, using local FE demo data because APIs are not integrated.
- Requirement baseline: FEAT-063 SRS v2.7-draft Rev57 (unsigned); relevant Parent requirements and no-preset open question were reviewed in FEAT-075.
- Related implementation evidence: FEAT-075 final web-flow review; FEAT-071 profile switching; FEAT-072 quota UI; FEAT-073 gender avatars; FEAT-074 grouped settings. These feature records inform implementation but do not supersede the current SRS.
- Initial findings: native flow already had basic route screens, but P06 directly confirmed script without a preflight, REQUEST_VIDEO jumped to playback, profile records lacked gender and only one profile was seeded, and quota/settings were plain demo placeholders.
- Current implementation: native preflight admits once into P07; P07 separately simulates processing, recoverable error and READY; playback is guarded by READY. Two gendered demo profiles, profile creation, quota simulator and two-group settings are present.
- Data boundary: local in-memory demo values only. Do not connect APIs, authentication, storage, real device permissions, media, or generation services.
- Open question retained: no-preset activity catalog behavior remains OPEN under SRS §31.10(13); do not add a fallback activity.
- Build boundary: TypeScript check passes. Android debug APK could not be produced because no Android SDK path is configured in the environment.
