# Official source evidence

Checked on 2026-08-24.

| Topic | Official source | Recorded fact | Project interpretation |
|---|---|---|---|
| Android distribution | https://developer.android.com/about/dashboards | Public page says platform-version data is available in Android Studio's Create New Project wizard and Play Console Reach and devices; public snapshot does not provide the version percentages. | Do not claim an unsupported market-share percentage. Re-check Play Console before release. |
| Google Play target | https://support.google.com/googleplay/android-developer/answer/11926878 | New apps and updates must target Android 16/API 36 or higher from 2026-08-31. | Use targetSdk 36. |
| React Native toolchain | https://reactnative.dev/blog/2026/08/11/react-native-0.87 | RN 0.87 requires Node >=22.13, AGP 9, Kotlin 2+, minCompileSdk 34, and uses compileSdk/buildTools 37. | Keep RN 0.87 and compileSdk 37. |
| API mapping | https://developer.android.com/guide/topics/manifest/uses-sdk-element.html | Android 10 maps to API 29; targetSdk and minSdk are independent. | Choose API 29 as the explicit compatibility floor while targeting API 36. |
| Lightning private deployment | https://lightning.ai/docs/security/privacy/deployment-options | Lightning documents BYOC and BYOC with VPN; BYOC-with-VPN is for stringent security and keeps communications off the open internet. | Prefer BYOC-with-VPN and verify Enterprise/account availability before live integration. |
| Lightning security | https://lightning.ai/docs/security/security-features/disk-encryption | Lightning documents TLS 1.2 in transit, AES-256 disk encryption, and a Make all traffic private cloud-account setting. | Enable private traffic and encryption controls; keep provider access backend-only. |
| Lightning secrets | https://lightning.ai/docs/overview/ai-studio/managed-secrets | Secrets are encrypted and injected at runtime. | Use managed runtime secrets; never place them in mobile/source control. |

`minSdk 29` is a project tradeoff, not a Google-published statement that Android 10 is the majority in 2026. It keeps a seven-year compatibility window while avoiding extra legacy branches for an image/audio/WebView-heavy capstone. The team must validate actual audience/device data before public release.
