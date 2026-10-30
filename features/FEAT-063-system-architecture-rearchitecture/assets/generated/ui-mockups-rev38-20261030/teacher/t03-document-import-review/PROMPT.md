# T03 — Generation prompt

Generated 2026-10-30 with the built-in image generation tool.

## Prompt as sent

```text
Use case: ui-mockup
Asset type: Teacher desktop filtered document-import review screen, 16:10.
Input images: Image 1 is the exact Sketch2Life logo mark; Image 2 is the shared style.
Primary request: Show the Teacher reviewing deterministic fields extracted from an uploaded lesson before any filtered fields are sent to AI assistance.
Use the exact same Teacher web sidebar on every Teacher screen: “Tổng quan”, “Lớp học”, “Giáo án”, “Buổi học”, “Phản hồi”, “Cài đặt”.
Key content: title “Nhập giáo án”; file “Giao_an_vong_doi_buom.docx · 2,4 MB”; concise support line “PDF, PPTX, DOCX · tối đa 25 MB và 100 trang · không nhận tệp quét hoặc đặt mật khẩu”; stepper “Tải tệp”, “Lọc và trích xuất”, “Giáo viên rà soát”; editable fields “Chủ đề”, “Độ tuổi”, “Mục tiêu”, “Các bước vẽ”, “Hoạt động”, “Vật liệu”, “Lưu ý an toàn”; show a missing-field warning only if that field is visibly empty; actions “Lưu chỉnh sửa” and blue primary “Xác nhận nội dung đã lọc”.
Style/medium: clean web form in compact cards, one sidebar, short labels, no text wall.
Constraints: original file remains private; only reviewed allowlisted fields can go to AI after confirmation. Never show the raw file/full text being sent to AI or automatic lesson completion. No contradictory warning when a field is filled. No purple, no alternate logo, no privacy banner, no English UI except brand/file extension, no watermark. Fictional example.
```

## Final refinement

No post-generation refinement recorded.

## Inputs and output

- Brand mark: apps/teacher-ui/src/assets/logo-icon.png.
- Shared style reference: ui-components-rev38-20261030/ui01-foundations-controls/components.png.
- Shared synthetic butterfly drawing is referenced where applicable; see shared/PROMPT.md.
- Output: teacher/t03-document-import-review/screen.png.
