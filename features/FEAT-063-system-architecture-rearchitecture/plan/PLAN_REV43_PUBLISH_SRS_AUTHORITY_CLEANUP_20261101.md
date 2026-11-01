# FEAT-063 Plan Rev43 — Publish canonical SRS authority cleanup

- Plan revision: 43 (Rev42 is already used by Swagger review on this branch)
- Date: 2026-11-01
- Base: `origin/dev` at `f68ed2b579c89e8fb1ee3dcf7e4c8f109acd31d8`
- Publication branch: `codex/feat063-srs-authority-20261101`
- Work type: documentation-only commit and push

## Goal

Publish the repository rule that the latest FEAT-063 SRS is the sole canonical working source for current product requirements and target architecture, and label older tracked feature contexts as historical/feature-local.

Canonical SRS: `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.3-draft, still unsigned.

## Exact commit manifest

Only the following 36 documentation paths may be included:

1. `AGENTS.md`
2. `docs/context/SRS_AUTHORITY.md`
3. `docs/context/PROJECT_CONTEXT.md`
4. `docs/context/SOURCE_REGISTER.md`
5. `features/FEAT-020-backend-ai-workflow-demo/CONTEXT.md`
6. `features/FEAT-026-current-system-srs/CONTEXT.md`
7. `features/FEAT-026-current-system-srs/CONTEXT_FINAL.md`
8. `features/FEAT-029-master-srs/CONTEXT.md`
9. `features/FEAT-030-original-derived-auto-rig/CONTEXT.md`
10. `features/FEAT-030-whiteboard-story-video/CONTEXT.md`
11. `features/FEAT-031-academic-reports-markdown/CONTEXT.md`
12. `features/FEAT-033-montessori-profile-and-flow-recovery/CONTEXT.md`
13. `features/FEAT-036-ui-current-direction-alignment/CONTEXT.md`
14. `features/FEAT-037-registration-age-genai-payment-alignment/CONTEXT.md`
15. `features/FEAT-039-collaborative-learning-scope/CONTEXT.md`
16. `features/FEAT-040-four-person-delivery-plan/CONTEXT.md`
17. `features/FEAT-041-dev-publication/CONTEXT.md`
18. `features/FEAT-042-feat018-contract-dev-merge/CONTEXT.md`
19. `features/FEAT-043-srs-ui-screen-set/CONTEXT.md`
20. `features/FEAT-044-be2-ai-job-foundation/CONTEXT.md`
21. `features/FEAT-045-be1-core-domain-foundation/CONTEXT.md`
22. `features/FEAT-046-be1-durable-core-adapters/CONTEXT.md`
23. `features/FEAT-048-be2-content-publication/CONTEXT.md`
24. `features/FEAT-048-be2-vision-correction/CONTEXT.md`
25. `features/FEAT-050-be2-knowledge-video/CONTEXT.md`
26. `features/FEAT-050-be2-sketch-generation/CONTEXT.md`
27. `features/FEAT-058-review2-document-package/CONTEXT.md`
28. `features/FEAT-060-classroom-integration-and-review-remediation/CONTEXT.md`
29. `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
30. `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
31. `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
32. `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
33. `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
34. `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
35. `features/FEAT-063-system-architecture-rearchitecture/evidence/SRS_AUTHORITY_AND_LEGACY_CONTEXT_CLEANUP_20261101.md`
36. `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV43_PUBLISH_SRS_AUTHORITY_CLEANUP_20261101.md`

The two FEAT-061/FEAT-062 context files and FEAT-026/FEAT-029 local source registers present only as untracked files in the original dirty workspace are excluded. They are not part of this branch's tracked tree; their local edits remain in that workspace.

## Steps

1. Record owner authorization for this exact manifest and plan hash in FEAT-063 `approvals/TASK_APPROVAL.md`.
2. Apply the authority record, global reading rules, tracked-context notices, and FEAT-063 evidence/status updates.
3. Verify the exact 36-path diff, `git diff --check`, plan/approval hash, and repository security validator.
4. Commit the approved manifest on the publication branch and push that branch without force.
5. Verify the remote ref equals the pushed commit.

## Acceptance criteria

- AC1: Root agent guidance and global context identify FEAT-063 SRS v2.3-draft as the canonical working baseline and retain its unsigned status.
- AC2: All 24 older tracked context files in this manifest identify their SRS references as historical/feature-local.
- AC3: No old SRS content, API route, runtime code, or database artifact is modified.
- AC4: The commit contains exactly the 36 paths above and passes repository security validation and whitespace checks.
- AC5: The new branch is pushed and its remote ref equals the verified commit; no force push occurs.

## Exclusions

- Any API endpoint/path rename or new route implementation; this commit is solely the SRS authority cleanup.
- Untracked or staged files from the original workspace that are not in the manifest.
- Tests, Docker, database, Firebase/AI/provider access, secrets, `.env`, visual promotion, merge, or changes to `dev`.
- Rewriting/deleting historical SRS originals or changing FEAT-063 SRS requirements/sign-off.

## Risks

- The SRS remains a draft; all authority text must preserve that status.
- The dirty original workspace is not the publication source. This branch is based on the clean, current `origin/dev` tree and intentionally excludes its unrelated changes.
- Repository instructions route agents to the SRS but cannot technically prevent an agent from manually opening historical files.

## Evidence

Record the reviewed path manifest, security/diff checks, commit ID, push result, and remote-ref verification in the feature's evidence file and status.
