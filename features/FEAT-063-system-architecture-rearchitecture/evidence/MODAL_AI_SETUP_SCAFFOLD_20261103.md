# Modal AI setup scaffold — implementation evidence

- Date: 2026-11-03, Asia/Saigon.
- Feature: FEAT-063.
- Approved plan: `plan/MODAL_AI_SETUP_SCAFFOLD_20261103.md`.
- Approved plan SHA-256: `7FE03A68DF76877457DF5C5F652FCB705669A624B2E07F7B6F317C9FB510E391`.
- Approval: `approvals/TASK_APPROVAL.md`, “Modal AI setup scaffold — 2026-11-03”.
- Canonical product source: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.3-draft, especially §§6.2–6.3, 9.5, 22, 24.3–27, 31.4–31.5.

## Delivered

- `deployment/modal/srs_v23/workloads.json`: registry of AI and deterministic pipeline stages, candidate status, data boundary, human gate, compute/quota owner and implementation readiness.
- `deployment/modal/srs_v23/contracts.py`: strict dev-only, versioned worker input contract with opaque IDs, attempt prefix, manifest reference, digest, and proposed synthetic input byte cap. Payload shape excludes raw media and credentials.
- `deployment/modal/srs_v23/l4_app.py`: L4 dev function skeleton and CPU-only health check. Inference function fails closed with `MODAL_WORKLOAD_NOT_CONFIGURED`.
- `deployment/modal/srs_v23/video_app.py`: L40S dev scene function skeleton and CPU-only health check. LTX inference remains unconfigured.
- `deployment/modal/srs_v23/modal.env.example`: placeholder values and resource names only.
- `deployment/modal/srs_v23/README.md`: owner setup, deploy commands, data-staging boundary, retries, and workload caveats.
- Additive FEAT-063 plan, approval, decision, context, status, source-register and evidence records; global source-register entry.

## Verification and limits

- Source review: all changed paths match the approved allowlist; existing `deployment/modal/qwen_vision_v2.py`, backend configuration, SRS, API and Docker files are unchanged.
- Static parse: three Python files parsed with `ast.parse`; `workloads.json` parsed with `json.loads` — passed.
- `git diff --check` — passed.
- `python tools/validate_repository_security.py` — `REPOSITORY_SECURITY_VALID`, 6,181 publishable files scanned. An initial scan identified the Secret-name example as a non-placeholder assignment; it was changed to a neutral placeholder and the final scan passed.
- Product tests, Modal CLI commands, account/resource creation, inference, GPU use, deployment, actual `.env` edits, and real-child data: not run, per approved scope.
- The scaffold does not implement inference handlers or backend dispatch/storage integration. Candidate model versions, licenses, GPU suitability, timeout values and SRS transfer caps remain subject to later POC/review. The existing legacy Qwen3-VL app is not changed or promoted.
