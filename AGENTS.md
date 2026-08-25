# Sketch2Life project operating rules

This repository is governed by the harness in `docs/governance/` and the records under `features/`.

## Non-negotiable workflow

1. Read the relevant project context and source register before proposing work.
2. Create or update a feature folder under `features/FEAT-.../`.
3. Write the feature plan and acceptance criteria before implementation.
4. Record explicit task approval in `approvals/TASK_APPROVAL.md`.
5. Do not implement while the task status is `DRAFT`, `PLANNED`, or `AWAITING_APPROVAL`.
6. For frontend visuals, generate into `assets/generated/`, record provenance, obtain visual approval, and only then reference/copy into `assets/approved/` and `assets/applied/`.
7. Store evidence inside the feature's own `evidence/` directory. Do not use a shared untraceable evidence dump.
8. Update context, decisions, evidence, and status after every meaningful implementation or review step.

## Architecture rules

- Keep domain rules independent from frameworks, providers, storage, queues, and UI.
- Dependencies point inward: interfaces/adapters -> application -> domain; infrastructure implements ports.
- Cross-feature behavior travels through versioned contracts, not implicit state or direct database coupling.
- Preserve originals and provenance; derived artifacts never silently replace source artifacts.
- Do not lock the final tech stack until the project questions in the current task are answered and recorded in an ADR.
- Keep Sprint 1 as four independent fixture/contract workstreams defined by ADR-0006. Do not assign backend/infra/E2E to Person 4 or the complete Android app to Person 3 by default.
- Treat the dependency-driven project roadmap and the parallel team sprint assignment as separate planning views. Integration requires a separately approved allocation.
- Apply Montessori eligibility hard rules before any future recommendation ranking; `NO_VALID_ACTIVITY` is valid and rules must never be relaxed to force a result.
- Treat FEAT-002 catalog records as synthetic/provisional. Never represent `PENDING_OWNER_REVIEW`, `PROVISIONAL_OWNER_REVIEWED`, or `production_eligible=false` records as qualified or production-approved content.

## Repository security rules

- Never commit `.env`, seed accounts/users/credentials, service-account files, provider tokens, signing keys, or real child data.
- `.env.example` contains placeholders only; actual values come from ignored local files or runtime secret managers.
- Firebase is Authentication-only. Firebase Storage, Firestore, and Realtime Database are forbidden.
- Mobile never contains S3, Lightning, or Runpod credentials/endpoints.
- External handbook/workbook originals and rendered extracts remain local and are not published.
- Run `python tools/validate_repository_security.py` before every commit/push.
