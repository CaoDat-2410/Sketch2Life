# Backend basic lesson CRUD repository review — EV-063-20

- Date: 2026-10-28 (Asia/Saigon).
- Feature: FEAT-063.
- Purpose: read-only repository inventory to prepare Plan Rev27 for the first manual backend CRUD slice.
- Environment: `repository root`, Windows PowerShell; repository source/document reads only.

## Sources reviewed

- `docs/context/SOURCE_REGISTER.md` and `docs/governance/WORKFLOW.md`, `APPROVAL_POLICY.md`.
- `docs/architecture/PYTHON_BACKEND_ARCHITECTURE.md`, `CONTRACTS_AND_INTEGRATION.md`.
- `backend/README.md`, `backend/pyproject.toml`, `backend/src/sketch2life/interfaces/http/router_composition.py`.
- BE1 API source and `features/FEAT-047-be1-runtime-backend/artifacts/API_CONTRACT.md` for Firebase-verified identity, organization and Teacher assignment behavior.
- `backend/src/sketch2life/domain/learning_content/model.py`, `application/learning_content_commands.py`, `application/learning_content_eligibility.py`, `contracts/schemas/learning_content.py`, `interfaces/http/routers/learning_content.py`, `infrastructure/learning_content/{tables,sql}.py`, and related test-file inventory.
- FEAT-063 SRS §31 and Data Table Register §14 / Lesson table declarations, plus the Plan Rev25 approval and Plan Rev26 pending status.

## Findings

- The backend uses a modular-monolith layout and already has Firebase authentication and organization/class assignment boundaries for BE1.
- `learning_content` has a mature candidate command lifecycle and isolated persistence, but its router is explicitly candidate-only, command-only, and absent from default router composition. Its generic payload does not represent the Lesson library version/activity fields in the SRS.
- The current Data Table Register proposes the Lesson library item, immutable version and version-activity records. It states the design tables have not been created; this review did not inspect a database.
- The first slice can be text-only and independent of every AI model/provider or job system. School Manager/Public/Parent access, uploads, delivery occurrences and runtime video are not needed to test Teacher draft CRUD.

## Review method and limits

Read-only `rg --files` / `rg -n` searches and targeted PowerShell `Get-Content` reads were used to inspect the paths above. No code, tests, builds, migrations, live database, secrets, external services, AI inference, Modal, or child data were accessed. This evidence records repository design facts and a planning recommendation; it is not implementation or runtime proof.
