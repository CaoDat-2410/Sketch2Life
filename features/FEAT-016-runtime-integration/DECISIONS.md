# Runtime Integration decisions

- 2026-09-05: FEAT-016 is a separate feature because FEAT-015 approval covers offline integration only.
- 2026-09-05: P1 remains canonical for activity/objective identity; runtime adapters must preserve ID/version.
- 2026-09-05: application commands own state transitions; providers, workers, storage and UI are adapters.
- 2026-09-05: fixture-only E2E is the first runtime target; live provider and public release are excluded.
- 2026-09-05: complete the approved fixture UI/lifecycle harness before opening the separate live-AI plan; the fixture screen exposes the same versioned contracts without credentials or provider coupling.
