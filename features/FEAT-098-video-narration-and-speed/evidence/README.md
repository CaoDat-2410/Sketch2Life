# FEAT-098 evidence

## Offline checks (2026-11-27, no GPU)

| Check | Result |
|---|---|
| Modal worker tests (`deployment/modal/srs_v23/tests`) | 529 passed, 5 skipped (includes real ffmpeg 7.1 runs of the default and the `small,fps16` filters) |
| Full backend suite (`backend/tests`) | 12583 passed, 1647 skipped, 116 failed, 11 errors |
| The 116 failures on the committed version (`git archive HEAD`) | the same 116 tests fail with the same messages (set order aside): none comes from this work |
| The 11 errors | 10 also error on HEAD; the 11th is a duplicate test file name (`test_owned_sql.py`) that appears only when the whole suite is collected |
| Repository security validator | `REPOSITORY_SECURITY_VALID` |
| Lint | no new `ruff` finding in `backend/`; `deployment/` already uses long lines and is left as it is |
| Image build (CPU) | first build failed (D8), then built; `natten 0.21.7+torch2130cu132` installed and imported |
| Convolution VAE | staged on the model volume (`vae/ltx-2.5-video-vae-conv-bf16.safetensors`) |

## Local assembly check (`assembly/`)

The real planner, narration timing, captions and ffmpeg assembler, with a saved LTX clip looped to each scene's planned
length and a tone as long as the voice would take (about 16 letters a second). It shows timing, not picture or voice
quality. Script: `assembly/assembly_check.py`; numbers: `assembly/assembly-report.json`.

| Age | Spoken words | Voice share | Length | Scene lengths | Held (frozen) time |
|---|---|---|---|---|---|
| 4 years | 115 | 47% | 50.9 s | 10.0 to 10.4 s | none |
| 9 years | 182 | 53% | 70.0 s | 10.0 s | none |

## GPU measurement (`benchmark/`)

One L40S session (2026-11-27, 17:04 to 17:18), the 10 s chick scene of the FEAT-094 speed measurement, same keyframe,
prompt and seed 940101. Script `benchmark/render_bench.py`, raw numbers `benchmark/report.json`, clips
`benchmark/<name>-<n>.mp4`, all five together `benchmark/side-by-side.mp4`. The two renders of a variant are identical
files. About 20 L40S minutes (timed stages 17.6 min plus two cold starts; estimate, not a bill).

| Variant | Render, second run | Against base | Normalise (CPU) | First-render compile | Peak GPU memory | Picture (sampled frames) |
|---|---|---|---|---|---|---|
| base (no `natten`) | 74.2 s | | 0.5 s | 65.8 s | 34.4 GB | reference |
| `natten` (switched on, S1) | 71.7 s | -3% | 0.5 s | 55.2 s | 34.5 GB | same as base |
| `conv_vae` (+ `natten`) | 56.5 s | -24% | 0.4 s | 22.1 s | 22.0 GB | close to base; the comb is slightly softer in one fast movement |
| `small` (+ `natten`) | 36.4 s | -51% | 0.5 s | 24.0 s | 32.3 GB | softer lines; the head smears and a leg breaks near the end |
| `fps16` (+ `natten`) | 45.1 s + 54.5 s CPU | +34% in total | 54.5 s | 23.0 s | 33.2 GB | colours of the head jump near the end |

- `natten` gives much less than hoped: about 2.5 s per scene and 10 s on the first compile.
- `fps16` is slower overall: ffmpeg motion interpolation costs more than the GPU saves.
- Compile times of the later variants share one container with `natten`, so part of their gain may be a warm compiler
  cache; the render times are the fair comparison.
- `conv_vae` with `small` together was not measured.
- Engineer's reading: `conv_vae` is worth switching on; `small` and `fps16` are not. The owner decides.

## One video through the app

**First attempt (2026-11-27, run `04be37ea`, synthetic deer drawing, 48 months): stopped at story review, no video
made.** The story the app showed is not a learning script (stored content: opening, middle, ending; no `learning`;
`prompt_version` `parent-story-rewrite.v1`). The app's first story starts by itself after context confirmation
(`story_first_start.py`), and that path, like the rewrite path, never builds the learning request; only
`reserve_story_revision` does, which this flow does not call. This gap dates from FEAT-094, whose app flow was never
verified. Without a fix, the app's videos keep the short narration and nothing is prepared during review.

