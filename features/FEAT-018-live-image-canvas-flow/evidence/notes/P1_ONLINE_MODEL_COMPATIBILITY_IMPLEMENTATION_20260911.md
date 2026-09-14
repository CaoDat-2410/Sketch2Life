# P1 online-model compatibility test implementation

- Evidence ID: `EV-018-P1-ONLINE-MODEL-COMPATIBILITY-20260911`
- Date: 2026-09-11
- Scope: approved provider-shaped compatibility tests at the P1 boundary
- Plan: `plan/P1_ONLINE_MODEL_COMPATIBILITY_TEST_PLAN.md`
- Approval: `approvals/TASK_APPROVAL.md`, P1 online-model compatibility test addendum

## Outcome

The online-model path remains compatible with the existing P1 compiler when model output arrives through the provider-neutral adapters. Tests use the approved profile identifiers only as provenance metadata and inject model-shaped payloads; no live network or model execution is part of this evidence.

## Coverage

- Qwen3-VL structured entity, action, relation, theme and ambiguity payload maps to `VisionUnderstandingResultV1` and round-trips without changing source identity.
- Whisper large-v3-turbo shaped transcript, segment and quality output maps to `AsrResultV1` and round-trips without changing source identity.
- A valid Qwen entity becomes an adult-confirmed `SemanticAnchorSetV1`, then compiles the existing butterfly fold-and-print `ExperienceSpecV1` and Gate B handoff.
- Missing adult confirmation, empty entity sets, unrelated entities, malformed ranges, unknown fields, prohibited nested claims, source override attempts and invalid payload shapes fail closed.
- Timeout and transient/permanent provider failures use typed errors and bounded retry behavior; provider details do not leak into public failures.

## Validation

- New compatibility suite: 22 passed.
- Combined P1 and compatibility suites: 81 passed.
- Full backend offline suite: 989 collected, 984 passed, 5 expected readiness/provider skips, no failures.
- Root offline suite: 33 passed. FEAT-018 replay: 1 passed.
- Ruff passed for the new suite. Downstream TypeScript typecheck and tests passed; no TypeScript source changed in this slice.
- Repository security validation: `REPOSITORY_SECURITY_VALID`; 927 publishable files scanned; no absolute machine paths, credentials or provider secrets.
- Harness validator was run and reports an unrelated untracked `features/FEAT-019-current-system-documentation` scaffold missing its evidence subdirectories. That scaffold is outside this approved change and is preserved untouched.

No P1 production source, P2/P3/P4 source, shared/mobile source, contract version, provider credential, raw media or real child data was added or changed. Live provider execution remains separately gated.