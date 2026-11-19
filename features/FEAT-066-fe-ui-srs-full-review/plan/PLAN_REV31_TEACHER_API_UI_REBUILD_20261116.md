# Teacher API integration and SRS UI rebuild plan

- Feature: FEAT-066 — Web SRS full review
- Plan revision: 31
- Status: **PLANNED — AWAITING IMPLEMENTATION APPROVAL**
- Date: 2026-11-16
- Scope: Teacher web only; planning and source-level API crosswalk

## 1. Goal

Rebuild the Teacher web workspace around the end-to-end Teacher flow in the canonical SRS, wiring each screen only to a backend contract that is present, role-authorized, and semantically compatible. Group APIs by the work a teacher performs; do not create one page per HTTP verb.

The flow is: authenticate and resolve the Teacher assignment → work with assigned classes and consent-filtered roster → author or import a lesson → review and pin an immutable lesson version → create an occurrence and plan → optionally request a Sketch Deck → let the server select one eligible child → review and confirm the sample input/script → follow job and safety states → receive a short-lived playback authorization → explicitly confirm classroom projection and close out.

Where a required contract is absent or does not match the SRS, the screen must explain the dependency and remain non-actionable. It must not simulate a successful action or substitute a Parent, demo, classroom-runtime, or synthetic-pilot endpoint.

## 2. Requirement and code baselines

| Source | Baseline | Use |
|---|---|---|
| Product SRS | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md, v2.7-draft Rev60, SHA-256 70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B; unsigned | Canonical working requirements per docs/context/SRS_AUTHORITY.md; §§1–31 are target requirements; §32 is as-built evidence. |
| Backend/API source | origin/dev 1c9148e88600a101887e477541c4c4893ba1c7df | Static inspection of route code, guards, contracts and router composition. No live endpoint/runtime check was made. |
| Teacher UI source | codex/fe-ui-web-remediation HEAD b72f9e46f9c63e019807d7c4a2c309b0aa46a133 | Current route/API wiring and visual-system inventory. |
| Prior feature records | FEAT-066 revisions 28–30 and older evidence | Historical task records only. They mention Rev68; this plan uses Rev60 under the current authority instructions and does not rewrite those records or either SRS. |

Relevant SRS sections: §§3, 5.2, 7.3 (FR-T-01–20), 9.6, 19, 21.1, 21.5–21.6, 31.4–31.8, UC-03/04/05/17, AC-56, and §14.1 OI-17. The SRS remains unsigned. Q-01 selection details, Q-13 identity/permission resolution, Q193 quota-purchase policy, and OI-17 screen/interaction sign-off remain open; the UI plan must not decide them.

This is a source-level plan, not proof that any endpoint is deployed, configured, or available in a given environment. The current origin/dev OpenAPI projection is not treated as a complete implementation inventory.

## 3. Current API-to-screen crosswalk

“Present” means the route and relevant behavior are visible in the inspected origin/dev source. “Wired” means the current Teacher UI calls the route through its adapter. Neither label asserts production runtime readiness.

