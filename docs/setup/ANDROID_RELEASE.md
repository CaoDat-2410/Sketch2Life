# Android APK-to-Google-Play release guide

## Artifact purposes

| Artifact | Command | Purpose | Signing |
|---|---|---|---|
| Debug APK | `pnpm --dir apps/mobile android:apk:debug` | Developer/emulator/device smoke test | Template debug key only |
| Release APK | `pnpm --dir apps/mobile android:apk:release` | Controlled off-Play/internal installation | Production release/upload key injected by CI |
| Release AAB | `pnpm --dir apps/mobile android:aab:release` | Google Play internal/closed/public tracks | Production upload key; Play App Signing for distribution |

APK is installable; AAB is the publishing input from which Google Play generates device-specific APKs. New Google Play apps must publish as AABs.

## Required sequence

1. Install Android SDK Platform 37, Build Tools 37.0.0, platform-tools, and an API 29/API 36 emulator image.
2. Build and smoke-test a debug APK on API 29 and API 36.
3. Before sharing an off-Play release APK, generate the production upload/signing key outside the repository.
4. Back up the key and passwords in an approved secret manager with at least two accountable maintainers.
5. Configure CI signing through runtime secrets; never add `*.jks`, passwords, or `local.properties` to Git.
6. Verify the release APK/AAB is not debuggable, contains no provider credentials, permits no cleartext traffic, and has the expected certificate/package ID.
7. Create the Google Play application for `com.sketch2life.mobile`, enable Play App Signing, then upload the AAB to internal testing.
8. Promote through closed testing only after crash, permission, auth, data deletion, and device-matrix evidence passes.

## Current limitation

This workspace machine has Java but no Android SDK/`ANDROID_HOME`, so no APK/AAB is emitted during foundation setup. Android Studio will create ignored `local.properties`; release signing remains intentionally absent until the key-management task is approved.

Official references: [Android App Bundles](https://developer.android.com/guide/app-bundle), [bundle testing and Play tracks](https://developer.android.com/guide/app-bundle/test), and [developer/package verification](https://developer.android.com/developer-verification/).

The project owner is the accountable custodian for Google Play and the Android upload/release key. A backup/recovery procedure still must be recorded before the first signed off-Play release APK.
