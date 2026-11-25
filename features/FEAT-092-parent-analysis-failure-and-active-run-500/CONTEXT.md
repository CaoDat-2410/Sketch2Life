# FEAT-092 context

Two Parent-flow defects found in the local dev run on 2026-11-25 (API container logs):

1. Drawing analysis spins forever. Modal `drawing.analyze` raised `AttributeError` in the worker; the backend
   treated any non-`RemoteError` exception as outcome-unknown, the run moved to `AWAITING_RECONCILIATION`, and
   the app classifies that state as `processing` until its 8 minute budget ends.
2. `GET /v1/story-runs/active/current` returns 500: stored suggestion-based main-activity snapshots carry 8
   provenance fields that `ParentActivityV1` (`extra="forbid"`) does not declare.

Current SRS authority: FEAT-063 SRS v2.7-draft (see docs/context/SRS_AUTHORITY.md).
