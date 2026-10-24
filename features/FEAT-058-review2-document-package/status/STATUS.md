# Status

## Current status — 2026-10-24

- Lifecycle: IN_PROGRESS under approved Plan Rev12; Rev11 remains historical and the revised Rev12 dossier/diagram QA is produced locally.
- Approved plan: `plan/PLAN_REV12_STATE_DIAGRAM_ROUTE_REFINEMENT_20261024.md` (current SHA-256 recorded in TASK_APPROVAL.md after this amendment).
- Scope includes correcting peer-review findings, redrawing crowded authored diagrams without on-canvas source labels, completing BM01/BM02 details, refreshing all four DOCX/PDF pairs, and conditional CI/Iteration 1/tag gates.
- Owner authorized CI preparation, Iteration 1 checks, and a `review-2` tag/BM02 run only after all gates pass; each diagram canvas must name its type. The hosted P4 gate is currently failed; no tag has been created.
- Project identifier `FA26SE225` and class/course identifier `SWP490` are being used with their evidence boundaries recorded in the source register. Proposed BM02 owners/due dates remain pending owner/team confirmation.
- Current working baseline used for report evidence: `dev@d0a754a2`; final publication commit and clean baseline are pending.
- Rev12 local outputs: Design Brief 6 PDF pages, Registration+BM03 10, consolidated Report 1–5+Tracking 100, Self-Review 6. All four DOCX packages parse and all 122 PDF pages rendered; no blank pages, 46 typed report figure captions, and no figure source captions. Registration+BM03 and all PDFs stay local.
- Diagram QA: 46-page editable Draw.io master (22 supplied-derived pages plus 20 state-machine and 4 activity pages). Supplied originals are unchanged; 16 source-attribution cells removed from derived canvases and PNGs. All 24 authored pages D23–D46 were individually inspected at full size; report gallery pages 52–97 were reviewed. No label/label, label/node, node/node, route/node, route/label, or route crossings. See `evidence/diagram-qa-rev12.json` and `evidence/diagram-master-qa-rev12.json`.
- CI/P4 gate remains failed and clean-tree/security publication checks are pending; do not create the tag or run BM02 on an unapproved tagged baseline.

- Lifecycle: COMPLETE (Rev10 authoring, visual QA, repository security validation and normal Git publication complete)
- Latest completed package revision: 10 (2026-10-24)
- Current revision: 10 complete
- Last completed historical package: 7 (2026-10-23)
- Approval: owner request and amendments are recorded in `approvals/TASK_APPROVAL.md`.
- Scope completed: four Review 2 submission dossiers, each in editable DOCX and PDF. Report 2's detailed Project Management Plan and time plan are integrated into the consolidated Report 1–5/Project Tracking dossier; no fifth standalone PM Plan is included in the submission set.

## Final deliverables

| Dossier | PDF pages | Artifact directory |
|---|---:|---|
| Registration + BM03 Record of Changes | 9 | `artifacts/submission_r2_rev10/` |
| Consolidated Report 1–5 + Project Tracking, including detailed PM Plan | 99 | `artifacts/submission_r2_rev10/` |
| BM02 Self-Review | 5 | `artifacts/submission_r2_rev10/` |
| BM01 Design Brief + Appendix A | 4 | `artifacts/submission_r2_rev10/` |

Rev10 contains exactly four dossier categories as DOCX/PDF pairs. BM01 sections 0–8 occupy pages 1–3 and Appendix A fits on page 4; its geometry is A4 with 2 cm margins and 11 pt body text. The full Registration+BM03 DOCX and all PDFs stay local because of personal contact data and validator rules.

## Evidence and limits

