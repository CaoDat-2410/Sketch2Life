# SAM 2.1 synthetic benchmark runability and limits — 2026-09-30

- Evidence: `E-030-SAM-QUALITY-012`
- Plan: approved integrated FEAT-018/020/030 increment; SAM mask-quality workstream.
- Scope exercised: dependency-free synthetic fixture sharing, bounded candidate selector, pixel metrics,
  and one grounded thin-detail prompt-anchor case.
- No child artwork/profile, SAM/Qwen model, checkpoint, GPU, Lightning endpoint, or external request
  was used.

## Issue and implementation

The benchmark previously used `runpy` on `tests/unit/test_sam21_quality_metrics.py` to obtain its
archetype masks. That coupled a standalone benchmark to pytest. The repository backend virtualenv
has pytest but not the optional NumPy runtime, while the available workspace Python has NumPy/Pillow
but no pytest. The archetype silhouettes and thin-detail masks now live in
`backend/src/sketch2life/benchmark/sam21_synthetic_masks.py`, a pure shared module imported by both
the tests and benchmark. Unsupported archetype names fail explicitly.

A separate selector case supplies a positive point on a thin feature and a negative point on a
synthetic wrong-object island. The intentionally high-score wrong-object mask and the mask missing
the grounded thin feature are rejected; the lower-score complete mask is selected. This proves
only that the existing prompt constraints can enforce explicitly grounded points when a candidate
contains them. It does not prove that an upstream prompt generator identifies every real thin feature.

## Reproduction and results

From repository root, run `backend/tools/benchmark_sam21_synthetic.py` with `backend/src` on
`PYTHONPATH` and a Python environment containing NumPy. The run used the Codex workspace Python
runtime and completed successfully without pytest:

- Nine analytic silhouettes: butterfly, bird, flower, tree branch, fish, biped, rigid,
  generic-organic, and unknown.
- Constructed distractor baseline vs prompt-validated candidate: IoU **0.9315 → 0.9937**;
  Dice **0.9642 → 0.9968**; boundary F1 **0.9234 → 0.9873**; false inclusion **0.0685 → 0**.
- Trade-off: thin-detail recall **1.0000 → 0.6394** and false exclusion **0 → 0.0063** in the
  constructed set. The explicit grounded-point case passed and retained both thin pixels while
  excluding the wrong-object point.
- Selector CPU wall time: **3.047 ms total** over nine synthetic cases. SAM inference latency and
  peak L4 VRAM are unmeasured (`null`).

The input candidates are deliberately fabricated masks; the figures measure metric/selector
plumbing and prompt-constraint behavior, not SAM model accuracy. The fixtures are binary analytical
shapes, not reviewed crayon drawings with pigment, paper texture, shadows, touching objects, or
human-authored anatomical ground truth. No held-out acceptance threshold or reviewer agreement is
claimed. In particular, the 0.639 thin-detail recall is a warning against treating prompt
consistency or a successful SAM response as proof of a precise rig.

## Verification and remaining gates

- Full backend suite after the fixture refactor: **1,650 passed, 10 skipped, 26 warnings** in
  150.96 seconds using a repository-local isolated basetemp. The default Windows pytest temp path
  is not writable in this session; that separate setup failure did not reach test assertions.
- Focused mask metric/runtime tests: **11 passed, 4 skipped**. The optional NumPy-dependent runtime
  tests are skipped in the repository virtualenv; the independent synthetic benchmark ran thematically
  equivalent selector cases in the workspace Python runtime.
- Ruff for the shared fixture, runtime tests, metric tests, and benchmark: passed. Targeted mypy
  with imported dependencies skipped: passed for the audit, benchmark, supervised flow, resolver,
  and synthetic-fixture modules.
- Local backend `/health`: HTTP 200. Expo `/status`: HTTP 200. Android bundle
  `/apps/ui-mobile/index.bundle?platform=android&dev=true&hot=false&minify=false`: HTTP 200,
  8,088,466 bytes. `emulator-5554` is connected with `com.sketch2life.mobile/.MainActivity`
  foreground and ADB reverse `8081 -> 8081`.
- No new SAM/model runtime activation or visual SAM playback was performed.

Still open: reviewed real/synthetic-drawing held-out references, calibrated acceptance thresholds,
full per-class failure analysis, actual L4 Qwen-resident latency/VRAM, and a fresh Android visual
acceptance flow. Keep live SAM activation behind its approved model ADR and benchmark gate.