| Teacher surface | Relevant API in origin/dev | Current UI status | SRS fit and planned disposition |
|---|---|---|---|
| Sign-in and role gate | GET /api/auth/v1/me; GET /api/be1/v1/organizations/{organization_id}/me | Shared auth checks the role and Teacher assignment. Teacher pages also reload assignment data before using scoped views. | Retain verified Firebase identity and server authorization. Every page remains assignment-bound; client filtering is an extra display guard, not authorization. |
| T01 — workbench | GET /api/be1/v1/organizations/{organization_id}/me; GET .../classes; GET /api/lesson-library/v1/organizations/{organization_id}/lessons | Wired for assigned classes and lesson list. Session/occurrence, quota, inbox and history summaries have no Teacher contract. | Rebuild as a focused next-action/work queue from real assigned classes and lessons. Remove or keep unavailable any synthetic KPI, unread count, quota chip, activity feed or run state. |
| T05 — assigned classes, roster and consent | GET .../classes; GET .../classes/{class_id}/profiles; GET .../classes/{class_id}/consents under /api/be1/v1/organizations/{organization_id} | Wired for read-only assigned classes, profiles and consent state. The backend profile read can fail closed with 409 CONSENT_NOT_EFFECTIVE. | Retain exact assignment/scope checks. Show only server-returned, consent-effective data and handle a consent conflict by withholding roster data. Do not add Teacher handoff, transfer, arbitrary child selection or synthetic data. |
| T05 — profile creation/enrollment | POST .../classes/{class_id}/profiles exists in BE1 | Not used by the production Teacher page; the handler is explicitly limited to local/test synthetic-pilot configuration and tags records SYNTHETIC_DEV. | Do not wire it as FR-T-04 production profile creation. A real managed-profile/enrollment contract is a backend dependency. |
| T02 — lesson library and authoring | GET/POST /api/lesson-library/v1/organizations/{organization_id}/lessons; GET/PATCH/DELETE .../lessons/{lesson_id}; POST .../lessons/{lesson_id}/access-grants | Core list/detail/create/update/archive and public-review request are wired. PATCH/DELETE use If-Match; creates and grant requests use idempotency keys. | Rebuild around draft, immutable version, approval and visibility states. A Teacher request for public review is not publication: show pending Manager decision until the Manager contract returns approval. Keep cursor paging, exact revision handling and server errors. |
| T03 — document import | POST .../lessons/{lesson_id}/upload-sessions; GET/DELETE /api/lesson-library/v1/upload-sessions/{upload_session_id}; PUT .../parts/{part_number}; POST .../complete; source-document and revision GET routes | Upload, resume/status, completion and read-only extracted-revision preview are wired. Availability still depends on storage, scanner and parser configuration. | Build upload/review as a single guided flow. Enforce PDF/PPTX/DOCX, 25 MB and 100-page/slide limits; clearly reject encrypted documents and OCR scans per the SRS/API response. Preserve file provenance and show quarantine/parse/review states. Do not send the raw document to the model. |
| T03 — confirm reviewed extraction into a lesson version | POST /api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/versions exists in backend source and accepts a source revision plus structured lesson content. The service creates a DRAFT lesson version and changes the linked document revision to CONFIRMED. | Not exposed by backendApi or called by the Teacher screens. | Candidate integration after contract review. Confirm that edit/correction, confirmation, revision lineage and resulting review state meet FR-T-07. Do not label the lesson public/approved; the created lesson version is DRAFT. |
| Manager approval handoff | GET /access-grants and POST /access-grants/{access_grant_id}/decision are Manager-guarded; Teacher can create a grant request. | Teacher only requests review; Manager decision belongs to the Manager role. | Keep the boundary explicit. No Manager decision UI or implicit public access in Teacher. |
| T13 — AI lesson suggestion, Sketch Deck and visual candidate | POST /api/teacher/v1/organizations/{organization_id}/ai/lesson-plan-suggestions; .../sketch-decks; .../lesson-visuals | Calls are wired from a standalone Teacher workflow. Backend requires Teacher role and Modal development configuration; calls are synchronous and return draft outputs. Current client manufactures plan_revision_ref from request_id; outputs are not persisted as a lesson/occurrence revision. | Reconcile this route with the canonical SRS before connecting it to production lesson flow. Persist/review the plan first and bind by immutable version/hash. Sketch Deck is opt-in and contains no child/profile/artwork input. Do not represent a request ID as plan lineage, a draft as approved, or a generated visual as a saved lesson asset. If async job/status/timeout semantics are not adequate, keep the feature unavailable until a compatible contract exists. |
| T04 — occurrence, lesson plan, activities and optional deck | SRS target resource group in §9.6 includes lesson occurrence/plan/activity and occurrence-bound Sketch Deck. No matching Teacher occurrence/plan/checklist API is exposed in the current FE adapter. | Explicitly unavailable route. | Backend contract required before functional UI. Pin the exact lesson version/hash; support activities and safety checklist; show Sketch Deck only when enabled and bind its revision to the plan hash. Changing the plan must stale the old deck. |
| T06 — sample StoryRun | SRS requires server-side random selection of exactly one eligible child, then Teacher confirmation of child/context, transcript/subject and script. No compatible Teacher occurrence-selection/StoryRun API is present in the current adapter. | Explicitly unavailable route. | Backend contract and owner decision Q-01 required. No arbitrary roster picker, fallback child, Parent story endpoint, StoryRun-lite demo, or BE1 session/lobby mapping. Keep one occurrence/activity/child/run and one successful sample invariant. |
| T07 — playback and projection | SRS requires a safe-ready state, short-lived playback authorization, explicit projection confirmation, and lifecycle closeout. No matching Teacher playback-token/projection/complete/cancel/reconciliation API is present in the current adapter. | Explicitly unavailable route. | Backend contract required. Do not use generic media/demo playback routes as the Teacher product flow. |
| T08/T11 — Teacher settings and profile | /api/auth/v1/me resolves role only; no Teacher profile/settings read/update API is wired. | Explicitly unavailable. | Show only identity fields actually returned by authenticated contracts. Profile editing and preferences wait for a typed endpoint. |
| T09 — history, job and quota | No Teacher occurrence/StoryRun history, status/reconciliation, or school-scoped video-quota methods are in the current adapter. Generic/demo/fixture job routes are not a substitute. | Explicitly unavailable. | Backend contracts required. If/when present, show organization quota only (not a per-Teacher pool); do not expose purchasing until Q193 and authorized offers are decided. |
| T10 — inbox | No Teacher inbox/read-state API is wired. | Explicitly unavailable. | Do not show unread badges or local fixture messages as server state. |
| T12 — activity catalog and occurrence checklist | Structured lesson content can contain activities. A versioned Activity Catalog and occurrence checklist API are not wired. | Embedded lesson content only; standalone screen unavailable. | Reuse the exact pinned lesson activity when available. Do not imply catalog search or checklist completion without the corresponding contract. |

