# FEAT-020 Evidence Index

Status: `PLANNED`

All evidence for this feature must remain in this directory and must be sanitized.

Planned evidence files:

- `preflight.txt` — runtime/model/CUDA checks with secret values redacted;
- `workflow-run-summary.txt` — safe one-command progress and terminal result;
- `workflow-result.json` — sanitized versioned final manifest;
- `e2e-result.txt` — the single real-AI E2E test result;
- `validation-summary.txt` — security, harness, architecture, skeleton, unit, and E2E checks;
- `provenance-check.txt` — original-image immutability and identity continuity checks.

Do not place raw image/audio files, raw prompts, full model outputs, credentials, tokens, or real child data here. Runtime media and large model artifacts must stay in ignored local/Lightning storage.
