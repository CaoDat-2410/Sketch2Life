# FEAT-024 implementation evidence

Date: 2026-09-15

## Implemented

- Qwen mapping now exposes a closed `VisionMappingDiagnosticV2` category on
  typed schema failure without persisting raw provider output.
- The real CLI enables bounded repair for missing collection arrays,
  deterministic local observation IDs, omitted confidence, and scalar
  Vietnamese text fields. The default adapter/test boundary remains strict.
- A typed ASR failure no longer blocks a successful VLM-only path; the result
  keeps the ASR failure metadata and marks scene grounding as `REAL_VLM_OBSERVATIONS`.
- `ExperienceContinuityV2` now carries planned drawing/video/activity/age/
  objective/safety dimensions separately from actual post-render continuity.
  Actual continuity remains null with `NOT_RENDERED` video status.
- Butterfly 0–3 uses `OBJ_MOVEMENT_COORDINATION` with sensory discrimination
  secondary; butterfly 9–12 is `RELATED_EXPANSION` with
  `TOPIC_NOT_DIRECTLY_OBSERVED`, explicit bridge metadata, and a reduced score.
- Each curated variant can carry age-specific setup, focus cues, handoff and
  off-screen instructions. The V2 experience spec now emits a typed bridge.

## Verification

- `python -m pytest backend/tests/unit/test_qwen_vision_adapter.py backend/tests/unit/test_qwen_vision_schema_path_diagnostic.py backend/tests/unit/test_semantic_personalization_v2.py -q`
  — passed: 119 tests.
- `python tools/validate_harness.py` — `HARNESS_VALID`.
- `python tools/validate_repository_security.py` — `REPOSITORY_SECURITY_VALID`.
- `python tools/validate_architecture.py` — reports a pre-existing dependency
  direction violation in `backend_ai_workflow.py`; this FEAT-024 change did not
  introduce that existing infrastructure import.
- The broader unit run excluding two locally unavailable PyAV modules reached
  100% with two unrelated baseline failures: timing-sensitive fake execution
  evidence and a pre-pinned media-validation digest. The FEAT-024 targeted
  suites pass.

## Remaining release gate

Run the real CLI on Lightning Studio with both approved media pairs and the
pinned Qwen/Whisper local model directories. This evidence must contain only
typed metadata and hashes, never raw model output or prompts.
