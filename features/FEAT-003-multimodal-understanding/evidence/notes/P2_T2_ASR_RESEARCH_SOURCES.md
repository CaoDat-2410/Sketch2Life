# P2-T2 ASR research-source note

- Date: 2026-08-28
- Scope: research/plan preparation only. No model, SDK, provider, GPU, or audio execution occurred.
- Related plan: `../../plan/P2_T2_ASR_RESEARCH_PLAN.md`

## Sources reviewed

| Source-register ID | Finding used in the plan | Planning consequence |
|---|---|---|
| `user-provided-handbook-v5-revised` | Audio passes a quality gate before ASR; ASR must preserve transcript, language, timestamps/confidence, source provenance, typed failure handling, and privacy boundaries. Model choices must be benchmarked before freezing. | Require the P2-T1 `PASS` link, preserve immutable source provenance, and defer model/profile lock-in to a measured benchmark. |
| `whisper-large-v3-turbo-model-card` | The candidate is a pruned, faster Whisper large-v3 variant with a stated quality/speed trade-off. | Treat it as a benchmark candidate, not a pre-approved quality conclusion. |
| `faster-whisper-transcription-api` | The upstream API exposes segments, language probability, timing, VAD-related information, and model diagnostic values. | Map only needed fields into `AsrResultV1`; do not expose SDK objects or raw provider output. |
| `faster-whisper-runtime-guide` | Compute profiles, VAD, word timestamps, and decoding settings have measurable runtime/quality effects; comparisons require equivalent settings. | Compare controlled profiles and record configuration hashes, cold start, and latency separately. |

## Open decisions

1. Exact model/revision and local-weight provenance.
2. Auto-detect versus declared fixture language policy.
3. Decode, VAD, and word-timestamp profile.
4. Approved runtime/device and timeout budget.
5. Vietnamese text-normalization/tokenization specification for WER/CER.

At the time of this 2026-08-28 research note, these decisions were open. The Phase B scope
is now approved under `approvals/TASK_APPROVAL.md`; the remaining `DECISION_REQUIRED` item is
the synthetic/TTS-versus-licensed fixture source and the subsequent supply of compliant local
fixture/reference-transcript refs and hashes.
