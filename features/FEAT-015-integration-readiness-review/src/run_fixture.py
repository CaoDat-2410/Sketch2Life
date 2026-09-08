"""Offline integration fixture runner."""
from __future__ import annotations

import argparse
import json

from integration_fixture import fixture_path, load_fixture, run_scenario


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="happy_cache_hit")
    args = parser.parse_args()
    fixture = load_fixture(fixture_path())
    print(json.dumps(run_scenario(fixture, args.scenario), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
