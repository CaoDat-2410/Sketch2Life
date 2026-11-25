# Plan Rev10 — Android Photo Picker Permission Path

Date: 2026-11-25  
Status: Approved under Addendum 10; scoped to the blocking Android Parent E2E photo selection.

## Finding

The Android 16 emulator has the system Photo Picker, but the Parent screen waits in its image-selection busy state before the picker appears. The app only declares legacy `READ_EXTERNAL_STORAGE`; the emulator reports that permission denied. Android 13+ provides a system picker that grants access to the selected URI without broad media-library permission.

## Change

For Android API 33+, launch Expo Image Picker's library selection without first requesting broad media permission. Retain the existing permission request on iOS and Android API 32 or earlier. Keep camera permission handling unchanged. Continue to use the actual Android photo picker and its URI grant; do not read MediaStore directly from the app.

## Acceptance

1. Pure tests cover Android API 32, Android API 33+, iOS, and unknown Android API level.
2. Mobile typecheck and full mobile tests pass.
3. In the emulator, tapping “Chọn từ thư viện ảnh” opens the system picker and both synthetic drawings can be selected.
4. No permission, upload, scanning, analysis, quota, or safety gate is bypassed.
5. Complete the two approved Android-to-backend-to-Modal runs and record scripts, videos, and timings under the feature evidence folder.

## Preservation

Do not change camera permissions, API contracts, Firebase records, user credentials, run records directly, or media-provider data outside the two generated synthetic drawings. No commit or push.
