# Local Python environment approval — 2026-10-20

## Approval

The user explicitly authorized: “Authorize isolated venv install”. This is a
scoped approval to create an ignored `backend/.venv` inside the FEAT-057
integration worktree and install the backend `.[dev,image-admission]` profile
from `backend/pyproject.toml`.

## Boundaries

- Use CPython 3.12 in the integration worktree only.
- Keep the shared Python environment untouched.
- Use the configured package index as needed.
- Install no model/GPU extras and download no model weights.
- This approval does not authorize runtime, server, HTTP/provider, Lightning,
  Studio, SQL execution, staging, commit, push, PR, or merge actions.
- Keep BE2-08–14 card approval, acceptance, and status records unchanged.

## Verification

The venv path is covered by the repository `.gitignore` rule `.venv/`.
Before installation, the integration worktree was on
`feature/be2-backend-ai-integration` at
`d35f035f87fddfc87b0d72d8929f5b1b843fce0e`, the index was empty, and
`backend/.venv` did not exist. The existing dirty worktree was preserved.
