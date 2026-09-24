# FEAT-018 Whiteboard Video Kaggle Validation

Date: 2026-09-24  
Environment: Kaggle Notebook with 2x Tesla T4 GPU  
Fixture: private dataset `cat.png`, 600x600 PNG

## Pipeline exercised

```text
PNG input
  -> Qwen3-VL semantic localization
  -> SAM2 box-prompt segmentation
  -> RGBA cutout
  -> progressive reveal renderer
  -> H.264 MP4 encoding
```

## Observed results

| Check | Result |
|---|---|
| Qwen3-VL model load | PASS |
| Semantic label | `a cheerful cartoon boy waving` on the first fixture; Garfield fixture used for segmentation |
| SAM2 mask shape | `600x600` |
| SAM2 mask type | Boolean mask |
| Cutout artifact | `/kaggle/working/cat_cutout.png` |
| MP4 codec | H.264 |
| Pixel format | `yuv420p` |
| Frame rate | 30 FPS |
| Resolution | `1280x720` |
| Duration | 8.0 seconds |
| File size | 0.18 MiB |

## Scope and limitations

This validates the provider/model and MP4 MVP path on a real GPU. The renderer currently uses a progressive reveal effect; it does not yet reconstruct the original drawing stroke order. The Kaggle notebook is experimental evidence and is not the production backend implementation.

The fixture is retained as a private test artifact and must not be published as a product asset without confirming image rights.
