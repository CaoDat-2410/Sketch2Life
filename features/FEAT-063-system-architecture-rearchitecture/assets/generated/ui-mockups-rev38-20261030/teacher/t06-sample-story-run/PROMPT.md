# T06 — Generation prompt

Generated 2026-10-30 with the built-in image generation tool.

## Prompt as sent

```text
Use case: ui-mockup
Asset type: Teacher desktop sample story-run review screen, 16:10.
Input images: Image 1 is the exact Sketch2Life logo; Image 2 is the shared UI style; Image 3 is the fictional child's drawing, shown as the source artwork for this sample video.
Primary request: Show the middle of a Teacher sample-video workflow after capture and subject confirmation, before starting video generation.
Use the same Teacher sidebar: “Tổng quan”, “Lớp học”, “Giáo án”, “Buổi học”, “Phản hồi”, “Cài đặt”; same brand, Cô Thảo and Ánh Dương school.
Key content: title “Video mẫu cho buổi học”; lesson “Vòng đời bướm”; class “Lớp Mầm 2”; representative child “Minh · 5 tuổi” with note “Được chọn ngẫu nhiên cho buổi này”; source drawing from Image 3; subject “Con bướm · Đã xác nhận”; switch “Đi theo hướng kịch bản giáo án” enabled; storyboard “5 cảnh” with five short scene titles; text field “Gợi ý viết lại cho AI”; counter “0/3”; blue primary action “Xác nhận kịch bản và tạo video”.
Style/medium: concise desktop review page, same stable role navigation and card styling.
Constraints: this is one-child sample run; no child profile fields go to Sketch Deck generation; no direct scene editing, no public sharing, no reused video, no final video approval. Only adult script confirmation precedes generation. No privacy/spec banner, no purple, no alternate logo, no English UI except brand, no watermark. Fictional sample only.
```

## Final refinement

Changed the purple lesson icon to system blue; preserved 5 scenes and rewrite counter 0/3.

## Inputs and output

- Brand mark: apps/teacher-ui/src/assets/logo-icon.png.
- Shared style reference: ui-components-rev38-20261030/ui01-foundations-controls/components.png.
- Shared synthetic butterfly drawing is referenced where applicable; see shared/PROMPT.md.
- Output: teacher/t06-sample-story-run/screen.png.
