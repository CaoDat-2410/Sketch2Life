# Montessori profile form and workflow recovery plan

- Feature: FEAT-033
- Revision: 3
- Status: APPROVED
- Prepared: 2026-09-29
- Related work: FEAT-018 supervised mobile flow; FEAT-020 backend/request-scoped profile; FEAT-022 catalog; FEAT-029 SRS.

## 1. Objective

Correct the current profile/recommendation experience against SRS v1.6, diagnose and repair the observed context-options HTTP 422 failure with useful safe errors, reduce measured UI stalls, and make catalog improvements only where a reproducible Montessori coverage audit identifies a real gap.

## 2. Owner-confirmed decisions for this proposal

- Interests and dislikes are entered as free text and classified by AI (not restricted to the current fixed UI chips).
- The interest/dislike text represents a relatively stable preference declared by the adult, rather than only the child's momentary curiosity.
- AI-proposed concept tags must be shown to the adult for confirmation/editing before they affect recommendations.
- Keep the adult-confirmed topic from the drawing as the recommendation anchor; stable preferences may personalize ranking only among related, otherwise-eligible activities. Do not broaden to unrelated activities merely because a profile preference matches.
- Remove the current hard-coded “adult-confirmed progress” examples from this form until real, reviewable child activity history exists.
- Remove profile-level supervision-availability choices. Confirm an adult is participating in the session and enforce the supervision requirement for each candidate/activity.
- Ask readiness questions in the context of the activity instead of displaying the entire readiness catalog.
- Profile data remains session-only for this increment; no durable storage is authorized.

## 3. Scope

### A. Reproduce and fix the 422 / unreadable-response path

1. Reproduce the versioned POST using the same shape produced by the mobile client, capture sanitized validation locations/codes, and identify the exact rejected field/header/contract condition before changing the schema.
2. Fix the actual producer/contract mismatch and add backend contract plus mobile API regressions. Do not weaken validation to make the request pass.
3. Return a typed, versioned, safe validation failure compatible with `MobileWorkflowResultV1`; show an actionable adult-facing message. Record only request ID, route, validation code and bounded field path. Never log or return raw profile text, child data, tokens, or raw submitted values.
4. Ensure unrelated non-JSON/proxy/network failures remain distinguishable from request validation errors; do not label every backend error “unreadable.”

### B. Redesign the initial child-profile form

1. Replace interest/dislike template chips with bounded Vietnamese text inputs and clear/edit controls. Keep the data volatile and scoped to the current session.
2. On explicit submission only (never per keystroke), send one bounded text-classification request through a backend-owned contract. Proposed implementation reuses the already configured Qwen3-VL runtime on the trusted backend/Lightning path; mobile must not call a model provider directly, and the implementation must not load a second copy of Qwen. Confirm model/runtime feasibility and the contract boundary before coding; if reuse is not possible, stop for a revised plan rather than silently adding a new model/service.
3. Classifier output is restricted to reviewed catalog concept IDs, confidence, and an `UNMAPPED` outcome. Show proposed tags to the adult and require confirmation/editing before any tag affects ranking. It cannot generate activities, change the Gate-A-confirmed drawing topic, widen candidates to unrelated topics, change objective/activity IDs, infer diagnosis/personality/emotion/mental state/readiness, or bypass deterministic rules. Unmapped or unconfirmed text is not silently treated as a recognized preference.
4. Bound text length/count, explain not to enter names or sensitive/medical details, keep raw text only for the active session, and exclude it from logs, analytics and evidence. Classification and activity ranking are separate: deterministic age/readiness/prerequisite/material/supervision/safety gates run before ranking.
5. Keep the agreed editor at child selection/initial profile only; no mid-flow profile editor. Show explicit loading/progress during classification and make retry user-initiated and bounded.

### C. Remove misleading profile fields and make Montessori context specific

