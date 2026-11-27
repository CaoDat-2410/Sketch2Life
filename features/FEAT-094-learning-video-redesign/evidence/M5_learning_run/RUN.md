# Phases 4 and 5: first live learning videos (2026-11-26 UTC)

Dev workspace `siesta-6107/dev`, code not committed. Synthetic data only: subject "con gà", age 48 months, interest tags
`nature`, `animals`; drawing and boxes of the earlier synthetic chick run. Run inside the video worker container with
`check_story.py` and `check_video.py` (no business state written, MP4 files stay local). The video worker's Parent app
path and the app screens were **not** exercised.

## Story worker

| Attempt | Time | Result |
|---|---|---|
| 1 (cold Qwen) | 454 s, of which writing 25 s and model load 192 s | passed all gates; short lines (8 to 9 words) |
| 2 and 3 (warm) | 27 s | passed all gates |
| 4 (cold, after the short-line rewrite rule) | 258 s | passed all gates; 11 to 12 words per scene, recap in the last scene (`story_run2.txt`) |

All facts were model drafts (`AI_DRAFT`): no knowledge card is approved.

## Videos (5 scenes of 10 s, 1280x720, 24 fps, 50.0 s)

| | Run 1 (`contact_sheet_run1.png`) | Run 2 (`contact_sheet_run2.png`) |
|---|---|---|
| Total | 618 s | 667 s |
| Preparation, video container cold | 100 s | 111 s |
| First scene, renderer load included | 163 s | 196 s |
| Other scenes | 84 to 92 s | 85 to 95 s |
| Video planning | none (confirmed script used) | none |
| Backgrounds | photographs; dogs in scene 5; a hand in scene 4 | crayon; no animals |
| Visual check (report mode) | scene 4 `NEW_CHARACTER` (the hand: correct) | scene 2 `SUBJECT_CHANGED` (the chick pecks: looks like a false positive) |

Run 1 showed that a learning script's setting needs an explicit style. After run 2 the style text was changed once more
("full-frame", no "paper"); **that last change has not been rendered**.

## Seen in sampled frames (the owner has not judged the videos)

Better than before: the chick is not mirrored, stays in frame and on the ground, the camera holds still, pecking and
eye closing read well.

Still wrong in run 2:

1. Scene 3: the flapping wing turns into a blue smear. The visual check did not report it.
2. Scene 5: a hand appears at the bottom edge in one sampled frame. The check, which looks at three moments, missed it.
3. Backgrounds had a white page edge.
4. White paper gaps inside the cut-out.
5. Narration still leaves about 5 s of each 10 s scene without voice.
