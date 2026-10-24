# Merge product branches and continue Review 2 documents

- Revision: 3
- Date: 2026-10-23 Asia/Saigon
- Base: BE1-ready `dev` at `f220781876472950093856e97bbdaaec5170a7c1`; final document baseline is `0a7ce768c153f2104cff930569c3eda6e484532c` after fetching the newly pushed Child UI branch.
- Scope now includes the directly requested branch integration ahead of final document questions.

## Owner authorization

Owner request: merge `FE_UI_Child`, `FE_UI_Admin`, `FE_UI_Teacher` and `feature/be2-backend-ai-integration` into the branch that already has BE1 ready, then create the Reports 1–5/Tracking and BM01 documents. The owner later confirmed the Child UI had just been pushed and directed us to fetch it. This is local branch integration and document authoring only; no push/PR or deployment is included.

## Steps

1. Preserve the dirty calling checkout. Use a separate clean worktree for integration.
2. Fetch and pin source/base SHAs. Confirm each source descends from the BE1 base and review incoming commits, migrations and high-risk paths.
3. Merge in dependency order: BE2 backend, Child, Teacher, Admin. A source identical to/already contained by target is recorded as a no-op. Resolve only source integration conflicts consistent with approved contracts; stop on unresolved semantic/security conflicts.
4. Run merge conflict checks, relevant validators/tests and repository security scan before creating merge commits. Preserve secrets, synthetic-data, Firebase and provider boundaries. No direct runtime approval is inferred by the code's presence; branch merge is the owner's explicit integration authorization.
5. Report branch merge SHAs and checks. Refresh document source analysis on the final merged result; capture remaining unknown form metadata as TBD or a labelled source inference.
6. Create the English consolidated course report from the official Report7 template, retaining Reports 1–5 and Project Tracking sections, and create the separate English BM01 from its template. Include source Mermaid diagrams and traceability to the registration and actual code/migrations.
7. Render both final DOCX files to PDF/page images, inspect every page, fix layout, and record input hashes, page counts, and gaps. Do not claim post-merge application tests or live Modal deployment unless executed separately.

## Acceptance

- AC10: Exact source SHAs and merge/no-op status recorded per named branch.
- AC11: Calling checkout's modified/untracked files are unchanged.
- AC12: Integration worktree is based on the BE1-ready `dev` line and contains each mergeable requested source branch.
- AC13: No merge conflict markers, unrelated cleanup or silently omitted source path.
- AC14: Required security validator passes before merge commits; focused or full tests are run as appropriate and results recorded without overclaim.
- AC15: No push, PR, deployment, provider call or credential/data introduction occurs.
- AC16: Refreshed documents are based on resulting merged source; unresolved implementation and product gates remain labeled.
- AC17: The final source baseline includes refreshed `origin/FE_UI_Child` source `ca3779869dfc1385cbbc7b8ca730f780386af7b2` at merge commit `0a7ce768c153f2104cff930569c3eda6e484532c`; `apps/child-ui` is documented as a fixture/stub prototype, not an integrated product client.
- AC18: Consolidated Report 1–5/Project Tracking and BM01 use the local official templates, meet BM01 sections 0–8 four-page/11 pt/2 cm constraint plus Appendix A, contain source diagrams and testable acceptance criteria, and pass page-by-page visual review.

## Risks

- The four branches may include separate descendant histories with shared backend/UI paths; resolve by inspecting conflicts and preserving tests/contracts.
- Database migrations may have multiple schema-owned heads. Preserve owner boundaries and do not invent a production migration graph; record exact ALEMBIC heads behavior.
- Branch inclusion alone does not establish end-to-end product integration, real provider acceptance or readiness.

## Verification

Record base/source/merge SHAs; check `git status`, merge bases, diff and conflict markers. Preserve prior repository security scan evidence. This document-only continuation does not run application suites. Verify requirement-to-diagram/test mapping, BM01 arithmetic/page limit, DOCX package validity, input hashes, and every rendered page. Confirm original dirty checkout status and ignored/local state are intact.
