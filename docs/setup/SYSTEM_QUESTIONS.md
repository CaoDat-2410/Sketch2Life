# System decisions and remaining questions

## Resolved on 2026-08-24

1. Android namespace/application ID: `com.sketch2life.mobile`.
2. Platform: Android-only; no iOS target.
3. Android SDKs: min 29, target 36, compile 37. Re-check Play Console reach before release.
4. Mobile workflow: bare React Native CLI 0.87.
5. Product modes: child, parent, and guide remain role-based modes in one app.
6. Progress transport: bounded HTTP polling for MVP, reversible through ADR-0004.
7. AI access: backend-only authenticated adapters; the current Lightning account is fixture/dev and is not treated as private networking.
8. Distribution: APK-first device/internal testing, then Google Play AAB through test tracks to public release.
9. Managed identity: Firebase Authentication only; Firebase data/storage products are forbidden.
10. AI lifecycle: Lightning fixture/dev on the current normal account; Runpod Serverless production.
11. Account model: only parent/guide users authenticate; child mode has no independent child account.
12. Initial sign-in methods: Google Sign-In and email/password.
13. Ownership: project owner controls Firebase, Google Play, and Android release/upload key custody.

## Still open before authentication/product integration

1. What retention/deletion period applies once the project moves beyond synthetic fixtures?
2. Which Runpod region/GPU/model profile meets the later production benchmark and data-residency requirement?
3. Which AWS region/services and S3 bucket lifecycle policy will be selected for production?
4. Which monitoring/crash-reporting provider will be accepted after privacy/redaction review?
