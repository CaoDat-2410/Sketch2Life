# Decisions

- Default story-video motion profile is deterministic whiteboard stroke drawing. Wan 2.2 is optional and must be selected explicitly; an L4 is not required to draw the default scene clip, but image generation still needs a configured model/runtime.
- A raster illustration is converted to ordered local edge paths. This makes progressive line drawing possible, but cannot reconstruct a human artist's actual pen trajectory.
- The scene compiler uses approved, ordered script segments and measured TTS timing. It does not infer educational facts from a picture or promise continuity that has not been checked.
- The original 5–10 second learning micro-video remains separate from the 40–60 second narrated storyboard output, matching the SRS boundary without silently changing the former duration target.
- Final MP4 download is exposed through a session/job route only for READY jobs. Derived artifacts remain server-local in this implementation.
- Director grouping uses measured TTS segment lengths to choose three to six scenes of 5–20 seconds, preferring approximately 10-second beats and avoiding mixed scene purposes. It never splits an approved segment or invents facts/anchors.
- The old cat demo fabricated zero hashes and an approval marker, so it was replaced by a submitter requiring an existing reviewed request JSON and session source artifact. This is a safety gate, not proof that a supplied approval is authentic.
- A local synthetic 40-second run verified muxing and timings. Visual inspection showed a small stylized hand and only raster-derived ink, not reference-level human-drawn quality; real-model visual acceptance remains open.
