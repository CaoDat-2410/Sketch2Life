# Longer narration and faster video: research (2026-11-27)

No GPU was used. Sources: the code on `dev`, the FEAT-094 run notes, one local measurement on a saved video, and web
pages (third-party claims are marked as such and were not tested here).

## 1. Where things stand

Learning video for 3 to 5 years: 5 scenes of 10 s, 1280x720, one L40S that prepares the pictures and then renders.

### Narration

| Item | Value | Where |
|---|---|---|
| Word cap per scene | 18 (3-5), 22 (6-7), 24 (9-10) | `backend/.../domain/learning_script.py` |
| Written in practice | 11 to 13 words although 14 to 18 are asked | `FEAT-094/evidence/M6_remaining/RUN.md` |
| Voice in the 50 s video of run 4 | about 12 s (24%); about 58 words, near 5 syllables per second | measured with `silencedetect` (-40 dB, 0.35 s) on `learning_run4.mp4` |
| Voice per scene | about 2.4 s of speech, then about 6 s of silence | same measurement |
| When the voice is longer than the clip | the last frame is held (frozen) | `ffmpeg_assembler.py` (`tpad`), `orchestrator.py` (`apply_stretches`) |
| Limits | 30 to 90 s total, 5 to 15 scenes (BR-24, FR-AI-04); a scene at most 473 frames (19.7 s) | SRS, `age_profile.py` |

So the narration is short for two reasons: few words, and a fast voice. The SRS allows 90 s; the video uses 50 s.

### Time (run 4, 50 s of video, video container cold, 623 s)

| Stage | Seconds | Share |
|---|---|---|
| Scene pictures (FLUX and SAM, loading included) | 81 | 13% |
| Waiting for the picture checks | 20 | 3% |
| First scene, renderer load included | 164 | 26% |
| Four more 10 s scenes at 87 to 93 s | about 360 | 58% |
| Writing the story before that (separate step, cold Qwen) | 257 | not in the 623 s |

Experiment on the same GPU (FEAT-094 `M1_experiments/RESULTS_SPEED.md`, profile `decode`, which is in use): a 6 s scene
renders in 39.5 s and a 10 s scene in 70 s. Of the 70 s: stage 1 about 14 s, stage 2 about 28 s, video decoding about
25 s. Once per container: reading checkpoints about 40 s, encoding prompts 13 s, compiling the decoder 35 s.

Render time grows with the number of generated frames, and today every second of video is generated.

## 2. Options for longer narration

| # | Option | GPU cost | Notes |
|---|---|---|---|
| N1 | Write more: three sentences per scene with a minimum length for each, checked and rewritten | text only | The model ignored a word target; a schema with three required sentences and character minimums constrains it. Not tested. |
| N2 | Speak slower (time stretch that keeps pitch, `atempo` 0.8 to 0.85, or a voice speed setting if VieNeu has one) | none | About 5 syllables per second now. One non-peer-reviewed source suggests about 120 words per minute for young children (English). Voice quality after stretching needs listening. |
| N3 | Scene length follows the voice; generated motion stays short (about 6 s) | less than today | Needs N4 for the remaining seconds. Already listed as an open owner decision in FEAT-094. |
| N4a | After the motion, a close-up of the part being taught, with its name and a slow zoom, cut from the prepared picture or the drawing | none | Teaching moment; no new content is invented. Needs a part position (recognition gives none today) or a fixed crop of the subject. |
| N4b | Slow zoom or pan on the last frame instead of freezing it | none | Smallest change. |
| N4c | Play the clip forwards then backwards | none | Wrong for directed actions (walking, pecking reversed). Not proposed. |
| N4d | Generate longer motion (12 s per scene) | about +45% render time | Goes against the second goal; longer clips drifted more in earlier runs (zoom, panning). |

Budget with N1 to N3: 24 to 28 words per scene at about 4 syllables per second is 6 to 7 s of speech plus 2 s of
pauses; at about 3.3 it is 8 to 9 s plus pauses. Five scenes then give 50 to 60 s with 60 to 75% voice; six scenes give
60 to 70 s. Older age bands stay under 90 s with at most seven scenes of 12 s.

## 3. Options for shorter generation

Estimates are arithmetic on the measurements above, not new measurements.

