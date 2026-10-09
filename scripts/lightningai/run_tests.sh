#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="${SKETCH2LIFE_LIGHTNING_VENV:-${ROOT_DIR}/.runtime/lightning-venv}"
if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  echo "REQUIRES_LIGHTNINGAI_SETUP: run setup.sh first" >&2
  exit 2
fi
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
cd "${ROOT_DIR}"
python -m pytest backend/tests/unit/test_story_world_v2.py \
  backend/tests/unit/test_story_world_v2_multidrawing.py \
  backend/tests/unit/test_lightning_runtime_setup.py \
  backend/tests/contract/test_whiteboard_video_app_wiring.py
python -m ruff check backend/src/sketch2life tools/verify_lightning_runtime.py
python -m mypy --follow-imports=silent backend/src/sketch2life
python tools/validate_repository_security.py
printf 'LIGHTNINGAI_TEST_PASS\n'
