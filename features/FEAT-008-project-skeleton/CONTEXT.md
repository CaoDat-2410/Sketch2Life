# FEAT-008 Project skeleton context

- Status: REVIEW
- Scope: Runnable foundation skeleton for the Python backend, React Native client, isolated art-renderer package, local infrastructure, validation tools, and setup documentation.
- Authorized by: Explicit current user request to build the complete skeleton.
- Assumptions at completion: React Native CLI bare workflow, pnpm workspace, Android + iOS folders reserved, Python 3.12/FastAPI backend, fixture-only data.
- Non-goals: Product use cases, domain behavior, model calls, database migrations, real credentials, real child data, or visual assets.

## Context ownership

Cross-project truth remains in `docs/context/`. Skeleton-specific decisions and proof remain in this feature folder.

The reserved iOS assumption was superseded by the project owner's Android-only decision in FEAT-009/ADR-0004. This historical feature record is otherwise unchanged.
