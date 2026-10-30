# A01 — Generation prompt

Generated 2026-10-30 with the built-in image generation tool.

## Prompt as sent

```text
Use case: ui-mockup
Asset type: Platform Admin public-catalog moderation screen, desktop 16:10.
Input images: Image 1 is the exact Sketch2Life logo; Image 2 is the shared design style.
Primary request: Let the Platform Admin moderate public lessons using actions that match each lesson's current status.
Use this exact Platform Admin sidebar on both Admin screens: “Tổng quan”, “Tổ chức”, “Thư viện bài học”, “Danh mục hoạt động”, “Quota & chính sách”, “Nhật ký”.
Key content: title “Thư viện bài học”; search and filters “Phạm vi”, “Trạng thái”, “Chủ sở hữu”; concise table with fictional rows; selected row “Vòng đời bướm · Bản 3” status “Đang công khai”, last updated “30/10/2026”; action for selected public row “Ẩn khỏi thư viện” in red; a separate hidden row may show “Mở lại công khai”; a pending-public request must show current scope “Trong trường” and status “Chờ duyệt”.
Style/medium: clear data table and a right-side detail panel, stable role sidebar, no excess text.
Constraints: never show “Mở lại công khai” for an already-public row; separate requested visibility from effective visibility; no child media; no privacy/spec banner; red only hide/destructive action; no purple, no alternate logo, no English UI except brand, no watermark. Fictional content.
```

## Final refinement

No post-generation refinement recorded.

## Inputs and output

- Brand mark: apps/teacher-ui/src/assets/logo-icon.png.
- Shared style reference: ui-components-rev38-20261030/ui01-foundations-controls/components.png.
- Shared synthetic butterfly drawing is referenced where applicable; see shared/PROMPT.md.
- Output: platform-admin/a01-content-moderation/screen.png.
