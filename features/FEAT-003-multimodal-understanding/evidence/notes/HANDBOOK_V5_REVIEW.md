# Handbook v5 review for FEAT-003 planning

- Review date: 2026-08-26
- Reviewer: Codex, at the project owner's request
- Source: `D:/Downloads/Sketch2Life_Complete_Technical_Handbook_v5_Revised (1).pdf`, 26 pages
- Authority: contextual planning input only. Direct user requests, accepted repository ADRs, and explicit task approval take precedence.
- Scope of review: Flow 1 multimodal understanding, validation/privacy, contracts, tech stack, observability, and evaluation.

## Planning conclusions used in plan revision 3

1. Inputs are original drawing plus narration, handled on separate paths; an unusable image or audio must request recapture rather than silently become a single-modality understanding result (pages 7-8).
2. Source media is immutable. Preprocessing is a working copy with its own provenance (pages 5 and 15).
3. The proposed baseline is Whisper large-v3-turbo through faster-whisper for ASR and Qwen3-VL-8B Instruct for drawing understanding. The repository still treats exact provider/model profile as benchmark and approval work (pages 8 and 18; ADR-0005).
4. ASR/VLM provider output must be converted to versioned structured contracts. `RawUnderstandingResult` preserves support, conflict, uncertainty, and provenance, and is only an AI proposal before Gate A (pages 6, 8, 16, and 22).
5. No psychological, personality, diagnosis, or mental-state inference is permitted from drawings (pages 5 and 23).
6. Evaluation needs schema validity, ASR WER/CER, drawing entity/action accuracy, uncertainty/conflict review, and latency. Standard logs must not contain raw child media; this feature uses synthetic fixtures only (pages 21-23).

## Reconciliation with repository decisions

- ADR-0006 is controlling for Sprint 1 ownership: P2 provides a standalone fixture/contract component, not Gate A, API, session/job orchestration, or integration runtime.
- ADR-0005 is controlling for provider lifecycle and credentials: fixture/dev access only until separately approved; production Runpod usage remains behind backend ports and no provider credential/endpoint enters mobile or source control.
- Threshold values are not frozen by this plan because the handbook itself requires target data/hardware benchmarking before freezing model-specific numbers.
