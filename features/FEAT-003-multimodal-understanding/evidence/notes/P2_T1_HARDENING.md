# P2-T1 hardening evidence

- Evidence ID: EV-003-T1-HARDENING-01
- Date: 2026-08-26
- Reviewer: Codex; implementation requested directly by the project owner
- Scope: FEAT-003 plan revision 4, reviewed P2-T1 fixes only
- Data: synthetic temporary PNG/WAV fixtures; no real child data, network, provider credential, or model access

## Closed review findings

- Signed PCM 8/16/24/32-bit full-scale negative samples are normalized into `[-1, 1]`; negative full-scale no longer creates an invalid RMS contract.
- PNG inspection rejects zero dimensions, dimensions over the pixel bound, bad CRC, missing IEND, invalid compressed output, and oversized files. Decode failures return `IMAGE_UNREADABLE`.
- WAV inspection rejects oversized files and reads frames only after a bounded duration check.
- Unavailable sources use `sha256=null` and `source_status=MISSING|UNREADABLE`; no path-derived digest is emitted.
- `MediaFixtureManifestV1` is validated from the checked-in JSON fixture, and results include a deterministic human-readable recapture message.

## Command and result

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests
backend/.venv/Scripts/python.exe -m ruff check backend/src backend/tests
git diff --check
```

Observed local result:

```text
23 passed
All checks passed!
```

The repository-wide architecture/security/harness checks are recorded after the adapter slice in the companion evidence note.
