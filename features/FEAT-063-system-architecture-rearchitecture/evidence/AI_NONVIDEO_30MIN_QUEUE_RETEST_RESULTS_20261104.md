# Non-video AI Modal queue retest with a 30-minute wait

**Status:** Partial; retest complete  
**Date:** 2026-11-04, Asia/Saigon  
**Approved plan:** [AI_NONVIDEO_30MIN_QUEUE_RETEST_20261104.md](../plan/AI_NONVIDEO_30MIN_QUEUE_RETEST_20261104.md)  
**Wait bound:** 1,800 seconds per Modal result call. Worker execution timeouts, model pins, and GPU type were unchanged.

## Scope

This was a direct Modal worker test using synthetic drawing and lesson fixtures. It did not retest Parent or Teacher HTTP APIs. Video generation and composition were not called. TTS and ASR were not repeated because they succeeded in the preceding retest. Lesson-plan suggestion remained undispatched under the existing SRS role restriction. Unknown calls were not retried.

## Results

| Workload | Result | Timing and evidence |
|---|---|---|
| drawing.analyze | UNKNOWN_NO_RETRY; no model output. The call was later verified terminal after its app was stopped. | 1,800-second wait bound; call fc-01M6KA82Q2EVRV25A2ARYN1NCV. |
| story.generate / storyboard.generate | UNKNOWN_NO_RETRY; no story output. The call was later verified terminal after its app was stopped. | 1,800-second wait bound; call fc-01M6KBZ7PDXR2NS0PR9R6X1TW1. |
| parent.sketch-guide.generate | SUCCEEDED. Contract checks passed; output is a single synthetic PNG, 768 x 512, 158,296 bytes, SHA-256 388647b52af176c78a833c29319942e92e2757bf0cda5637823a707057eaf618. Step ordering, child usability, safety, and product readiness were not evaluated. | Dispatch 20:58:48, result 20:59:24; 36 seconds. Call fc-01M6KDPA6MM13ESNFWR6CGHVSR. Image: assets/ai_nonvideo_30min_queue_retest_20261104/parent_sketch_guide.png. |
| teacher.sketch-deck.generate | SUCCEEDED after redeploy. Validated 5-slide, 16:9 Vietnamese DRAFT with 4 drawing steps and exactly 2 approved activities. | Dispatch 21:04:49, result 21:22:11; 17 minutes 22 seconds. Call fc-01M6KE1AJDA80F20YD1AP3F0YH. |
| lesson.visual.generate | UNKNOWN_NO_RETRY; no image output. Modal call was verified terminal after stopping FLUX. | 1,800-second wait bound; call fc-01M6KDQHE03VDSWXNDPSZ9MJFZ. |
| drawing.segment (SAM2.1 Hiera-Small) | Checkpoint was already present and its pinned SHA-256 was verified. Segmentation timed out before inference; no mask was created. Modal logs explicitly showed the function waiting to be scheduled on GPU_L4. | Checkpoint check: 3.11 seconds. Inference wait: 1,800 seconds, 21:29:36 to 21:59:38. The timeout runner cancelled the call; its exception path did not persist the Modal call ID. The Modal function ID and the limitation are recorded in sam2_segment_result.json. |

The first Teacher Deck attempt at 20:59:25 failed with NotFoundError before dispatch because the prior app deployment had already been stopped. It did not run inference. The language app was redeployed, and the fresh call above was issued once with new job, generation, and attempt IDs.

## Conclusion

The longer wait helped two GPU-backed workloads complete: Parent Sketch Guide returned in 36 seconds, and Teacher Sketch Deck received capacity and completed after 17 minutes 22 seconds. It did not secure a GPU within 30 minutes for drawing analysis, story generation, lesson visuals, or SAM2. Modal logs explicitly showed GPU_L4 scheduling waits for Teacher Deck and SAM2; the other timed-out calls returned no output by the 30-minute client bound. These timeouts are capacity outcomes, not evidence that the model inference itself failed.

There were 2 successful inference outputs, 4 capacity timeouts with no output, and 1 Teacher pre-dispatch NotFound event. No request was retried after an unknown outcome. No video inference occurred and all product workloads remain disabled.

## Shutdown

All Modal dev apps were stopped and verified with zero tasks at 22:00:30 Asia/Saigon. Shared Modal Volumes were retained. No commit or push was performed.

The run summary, dispatch intents, per-workload results, and generated image are in assets/ai_nonvideo_30min_queue_retest_20261104/.
