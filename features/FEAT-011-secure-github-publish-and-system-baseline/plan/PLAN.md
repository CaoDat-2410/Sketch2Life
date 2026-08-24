# FEAT-011 plan

- Status: DONE
- Plan revision: 1
- Implementation status: DONE

## Goal

Publish a clean, auditable foundation repository and provide a detailed single-document description of the current system without leaking secrets or overstating implementation status.

## Scope

- Record final auth/signing ownership decisions.
- Generate `docs/SYSTEM_BASELINE.md` covering product, architecture, boundaries, workflows, security, deployment, team split, status, commands, and remaining questions.
- Audit all Git candidates for environment files, credentials, seed accounts, keys, machine paths, caches, and source-document leakage.
- Remove the committed-template debug keystore and rely on the developer-local Android debug key.
- Validate the full workspace, create the initial commit, configure the exact remote, and push `main` without force.

## Steps

1. Record approval and inspect remote/local repository state.
2. Harden ignore/signing/source-path rules and create the detailed baseline document.
3. Run secret/seed/path scans and all architecture/code checks.
4. Inspect the exact staged file list, commit locally, fetch remote state, and push without rewriting remote history.
5. Store push commit/remote evidence inside this feature.

## Acceptance criteria

- [x] Child mode/account ownership, sign-in methods, and release-key owner are recorded.
- [x] One detailed current-system Markdown document exists and clearly separates implemented foundation from planned product behavior.
- [x] `.env`, seed credentials/accounts, service-account files, provider keys, signing keys, caches, and local source documents are absent from the commit.
- [x] Android debug signing no longer depends on a repository keystore.
- [x] Absolute machine paths are removed from publishable context/evidence.
- [x] Harness, architecture, TypeScript, Python, tests, lint, and security scans pass.
- [x] Remote URL is exact and remote history is inspected before push.
- [x] `main` is pushed without force and commit evidence is recorded.

## Risks and mitigations

- Remote may contain history: fetch/inspect first; never force-push.
- Git credentials may be unavailable: request approval/login only when required; do not print tokens.
- False-positive secrets in examples: keep only explicit placeholders and document them.
- Source evidence may contain handbook extracts: exclude source screenshots/documents from public commit unless explicitly approved.

## Verification plan

- Use `git check-ignore`, staged-file review, filename scans, and content scans before commit.
- Run all existing validators/test suites.
- Verify remote URL, branch, commit hash, and upstream after push.

## Evidence plan

Store a sanitized audit report and publish result in `evidence/notes/`; never store tokens, full credential output, or sensitive remote metadata.

Implementation is authorized by `approvals/TASK_APPROVAL.md` for revision 1 only.
