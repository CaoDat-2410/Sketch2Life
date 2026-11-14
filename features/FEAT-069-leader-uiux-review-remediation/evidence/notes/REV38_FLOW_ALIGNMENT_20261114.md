# Rev38 UI/UX flow alignment review — pre-Rev7 snapshot

Date: 2026-11-14 (Asia/Saigon)
Branch: `FE_UI_Project_Ver2`
Scope: read-only comparison of the `UI_Project/` source before Rev7 implementation against the leader-provided Rev38 screen and component indexes, with current product flow checked against FEAT-063 SRS v2.5-draft. This is a historical gap audit; Rev7 implementation and verification are recorded in `evidence/notes/EXECUTION.md`.

## Authority and method

The references reviewed were `UI_Project/design-references/ui-mockups-rev38-20261030/SCREEN_INDEX.md`, `ui-components-rev38-20261030/COMPONENT_INDEX.md`, current role UI source, and `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` §5.1 and relevant Parent/Teacher requirements. Representative boards opened for visual inspection were P01, P03, P07, T03, M01, A01, UI01 and UI06. Rev38 labels itself as generated visual drafts; it is based on SRS v2.3/API Rev37 and says its visual tokens are not implementation contracts. FEAT-063 v2.5-draft is the current working SRS and remains unsigned. Therefore this review reports resemblance/alignment, not formal product sign-off.

The comparison is a source and design review, not a complete click-through of every route. The five UI workspaces were production-built. Parent home was reopened in the local browser after the Rev6 change and its accessibility tree was checked. The comparison predates Rev7's fixture-flow implementation; it should not be read as the current route inventory. No API/auth requests were made; the workspaces remain local previews.

## Screen flow comparison

| Rev38 screen | Current `UI_Project/` state | Assessment |
|---|---|---|
| P01 Lesson Library / child selection | Parent lesson/library routes and child selection exist. The home profile summary card has now been removed; child selection remains in the story-start flow and Family Profile. Rev38 places a child-selection entry in the Library. | Partial: selection exists but its entry point differs. |
| P02 Lesson detail | Local lesson detail/selection preview exists. | Partial: preview behavior, not a connected lesson contract. |
| P03 Drawing guide | Three-step static guide exists before capture. Rev38 combines the optional guide with the active drawing/capture surface and an in-progress guide toggle. | Partial: different interaction and placement. |
| P04 Capture / subject confirmation | Capture and local subject/mismatch review states exist. No VLM analysis is performed. | Partial: confirmation is represented, analysis is a fixture. |
| P05 Context / idea confirmation | Idea, editable sample transcript, and context confirmation are represented. Current Parent sequence reviews the subject before idea/context. | Partial and an open flow conflict: canonical SRS §5.1 orders capture → idea/transcript → subject review → context confirmation. |
| P06 Story review | Story review, context confirmation, and a local rewrite counter are represented. | Partial: generated story/rewrite operations are preview states. |
| P07 Video job status | Current generation step is an honest unavailable preview. Rev38 shows resumable discrete job stages plus failed and safety-blocked states. | Gap: those job and resume states are not represented. |
| P08 Video and activities | Video is unavailable/non-playable in preview; activities are shown after the story/video step. | Partial: ordering matches the SRS, but playback, captions, completion/retry and occurrence behavior are not implemented as the Rev38 flow. |
| P09 History / feedback | History and feedback preview routes exist. | Partial: retention windows, deletion lifecycle and lesson-scoped feedback behavior are not fully represented. |
| P10 Child profiles | Profile list/form preview exists; the requested gender field is local UI state. Current SRS and Rev38 do not define gender. | Partial: local profile editing only; gender needs product reconciliation before it is treated as a real profile attribute. |
| P11 Authentication | Sign-in/activation screens are preview UI. | Partial: no live authentication flow is claimed. |
| P12 Video quota | Quota screen is an empty/unavailable state. Rev38 illustrates quota counts and payment choices. | Gap: the illustrative purchase/quota flow is absent; no current UI contract supports claiming a live purchase. |
| T01 Teacher lesson workspace | Source-shaped dashboard/list preview exists with lesson, assignment, visibility and review counts. Rev38 emphasizes next session, class/lesson and feedback. | Partial: information hierarchy and metrics differ. |
| T02 Lesson authoring | Local three-step lesson form exists. Rev38 uses four structured sections/activity cards and a send-for-review action. | Partial: authoring structure and review submission differ. |
| T03 Document import review | File selection/placeholder UI exists, but no extracted-field review is shown. | Gap: the key scan/extraction/review/confirm sequence is missing. |
| T04 Session / Sketch Deck | Session/deck preview routes exist. The full optional deck toggle and presentation behavior from Rev38 are not represented end-to-end. | Partial. |
| T05 Classes / children | Class/roster preview routes use fixtures. | Partial: not the full assigned-roster flow. |
| T06 Sample story run | A six-step local sample wizard exists. | Partial: the steps are fixture-only and do not complete the full eligible-child/lesson/script/video flow. |
| T07 Video presentation confirmation | Presentation screen exists but remains disabled until playback/API capability is available. | Gap for the playable sample and explicit presentation-ready flow. |
| M01 Publication review | Current manager preview is a generic two-step decision/reason/confirmation flow. Rev38 starts with four unchecked gates and disables approval until each passes. | Gap: checklist gating and exact version review are not represented. |
| M02 Organization management | Organization/school manager routes exist as fixture previews. | Partial: no full groups/classes/slots/quota management workflow. |
| A01 Content moderation | Moderation list/detail and generic preview action exist. | Partial: status-specific hide/reopen actions and resulting states do not match the Rev38 proposal. |
| A02 Platform operations | Dashboard is a fixture; detailed operational routes are generic or unavailable. | Gap for the proposed organization/catalog/policy/quota overview. |

