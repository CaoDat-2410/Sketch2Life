# P04 — Generation prompt

Generated 2026-10-30 with the built-in image generation tool.

## Prompt as sent

```text
Use case: ui-mockup
Asset type: Android Parent capture-and-subject-confirmation screen, portrait 9:19.
Input images: Image 1 is the exact Sketch2Life sprout logo; Image 2 is the shared blue/yellow/mint UI style; Image 3 is the one fictional child drawing and must remain the same drawing.
Primary request: Show the result immediately after the adult has captured the child's butterfly drawing. Clearly distinguish the captured paper photo from the VLM's uncertain subject suggestion.
Key content: title “Xác nhận chủ thể”; captured artwork from Image 3 as the largest element; compact suggestion card “Có thể là con bướm”; one sentence “Hãy kiểm tra trước khi tiếp tục”; blue primary button “Đúng rồi”; secondary outline action “Chỉnh chủ thể”; small link “Chọn ảnh khác”.
Style/medium: clean, realistic Vietnamese mobile product UI; use the same logo, colors and rounded card system.
Constraints: preserve the exact recognizable drawing from Image 3; no invented confidence percentage; no preselected-subject step before capture; no duplicate thumbnails, no decorative privacy banner, no long text, no purple, no alternate logo, no English UI except “Sketch2Life”, no watermark. Fictional sample only.
```

## Final refinement

No post-generation refinement recorded.

## Inputs and output

- Brand mark: apps/teacher-ui/src/assets/logo-icon.png.
- Shared style reference: ui-components-rev38-20261030/ui01-foundations-controls/components.png.
- Shared synthetic butterfly drawing is referenced where applicable; see shared/PROMPT.md.
- Output: parent/p04-capture-subject-confirmation/screen.png.