### API boundary decisions for this plan

- The origin/dev BE1 session, lobby/join, canvas, artifact and gallery endpoints are classroom-runtime or other resource flows. They are not aliases for the SRS lesson occurrence, one-child StoryRun, playback or projection contracts.
- Parent profile/story routes and the conditionally mounted /api/story-runs lite demo are not Teacher product contracts.
- Lesson Library route presence does not guarantee parser/scanner/storage configuration. The current app initializes those dependencies as unconfigured unless environment setup supplies them.
- The Teacher AI router is present, but its Modal development guard and synchronous output do not establish a production-ready job contract.
- No live backend, credentials, child records or provider were used to make this crosswalk.

## 4. Screen and interaction plan

1. **T01 Workbench:** one clear next action; real assigned classes and lesson drafts; compact, source-backed lists. No KPI grid, fake recent activity, quota chip or unread count.
2. **T05 Classes and roster:** assigned classes only; detail view checks the exact Teacher assignment; consent/purpose is visible without exposing data outside its purpose. No Teacher transfer/handoff action.
3. **T02 Lesson library/editor:** paginated list, draft editor, version/ETag-aware save, archive confirmation, and a distinct request-review state. Public access only after Manager approval.
4. **T03 Import and extraction review:** choose an existing draft lesson, validate file locally, show upload progress/resume and backend scan/parse states, review structured extraction and provenance, then create a version only through the confirmed contract. Explain unsupported OCR/encryption responses in plain Vietnamese.
5. **T13 AI assist:** place suggestions within the persisted lesson authoring flow rather than presenting an isolated success path. Teacher reviews and edits structured draft. Deck generation has a separate explicit opt-in and exact plan revision/hash. AI errors retain the draft and show a safe retry only when the request contract makes retry safe.
6. **T04 Occurrence and plan:** design the intended screen sequence, but leave create/save actions blocked until occurrence, plan, activity checklist and deck lifecycle contracts exist.
7. **T06 Sample run:** design steps for server selection → teacher confirmation → camera/upload and text/audio idea → transcript and subject review → script/storyboard review/confirmation → job/safety status. Never show a child chooser. Keep run creation blocked until all required endpoints and Q-01 policy are defined.
8. **T07 Playback/projection:** show only safe-ready content and a short-lived server token; require an explicit confirm projection action and truthful completion/cancel/reconciliation state. Block the flow until API support exists.
9. **T08–T12 supporting screens:** retain a truthful unavailable view or scope information into the relevant Teacher workflow until profile, settings, history, inbox, catalog and checklist contracts arrive.

Navigation should reflect the actual Teacher flow: **Bàn làm việc → Lớp → Giáo án → Buổi dạy → Lịch sử**. Optional Sketch Deck and sample-video actions belong inside the relevant occurrence, not as unrelated dashboard shortcuts. If the current route IDs must remain stable for deep links, preserve them while changing labels and grouping.

## 5. UX, visual and accessibility rules

Apply the relevant guidance from design-taste-frontend, ui-ux-pro-max, frontend-design, senior-frontend, ui-design-system, senior-architect, task-decomposition and sketch2life-harness:

