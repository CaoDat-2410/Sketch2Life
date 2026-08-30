# P2-T2 Phase A implementation evidence

- Evidence ID: EV-003-T2-01
- Date: 2026-08-30
- Approved scope: P2-T2 Phase A only; see `../../approvals/TASK_APPROVAL.md`.
- Data policy: synthetic fixture references and deterministic fake outputs only.

## Delivered artifacts

- `backend/src/sketch2life/contracts/schemas/asr.py`: versioned request/result contracts, discriminated success/failure union, fake-only profile catalog, source/working-copy provenance rules, validation provenance, retry/repair fields, and synthetic fixture manifest entry contract.
- `backend/src/sketch2life/application/ports/asr.py`: provider-neutral `AsrPort`.
- `backend/src/sketch2life/infrastructure/ai/fake_asr.py`: deterministic fixture fake; no model, SDK, provider, GPU, dependency, or audio mutation.
- `data/fixtures/manifests/asr-phase-a-v1.json`: synthetic P2-T1-PASS fixture references and expected fake scenarios.
- `backend/tests/unit/test_asr_phase_a.py`: Phase A contract/unit suite.

## Verified behaviors

- `source_audio_ref` and SHA-256 are preserved on both success and failure; no Phase A working copy is created.
- A quiet-but-mappable output is `SUCCEEDED` with `NO_SPEECH_SUSPECTED`; it does not override P2-T1 or become a recapture decision.
- Provider/mapping failures are typed `FAILED` contracts. Fake timeout, transient/non-transient provider failure, model-unavailable, schema-invalid repair, and retry attempt counts follow the approved matrix.
- Unknown profile IDs fail at request construction before `AsrPort`; `INPUT_NOT_VALIDATED` remains a typed port result with no inference attempt.
- The profile catalog contains deterministic fake entries only. No Whisper, `faster-whisper`, model weights, GPU, endpoint, credential, or live benchmark was added.

## Commands and results

| Command | Result |
|---|---|
| `backend/.venv/Scripts/python.exe -m pytest tests/unit/test_asr_phase_a.py` | 17 passed |
| `backend/.venv/Scripts/python.exe -m pytest` | 27 passed |
| `backend/.venv/Scripts/python.exe -m ruff check --no-cache src tests` | passed |
| `backend/.venv/Scripts/python.exe -m mypy src` | passed, 33 source files |
| `python tools/validate_harness.py` | `HARNESS_VALID` |
| `python tools/validate_architecture.py` | `ARCHITECTURE_VALID` |
| `python tools/validate_skeleton.py` | `SKELETON_VALID` |
| `python tools/validate_repository_security.py` | `REPOSITORY_SECURITY_VALID` |
| `git diff --check` | passed |

## Remaining gate

P2-T2 Phase B remains unapproved: it alone may introduce the real `faster-whisper`/Whisper adapter, dependency/model weights, GPU/provider execution, and ASR profile-selection evidence. P2-T5 remains the separately approved owner of the CLI and end-to-end benchmark report.
