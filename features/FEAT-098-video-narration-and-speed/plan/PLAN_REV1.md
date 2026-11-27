# FEAT-098 plan Rev 1: more narration and knowledge, faster video

Status: awaiting the owner's approval. Evidence and sources: `../research/VIDEO_RESEARCH.md`.

## 1. The owner's choices (chat, 2026-11-27)

| Question | Answer |
|---|---|
| Length and narration | No need for a longer video; say more, with more knowledge. |
| Voice longer than the motion | The AI generates the longer motion (no filler pictures). |
| Speed | Try the pasted tips (distilled/fast, draft then upscale, lower resolution/frame rate, memory) and research them. |
| GPU testing | Finish everything, then run the video test. |

## 2. Goals

1. About twice the words and more facts per video, at about today's length (5 scenes, about 10 s each).
2. Shorter wait from the confirm tap to a finished video, on the same single L40S.

## 3. Part A: narration

| Age | Scenes | Facts now → new | Words per scene now → new |
|---|---|---|---|
| 3 to 5 | 5 | 3 → 5 | 11-13 written → 22-25 |
| 6 to 7 | 6 | 4 → 6 | up to 22 → 28-32 |
| 8 to 10 | 7 | 5 → 7 (6 if the card has 6) | up to 24 → 28-32 |

- A1. Script shape: three sentences per scene as three required fields with a minimum length each; one scene may carry
  two facts; the ending recaps. The "no knowledge outside the facts" check stays.
- A2. Limits updated together: worker request check (12 to 26 words and `facts <= scenes - 2` today), backend bands,
  age speech-rate table.
- A3. The upper word numbers keep today's caption reading speed (14 characters per second for 3 to 5, 18 older) inside
  a 10 s scene. More words for 3 to 5 would need a faster caption rule; not proposed.
- A4. Voice first: the narration is synthesised before rendering, and each scene is rendered to the voice length
  (10 s normally, up to 12 s). The frozen last frame remains only as a last resort above 12 s. Total stays within
  90 s (BR-24).
- A5. Voice speed: try 0.9 (pitch kept) for 3 to 5 and keep it only if it sounds natural.
- Facts come from the knowledge card when approved, otherwise they are AI drafts the adult reviews (as today). The 40
  cards have 6 or 7 facts each and are still `DRAFT`.

## 4. Part B: speed

### B1. Built and switched on (no intended change of the picture)

| # | Work | Expected | Basis |
|---|---|---|---|
| S1 | Install the `natten` extra of `ltx-pipelines` in the video image | faster decoding (25 of 70 s per 10 s scene today) | the LTX docs name it the fastest decoder path on Ada cards; our FEAT-094 report shows `natten: null`, so it is not installed. No timing published |
| S2 | While the adult reviews the script: prepare the scene pictures, then load the renderer; redo only rewritten scenes | hides about 80 to 160 s after the confirm tap | run 4 stage times; the warm-up exists, early pictures do not |
| S3 | A4 above | no GPU time on frozen or unused frames | |

If `natten` cannot be installed for the pinned torch and CUDA, that is reported and the decoder stays as it is.

### B2. Built behind a setting, off until measured and accepted

| # | Option | Pasted tip it answers | Expected (arithmetic, unmeasured) |
|---|---|---|---|
| S4 | Convolution video VAE | lighter model parts | shorter decoding; softer picture possible |
| S5 | Render 960x544, upscale to 720p | lower resolution, then upscale | about 35 to 45% less per scene |
| S6 | Render 16 frames per second, interpolate to 24 | lower frame rate | up to about 30% less; support for 16 fps is not documented |

Not applicable from the pasted tips: "LTX-2.5 Fast" is a hosted API product with no published weights (we already run
the distilled model, 8 + 4 steps); the distilled pipeline already renders a smaller first stage and upscales it, and has
no documented switch to skip the second stage; ComfyUI and 3D-layout workflows do not apply; driver and cooling tips do
not apply on Modal; memory limits are already handled with a fallback.

Not chosen or not useful: two GPUs in parallel, a larger GPU, Modal memory snapshots, Sol Engine (see research).

## 5. Part C: test, after A and B are built

1. Offline tests and a local assembly check with saved clips (no GPU).
2. One batched GPU session, same keyframe, prompt and seed, 10 s scene: base, `natten`, S4, S5, S6; seconds, peak
   memory and clips side by side. The owner picks which to switch on.
3. One full learning video through the app with the accepted settings.

Budget: up to 45 minutes of L40S (about 1.5 USD) plus the story model. A change found by the test is fixed offline
first; a second full video needs the owner's yes.

## 6. Acceptance

1. Test video for 3 to 5: at least 110 spoken words (about 58 in run 4), voice at least 45% of the length (24% in
   run 4), no frozen scene ends.
2. Length within 10% of today's for the same scene count, and within 30 to 90 s.
3. Facts per band as in section 3, each from a card or marked as an AI draft; captions pass the existing rules.
4. Wait from confirm to ready, 5 scenes, cold video container (10.4 minutes in run 4): at most 7.5 minutes with B1
   alone (arithmetic gives about 7.3 before any decoder gain); aim 5 minutes with accepted B2 options. Measured once; the
   real number is reported whatever it is.
5. S4 to S6 are on only if the owner accepts the side-by-side clips.
6. Existing tests pass; stored v1 stories still load.

## 7. Risks

- The writer model may still fall short of the word minimum; after the retries the story is kept and the gap reported.
- More facts raise the chance of a wrong AI-drafted fact until cards are approved.
- Preparing during review costs GPU time when the adult leaves or rewrites (about 0.05 to 0.1 USD each time).
- The renderer peaks at 41 of 48 GB; `natten` or longer scenes may need the safe fallback.
