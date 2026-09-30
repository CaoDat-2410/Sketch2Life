# FEAT-033 — Montessori profile form and workflow recovery

Completion audit: phase-one candidates are selected using stable activity IDs and family
deduplication without relevance ranking. The server recomputes the same shortlist, applies adult-
confirmed readiness/material/supervision hard gates, then ranks survivors. An adversarial test
covers the pre-gate ranking failure. Catalog audit numbers and recommendation preparation enums
now fail safely on malformed values. Latest integrated full backend suite: 1,650 passed, 10 skipped
(one optional-NumPy SAM regression is skipped by the local virtualenv); focused mypy,
Ruff, mobile UI tests and TypeScript pass. See `FEAT033-EV-20260930-09`.

Remaining gates: successful external Lightning classifier and full Android Gate-B smoke; qualified
Montessori review before content changes; and a comparable native input-to-presented-pixel trace
for AC-09. No remote deployment or repository commit/push was performed.

- Status: IN_PROGRESS
- Owner: Project owner
- Goal: Align the child-profile/recommendation UI with the approved SRS, remove misleading inputs and full-catalog presentation, diagnose the profile request rejection, and address measured mobile responsiveness issues.
- Scope: Session-only adult-entered interests/dislikes with bounded AI classification; remove the fake progress examples; remove profile-level supervision choices while preserving adult-presence and activity-specific safety rules; ask only context-relevant readiness questions before final ranking; close the `/p1/context-options` validation/error-reporting gap; audit and selectively improve catalog coverage.
- Non-goals: Durable profile/history writes, changing consent/retention/auth/storage architecture, inferring a child's psychology or readiness from image/audio, model training/downloads, AI-authored activities, changing Gate A/B meaning approval, or committing/pushing.
- Dependencies: SRS v1.6 (`features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md`); current FEAT-018 flow; FEAT-020 request-scoped profile contract and recommender; FEAT-022 catalog governance; ADR-0010 session-only profile boundary.
- Risks: Text classification adds inference latency and may involve child-related data; classifier output must be constrained to reviewed IDs and never bypass deterministic eligibility. The historical 422 body is unavailable, though a sanitized contract replay reproduced the material-ID mismatch. Catalog count alone does not prove Montessori qualification. An Android AVD is now connected; a valid pre-change and input-to-paint latency trace are still unavailable.

## Context snapshot

The owner supplied five screenshots showing (1) a selectable “adult supervision available” profile field, (2) fixed interest/dislike chips, (3) three hard-coded adult-confirmed progress examples, (4) the full readiness-choice list, and (5) “Backend returned an unreadable response.” The user then chose AI classification for free text, removal of progress from the current form, and activity-specific readiness questions with adult participation confirmed in-session.

The SRS requires adult participation and supervision, direct caregiver supervision for ages 0–3, and hard filtering for age/readiness/prerequisite/supervision/material/safety before ranking (BR-001, BR-009, BR-011, BR-013). It treats progress/feedback as adult observation/history, not a handful of invented child accomplishments (BR-023; B7 Observation/Feedback and SessionHistory). Only reviewed catalog entries may be ranked (BR-010).

The historical production request body is unavailable, so its exact submitted value cannot be reconstructed. A sanitized replay of the current mobile-compatible V2 payload reproduced the contract defect: candidate catalog entries emitted `MAT_…` material IDs while profile validation accepted only `GMAT-…`. The bounded validation path was `child_profile.available_material_option_ids` (`value_error`). Validation now accepts only the two existing catalog ID namespaces, and contract tests cover valid V2 requests plus safe typed failures. The handler preserves distinct validation, transport, and malformed-response errors without logging submitted values.

The reproducible catalog audit reports 300 semantic profiles, 33 scene concepts, 20 objectives, readiness metadata marked `AUTHORED` on 100/300 templates and `UNSPECIFIED` on 200/300, material and minimum-supervision metadata on 300/300, and activity-history prerequisites on 14 templates. Its static, adult-confirmed upper bound is 85 profiles after age/readiness/material/safety/history gates. With child readiness unobserved, 17 otherwise eligible profiles remain only because their authored templates have no readiness prerequisites; unknown readiness does not satisfy any authored prerequisite. The 2026-09-30 report adds FEAT-022 demand-tier × age coverage, objective slices requiring two distinct activity families, and declared topic-family coverage; many slices remain below target or empty. FEAT-022's raw selectable-variant count target has been reached, but that does not establish adequate safe coverage. No activity/readiness content is added without an authoritative source and reviewer.

The public-system benchmark across Montessori Compass, Transparent Classroom, AMI and AMS is recorded in `evidence/notes/MONTESSORI_FORM_BENCHMARK_20260929.md`. It indicates a useful distinction for this product: actual activity/objective/observation records are separate from an initial profile; a scope-and-sequence is a searchable adaptable framework rather than a giant checklist; and interest is considered alongside observed readiness/prerequisites, not used to bypass them. The owner confirmed adult-declared relatively stable interests, adult confirmation of AI-proposed tags, and keeping recommendations anchored to the confirmed drawing topic. Readiness is an activity-specific prerequisite query, not a score.

