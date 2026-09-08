# P2-T2 and P2-T3 adapter evidence

- Evidence ID: EV-003-T2-T3-01
- Date: 2026-08-26
- Reviewer: Codex; implementation requested directly by the project owner
- Scope: FEAT-003 plan revision 4, P2-T2 and P2-T3 only
- Data: deterministic in-memory fixture responses and typed fake provider boundaries; no live model call, credential, endpoint, or child data

## Delivered behavior

- `AsrPort` and `VisionUnderstandingPort` are application-facing protocols.
- `FixtureAsrAdapter` and `FixtureVisionAdapter` provide deterministic contract tests.
- `WhisperAsrAdapter` maps an injected typed engine result to `AsrResultV1`, including language, confidence, timestamped segments, quality, provenance, and typed failures.
- `Qwen3VLStructuredAdapter` maps only structured payloads accepted by a strict Pydantic shape. Free text, unknown fields, malformed values, and prohibited psychological/personality fields are rejected.
- Every success/failure preserves the requested source reference; no raw SDK object or provider payload is returned.
- Retry budgets are capped at one retry in each adapter. T4 fusion and T5 evaluation remain out of scope.

## Command and result

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests
backend/.venv/Scripts/python.exe -m ruff check backend/src backend/tests
python tools/validate_architecture.py
python tools/validate_harness.py --feature features/FEAT-003-multimodal-understanding
python tools/validate_repository_security.py
git diff --check
```

Observed local result:

```text
23 passed
All checks passed!
ARCHITECTURE_VALID
HARNESS_VALID
REPOSITORY_SECURITY_VALID
```

The Python 3.14-hosted mypy executable was unavailable for a clean run in this environment; this is an environment limitation and not evidence of a successful type check.
