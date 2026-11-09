# Rev45 non-video AI execution — 2026-11-05

**Status: PARTIAL.** Callable Qwen and speech workers now pass synthetic inference and output-contract checks. FLUX image generation remains blocked by missing Hugging Face access in Modal `dev`; optional SAM2 remains blocked by GPU scheduling. No video workload was called.

## Root cause and repair

Story and Teacher Deck generation had ended early with incomplete JSON even though their prompts and output limits appeared valid. The parser used LM Format Enforcer's default 92-character ASCII alphabet. When a Vietnamese letter such as `ư` or `ớ` appeared inside a bounded JSON string, the character parser discarded its active object/string state; `can_end()` then returned true and Qwen's model EOS became allowed before the JSON object had closed.

The worker now extends the LMFE alphabet with Unicode Latin, combining marks, Vietnamese letters, and typographic punctuation. The environment value is set at runtime immediately before importing LMFE. A first deploy attempt exposed a separate Dockerfile quoting issue when the alphabet was passed through `Image.env`; moving it to runtime configuration resolved the build issue without removing JSON quote/backslash characters. The strict output parser, schema bounds, semantic checks, and human review gates remain active.

## Synthetic Modal results

All six requests used synthetic assets or text and reached terminal results. Parent drawing analysis used one generated butterfly drawing; the proposed subject still requires adult confirmation. Story generation was called only after the runner recorded synthetic adult confirmation.

| Workload | Result | Caller elapsed | Modal call |
|---|---|---:|---|
| `drawing.analyze` | Passed; Qwen3.5 returned candidate `bướm` and visible features; adult confirmation required | 44.014 s | `fc-01M6NSD166E4AFKA97S4SPT38M` |
| `story.generate` + `storyboard.generate` | Passed strict worker/output and lifecycle checks; 5 scenes, 30 seconds | 113.381 s | `fc-01M6NSEAXMP5F4WQX8KGF9BCWC` |
| `teacher.sketch-deck.generate` | Passed; 5-slide 16:9 Vietnamese `DRAFT`, 4 drawing steps, 2 approved activity references | 43.464 s | `fc-01M6NSHST2SCSG9JMH572ZHSWH` |
| `lesson.plan.suggest` | Passed `LessonContentInputV1`; one outdoor activity, `age-band-3-6`, `vi-VN`, `draft_only=true` | 61.636 s | `fc-01M6NSK42V631DF61H4T3QCFH0` |
| `tts.narration.generate` | Passed; valid synthetic WAV, 153,644 bytes | 19.161 s | `fc-01M6NSQ9G0AKKPX8K1KHA8ZYC` |
| `asr.transcribe` | Passed; exact Vietnamese fixture transcript, language `vi`, probability 1.0 | 23.900 s | `fc-01M6NSQX455RM0V9ZY1Y5F4CEQ` |

Model pins: `Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a`; `VieNeu-TTS-v3-Turbo@61b85e3d937fbbacb387714180e8182823512523` with `MOSS-Audio-Tokenizer-Nano-ONNX@ceff0d0749bfb3fa2d61149794ec6feef0d1e1ae`; `faster-whisper-large-v3@edaa852ec7e145841d8ffdb056a99866b5f0a478`.

The constrained-decoder CPU probe returned `ready`, including `story_partial_vietnamese_eos_blocked=true` and nested Story/Teacher length-limit checks. The pinned-model GPU generation probe emitted 12 tokens; all were allowed by the callback and the resulting JSON was valid (1.4 seconds generation time). Captured probe responses: [`modal_qwen35_decoder_probes.json`](assets/ai_nonvideo_ai_end_to_end_20261105/vietnamese_alphabet_retest_12/modal_qwen35_decoder_probes.json); synchronous `.remote()` did not expose a Modal call ID for these diagnostics.

Machine-readable per-call evidence and the WAV fixture are in [`assets/ai_nonvideo_ai_end_to_end_20261105/vietnamese_alphabet_retest_12/`](assets/ai_nonvideo_ai_end_to_end_20261105/vietnamese_alphabet_retest_12/). Speech round-trip evidence is in [`assets/ai_nonvideo_ai_end_to_end_20261105/speech_retest_13/`](assets/ai_nonvideo_ai_end_to_end_20261105/speech_retest_13/).

## Remaining blockers and API limits

- **Parent Sketch Guide / lesson visuals (FLUX.3):** Modal `dev` still has no `sketch2life-dev-huggingface` Secret. The pinned checkpoint download previously returned HTTP 401. No image request was dispatched in this run. The owner selected adding an HF token as a Modal Secret; this must be present before the two image workloads can be exercised. No secret value was read or written by this task.
- **Optional `drawing.segment` (SAM 2.1):** the staged checkpoint remains integrity-verified, but the last synthetic call waited 1,800 seconds for `GPU_L4` capacity and created no mask. This pass did not recheck current GPU availability or repeat the capacity-only attempt. Segmentation remains optional; retain the source image and use the OpenCV/Pillow baseline.
- **Product REST API:** the six live calls above invoke private Modal workers; they do not prove a durable authenticated product API. The main backend OpenAPI still has no AI dispatch operation. StoryRun-lite is fixture-only and its Modal work is process-local. The focused route/contract/OpenAPI suite passed, but the broader SRS routes for Parent guide/story gates, Teacher deck, lesson visuals, and shared durable job polling remain absent or unspecified in the current catalog.
- **Video:** all video generation, composition, validation, safety, and playback were excluded as requested.

## Verification and shutdown

- Modal worker/parser tests: **76 passed**.
- Focused backend API, Lesson Library, Modal client, AI contract, and OpenAPI tests: **61 passed, 6 skipped**.
- `py_compile` and targeted Ruff passed for the changed worker, tests, and evidence runners.
- Both task-used Modal apps (`sketch2life-srs23-language-audio-dev`, `sketch2life-srs23-drawing-vlm-dev`) were stopped and verified at **0 tasks**. Shared model and scratch Volumes were preserved. The Modal `dev` Secret list was empty at shutdown.
- Repository security validator passed for 6,556 publishable files; `git diff --check` exited 0. The validator initially matched non-secret configuration identifiers containing `SECRET`/`TOKEN`; those identifiers were renamed, with runtime behavior and the actual Modal secret/environment key unchanged.
- Product workload switches remain disabled. No commit or push was made.
