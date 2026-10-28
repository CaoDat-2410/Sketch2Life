# EV-063-15 — Detailed System Flows PDF and Draw.io Update

**Date:** 2026-10-27 (Asia/Saigon)  
**Feature:** FEAT-063 — Whole-repository architecture redesign  
**Plan:** Revision 22, approved for documentation artifacts only  
**Status:** Complete; source SRS and data register remain drafts

## Purpose and scope

Created a separate, detailed PDF of the system's operational and user activity flows, while keeping a single editable Draw.io master as the source for both the full package and the flow-only export. The flow pages were added to the existing architecture master; no second Draw.io file was created.

This work covers documentation and artifact generation only. It did not change product source code, database declarations or migrations, access live databases, run product tests/builds, call Modal/payment/AI providers, deploy services, or use real child data.

## Source basis

- Feature SRS `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.0-draft and `DATA_TABLE_REGISTER.md` v2.0-draft.
- Existing feature context, decisions, source register, architecture conventions, and repository table declarations.
- Supplied project reports and SRS/Software Design reference documents in the requested Document folder.
- Diagram conventions referenced from ISO/IEC/IEEE 29148, OMG UML 2.5.1, C4, and native Draw.io multipage diagrams.

The diagrams express the draft target and owner-confirmed decisions. They do not certify external provider capability, production hosting, legal readiness, prices, model quality, or live database state.

## Output artifacts

| Artifact | Pages | SHA-256 | Notes |
|---|---:|---|---|
| `owner-selected local document directory\Sketch2Life_SRS_Architecture_Diagrams.drawio` | 69 | `3d8f92c0ef3fb633f54f7fbda655cb3598a389ddad00bb645233e25bc8ed3e20` | Single editable monochrome master |
| `owner-selected local document directory\Sketch2Life_SRS_Architecture_Diagrams.pdf` | 69 | `f9a826d2ef3e2770277b8bc6a2598e281771ded5da55a4ba3f306f9211dfac57` | Full multipage package exported from the master |
| `owner-selected local document directory\Sketch2Life_System_Flows_Detailed.pdf` | 24 | `70256c143aa36df3fbc174c1d23fef1de55ec291e6ca6f903d45745b6732b812` | Flow index and 23 detailed flow pages exported from named master pages |

All pages are landscape, approximately 1210.1 × 854.9 pt. The flow-only PDF contains master page 45 as its index, followed by master pages 46–68. The 69-page master has 78 active target tables represented once and 48 legacy mappings in a separate read-only inventory, for 126 projected physical mappings per repository declarations. These counts are a design inventory and have not been validated against a live database.

## Detailed flow page map

| Master page | Flow PDF page | Flow |
|---:|---:|---|
| 45 | 1 | System flow index |
| 46 | 2 | Identity, authentication, authorization, and account recovery |
| 47 | 3 | Parent child profile and personalization context |
| 48 | 4 | Parent end-to-end StoryRun to video |
| 49 | 5 | Organization, class capacity, assignment, and roster |
| 50 | 6 | Teacher child profile creation and contextual data |
| 51 | 7 | Lesson upload, extraction, correction, and immutable revision |
| 52 | 8 | Lesson occurrence plan, activity approval, and revision pinning |
| 53 | 9 | Teacher AI Sketch Deck generation, review, presentation, and regeneration |
| 54 | 10 | Artwork, text/audio intake, Whisper transcription, and input review |
| 55 | 11 | VLM subject recognition, adult correction, and context approval |
| 56 | 12 | Story/storyboard generation, rewrite limits, and script confirmation |
| 57 | 13 | Compute budget and video quota admission saga across owners |
| 58 | 14 | Full story-to-video pipeline, scene validation, composition, narration, and safety |
| 59 | 15 | Durable AI jobs, attempts, retries, stale results, and reconciliation |
| 60 | 16 | Safety outcome, private playback, class audience confirmation, and regeneration |
| 61 | 17 | Subscription, class capacity, payment callback, renewal, and grace period |
| 62 | 18 | Monthly quota grants, top-up, FIFO usage, and expiry rules |
| 63 | 19 | In-app/email/push notifications and reminder delivery |
| 64 | 20 | Teacher reassignment, access fencing, and offboarding |
| 65 | 21 | Idle closeout, cancellation, completion, deletion, and retained ledger metadata |
| 66 | 22 | Activity catalog review, publication, custom activity, and revocation |
| 67 | 23 | Monitoring, alerting, provider incidents, recovery, and privacy-safe telemetry |
| 68 | 24 | Data inventory, expand/backfill/reconcile, cutover, and rollback |

The diagrams show main paths plus the relevant authorization checks, alternate outcomes, failure branches, immutable revision or hash boundaries, quota/compute effects, lifecycle effects, and record ownership. They preserve the one-child-per-StoryRun invariant and distinguish the Parent flow from the Teacher one-child sample-video flow. The video flow follows the supplied LTX-2.5/Modal concept, subject to technical benchmark and provider validation.

## Visual and file QA

- The Draw.io master was exported through the Draw.io CLI. PDF page counts were independently read from the resulting files: 69 full-package pages and 24 flow-only pages.
- `render_pdf_qa.py` rendered every PDF page at 1.5×: 69 full-package pages plus 24 flow-only pages (93 page renders total). The render inventory and page-size/hash summary are recorded in `evidence/flow_pdf_qa_20261027/PDF_RENDER_MANIFEST.txt`.
- Contact sheets were reviewed for all 24 flow pages and all 69 full-package pages. Full-resolution checks included the cover and representative video-pipeline, quota, and migration pages; the earlier 45-page package review is preserved in EV-063-14.
- Page titles and the ordered page subset were checked against the master page names. The PDFs contain no replacement glyphs in the text extraction check.
- Diagram fills, strokes, and fonts were checked to use only black, white, or no fill; no color palette is used. The checked Draw.io source is native and remains editable.
- Rendered diagrams are landscape; their page layouts fit the exported page bounds without observed clipping. Text remains legible at page view and readable at full PDF zoom.

## Constraints and outstanding gates

- The SRS and data-table register are still drafts; this artifact does not constitute owner approval of their requirements or data model.
- The ERD is a logical target based on repository declarations, not a reverse-engineered live schema. The 78/48/126 counts must be verified in a separately approved database inventory/migration task.
- Model versions and GPU performance, Modal transfer behavior, provider/payment integrations, production region/hosting, operational SLOs, legal/privacy requirements, costs and commercial values remain validation or approval gates.
- Mermaid drafts and the older 45-page package are historical. The current source of truth for this package is the 69-page Draw.io master and this evidence record.

