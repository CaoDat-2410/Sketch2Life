# Plan Rev10 Current State Review 2 Dossiers and Publication

- Date: 2026-10-24 (Asia/Saigon)
- Feature: FEAT-058-review2-document-package
- Revision: 10 (amends Rev9)
- Status: Approved for documentation authoring and the owner's explicitly requested commit/push after publication-security checks pass.

## User direction

The owner delegated the N1-N9 filter with “check hệ thống và tự ấy đi” and clarified that unknowns should be listed explicitly. The owner authorized exactly four dossier categories, each as Word and PDF, and approved the missing state-machine/activity diagram types authored from Mermaid and converted into editable Draw.io. The owner selected `Phieu_FA26SE225_v1.2.docx` as the registration authority.

The owner subsequently requested commit and push of the current project changes, with a clean working tree afterward. This is authorization to publish the current local branch after the repository security validator passes. It does not authorize force push, tag creation, deployment, provider calls, or publication of prohibited local reference material.

## Near-term planning proposal

| ID | Status in proposed near-term plan | Reason and dependency | Known unknowns retained |
|---|---|---|---|
| N1 | Keep | Agree the Alembic lineage and install/upgrade/rollback approach before database acceptance. | Delivery-path heads, approver, clean-install procedure and rollback policy are TBD. |
| N2 | Keep | Complete BE1 route, transaction, authorization, receipt and security review before database acceptance; review can proceed alongside N1. | DTO/version, guard/idempotency details, trusted proxy configuration, key lifecycle, cross-replica throttle and concurrency rules are TBD. |
| N3 | Keep, after N1/N2 | Execute isolated synthetic PostgreSQL acceptance for WF-01/WF-02; four DB cases were skipped without `BE1_TEST_DATABASE_URL`. | Operator, isolated environment, DB version, scenario thresholds and evidence location are TBD. |
| N4 | Keep, after or alongside N3 | Validate QR/deep link, restart, reconnect and network-loss behavior on supported devices before claiming end-to-end acceptance. | Device/OS/browser matrix, recovery criteria and test owner are TBD. |
| N5 | Defer | WF-03/WF-04 integration depends on FEAT-057 adoption gates and approved versioned contracts. Requirements remain in scope. | Owner, contract version, fallback and human review/safety path are TBD. |
| N6 | Defer | Configure external runtime services after contract decisions and before any live checks. No live configuration or budget is evidenced. | Firebase project, storage profile, Modal profile, region, secret owner and cost cap are TBD. |
| N7 | Keep as pre-pilot gate | Complete consent, purpose, retention, export/deletion, purge and audit controls before real child data is used. Synthetic acceptance may proceed without child data. | Consent language, data classes, purge/backup rules and institutional/legal approval are TBD. |
| N8 | Defer; rewind stays disabled | OD07 is unresolved and forward-only progression remains valid while rewind is disabled. No scope is removed. | Whether rewind is required and its guards/receipts are TBD. |
| N9 | Defer, after N3/N6 | Measure the stated 40-child target after a repeatable database and runtime profile exists; it is not a hard admission cap. | Workload, device/network profile, thresholds, hosting/cost and measurement owner are TBD. |

No candidate is marked “Omit from near-term plan.” Deferral is a sequencing proposal and does not remove WF-01 through WF-04 or their registered requirements. No calendar dates, capacity, sprint assignment, effort commitment or accountable owner is inferred.

## Scope and deliverables

Create exactly four Review 2 dossier categories, each in editable DOCX and PDF (eight files):

1. Registration v1.2 plus BM03 Record of Changes.
2. Consolidated Reports 1-5 and Project Tracking, including the detailed PM plan and current SRS v3.3 requirements/design evidence.
3. BM02 Self-Review, retaining the official prompt and stating the absent `review-2` tag and draft limitation.
4. BM01 Design Brief plus Appendix A, conforming to the guide's page/format/content limits.

