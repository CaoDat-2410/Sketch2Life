# P03 — Generation prompt

Generated 2026-10-30 with the built-in image generation tool.

## Prompt as sent

```text
Use case: ui-mockup
Asset type: Android Parent drawing-session screen, portrait 9:19.
Input images: Image 1 is the exact Sketch2Life logo mark; Image 2 is the shared style reference; Image 3 is the fictional child butterfly drawing reference. Reuse Image 3's same butterfly silhouette and crayon colors, but depict it as a paper drawing in progress, not as a captured photo.
Primary request: Show a child drawing “Con bướm” on paper while the adult has explicitly enabled the optional generic line-sketch guide.
Scene/backdrop: calm warm-white mobile screen, paper drawing area and a separate compact guide panel.
Key content: title “Bé đang vẽ”; small selected topic “Con bướm”; the paper artwork; optional state “Gợi ý vẽ đang bật”; exactly one control “Tắt gợi ý”; three numbered simple line-sketch steps; blue primary bottom button “Chụp tranh”; secondary gallery icon “Chọn ảnh”.
Style/medium: realistic product UI, same brand/colors/type; guidance is a small optional aid and never covers or replaces the child's drawing.
Constraints: no camera frame, no captured-photo preview, no child/profile data in the guide, no duplicate enable/disable controls, no long copy, no English UI except “Sketch2Life”, no privacy/spec banner, no watermark.
```

## Final refinement

Changed the optional guide-off control from destructive red to neutral blue.

## Inputs and output

- Brand mark: apps/teacher-ui/src/assets/logo-icon.png.
- Shared style reference: ui-components-rev38-20261030/ui01-foundations-controls/components.png.
- Shared synthetic butterfly drawing is referenced where applicable; see shared/PROMPT.md.
- Output: parent/p03-drawing-line-guide/screen.png.
