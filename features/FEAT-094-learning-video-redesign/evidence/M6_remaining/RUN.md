# Remaining items of phases 0 to 5 (2026-11-27)

Dev workspace `siesta-6107/dev`, code not committed. Synthetic data only.

## Changes and what checked them

| Item | Change | Offline check |
|---|---|---|
| White page edge | the painted plate is zoomed 6% when one side shows a pale margin | unit tests; applied to the five frames of run 2, the margin disappears |
| Hand entering a scene | local measure on every frame: a border block that differs from the first frame (level 40 for 6 frames) reports `EDGE_CHANGED` | on the ten saved scenes it reports exactly the two with a hand (levels 98 and 111, clean scenes at most 23) |
| Model check | sheet of six frames instead of four; the question names hands, smears and normal poses | unit tests |
| Bad background | Qwen compares the composed first frame with the drawing; a rejected background is painted once more before rendering (waits at most 90 s) | unit tests |
| Wing smear | fast actions (flap, jump, spin, shake) are asked for again | unit tests |
| Silence | script asked for max-4 to max words (14 to 18 at 3 to 5 years); 0.8 s pause between sentences | unit tests |
| Contact shadow | soft ellipse under a standing subject | unit tests |
| Part labels (D1) | part name top left from 0.4 s to 4.4 s, no arrows (no part positions) | unit tests; Vietnamese text drawn by the real ffmpeg |
| Second suggestion set after a reload | the app asks with `reuse_latest`; the server returns the finished set or answers "in progress" | unit tests; the new query runs on the dev database |
| Image drift | serving Qwen image installs a 197-package lock; video image refuses another ffmpeg series | unit tests; both apps deployed |
| Knowledge cards | every card names the pages it was compared with, still `DRAFT` | `CARD_SOURCE_REVIEW.md` |

Calibration of the edge measure used only ten scenes of one drawing; its false-positive rate on other drawings is not
known. The visual check stays in `report` mode.

## Not built, and why

- **Removing paper-coloured gaps inside the cut-out:** in the test drawing the white streaks are part of the child's
  colouring; removing them would punch holes into the drawing.
- **Early keyframes (S7):** needs a preparation job before a video exists; preparation is about 15 s to 111 s and the
  warm-up at story review already covers the container start.
- **E5, E6, S8, S9:** conditional items; the waiting time is inside the target. S9 needs a separate approval.
- **30-drawing evaluation (phase 6):** deferred by the owner.

## Tests

- Modal worker tests: 495 passed, 5 skipped.
- App: 308 passed, 5 failed (failures in `parentSrsBehavior`, present before this work); type check clean.
- Backend unit and contract tests: failures compared with the committed code; one FEAT-050 source-count test fails on
  untouched files, the others fail on the committed code too or come from routes committed earlier.

## Live run 3 (outside the app, synthetic chick, 48 months)

- Story: 227 s with a cold Qwen on the pinned image; lines of 10 to 13 words although 14 to 18 were asked
  (`story_run3.txt`).
- Video: 698 s for 50 s (preparation 94 s, first-frame checks 67 s, first scene with renderer load 174 s, other scenes
  about 87 s). Five AI backgrounds, no repaint.
- Findings of the local edge measure: scenes 1, 2, 5. The Qwen check answered "no problem" ten times out of ten.
- Seen in sampled frames (`contact_sheet_run3.png`): the part label "Mỏ" and the ground shadow show; scene 2 has a
  **large realistic hen** painted behind the child's chick (the setting named the chicken); the bushes of scene 1 smear;
  a ragged white page edge remains in scenes 1, 3, 5; scene 5 sways slightly (measured 45, counted as an edge change).

Changes after run 3: settings naming an animal are rewritten by the worker and removed by the backend; every background
plate is zoomed 6%; the edge level is 60 (hands 98 and 111, other real defects 75 and 82, clean at most 23, sway 45);
the first-frame question names a second animal of the same kind; first frames are checked while later ones are
prepared; sentence length is asked per sentence.

## Live run 4 (after those changes, same synthetic input)

| | Run 3 | Run 4 |
|---|---|---|
| Story, Qwen cold after a redeploy | 227 s | 257 s |
| Video, video container cold | 698 s | **623 s** |
| Preparation | 94 s | 81 s |
| Waiting for first-frame checks | 67 s | 20 s |
| First scene, renderer load included | 174 s | 164 s |
| Other scenes | 87 to 97 s | 87 to 93 s |
| Findings | scenes 1, 2, 5 | scene 3 |

Seen in sampled frames (`contact_sheet_run4.png`, `learning_run4.mp4`; the owner has not judged it): no page edge, no
extra animal or hand, the chick stays whole, pecking and eye closing read well, the label "Mỏ" shows. Still wrong:
scene 3 pans, the tree trunks and objects behind the chick slide (reported by the edge measure). Lines are still 11 to 13
words (14 to 18 asked), so more than half of each scene has no voice.

## The deployed checks on earlier material (`check_saved_scenes.py`, `saved_scenes_result.txt`)

- Ten scenes of runs 1 and 2: both hands reported by the edge measure and by Qwen (`NEW_CHARACTER`); nothing reported
  on the other eight, the pecking scene that was a false positive before included. The smear of run 2 scene 3 is still
  missed.
- Five first frames of run 3 against the drawing: only scene 2, the painted second hen, is rejected.

These are fifteen scenes of one drawing: they do not give a false-positive rate for other drawings.

## Tests after the last change

- Modal worker tests: 497 passed, 5 skipped. Video backend tests of the changed modules pass.

## Not verified

- The new Parent screens, the warm-up at story review, the reload fix and the learning flow **through the app**: the
  emulator app lost its session during the code changes and waits for a new sign-in.
