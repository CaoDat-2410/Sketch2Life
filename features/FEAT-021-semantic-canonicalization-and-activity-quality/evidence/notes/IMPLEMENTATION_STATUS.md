# FEAT-021 implementation status

Date: 2026-09-14

## Implemented

- Canonical semantic V2 fields for child-interest precedence, concept roles, and activity identity.
- ASR-first child-interest resolution with explicit ASR/VLM agreement and conflict states.
- Activity family, variant, catalog revision, and canonical template version parity checks.
- Fail-closed age-band handling with explicit `UNAVAILABLE_AGE_BAND` output when no safe catalog activity exists.
- Age-specific Vietnamese learning-objective payloads and non-deterministic tie-breaking that avoids immediate activity repetition.
- Activity coverage reporting across concept and age-band pairs without synthesizing unapproved activities.
- V1-to-V2 bridge hardening so legacy activity identity drift cannot silently pass through the workflow.

## Validation

- Targeted semantic/activity tests: 15 passed.
- Full backend test suite: passed (exit code 0).
- Ruff: passed.
- Strict mypy on changed modules: passed.
- Harness validation: passed.
- Repository security validation: passed.

## Known remaining content gap

The catalog source still contains 100 curated activity profiles. The coverage report currently measures 48 unmapped profiles, 33 concept/age gaps, and a coverage ratio of approximately 0.2326 across 43 mapped concept-age pairs. The approved target is 200-250 curated activities with at least three safe candidates for common concept-age pairs. This requires authored catalog content and is intentionally not filled by AI-generated runtime activities.

## Runtime note

The Lightning AI real-model end-to-end run remains an environment validation step. It requires the locally downloaded Qwen vision and faster-whisper model directories and the dependency versions documented in the project instructions.
