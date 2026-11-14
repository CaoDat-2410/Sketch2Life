# FEAT-069 task approval

- **Status:** APPROVED for the exact scope in Plan Rev1.
- **Approver:** Project owner, direct instruction in this conversation: “bạn làm sao cho đáp ứng yêu cầu của leader cho tôi đi”.
- **Recorded timestamp:** 2026-11-14 00:41:49 Asia/Saigon.
- **Approved plan:** `features/FEAT-069-leader-uiux-review-remediation/plan/PLAN.md`.
- **Plan revision:** 1.
- **Approved plan SHA-256:** `F5D04A3A1FABEE62B4CD59B3E34221B4A0FA063D857195126302BC517443314F`.
- **Scope:** implement review-compatible Parent mobile and Teacher web UI improvements; preserve FEAT-063 SRS v2.5-draft and current API/security boundaries; document unresolved leader/SRS/API conflicts; build and inspect the affected UIs; update feature/source records; run security validation before the previously authorized normal push to `origin/FE_UI_Project_Ver2`.
- **Acceptance criteria:** AC1–AC10 in the hash-identified Plan Rev1.
- **Exclusions:** backend/API/database/auth/schema/SRS/provider/deployment changes; shared API writes; live ASR/AI calls; unsupported gender field; Parent outdoor activities before video; removal of required context/script confirmation; generated raster assets; Child Expo changes; force push/history rewrite.
- **Approval basis:** the user's direct request authorizes this bounded implementation. Leader transcript text is feedback, not a change to canonical product/SRS/API requirements.

## Plan Rev2 approval

- **Status:** APPROVED for the exact UI-only scope in Plan Rev2.
- **Approver:** Project owner, direct instruction in this conversation: “nói chung giờ tôi muốn bạn đáp ứng toàn bộ yêu cầu của leader được không, tôi đã cung cấp hết dữ liệu cần có để bạn làm rồi đó”.
- **Recorded timestamp:** 2026-11-14 01:28:17 Asia/Saigon.
- **Approved plan:** `features/FEAT-069-leader-uiux-review-remediation/plan/PLAN_REV2.md`.
- **Plan revision:** 2.
- **Approved plan SHA-256:** `6239B3640D367A2EA847DDA97F1FAE5DB9978222F4E3362E43BBD5065BB3B6ED`.
- **Scope:** complete the remaining Parent/Teacher leader-review UI items as review prototypes; keep SRS v2.5-draft canonical, preserve adult context confirmation, mark the requested pre-video activity and local gender field as proposed preview behavior, and disclose unavailable API/AI paths; build, visually inspect, document evidence, validate repository security, and push normally to the previously authorized `origin/FE_UI_Project_Ver2` if fast-forwardable.
- **Acceptance criteria:** AC1–AC12 in the hash-identified Plan Rev2.
- **Exclusions:** backend/API/auth/schema/database/SRS/provider changes, API writes, live AI/ASR, persistent gender, child data/media, automated tests, release signing, Child Expo changes, force push/history rewrite.
- **Approval basis:** this direct user request authorizes the UI-only implementation against the full leader transcript. It does not sign off the unsigned canonical SRS or authorize backend contract changes.

## Source boundary checkpoint — 2026-11-14

- The project owner confirmed `UI_Project/` is the primary UI/UX to revise and the top-level `apps/` tree is legacy UI excluded from this handoff. The owner also reiterated that the deliverable must satisfy the leader's complete review.
- Rev2 remains the approved implementation plan and hash above; its implementation targets remain the `UI_Project/` Parent Android/WebView and three web role workspaces.
- A read-only comparison used the permitted newer backend source `origin/feature/feat063-m2-parent-teacher-foundation@5c07c94e`. This branch includes Parent profile/story router groups that are not mounted in the delivery branch at `2518dc07`; no such routes are represented as connected in the UI handoff.
- No source from the legacy top-level `apps/` directory was copied or added to the run targets.

## Plan Rev3 approval — API-aligned UI/UX completion

