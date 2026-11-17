# FEAT-036 evidence index

| Evidence ID | Type | Artifact | Summary / limitation |
|---|---|---|---|
| FEAT-036-EV-001 | screenshot album | `screenshots/ui-current-20261005/` | Eleven evidence images: four preserved from FEAT-035-EV-003 and seven captured from the Pixel 10 AVD. Five of 15 active app screen routes have runtime evidence. See the album README for provenance and hashes. |
| FEAT-036-EV-002 | source review | `notes/UI_AUDIT_20261005.md` | Read-only source and requirements comparison for active mobile screens, activity chooser, video placeholder, and missing web surfaces. No runtime claim for unpictured screens. |
| FEAT-036-EV-003 | capture limitation | `screenshots/ui-current-20261005/README.md` | Source has a 15-screen Web developer switcher (`?dev=true`) and direct-route parameter (`?screen=<id>`), but Expo Web remained blank with an empty root. The native React Native Dev Menu opens but has no app-route selector. `index.ts` does not call Expo's web root bootstrap. |
| FEAT-036-EV-004 | fresh runtime screenshot album | `screenshots/ui-full-20261005/` | Thirteen newly captured PNGs, all with unique SHA-256 hashes. Eleven route components are directly pictured; voice is represented by its reachable inline mode. The Pixi preparation error blocked Video Placeholder, Outdoor Activity, and Feedback. See the folder README for exact coverage and provenance. |

No product code was changed and no test suite was run. The follow-up UI flow used the bundled synthetic drawing through the app's configured local demo workflow; no real child content or production account/data was used.