| # | Option | Expected effect | Evidence | Risk |
|---|---|---|---|---|
| T1 | Generate 6 s per scene instead of 10 s (with N3 and N4) | about 30 to 40 s less per scene, about 3 min per 5-scene video | 39.5 s against 70 s in our experiment | motion covers only part of the scene |
| T2 | Prepare pictures and load the renderer while the adult reviews the script (S6 exists but was never seen in the app; S7 early pictures not built) | hides about 80 to 160 s of waiting after the confirm tap | stage times above | GPU paid for nothing if the adult leaves or rewrites |
| T3 | Convolution video VAE (`ltx-2.5-video-vae-conv-bf16`) instead of the diffusion VAE | decoding is 25 of 70 s today; may also remove the 35 s compile | model card calls it "faster, lighter"; **no figure given** | picture quality; must be compared side by side |
| T4 | Render smaller (for example 960x544) and upscale to 720p | stages and decoding scale with pixels; maybe 35 to 45% less per scene | not measured | soft lines |
| T5 | Render scenes on 2 or 3 L40S at once | wall time of rendering divided by up to 2 or 3 at the same GPU seconds, plus one load per extra machine | arithmetic | the owner ruled this out in FEAT-094 (Q7); cost of loads |
| T6 | A faster GPU (H100 at about 2.0 times the L40S price per second, A100 80 GB at 1.28 times) | unknown | Modal pricing page; no LTX-2.5 figures for these | only worth it if the speed-up exceeds the price ratio; plan S9 needed a separate yes |
| T7 | Fewer frames per second and interpolation (RIFE or the LTX temporal upscaler) | fewer frames to generate | temporal upscaler is only wired into another pipeline (`dfr_pipeline`) | smeared crayon lines; more work |

Not useful here:

- **Modal GPU memory snapshots**: alpha; the documentation says they do not speed up loading weights from storage.
- **NVIDIA Sol Engine / Sol-Attn**: measured only on B200, RTX 5090 and GB10; no code link or Ada figure found.
- **Fewer denoising steps / TeaCache**: the distilled schedule is fixed (8 + 3 steps); no figure found for caching on it.

## 3b. Added after the owner's pasted tips (same day)

- **A decoder option we are missing:** the LTX optimization notes call the `natten` extra the fastest production path for
  the diffusion video decoder on Hopper, Ampere and Ada cards; without it decoding falls back to Triton or eager code.
  Our FEAT-094 report records `natten: null` (`M1_experiments/speed_decode/report.json`). No timing is published.
- The distilled pipeline runs 8 steps then 4 steps, and no flag changes that or skips the second stage. No single-stage
  speed figure exists (the one-stage pipeline is documented as educational).
- "LTX-2.5 Fast" (Layer, Replicate) is a hosted product; the repository lists no open "fast" weights besides the
  distilled checkpoint.
- 12 or 16 frames per second is not documented for the distilled pipeline. By the documented token formula, halving the
  frames about halves the video tokens.
- No published seconds per clip for L40S or other Ada cards were found.
- Docs: https://github.com/Lightricks/LTX-2/blob/main/packages/ltx-pipelines/docs/optimization.md and
  https://github.com/Lightricks/LTX-2/blob/main/packages/ltx-pipelines/docs/pipelines.md

The owner then chose to keep the video length and generate longer motion rather than add filler pictures, so options
N4 and T1 above are not in the plan.

## 4. Rough combined estimate (not measured)

Five scenes, from the confirm tap, video container cold:

| Set | Video length | Wait | GPU seconds |
|---|---|---|---|
| Today (run 4) | 50 s | about 10.4 min | about 620 |
| T1 | 55 to 65 s | about 7.5 min | about 430 |
| T1 + T2 | same | about 4.5 to 5 min | about 430 |
| T1 + T2 + T3 (if it helps as hoped) | same | about 3.5 to 4 min | about 370 |
| T1 + T2 + T5 with two machines | same | about 3 min | about 520 |

At the listed L40S price (0.000542 USD per second) 620 s is about 0.34 USD for the video GPU, 430 s about 0.23 USD.

## Sources

- LTX-2.5 model card: https://huggingface.co/Lightricks/LTX-2.5
- Sol Engine page: https://nvlabs.github.io/Sana/Sol-Engine/LTX25/
- ComfyUI LTX-2.5 guide: https://docs.comfy.org/tutorials/video/ltx/ltx-2-5
- Modal memory snapshots: https://modal.com/docs/guide/memory-snapshots
- Modal pricing: https://modal.com/pricing
- Speech rate for young children (an audiologist's statement, not a study): https://wichita.edu/about/wsunews/archive/index.php?nid=3349
