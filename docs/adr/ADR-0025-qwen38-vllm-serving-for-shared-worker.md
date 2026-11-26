# ADR-0025: serve the shared Qwen worker with vLLM

- **Date:** 2026-11-26
- **Status:** Accepted for the Modal `dev` environment (FEAT-093 Amendment C); production selection remains open.
- **Authority:** Owner instruction of 2026-11-26 to make Qwen generation faster (KV cache compression, context limit,
  speculative decoding, quantisation check).
- **SRS:** FEAT-063 v2.7-draft is the current unsigned baseline. This ADR does not amend it.

## Context

ADR-0024 pins `Qwen/Qwen3.8-27B-FP8` on L40S. Served through `transformers` with a token-by-token JSON constraint, it
decoded about 5.7 tokens/s, so one story took about five minutes and a rejected output could not be retried cheaply.

## Decision

1. `qwen-worker` serves the same pinned checkpoint with `vllm==0.34.0`: `max_model_len` 16384, MTP speculative decoding
   with 3 draft tokens, structured JSON output, thinking disabled.
2. A thin adapter (`qwen_vllm.py`) keeps the handlers' `generate` calls, schemas and quality gates.
3. A rejected output is generated again, at most three attempts.
4. The FP8 KV cache stays off: engine start-up failed in the hybrid (mamba) layers with it.
5. Standalone Teacher functions and the other workers are unchanged.

## Consequences

- Measured on L40S: 56 tokens/s with MTP against 25 without (evidence M12). Engine cold start 85-175 s.
- The character allow-list of the previous JSON constraint does not apply under vLLM; the non-Latin quality gate rejects
  such output and the retry replaces it.
- Greedy output differs from the `transformers` output; stored provenance still names the same model revision.
- Rollback: set the `qwen-worker` image back to the `transformers` image and redeploy.
