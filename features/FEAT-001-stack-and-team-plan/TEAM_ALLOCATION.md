# Four-person MVP workstream allocation

The four workstreams map to the reference workbook while adding explicit integration ownership so the complete flow is covered.

| Person | Primary ownership | Main deliverables | Critical handoffs |
|---|---|---|---|
| Person 1 | Montessori domain, recommendation, Gate B | Versioned activity catalog, hard constraints, learning-objective lock, ActivityHandoff, fixture/evaluation rules | Contracts to P2/P4; approval UI needs to P3 |
| Person 2 | Multimodal understanding + AI adapters | Image/audio quality, Whisper, Qwen3-VL, fusion, uncertainty, Raw/CanonicalUnderstandingResult, Lightning-dev and Runpod-production adapters | Gate A data to P3/P4; provenance to P1 |
| Person 3 | Mobile app + personalized art animation | React Native capture/playback, Gate A/B screens, PixiJS/GSAP bridge, original-art preservation, visual asset gate | Contracts from P1/P2/P4; device evidence |
| Person 4 | Backend orchestration + learning media | FastAPI facade, session/job state machine, experience planner, cache-first resolver, Wan2.2/validation/fallback, storage/queue integration | Integrates all outputs; deployment/e2e evidence |

## Shared milestones

1. Contract freeze: all four review schemas, IDs, versions, and fixture manifests.
2. Vertical slice: capture -> understanding -> Gate A -> recommendation -> Gate B.
3. Experience slice: original-art animation -> learning asset -> Activity Bridge.
4. Full E2E: feedback, deletion semantics, observability, and fixture evaluation report.

Ownership means primary implementer, not sole reviewer. Each workstream needs one cross-reviewer from another person before it is marked done.
