#!/usr/bin/env python3
"""Run one configured generation smoke test for the Person 4 POC."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


FEATURE_ROOT = Path(__file__).parents[1]
SRC_ROOT = FEATURE_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from learning_video.provider_factory import create_generation_provider  # noqa: E402
from learning_video.schemas import GenerationBrief  # noqa: E402
from learning_video.settings import load_settings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="YAML profile to load")
    parser.add_argument(
        "--brief",
        type=Path,
        default=FEATURE_ROOT / "fixtures/objectives/butterfly_generation_brief.json",
        help="Generation brief JSON fixture",
    )
    args = parser.parse_args()

    settings = load_settings(args.config)
    brief = GenerationBrief.model_validate(json.loads(args.brief.read_text(encoding="utf-8")))
    provider = create_generation_provider(settings)
    result = provider.generate(brief)

    print(f"provider={settings.wan.provider}")
    print(f"artifact_id={result.artifact_id}")
    print(f"output_path={result.output_path}")
    print(f"model={result.provenance.model_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
