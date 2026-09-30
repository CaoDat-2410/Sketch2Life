# Android responsiveness comparison — 2026-09-30

Evidence ID: `FEAT033-EV-20260930-24`
Acceptance criterion: AC-09

## Environment and method

- Dedicated test AVD: `Pixel_10_2`, Android API 37.1 / Android 17, x86_64, 4 vCPUs, 2 GB RAM.
- Baseline source: clean managed worktree at `2d530e7` (before the FEAT-033 working-tree changes).
- Current source: FEAT-033 implementation from the task working tree, whose HEAD is also `2d530e7`; it was served by the main Metro on port 8081. The baseline bundle was served from its isolated checkout on port 8082 after installing dependencies from the frozen lockfile.
- Input exercise: 24 synthetic single-character edits separated by 140 ms. Only timing aggregates were retained; no synthetic text was saved.
- Input measure: development-only JavaScript `onChangeText` callback to the next `requestAnimationFrame`, summarized as p95 per run. This is a responsiveness proxy, not native input-event-to-presented-pixel latency.
- Scroll exercise: four repeated swipe gestures per capture; Android `dumpsys gfxinfo` frame summaries were collected. Screen content and list structure were not identical between revisions.

## Results

| Measure | Baseline | Current | Interpretation |
|---|---:|---:|---|
| Input proxy, run 1 p95 | 153.55 ms | 23.91 ms | Lower current callback-to-next-frame time |
| Input proxy, run 2 p95 | 161.58 ms | 23.52 ms | Same direction on repeat |
| Median of the two run-level p95 values | 157.57 ms | 23.72 ms | About 85% lower; not a native latency claim |
| Scroll frame p95, capture 1 | 25 ms | 32 ms | Current capture is higher |
| Scroll frame p95, capture 2 | 22 ms | 32 ms | Current capture is higher |
| Scroll janky frames, capture 1 | 10/193 (5.18%) | 14/193 (7.25%) | Mixed-device/frame sampling; screens differ |
| Scroll janky frames, capture 2 | 8/182 (4.40%) | 11/187 (5.88%) | Follow-up signal, not causal proof |

The baseline input was the existing material-search field; the current input was the new stable-
interest free-text field. Therefore the pair is useful for a coarse interaction comparison but is
not a like-for-like component benchmark. Source inspection confirms typing only updates bounded
draft state/revision and development timing samples; the classifier API is called from the explicit
submit button, not from `onChangeText`. The mobile regression script checks the one-attempt-per-text-
revision gate. No classifier submit was made during these timing samples.

For scroll captures, the system reported no missed-vsync or slow-UI-thread frames in the sampled
windows. Slow draw-command counters were higher in current captures (11/13 versus 7/10 baseline);
given the different UI content and short captures, this cannot establish an application regression,
but it should not be hidden as a clean scroll pass.

## Cold mount and limits

The baseline profile mount took 2,887.9 ms from the dashboard tap until the accessibility tree
contained the profile title. This is a tap-to-accessibility-dump upper-bound proxy, not a direct
render-present timestamp. A matching current attempt was discarded: the test AVD returned to the
system launcher instead of reaching the expected profile screen, and `gfxinfo` contained no rendered
frames. No current cold-mount number is reported.

The remote classifier endpoint was unavailable (HTTP 503 in a separate single synthetic probe), so
classification wait and the complete recommendation flow could not be timed. The main emulator
`emulator-5554` was not interacted with. After the test, the dedicated AVD was shut down and its
baseline Metro server on port 8082 was stopped; only `emulator-5554` remained online. Main backend
health and Metro `/status` both returned HTTP 200.

## Decision

The input proxy is an encouraging improvement, but AC-09 is **not closed**: the field comparison is
not equivalent, native event-correlated input-to-pixel evidence is unavailable, current cold mount
was not captured, scroll p95 warrants review, and remote classification latency remains unmeasured.
Keep the criterion open until the agreed device can provide a comparable event-correlated trace and
the scroll difference is either explained or corrected.
