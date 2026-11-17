# Isolated Python environment preflight — 2026-10-20

- Interpreter: CPython 3.12.10.
- Profile installed in ignored integration-worktree `backend/.venv`: backend `.[dev,image-admission]`.
- `pip check`: PASS (`No broken requirements found`).
- Imports and versions:
  - pytest=8.4.2
  - ruff=0.17.1
  - mypy=1.20.2
  - Pillow=12.3.0
  - python-multipart=0.0.32
  - av=18.1.0
- Shared Python environment unchanged.
- No model/GPU extras or model weights installed.
- Package installation logs are under `evidence/raw/goal-offline-20261020/`; machine-local path prefixes were sanitized.
