# FEAT-018 P1 Online Model Compatibility Test Plan

- Status: IMPLEMENTED — approved and validated 2026-09-11
- Parent scope: `P1_CATALOG_GATE_INTEGRITY_POLISH_PLAN.md`
- Scope: provider-shaped ASR/VLM contract fixtures, adapter boundary tests and model-output-to-P1 handoff tests
- Out of scope: live provider calls, model downloads, credentials, production API/cloud, Android/mobile, contract version changes and real child data

## Objective

Prove that P1 remains usable when model output arrives from the approved online profiles through the existing provider-neutral adapters. Tests use realistic structured payloads and injected fake clients/transports so they exercise the same schema and failure boundary without network or model execution.

## Compatibility cases

1. Qwen3-VL structured entity/action/relation/theme/ambiguity output maps to `VisionUnderstandingResultV1` with `provider=lightning` provenance and unchanged source identity.
2. Whisper large-v3-turbo shaped transcript, segments and quality output maps to `AsrResultV1` with unchanged source identity.
3. A model-shaped VLM entity can be converted only after adult confirmation into `SemanticAnchorSetV1`, then compile the existing butterfly fold-and-print P1 spec and Gate B handoff.
4. JSON round-trip keeps contract names, versions, provenance, source hashes and all identity fields stable.
5. Unknown fields, free text, prohibited nested claims, invalid ranges, non-object payloads and malformed segment intervals fail closed with typed errors.
6. Timeout/transient failures follow bounded retry semantics; permanent failures do not leak provider payloads.
7. Model output with low confidence or no usable entity cannot bypass adult confirmation or produce a P1 spec.
8. A model output with a different source hash cannot be attached to the current session/artifact.

## Acceptance criteria

- The approved Qwen3-VL-8B-Instruct and Whisper large-v3-turbo profile identifiers are accepted only as provenance metadata; P1 behavior remains provider-neutral.
- Valid online-shaped output reaches typed contracts and the existing P1 compiler without a source, contract or identity rewrite.
- Invalid or unsafe output yields typed failure or Gate A/P1 blocking and never creates an ExperienceSpec.
- No network, model weights, provider token, raw media or real child data is required by the test suite.
- Existing P1/P2/P3/P4 offline tests remain green and no downstream source changes are needed.

## Validation

- Run the new compatibility suite and existing P1 suite.
- Run the full offline backend/root/FEAT-018 suites, TypeScript checks/tests, Ruff, mypy and repository validators.
- Record counts and the explicit no-live-provider boundary in feature-local evidence.