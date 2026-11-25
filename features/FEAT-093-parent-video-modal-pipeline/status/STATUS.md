# FEAT-093 status

**State:** APPROVED (offline backend pipeline built; live path and app not done)

Previous state line: APPROVED (Rev 2 + Amendment A + Amendment B, 2026-11-25). M0 partly done; M1 and M2 implemented (not yet live-checked).

| Milestone | Status | Notes |
|---|---|---|
| M0 spikes and freeze | partly done | LTX spike (488 s for 5 x 6 s) and SRS reconciliation done. C2 memory/swap cost, Qwen decoding profile and Modal GPU concurrency are measured when C2 is built (M3-M5). |
| M1 recognition v2 backend | implemented | Analyzer result carries main/secondary subjects with boxes; stored with entity ids; `subject_role_scoring.propose_roles`; client view adds `suggested_included` and `needs_choice`; 14 unit tests. Eval set R6 (30 drawings) not built yet. |
| M2 recognition UI | implemented | `UnderstandingScreen` choice card and gate, scenery starts off, controller state; 4 vitest tests. Emulator run U1-U3 pending. Crop thumbnails are not done (boxes are not sent to the client by design); decision needed if wanted. |
| M3-M5 backend pipeline (offline) | implemented | Pure domain (age profile, timeline, captions, narration QC, plan, staging builder), orchestrator (two containers, pipelining), C1 scene renderer adapter, C2 scene-preparation core (`scene_prepare.py`, plate QC, paper fallback) and adapter, narration clause function `synthesize-narration-clause` (source only) and adapter, ffmpeg assembler, technical validator, `PipelineVideoRenderer` behind `VideoRenderPort`. About 100 offline tests, all with fakes. ffmpeg added to the API image. |
| Open before M10 (live) | not started | (1) Modal function `prepare-video-scene` (FLUX plate + SAM + `scene_prepare`), needs the gated FLUX model deployed and a combined image; (2) SQL `VideoSourceReaderPort` (story, subjects/boxes, activity, drawing) and the video worker process plus job progress columns; (3) vision-based consistency and safety checks (validator reports `VIDEO_VISION_CHECKS_PENDING`); (4) `story_video_adapters` composition for the real renderer and retiring the candidate path; (5) app: VideoScreen stages and ETA, waiting-time checklist, status chip and badge, captions overlay, local notifications, UI scripts U1-U22; (6) deploy `language_audio_app` and the video app, then the M10 run. |

GPU budget used: 1 video (5 scene renders) of 12 videos / 40 scene renders.

Live runs since the LTX spike: 1 drawing analysis dispatched on 2026-11-25 for the M2 UI check and then abandoned at the owner's request (credit saving); no further live runs until the offline work is done.
