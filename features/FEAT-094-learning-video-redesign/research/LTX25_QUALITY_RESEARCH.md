# LTX-2.5: what decides video quality, and what our pipeline does today

Research date: 2026-11-26. Status: desk research plus code reading. **Nothing here has been benchmarked.**

## 1. Sources and their limits

Read:
- Lightricks/LTX-2 repository: [pipelines](https://github.com/Lightricks/LTX-2/blob/main/packages/ltx-pipelines/docs/pipelines.md),
  [conditioning](https://github.com/Lightricks/LTX-2/blob/main/packages/ltx-pipelines/docs/conditioning.md),
  [optimization](https://github.com/Lightricks/LTX-2/blob/main/packages/ltx-pipelines/docs/optimization.md),
  [root README](https://github.com/Lightricks/LTX-2/blob/main/README.md)
- Source at our tag v1.6.2:
  [types.py](https://github.com/Lightricks/LTX-2/blob/v1.6.2/packages/ltx-pipelines/src/ltx_pipelines/utils/types.py),
  [constants.py](https://github.com/Lightricks/LTX-2/blob/v1.6.2/packages/ltx-pipelines/src/ltx_pipelines/utils/constants.py),
  [distilled.py](https://github.com/Lightricks/LTX-2/blob/v1.6.2/packages/ltx-pipelines/src/ltx_pipelines/distilled.py)

Not readable: the LTX-2.5 and Layout-To-Render model cards on Hugging Face (HTTP 401), the ltx.io prompt guides (fetch
error; only search summaries seen), docs.ltx.video prompting guide (HTTP 403). Community posts below are unverified.

## 2. Facts that bear on quality

| Topic | Finding | Source strength |
|---|---|---|
| Distilled pipeline | Fixed 8 + 4 steps, no guidance, **no negative prompt**, `enhance_prompt` off by default | source code |
| Two stages | Stage 1 renders at half the target size, stage 2 upsamples | source code |
| Image conditioning | `replace` pins a frame (index 0 or 1+8k); `guide` steers any frame; strength has no default | source code |
| Input compression | Conditioning images are re-compressed with H.264 before use; default CRF is 18 for the 2.4 generation, 33 for older; `crf=0` skips it. Which default 2.5 gets was not confirmed | source code |
| End frame | First-plus-last-frame is documented only for the full-model two-stage pipeline; our code has used an end-frame `guide` on the distilled one (FEAT-087) | docs + our code |
| Prompt | One paragraph, at most 200 words, chronological, start with the action; camera wording such as "The camera remains static throughout" | repository README |
| Image-to-video prompt | Describe what happens, not what is already in the picture; re-describing causes drift; one dominant action | vendor blog summaries and community |
| Control video | `ICLoraPipeline` (distilled only) follows a reference video | docs |
| Layout-To-Render IC-LoRA | Turns a rough layout video plus an art-directed first frame into a finished shot (made for 3D blockouts) | search summaries; card unread |
| Higher quality | `DFRPipeline`: distilled model plus a detailing LoRA, "slower, more VRAM" | docs |
| Licence | LTX-2.x Community License (not Apache); one summary says free commercial use under USD 10M revenue | README; threshold unverified |

## 3. Our pipeline against those facts

| # | What we do | Why it matters | Confidence |
|---|---|---|---|
| F1 | The wrapper `_ltx_animation_prompt` says **"Add only a prop explicitly named in the approved action, once and beside the subject."** Run 1's action named the child | Invites the model to paint what the text names. Most likely cause of the child who was not drawn | likely, not proven |
| F2 | The same wrapper is mostly prohibitions ("no ... cards, screens, captions, logos, extra objects, speech") and re-describes the subject | With no negative-prompt support, naming unwanted things may bring them in; re-describing causes drift | docs support the risk |
| F3 | Only the first frame is conditioned (`replace`, strength 1.0) in the current path | Nothing holds the end of the clip, so content can appear or drift | code |
| F4 | CRF left at the checkpoint default | Recompression may soften thin crayon strokes | to test |
| F5 | Scene clips are cropped to 1280x720, then the assembler **pads them back to 1280x768 with white**, and the validator requires 768 | The final video has 24 px white bands and is not 16:9; BR-24 asks for 720p 16:9. **Defect**, visible in Run 1 | confirmed |
| F6 | Seed derives from story hash and scene index; a retry reuses it | A retried scene reproduces the same bad result | code |
| F7 | No check of generated frames (`VIDEO_VISION_CHECKS_PENDING`) | An added child reaches the parent; SRS FR-AI-06 and FR-AI-12 expect consistency and safety checks | confirmed |
| F8 | `OffloadMode.CPU` | Speed, not quality. The source states about 28 GB VRAM without offload for LTX-2; 2.5 not stated | to test |

Correction to `LTX25_SPEED_NOTES.md`: the docs call `fp8-scaled-mm` best on Hopper and later and meant for FP8
checkpoints (L40S is Ada); `fp8-cast`, which we use, is the policy for bf16 checkpoints. No flag to skip audio exists
in `DistilledPipeline`.

## 4. Proposed experiments (same drawing, keyframe and seed; one change at a time)

| ID | Experiment | Judged on |
|---|---|---|
| E1 | New prompt: motion only, starts with the action, static camera sentence, no prop or prohibition clauses | new objects, drift |
| E2 | End-frame guide with the composited end keyframe, strength 0.7 and 0.9 | drift, new objects, amount of motion |
| E3 | CRF 0, 18, 33 | stroke sharpness, motion |
| E4 | `OffloadMode.NONE`, then `torch.compile` | seconds per scene, peak VRAM |
| E5 | `DFRPipeline` | quality against time |
| E6 | `ICLoraPipeline` driven by a rendered cut-out animation (links to the motion-type library) | stroke fidelity, controllability |

Each render is judged by a fixed checklist plus an automated check: the Qwen worker compares sampled frames with the
first frame and reports new objects or people and changes to the subject. That check can later gate production output:
regenerate with a new seed (SRS allows two retries per scene), then fall back to the cut-out clip.

Estimated cost for E1-E3 on three drawings: about 18-20 renders, about 45 GPU-minutes on L40S.

## 5. What this research does not answer

LTX-2.5's stated limits on illustrated or children's-drawing input; its VRAM need; recommended end-frame strength;
whether Layout-To-Render works on flat 2D layouts; independent quality comparisons. All need the model cards (gated;
the owner's Hugging Face access can open them) or our own tests.
