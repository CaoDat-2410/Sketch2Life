# FEAT-010 plan

- Status: DONE
- Plan revision: 1
- Implementation status: DONE

## Goal

Make release, identity, storage ownership, and AI provider boundaries explicit and enforceable without provisioning external services.

## Scope

- Add APK/AAB build commands and a release/signing guide.
- Select Firebase Authentication only; forbid Firebase Storage/Firestore/Realtime Database.
- Add provider-neutral identity verification ports and configuration placeholders.
- Reframe Lightning as fixture-only development and Runpod Serverless as production AI provider.
- Preserve backend-only AI access and S3 artifact ownership.
- Update ADRs, context, source register, validators, and evidence.

## Steps

1. Record owner approval and official-source evidence.
2. Add release/auth/AI decisions and security boundaries.
3. Add setup-only ports, settings, scripts, and validation rules.
4. Run harness, architecture, Python, and TypeScript checks.

## Acceptance criteria

- [x] Android exposes explicit debug APK and release AAB build commands.
- [x] Documentation distinguishes test APK, signed release APK, and Google Play AAB.
- [x] Firebase is limited to Authentication; storage remains backend-owned S3-compatible storage.
- [x] Backend authentication depends on a provider-neutral token verifier port.
- [x] No real Firebase project file, service-account key, Runpod key, or Lightning token is committed.
- [x] Lightning is documented as fixture/dev only; Runpod is the production AI adapter target.
- [x] Mobile never calls Lightning/Runpod or S3 directly.
- [x] Security and architecture validators enforce the forbidden provider/storage shortcuts.
- [x] All applicable checks pass and evidence remains feature-local.

## Risks and mitigations

- Signing-key loss can break updates/ownership proof: create, escrow, and back up the release/upload key before external APK distribution.
- Firebase SDK scope creep: allow only Auth packages/config; reject storage/database dependencies in validation.
- Personal Lightning has no guaranteed private network: fixture-only data and backend-only authenticated gateway.
- Runpod endpoints are bearer-authenticated public APIs: use restricted endpoint keys, runtime secrets, rotation, timeouts, and backend-only calls.

## Verification plan

- Validate package scripts and forbidden dependency patterns.
- Run harness/skeleton/architecture validators.
- Run frozen lockfile, TypeScript, Jest, ESLint, Ruff, Mypy, and Pytest checks.
- Record Android SDK absence as the reason no APK is emitted in this setup-only feature.

## Evidence plan

Store official source links and reproducible validation notes under this feature's `evidence/notes/` directory.

Implementation is authorized by `approvals/TASK_APPROVAL.md` for revision 1 only.