- Treat Teacher as an authenticated learning workspace, not a marketing landing page. Keep Vietnamese-first labels and a clear next action on each workflow screen.
- Reuse the current approved paper/crayon tokens and shared shell. Improve hierarchy and spacing within that system; do not introduce a parallel design system or add dependencies.
- Use a purposeful workbench and readable lists/forms instead of generic card grids. Keep instructional content short and grounded in real product behavior.
- Every API screen defines loading, empty, retryable error, access denied, not found, stale revision/conflict, validation, rate/quota limit, unavailable service and success states as applicable. Convert backend errors to safe, actionable Vietnamese copy; do not reveal stack/provider/SQL details.
- Mutations use stable idempotency keys for retries where the contract requires them; edits/archive/review use current If-Match revisions. Never automatically retry a non-idempotent command after an unknown outcome.
- Keep auth tokens, child profile/consent data and raw lesson files/text out of browser persistence. Any upload resume record stores only the minimum opaque session reference and non-sensitive recovery metadata; audit the current local-storage behavior before altering it.
- Keyboard access, visible focus, semantic labels and error association are mandatory. Aim for 44×44 px interactive targets, readable contrast, reduced-motion support, and no horizontal overflow at 390 px.
- Validate later at 1440×900, 1024×768, 768×1024 and 390×844, plus keyboard-only navigation. Capture screenshots and observations under FEAT-066 evidence.
- Do not generate new visuals as part of this plan. If implementation needs visual assets, follow the repository flow: create in assets/generated/, record provenance, obtain visual approval, then promote through approved/applied locations.

## 6. Ordered work breakdown

Estimates are frontend person-days for planning only. Backend contract/configuration work is called out separately and is not estimated because ownership and scope are not yet approved.

| ID | Work | Depends on | Deliverable / acceptance | Estimate |
|---|---|---|---|---:|
| P0 | Freeze Rev60 route-to-SRS/API crosswalk and exact role/endpoint guards | This plan; canonical SRS | Every Teacher UI action is marked wired, backend-present-but-unwired, conditional, or missing; no inferred contract. | 0.5–1 d |
| P1 | Define Teacher information architecture and shared state/component requirements | P0; reuse existing web tokens/shell | Screen map, nav labels, state matrix and responsive rules; no new design system. | 0.5–1 d |
| P2 | Rebuild T01 and T05 around assigned classes and real consent-scoped data | P1; existing auth/BE1 reads | No fixture metrics or handoff actions; unauthorized/out-of-assignment and consent-conflict paths fail closed. | 1–2 d |
| P3 | Rebuild T02 Lesson Library/editor | P1; current lesson CRUD/grant routes | Paging, save/archive conflicts, draft/version lineage and pending Manager review are explicit and API-backed. | 1.5–2.5 d |
| P4 | Rebuild T03 upload, recovery and extraction review | P3; Lesson Library runtime dependencies; confirm version semantics | Limits and scan/parse states are handled; resume avoids sensitive browser persistence; confirmation creates a correctly linked immutable version or stays blocked. | 2–3 d |
| P5 | Rework T13 AI assist into the persisted lesson workflow | P3/P4; confirm Modal/runtime, output policy, persistence and job/timeout contract | No fake revision ref; reviewed output is attached to a real version/hash; explicit opt-in and draft/safety states. If these prerequisites fail, retain unavailable status. | 1–2 d |
| B1 | Specify and implement missing typed contracts: production Teacher profile/enrollment; occurrence/plan/activity/checklist/deck; server child selection and StoryRun; quota/job/reconciliation/playback/projection/lifecycle; profile/settings/history/inbox as prioritized | Product/owner decisions Q-01/Q-13/Q193 where applicable; SRS scope | Versioned request/response/error, authorization, idempotency, revision/hash, lifecycle, audit and privacy contracts, with BE owner sign-off. This is a separate backend plan; effort TBD. | TBD |
| P6 | Build T04 occurrence, plan and optional Sketch Deck UI | B1; approved design/sign-off OI-17 | Exact lesson version/hash is pinned; no stale deck; checklist and opt-in states match backend. | 2–3 d |
| P7 | Build T06 single-child sample flow | B1; Q-01 owner decision | Server chooses one eligible child; teacher confirms; one occurrence/activity/run/sample invariants remain visible and enforced by server. | 3–5 d |
| P8 | Build T07 playback, projection, completion/cancel and reconciliation UI | B1; P7; playback/safety contract | Only safe-ready media plays; token is short lived; projection and lifecycle outcomes come from server. | 2–3 d |
| P9 | Complete T08–T12 only for approved contracts | B1; relevant role/product decisions | No fixture profile, inbox, history, quota, catalog or preference state. Prioritize with owner after the core lesson-to-run path. | 2–4 d |
| P10 | Manual UI, browser and accessibility review; feature-local evidence and closeout | Implemented phases; visual review approval | Required viewports, keyboard flow, runtime console, network boundary, loading/error states and screenshot observations recorded. No application tests unless separately requested. | 1–2 d |

