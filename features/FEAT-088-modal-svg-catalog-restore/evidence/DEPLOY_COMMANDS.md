# Deploy the three current Modal AI apps

Run these commands in PowerShell from the active worktree. They deploy the current source files to profile `hieuptse184252`, environment `dev`.

```powershell
Set-Location '<LOCAL_ROOT>\.codex-worktrees\fe'

& '<LOCAL_ROOT>\.venv-modal\Scripts\modal.exe' deploy --profile hieuptse184252 --env dev deployment/modal/srs_v23/drawing_vlm_app.py
& '<LOCAL_ROOT>\.venv-modal\Scripts\modal.exe' deploy --profile hieuptse184252 --env dev deployment/modal/srs_v23/language_audio_app.py
& '<LOCAL_ROOT>\.venv-modal\Scripts\modal.exe' deploy --profile hieuptse184252 --env dev deployment/modal/srs_v23/video_app.py
```

The deployed app names in this source are:

- `sketch2life-srs23-drawing-vlm-dev` — Qwen3.8 drawing/image analysis.
- `sketch2life-srs23-language-audio-dev` — Qwen3.8 language, Whisper transcription, and VieNeu narration.
- `sketch2life-srs23-dev-video` — LTX-2.5 video generation.

These commands were prepared but not run. The restored Openclipart catalog Volume is `sketch2life-openclipart-catalog-dev`. The current `language_audio_app.py` does not mount or query that Volume, so deploying these three files alone will not enable catalog-backed SVG guide generation. That requires a separate Qwen3.8 integration change.
