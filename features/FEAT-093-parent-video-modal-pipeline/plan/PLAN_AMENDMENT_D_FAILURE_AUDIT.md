# FEAT-093 Amendment D: failure audit and shorter waits

- Date: 2026-11-26
- Basis: owner instruction in `approvals/TASK_APPROVAL.md`; review of the story, activity, understanding and video paths;
  smoke calls on the vLLM worker (evidence M12).

## Findings and fixes

| ID | Finding | Fix |
|---|---|---|
| D1 | Worker retries missed story gate errors (`ValueError`) and most `MODAL_MODEL_OUTPUT_*` codes. | Retry on every output-rejection code, whichever exception class. |
| D2 | The backend activity gate rejects the whole answer with no second try, and rejected units ("5 cm") the worker accepts. | Same sentence rule on both sides; one more generation when the backend gate rejects; activity and story sample without a fixed seed so a second call differs. |
| D3 | A dead vLLM engine would leave the warm container failing every call. | Stop the container from taking inputs and report a stable code. |
| D4 | Context limit 16,384 leaves about 11,900 input tokens for activity suggestions. | 32,768 (the KV cache pool is larger than one request needs). |
| D5 | Timeline: complete lines ending in "rồi" were rejected; the prompt had lost its line breaks; a one-subject drawing could get impossible interactions; retries repeated greedy output. | Fixed in the parser, prompt, schema and sampling. |
| D6 | Captions could fail the whole video after every scene was rendered (cue too short, too fast or too long with a speaker label). | Place voice clauses with reading time reserved, so the caption rules hold by construction. |
| D7 | Silence at the edges of a voice clip failed the run although the assembler trims it. | Not a failure. |
| D8 | A finished video of 29.99 s or 90.01 s failed the window check. | One-frame tolerance. |
| D9 | Client waits (900 s preparation, 1,700 s render) are close to cold start plus queue. | 1,800 s and 2,700 s. |
| D10 | Narration waited behind scene preparation on one thread although they use different containers. | Separate thread. |
| D11 | Unexpected pipeline errors left no trace. | Log the exception type. |
| D12 | Custom-topic checking crashed on a setting that does not exist. | Add the setting (default off, as in `.env.example`). |
| D13 | The Qwen engine starts cold (about 3.5 minutes) at the first AI step. | Warm it when the parent opens the topic step (at most once per 5 minutes). |

## Acceptance criteria

1. Each finding has an offline test that failed before the fix, where the behaviour is testable offline.
2. A smoke call of every shared-worker workload succeeds on the deployed `dev` app.
3. Two live app runs (different subject and drawing) are reported with per-stage times; failures are reported with codes.
4. Repository security validation passes before any commit.

## Not in scope (needs a separate decision)

Rendering scenes on several LTX containers at once or on a larger GPU (cost change), vision-based video checks, keeping
the parent signed in after the app is closed.
