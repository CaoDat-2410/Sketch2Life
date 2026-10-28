# Evidence index

Add reproducible evidence for every acceptance criterion. Include commands, inputs, outputs, environment, timestamp, and interpretation.

- `MODAL_QWEN_SETUP_20261028.md`: exact Qwen3-VL-8B candidate identity, custom ASGI route/resource configuration, account-side setup instructions, and measured versus unmeasured limits. No remote resource or provider run is claimed.
- `PHASE_A_OWNER_REPORT_20261028.md`: sanitized record of the owner's local CLI setup and snapshot preparation, based on output shared in chat.
- `PHASE_B_OWNER_REPORT_20261028.md`: owner-reported Volume setup, Secret-name listing, serve attempts, health response, authentication checks and first admitted request failing with `MODEL_LOAD_FAILED`; successful inference remains pending.
- `modal-smoke-20261029-v1/`: owner-generated synthetic house-and-sun image, fixture provenance, actual admission receipt, prepared request, probe source and sanitized failed-result metadata/timing report. No raw model output or credential is included.

Configuration was prepared from the repository source and first-party Modal docs. The owner completed local CLI authentication and snapshot preparation, created the named Volume, uploaded the snapshot and reported the expected remote layout, temporary Web Function creation, health response and bounded authentication checks. The first admitted synthetic request failed during model loading; successful inference and GPU memory/cost measurements remain pending.
