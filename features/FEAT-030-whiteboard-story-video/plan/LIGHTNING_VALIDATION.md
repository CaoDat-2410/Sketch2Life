# Lightning validation runbook (owner-operated, synthetic inputs only)

This is a validation procedure, not evidence of a successful model run. Use a synthetic/non-child source image and a reviewed `StoryVideoCreateRequestV1` JSON for an existing backend session. The backend's process-local artifact store must still contain the source image named by the package; restarting the backend loses that state.

## Provider media smoke before the full session workflow

From the repository root on the L4 studio, activate the same project Python environment in **both** terminals. Verify `which python` and `python -c 'import torch; print(torch.cuda.is_available())'` before starting; both terminals must use that interpreter. Then:

```bash
# Terminal 1: provider only; do not start the backend for this first media gate.
cd ~/Sketch2Life
export PORT=8001
export SKETCH2LIFE_STORY_MOTION_PROVIDER=whiteboard-stroke-v1
export SKETCH2LIFE_IMAGE_MODEL=stabilityai/stable-diffusion-xl-base-1.0
export SKETCH2LIFE_TTS_PROVIDER=edge_tts
export EDGE_TTS_VOICE=vi-VN-HoaiMyNeural
python tools/lightning_whiteboard_provider.py
```

```bash
# Terminal 2: inspect preflight before accepting any model/TTS work.
cd ~/Sketch2Life
python -m tools.create_story_video_media_fixture --output-dir /tmp/sketch2life-media-smoke-02
python tools/story_video_media_smoke.py --input /tmp/sketch2life-media-smoke-02/synthetic-house-story.json --preflight-only
# Only after review of preflight and image-model cost; this makes images, not TTS/video:
python tools/story_video_media_smoke.py --input /tmp/sketch2life-media-smoke-02/synthetic-house-story.json --preview-images --confirm-synthetic-only
# Inspect the reported scene images. If using SAM2, add/review draw_cues for each scene.
# Then accept TTS/render cost before the final media smoke:
python tools/story_video_media_smoke.py --input /tmp/sketch2life-media-smoke-02/synthetic-house-story.json --confirm-synthetic-only
```

`edge_tts` is an external network TTS path, not an offline voice model. Do not substitute real child speech/text for this synthetic test. If the fixture output directory already exists, inspect it and choose a new explicit directory instead of overwriting files. A successful import/preflight does not guarantee that the model weights are available or that the final video will look acceptable.

On the studio, after starting only the provider at `http://127.0.0.1:8001`, run `python -m tools.create_story_video_media_fixture --output-dir /tmp/sketch2life-media-smoke-02` from the repository root. Use a **new** directory; the previous `-01` fixture was the rejected monochrome/repeated first run and must not be overwritten. This creates a deterministic, non-child colored drawing with house/tree/sun/flower and a four-scene JSON **outside Git**. The JSON has `source_image` (path relative to the JSON), `locale` (`vi-VN`) and `scenes` (four objects with `text`, `visual_prompt` and a normalized `focus_box` selecting a different region of the same source image). You may instead supply your own synthetic PNG/JPEG/WebP and three to six reviewed test scenes. Each scene's narration must measure 5–20 seconds and the total 40–60 seconds. Do not use real child media, names, credentials or an unreviewed story in this fixture, and do not commit the fixture or output MP4.

Run `python tools/story_video_media_smoke.py --input /tmp/sketch2life-media-smoke-02/synthetic-house-story.json --preflight-only` first. After accepting image-model cost, use `--preview-images --confirm-synthetic-only` to see all generated scene image paths and a `contact_sheet_ref` in a new system-temp directory before TTS/video work. Open that sheet: it compares the source and every scene, with numbered orange boxes for reviewed `draw_cues`; inspect each full-resolution image too before drawing cue boxes. The sheet is only a visual review aid, not an automatic quality pass. Then run the same fixture with `--confirm-synthetic-only` alone after accepting TTS/render cost; it prints each media stage and the final MP4 path/hash. The example text is not guaranteed to measure 40–60 seconds for every TTS voice: if the duration guard stops after TTS, revise the synthetic text and rerun; the preview may already have generated images, but the changed text changes the media-only cache key. Consecutive nearly identical illustrations return `SCENE_VISUAL_DUPLICATE` before stroke rendering: inspect saved illustrations and revise prompt/crop/model settings, **do not blindly rerun**. This is a **provider-only media test**: it bypasses the backend, Director and Gate B, creates no `ApprovedStoryPackageV1`, and cannot be used as product acceptance. Inspect the MP4's line drawing, scene distinctness/continuity, source colors, voice, captions and duration. Record the model/voice/config and any failure locally before proceeding to the full workflow below.

