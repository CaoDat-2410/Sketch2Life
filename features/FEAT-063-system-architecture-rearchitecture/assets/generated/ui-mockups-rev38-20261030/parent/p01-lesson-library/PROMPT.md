# P01 — Generation prompt

Generated 2026-10-30 with the built-in image generation tool.

## Prompt as sent

```text
Use case: ui-mockup
Asset type: Android parent-app screen, portrait 9:19.
Input images: Image 1 is the exact Sketch2Life sprout logo mark. Image 2 is the style reference for the same brand, blue primary, yellow accent, mint support color, rounded cards and typography. Use the same wordmark “Sketch2Life”; ignore text in the style board.
Primary request: Create the Parent lesson library screen for a Vietnamese child-centered learning app. Show one selected fictional child, Minh, age 5, and only a few lesson cards.
Scene/backdrop: clean warm-white mobile app, calm blue and mint surfaces.
Key content: header “Bài học khám phá”; profile switcher “Minh · 5 tuổi”; numeric sample “Còn 2 lượt tạo video”; search field “Tìm bài học”; cards “Vòng đời bướm” and “Cây xanh quanh em”; small continuation card “Bạn có buổi học đang làm dở” with button “Tiếp tục”.
Style/medium: realistic, concise, highly legible product UI; blue primary buttons, yellow only as accent; use the exact logo mark consistently.
Constraints: no family-sharing claim, no long paragraphs, no privacy/spec banners, no English UI copy except “Sketch2Life”, no purple, no alternate logos, no dates, no watermark. The quota count and child are fictional examples.
```

## Final refinement

Made Continue blue and standardized bottom navigation to Bài học / Lịch sử / Hồ sơ.

## Inputs and output

- Brand mark: apps/teacher-ui/src/assets/logo-icon.png.
- Shared style reference: ui-components-rev38-20261030/ui01-foundations-controls/components.png.
- Shared synthetic butterfly drawing is referenced where applicable; see shared/PROMPT.md.
- Output: parent/p01-lesson-library/screen.png.
