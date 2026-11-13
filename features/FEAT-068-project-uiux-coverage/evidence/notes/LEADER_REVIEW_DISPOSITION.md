# Leader review disposition — UI/UX review round 2

- Captured: 2026-11-13, Asia/Saigon.
- Source: owner-provided `Bien_Ban_Review_UI_UX_Sketch2Life_Lan_2.docx`, stored locally outside the repository. The original and any rendered extracts are not copied into Git.
- Use: product/usability feedback for this feature. Current product behavior remains governed by the unsigned FEAT-063 SRS v2.5-draft and the mounted source/API implementation.

| Review feedback | Implementation disposition |
|---|---|
| Parent home needs a compact hierarchy with an obvious create-story action, accessible child/profile context, and bottom navigation. | Applied: concise home content, prominent story entry, child context, and centered four-item bottom navigation. |
| Separate public lessons from school/teacher shared lessons; make lesson details easier to review. | Applied: distinct public/shared library tabs and a centered lesson preview sheet. |
| Make a drawing guide optional, remove the sample-image shortcut, and place the lesson direction choice after the drawing is reviewed. | Applied: optional static guide, no fabricated default capture, and lesson direction in the post-capture context review. The guide is explicitly static; no AI sketch-generation API is claimed. |
| Keep audio instructions short and confirm any transcript before use. | Applied: the transcript is part of the idea/review step and remains required only when audio is present. |
| Avoid optional context-field opt-outs and unsupported child attributes. | Applied: adult confirms the minimal context snapshot; no persisted gender field or unsupported context-omission selector was added. |
| Put lesson activities after the story video. | Applied per SRS §5.1 and FR-PL-16: activities remain after the video is available. |
| Improve Teacher contrast; remove the notifications card; center lesson details; support a clear lesson session with lesson materials and activity. | Applied: stronger contrast, a focused two-panel dashboard, centered detail modal, and a Teacher session workspace with lesson/activity selection and preview-only sketch/photo/occurrence states. |
| Improve School Manager and Platform Admin where the review has little role-specific feedback. | Existing role-specific workspaces are retained and included in the shared web visual treatment/build; this feature does not invent new server operations. |

## Explicit constraints carried forward

- Where the review mockups imply a pre-video activity choice, the current SRS takes precedence: activities are offered after the video is playable.
- Parent and Teacher interactions without a mounted authenticated API are clearly local preview or unavailable states. No fake AI generation, upload, persistence, playback, or progress success is claimed.
- The supplied Rev38 folders remain reference-only. The generated mockup images are not runtime assets.
- Parent remains the bundled Android WebView host in `apps/mobile`; Teacher, School Manager, and Platform Admin remain web workspaces. The old Expo workspace is not the Parent target and is left untouched.
