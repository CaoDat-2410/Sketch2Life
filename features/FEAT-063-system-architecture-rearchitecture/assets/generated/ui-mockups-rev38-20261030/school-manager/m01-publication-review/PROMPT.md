# M01 — Generation prompt

Generated 2026-10-30 with the built-in image generation tool.

## Prompt as sent

```text
Use case: ui-mockup
Asset type: School Manager desktop Public lesson review screen, 16:10.
Input images: Image 1 is the exact Sketch2Life logo mark; Image 2 is the shared web UI style.
Primary request: Review one Teacher's request to publish a particular lesson version. Make the current school visibility and requested Public visibility clearly distinct.
Use this exact School Manager sidebar on both Manager screens: “Tổng quan”, “Giáo viên & nhóm”, “Lớp & slot”, “Quota”, “Duyệt công khai”, “Cài đặt”.
Key content: title “Duyệt công khai”; queue “Chờ duyệt”; lesson “Vòng đời bướm · Bản 3”; teacher “Cô Thảo”; school “Trường Mầm non Ánh Dương”; two tabs “Nội dung” and “So sánh phiên bản”; current scope “Trong trường”, requested scope “Công khai”; four unchecked checklist items; feedback field; enabled “Yêu cầu chỉnh sửa”; disabled grey “Duyệt công khai” until all required checklist items pass.
Style/medium: clean Manager web queue and review detail, readable, consistent sidebar and button colors.
Constraints: do not show Parent accounts as owned by the organization; Manager sees school-scoped lesson only. Approval must be disabled while checklist is incomplete. Red only for destructive/error; no privacy/spec banner, no child media, no purple, no alternate logo, no English UI except brand, no watermark. Fictional content.
```

## Final refinement

No post-generation refinement recorded.

## Inputs and output

- Brand mark: apps/teacher-ui/src/assets/logo-icon.png.
- Shared style reference: ui-components-rev38-20261030/ui01-foundations-controls/components.png.
- Shared synthetic butterfly drawing is referenced where applicable; see shared/PROMPT.md.
- Output: school-manager/m01-publication-review/screen.png.