Use the five supplied Draw.io sources unchanged and expand the editable Mermaid-to-Draw.io master to twenty-two pages: eighteen lifecycle views covering all fifteen registries in SRS v3.3/B19.4 (session lifecycle plus pause/recovery and early-termination companion views; shared learning stage; group progress; admission; device connection plus grant-revocation companion view; draft sync; sketch pipeline; child suggestion response; knowledge editorial; media job; video delivery; activity execution; observation; content publication; data request), and one activity diagram for each main workflow WF-01–WF-04. The course guide requires state-machine coverage for each main entity with a lifecycle (p. 2), and at least four activity diagrams for a four-person team, one per main workflow (p. 5). Mermaid is retained as source for these authorized diagram types; final diagrams are native editable Draw.io pages, and the supplied Draw.io files remain unchanged. WF-03/WF-04 pages are target design and do not claim runtime acceptance. Preserve Rev7 and Rev9 as historical. The output folder is `artifacts/submission_r2_rev10/`.

## Repository publication boundary

- Keep external reference PDFs/spreadsheets, their rendered extracts, sensitive raw logs, local-only page renders and submission PDFs local where the repository security validator excludes them. Do not weaken or edit the validator to bypass a finding.
- Replace publishable absolute workstation paths in records/logs with repository-relative provenance or a neutral local-source label.
- Retain user-requested final DOCX/PDF files locally. The final PDFs are not committed because the mandatory validator explicitly bans publishable `.pdf` files.
- Do not commit generated archive bundles or unapproved assets where their source/provenance/visual approval is not established. Keep them locally and add precise ignore rules as needed.
- Review staged paths, run `python tools/validate_repository_security.py` immediately before commit and again immediately before push, commit the approved safe working-tree changes, push the existing `dev` branch without force, and verify the final worktree is clean. No app test suite is added or run for this publication step.

## Work sequence

1. Record this plan, delegated N1-N9 proposal, and the user's publication instruction in FEAT-058 approvals/decisions.
2. Update the four dossiers from the selected form, SRS v3.3, current feature evidence, course guide and supplied/authorized Draw.io diagrams. Preserve unknowns and distinguish implemented-local behavior from acceptance evidence.
3. Produce the four DOCX/PDF pairs locally. Render and inspect every page; verify BM01 constraints and compare key page geometry to supplied templates.
4. Update FEAT-058 context, source register, decisions, status and QA receipts; preserve prior revisions.
5. Sanitize repository records and define local-only outputs so the security validator passes without changing its rules. Review the exact stage list.
6. Run the mandatory repository security validator, commit the safe current changes, re-run the validator, push `dev`, and verify clean status and the remote commit.

## Acceptance criteria

- AC51: N1-N9 each have a detailed Keep/Defer/Omit-from-near-term/Unknown decision and reason; all nine remain within registered product scope unless a separately approved scope change is recorded.
- AC52: No names, dates, class/project codes, capacities, device matrix, or runtime settings are invented; unknowns are labeled TBD.
- AC53: Exactly four dossier categories are produced as four DOCX plus four matching PDF files; BM04 is excluded.
- AC54: The documents consistently use the selected registration, SRS v3.3/B28 and current FEAT-060/FEAT-057 evidence; design diagrams are not presented as runtime proof.
- AC54a: The report includes state-machine coverage for all fifteen B19.4 lifecycle registries (eighteen focused Draw.io state pages including companion views) and one activity page for each of WF-01–WF-04; all pages are editable in the same Draw.io master and are described as design models, not runtime proof.
- AC55: BM02 preserves the official prompt and does not claim the missing `review-2` tag gate is complete.
- AC56: BM01 sections 0-8 fit the required four A4 pages with 11 pt body text and 2 cm margins, exactly five decisions, three risks, no more than six measurable NFRs, and Appendix A follows.
- AC57: Every final PDF page is rendered and visually inspected; all output hashes, page counts, limitations and QA results are recorded locally.
- AC58: The repository security validator passes before commit and before push; no prohibited local reference, absolute path, secret or PDF is committed.
- AC59: The commit is pushed to the requested current branch without force, and `git status` shows a clean worktree.

## Risks and limitations

- The security validator bans all publishable PDFs, including generated course deliverables. Therefore the requested PDF outputs will be delivered from the local feature output folder but excluded from Git publication.
- The current branch is 726 commits ahead of `origin/dev`; a normal push publishes that existing local history plus this commit. It is a fast-forward from `origin/dev` and will be rechecked before pushing.
- BM02 remains a draft if the course's exact `review-2` tag is absent, even after the worktree is committed and pushed.
- No app tests, live-provider calls, deployments, or real child-data runs are part of this task.
