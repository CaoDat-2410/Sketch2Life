# FEAT-063 Plan Rev44 — publish the as-built SRS alignment

- **Plan revision:** 44
- **Date:** 2026-11-06
- **Lifecycle:** APPROVED; the owner’s direct “commit and push” instruction authorizes this publication scope. The approval record identifies the reviewed plan hash.
- **Change type:** Documentation publication only.
- **Source work:** Plan Rev43, the v2.4-draft SRS alignment and its evidence.

## Goal

Publish the approved FEAT-063 v2.4-draft as-built SRS alignment and the minimum repository authority/tracking records needed to make that version the canonical working baseline. Publish on a new branch based on the fetched current `origin/dev`, since the checked-out local `dev` is 500 commits behind and 6 commits ahead of the remote-tracking branch. Do not rewrite either branch.

## Exact file scope

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
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-33_AS_BUILT_SRS_ALIGNMENT_20261106.md`
- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV43_AS_BUILT_SRS_ALIGNMENT_20261106.md`
- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV44_PUBLISH_AS_BUILT_SRS_20261106.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`

## Out of scope

- All other staged, unstaged and untracked work in the original checkout, including application code, generated UI assets, older feature contexts and evidence.
- Product/API/database/schema/migration/test/provider/deployment/secret changes.
- SRS sign-off; v2.4 remains an unsigned draft.
- Force-push, rewriting `dev`, or publishing the six local-only commits on the stale `dev` branch.

## Acceptance criteria

- **AC1:** The branch is based on the fetched `origin/dev` and includes only this plan’s exact file scope.
- **AC2:** The v2.4-draft SRS and data register, Rev43 evidence and canonical authority pointers are present without overwriting newer remote-only documentation.
- **AC3:** `python tools/validate_repository_security.py` passes in the publication worktree before commit and again before push.
- **AC4:** The documentation is committed with a descriptive message and pushed normally to a new remote branch; no force push is used.
- **AC5:** The original checkout’s existing staged/unstaged/untracked work is preserved.

## Verification

- Review the source diff and apply only this manifest to a temporary worktree based on current `origin/dev`.
- Confirm the resulting branch diff contains only the exact file scope and no unrelated source changes.
- Run the repository security validator before commit and before push. No test suite is required for documentation publication.

## Approval basis

The project owner directly instructed “commit and push” after the Rev43 SRS alignment. This authorizes publication of the exact documentation scope above, not SRS sign-off or publication of unrelated work.
