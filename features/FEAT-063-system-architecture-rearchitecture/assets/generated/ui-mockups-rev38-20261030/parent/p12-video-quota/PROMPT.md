# P12 — Generation prompt

Generated 2026-10-30 with the built-in image generation tool.

## Prompt as sent

```text
Use case: ui-mockup
Asset type: Android Parent video-quota and top-up options screen, portrait 9:19.
Input images: Image 1 is the exact Sketch2Life logo mark; Image 2 is the shared visual style.
Primary request: Make video quota concrete with server-provided numeric counts and a clear path to view optional top-ups, without inventing prices or package entitlements.
Key content: title “Lượt tạo video”; summary “Còn 2 lượt trong kỳ”; secondary line “Đã dùng 4 lượt”; section “Mua thêm lượt” with two neutral cards “Gói bổ sung” and “Gói theo tháng” with no price or count; payment choices “MoMo” and “VNPAY”; blue primary action “Xem lựa chọn”; info note “Video đã tạo vẫn xem được”.
Style/medium: same brand/logo/colors, simple scannable mobile dashboard.
Constraints: numeric counts are explicitly illustrative; no fixed package prices, no success claim, no payment logos other than text names, no red purchase button, no English UI except “Sketch2Life”, no purple, no specification banner, no watermark.
```

## Final refinement

Standardized bottom navigation to Bài học / Lịch sử / Hồ sơ.

## Inputs and output

- Brand mark: apps/teacher-ui/src/assets/logo-icon.png.
- Shared style reference: ui-components-rev38-20261030/ui01-foundations-controls/components.png.
- Shared synthetic butterfly drawing is referenced where applicable; see shared/PROMPT.md.
- Output: parent/p12-video-quota/screen.png.
