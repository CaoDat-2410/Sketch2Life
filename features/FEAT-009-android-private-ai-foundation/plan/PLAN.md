# FEAT-009 Android and private-AI foundation plan

- Status: DONE
- Plan revision: 1
- Implementation status: DONE

## Goal

Turn the generic mobile/backend shell into a deliberate Android-only foundation with a private, server-side AI trust boundary and durable decision/evidence records.

## Scope

- Generate the official React Native 0.87 Android native skeleton.
- Set application ID/namespace to `com.sketch2life.mobile`.
- Set min/target/compile SDK to 29/36/37 and document the reasoning.
- Remove iOS commands/placeholders from the active project.
- Default asynchronous progress to bounded polling for the MVP.
- Add backend-only private Lightning AI configuration/port skeleton and security guidance.
- Update context, ADRs, setup guides, and feature-local evidence.

## Steps

1. Record owner approval and official-source rationale.
2. Generate and normalize the Android native project without adding UI.
3. Add the backend AI port/configuration boundary without a live provider call.
4. Document trust boundaries, secret handling, polling, and remaining auth decision.
5. Run harness, architecture, type, test, Python, and Android configuration checks.

## Acceptance criteria

- [x] Android native skeleton exists and uses `com.sketch2life.mobile`.
- [x] Android declares minSdk 29, targetSdk 36, and compileSdk 37.
- [x] Active scripts/docs are Android-only and no iOS project remains.
- [x] Mobile has no Lightning AI credentials or direct provider adapter.
- [x] Backend exposes an abstract AI gateway port and typed private connectivity settings only.
- [x] Private endpoint, short-lived identity, TLS, egress restriction, redaction, retention, and output validation are documented.
- [x] Polling is recorded as the reversible MVP progress transport.
- [x] Harness and code/configuration checks pass with evidence stored in this feature.
- [x] No frontend visual or product behavior is introduced.

## Risks and mitigations

- Android compatibility estimates can age: record the source date and re-check Play Console before release.
- Private Lightning networking is provider-specific: keep the application port provider-neutral and provision through a later approved feature.
- Polling can create load: use job-version ETags, bounded intervals, exponential backoff, and terminal-state stop conditions when implemented.
- Native generation can overwrite authored files: generate in an isolated temporary directory and copy only the reviewed Android baseline.

## Verification plan

- Inspect Gradle namespace/application ID and SDK values.
- Run harness, skeleton, and architecture validators.
- Run TypeScript typecheck/Jest and Python Ruff/Mypy/Pytest.
- Run Gradle project tasks when the local Android SDK/toolchain permits it; otherwise record the exact environmental blocker.

## Evidence plan

Store source links and validation output under this feature's `evidence/notes/` directory. No shared evidence dump is permitted.

Implementation is authorized by `approvals/TASK_APPROVAL.md` for revision 1 only.
