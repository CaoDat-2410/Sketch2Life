# P08 — Generation prompt

Generated 2026-10-30 with the built-in image generation tool.

## Prompt as sent

```text
Use case: ui-mockup
Asset type: Android Parent private-video-ready screen, portrait 9:19.
Input images: Image 1 is the exact Sketch2Life logo mark; Image 2 is the shared UI design; Image 3 is the same fictional butterfly artwork, shown within the generated video's opening frame.
Primary request: Show a finished private child-specific video first, followed below by two outdoor activities from the selected lesson.
Key content: video player titled “Chuyến bay của bướm”; visible captions control “CC” enabled; section “Hoạt động ngoài trời”; two concise activity cards “Quan sát vòng đời bướm” and “Ghi lại điều con thấy”, each with one material line and short first step; sticky blue primary action “Hoàn tất”; secondary action “Tạo lại video”.
Style/medium: simple polished Vietnamese mobile product UI, same wordmark/colors, not crowded.
Constraints: the butterfly in the video must visibly derive from Image 3 and keep its childlike crayon colors; do not show a different child's art; outdoor activities occur after the video; no video approval gate, no child video download/export, no long copy, no English UI except brand and “CC”, no purple, no privacy/spec banners, no watermark.
```

## Final refinement

Used the shared child butterfly art as paper inside the video player; removed generated facial details.

## Inputs and output

- Brand mark: apps/teacher-ui/src/assets/logo-icon.png.
- Shared style reference: ui-components-rev38-20261030/ui01-foundations-controls/components.png.
- Shared synthetic butterfly drawing is referenced where applicable; see shared/PROMPT.md.
- Output: parent/p08-video-and-activities/screen.png.
