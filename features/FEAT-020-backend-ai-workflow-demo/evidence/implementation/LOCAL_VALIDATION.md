# Local Validation Record

## Static checks

Commands were executed from the repository root:

```powershell
backend\.venv\Scripts\python.exe -m compileall -q backend/src/sketch2life
backend\.venv\Scripts\python.exe -m ruff check backend/src/sketch2life backend/tests/e2e/test_lightning_backend_workflow.py
backend\.venv\Scripts\python.exe -m mypy backend/src/sketch2life/contracts/schemas/workflow_demo.py backend/src/sketch2life/application/services/backend_ai_workflow.py backend/src/sketch2life/infrastructure/ai/workflow_prompt.py backend/src/sketch2life/infrastructure/catalog/pixi_assets.py backend/src/sketch2life/interfaces/cli/workflow_demo.py backend/src/sketch2life/workflow_demo.py backend/tests/e2e/test_lightning_backend_workflow.py
```

## Recorded results

- `compileall`: passed.
- Ruff on all new implementation files and the single E2E test: passed.
- Strict mypy on the seven implementation/test files: passed with no issues.
- Full backend suite with a workspace-local basetemp: passed; five tests were skipped by their existing opt-in/runtime gates.
- `python tools/validate_repository_security.py`: `REPOSITORY_SECURITY_VALID`.
- `python tools/validate_harness.py`: `HARNESS_VALID`.
- Typed orchestrator smoke with in-memory provider doubles: passed for `0-3`, `3-6`, `6-9`, and `9-12`; all bands emitted distinct selection vectors for the tested seed, with valid manifest hash and deferred-video records. This smoke is not the acceptance path and is not committed as an E2E fixture.
- `inspect_real_runtime()`: correctly returned `RUNTIME_NOT_READY` issues for the current workstation because Qwen3-VL and faster-whisper runtime configuration is not installed here.
- CLI `--help`: passed.
- Preflight error-manifest construction with missing paths: passed and produced a sanitized four-band `RUNTIME_NOT_READY` manifest.

## Lightning acceptance command

After the repository is pulled into Lightning Studio and the real model runtimes are configured, run:

```bash
python -m sketch2life.workflow_demo \
  --image ./features/FEAT-020-backend-ai-workflow-demo/test-assets/input-image.png \
  --narration-audio ./features/FEAT-020-backend-ai-workflow-demo/test-assets/narration.wav \
  --age-mode all \
  --demo-autopilot \
  --output ./runtime-output/workflow-result.json
```

The real-AI acceptance test is opt-in through `SKETCH2LIFE_RUN_REAL_AI_E2E=1` and uses the same replaceable test inputs. It is intentionally not claimed as locally executed because this workstation has no configured Qwen3-VL/faster-whisper runtime.

## Safety note

Raw model outputs, prompts, credentials, machine paths, and child media are not stored as evidence. The committed PNG/WAV are synthetic, pre-generated inputs only; the workflow must still call the real adapters in Lightning Studio.