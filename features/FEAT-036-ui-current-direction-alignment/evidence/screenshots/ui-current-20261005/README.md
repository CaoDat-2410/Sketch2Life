# Current UI screenshot album — 2026-10-05

The folder contains 11 evidence images. Runtime captures are synthetic Android emulator states at
1080 × 2424 on `emulator-5554` (Android API 37, AVD `Pixel 10`). No production data is present.

| File | Screen/state | Source and SHA-256 |
|---|---|---|
| `onboarding-emulator-20261005.png` | Onboarding | Copied from `features/FEAT-035-branch-review-remediation/evidence/screenshots/emulator-debug-current-20261005.png`. SHA-256: `6D9FA5E7C993EABA7A5B07CE3AFA82181C680DC75AE46F5D851FA475847542B9`. |
| `home-emulator-20261005.png` | Home/dashboard | Copied from `features/FEAT-035-branch-review-remediation/evidence/screenshots/emulator-flow-next-20261005.png`. SHA-256: `2D117F3E75F21BE00A9082A494596042883F78AEBCBA8982EDF763E5D2F4FACE`. |
| `profile-emulator-20261005.png` | Child profile | Copied from `features/FEAT-035-branch-review-remediation/evidence/screenshots/emulator-create-20261005.png`. SHA-256: `231EAA92464C20634FFB173D361024AB83DD5E84B6D164A36142559AAFEA3B12`. |
| `activity-recommend-prerequisite-emulator-20261005.png` | Activity recommendation prerequisite (`ActivityRecommendScreen`) | Captured with `adb exec-out screencap -p` from the app already foreground on the emulator; no screen navigation was performed. SHA-256: `CC08EAF6CE95CB0329FA6A32048B5D2EAB1ACE528A4CE8B5EFD179AB79D376E4`. |
| `android-launch-error-emulator-20261005.png` | Initial native launch error before Metro was available | `adb exec-out screencap -p`; shows React Native's “Unable to load script” red screen. SHA-256: `D8B7346980696F4DD048B5325060501C25A5DAE2BE123DA17302880F32774064`. |
| `onboarding-runtime-emulator-20261005.png` | Onboarding, captured from the running Android app | `adb exec-out screencap -p`. SHA-256: `52C55C70EB3A7856377B3C4D63AB4173A883C2B096C153BE92833E3F7CAC8B84`. |
| `dashboard-runtime-emulator-20261005.png` | Home dashboard, captured from the running Android app | `adb exec-out screencap -p`; story-card artwork and system insets are visible. SHA-256: `B035DC548188735CF0261AE2CC586F586B02C46F494FC245BF72AF5C62EE5CA4`. |
| `profile-runtime-emulator-20261005.png` | Child profile editor, captured from the running Android app | `adb exec-out screencap -p`. SHA-256: `6F6438FAB58CF92B4CA08C46CA6A55E87A780A602BC4FC2D604890D8DCC30C3A`. |
| `story-preview-runtime-emulator-20261005.png` | Story preview after the app loaded | `adb exec-out screencap -p`. SHA-256: `6A9C0FC2F1FE851ECDFC7A28F858690B395157AC4A0CA060993486F3EB6BFD85`. |
| `story-flow-gate-runtime-emulator-20261005.png` | Activity recommendation prerequisite (`FlowPrerequisiteNotice`) | `adb exec-out screencap -p`. SHA-256: `EE30FA30FA8AB296508BB95FF855E816F7F01CC33EC555A09EB23983DE5B5E5B`. |
| `react-native-dev-menu-emulator-20261005.png` | Native React Native Dev Menu (Bridge) over Home | `adb exec-out screencap -p`. SHA-256: `C5B7D57D4CD951E8DB930F4699A8E9B89E6D9D6E20FF8750FAA0D2E36C868EBF`. |

## Coverage and limitations

The active app map has 15 screens. Runtime evidence covers five unique app routes: Onboarding,
Dashboard, Child Profile, Story Preview, and the Activity Recommendation prerequisite. The album
also records the initial missing-bundle error and the native developer menu. Splash, Capture, Voice,
AI processing, scene understanding, experience review, Pixi intro, video placeholder, activity
detail, and feedback remain without runtime screenshots.

Source review confirms a developer switcher with 15 entries (`?dev=true`) and direct web screen
selection (`?screen=<id>`). I tried both `127.0.0.1` and `localhost`, including
`?screen=dashboard&dev=true`; each returned HTTP 200 but left the page blank with an empty `#root`.
`apps/ui-mobile/index.ts` currently calls `AppRegistry.registerComponent` directly and does not use
Expo's `registerRootComponent` web bootstrap. That appears to block this preview route from mounting;
it is a capture blocker, not proof of a native-device defect. On Android, `Ctrl+M` opens the standard
React Native Dev Menu (Bridge), but that menu contains runtime tools, not app screen routes. `BaoApp`
reads `?dev=true` only on Web, and its triple-tap clock handler returns on non-Web platforms. The
app initially showed the missing-bundle red screen. After Metro/ADB reverse was available, relaunch
loaded the app; current Android Home has working artwork thumbnails and no observed status-bar or
gesture-navigation collision. Story Preview looked washed out in the default demo state; compare it
with a selected-drawing run before classifying that as a confirmed UI defect.

The mockup PNGs under `apps/ui-mobile/assets/images/` were intentionally excluded because they are
design assets, not current runtime screenshots. These captures are visual smoke evidence, not a
full-flow or device-matrix acceptance run. Five of the 15 active app routes have runtime evidence;
the remaining ten were not navigated through all of their prerequisites.
