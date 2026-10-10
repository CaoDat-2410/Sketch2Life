# Fresh full-UI capture set — 2026-10-05

## Capture record

- Device: Android Studio `Pixel 10` AVD, `emulator-5554`, API 37.
- Source: fresh `adb exec-out screencap -p` captures from the live emulator; no PNGs were copied
  from the earlier `ui-current-20261005` album.
- Input used to progress the workflow: synthetic butterfly-and-flower drawing already on the AVD
  (`/sdcard/Pictures/FEAT033-test-drawing.png`) and a typed adult subject confirmation. The app used
  its configured local demo workflow. No real child content or production account/data was used.
- The album contains 13 PNGs. SHA-256 comparison found 13 unique hashes and zero exact duplicate
  images. Portrait captures are `1080x2424`; Pixi Intro is landscape at `2424x1080`.
- No product UI or application source code was changed.

## Screens and states

| File | Current UI captured |
|---|---|
| `01-splash.png` | Splash Screen |
| `02-onboarding.png` | Onboarding |
| `03-home-dashboard.png` | Home Dashboard |
| `04-child-profile.png` | Child Profile |
| `05-capture-upload.png` | Capture / Upload with the synthetic drawing selected |
| `06-voice-recording-inline.png` | Capture screen's inline voice-recording mode; no recording was started |
| `07-ai-processing.png` | AI Processing |
| `08-scene-understanding.png` | Scene Understanding; analysis returned no suggested subject, so adult confirmation was entered to continue |
| `09-story-preview.png` | Story Preview with the selected synthetic drawing |
| `10-activity-recommend.png` | Activity Recommendation with two age-matched options |
| `11-experience-review.png` | Parent Review for the selected activity |
| `12-pixi-intro-error.png` | Pixi Intro after renderer preparation failed; retry returned the same app error dialog |
| `activity-recommend-prerequisite.png` | Activity prerequisite state before Gate A had been completed |

## Coverage limits

The active screen map contains 15 IDs. Eleven screen components were directly captured: `splash`,
`onboarding`, `dashboard`, `profile`, `capture`, `ai_processing`, `scene_understanding`,
`story_preview`, `activity_recommend`, `experience_review`, and `pixi_intro`.

The separate `voice` screen component was not reachable from the native app's visible flow; the
current Capture screen exposes voice recording inline, and that state is pictured above. Pixi
preparation failed even after retry, leaving the `video_placeholder`, `activity_detail`, and
`feedback` routes inaccessible through this flow. These four route IDs do not have direct runtime
screenshots in this album.

## SHA-256

| File | SHA-256 |
|---|---|
| `01-splash.png` | `E4A391283DC872498ACD2A8AC5A00D4591E5F36B97624AB0DD2D246BB93F1CC7` |
| `02-onboarding.png` | `3D9AE75D3EDB1ABDBB7696D08A922A7BAAE6DDADBBE81996FA1744CB94B1EF0` |
| `03-home-dashboard.png` | `67EB2A3BAB0CC8E83C0053B9B2CFD3FD839215AFE52018B3FC9FF2AEF8D6A892` |
| `04-child-profile.png` | `805F761B1908F2809EE3D7B60CC353C410A42F1E9672B33E0053FFCFFC6CF2A9` |
| `05-capture-upload.png` | `28FB7956540F62BBB9AA7B555C676A32D97DB51AD127FA5D0186C14009CAC290` |
| `06-voice-recording-inline.png` | `84FC0E4DD7CCB29F9C15D7625188C1EAE1826BA6D7C59526705CAB69455B4439` |
| `07-ai-processing.png` | `10926A99794D9DD45EDFAA48BF0134DCF024B99DB130400630CCBAEC41C39D70` |
| `08-scene-understanding.png` | `D2A147FA2FA4F3D18AE6D279343675C13F0609B2CA2695F5DF09A92780E7DCEA` |
| `09-story-preview.png` | `6C8D2C025A82C8848919D5EA1CB3DFA1FA9AAF12DB180E3CD49FB696106AB920` |
| `10-activity-recommend.png` | `47D909EB3A0426FB65593FBCEEB7DD3BC8D8F1E3FBB4B56793FC1B01899DCD68` |
| `11-experience-review.png` | `34E7771E3FECB450D4A5D771BB8513A0D842618B8A66BB5793D8057AE55BF0EE` |
| `12-pixi-intro-error.png` | `67C4A0188BDD2DFC6BB48405803D00CB2B24AFCD92D1FA45851DECE8850A2D2B` |
| `activity-recommend-prerequisite.png` | `C8CF3AD277F39BA94EC4BBB2DE4B2AF820DB6609CCB37915302BC8E9E4080C90` |
