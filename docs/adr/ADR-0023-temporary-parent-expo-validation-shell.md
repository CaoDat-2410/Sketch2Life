# ADR-0023: Temporary Parent Expo validation shell

- **Status:** Accepted for the temporary FEAT-063 Rev73 implementation only; final Android stack decision remains open.
- **Date:** 2026-11-11
- **Decision owners:** Project owner (direct request), implementation recorded by Codex.

## Context

The canonical FEAT-063 v2.7-draft SRS Rev62 is unsigned and §9.3 records `apps/mobile` (React Native 0.87) as the current Android target. The repository also contains `apps/ui-mobile`, an Expo SDK 52 application, but its current Parent demo uses a legacy flow and fixture-capable service. The owner requested a temporary Expo Android UI with separate Parent workflow screens, real API integration and live Modal testing.

## Decision

Use `apps/ui-mobile` as an isolated temporary Expo host for a concise Parent workflow prototype and its Android validation. Replace only its mounted app entry and add a dedicated Parent implementation that calls current Firebase Auth and `/api/parent/v1` contracts directly. Preserve the existing React Native `apps/mobile` source and its ownership boundary. Do not interpret this ADR as a final migration of the Android product to Expo or a change to SRS §9.3.

The prototype uses no generated UI images, no fixture fallback and no child artwork until the mandatory image-selection screen. The E2E stops after adult story confirmation; video generation remains out of scope.

## Consequences

- The owner can review a navigable Android Parent flow without replacing native application work.
- Some auth/API adapter code may be duplicated temporarily; a later migration decision should consolidate it behind a shared package if Expo is selected.
- Android permission/configuration changes are limited to the Expo app and do not alter `apps/mobile`.
- Production architecture, final mobile framework and release approach remain unresolved and require a separate owner decision and SRS/ADR update.

## Alternatives considered

1. Build directly into `apps/mobile`: rejected for this temporary UI task because the owner explicitly requested Expo and the native app has unrelated in-progress changes.
2. Continue using the existing Expo Parent demo: rejected because it carries legacy workflow semantics and fixture fallback.
3. Migrate the whole Android app to Expo: not decided here; broader than the requested temporary workflow skeleton.
