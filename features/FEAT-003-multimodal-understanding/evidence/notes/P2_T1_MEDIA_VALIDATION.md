# P2-T1 deterministic media validation evidence

- Evidence ID: EV-003-T1-01
- Date: 2026-08-26
- Reviewer: Codex; implementation requested directly by the project owner
- Approved scope: FEAT-003 plan revision 3, P2-T1 only
- Data: runtime-generated synthetic PNG/WAV fixtures only; no real child data, provider credential, model, API, queue, database, or mobile access

## Delivered behavior

- `MediaValidationResultV1` is a frozen Pydantic contract with `PASS | RECAPTURE`, ordered reason codes, source artifact references/hashes, signals, and policy provenance.
- The policy and decision logic are pure domain code. PNG/WAV inspection is a local infrastructure adapter passed through an application port; the application layer does not import infrastructure.
- Files are read only. No normalization or working-copy creation occurs in P2-T1; both `working_copy_ref` fields are explicitly `null`.
- The versioned synthetic manifest is `data/fixtures/manifests/media-validation-v1.json`. Tests generate the binary media in temporary directories so no source media is checked in.

## Commands and results

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests
backend/.venv/Scripts/python.exe -m ruff check backend/src backend/tests
backend/.venv/Scripts/python.exe -m mypy backend/src
python tools/validate_architecture.py
python tools/validate_harness.py
python tools/validate_repository_security.py
git diff --check
```

Result on 2026-08-26:

```text
10 passed
All checks passed!
Success: no issues found in 30 source files
ARCHITECTURE_VALID
HARNESS_VALID
REPOSITORY_SECURITY_VALID
```

## Covered fixtures and interpretation

| Fixture | Expected result | Evidence |
|---|---|---|
| Valid synthetic drawing + narration | `PASS` | Stable contract serialization and unchanged SHA-256 hashes. |
| Small, dark, low-contrast, blurry, edge-filled image + short silent audio | `RECAPTURE` | Ordered image and audio reasons remain identical on repeated execution. |
| Corrupt PNG + corrupt WAV | `RECAPTURE` | Emits `IMAGE_UNREADABLE`, then `AUDIO_UNREADABLE`. |
| Constant but non-silent WAV | `RECAPTURE` | Emits `AUDIO_NO_SPEECH_SIGNAL` from the documented energy/zero-crossing proxy. |
| Clipped WAV | `RECAPTURE` | Emits `AUDIO_CLIPPING`. |

## Limitation and follow-up

The speech-presence result is a deterministic signal proxy, not a trained VAD and not a claim of child-speech accuracy. Threshold calibration on an approved synthetic benchmark is future P2-T5 work. P2-T2 through P2-T5 are not authorized by this evidence.
