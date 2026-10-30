# M02 — Generation prompt

Generated 2026-10-30 with the built-in image generation tool.

## Prompt as sent

```text
Use case: ui-mockup
Asset type: School Manager organization dashboard, desktop 16:10.
Input images: Image 1 is the exact Sketch2Life logo; Image 2 is the shared UI style.
Primary request: School Manager workspace for “Trường Mầm non Ánh Dương”, focused on organization members/groups, class slots and school quota.
Use this exact School Manager sidebar on both Manager screens: “Tổng quan”, “Giáo viên & nhóm”, “Lớp & slot”, “Quota”, “Duyệt công khai”, “Cài đặt”.
Key content: title “Quản lý trường”; summary “8/10 lớp đang dùng”; quota card “86 lượt tạo video còn” (clearly illustrative); section “Giáo viên” with 8 members and action “Mời giáo viên”; section “Nhóm phụ huynh” with 4 school groups and action “Quản lý nhóm”; class table with two classes; actions “Thêm lớp” and “Xem quota”.
Style/medium: concise administrative web dashboard, fixed same sidebar, clear information hierarchy.
Constraints: parent groups are not ownership of Parent accounts; no global Parent directory, no cross-school visibility, no invented price or package name, sample quota numbers clearly illustrative, no child media, no purple, no alternate logo, no long privacy/spec banner, no English UI except brand, no watermark.
```

## Final refinement

Reduced table density and aligned Cô Thảo, Ánh Dương school, Lớp Mầm 2 and its parent group across screens; corrected the first class level to “Mẫu giáo” for the five-year-old example.

## Inputs and output

- Brand mark: apps/teacher-ui/src/assets/logo-icon.png.
- Shared style reference: ui-components-rev38-20261030/ui01-foundations-controls/components.png.
- Shared synthetic butterfly drawing is referenced where applicable; see shared/PROMPT.md.
- Output: school-manager/m02-organization-management/screen.png.
