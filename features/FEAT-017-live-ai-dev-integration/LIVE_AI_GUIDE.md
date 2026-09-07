# FEAT-017 live AI connection guide

This guide connects the existing React Native fixture UI to a live Lightning development endpoint through the Sketch2Life backend. The first live slice is P2 ASR/VLM understanding only. P1 selection, P3 original-art playback, P4 learning media and activity handoff continue to use the approved fixture contracts, so Gate A remains visible and mandatory.

The Lightning endpoint is a custom HTTPS service running in a Lightning Studio or deployment. Lightning documents Studio/deployment inference workflows and public web app exposure here:

- https://lightning.ai/docs/platform/inference/inference-overview
- https://api.lightning.ai/docs/platform/build/ai-studio/deploy-a-studio
- https://lightning.ai/docs/overview/host-web-apps/expose-web-apps

## 1. What is already complete

Before connecting live AI, the repository already passes:

- FEAT-015/016 Python regression: 32 tests.
- FEAT-017 live adapter/route tests: 5 tests.
- Mobile Jest: 7 tests.
- Mobile typecheck and lint.
- Harness, architecture, repository security, and Metro Android bundle composition.

The live route is `POST http://127.0.0.1:8000/v1/live-understanding`. It accepts only `integration-fixture-v1`, verifies the fixture manifest and source hashes, calls the two backend-only provider paths, maps both outputs to `AsrResultV1` and `VisionUnderstandingResultV1`, and returns `gate_a_required: true`.

## 2. Lightning endpoint contract

Expose these two POST paths from your Lightning Studio/deployment. The backend sends JSON with the media bytes encoded as base64. The backend never sends a token or provider URL to the mobile app.

`POST /v1/asr` request shape:

```json
{
  "contract_name": "AsrRequestV1",
  "contract_version": "1.0",
  "model_profile": "live-p2-understanding-v1",
  "source_audio": {
    "artifact_ref": "child-narration-001",
    "sha256": "<64 lowercase hex characters>",
    "content_base64": "<fixture WAV bytes>"
  }
}
```

Return only the structured fields below. Do not return prompts, raw SDK objects, hidden chain-of-thought, credentials, or logs in the response:

```json
{
  "transcript": "butterfly",
  "language": "en",
  "language_confidence": 0.95,
  "segments": [
    {"start_seconds": 0, "end_seconds": 1.2, "text": "butterfly", "confidence": 0.9}
  ],
  "quality": {
    "no_speech_probability": 0.02,
    "average_log_probability": -0.15,
    "segment_count": 1
  }
}
```

`POST /v1/vision` uses the same envelope with `source_image`, `response_schema_version: "VisionUnderstandingResultV1"`, and `content_base64`. Return this shape:

```json
{
  "entities": [{"label": "butterfly", "confidence": 0.94}],
  "actions": [{"label": "fly", "confidence": 0.81}],
  "relations": [],
  "themes": [],
  "ambiguous_regions": [],
  "uncertainty": 0.06
}
```

The provider service may use Whisper/faster-whisper and a vision model internally, but that choice stays inside Lightning. The backend contract is the stable boundary.

## 3. Configure the backend safely

Create a token file outside Git. On PowerShell:

```powershell
$secretRoot = Join-Path $env:USERPROFILE ".sketch2life\secrets"
New-Item -ItemType Directory -Force $secretRoot | Out-Null
notepad (Join-Path $secretRoot "lightning.token")
```

Paste only the development token, save, and close Notepad. Do not put it in `.env`, the notebook, mobile code, screenshots, or Git.

In the same PowerShell window, configure the backend. Replace the base URL with the HTTPS URL of the Lightning Studio/deployment that exposes `/v1/asr` and `/v1/vision`:

```powershell
$repoRoot = (Get-Location).Path
$env:SKETCH2LIFE_ENV = "local"
$env:SKETCH2LIFE_AI_PROVIDER = "lightning_dev"
$env:SKETCH2LIFE_LIGHTNING_AI_BASE_URL = "https://YOUR-LIGHTNING-URL"
$env:SKETCH2LIFE_LIGHTNING_AI_TOKEN_FILE = Join-Path $secretRoot "lightning.token"
$env:SKETCH2LIFE_LIGHTNING_MODEL_PROFILE = "live-p2-understanding-v1"
$env:SKETCH2LIFE_LIVE_FIXTURE_ROOT = "$repoRoot\features\FEAT-015-integration-readiness-review\fixtures\integration-fixture-v1"
```

Check that the token file is readable without printing its contents:

```powershell
Test-Path $env:SKETCH2LIFE_LIGHTNING_AI_TOKEN_FILE
(Get-Item $env:SKETCH2LIFE_LIGHTNING_AI_TOKEN_FILE).Length
```

