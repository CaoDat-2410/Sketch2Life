# P09 — Generation prompt

Generated 2026-10-30 with the built-in image generation tool.

## Prompt as sent

```text
Use case: ui-mockup
Asset type: Android Parent lesson-history and feedback screen, portrait 9:19.
Input images: Image 1 is the exact Sketch2Life logo mark; Image 2 is the shared UI design; Image 3 is the same fictional butterfly artwork used as a small lesson thumbnail.
Primary request: Show recent lesson history and one feedback thread attached to the delivered lesson, not a general chat screen.
Key content: title “Bài học đã dùng”; filter “Gần đây”; one history card “Vòng đời bướm” with sample date “30/10/2026” and child “Minh”; section heading “Phản hồi về bài học”; one short Parent message and one short Teacher reply; text-only composer “Viết phản hồi”; blue action “Gửi phản hồi”; small overflow menu on the history card for deletion.
Style/medium: concise Vietnamese mobile interface, same logo/colors, clear relation between feedback and one lesson delivery.
Constraints: no general chat inbox, no family sharing, no completion checkbox, no drawing/photo attachment, no generic “trao đổi” wording, no long paragraphs, no English UI except “Sketch2Life”, no purple, no alternate logo, no watermark. Fictional sample only.
```

## Final refinement

Scoped all feedback to the selected lesson and removed general-chat implication.

## Inputs and output

- Brand mark: apps/teacher-ui/src/assets/logo-icon.png.
- Shared style reference: ui-components-rev38-20261030/ui01-foundations-controls/components.png.
- Shared synthetic butterfly drawing is referenced where applicable; see shared/PROMPT.md.
- Output: parent/p09-history-feedback/screen.png.
