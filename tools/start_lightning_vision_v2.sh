#!/usr/bin/env bash
set -Eeuo pipefail

: "${STUDIO_ROOT:=/teamspace/studios/this_studio}"
: "${PROJECT_ROOT:=$STUDIO_ROOT/Sketch2Life}"
: "${MODEL_DIR:=$STUDIO_ROOT/models/qwen3-vl-8b-instruct}"
: "${ASR_MODEL_DIR:=$STUDIO_ROOT/models/faster-whisper-large-v3-turbo}"
: "${SAM2_ROOT:=$STUDIO_ROOT/vendor/sam2}"
: "${SAM2_MODEL_DIR:=$SAM2_ROOT}"
: "${LIGHTNING_DEV_AUTH:?Set LIGHTNING_DEV_AUTH through Lightning managed secrets before starting the server.}"

if [[ ! -d "$PROJECT_ROOT" ]]; then
    printf 'Project directory does not exist: %s\n' "$PROJECT_ROOT" >&2
    exit 1
fi

export SKETCH2LIFE_VISION_MODEL_DIR="$MODEL_DIR"
export SKETCH2LIFE_VLM_ROOT="$MODEL_DIR"
export SKETCH2LIFE_VISION_MODEL_CACHE_DIR=""
export SKETCH2LIFE_VISION_DEVICE="cuda"
export SKETCH2LIFE_VISION_DEVICE_INDEX="0"
export SKETCH2LIFE_VISION_ALLOW_MODEL_DOWNLOAD="false"

export SKETCH2LIFE_SAM21_MODEL_DIR="$SAM2_MODEL_DIR"
export SKETCH2LIFE_SAM21_CHECKPOINT="$SAM2_ROOT/checkpoints/sam2.1_hiera_small.pt"
export SKETCH2LIFE_SAM21_MODEL_CONFIG="$SAM2_ROOT/sam2/configs/sam2.1/sam2.1_hiera_s.yaml"
export SKETCH2LIFE_SAM21_DEVICE="cuda"

export SKETCH2LIFE_ASR_MODEL_ROOT="$ASR_MODEL_DIR"
export SKETCH2LIFE_ASR_MODEL_SIZE="large-v3-turbo"
export SKETCH2LIFE_ASR_DEVICE="cuda"
export SKETCH2LIFE_ASR_COMPUTE_TYPE="float16"
export SKETCH2LIFE_ASR_BEAM_SIZE="5"
export SKETCH2LIFE_ASR_MODEL_REVISION="lightning-runtime"

export PYTHONPATH="$PROJECT_ROOT/backend/src:$SAM2_ROOT${PYTHONPATH:+:$PYTHONPATH}"

cd "$PROJECT_ROOT"
printf 'Starting Lightning Vision V2 on 0.0.0.0:%s\n' "${PORT:-8000}"
exec python -m uvicorn tools.lightning_vision_v2_server:app \
    --app-dir "$PROJECT_ROOT" \
    --host 0.0.0.0 \
    --port "${PORT:-8000}"
