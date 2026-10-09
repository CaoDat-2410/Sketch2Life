# FEAT-030 — narrated whiteboard story video

This feature extends the existing session-local 5–10 second whiteboard learning clip with a separate 40–60 second, multi-scene story-video path. It does not replace Pixi exploration or the original source drawing. The source of approved facts, anchors and narration remains `ApprovedStoryPackageV1`; visual generation cannot be treated as factual authority.

Owner reference: `yogendra-yatnalkar/storyboard-ai` (scene-based narrated whiteboard style). This reference expresses visual intent, not proof that the current renderer has the same hand-drawing quality. Master SRS v1.4 remains the authority for original-image identity, safety, provenance and READY gating.

Additional owner reference: `Atharva-Kanherkar/chalkboard` (MIT-licensed vector/diagram whiteboard renderer). Its cached RoughJS path reveal informs the opt-in vector pilot; its image/SVG fade behavior means it is not a drop-in raster child-art animator. The video-first, adult-reviewed product flow above remains authoritative.

Implementation is local/backend and provider-adapter code. No Lightning GPU, paid model inference, real child data or production deployment is exercised by this feature record.
