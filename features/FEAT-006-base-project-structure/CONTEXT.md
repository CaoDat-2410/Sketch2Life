# FEAT-006 Base project structure context

- Status: IN_PROGRESS
- Primary owner: Project owner + four-person team
- Scope: Establish the mobile-only repository skeleton and clean-architecture boundaries.
- Authorized by: Explicit current user request to set up the base project structure.
- Not in scope: Product behavior, API endpoints, model integration, database migrations, UI implementation, or generated frontend visuals.

## Assumptions used for the scaffold

- React Native + TypeScript remains the current frontend proposal.
- FastAPI/Python remains the current backend proposal.
- Backend and AI provider clients remain behind adapters.
- Fixture-only development data is stored separately from source code.
- Parent/guide flows live in the same mobile app as role-based modes.
