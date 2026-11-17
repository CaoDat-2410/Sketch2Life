# SAM 2.1 synthetic mask visual review

**Date:** 2026-11-06 (Asia/Saigon)

**Input:** `../assets/parent_generated_image_activity_retest_20261103/synthetic_childlike_butterfly.png`

**Output:** `sam2_synthetic_butterfly_mask.png`

The input contains a colored butterfly drawing with a head, antennae, long central body, and four large wings. The generated 1254×1254 binary mask contains one narrow vertical region over the central body. It does not include the wings, head, or antennae.

The measured mask area is 3.34% of the image and the model score is 0.7023. Those values do not override visual inspection: this output is only a partial subject mask and is not acceptable as a complete butterfly segmentation result.

**Disposition:** worker/model feasibility PASS; whole-subject mask quality PARTIAL/FAIL. Preserve the original drawing and keep SAM 2.1 disabled in the product workload registry. Any follow-up using point/box or multi-point prompts requires its own approved quality evaluation; no second inference was run under Plan Rev53.
