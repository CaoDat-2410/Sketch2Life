# FEAT-014 decisions

- Keep the console activity-explicit: the caller supplies one `ACT-xxxx` ID and the tool evaluates only that record.
- Reuse one shared deterministic eligibility function between the Golden validator and console; do not maintain two rule implementations.
- Support scriptable arguments/scenario files for reproducibility and guided prompts for manual review.
- Use stable exit codes: `0` valid/list/help, `2` valid input but blocked/no-valid, `1` malformed input or harness failure.
- Evidence recording is opt-in through a validated run ID and may write only sanitized JSON under this feature's `evidence/runs/` directory.
- Refuse evidence overwrite and path-like run IDs.
- Do not accept free-form child information, names, narration, media, diagnoses, scores, or provider payloads.
- Keep all records non-production regardless of an eligibility result.
