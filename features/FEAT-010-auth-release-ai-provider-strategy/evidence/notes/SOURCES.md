# Official source evidence

Checked on 2026-08-24.

| Topic | Official source | Recorded fact | Project interpretation |
|---|---|---|---|
| Google Play format | https://developer.android.com/guide/app-bundle | New Google Play apps publish with Android App Bundles; APK is an installable artifact. | Build APKs for devices/internal tests and AAB for Play. |
| Play testing | https://developer.android.com/guide/app-bundle/test | Play supports internal, closed, and open test tracks before production. | Progress from local APK to Play internal/closed testing before public release. |
| Firebase backend auth | https://firebase.google.com/docs/auth/admin/verify-id-tokens | Client sends an ID token over HTTPS; backend verifies integrity/authenticity and extracts `uid`. | Backend owns authorization after provider-neutral token verification. |
| Firebase Android auth | https://firebase.google.com/docs/auth/android/start | Firebase Authentication can be enabled independently and has a local Auth emulator. | Use Auth only; no Firebase data/storage products. |
| Runpod endpoints | https://docs.runpod.io/serverless/endpoints/overview | Queue endpoints expose async `/run` and status operations and require bearer authentication. | Map the existing `AiGateway` to Runpod in production. |
| Runpod keys | https://docs.runpod.io/get-started/api-keys | Restricted keys can limit access per Serverless endpoint. | Use one endpoint-scoped backend runtime key and rotate/revoke it. |

Provider features and Google Play requirements must be re-checked before production release.