1. Remove the three fabricated progress chips and associated role/date controls from this form. Do not imply the demo has historical observations. Adult-confirmed history can return only with a real, consented, versioned observation/history source and a separately approved scope.
2. Remove `adult_supervision_available` from the editable child profile. Confirm the session's adult participant explicitly; show and enforce the exact supervision required by each activity at review/handoff. Age 0–3 continues to require direct caregiver supervision (SRS BR-013). The UI cannot lower a catalog safety requirement.
3. Replace the global readiness chip wall with a two-phase, context-limited flow: first obtain a small, unranked set of age/topic-compatible candidates and their exact authored readiness criteria; ask the adult only about criteria that are prerequisites for those concrete activities; then apply all hard eligibility gates and rank only eligible candidates. Readiness is an observed prerequisite, not a score, diagnosis, or generalized label for the child. If an activity has no readiness prerequisite, do not ask a readiness question for it. If a required criterion is unknown/not observed, exclude only activities that depend on that criterion and keep eligible alternatives; do not fail the whole recommendation flow. “Can do with adult support” satisfies a criterion only when the authored activity explicitly permits that support; never silently treat unknown as ready. Do not present provisional items as final recommendations, and do not return the full catalog to the UI.
4. Preserve material availability as a hard constraint. Reuse a searchable/capped selection surface or ask only for materials required by the relevant candidate set; do not silently default a required material to available. Keep selection and “not confirmed” semantically distinct.
5. Explain in plain Vietnamese that readiness is an observed prerequisite for a concrete activity—not a label, diagnosis, achievement score, or inference from the drawing.

### D. Catalog audit and targeted expansion

1. Re-run and extend the catalog report across concept/objective × age band × readiness/prerequisite/material/safety metadata and eligible candidate counts after hard filtering.
2. Compare measured gaps with FEAT-022 tiers and the SRS 0–12 bands. Add only meaningful, missing, authored Montessori activities or missing reviewed metadata; each addition requires source/provenance, objective, age adaptation, observable outcome, prerequisite/readiness, material/substitute, supervision/safety rationale, reviewer/status and version.
3. Preserve the approved-only runtime rule and existing activity identity/version. AI may classify/rank allowlisted records but may not author catalog entries. Report pre/post coverage and never equate 300 records or `review eligible` with production Montessori qualification.

### E. Responsiveness and integrated verification

1. Measure a baseline on a connected, identified Android emulator/device: profile-screen cold mount, text input responsiveness, list scroll, classification wait, recommendation response and JS/native frame stalls. Distinguish emulator slowness from app regressions.
2. Remove the unnecessary long static chip wall, isolate/memoize high-churn profile controls where profiling justifies it, avoid network/model work during typing, and limit repeated renders. Do not introduce an unapproved UI/runtime library.
3. Measure the same scenarios after changes. Proposed acceptance: no network/model call while typing; at most one classifier inference per explicit submit; no second Qwen model load; p95 text-input response under 100 ms on the agreed emulator; no red screen/uncaught JS exception; preserve a visible bounded loading state for remote work. If the target cannot be met, report measured traces and obtain direction rather than hiding the loading state.
4. Verify backend contract/unit tests, mobile typecheck/UI tests, catalog validation/coverage report, repository security validator and a real connected Android smoke for session setup → Gate A → free-text classification → contextual readiness → final candidates → Gate B. Store sanitized logs and measurements in this feature's `evidence/` only.

## 4. Acceptance criteria

- **AC-01 — Root cause:** The exact reason for the observed 422 is reproduced and documented with sanitized validation code/path; the corrected valid profile request succeeds and invalid inputs return a stable typed failure.
- **AC-02 — Error clarity:** A validation rejection is never shown as “Backend returned an unreadable response”; the message is safe and actionable, with no raw request values exposed.
- **AC-03 — Free-text interests:** An adult can enter/edit/remove adult-declared relatively stable interest and avoid-topic phrases without fixed chips. The adult confirms/edits proposed tags before they affect recommendations; ambiguous/unmapped/unconfirmed phrases are not silently used. They can only personalize ranking within candidates related to the Gate-A-confirmed drawing topic.
- **AC-04 — AI boundary:** Classification runs only after an explicit adult submit, once per submitted revision, through a backend-owned contract; reviewed tags require adult confirmation; it does not duplicate-load Qwen or generate activities and logs no raw text.
- **AC-05 — No fake history:** The current profile form contains no prefilled progress examples or claims that the system knows what this child has accomplished.
- **AC-06 — Supervision:** No selectable supervision-availability field remains in the child profile. An adult participant is confirmed; each activity's authored requirement is displayed/enforced; ages 0–3 require direct caregiver supervision.
- **AC-07 — Contextual readiness:** No full readiness catalog is shown or sent to mobile. Adult questions come only from readiness prerequisites attached to a bounded unranked age/topic candidate set; activities without prerequisites do not trigger extra questions. A missing/unknown answer blocks only activities requiring that criterion, not unrelated eligible alternatives. `WITH_SUPPORT` counts only if the authored criterion allows it. Final filtering/ranking follows the SRS hard-rule order.
- **AC-08 — Catalog integrity:** All new or changed catalog records are provenance-backed, reviewed, versioned and linted; coverage report shows measured pre/post gaps; no runtime-generated activity is introduced.
- **AC-09 — Responsiveness:** Results are measured before/after on an identified connected emulator; no classification request fires during typing; p95 input response is <100 ms or a deviation is documented for owner review; no uncaught JS error occurs.
- **AC-10 — Flow:** End-to-end Android smoke completes the revised recommendation flow with backend/Metro connectivity and logs sufficient to distinguish validation, no-match, network and classifier failures without exposing child data.
- **AC-11 — Security/evidence:** `python tools/validate_repository_security.py` passes before any later commit/push; feature-local evidence contains no real child data, secrets, credentials or raw free text.

