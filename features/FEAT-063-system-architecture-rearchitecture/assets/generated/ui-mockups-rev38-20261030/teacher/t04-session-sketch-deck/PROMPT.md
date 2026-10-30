# T04 — Generation prompt

Generated 2026-10-30 with the built-in image generation tool.

## Prompt as sent

```text
Use case: ui-mockup
Asset type: Teacher desktop lesson-occurrence preparation screen, 16:10.
Input images: Image 1 is the exact Sketch2Life logo mark; Image 2 is the shared UI design.
Primary request: Prepare the “Vòng đời bướm” occurrence and show the optional Teacher Sketch Deck after the Teacher has enabled it.
Use the exact same Teacher sidebar: “Tổng quan”, “Lớp học”, “Giáo án”, “Buổi học”, “Phản hồi”, “Cài đặt”. Keep the same wordmark, Cô Thảo, Trường Mầm non Ánh Dương, blue primary and 2026 date style.
Key content: occurrence title “Chuẩn bị buổi học”; class “Lớp Mầm 2”; date “30/10/2026”; one clear switch “Bật gợi ý nét vẽ cho buổi này” in the enabled state; deck preview with four simple line-art drawing steps and a small list of two lesson activities; primary action “Trình chiếu bộ gợi ý”; back navigation.
Style/medium: clean desktop web UI, consistent sidebar and single-switch state.
Constraints: Deck is optional; show exactly one enable/disable control, no duplicate “Tắt gợi ý” button. If the switch is off there is no AI job/deck. No child profile/art input to deck generation, no roster display in the deck, no privacy/spec banners, no purple, no alternate logo, no English UI except brand, no watermark.
```

## Final refinement

No post-generation refinement recorded.

## Inputs and output

- Brand mark: apps/teacher-ui/src/assets/logo-icon.png.
- Shared style reference: ui-components-rev38-20261030/ui01-foundations-controls/components.png.
- Shared synthetic butterfly drawing is referenced where applicable; see shared/PROMPT.md.
- Output: teacher/t04-session-sketch-deck/screen.png.
