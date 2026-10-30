# T07 — Generation prompt

Generated 2026-10-30 with the built-in image generation tool.

## Prompt as sent

```text
Use case: ui-mockup
Asset type: Teacher desktop video preview and class-presentation confirmation screen, 16:10.
Input images: Image 1 is the exact Sketch2Life logo; Image 2 is the shared UI style; Image 3 is the same child artwork, visibly transformed into the sample video's opening frame.
Primary request: A ready Teacher sample video preview with a separate explicit action to present it to the current class occurrence.
Use the same Teacher sidebar: “Tổng quan”, “Lớp học”, “Giáo án”, “Buổi học”, “Phản hồi”, “Cài đặt”; same brand, Cô Thảo and Ánh Dương school.
Key content: title “Video mẫu sẵn sàng”; lesson “Vòng đời bướm”; class “Lớp Mầm 2”; label “Video riêng tư”; large player using the same crayon butterfly from Image 3; captions toggle “Phụ đề”; blue primary action “Xác nhận trình chiếu cho lớp”; secondary action “Quay lại buổi học”.
Style/medium: clear desktop video-preview UI with familiar sidebar and no crowded metadata.
Constraints: presentation confirmation is an occurrence action, not a final video approval; no button labeled “Duyệt video”; no download/export or public link; do not alter child artwork identity; no purple, no alternate logo, no privacy/spec banner, no English UI except brand, no watermark. Fictional sample only.
```

## Final refinement

Set the sample runtime to 1:00 and kept occurrence presentation confirmation.

## Inputs and output

- Brand mark: apps/teacher-ui/src/assets/logo-icon.png.
- Shared style reference: ui-components-rev38-20261030/ui01-foundations-controls/components.png.
- Shared synthetic butterfly drawing is referenced where applicable; see shared/PROMPT.md.
- Output: teacher/t07-video-presentation-confirmation/screen.png.