- Final Rev10 QA receipt: `evidence/metrics/final_package_qa_20261024_rev10.json`.
- Source register and source hashes: `SOURCE_REGISTER.md`; exact merge-source details: `evidence/notes/BRANCH_MERGE_RESULT_20261023.md` and `evidence/metrics/merged_branch_snapshot_20261023.json`.
- All 117 Rev10 PDF pages were rendered and visually inspected; final output hashes, DOCX integrity, page counts and diagram inventory are in the Rev10 receipt.
- Source baseline documented in reports: `dev@0a7ce768c153f2104cff930569c3eda6e484532c`. Package/runtime changes were committed as `9d4ca30a` and pushed to `origin/dev`; the `review-2` tag remains absent, so BM02 is an evidence-based draft, not a completed tagged-baseline run.
- Modal is selected; deployment settings and live endpoint are TBD. No application tests were run for this documentation task. No tag, deployment, provider call or reviewer approval is claimed.
- The public repository received the safe editable DOCX and Draw.io sources, scripts and records. The contact-bearing Registration+BM03 DOCX, all PDFs, rendered page images and raw Mermaid import logs remain local. FEAT-060 feature-owned validation evidence is committed; unapproved imagery and archives remain excluded.

Revision 6 outputs remain historical. Revision 7 fixes horizontal overflow and supersedes revision 6 for this submission request.

## Revision 8 planning checkpoint — 2026-10-24

- Lifecycle: AWAITING_OWNER_FILTER.
- Plan: Rev8 prepared; plan SHA-256 `326FE8D683C335347935404A8AD74C253EABEDB4EFAF10EF28666CFFDD34DD5D`; user authorization is recorded in `approvals/TASK_APPROVAL.md`.
- Scope: refresh four Review 2 dossier categories against SRS v3.3 and current project evidence; deliver each as DOCX and PDF (eight files total); use the supplied Draw.io diagrams only.
- Owner input needed before final authoring: filter the next-work list in `evidence/notes/OWNER_FILTER_CANDIDATES_20261024.md`; either provide the missing state-machine/activity Draw.io pages required by the guide or accept that the reports will identify those as missing.
- Current final outputs remain revision 7 in `artifacts/submission_r2_rev7/`. No revision 8 DOCX/PDF has been created.
- Current baseline is dirty `dev@0a7ce768c153f2104cff930569c3eda6e484532c`; FEAT-060 local implementation has separate UI/backend checks but no PostgreSQL-backed FE-to-BE acceptance run. Do not call it release-ready.
- No runtime code, application tests, tag, commit, push, deployment, provider call, or external publication occurred for this planning update.

## Revision 9 active checkpoint — 2026-10-24

- Lifecycle: IN_PROGRESS; current approved documentation scope is Plan Rev9. Rev7 remains the latest completed submission package.
- Plan: `plan/PLAN_REV9_CURRENT_STATE_AND_DIAGRAMS_20261024.md`, SHA-256 `F8DB72A34425B27AAEE2D12A9438ACA68DD6F9DE9B8816DC70285639F9EEEC93`; direct owner authorization and the page-level diagram clarification are recorded in `approvals/TASK_APPROVAL.md`.
- Owner selected exact registration source `[Downloads]/Phieu_FA26SE225_v1.2.docx`; its SHA-256 is identical to the prior `(1)` copy. Blank project/class metadata remains unconfirmed.
- Owner authorized exactly two missing diagram types: state machine and main-workflow activity. Mermaid sources are converted/imported into a seven-page editable Draw.io master (six state-machine pages covering session, admission and device states; one activity page). All seven pages have been rendered for visual review; no runtime claim follows from these design diagrams.
- The expanded candidate inventory with evidence, unknowns and dependencies is `evidence/notes/OWNER_FILTER_CANDIDATES_20261024.md`. Owner has not filtered N1–N9; final dossier authoring remains gated.
- No Rev9 Word/PDF package has been authored. The current deliverables remain Rev7 in `artifacts/submission_r2_rev7/`.
- No product code, app tests, tag, commit, push, provider call, deployment, or external publication is part of this Rev9 work.

## Revision 7 complete

The owner reported horizontal content overflow in the delivered PDFs. The table grid/first-row width mismatch was corrected and oversized report tables were reduced to the printable area. All four DOCX/PDF pairs were regenerated, all 66 pages were visually inspected, and the horizontal-bounds audit passed with no violations. The revised receipt and render inventory are referenced above.
