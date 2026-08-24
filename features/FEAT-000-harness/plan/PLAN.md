# FEAT-000 Harness plan

- Status: APPROVED
- Plan revision: 1
- Implementation status: DONE
- Implementation scope: repository harness only

## Steps

1. Create context and source-authority records.
2. Create clean-architecture scaffold and dependency rules.
3. Create feature/evidence/approval templates.
4. Create mechanical validation for repository and approval gates.
5. Verify the harness and record evidence.

## Acceptance criteria

- [x] Detailed project context exists.
- [x] Reference documents are distinguished from direct user instructions.
- [x] Each future feature has a dedicated folder and evidence location.
- [x] Clean-architecture boundaries are documented and scaffolded.
- [x] A task approval record is required before implementation.
- [x] Frontend asset generation/review/application states are documented and checked.
- [ ] Project owner confirms final harness conventions after review.

## Verification

- Run `python tools/validate_harness.py`.
- Inspect the generated file list and evidence record.
