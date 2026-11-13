# Decisions

## D-067-01 — Keep the Parent prototype visually intact in a bundled WebView

- Status: Approved for the FEAT-067 Plan Rev1 preview task.
- Decision: Use the existing React Native Android app as the installable host and render the existing Parent Vite prototype from assets bundled into the APK.
- Rationale: The user wants the exact Parent UI currently shown at the local URL to appear as an Android app on the emulator. The prototype already contains the complete visual experience and interactions; a local bundled WebView preserves it without replacing it with the separately designed native dashboard.
- Boundary: This is a hybrid preview, not a claim that every screen has been reimplemented with native React Native controls or connected to backend/device APIs.
