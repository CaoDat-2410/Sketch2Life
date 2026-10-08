# Decisions

- Default story-video motion profile is deterministic whiteboard stroke drawing. Wan 2.2 is optional and must be selected explicitly; an L4 is not required to draw the default scene clip, but image generation still needs a configured model/runtime.
- A raster illustration is converted to ordered local edge paths. This makes progressive line drawing possible, but cannot reconstruct a human artist's actual pen trajectory.
- The scene compiler uses approved, ordered script segments and measured TTS timing. It does not infer educational facts from a picture or promise continuity that has not been checked.
- The original 5–10 second learning micro-video remains separate from the 40–60 second narrated storyboard output, matching the SRS boundary without silently changing the former duration target.
- Final MP4 download is exposed through a session/job route only for READY jobs. Derived artifacts remain server-local in this implementation.
