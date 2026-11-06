# FEAT-063 Plan Rev51 — publish SRS v2.5 and reconcile latest dev source

- **Plan revision:** 51
- **Date:** 2026-11-06
- **Lifecycle:** REVIEW; the owner's direct “commit and push” request authorized this exact publication scope, recorded in the root and feature approval registers.
- **Change type:** Documentation-only publication on a new branch.
- **Starting point:** fetched `origin/dev` at `4749451080f49243464d40a464b8f83a03ae77bb`.

## Goal

Publish the FEAT-063 SRS v2.5-draft alignment on a new branch from current `origin/dev`. The source review that produced Rev45 predates the current dev merge, so add a dated source-only §32.6 crosswalk for the fetched dev tree. Keep product requirements and model directions separate from dev-only profile pins, API fixtures, test outcomes, and unverified production status.

The existing workspace is 590 commits behind `origin/dev` and contains unrelated staged, unstaged and untracked work. Use an isolated Git worktree. Reapply only the listed documentation changes onto the fetched remote version, preserving all remote-only material in context, decisions, approvals, evidence, and status records.

## Exact publication manifest

- `AGENTS.md`
- `approvals/TASK_APPROVAL.md`
- `docs/context/PROJECT_CONTEXT.md`
- `docs/context/SOURCE_REGISTER.md`
- `docs/context/SRS_AUTHORITY.md`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-55_SRS_SYSTEM_CODE_ALIGNMENT_REV45_20261106.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-56_SRS_PUBLICATION_REV51_20261106.md`
- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV45_SRS_SYSTEM_CODE_ALIGNMENT_20261106.md`
- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV51_PUBLISH_REV45_SRS_20261106.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`

## Out of scope

- Application source, API behavior, tests, builds, database, schema, migrations, providers, Modal resources, secrets, deployment, or production configuration.
- Every other staged, unstaged, and untracked path in the original checkout.
- Publishing to `dev`, force-push, history rewrite, PR creation, SRS sign-off, or owner decisions beyond the approved SRS direction.
- Re-running AI inference, database queries, or runtime/OpenAPI snapshots. Rev51 uses source review and existing attributed evidence only.

## Acceptance criteria

- **AC1 — Remote base:** the publication branch starts exactly at fetched `origin/dev` `4749451080f49243464d40a464b8f83a03ae77bb` and does not rewrite `dev`.
- **AC2 — Current-source reconciliation:** SRS §32.6 records the current main API and separate StoryRun-lite/Modal dev composition from source and attributed Rev44–46 evidence; historical Rev43 observations remain dated and scoped.
- **AC3 — Requirement authority:** §§1–31 remain target requirements; dev-only Qwen/FLUX pins, in-process background work, and synthetic test outcomes are not converted into production requirements or acceptance claims.
- **AC4 — Traceable package:** canonical pointers say v2.5-draft, companion metadata matches, decisions/status/evidence are updated, and evidence/plan identifiers do not collide with existing remote records. The prior local SRS review report is published as EV-063-55 because EV-063-34 is already assigned in `origin/dev`.
- **AC5 — Exact change set:** the staged paths equal this manifest; no unrelated local work is staged or published.
- **AC6 — Security:** `python tools/validate_repository_security.py` passes before every commit and every push; `git diff --check` is clean.
- **AC7 — Publication:** publish only the new branch by normal push, fetch it, and verify the remote SHA matches the final local branch tip.
- **AC8 — Workspace safety:** the original dirty checkout remains unchanged except for this plan and its approval-register additions; all original staged, unstaged, and untracked work stays out of the publication worktree.

## Execution and verification

1. Record owner approval for this hash-identified plan.
2. Create an isolated worktree and branch from the exact fetched `origin/dev` base above.
3. Apply only the manifest, porting changes onto current remote documentation without replacing newer remote records.
4. Review target-versus-as-built wording, source citations, evidence-ID uniqueness, changed paths, staged paths, and whitespace.
5. Run the repository security validator; commit the documentation package.
6. Run the validator again; push the new branch normally and fetch/verify the resulting remote SHA.
7. Add the publication close-out to EV-063-56 and status/approval records, then security-validate, commit, push, and verify the final branch tip again.

No product test suite is required for this documentation-only task. The security validator is mandatory before each Git write to the repository history or remote.

## Review close-out

- The exact 17-path package was committed as `620386fb227e2d8b76c48e72ad22892e3b0c1c53` (`docs(FEAT-063): publish SRS v2.5 alignment`) and pushed normally to `origin/docs/feat063-rev45-srs-code-alignment-20261106`.
- A fresh fetch confirmed the remote branch matched that commit. No force option or update to `dev` was used.
- Repository security validation passed before the package commit and again before the first push; each scan reported 6,563 publishable files, with no secrets, credentials, signing keys, or absolute machine paths.
- The original dirty checkout remains isolated from the publication branch. The SRS and Data Table Register remain unsigned drafts.