Also seen: the activity suggestions were refused twice by their existing quality gate
(`EXPLORATION_NOT_EXPLICIT`, `CHILD_AGENCY_NOT_EXPLICIT`); the app's retry then passed.

**First-story path fixed** (owner, 2026-11-27: "Sửa rồi chạy video"): the Parent first story now asks for the learning
script (`story_first_start.py`; three tests, watched failing first; the story, learning and video tests show no new
failure).

**Rewrite in the app is broken, not fixed.** "Viết lại câu chuyện" calls `story-rewrites`, which builds
`sketch2life.story-rewrite-input.v1`; the Modal story client accepts only `story-generation-input.v3`, so every app
rewrite ends `STORY_INPUT_CONTRACT_INVALID` (seen on run `04be37ea`). It dates from before FEAT-098. Fixing it changes
how the adult's rewrite hint (untrusted text, kept in its own field) reaches the worker, so it needs its own decision.

**Second attempt: video made** (run `dd8a3ee8`, same drawing, profile 48 months; the first run was cancelled in the app
after the owner agreed). Learning script, 5 scenes, drafted facts (the deer card is still `DRAFT`), antler lines
spoken. Files in `app_run/`: `app_run.mp4` (original, 70 MB, kept locally, not committed), `app_run_preview.mp4` (re-encoded copy for viewing),
`captions.vtt`, `story.json`, `contact_sheet.png`.

Timeline (local time): story ready 18:11:33; five pictures prepared 18:13:50 to 18:14:16 (cold video container);
renderer ready 18:15:52; "Xác nhận câu chuyện này" 18:17:03; video requested 18:17:35; first scene started 18:19:47;
video ready 18:23:30.

| Acceptance (plan section 6) | Target | Run 4 | This run | Met |
|---|---|---|---|---|
| Spoken words, 3 to 5 years | at least 110 | about 58 | 97 (18 to 21 per scene; 22 to 25 asked) | no |
| Voice share of the length | at least 45% | 24% (38.1 s silent) | 39% (30.5 s silent) | no |
| Frozen scene ends | none | one 0.7 s freeze | none (`freezedetect`) | yes |
| Length | within 10%, 30 to 90 s | 50 s | 50 s | yes |
| Facts per band, marked | 5, source shown | 3 | 5, shown as AI drafts | yes |
| Video request to ready | at most 7.5 min (aim 5) | 10 min 23 s, cold | 5 min 54 s | yes (aim missed) |
| Existing tests | pass, v1 stories load | | no new failure | yes |

Conditions of the time: the script was left in review for 5.5 minutes, so pictures and renderer were ready before
the request. A confirmation sooner than about 4.5 minutes after the story would have waited for part of that. Not
measured.

Where the time still goes: the first render started 2 min 12 s after the request. The five cached pictures answered by
18:18:23; the voice (about 15 clauses, one call every 6 s, 1.5 s of work each) ran until 18:19:41, and since FEAT-098
rendering waits for all of it. Rendering a scene as soon as its own voice is ready, or making the voice during review,
would remove most of that wait. Not built.

Picture (sampled frames, not judged by the owner): the child's deer stays whole, scenes have no frozen end; in the
last scene it lowers its head and comes back. The deer is paler than in the drawing and the drawn tree is cut into a
loose green patch and a trunk; both are already in the prepared first frames, so they come from preparation, which this
feature did not change. The file is 11 Mbit/s (run 4: 3.9) because the assembler encodes at constant quality (CRF 18)
and these backgrounds are detailed; a 70 s video at this rate would be near the 100 MB playback limit.

GPU use: about 20 L40S minutes for the measurement and about 16 for this video container (start to idle shutdown):
about 36 of the 45 approved (from container times, not a bill).

## Found, not changed

- Rewrite in the app (above): always refused.
- The activity suggestions' quality gate refused the first answer in both runs; the app's retry passed.
- The app's remaining-time estimate still assumes 90 s a scene (`story_run_detail.py`) and showed 12 minutes.
- The spoken-text filter, found here as well, was fixed afterwards with the owner's yes (amendment A in
  `approvals/TASK_APPROVAL.md`; `backend/tests/unit/test_spoken_text_filter.py`).