Optional `draw_cues` in each synthetic scene can test narration-timed drawing. Supply one to four ordered objects, each with `element_id`, `label`, and a normalized `[left, top, right, bottom]` `focus_box` **relative to the generated scene illustration**, not the source-image crop. The media smoke divides that scene's measured TTS duration across those objects. For example: `"draw_cues": [{"element_id":"house","label":"Ngôi nhà","focus_box":[0.05,0.1,0.55,0.9]},{"element_id":"tree","label":"Cái cây","focus_box":[0.5,0.1,0.95,0.9]}]`. The generated fixture intentionally has no guessed cue boxes: first use `--preview-images --confirm-synthetic-only` to generate and inspect the saved illustrations, then add boxes only if their composition supports them. Preview does not call TTS or render MP4. Editing only cue boxes keeps the media-only image/TTS cache key stable, while each cue-layout clip and final assembled MP4 use content-dependent filenames so an earlier artifact is not overwritten. Editing source/text/visual prompts/focus crops or model/voice settings can still rerun inference. A cue with no nearby drawable strokes returns `DRAW_BEAT_EMPTY`; adjust the cue/image, not the READY status. These boxes are a spatial heuristic, not SAM object masks or proof of adult script authorization.

An optional `SKETCH2LIFE_STORY_SEGMENTER=sam2` on the **provider** changes cue assignment from box-centroid heuristics to SAM2 object masks. It is off by default. Install the [official SAM2 runtime](https://github.com/facebookresearch/sam2#installation) in that same provider environment and check `story_segmenter` in preflight; importability does not prove weights are already present. Before paying for TTS/image inference, explicitly run `python tools/verify_story_sam2.py --allow-model-download` on the L4 using that interpreter. This command may download the `facebook/sam2.1-hiera-small` checkpoint, then checks one synthetic mask inference; it makes no story image, TTS or MP4. Do not run it when using the default `bbox` segmenter. A successful synthetic inference does **not** prove mask quality on generated scenes. Every scene needs reviewed `draw_cues` before a SAM2 media smoke starts: the smoke command now rejects missing cues before TTS or image calls. If the generated illustration does not match a cue box, mask quality/overlap checks block the scene; do not mark it READY or rerun blindly. This is SAM2, whereas the external reference describes SAM3, and neither model guarantees hand-quality line art or accurate word-level pacing without visual review.

If TTS times out mid-request, do not blindly rerun. Inspect the private logs and costs first; a retry with the exact same request, voice and package hash can reuse completed WAV segments only when their cache manifests and file hashes still match. Changing the text or voice invalidates that reuse. `BLOCKED`/rejected TTS needs a configuration or input fix rather than the same retry.

## Full approved-session validation

1. Pull the reviewed commit on the studio. Confirm `nvidia-smi`, `ffmpeg -version`, `ffprobe -version`, TTS import, image model access and renderer imports. Provider preflight additionally encodes/decodes one temporary synthetic H.264 frame and checks FFmpeg's `subtitles` filter. It does not download or render an image model; a green result is still not proof of model access or video quality.
2. Start the provider with `PORT=8001`, `SKETCH2LIFE_STORY_MOTION_PROVIDER=whiteboard-stroke-v1`, a reviewed `SKETCH2LIFE_IMAGE_MODEL`, and a configured `SKETCH2LIFE_TTS_PROVIDER`. Run `python tools/lightning_whiteboard_provider.py` from the repository root with the project Python environment. Wan code/weights are not required for this default whiteboard profile.
3. Start the backend separately with `SKETCH2LIFE_ENV=local`, `SKETCH2LIFE_AI_PROVIDER=lightning_dev`, `SKETCH2LIFE_LIGHTNING_AI_BASE_URL=http://127.0.0.1:8001`, and `python -m uvicorn sketch2life.main:app --app-dir backend/src --port 8000` from the repository root. Keep credentials only in local secret files or the studio secret manager.
4. Submit the reviewed request using `python tools/story_video_demo.py --request /path/to/reviewed-story-request.json`. This tool does not upload an image, create a session, write a script, or fabricate approvals. The existing session must have passed Gate B, `package.session_version` must match its current version, and `package.source_image_ref` must identify its admitted image in the still-running backend process. Set `story_script_sha256` to `story_script_segments_hash(tuple(segments))` and `package_hash` to `stable_model_hash(package, exclude={"package_hash"})` after all other package fields are final. Do not use the removed all-zero-hash cat fixture.
5. Wait for `READY`, download the printed MP4 URL, and inspect: 40–60 seconds, all intended scene beats, identity/approved facts, stroke progression, TTS-subtitle sync, scene continuity, and absence of invented content. Record model/voice/config versions, GPU, input IDs/hashes and failure examples as feature-local evidence. A status code 200 from scene rendering alone is not acceptance.

If preflight fails, stop before job creation. If render/assembly fails, retain typed job status and private logs; do not relabel the job READY. Any real child media, paid repeated inference or production rollout needs its own authorization and privacy review.