Start the backend from a second PowerShell window with the same environment variables:

```powershell
$repoRoot = (Get-Location).Path
Set-Location "$repoRoot\backend"
$env:PYTHONPATH = "$repoRoot\backend\src"
.\.venv\Scripts\python.exe -m uvicorn sketch2life.main:app --host 0.0.0.0 --port 8000
```

Confirm the process is up:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## 4. Run the notebook or smoke script

Open [live_ai_smoke_test.ipynb](notebooks/live_ai_smoke_test.ipynb) in Jupyter, VS Code, or Lightning Studio. Run the cells in order. The notebook:

1. verifies the fixture is synthetic and its image/audio hashes match;
2. checks that the backend is reachable;
3. submits `integration-fixture-v1` to the backend;
4. prints only status, proposal label, contract versions, provenance and latency;
5. asserts `gate_a_required` and source-hash preservation;
6. exercises the normal failure path with an unavailable backend URL without printing secrets.

Equivalent direct smoke test:

```powershell
Set-Location $repoRoot
backend\.venv\Scripts\python.exe tools\live_ai_smoke.py --base-url http://127.0.0.1:8000
```

The smoke test will fail closed if the backend is disabled, the fixture root is not configured, a hash changes, a provider response is malformed, or Gate A is missing.

## 5. Test the UI on Android

The default debug backend address is `http://10.0.2.2:8000`, which maps the Android emulator to the host machine. Keep the backend bound to `0.0.0.0:8000` as shown above.

From the repository root:

```powershell
pnpm --dir apps/mobile start
```

In another window with an Android emulator available:

```powershell
pnpm --dir apps/mobile android
```

On the first screen:

1. Tap **Try live backend (synthetic fixture)**.
2. Wait for the backend proposal. The next screen is **Gate A**.
3. Confirm the meaning. The app advances to P1/Gate B.
4. Approve the canonical activity/objective pair.
5. Play the original drawing reveal.
6. Start the activity and submit feedback.

If you use a physical Android device, replace the debug backend address in `apps/mobile/src/features/fixture/FixtureFlowScreen.tsx` with the host computer's LAN address, keep the backend on the same network, and use a development-only HTTP exception. Never use a provider URL or token in that file.

## 6. Expected live response and evidence

A successful smoke run has:

- `status: PROPOSAL`;
- `gate_a_required: true`;
- `asr.status: SUCCEEDED` and `vision.status: SUCCEEDED`;
- provider provenance with `provider: lightning` and the configured model profile;
- source hashes equal to the checked-in synthetic fixture manifest.

Record only sanitized metadata in `features/FEAT-017-live-ai-dev-integration/evidence/`: timestamp, fixture hash, request ID, model/config profile, status, latency, and failure category. Do not store raw media, prompts, provider payloads, Authorization headers, signed URLs, or token material.

## 7. Troubleshooting

- **503 live mode is disabled:** the backend process does not have `SKETCH2LIFE_AI_PROVIDER=lightning_dev`.
- **503 runtime settings are incomplete:** check the base URL, token-file path, and fixture-root path in the same shell that launched Uvicorn.
- **Provider error or timeout:** call the Lightning `/health` endpoint if your deployment has one, then verify `/v1/asr` and `/v1/vision` return the exact JSON shapes above. The backend retries once and returns a typed failure.
- **Malformed output:** inspect the provider server's structured response schema. Do not loosen backend validation to accept free-form output.
- **Android cannot connect:** emulator uses `10.0.2.2`; a physical device uses the host LAN IP. Confirm Windows firewall and that Uvicorn listens on `0.0.0.0`.
- **Proposal reaches no activity:** that is expected until Gate A is confirmed. Live AI never bypasses Gate A.

Runpod production, real child data, Android release, and live P3/TTS/video remain outside this approved feature.



## 8. Studio provider wrapper and exact tech-stack models

The approved harness baseline for this live slice is fixed: `Whisper large-v3-turbo` through `faster-whisper`, and `Qwen/Qwen3-VL-8B-Instruct` for structured drawing understanding. `Wan2.2-TI2V-5B` remains outside this P2 smoke.

Use `tools/lightning_provider_server.py` as the Studio `server.py`. It loads the model paths `models/asr` and `models/vlm/qwen3-vl-8b-instruct`, exposes `/health`, `/v1/asr`, and `/v1/vision`, and rasterizes the checked-in synthetic SVG fixture with `cairosvg` before Qwen3-VL inference. Install `cairosvg` in the Studio before restarting the provider:

```bash
pip install cairosvg
```

The provider returns only the versioned structured contract; it does not return raw model output or prompts. The first live request loads the models and can take longer than a warm request.
