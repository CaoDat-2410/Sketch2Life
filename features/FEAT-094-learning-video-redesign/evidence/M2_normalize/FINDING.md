# Every scene failed its own check after the workspace move (2026-11-26)

- **Symptom:** app run, video generation failed with `VIDEO_SCENE_RENDER_FAILED`; both attempts of scene 1 failed in the
  worker at `scene_media_validation` with `VIDEO_SCENE_PROFILE_INVALID`.
- **Root cause:** the inference image built in workspace `siesta-6107` installs ffmpeg 7.1.5 (Debian 13). After the
  `setpts` filter it no longer keeps the frame rate, and without an output `-r` it writes **25 fps**: 144 frames became
  5.76 s instead of 6 s. The image installs ffmpeg and resolves the LTX dependencies without pins, so a rebuild can
  change behaviour.
- **Reproduced** on the deployed image, CPU only (`check_normalize.py`): 6 of 6 durations `VIDEO_SCENE_PROFILE_INVALID`.
- **Fix:** name the output rate (`-r 24`) in the scene normalisation and in the silent-story assembly.
- **After:** the same check gives 6 of 6 `VALID` at 24 fps with exact durations. `check_assembler.py` also passes the
  backend assembler and validator (ffmpeg 7.1.5 in the API image) for 5, 7 and 9 scenes.
- **Open:** the images are still not pinned. The new `ltx_speed.py` is mounted as the last layer so that this deploy
  did not rebuild the dependency layers.
