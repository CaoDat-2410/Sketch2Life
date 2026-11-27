# Phase 0 app verification run (2026-11-26)

Synthetic chick drawing ("Các loài chim"), child age 48 months, Parent app on the emulator, dev backend, Modal
`siesta-6107/dev`. Second attempt, after the frame-rate fix and with the `fast` speed profile and the motion-only prompt
deployed (commit `0d2dd603`).

## Result

`READY`; the video plays in the app. Files: `contact_sheet.png`, `captions.vtt` (the MP4 stays local).

| Check | Result |
|---|---|
| Video stream | H.264, 1280x720, 24 fps, 720 frames, 30.0 s |
| Audio | AAC 48 kHz, mean -22.3 dB, max -1.2 dB |
| White bands | none |
| People or animals that were not drawn | none in the 25 sampled frames |
| Speed profile | `fast` for the whole run, no out-of-memory fall-back |

## Timing

| Stage | Time |
|---|---|
| Job accepted to `READY` | 9 min 26 s |
| Video planning on a cold Qwen | 228 s |
| Renderer warm-up (checkpoint read and decoder compile) | 125 s, overlapping planning |
| Prompt priming | 10 s |
| Each 6 s scene | 45 to 50 s (about 115 s in the earlier live run) |
| Queued to last scene rendered | about 5 min after planning |

The earlier live run (FEAT-093, bicycle, warm containers) took about 14 minutes for the same length.

## Defects seen (author's reading of sampled frames; the owner has not judged the video)

1. The chick is mirrored in the scenes: the drawing faces right, the video shows it facing left.
2. Scenes 1 and 5 zoom in although the prompt asks for a static camera.
3. Scene 2: the chick walks out of the frame by the end.
4. Scene 3: the chick hangs in front of the tree trunk, above any ground.
5. White paper gaps inside the cut-out remain.
6. Captions are five very short lines that teach nothing (phase 4).
7. The narrated lines differ from the story the Parent confirmed (phase 4).

## Not covered

The truncated confirm button was not reproduced: the run resumed after the understanding step.
