"""Explicit, synthetic SAM2 load/inference check before paid story media work.

This command may download model weights. It never opens child media or creates
story images, TTS, or MP4 artifacts.
"""

from __future__ import annotations

import argparse
import json

MODEL_ID = "facebook/sam2.1-hiera-small"


def verify_sam2(predictor=None) -> dict[str, object]:
    import numpy as np
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("SAM2 verification requires the L4 CUDA GPU")
    if predictor is None:
        from sam2.sam2_image_predictor import SAM2ImagePredictor

        predictor = SAM2ImagePredictor.from_pretrained(MODEL_ID)

    synthetic = np.full((256, 256, 3), 255, dtype=np.uint8)
    synthetic[48:208, 48:208] = (30, 30, 30)
    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
        predictor.set_image(synthetic)
        masks, scores, _ = predictor.predict(
            box=np.asarray([48, 48, 208, 208], dtype=np.float32),
            multimask_output=True,
        )
    masks = np.asarray(masks)
    scores = np.asarray(scores)
    if (
        masks.ndim != 3
        or masks.shape[1:] != (256, 256)
        or masks.shape[0] < 1
        or scores.shape != (masks.shape[0],)
        or not np.isfinite(scores).all()
    ):
        raise RuntimeError("SAM2 returned invalid synthetic mask output")
    return {
        "ready": True,
        "model": MODEL_ID,
        "gpu": torch.cuda.get_device_name(0),
        "masks": int(masks.shape[0]),
        "note": "Synthetic inference only; scene mask/visual quality is unverified.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-model-download",
        action="store_true",
        help="Acknowledge that loading SAM2 may download weights from Hugging Face",
    )
    args = parser.parse_args()
    if not args.allow_model_download:
        parser.error("pass --allow-model-download only after approving the model download")
    print(json.dumps(verify_sam2(), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
