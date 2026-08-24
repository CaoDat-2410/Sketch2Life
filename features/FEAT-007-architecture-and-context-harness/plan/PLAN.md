# FEAT-007 Architecture and context harness plan

- Status: REVIEW
- Plan revision: 1
- Implementation status: DONE
- Scope: architecture guides, context/evidence operating guides, and placeholder structure only

## Acceptance criteria

- [x] Python backend layers and dependency direction are documented.
- [x] React Native feature/bridge/infrastructure boundaries are documented.
- [x] Contract and integration rules are documented.
- [x] Context locations, ownership, update rules, and snapshot format are documented.
- [x] Evidence location, minimum metadata, quality, and retention rules are documented.
- [x] No product implementation or dependency installation is performed.

## Verification

- Run `python tools/validate_harness.py`.
- Inspect architecture and governance documents.
- Scan for product source files under `apps/mobile` and `backend`.
