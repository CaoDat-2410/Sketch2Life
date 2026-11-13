# Feature decisions

## D-068-01 Current product behavior source

Use the FEAT-063 SRS v2.5-draft as the current working product/flow authority. Treat the supplied leader-review notes and Rev38 reference images as important context, but do not let older material silently override the current SRS or API source.

## D-068-02 Parent activity and context order

Parent sees lesson outdoor activities after a playable video, as required by SRS §5.1 and FR-PL-16. Preserve an adult review/confirmation of the minimal context snapshot; remove the unrelated choice to opt out of profile age/context fields. Do not add a pre-video activity-selection step.

## D-068-03 Unsupported profile and mismatch fields

Do not add a persisted child gender field because it is absent from the current SRS and API contracts. Do not invent a lesson-deviation two-choice modal without a backend state/contract. Keep the SRS-supported subject confirmation/correction flow and optional lesson script direction.

## D-068-04 Truthful preview states

Use available mounted APIs only where the existing client/auth configuration can call them. For target flows without a mounted authenticated API, retain clearly labelled synthetic preview state or show an unavailable state; never imply that an API write, AI job, video, quota change, or persistence succeeded when it did not.

## D-068-05 Visual implementation

Use code-native layout, CSS, icons, and existing source artwork. The supplied generated Rev38 screen/component PNGs remain reference-only. No new raster asset is required or promoted by this feature.

## D-068-06 App boundaries

The Parent deliverable remains the existing Android React Native host loading the responsive Parent UI from its local WebView bundle. Teacher, School Manager, and Platform Admin remain web workspaces. Do not modify or delete the legacy Child Expo workspace.
