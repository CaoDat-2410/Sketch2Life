# Parent mobile UI source review — 2026-11-23

- **Evidence ID:** EV-084-01
- **Type:** Source review
- **Reviewer:** Codex
- **Reference:** Current FEAT-063 SRS Rev75 and all 27 `*Screen.tsx` components under `apps/ui-mobile/src/parent/presentation/screens/`, plus `ParentBottomBar.tsx` and shared `components/ui.tsx`.
- **Method:** Source inventory of all 27 screen components and the bottom bar, with targeted copy/layout review of topic, subject, activity, capture, lesson gallery, story, home, profile, settings, auth, notifications and video screens; compare shared components, palette and artwork references. No app was launched; this is not emulator visual evidence.

## Key findings

- Topic suggestions already have a mobile UI. `TopicScreen` renders server-provided cards, a separate custom-topic field, refresh, skip, loading, error and continue actions.
- Drawing-subject suggestions already have a mobile UI. `DrawingSubjectScreen` renders server-provided cards and a separate custom-subject input with validation states. The cards lack illustrative cues and repeat the topic/custom-entry explanation.
- `ActivityScreen` is the most text-dense Parent flow screen. Several headings explain the same selection/context, and the catalog source label can include an internal lesson-version UUID. Activity instructions and safety notes are useful adult-review content and must remain.
- `CaptureScreen` repeats the photo/recognition explanation in its heading, card, empty state and bottom notice. One clear transfer explanation can replace the duplicate copy without changing behavior.
- `StoryScreen` contains both the full story and scene-by-scene review. This is long by design because the adult must review the generated script/storyboard before confirmation; keep it intact.
- `LessonGalleryScreen` detail sections contain learning objectives, drawing steps, subject notes, optional story direction, activity materials/instructions and safety notes. These are lesson content, not decorative prose; preserve them in this scope.
- Consent, account, profile, invitation, notification, quota, failure, reconciliation, confirmation and video-safety messages explain real user decisions or system states. Do not remove them merely to shorten screens.
- The creative flow uses `Card`, `Notice`, `ScreenFrame`, shared button components and the `creative*` palette. Before this change, the topic screen had artwork for only part of the catalog and reused the nature illustration for other IDs. The shared visual map now uses existing artwork where it fits and topic-specific icon/color fallbacks for every catalog topic.

## Screen inventory and disposition

| Screen | Review disposition |
|---|---|
| Account | Preserve credential/security and error details. |
| Activity | Polish: compact redundant copy; remove internal lesson-version ID from user-facing label; retain instructions/safety. |
| Auth | Preserve sign-in, consent and authentication errors. |
| Capture | Polish: consolidate repeated photo/recognition explanation; retain transfer notice, lock, error and analysis states. |
| Context | Preserve profile/context snapshot and confirmation details. |
| DrawingGuide | Preserve step instructions and optional/skip affordance. |
| DrawingSubject | Polish: add existing topic artwork/icon cues and shorten duplicate helper copy. |
| Handoff | Preserve pending/failure state details. |
| Home | Existing illustration-led entry and resume cards; preserve. |
| Idea | Optional text/audio and guide controls are distinct; preserve capability and error details. |
| LearningPath | Three separate start choices are clear; preserve. |
| LessonGallery | Preserve lesson content and access labels; no safe copy reduction identified from source alone. |
| LessonHistory | Preserve delivery, feedback and teacher-reply context. |
| LessonPicker | Selection rows already show title, topic and access state; preserve. |
| Notifications | Preserve read/unread and load/error states. |
| ProfileForm | Preserve required fields, consent and validation states. |
| Profile | Preserve profile, consent, sharing, account and family navigation. |
| ProfileSharing | Preserve access scope, invitation and revoke explanations. |
| Quota | Preserve current entitlement and purchase/status messaging. |
| Settings | Compact settings surface; preserve. |
| SketchGuide | Preserve progressive drawing steps and review/skip behavior. |
| StoryHistory | Preserve run status and history actions. |
| Story | Keep full story and scene-by-scene review for the adult confirmation gate. |
| Topic | Polish: keep all API cards/actions; shorten duplicated intro/custom-topic copy. |
| TranscriptReview | Preserve transcript correction/confirmation. |
| Understanding | Preserve recognition uncertainty and adult subject confirmation. |
| VideoCandidate | Preserve experimental/safety notice, pending/reconciliation states and controls. |
| ParentBottomBar | Preserve navigation structure and labels. |

## Source changes and checks

- `TopicScreen`: shorter intro/custom-topic copy; unsupported topics no longer reuse unrelated nature art.
- `DrawingSubjectScreen`: topic artwork/icon in the topic header, subject icons in API-driven cards, and shorter custom-entry/validation copy. The custom-topic path still requires an adult-entered object and validation.
- `ParentExpoApp`: passes selected topic ID as display metadata only.
- `ActivityScreen`: compact topic/subject context, less explanatory duplication, shorter loading/result copy, and no internal lesson-version UUID in visible source text. Activity fields and safety notes remain visible.
- `CaptureScreen`: one concise transfer notice appears before a run starts; duplicate explanation was removed. Photo lock, errors and analysis actions are unchanged.
- Static check: `git diff --check` returned clean for the changed mobile files.
- Static asset check: all six referenced existing topic images are present.
- Icon check: all 27 Ionicons names referenced by `topicVisuals.ts` exist in the installed glyph map.
- Route check: the sole `DrawingSubjectScreen` call site passes `topicId`.

## Limits

No screenshot, device/emulator render, tap test, test suite, typecheck, API call or AI inference was run for this source review. Device layout and visual fidelity remain unverified.
