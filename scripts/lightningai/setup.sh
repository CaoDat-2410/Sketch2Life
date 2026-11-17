#!/usr/bin/env bash
set -Eeuo pipefail

# Run on LightningAI only. Uses a separate venv and never modifies Wan's environment.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="${SKETCH2LIFE_LIGHTNING_VENV:-${ROOT_DIR}/.runtime/lightning-venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ "${SKETCH2LIFE_ALLOW_INSTALL:-0}" != "1" ]]; then
  echo "REFUSING_INSTALL: set SKETCH2LIFE_ALLOW_INSTALL=1 on LightningAI after review" >&2
  exit 2
fi
[[ -f "${ROOT_DIR}/backend/pyproject.toml" ]] || { echo "REPOSITORY_ROOT_INVALID" >&2; exit 2; }
if [[ -n "${WAN_REPO_DIR:-}" && "${VENV_DIR}" == "${WAN_REPO_DIR}"* ]]; then
  echo "REFUSING_TO_MODIFY_WAN_ENV: choose a separate venv" >&2
  exit 2
fi

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
python -m pip install -e "${ROOT_DIR}/backend[dev,whiteboard-renderer]"
python -m pip check
python "${ROOT_DIR}/tools/verify_lightning_runtime.py" --mode inventory --json-out "${VENV_DIR}/runtime-inventory.json"
printf 'SETUP_COMPLETE\nvenv=%s\n' "${VENV_DIR}"