## 5. Non-goals and constraints

- No durable child profile, history, progress, or raw interest storage; no database/storage selection; no Firebase Storage/Firestore/Realtime Database.
- No model training/download, a second Qwen process, mobile-held AI credentials, unrestricted model output, or AI-generated activities.
- No inferred psychological, clinical, emotional, personality, readiness, or mastery labels.
- No weakening of SRS age, consent, adult participation, readiness, prerequisite, material, supervision or safety gates.
- No changes to unrelated Pixi/SAM/video flows, no commit/push, and no broad cleanup of existing unrelated worktree changes.

## 6. Risks, dependencies, and gates

- **422 cause unknown:** existing logs omit sanitized Pydantic issue paths; reproduce before editing contracts.
- **AI latency/runtime:** text classification may add wait time and interact with L4/Qwen memory. Reuse the existing loaded model path only; measure cold/warm latency and reject duplicate model loading.
- **Free text privacy:** prompt/input caps, no raw logging, adult-facing entry guidance and no persistent storage are mandatory.
- **Pedagogical accuracy:** classifier is not the Montessori recommender. Taxonomy mapping and added activities require source/reviewer evidence; safety/readiness remain authored deterministic rules.
- **Readiness flow:** service/API may need an additive versioned two-phase contract. Resolve any project-level contract conflict and record an ADR before implementation; do not silently break frozen V1 contracts.
- **Device verification:** no emulator was connected during audit; implementation acceptance requires a real connected test device/emulator and measured baseline.
- **Approval gate:** this plan changes the scope of the prior FEAT-018/020/030 approval. The project owner explicitly approved revision 3 on 2026-09-29; see `approvals/TASK_APPROVAL.md`. Implementation is limited to this revision.

## 7. Work sequence

1. Capture the sanitized failing contract and identify the 422 field/path.
2. Confirm/version the text-classification and two-phase readiness contracts; record any necessary ADR.
3. Fix typed validation handling and add backend/mobile regression tests.
4. Implement the input, classifier boundary, adult/supervision confirmation and contextual readiness UI/API.
5. Run the coverage audit; author only approved gap-closing catalog changes.
6. Profile and improve UI responsiveness; run backend, mobile, catalog, security and connected-Android gates.
7. Record evidence, decisions, context and status in FEAT-033; review full diff. Commit/push only if separately requested.

## 8. Benchmark-derived design rationale

The public product/help documentation and Montessori pedagogy benchmark is recorded in
`evidence/notes/MONTESSORI_FORM_BENCHMARK_20260929.md`. Its findings reinforce these plan constraints:

- Make actual activity/lesson and objective—not a static child-profile checkbox—the unit of progress/readiness evidence.
- Treat scope-and-sequence as a searchable, adaptable framework; do not render the full readiness catalog as the form.
- Separate direct observation from adult interpretation. Interest is a signal, not a diagnosis or an override for prerequisites/readiness/safety.
- Present AI topic classifications as bounded suggestions that require adult correction/confirmation before use (owner-confirmed).
- Do not claim “mastered” from a selected interest, finished screen flow, or single unverified event. The current demo has no child history source, so the hard-coded progress examples stay out.
- Keep the adult-confirmed drawing topic as the primary recommendation anchor; profile preferences cannot redirect the child to an unrelated catalog topic.
- Ask readiness only when a concrete candidate has an authored prerequisite. An unknown observation excludes only candidates that depend on it; no-prerequisite and otherwise-eligible alternatives remain available.

The cited vendors' public product pages are examples of software workflows, not normative Montessori standards. The controlling requirements remain the owner-approved SRS, ADRs and this feature's approved scope.