The project owner explicitly approved plan revision 3 on 2026-09-29; the record is in `approvals/TASK_APPROVAL.md`. Implementation is limited to this approved scope.

Implementation findings and sanitized verification are recorded in `evidence/notes/IMPLEMENTATION_FINDINGS_20260929.md` and `evidence/notes/IMPLEMENTATION_FOLLOWUP_20260930.md`.

At the 2026-09-30 follow-up, Android AVD `emulator-5554` (`sdk_gphone16k_x86_64`) was connected, the app was foregrounded, Metro reverse `8081 -> 8081` was active, and local backend health returned `ok`. A reset, controlled profile scroll sample recorded 130 frames, 3 janky frames (2.31%), and 19 ms P95 frame duration; this is not an input-to-paint measurement. Successful live classification and the full Android happy path remain blocked by the unstable/not-yet-current Lightning preference endpoint; see the follow-up evidence.

The V2 profile contract now explicitly carries `preference_tags_confirmed`; server validation rejects non-empty tags without adult confirmation while the mobile serializer still suppresses those tags before confirmation. Phase-one readiness candidates are displayed in stable activity-ID order rather than semantic-score order. Regression evidence is recorded in the 2026-09-30 follow-up.

Continued review added a session-local classification revision gate: unchanged text cannot trigger duplicate model requests; each content revision allows at most one classifier inference, edits create a new revision, and stale responses cannot complete newer drafts. The UI explains unmapped/no-match results. See evidence IDs `FEAT033-EV-20260930-02` and `-20260930-20` for the original gate and the completion-audit correction to enforce AC-04's one-request-per-revision limit. Remote classifier success, full Gate-B smoke, qualified catalog review, and input-to-paint profiling remain outstanding.

The follow-up then added a development-only profile-input responsiveness proxy on the connected AVD: 24 synthetic edits measured p95 40.80 ms from the JavaScript `onChangeText` callback to the next animation-frame callback. This does not measure native keyboard event-to-presented-pixel latency and has no comparable pre-change trace, so AC-09 remains incomplete. The synthetic draft was cleared, and temporary emulator/host screenshots and UI dumps created for this check were deleted. See `FEAT033-EV-20260930-03` in the implementation follow-up.

A fresh bounded synthetic request through the running local preference-classification route returned typed HTTP 503 `CLASSIFIER_ENDPOINT_UNAVAILABLE`, confirming the configured Lightning deployment does not yet expose `/v2/profile/preferences/classify`. The repository server source contains that route and reuses the shared Qwen generation runner; no remote deployment was changed. The external Lightning checkout must be updated/restarted before a live classification or full Android Gate-B happy path can be verified. See `FEAT033-EV-20260930-04`.

The focused local regression rerun for profile schemas, classification adapters, catalog audit, topic matching, P1 hard gates, and mobile session contracts passed all 97 tests; this verifies local contracts but does not substitute for live remote inference.

The latest review corrected the AI-proposal commit boundary: the classifier request returns data only, and the profile screen applies it only after matching the current draft revision and selected child; tags remain adult-unconfirmed. Mobile gate regressions, typecheck, and the Metro Android bundle pass. See `FEAT033-EV-20260930-05`.

Post-change runtime checks kept the local backend healthy, confirmed the connected Android activity and Metro reverse mapping, found no recent fatal JS log, and passed repository security validation.

A repeat AVD input check measured 23.06 ms JS callback→next-frame p95 and 22.50 ms p95 from Android input handling to frame completion, but `InputEventId` was zero across the 30 captured frame rows. The broader frame counters disagree between modern and legacy jank metrics; GPU renderer is host-accelerated NVIDIA OpenGL. This cannot establish native input-to-paint or a valid before/after comparison, so AC-09 remains open; see `FEAT033-EV-20260930-06`.

The mobile API now distinguishes malformed/non-JSON API or proxy responses from FastAPI validation errors instead of showing the generic unreadable-response message. Typed safe backend failures remain intact; response bodies are not copied into errors, logs, or evidence. On the current Expo monorepo setup, the Android bundle is served from `/apps/ui-mobile/index.bundle`; the root `/index.bundle` is not the app entry and must not be used as the Metro health probe. Evidence and tests: `FEAT033-EV-20260930-07` in the implementation follow-up.

The catalog coverage report now distinguishes pre-production review-scope counts from production eligibility. Current semantic profiles and P1 templates are 200 `DEMO_ELIGIBLE` plus 100 `PROVISIONAL_OWNER_REVIEWED`, with zero `PRODUCTION_APPROVED`; the former 85 static survivors are not production availability. The regenerated report counts a production candidate only when both matching catalog records are approved and production-eligible. No catalog content was changed pending qualified Montessori review. See `FEAT033-EV-20260930-08`.

