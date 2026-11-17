# Sketch2Life project operating rules

This repository is governed by the harness in `docs/governance/` and the records under `features/`.

## Current product SRS authority

- Before answering or changing current product requirements, read `docs/context/SRS_AUTHORITY.md` and use only `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (v2.7-draft) as the canonical working SRS.
- The v2.7 SRS remains a draft awaiting formal owner sign-off. Its as-built/source snapshots are environment-specific and do not replace the target product requirements. Canonical working source does not mean final approval.
- Older SRS copies and older feature contexts are historical/feature-local records. Do not use them as current product requirements or let them override the FEAT-063 SRS. Consult them only for explicit historical comparison or feature-specific implementation evidence.
- If a current requirement is missing or conflicts with an older record, preserve the open question and report it; do not import an older requirement silently.

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

## Repository security rules

- Never commit `.env`, seed accounts/users/credentials, service-account files, provider tokens, signing keys, or real child data.
- `.env.example` contains placeholders only; actual values come from ignored local files or runtime secret managers.
- Firebase is Authentication-only. Firebase Storage, Firestore, and Realtime Database are forbidden.
- Mobile never contains S3, Lightning, or Runpod credentials/endpoints.
- External handbook/workbook originals and rendered extracts remain local and are not published.
- Run `python tools/validate_repository_security.py` before every commit/push.
