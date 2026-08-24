# FEAT-010 authentication, release, and AI-provider strategy

- Status: DONE
- Owner: four-person Sketch2Life team
- Goal: freeze the APK-to-Play release path, managed-auth boundary, and dev/production AI-provider split.
- Scope: ADRs, provider-neutral auth/AI ports and settings, Android build scripts, security/setup guides, validators, context, and evidence.
- Non-goals: creating cloud projects/accounts, adding real Firebase/Lightning/Runpod credentials, implementing sign-in UI, live model calls, producing a distributable APK/AAB on a machine without Android SDK, or using real child data.
- Dependencies: FEAT-009 Android foundation, S3-compatible object-storage boundary, Firebase Authentication, Lightning AI development account, and future Runpod production account.
- Risks: accidentally coupling identity to Firebase Storage, shipping debug-signed APKs as release artifacts, exposing AI provider keys to mobile, and treating an authenticated public endpoint as private networking.

## Context snapshot

The owner selected APK-first internal installation followed later by public Google Play, managed authentication with Firebase acceptable, S3 rather than Firebase Storage, a normal Lightning AI account with about 30 credits for development, and Runpod for production.

Official sources confirm that new Google Play apps publish as Android App Bundles, Firebase clients send ID tokens over HTTPS for backend verification, and Runpod Serverless endpoints use bearer API keys with endpoint-scoped restricted permissions. These sources inform the setup but do not authorize account provisioning or live integration.
