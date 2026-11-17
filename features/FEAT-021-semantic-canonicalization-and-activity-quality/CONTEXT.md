# FEAT-021 Context

## Scope

This feature hardens the backend semantic workflow after FEAT-020. It makes V2 canonical, gives child narration priority when ASR confidence is sufficient, enforces activity identity/version consistency, blocks runtime-created activities, reports unavailable age bands explicitly, and measures catalog coverage.

## Deferred scope

PixiJS runtime rendering, video generation, production human gates, and caregiver feedback persistence remain separate follow-up features.

## Runtime inputs

- Real Vietnamese ASR output.
- Real VLM output.
- Replaceable image and WAV artifacts.
- Reviewed catalog records only.

## Canonical flow

```text
ASR + VLM -> one ConfirmedSceneUnderstandingV2 -> age ranking -> catalog gate -> V2 handoffs
```

## Constraints

- No credentials, raw model output, prompts, or child data in evidence.
- AI may suggest an existing catalog activity ID but may not create a new activity at runtime.
- Real-AI acceptance belongs on Lightning Studio; unit/contract tests may use provider doubles.
