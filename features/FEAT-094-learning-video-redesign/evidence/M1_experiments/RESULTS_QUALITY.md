# Phase 1: LTX-2.5 quality experiments E1-E3 (2026-11-26)

Ten 10 second scenes on one L40S with the `decode` speed profile, two synthetic drawings (a bicycle keyframe over an
AI background taken from the FEAT-093 live video, and a chick on paper), one seed per drawing. Judged by the author from
six frames per video (`quality/sheet_bike.png`, `quality/sheet_chick.png`); **one seed per variant**, so these are
indications, not measurements. The owner has not judged the videos yet.

## E1: prompt

| | Old wrapper prompt | New motion-only prompt |
|---|---|---|
| Bicycle | the camera zooms in until the bicycle leaves the frame | scale kept; the background still slides as if the camera followed the bicycle, and the tree passes **in front of** it |
| Chick | **a second comb-like object appears** on the grass | the chick pecks and rises; no new object; strokes kept |

The new prompt is better on both drawings. It does not by itself keep the background still when the action moves the
subject sideways.

## E2: end frame guide (chick)

With strength 0.7 and 0.9 the chick arrives at the end pose the system composed. No visible difference between the two
strengths. A flaw of the test input (a gap left in the grass where the legs were cut out) is reproduced faithfully, so
the end frame must be composed cleanly.

## E3: input compression (CRF 0, 18, 33)

No clear gain from changing it. 18, the checkpoint default, stays.

## Seen besides the questions

- Paper residue between the wheel spokes of the bicycle keyframe is kept by the model: the mask cleanup of phase 5 is
  needed.
- The speed profile output matches the baseline output for the same seed by eye.

## Proposed configuration

New motion-only prompt, end frame guide at 0.7, CRF default. Still to test (phase 5): end frame for a subject that
moves across a background; E5 (stage 1 resolution) and E6 (`DFRPipeline`) were not run.
