# Repository security audit

- Audit date: 2026-08-24
- Scope: every tracked or untracked, non-ignored file eligible for publication.
- Result: PASS before staging.

## Controls verified

- `.env` and `.env.*` are ignored, while only `.env.example` templates are publishable.
- Android signing files (`*.jks`, `*.keystore`) are ignored and no repository-managed debug keystore remains.
- Firebase client configuration and service-account credential files are ignored.
- Seed-account and seed-user files are ignored; no seed credential is present.
- External PDF/XLS/XLSX source documents and temporary handbook page extracts are excluded.
- Publishable context and evidence contain no absolute local-machine path.
- Common private keys and provider-token patterns are absent.
- Generated dependency, build, test-cache, virtual-environment, and IDE output remain ignored.

## Repository-specific safeguard

`tools/validate_repository_security.py` enumerates the same publishable candidate set as Git and fails on prohibited filenames, sensitive content, local paths, or missing ignore rules. It must run before review, commit, and push.

## Remote preflight

- Intended remote: `https://github.com/CaoDat-2410/Sketch2Life.git`
- Intended branch: `main`
- Remote-head inspection result: no branch heads existed before the initial publish.
- Push policy: normal fast-forward/initial push only; force-push is forbidden for this operation.

No secret value, credential output, signing material, or sensitive child data is stored in this evidence.
