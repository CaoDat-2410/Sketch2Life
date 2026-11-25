# Plan Rev11 — Clear Capture Intent When Choosing a Learning Path

Date: 2026-11-25  
Status: Approved under Addendum 10; blocker discovered while validating the real Android picker.

## Finding

The home camera shortcut stores `pendingCaptureSource=camera`. If the parent then chooses “Theo chủ đề” or “Theo bài giảng”, that pending intent survives the intermediate screens. On reaching capture, the screen auto-launches the camera and remains busy, so a tap on the gallery control cannot open Android's photo picker.

## Change

Clear `pendingCaptureSource` when the user explicitly selects the topic or lesson path. Preserve direct camera/gallery shortcuts and their behavior. Keep the Android 13+ system Photo Picker permission change from Rev10.

## Acceptance

1. A focused regression check proves both topic and lesson selection clear a pending camera/gallery intent.
2. Mobile tests and typecheck pass.
3. On Android, entering through the camera shortcut, selecting a learning path, and reaching capture does not auto-launch the camera.
4. Tapping the gallery button opens Android's system picker; the child-style synthetic drawing can be selected.
5. No server gates, auth, consent, upload scanning, inference, quota, or safety checks are bypassed.

## Preservation

Do not change the direct camera/gallery shortcut path, API contracts, account data, or run records. No commit/push.
