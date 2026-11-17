# FEAT-021 Evidence

Evidence for this feature is stored in this directory and must identify the commit SHA, command, test result, and relevant input/model revision without storing secrets or raw child media.

## Current validation

- Targeted semantic/catalog tests: recorded after final validation.
- Full backend regression: recorded after final validation.
- Ruff and strict mypy: recorded after final validation.
- Harness/security validation: required before commit.
- Lightning real-AI acceptance: must be executed in the configured Lightning Studio environment.
