# Integrated SAM mask and pigment cutout quality — offline evidence

- Date: 2026-09-29
- Workstream: approved FEAT-018/020/030 integrated plan.
- Inputs: generated binary masks only; no child artwork or provider/model response.
- No SAM model, GPU, checkpoint or Lightning endpoint was invoked.

## Runtime and renderer changes

- SAM2.1 requests bounded multimask candidates. The selector rejects candidates violating area,
  positive/negative point, bounding-box overlap or out-of-box consistency checks, then chooses by
  SAM score with a small box-fit tie-break. Rejected prompts do not invalidate an already accepted
  subject mask.
- Added pure mask metrics for IoU, Dice, tolerant boundary F1, thin-detail recall, false inclusion/
  exclusion and part-parent consistency.
- Pigment cutout reconstruction samples only credible low-chroma, bright local paper. It does not
  use saturated crayon strokes as seed colors, fails with a typed error when safe donors are absent,
  preserves source bytes and leaves every pixel outside the verified mask unchanged.

## Synthetic candidate-selection benchmark

Command: `backend\\.venv\\Scripts\\python.exe backend/tools/benchmark_sam21_synthetic.py`
from repository root with `PYTHONPATH=backend/src;.`.

Nine generated archetypes: butterfly, bird, flower, tree branch, fish, biped, rigid, generic organic
and unknown. In this constructed fixture, prompt-consistency selection versus its intentionally
distracting high-score candidate produced:

| Metric | Baseline | Prompt-validated candidate |
|---|---:|---:|
| IoU | 0.9315 | 0.9937 |
| Dice | 0.9642 | 0.9968 |
| Boundary F1 | 0.9234 | 0.9873 |
| False inclusion | 0.0685 | 0.0000 |
| False exclusion | 0.0000 | 0.0063 |
| Thin-detail recall | 1.0000 | 0.6394 |

Nine of nine synthetic selections passed prompt constraints; selector CPU wall time for this run was
3.25 ms total. SAM latency and peak L4 VRAM are **not measured** (`null`). This is a selector/metrics
plumbing exercise, not an estimate of SAM segmentation accuracy. The thin-detail recall drop is a
material trade-off: prompt consistency alone cannot qualify masks for production or guarantee
anatomical completeness.

## Verification and pending gates

- Python full backend suite passed from repository root; focused runtime/metric/profile/P1/contract/
  versioned-metadata regression suite and changed-backend Ruff checks passed.
- Renderer full suite: 45 passed; TypeScript check and demo build passed.
- Android visual playback unavailable because `adb` is not on PATH.
- Still required: reviewed/held-out reference masks, real drawing mask-to-anatomy scoring, L4 latency
  and memory measurements, WebGL/Android playback, and a reviewer-approved acceptance threshold.
- No commit/push or live SAM/Qwen/Lightning request was performed.
