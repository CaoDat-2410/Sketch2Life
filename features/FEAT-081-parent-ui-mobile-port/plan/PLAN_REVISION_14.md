# FEAT-081 Plan Revision 14 — Sync Android Launcher Icon Outputs

## Status and authority

This plan records the owner's direct 2026-11-15 request to replace the mobile app logo. Plan Revision 13 already approves the exact supplied image and Expo icon configuration. This narrow extension synchronizes the tracked Android launcher image outputs from that configuration.

## Goal

Regenerate only the existing Android launcher icon density assets from the approved applied logo so the tracked native project matches `apps/ui-mobile/app.json`.

## Authorized files

| Path | Incoming bytes | Incoming SHA-256 |
|---|---:|---|
| `apps/ui-mobile/app.json` | 1,566 | `4018F93BDFD45B308412121C30D3C9141A1AF96C3747EE7872D4F3F498C18730` |
| `apps/ui-mobile/android/app/src/main/res/mipmap-hdpi/ic_launcher.webp` | 8,217 | `BE194C0EE74498BDC68D0D6ACCE2CD15CA0546B2CA1802CDED18485F7BCBF1EE` |
| `apps/ui-mobile/android/app/src/main/res/mipmap-hdpi/ic_launcher_foreground.webp` | 28,264 | `5CBFFE5268E4824A2210FBAE7FF79BCF79B2D2377BC9235590DA302D53373A22` |
| `apps/ui-mobile/android/app/src/main/res/mipmap-mdpi/ic_launcher.webp` | 4,313 | `7E1F494CB1134FE727AEBFEEEDB60E3CA272AB0922B0003294CA1A7C3DC6BDF7` |
| `apps/ui-mobile/android/app/src/main/res/mipmap-mdpi/ic_launcher_foreground.webp` | 15,336 | `2FA82D7143709D1332F4FFEE8D56B9C70AA2D8CE77330EA14D25AAAAF3A91E33` |
| `apps/ui-mobile/android/app/src/main/res/mipmap-xhdpi/ic_launcher.webp` | 12,771 | `B3362883BA70995F62E23FFE6B2390749B566FABAD979675108909B1736500F4` |
| `apps/ui-mobile/android/app/src/main/res/mipmap-xhdpi/ic_launcher_foreground.webp` | 43,398 | `C2BD6AFC5ACCB48FC85FE82B1FD9F0795C248E1E772367FCB9E9936517059CA7` |
| `apps/ui-mobile/android/app/src/main/res/mipmap-xxhdpi/ic_launcher.webp` | 23,662 | `75B93B8A367393D4ABCC9A7C342C0368D1B1F97CF76A8655116B9C5013E33E66` |
| `apps/ui-mobile/android/app/src/main/res/mipmap-xxhdpi/ic_launcher_foreground.webp` | 80,783 | `0B6F3E0CED230BBBB9B6CE9C925CAE037A664251B455F16122ABC39A86B01523` |
| `apps/ui-mobile/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.webp` | 36,456 | `7D68CA8BB14E672485159C392D467C2BAB44F58CFC31C71C45F391E8688974D8` |
| `apps/ui-mobile/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher_foreground.webp` | 124,949 | `A2DC47B09265B040271DDAF1604C34284234BD39BAA890D49CD033F683A46AA5` |
| `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_14.md` | — | — |
| `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md` | record pre-append pin in Addendum 29 | — |

## Implementation rules

1. Use the already approved `apps/ui-mobile/assets/applied/sketch2life-logo.png` through the local Expo prebuild pipeline: `pnpm exec expo prebuild --platform android --no-install` from `apps/ui-mobile`.
2. Keep changes to the listed launcher density assets. If prebuild proposes unrelated tracked changes, stop and report them without retaining those changes.
3. Do not install packages, build an APK, launch an emulator, run tests, typecheck, validators, diff-check, network, backend, or Modal commands. Do not stage, commit, or push.

## Acceptance criteria

- The ten tracked Android launcher images are regenerated from the approved Expo icon configuration.
- No unrelated Android/native file is changed.
- The user can apply the icon to a device through a later normal app build/install.

## Relationship to prior scope

This plan extends Plan Revision 13 only for regenerating the listed Android launcher images. It supersedes only that plan's prohibition on Android prebuild; all other constraints remain in effect.
