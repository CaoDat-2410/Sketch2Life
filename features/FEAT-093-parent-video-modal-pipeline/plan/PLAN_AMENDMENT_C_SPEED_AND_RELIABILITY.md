# FEAT-093 Amendment C: faster generation and fewer failures

- Date: 2026-11-26
- Basis: live runs of 2026-11-26 (activity gate failure, two story failures after 5 minutes each, story
  decoding at about 5.7 tokens/s) and the owner's instruction recorded in `approvals/TASK_APPROVAL.md`.
- Extends Rev 2 + Amendments A/B. Everything not named here is unchanged.

## Work items

| ID | Change | Why |
|---|---|---|
| C1 | Remove the butterfly life-cycle rule (worker gate, backend gate, subject-specific prompt text). The general "no invented science facts" prompt rule stays; the adult reviews every story. | One hard-coded subject rule failed a whole story run. |
| C2 | Story `visual_prompt` limit 900 -> 320 characters, one or two sentences. | The five prompts hit the cap and were about 60% of the story output; the new video pipeline reads only the title and the three story sections. |
| C3 | Qwen speed spike on L40S: vLLM with the pinned FP8 checkpoint; measure context limit, FP8 KV cache, MTP on/off, constrained JSON. | Owner asked for KV compression, context limit, speculative decoding and a quantisation check. |
| C4 | If C3 reaches at least 3x the current single-stream rate and constrained JSON passes the existing parsers, serve every Qwen text/vision workload from vLLM (ADR-0025). Otherwise keep transformers and report. | Engine change only on measured evidence. |
| C5 | Bounded regeneration inside the Qwen worker (at most 3 attempts) when any shared-worker output fails a quality gate; later attempts sample (temperature 0.6). The story also samples on its first attempt. Needs C4 for acceptable time. | Greedy decoding repeats the same rejected output; the adult must otherwise restart. |
| C6 | Video pipeline: one retry for a failed or timed-out scene preparation, scene render or narration call; timeline attempts 2 -> 3. An unknown dispatch outcome is not retried. | One failed call currently discards the whole video. |
| C7 | Start the scene-preparation and scene-render containers while the timeline is being planned. | Their cold starts (about 8 and 14 minutes observed) run one after the other today. |

## Acceptance criteria

1. A butterfly story that omits a life-cycle stage is accepted by both worker and backend; offline tests cover it and no
   butterfly-specific gate or prompt text remains.
2. C3 produces a table of configurations with tokens/s, output validity and errors, stored in
   `evidence/M12_speed/`.
3. With C4 adopted: story generation on a warm container finishes in 90 seconds or less in the live run.
4. Offline tests prove: a gate failure triggers a new attempt and a third failure returns the existing error code; a
   transient scene failure is retried once and the second failure keeps the existing code.
5. At most two full live end-to-end runs (different subject and drawing) and one benchmark session of at most
   60 GPU-minutes. Both runs report per-stage timings. A run that fails is reported with its code, not hidden.
6. `python tools/validate_repository_security.py` passes before any commit.

## Not in scope

Parallel scene rendering on several LTX containers, changing model weights, production selection, commit/push to a
remote without a separate request.

## Results and changes after the spike (2026-11-26)

- C3 (evidence `evidence/M12_speed/bench_result.json`): vLLM 0.34.0 on L40S, real story prompt and schema.
  `transformers` live run about 5.7 tokens/s; vLLM 25.3; vLLM with MTP (3 draft tokens) 56.2. Constrained JSON cost
  nothing measurable and passed the story parser. The FP8 KV cache crashed engine start-up in the hybrid (mamba) layers.
- C4 adopted: context limit 16,384, MTP on, KV cache in the default type. Teacher-only standalone functions keep
  transformers.
- Retries are generic (no broken-rule note in the prompt), which differs from the first wording of C5.
- The story prompt now asks for a character-driven story instead of a description of the drawing.