See `evidence/notes/CURRENT_SYSTEM_AUDIT_20260929.md` and `evidence/notes/MONTESSORI_FORM_BENCHMARK_20260929.md`. Source authority: `docs/context/SOURCE_REGISTER.md`, especially `feat-029-master-srs`, `sketch2life-workflow`, and the registered official Montessori/catalog sources cited within FEAT-022.

Latest continuation (2026-09-30): a separate temporary Android test AVD verified the free-text
fields empty before synthetic input, measured 21.12 ms JS callback→next-frame p95 at 140 ms/character,
then cleared the draft and shut down; the user's emulator was not interacted with. Fast 40 ms
bursts were 149.92/166.54 ms, so this proxy is pacing-sensitive and does not satisfy native
input-to-pixel/before-after AC-09. A reproducible serializer helper now drives the mobile V2 P1
request and its regression preserves both `MAT_` and `GMAT-` namespaces while excluding unconfirmed
tags/raw free text. The backend classifier endpoint still returns synthetic HTTP 503
`CLASSIFIER_ENDPOINT_UNAVAILABLE`; no external deployment was changed. The catalog audit remains
300 templates, 100 authored / 200 unspecified, 85 pre-production static survivors, and zero
production survivors pending qualified review. The generated pytest basetemp ignore rule preserves
existing scratch files while allowing security validation to pass. See EV-11 and EV-12 in the
implementation follow-up.

The current-state completion audit found that the old profile selector exposed only 3–4, 5–6,
7–8, and 9+ despite SRS BR-012/013 covering 0–155 completed months and requiring direct caregiver
supervision below 36 months. The mobile profile now accepts exact completed years and months, with
no DOB field and a session-local 0–155-month value; age 0–35 additionally requires an explicit
caregiver/direct-supervision confirmation. The mobile serializer uses P1ContextV2 only below 36
months and retains P1ContextV1 for older ages; the backend revalidates caregiver presence during
P1 filtering. This is an implementation choice, not a resolution of DOB/time-zone/snapshot policy
in SRS OPEN-014. See `FEAT033-EV-20260930-13`, `-14`, and `-15`.

Focused mobile, backend contract/unit and full backend unit/contract checks pass for the local
implementation. The full Android happy path remains unverified because the deployed Lightning
service lacks the preference-classifier endpoint. Qualified source-backed catalog review and a
comparable native input-to-presented-pixel responsiveness trace also remain open; see the latest
feature-local follow-up and status.

The completion audit also closed a validation asymmetry: invalid POST profile bodies and invalid
GET context-options query values now both return the versioned typed workflow failure. A regression
proves that an out-of-range age is reported by safe field path without logging its submitted value.
The current catalog report was regenerated in memory and matches the checked-in JSON exactly.

The dedicated Pixel_10_2 API 37 smoke verified the 35/36-month caregiver boundary while leaving
the main emulator intact. Backend unit/contract, mobile UI-copy/typecheck, targeted Ruff, diff and
security checks all pass. Local backend, Metro and Android bundle are healthy. The test AVD was
closed after removing its synthetic session draft; the main emulator remains online. AC-09 is not
claimed complete because the latest frame trace has no nonzero Android `InputEventId`; successful
remote classification/Gate-B and qualified catalog review also remain external gates. See
`FEAT033-EV-20260930-17`.

The latest flow audit also found that activity-specific readiness/material responses and the adult
participation confirmation survived a successful feedback save and could be silently reused in the
next exploration. Those session-bound fields now clear only after successful feedback persistence;
the stable adult-declared preference fields and age remain volatile in the app session. Mobile
regression/type checks and the current Metro Android bundle pass. See `FEAT033-EV-20260930-18`.

The next contract replay found that three authored legacy readiness slugs did not match the V2
`READY_…` namespace and that `caregiver_present` had been conflated with child readiness. The
catalog adapter now canonicalizes the authored slugs and validates caregiver presence from the
under-three/direct-supervision safety metadata. The same end-to-end replay found P1 filtering
re-ranked a default top-three after contextual candidate finalization, potentially rejecting a
valid selected candidate; it now revalidates against the bounded deterministic phase-one shortlist
before applying existing hard gates. See `FEAT033-EV-20260930-19`. These changes do not add catalog
content or relax eligibility rules.

The completion pass found one additional AC-04 mismatch: the classifier gate allowed two attempts
for unchanged text despite the plan's one-inference-per-revision requirement. It now allows one
explicit inference per content revision; after failure, editing the text creates a new revision.
The Android SDK was located from Android Studio's configured path (`D:\AndroidStudio`), and a
read-only ADB recheck found the main emulator/app online and foregrounded, recent fatal/Metro-error
matches absent, and emulator-to-host TCP reachable on the backend/Metro ports. No child profile was
opened or changed. See `FEAT033-EV-20260930-20` and `-21`. The live classifier flow, qualified
catalog review, and comparable native responsiveness trace remain open.

A current, single synthetic classification request through the local backend returned HTTP 503.
It was not retried, and its response body/raw phrase were not retained; the exact subtype was not
captured by the caller. See `FEAT033-EV-20260930-22`. The successful live classifier and full
Android Gate-A-to-Gate-B path remain unverified.
