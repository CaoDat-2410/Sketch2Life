# FEAT-006 Base project structure plan

- Status: REVIEW
- Plan revision: 1
- Implementation status: DONE
- Scope: directories, boundary READMEs, fixture/test/infra placeholders, and architecture map only

## Steps

1. Update architecture/context for mobile-only.
2. Add `apps/mobile` presentation and bridge boundaries.
3. Add backend clean-architecture directories and boundary documents.
4. Add contracts, fixtures, test, and infrastructure placeholders.
5. Validate the harness and record the resulting structure as evidence.

## Acceptance criteria

- [x] Mobile-only code boundary exists.
- [x] Backend domain/application/interfaces/infrastructure boundaries exist.
- [x] Cross-boundary contracts and fixture-only data locations exist.
- [x] Feature-local asset approval directories remain available.
- [x] No product behavior or model call is implemented in this scaffold.
- [x] Existing architecture docs describe the actual base structure.

## Verification

- Run `python tools/validate_harness.py`.
- Inspect the base structure file list.
- Confirm no product implementation files were added.
