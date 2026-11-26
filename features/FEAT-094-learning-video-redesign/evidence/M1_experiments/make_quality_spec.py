"""Write the E1-E3 quality spec. Run with the Modal virtual environment (it imports the deployed video worker)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / "deployment" / "modal" / "srs_v23"))
sys.path.insert(0, str(HERE))

import video_app  # noqa: E402
from prompts import BIKE, CHICK, motion_prompt  # noqa: E402


def main() -> None:
    scenes = []
    for drawing, action, seed in (("bike", BIKE, 940201), ("chick", CHICK, 940202)):
        base = {"image": f"{drawing}_start.png", "seconds": 10.0, "seed": seed}
        new = motion_prompt(action)
        scenes.append({**base, "name": f"{drawing}-e1-old-prompt", "prompt": video_app._ltx_animation_prompt(action)})
        scenes.append({**base, "name": f"{drawing}-e1-new-prompt", "prompt": new})
        for crf in (0, 33):
            scenes.append({**base, "name": f"{drawing}-e3-crf{crf}", "prompt": new, "crf": crf})
    chick = next(scene for scene in scenes if scene["name"] == "chick-e1-new-prompt")
    for strength in (0.7, 0.9):
        scenes.append(
            {**chick, "name": f"chick-e2-end{int(strength * 10)}", "end_image": "chick_end.png", "end_strength": strength}
        )
    profile = {"offload": "none", "resident": True, "prompt_cache": True, "decode_mode": "combined_compile",
               "expandable": True}
    spec = {"profile": profile, "scenes": scenes}
    (HERE / "inputs" / "quality.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    print(len(scenes), "scenes")


if __name__ == "__main__":
    main()
