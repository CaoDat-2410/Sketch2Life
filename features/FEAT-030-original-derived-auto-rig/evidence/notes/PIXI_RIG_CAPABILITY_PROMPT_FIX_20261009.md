# Pixi rig-capability prompt and diagnostics fix

Date: 2026-10-09 (Asia/Saigon)

## Runtime evidence and diagnosis

The owner screenshot shows `/v4/pixi/show-plan` returning HTTP 200, followed by the UI message that the current mask does not support the chosen movement. This means request parsing/model response validation succeeded and the downstream capability compiler rejected the selected plan. The existing prompt exposed all render strategies and actions regardless of `rigTier` and validated `partRoles`, so it invited outputs the compiler correctly rejected.

## Change

- Added shared pure helpers in `pixi_show_compiler.py` for source actions by rig tier/part roles, strategies by tier/environment availability, and source actions by selected strategy.
- The Lightning V4 prompt now receives these request-derived allowlists. It asks full rigs to select only articulated actions supported by verified roles, cutouts to use whole-subject actions, bbox-only output to remain static, and topic scenes only when an eligible environment candidate exists.
- The compiler uses the same helper rules and logs fixed reason codes such as `required_part_role_missing`, `articulated_action_requires_full_rig`, and `topic_scene_requires_verified_cutout`. Public workflow error behavior is unchanged; no user, image, prompt, asset, or model-output values are logged.
- No extra inference, retry, planner-output repair, contract change, or fallback was added.

## Verification and limits

- Command: `python -m py_compile backend/src/sketch2life/application/services/pixi_show_compiler.py tools/lightning_vision_v2_server.py` — passed.
- Command: `git diff --check -- backend/src/sketch2life/application/services/pixi_show_compiler.py tools/lightning_vision_v2_server.py features/FEAT-030-original-derived-auto-rig` — passed.
- Tests and live model inference were not run. Runtime acceptance requires deploying the backend compiler and Lightning prompt changes, restarting the relevant services, then retrying with synthetic artwork.
- The screenshot's exact rejected capability branch was not present in the supplied terminal log; the new fixed reason code will identify it if the model still returns an unsupported plan.
