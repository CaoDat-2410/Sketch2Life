# Local Parent video candidate configuration — 2026-11-22

## Cause

The screenshot's backend error was accurate. In the API container, both local synthetic gates were false. The root CAPSTONE .env did not contain either variable, so Compose applied its false defaults. The backend requires both flags, local/test environment, and Modal dev provider before dispatching a Parent video candidate.

## Change and validation

- Added only these non-secret local settings to <local-machine-path>
  - SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED=true
  - SKETCH2LIFE_PARENT_VIDEO_DEV_CANDIDATE_ENABLED=true
- Preserved SKETCH2LIFE_ENV=local and SKETCH2LIFE_AI_PROVIDER=modal_dev.
- Recreated only the API service in Compose project s2l-feat081-rev23 using its existing worktree compose file and temporary Rev117 override; no dependencies/database were recreated.
- Effective API container values were verified without printing any other environment entries. Container is running; /health returned status ok, service sketch2life-api.
- Modal CPU model-status returned staged for Lightricks/LTX-2.5 revision 49b093a39c19169a8a81721dcc541e07e945232f, 71,114,917,404 bytes. gpu_model_loaded=false and inference_ready=false because no GPU generation was run. Modal active-container inventory was empty after the status check.

## Limits

This enables only the local synthetic technical-preview route. It does not make output product-ready or pass video safety/consistency validation. No video generation request was sent and no GPU inference was started. The existing screen may still show the old disabled error until refreshed.