**Planning range:** about 7–12 frontend days for the currently supportable T01/T02/T03 work plus a conditional T13 assessment, and a further 10–17 frontend days for future missing-contract flows, plus backend work of unknown size. This is an initial sizing, not a delivery commitment. Phases P6–P9 cannot start as functional API integration until B1 contracts and required owner decisions are ready.

## 7. Acceptance criteria

- **AC1 — SRS trace:** every Teacher navigation item, visible command and screen state maps to Rev60 sections/FRs and one of: an implemented compatible API, a backend-present-but-unwired route requiring review, a conditional development API, or an explicit missing contract.
- **AC2 — identity and scope:** sign-in and all protected actions use verified identity and server role/class/organization authorization. UI filtering is never treated as a security check.
- **AC3 — lesson provenance:** lesson drafts, source document, extraction revision, immutable lesson version and review grant remain distinct and linked by exact IDs/version/hash. A Teacher grant request is never shown as Manager approval or public publication.
- **AC4 — safe import:** file limits and unsupported encrypted/OCR cases are clear; upload lifecycle states come from the server; raw source and child data are not sent to AI or browser persistence.
- **AC5 — AI honesty:** generation is explicit and optional where required; output is draft; generation cannot proceed against a locally invented revision ID or unpersisted/stale plan; provider/runtime gaps remain visible.
- **AC6 — one-child run boundary:** no arbitrary child picker or fallback exists; selection and sample claim come from the server under an owner-approved Q-01 policy; one occurrence has at most one successful sample.
- **AC7 — playback and lifecycle:** play/projection/complete/cancel actions require their corresponding verified server states and short-lived authorization; unknown outcomes surface reconciliation rather than fabricated success.
- **AC8 — UI quality:** Vietnamese-first hierarchy, existing tokens, responsive layout, keyboard/focus/contrast/reduced-motion support, 44×44 px targets where applicable, and clear loading/empty/denied/conflict/error states pass manual review.
- **AC9 — evidence and approvals:** implementation screenshots/observations live in FEAT-066 evidence; asset provenance/visual approval is followed if assets are needed; exact implementation approval is recorded before code changes.
- **AC10 — scope discipline:** Teacher only in this first role plan; Parent/mobile, School Manager/Admin implementation, backend/API changes, policy decisions, new dependencies, tests, commit and push are separate authorization items.

## 8. Risks and open decisions

1. Rev60 is the canonical working SRS but unsigned. Product owner sign-off and the open items remain visible; this plan does not close them.
2. Q-01 leaves child eligibility, consent inputs, exclusions, reselection, no-eligible response and evidence open. No T06 implementation may guess these.
3. Q-13 leaves identity/permission resolver details open. UI cannot replace server-side role and scope enforcement.
4. Q193 leaves purchase offer/actor/scope terms open. This plan covers a future organization-scoped quota display only after a contract; no purchase flow.
5. OI-17 calls for product/design/accessibility review of key Teacher screens before implementation. This plan is not that visual approval.
6. Several route modules exist in origin/dev but runtime service dependencies are configured by environment. Static presence must not be reported as deployed availability.
7. Current T13 UI creates local pseudo-lineage and the Modal endpoints return draft outputs synchronously. Persistence, immutable lineage, timeout/retry and job-state compatibility are unresolved.
8. Existing FEAT-066 history includes a Rev68 task baseline. Preserve those records as historical; use Rev60 for new requirements under the current authority instructions.

## 9. Implementation gate and current disposition

This document authorizes planning only. No source code, API contract, visual asset, task approval record, commit or push is part of this revision. Keep implementation at **AWAITING_APPROVAL** until the owner approves a specific implementation scope and the root approvals/TASK_APPROVAL.md record is updated. The unsigned SRS and all owner-open decisions remain unchanged.