## Component system comparison

| Rev38 group | Current UI comparison |
|---|---|
| UI01 Foundations and controls | Visible design system differs: current Parent leans forest green/warm cream; Rev38 proposes blue primary, yellow accent and mint support. Since Rev38 marks these as unapproved tokens, this is a visual difference, not by itself a requirements defect. |
| UI02 Parent dialogs and sheets | Related subject/script/request dialogs exist in preview, but not every staged loading/error/confirmation state is represented. |
| UI03 Web decision dialogs | Decision dialogs/actions exist in role previews; full status-specific transitions are incomplete. |
| UI04 Toasts and inline notices | Shared feedback patterns exist, but data/action results remain local. |
| UI05 Loading, empty, error and safety states | Some preview/empty/unavailable states exist; resumable video and automated safety states are not complete. |
| UI06 Teacher import review | Incomplete: file selection does not continue into extracted-field review and confirmation. |
| UI07 Video quota and job states | Incomplete: no stage-by-stage resumable job or illustrative quota purchase flow. |
| UI08 Lesson and child-profile grants | Shared grant patterns/routes are represented as local previews; not all grant/revocation states have a complete route. |
| UI09 Lesson-scoped feedback | Feedback preview exists; a complete lesson-scoped thread/retention lifecycle is not demonstrated. |

The web role navigation is also broader than the Rev38 proposal: current source has 18 Teacher, 15 School Manager, and 12 Platform Admin entries versus six proposed entries for each role. This should be treated as an information-architecture difference to review, not automatically deleted functionality, because Rev38 is a generated proposal and the current route set contains additional preview areas.

## Conclusion and priority gaps

The current UI **does not match all Rev38 flows**. The strongest gaps are Parent video job/playback states, Teacher document extraction review, Manager's checklist-gated publication decision, and the completeness of Teacher presentation and Admin moderation/operations. Parent flow is partially represented, but the current subject-before-idea ordering conflicts with canonical FEAT-063 §5.1; keep this as an open decision instead of copying the older Rev38 ordering. Parent activity placement after the story/video step is consistent with the current SRS.

Removing the duplicate home child card is consistent with the owner's latest request and leaves child selection in story setup. It is not a one-to-one match for P01, which places a selection entry in the lesson library. The current gender control is also an owner-requested local preview field absent from the current SRS and Rev38.

None of these role previews calls the backend. This report does not establish API availability, authentication, persistence, AI/ASR, video playback, APK runtime, or formal leader acceptance. Broader flow changes require their own scoped plan/approval and must preserve the unsigned SRS authority boundary.
