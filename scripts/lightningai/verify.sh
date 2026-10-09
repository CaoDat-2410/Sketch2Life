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
command -v nvidia-smi >/dev/null || { echo "GPU_TOOL_MISSING" >&2; exit 2; }
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
python "${ROOT_DIR}/tools/verify_lightning_runtime.py" --mode inventory --require-cuda
python - <<'PY'
from sketch2life.infrastructure.config.settings import Settings
settings = Settings()
assert settings.story_render_v2_enabled is False, "V2 must remain OFF by default"
assert settings.whiteboard_video_enabled is False, "video runtime must remain OFF"
print("FLAGS_VALID: V1 default, V2 and video runtime OFF")
PY
printf 'LIGHTNINGAI_ENVIRONMENT_READY\n'