- **Status:** APPROVED for the exact frontend-only scope in Plan Rev3.
- **Approver:** Project owner, direct instruction in this conversation: “dựa vào API đang có để build UIUX lên đi ... giúp tôi check xem các API để mình làm UIUX đúng ... hoàn chỉnh 100% yêu cầu của leader”.
- **Recorded timestamp:** 2026-11-14 02:30:58 Asia/Saigon.
- **Approved plan:** `features/FEAT-069-leader-uiux-review-remediation/plan/PLAN_REV3.md`.
- **Plan revision:** 3.
- **Approved plan SHA-256:** `21A1FB640990D078793918AFCA651394FBACB42BFD0F80C173B28A385BFCAEB9`.
- **Scope:** Align the Parent Android and three web role workspaces with current delivery-branch API contracts and the leader review; distinguish mounted endpoints from allowed newer-branch references; preserve preview-only behavior wherever identity or routes are missing; build, visually review, update feature evidence, validate repository security, and publish normally to the previously authorized branch if fast-forwardable.
- **Acceptance criteria:** AC1–AC10 in the hash-identified Plan Rev3.
- **Exclusions:** backend/API/schema/auth/provider/SRS changes or route merges; live API/AI calls or database writes during implementation/QA; forbidden branches as source; legacy `apps/` and Child Expo; force push/history rewrite; automated tests.
- **Approval basis:** the owner's direct request authorizes this bounded frontend work. It does not authorize backend integration changes or claim missing runtime services are working.

## Plan Rev3 Parent Library addendum approval

- **Status:** APPROVED for `plan/PLAN_REV3_ADDENDUM_PARENT_LIBRARY.md`.
- **Approver:** Project owner, direct request in this conversation to build UI/UX against the APIs currently present in the project and complete the leader's requirements.
- **Scope:** conditionally read the current Parent public/shared Lesson Library and invitation APIs when the Firebase token bridge exists; fetch selected lesson detail on demand; use the typed invitation accept/decline operation only after user selection; preserve preview/no-fallback error states; leave Parent profile/story/AI/video unsupported flows preview-only.
- **Exclusions:** backend/API/auth/schema/SRS changes, live API calls during implementation/QA, unsupported Parent flows, user/child data, automated tests.
- **Approval basis:** direct owner instruction; see exact limits in the addendum.

## Plan Rev4 UI-only clarification approval

- **Status:** APPROVED for this exact UI-only scope.
- **Approver:** Project owner, direct clarification in this conversation: “cứ làm UIUX theo đúng yêu cầu của leader là được không phải ghép hay nối API gì cả”.
- **Approved plan:** `plan/PLAN_REV4_UI_ONLY.md`.
- **Plan revision:** 4.
- **Approved plan SHA-256:** `EE85CB380638985969419A38646B1D72383C74CC390027C903D1950C387FF4C3`.
- **Scope:** Use API/source only as business-flow reference; remove conditional API/auth wiring; align role UI flows with the leader disposition, including post-video Parent activities and no unsupported gender field; show Parent Settings only on the Family Profile page; visually verify and build the UI workspaces and Parent APK.
- **Exclusions:** backend/API/auth/schema/database/SRS changes; live calls/writes; real child data/media; legacy `apps/`, Child Expo; automated tests; force push/history rewrite.
- **Approval basis:** direct owner clarification supersedes the prior Rev3 interpretation for current UI work.

## Plan Rev5 — complete API-informed UI preview states

- **Status:** APPROVED for the exact UI-only scope in `plan/PLAN_REV5_PREVIEW_COMPLETION.md`.
- **Approver:** Project owner, direct request in this conversation to complete the mismatch, speech-to-text, drawing-guide and Teacher Dashboard UI from source/API references; add gender to Parent profile and child selection; and run the UI for review.
- **Plan revision:** 5.
- **Approved plan SHA-256:** `F49F00D71E5E0D84B2EA695A1BB63010DA2E82E8A8FAC356542BDA145279262A`.
- **Scope:** UI-only; no API calls. Mismatch-result preview modal, editable fixture transcript states, optional generic-topic drawing guide, source-shaped Teacher Dashboard preview, and local-only gender controls on Parent profile and child picker. Build and run the UI for review.
- **Exclusions:** backend/API/auth/schema/SRS changes, live service calls/writes, persisted gender, real child data, legacy top-level `apps/` implementation, automated tests and history rewrite.
- **Approval basis:** direct owner instruction. The canonical SRS is not amended; gender remains a preview-only product question.
