# FEAT-081 Wave V: Native Parent UI Visual Alignment — Plan Revision 5 Draft

Status: DRAFT plan source; Addendum 11 records Plan Revision 5 APPROVED and Wave V NOT LAUNCHED.
Date: 2026-11-13.
Target: apps/ui-mobile on feature/fe-mobile-remediation.
Source direction: Person 2, 2026-11-13.
Reference: read-only sample at .worktrees/ui, feature/fe-ui-full-remediation, HEAD 30c94342.
Decision: features/FEAT-081-parent-ui-mobile-port/DECISIONS.md (D-013).
Approval: features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md (Addendum 11).

This draft plans a native React Native presentation redesign of the current Parent mobile UI. It uses the sample source as visual reference and rewrites the design in native components. It does not port behavior or sample implementation. Wave 4 P07-P09 functionality that depends on real APIs remains deferred. Wave V does not add any video-job, player, post-video, or other product behavior. It does not authorize implementation, testing, validation, staging, committing, or publishing.

## 1. Goal and boundaries

Apply the sample's tokens plus per-screen layout and hierarchy parity to the existing Parent screens; pixel perfection is not required, and the owner may refine the look later. Preserve existing native behavior. Presentation changes may cover hierarchy, layout, spacing, color, typography and component shape. Make no copy changes except text strictly required by layout and separately approved by the owner. The default is no wording change.

Keep every current screen export, prop, callback, route, state machine, domain contract, API call, validation rule, and test unchanged. JSX may be regrouped to create a visual hierarchy, but it must render the same content and controls and preserve their order of operation. No sample React DOM, CSS, HTML, data, fixture behavior, image, icon, font, illustration, simulated phone frame, or branch content may be copied. The sample worktree remains read-only; no merge or cherry-pick.

Owner direction defers Wave 4 P07-P09 functionality until real APIs exist. Existing current native screens may receive presentation-only changes under the checkpoint list below. That does not create P07 status, P08 video player, P08c feedback, P14 recovery, P15 registration, new routes, or API work. HandoffScreen and ActivityScreen retain only their existing native behavior. V4 screens remain mounted as they are in the current app; the backend routes behind them do not exist yet. Preserve exact current route availability and every current state, with no route, filter, detail view, or behavior added or removed.

Do not change backend or route code, application/domain/infrastructure code, screen/controller state logic, contracts, tests, package manifests, lockfiles, scripts, generated/approved/applied assets, DECISIONS.md, TASK_APPROVAL.md, CONTEXT.md, or STATUS.md. No new dependencies. Use system fonts. Do not implement dark mode, landscape, or tablet variants in this wave unless the owner selects a different scope and approves a revised plan.

## 2. Sample visual analysis

All references below are to read-only sources in .worktrees/ui. Sample state/data is visual evidence only and is never a source of native behavior or production content.

### Design tokens

| Area | Sample observation | Source reference |
|---|---|---|
| Light palette | Primary blue #2563EB with dark/focus blue #1D4ED8 and edge #1E3A8A; pale blue #DBEAFE / #EFF6FF; amber #FBBF24; mint #047857; danger #DC2626; pink #BE185D; violet #6D28D9; ink #0F2447 / #334155 / #475569; white, #FAFDFF, #EEF4FC surfaces; line #D5E3F7. | .worktrees/ui/apps/parent-ui/src/styles/tokens.css:5-42 |
| Dark palette | A complete alternate dark palette is defined in CSS, with dark surfaces, text and shadows. It is reference-only for Wave V. | .worktrees/ui/apps/parent-ui/src/styles/tokens.css:45-81 |
| Typography | Be Vietnam Pro is loaded by CSS with system fallbacks. Display/body hierarchy uses 22/18/14/13/11.5 px; body line height is 1.5; controls use bold weights. | .worktrees/ui/apps/parent-ui/src/styles/tokens.css:2,39-40,271-280 |
| Spacing | Page inset is 18 px horizontally, 6 px top and 28 px bottom with 14 px vertical gap. Common stack/row gaps are 10 px. | .worktrees/ui/apps/parent-ui/src/styles/tokens.css:156,265-270 |
| Radius | Large card 24 px; compact card 20 px; flat panel 16 px; primary button 20 px; secondary 18 px; round control 14 px; note 18 px; chip 999 px. | .worktrees/ui/apps/parent-ui/src/styles/tokens.css:207-213,243-263,297-367,374-396,429-446 |
| Elevation | Cards and controls use layered soft blue/ink shadows, including inset highlights; buttons use a heavier colored lower edge. | .worktrees/ui/apps/parent-ui/src/styles/tokens.css:41-42,243-254,297-356 |
| Control sizing | Round header controls are 44 px. Tab controls have 44 px minimum height. Primary buttons are 48 px; compact buttons and chips remain at least 44 px. | .worktrees/ui/apps/parent-ui/src/styles/tokens.css:207-210,172-201,297-345,367-388 |

### Shared kit and chrome

.worktrees/ui/apps/parent-ui/src/components/Kit.tsx provides sample Wordmark, Mascot, Dino, Robot, SunDoodle, status-bar glyphs, inline parent/child SVG avatars, and a gender field (.worktrees/ui/apps/parent-ui/src/components/Kit.tsx:9-170,215-400). Its behavioral helpers include TopBar, StepChips, Btn, Soft, Progress, Note, Switch, Waveform, Sheet, and gradient constants. These are React DOM/CSS helpers and SVG drawings, not native source to copy. Their visual roles can inform the native component map in section 4.

.worktrees/ui/apps/parent-ui/src/components/MobileLayout.tsx wraps the web routes in a browser-only stage and simulated 390×844 phone, with fake status bar/notch, fake frame/background, scrolling page area, tabs, central create shortcut, toast and modal-sheet overlays (.worktrees/ui/apps/parent-ui/src/components/MobileLayout.tsx:32-516; .worktrees/ui/apps/parent-ui/src/styles/tokens.css:151-170 and 1320-1336). It chooses visible tabs from the sample route/local-preview state and owns web routing and sample state. None of the frame, fake OS chrome, route logic, tab logic, toast logic or sheet logic is copied. Native uses the real Android status/navigation areas and the existing ParentBottomBar's four tab IDs and callback.

The sample header centers a 16 px heavy title between 44 px round controls and optional text links (.worktrees/ui/apps/parent-ui/src/styles/tokens.css:205-240). Cards use 24 px rounded white surfaces, restrained borders and layered shadows; flat information blocks use 16 px radius (.worktrees/ui/apps/parent-ui/src/styles/tokens.css:242-263). Page patterns favor one scroll column, section headings, small status chips and one prominent bottom/section CTA. The tab bar has five web slots because of a raised create action; the native bar retains its current four-item API and does not gain an extra route or action (.worktrees/ui/apps/parent-ui/src/components/MobileLayout.tsx:128-190; .worktrees/ui/apps/parent-ui/src/styles/tokens.css:160-202).

### Per-page patterns and states

| Sample page | Visual pattern and observed sample states | Reference and native relevance |
|---|---|---|
| P01 lesson library | Child switcher and profile status, prominent create/story CTA, active-run summary, recent cards, lesson entry and help content; loading/empty/selection/status variants are represented by mock data. | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:193-485; .worktrees/ui/apps/parent-ui/src/data/mockParentData.ts:1-149,248-544. V2 Home and lesson surfaces. |
| P02 lesson detail | Back/title header, large lesson summary, tags, knowledge-point rows and guide/capture CTAs. | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:591-718. V2 LessonPicker/Gallery presentation reference only. |
| P03 drawing guide | Step indicator, one instruction per view, illustration area, optional-guide control and previous/next/continue controls. | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:719-860. V3 DrawingGuide visual grouping only; no sample guide text/art/optional-toggle behavior. |
| P04 capture and subject review | Capture/preview surface, candidate or review card, explanatory note and confirm/edit actions; mock permission, candidate and error states. | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:861-1005. V3 Capture/Understanding styling only; current native media/subject states stay. |
| P05 idea/context | Topic and adult-idea entry, optional sample recording/transcript review, then distinct context review/confirmation. | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:1006-1224. V3 Topic/Context/TranscriptReview layout reference only. No recording/transcription behavior is added. |
| P06 story review | Story scenes in readable cards, revision/state information and a distinct review/confirm action. | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:1225-1372. V3 Story layout only; current rewrite cap and confirmation state stay. |
| P07 video job status | Status/progress card, explanatory state and retry/review actions in mock states. | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:1373-1510. Deferred functionality; no new screen/state/API. Existing HandoffScreen may only be restyled using its own current props/states. |
| P08 video and activities | Video/player surface, player controls, landscape mode and post-video activities. | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:1511-1745. Deferred and excluded. No player, landscape mode, completion, or video state. |
| P08b outdoor activities | Activity cards, selection and completion presentation. | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:1746-1846. No new activity chooser/completion behavior; existing ActivityScreen only. |
| P08c session feedback | Post-video rating/feedback form. | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:1847-1963. Explicitly excluded; no new feedback UI or route. |
| P09 history/feedback | Filter chips, grouped run rows, selected-run details, feedback and empty/loading/error presentations. | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:1964-2201. V4 may restyle current history screens only; no sample feedback data/actions. |
| P10 profiles | Profile list and detail/form hierarchy, selected/archived/deleting states, confirmations and validation. | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:2202-2528. V1 profile list/form styling; only existing native fields/states. |
| P11 authentication | Brand/header area, login form, provider action, helper/recovery links and form feedback. | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:2546-2834. V1 auth styling; no copied artwork, recovery, or registration route. |
| P12 quota | Large balance, usage/bucket cards and fictional purchase tiers/payment states. | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:2835-3074. V4 read-only quota styling only; no purchase flow or payment behavior. |
| P13 settings | Account/profile/settings rows, grouped sections and theme/security/navigation entries. | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:3075-3396. V1 settings and V4 notifications/sharing presentation references; no new toggles/theme/routes. |
| P15 registration and P14 recovery | Separate forms with field validation, submit and success/error states. | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:3397-3629. Explicitly excluded; no registration/recovery screen or route. |

## 3. Proposed native token map and asset/dependency gaps

Create the additive native token module apps/ui-mobile/src/parent/presentation/components/parentUiTokens.ts in V0. It contains plain TypeScript values only and imports no web or new package code. The current ui.tsx palette export keeps its exact key shape and values as a compatibility facade; screens do not import a new token API in this wave.

| Native token group | Proposed starting values | React Native mapping |
|---|---|---|
| colors | primary #2563EB, primaryDark #1D4ED8, primaryEdge #1E3A8A, paleBlue #DBEAFE, paleBlueSoft #EFF6FF, accent #FBBF24, accentInk #78350F, mint #047857, mintSoft #D1FAE5, danger #DC2626, dangerSoft #FEE2E2, pink #BE185D, violet #6D28D9, ink #0F2447, ink2 #334155, ink3 #475569, surface #FFFFFF, surfaceAlt #FAFDFF, surface2 #EEF4FC, line #D5E3F7, page #F7FBFF. | Use View/Text backgroundColor, color and borderColor. Keep text contrast and status conveyed by label/icon as well as color. |
| type | hero 22, title 18, section 14, body 14 or 13, supporting 13, caption 12, compact 11.5; line-height ratios 1.24/1.26/1.35/1.5; weights 400-800. | Text style fontSize, numeric lineHeight computed from fontSize times the sample ratio, and fontWeight. Use system default fontFamily; omit custom font names and keep allowFontScaling defaults. |
| spacing | 4, 6, 8, 10, 12, 14, 18, 20, 24, 28; page horizontal 18, page vertical gap 14, common stack 10, bottom scroll clearance 28. | StyleSheet numeric dp values for padding, margin and gap. Use flex layouts and ScrollView contentContainerStyle; avoid fixed page heights. |
| radius | control 14, flat 16, secondary/note 18, compact card 20, card/primary button 24/20, full pill 999, circle 999. | borderRadius in StyleSheet; use consistent shapes without CSS clipping/filter rules. |
| shadow | soft ink-blue shadow and low elevations 1-3; primary colored button edge treated as a 2-3 dp shadow. | iOS shadowColor/shadowOffset/shadowOpacity/shadowRadius plus Android elevation through Platform.select. No inset or multi-layer CSS shadow emulation. |
| layout | page side 18, header control 44×44, minimum interactive target 44×44, primary CTA minimum 48, tab hit target minimum 44, card padding 15-16. | minWidth/minHeight, padding and flex sizing. Respect safe areas and scroll/keyboard insets from the existing native shell. |

The sample's custom Be Vietnam Pro CSS import is not available as a native font and is not used. Adding/downloading font files or a font package would require a separate owner decision, package/lockfile allowlist change, offline asset review and provenance. The sample's inline SVG mascots, logo/brand mark, parent/child avatars, sun doodle, guide illustrations, page art and custom SVG icon registry are not copied. No sample raster/media assets or mock data are copied. Use native text and the icon library already used by ParentBottomBar only where current native controls already need an icon; no emoji-as-required-status. Do not add react-native-svg, Expo gradient, icon/font packages, or any other dependency. Approximate gradient surfaces with flat token colors and restrained native elevation. If future parity requires artwork, it needs separate generated-art provenance and the repository frontend asset gate; no asset is required by this plan.

The sample uses CSS gradients, inset shadows, browser-specific active/hover/focus styles, CSS font variants, a web status-bar mock and DOM sheets. React Native has no direct equivalent for all of these without extra packages. Approximate only the static hierarchy with native View/Text/Pressable/StyleSheet and platform shadow properties; do not add browser effects or new interactive behavior.

## 4. Component map and backward-compatible APIs

Restyle the existing ui.tsx primitives in place. Keep each current named export and its prop type/optional defaults/callback signature exactly as-is. No screen import or call site is to change solely to adopt a renamed API.

The current exported API (including defaults) to preserve exactly is:
- palette keys ink, muted, blue, paleBlue, background, white, border, green, paleGreen, amber, paleAmber, red, paleRed.
- ScreenFrame: PropsWithChildren<{title: string; subtitle?: string; step?: string; onBack?: () => void; backDisabled?: boolean}>.
- Card: PropsWithChildren<{style?: object}>.
- PrimaryButton: {label: string; onPress: () => void; disabled?: boolean; busy?: boolean}; disabled and busy default to false.
- SecondaryButton: {label: string; onPress: () => void; disabled?: boolean}; disabled defaults to false.
- ConfirmButton: {label: string; title: string; message: string; confirmLabel: string; onConfirm: () => void; destructive?: boolean}; destructive defaults to false.
- TextButton: {label: string; onPress: () => void; disabled?: boolean}; disabled defaults to false.
- Field: TextInputProps & {label: string}.
- Notice: {text: string; tone?: 'info' | 'success' | 'warning' | 'error'}; tone defaults to info.
- SectionTitle: PropsWithChildren.
- ChoiceRow: {title: string; detail?: string; selected?: boolean; onPress: () => void}.
Preserve current runtime defaults, accessibility props and confirmation behavior as well as these signatures.

| Sample kit role | Native target | Planned treatment |
|---|---|---|
| TopBar | ScreenFrame | Restyle existing header, back target, title, optional subtitle and step placement. Keep its current API: ScreenFrame({title, subtitle?, step?, onBack?, backDisabled?, children}). |
| Card / flat box | Card | Restyle padding, radius, border and low shadow; preserve Card({children, style?}). |
| Btn / primary and Soft | PrimaryButton, SecondaryButton, TextButton | Restyle in place. Keep label/onPress/disabled/busy props exactly unchanged. Keep primary busy/disabled visual states and press targets. |
| Confirm action / sheet | ConfirmButton | Restyle the existing confirmation presentation only. Keep label, title, message, confirmLabel, onConfirm and destructive props and existing confirmation behavior. No sample Sheet overlay. |
| Field | Field | Restyle label/input spacing, border, focus/disabled/error presentation while forwarding the same TextInputProps and label. Keep keyboard, value, validation and submission semantics. |
| Note | Notice | Restyle the four existing info/success/warning/error tones; retain Notice({text, tone?}) exactly. Use text/icon/shape plus color for meaning. |
| Section heading | SectionTitle | Restyle type, spacing and optional divider treatment without changing children. |
| Selection row | ChoiceRow | Restyle selected/unselected row and focus/pressed states; keep title, detail?, selected?, onPress unchanged. |
| Palette | palette | Keep its current exported property names and shape for any existing imports. Values may be remapped in-place to the approved light tokens, but no screen usage changes. |
| StepChips | ScreenFrame step | Reuse the current optional step presentation where present; do not add or infer steps or a new flow. |
| Icon badge | Additive IconBadge | New export from ui.tsx only if needed by current screen layouts: IconBadge({children, tone?: 'primary' | 'accent' | 'success' | 'danger' | 'neutral', size?: number}). It is presentational, has no callback/state and accepts a native child. |
| Status chip | Additive StatusBadge | New export from ui.tsx only for current statuses: StatusBadge({label, tone?: 'primary' | 'success' | 'warning' | 'danger' | 'neutral'}). The text remains supplied by the screen and existing state; no state is inferred. |
| Progress | No new progress API by default | If visual audit finds an existing numeric progress value already rendered in a current screen, restyle that existing view in place. Do not add progress state, timers, or a new progress screen. |
| Switch, Waveform, sample Sheet, sample gradients | No new native behavior | Do not port these helpers. Restyle current equivalent controls only; no audio UI, settings toggle, overlay or gradient behavior is added. |

ParentBottomBar keeps the exact exported ParentMainTab union home | lessons | start | profiles and component props activeTab/onNavigate. Restyle its current four tabs, labels, icon size, active marker, bar surface and safe bottom spacing. Do not add the sample's fifth slot, a new start action, route, callback, or tab identifier.

Only new module/API proposals are the token module and additive IconBadge/StatusBadge. Existing component APIs and every screen export/prop/callback stay backward-compatible. The new optional primitives may be omitted if V0 can achieve the same design with existing exports; they may not cause behavior or route changes.

## 5. Checkpoints

Each V checkpoint is a separately approved implementation launch, its own baseline/post test run set, owner validation and emulator walkthrough, evidence report, and commit. Approval or completion of one checkpoint does not launch the next. This draft launches none. All screen states below mean the states already present in the current native components/controllers; do not import sample state machines.

Owner runs the emulator walkthrough at each checkpoint on the 6.1-inch portrait Android emulator. Verify 44 dp minimum touch targets (48 dp for primary CTA); status/navigation/safe areas; scroll and keyboard reachability; no clipping at large system text; contrast for normal/disabled/error/success states; selection/progress/error meaning is not color alone; press feedback; long labels; and screen-height bottom CTA access. The owner may capture before/after screenshots for review, but screenshots are not committed to the repository. The evidence report records screenshot references and the owner result only. Cover touched screens and representative loading, empty, disabled, error and confirmation states that already exist. No fake OS frame/status bar.

### V0 — native tokens, shared primitives and bottom navigation

E: ui.tsx and ParentBottomBar.tsx only. N: parentUiTokens.ts and the V0 evidence report.
Sample reference: .worktrees/ui/apps/parent-ui/src/styles/tokens.css:5-42,151-280,282-450; .worktrees/ui/apps/parent-ui/src/components/Kit.tsx exports; .worktrees/ui/apps/parent-ui/src/components/MobileLayout.tsx:143-190.
Apply the approved light palette, type/spacing/radius/shadow scale to current ScreenFrame, Card, buttons, ConfirmButton, Field, Notice, SectionTitle, ChoiceRow and ParentBottomBar. Use real native status/navigation areas. Preserve every primitive prop/API, disabled/busy/pressed/confirmation state, tab IDs/callback and current safe-area behavior. Accessibility: shared 44 dp target minimum, primary 48 dp, text scaling, contrast and labels; no icon-only meaning. Owner emulator checklist focused on one header, one long-scroll screen, one form field, all four tabs and bottom safe area.
Evidence path: features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVEV_V0_20261113.md.

### V1 — authentication, profiles, account and settings

Screens: AuthScreen, ProfileScreen, ProfileFormScreen, AccountScreen, SettingsScreen, GoogleSignInButton.
Sample reference: P11 .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:2546-2834; P10 .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:2202-2528; P13 .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:3075-3396; shared header/card/field/button tokens.
Apply the sample's clear header/form groups, card-backed profile rows, stronger primary CTA, compact status chips and grouped settings rows. Do not copy brand art, sample avatars, gender fields, registration/recovery forms or theme toggles.
Preserve current login/provider state, loading/error/disabled fields, profile selection/archive/deletion and validation states, save/cancel/confirmation, account/sign-out states and every callback. Maintain existing auth form keyboard flow and destructive confirmation.
Accessibility: explicit field labels, secure-field semantics and visible focus/disabled/error state; common checklist. Owner emulator checklist: auth form with keyboard visible, Google button busy/error states, empty/list/archived profile states, profile form validation/confirmation, account actions and settings rows.
Evidence path: features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVEV_V1_20261113.md.

### V2 — home, lesson picker and gallery

Screens: HomeScreen, LessonPickerScreen, LessonGalleryScreen.
Sample reference: P01 .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:193-485; P02 .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:591-718; .worktrees/ui/apps/parent-ui/src/data/mockParentData.ts:1-149,248-544; shared card/section/button tokens.
Apply a profile/header summary, high-contrast primary start action, compact active-run summary, recent-content cards, consistent lesson choice rows and readable lesson details. Do not use mock stories/lessons/images, sample CTA actions or extra FAQ routes.
Preserve current profile choice, lesson pin/version/hash, current run summary, loading/error/empty states, card selection and navigation callbacks exactly. No route additions, selection defaults or fabricated content.
Accessibility: selected state must have text/semantics plus color; cards expose clear targets; common checklist. Owner emulator checklist: home with/without recent items and active run; picker loading/empty/selected; gallery category/selection/details; verify long lesson titles and scroll.
Evidence path: features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVEV_V2_20261113.md.

### V3 — existing flow screens

Screens: TopicScreen, DrawingGuideScreen, ContextScreen, CaptureScreen, UnderstandingScreen, StoryScreen, HandoffScreen, ActivityScreen, TranscriptReviewScreen.
Sample reference: P03 .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:719-860; P04 .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:861-1005; P05 .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:1006-1224; P06 .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:1225-1372; P07 .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:1373-1510 and P08b .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:1746-1846 for presentation references only.
Apply one-column step/content/action grouping, readable instruction/story cards, distinct informational notices, native capture preview framing and consistent primary/secondary actions. HandoffScreen and ActivityScreen get only layout/color/spacing changes for their current UI; P07 status/progress/retry and P08b activity selection/completion are not added. TranscriptReviewScreen keeps its current transcript review states; no sample waveform or new recording/transcription behavior is added.
Preserve existing topic/idea validation; guide step order/current index/empty/skip and back/next callbacks; context confirmation; capture permission/picker/preview/loading/error states; current subject review/confirmation; story draft/rewrite count (including existing limit of three)/revision confirmation; current Handoff event/pass states; Activity requested/busy/error/fallback/empty/results/source/skip behavior; TranscriptReview transcript/error/busy/edit/confirm/continue-without-audio states. No API, timer, retry, route, stage, state, or content changes.
Accessibility: camera/permission actions have labels; controls stay usable with keyboard/large text; current destructive/confirmation cues remain; common checklist. Owner emulator checklist: guide with and without steps; capture permission/preview/error; understanding loading/review/confirmation; story draft/rewrite limit/confirm; Handoff's current states; Activity request/fallback/results/error/skip; TranscriptReview content and keyboard.
Evidence path: features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVEV_V3_20261113.md.

### V4 — existing history, quota, notifications and sharing surfaces

Screens: StoryHistoryScreen, LessonHistoryScreen, QuotaScreen, NotificationsScreen, ProfileSharingScreen.
Sample reference: P09 .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:1964-2201; P12 .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:2835-3074; P13 .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:3075-3396; P10 profile detail rows .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx:2249-2528.
Apply compact row/card grouping and the status, empty, loading and error hierarchy already present. Restyle the current quota summary, notification rows/read states and sharing cards as rendered today. Do not add filters, detail routes, feedback, purchase tiers/payment, share dialogs or notification behaviors. Do not copy sample fixture statuses or implement unavailable functionality.
Preserve StoryHistory run states, loading/empty/error, cancel/delete eligibility and confirmations; LessonHistory delivery list, feedback state/validation, loading/empty/error and pagination; quota not-configured/value/loading/error; notifications read/unread/loading/empty/error/pagination; and sharing profile/form validation, loading/error/empty, grant labels/states and revoke availability. Do not add filters, selected-run details, routes or behavior. apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx:224-261 currently mounts these screens and remains H. The backend routes behind them do not exist yet. Preserve current route availability and all current states exactly.
Accessibility: history selection/status and notification read state must be programmatically and textually clear; balance is not conveyed by color; common checklist. Owner emulator checklist: history run/delivery list, cancel/delete and feedback states, empty/error; quota loading/value/error; unread/read notification rows; sharing grant statuses and revoke availability; verify baseline routes only.
Evidence path: features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVEV_V4_20261113.md.

## 6. Exact proposed allowlists

Modes: E = editable existing presentation path; N = exact new implementation/evidence path; R = read-only reference; H = exact hash-only frozen path. There are no wildcard entries. The effective list for each checkpoint is its E rows and N rows plus every Shared H and Read-only R row. No unlisted repository path is authorized. E/H/R pins below are the current working-tree snapshot re-hashed for this draft; sizes are bytes and each SHA-256 value is full length. The pre-existing modifications to CONTEXT.md and STATUS.md are R-only and must remain untouched.

E rows are tagged V0-V4. H and R rows apply unchanged to each checkpoint. ui.tsx is the only file opened from the previous H set: it moves to E in V0. Every other H row stays byte-identical. In particular ParentApi.ts, ParentPorts.ts, ParentApplicationModule.ts, ParentLearningUseCases.ts, types.ts, package.json, pnpm-lock.yaml, tests and scripts are frozen. ParentExpoApp.tsx, navigation/controllers, all domain/application/infrastructure paths, theme.ts and test files remain H. No test or validator file is editable.

### N — exact new paths by checkpoint

| Mode | Checkpoint | Exact path | Draft snapshot |
|---|---|---|---|
| N | V0 | apps/ui-mobile/src/parent/presentation/components/parentUiTokens.ts | Absent at draft snapshot |
| N | V0 | features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVEV_V0_20261113.md | Absent at draft snapshot |
| N | V1 | features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVEV_V1_20261113.md | Absent at draft snapshot |
| N | V2 | features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVEV_V2_20261113.md | Absent at draft snapshot |
| N | V3 | features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVEV_V3_20261113.md | Absent at draft snapshot |
| N | V4 | features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVEV_V4_20261113.md | Absent at draft snapshot |

### E/H/R — pinned existing paths


#### E — editable existing paths

| Mode | Checkpoint | Exact path | Bytes | SHA-256 |
|---|---|---|---:|---|
| E | V0 | apps/ui-mobile/src/parent/presentation/components/ui.tsx | 11444 | 722636038EE8CBDFA36A90F6D102ABB4F69A43DC5B6848978EEC8795DFFDB773 |
| E | V0 | apps/ui-mobile/src/parent/presentation/screens/ParentBottomBar.tsx | 2054 | 4E8CB3F6B92AE8614DBE282E623A4E769CF16574EF0B14CAAC468B3A7C054358 |
| E | V1 | apps/ui-mobile/src/parent/presentation/screens/AuthScreen.tsx | 4101 | DADAC33D4EA38F813C4549DE3959D3405FE2EA37C2ECE498DDD2CFDD25336DEC |
| E | V1 | apps/ui-mobile/src/parent/presentation/screens/ProfileScreen.tsx | 4019 | 66E39128D43B3D5E4F497785B4E986C82E23BFC4D1CC91771F6F43B8422D4CA4 |
| E | V1 | apps/ui-mobile/src/parent/presentation/screens/ProfileFormScreen.tsx | 3169 | C20BDE89B47BFF70F7389E9D8694952FE648B45B0A70ED36540D9B4CF5D6630F |
| E | V1 | apps/ui-mobile/src/parent/presentation/screens/AccountScreen.tsx | 3187 | 2A350B4BD4949DCABCA2287DC390581E69B917956A8CF811B2E92AC32205B3B0 |
| E | V1 | apps/ui-mobile/src/parent/presentation/screens/SettingsScreen.tsx | 2191 | FD1015ACF453F3C303392F4A005F60EDBBD3F791BDF365AD6996F4316C81A185 |
| E | V1 | apps/ui-mobile/src/parent/presentation/components/GoogleSignInButton.tsx | 2562 | 26F0BF8BAB3AC1BB47AEC341539ADDCC870AE49D2CE76DD58716053B791EF5C9 |
| E | V2 | apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx | 4838 | A4A29FCA5B3EF090A22779214939A0DE6165F96276C9AEA58E0C2E6CD4632B9F |
| E | V2 | apps/ui-mobile/src/parent/presentation/screens/LessonPickerScreen.tsx | 1595 | C43EC59DBA63C00E9C9489072BF014060AF33AE3C93198F29D8BAD78903782B0 |
| E | V2 | apps/ui-mobile/src/parent/presentation/screens/LessonGalleryScreen.tsx | 9876 | 35D75628DF9220FABA787010E5E40A895FA99AE3A3A34F325E7B752DDFB04003 |
| E | V3 | apps/ui-mobile/src/parent/presentation/screens/TopicScreen.tsx | 6667 | 8A87F7C3769CD57DF9F97E21D85163FF448409B586E1C6CFADB9C16937B157D5 |
| E | V3 | apps/ui-mobile/src/parent/presentation/screens/DrawingGuideScreen.tsx | 2814 | 45D6310ABB43B5C0ECD5AE854D6C906AB9919DB67E179510088BCB82B4235B9F |
| E | V3 | apps/ui-mobile/src/parent/presentation/screens/ContextScreen.tsx | 2851 | 79EAC93B95E8F02E927E80D3BDE34CAADE07C550F1B0B99D5373AE8B494CB68E |
| E | V3 | apps/ui-mobile/src/parent/presentation/screens/CaptureScreen.tsx | 4266 | 49DD0029CF29075E042D09F6017DB8CC37449CE91E35095DB6A61196D942A102 |
| E | V3 | apps/ui-mobile/src/parent/presentation/screens/UnderstandingScreen.tsx | 2097 | 8F21667581CBB1F89C80309E0FCBD0CC71F7A9909AF10B4A18ED38DB03216D8E |
| E | V3 | apps/ui-mobile/src/parent/presentation/screens/StoryScreen.tsx | 3891 | 51FF610C83D79002C248B3447DCFE7A7758E9EA7DE80975B872E1E9070301FB9 |
| E | V3 | apps/ui-mobile/src/parent/presentation/screens/HandoffScreen.tsx | 1704 | 18C2DB25669A1020F1D593F532E4C38F1905F2EF296C02245C7D2DF2E925EA7C |
| E | V3 | apps/ui-mobile/src/parent/presentation/screens/ActivityScreen.tsx | 3462 | 64CD3C7CDA5291C4EA69363A77EEF5872EAC26B02A2C908C1B9455EAC00A07A7 |
| E | V3 | apps/ui-mobile/src/parent/presentation/screens/TranscriptReviewScreen.tsx | 2360 | 8834A9E90745BEBD3F83483A2A5C0A85F92231D2073A91E92BAFEBFE93944823 |
| E | V4 | apps/ui-mobile/src/parent/presentation/screens/StoryHistoryScreen.tsx | 3716 | AA1138C6AB64B9E7EC3D327AE01360DFE5D1512744410F07EB207C5BEE57A759 |
| E | V4 | apps/ui-mobile/src/parent/presentation/screens/LessonHistoryScreen.tsx | 3421 | 6D9B1DB17245635F583BDBC2DE559549ABDC75FFAAED26A9D702F4FED7429ABB |
| E | V4 | apps/ui-mobile/src/parent/presentation/screens/QuotaScreen.tsx | 1480 | B6DD6051244288845178E195BFBD5BB69A4748897293BDC7AA37EAB5512FB93C |
| E | V4 | apps/ui-mobile/src/parent/presentation/screens/NotificationsScreen.tsx | 1798 | 5C9AC558A53CE96BC13771835D3B5A0FF3AC0FE21B18D96EE85C780AFD366E7E |
| E | V4 | apps/ui-mobile/src/parent/presentation/screens/ProfileSharingScreen.tsx | 3529 | A9EB79B7BC2C5E1EEFF8304299F37C251BF285DD5500F673194C67064773CA29 |

#### H — frozen hash-only paths, shared by V0-V4

| Mode | Checkpoint | Exact path | Bytes | SHA-256 |
|---|---|---|---:|---|
| H | Shared | apps/ui-mobile/src/parent/application/ParentApplicationError.ts | 1027 | 3087B87025511877F983BF0A9331E11DF110078F938354C87800E61CFF4BD2AF |
| H | Shared | apps/ui-mobile/src/parent/application/ports/ParentApplicationModule.ts | 2164 | 0373643C8C92C9EA6D144C22F27202D8A09163FB03D369A786982E9413CBB9A3 |
| H | Shared | apps/ui-mobile/src/parent/application/ports/ParentPorts.ts | 8472 | 62CDC570BEEE074D1BD4558A5567E37CD2911DC7041D4689F231CC2884182551 |
| H | Shared | apps/ui-mobile/src/parent/application/use-cases/ParentAccountUseCases.ts | 765 | 1EDA6FD349FA8E1E719C97C3A1551B90F7BDCFAB236C81F5E3FDD8BE39560635 |
| H | Shared | apps/ui-mobile/src/parent/application/use-cases/ParentLearningUseCases.ts | 6766 | 8812D4AB0DAB6DB7C35CDA9F14EEEB953201AC0157DDE1C4C2216A8FD40C43AE |
| H | Shared | apps/ui-mobile/src/parent/application/use-cases/ParentLessonUseCases.ts | 711 | 0C46FF6814B06E6363CBE779C63A2AD0EB2F59C6DFCDD5206B7756C5748CB59C |
| H | Shared | apps/ui-mobile/src/parent/application/use-cases/ParentPlatformUseCases.ts | 2722 | 4E4FB4449451B036FA479D73DD5E4F1CE5A4D27169B5603578B6221486AB2A16 |
| H | Shared | apps/ui-mobile/src/parent/application/use-cases/ParentProfileUseCases.ts | 2994 | C3A88AB853C6EE96882ABF950EAC76032E68D97D6E52D7A42EF63C869E99CCC2 |
| H | Shared | apps/ui-mobile/src/parent/domain/types.ts | 10152 | 990FA43EF6E04874FD72E9E62AC7CCAD9332F687BFE92A64586A87A7010A0240 |
| H | Shared | apps/ui-mobile/src/parent/domain/storyDraft.ts | 2320 | E8D24ED55701511EB5F13A1E6C32CFE0DBACA459D444DD27F55248EAD4ED9C0C |
| H | Shared | apps/ui-mobile/src/parent/domain/profileRules.ts | 356 | 25EA93AD268DC49704D64F87A2D1252983F745A530CB43D8D67AEFD3EE16C3EE |
| H | Shared | apps/ui-mobile/src/parent/infrastructure/config.ts | 1049 | F0C1E0198460E9A432E81D9E8724BCC35CD030CA8C411F2050503F1C87C0FF07 |
| H | Shared | apps/ui-mobile/src/parent/infrastructure/auth/ParentAuth.ts | 10305 | BBFEEF77C3CABD2632AFE7EE96D6996509C809BB8521FBD80326223961DD6077 |
| H | Shared | apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts | 25559 | 182EBB83A8A9A284444FAADE68740C5DD50CDD0F387393A4577A2C7AD626F7DE |
| H | Shared | apps/ui-mobile/src/parent/ParentModule.ts | 1238 | B1E6A5236F57E0A6A4950150A245C29FE2098E75F95C55B2EB1787360806EA12 |
| H | Shared | apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx | 16836 | 5861CED5A1D98A4D8E00251B278C9AAEC271E4F4D4292E59691A20901E21508C |
| H | Shared | apps/ui-mobile/src/parent/presentation/navigation/parentFlowV1.ts | 13722 | 70872D3BE7316D88B2608B16C9D153F4F086F5654D007ABFC668A02CF5CBE242 |
| H | Shared | apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts | 34507 | 19EEEB022C9874622A682D9DD822BD2982CE05F4840BEEE6E23A617315CD7DCA |
| H | Shared | apps/ui-mobile/src/parent/presentation/navigation/useParentPlatformController.ts | 7643 | BB91CC698A6C9512DB6ABEE7691D78214EC8309D772B014464DA16C999DCFDFA |
| H | Shared | apps/ui-mobile/src/parent/presentation/navigation/workflowTypes.ts | 755 | 611A0C2207287963762295F42C02323AE297F20C4D5833F5304AD71B8371F29A |
| H | Shared | apps/ui-mobile/src/parent/presentation/screens/catalogViewModel.ts | 1962 | 5BE1210C95C9F1CEBABADEE7DAD2169620B5B438BA85DE24941236DF018630F0 |
| H | Shared | apps/ui-mobile/src/theme.ts | 2134 | 7114FB92B63855E2FE9E6B77D1111AAD8FB1F33555ABBF321B6D3DE1D8F16B46 |
| H | Shared | apps/ui-mobile/package.json | 2081 | AC8C5AB17D61B4DD126D28D9918CB4E4EB5C40EEFD3B4C965D9597294B9CD9FF |
| H | Shared | pnpm-lock.yaml | 470780 | 5D778524730134CAFE360564408CBF45030B476C99A69CCD32897BAB55559A72 |
| H | Shared | apps/ui-mobile/tests/apiRetryIdentity.test.mjs | 3188 | C0DC06450146667AC16C8108960E892F30B4D34AD0A1B0AD3EBB3EC19D5C6054 |
| H | Shared | apps/ui-mobile/tests/catalogViewModel.test.ts | 3254 | 8FAA29A92BD4D750C27E2109256611BA3DA8ECFE1BE72044127A81B78699C978 |
| H | Shared | apps/ui-mobile/tests/mainFlowSafety.test.mjs | 7985 | 41B82F60E83B17DBB09F7195ACF122E3653046A49822D42D5416E39B53582D74 |
| H | Shared | apps/ui-mobile/tests/parentApiI2Contract.test.ts | 17370 | C7FC2FB9421AF32553EDABB4F633547C842A825161FA41AB524CA8DCAC541075 |
| H | Shared | apps/ui-mobile/tests/parentFlowV1.test.ts | 13508 | 7F4623080EDE3980D96CD426242C161A630F198B1627685D6B4DB0C0F4A9FCD5 |
| H | Shared | apps/ui-mobile/tests/parentLearningI2.test.ts | 5841 | E92C927657EE1AF2AD3152DEEE6519AF56B866BDECCDB00E7A7BD5BC03884892 |
| H | Shared | apps/ui-mobile/tests/storyDraft.test.ts | 1770 | 07C8BE23A875F2082CDC2626A23E4462A46CF61525BD487F9053CCD00CBCFC50 |
| H | Shared | apps/ui-mobile/scripts/validate-ui-copy.mjs | 21206 | 5AD006820035DF1B4DF1489338CBC08A06B877B80B2B345C1A82806D729A0391 |
| H | Shared | apps/ui-mobile/scripts/start-android-dev.ps1 | 4507 | 3EF2CE8D9232CF483121794FB19B2577531686511C721D4D7EC2BA215850EB18 |
| H | Shared | apps/ui-mobile/scripts/ui-verification.md | 126 | AC355095C4FFC7D3930E7104031B40F73966ED0CAD06850811457B1B913AE3D9 |
| H | Shared | apps/ui-mobile/scripts/component-registry-check.md | 94 | 074D275BB80B32EBB84BFECC68048B1DA8AFEC4A0720CAC2BA41B798D39833D0 |

#### R — read-only references, shared by V0-V4

| Mode | Checkpoint | Exact path | Bytes | SHA-256 |
|---|---|---|---:|---|
| R | Shared | .worktrees/ui/apps/parent-ui/src/pages/ParentScreens.tsx | 146061 | C730BC255D193C1F7E86502E66808D73821D954168CC8C027E5979F21FCC575B |
| R | Shared | .worktrees/ui/apps/parent-ui/src/components/Kit.tsx | 15183 | 45EAF898312297BB5F97B6AA4E6FD96C6354AEC1003A7CE21319D0E7AFFCF93E |
| R | Shared | .worktrees/ui/apps/parent-ui/src/components/MobileLayout.tsx | 21561 | 2AD1684F22EF7643E737B415B30E819A2A1098A0250F51EF02CF771F5E1D0F7C |
| R | Shared | .worktrees/ui/apps/parent-ui/src/styles/tokens.css | 62328 | 84DB43957C041BBC9A60E4690DE93295D89E75124CA09E600B6E8F3734E7300F |
| R | Shared | .worktrees/ui/apps/parent-ui/src/data/mockParentData.ts | 18193 | 7ED10C9590FAB3BF659B7D8D2E3FADB2E888329C565300C40445CE6424D92B26 |
| R | Shared | tmp/ui-port-plan/PORT_MAP.md | 5823 | 28CC2356D8913335E265802297F217EBAB573E37030DD8A3BC2F8A3A39BE0ECB |
| R | Shared | tmp/ui-port-plan/ASSETS_AND_GATES.md | 5663 | DF0F9B40164C2CB79B78CDF30CD9E3B70867464FE03F474A706F0C0007201358 |
| R | Shared | tmp/ui-port-plan/SAMPLE_INVENTORY.md | 10325 | 4CBC7CD3644F989BD3D01A3214ED2DD2757F7883DB4DD1D0247CDB1769089204 |
| R | Shared | tmp/ui-port-plan/TARGET_INVENTORY.md | 5961 | 931B43385207309048012DCEA53923EF556B29D945A6EA0B313C23266A52CFB0 |
| R | Shared | tmp/ui-port-plan/ANDROID_READINESS_R2.md | 6358 | 096F0BE668CC61172AFF9F032DBC751E64BABDD3B43E6ECF492B3EE996AB898E |
| R | Shared | docs/context/SRS_AUTHORITY.md | 4054 | 032223EDDD46D251DE052C54BFF16AB1D4D794F865A457272507D893E3C1521F |
| R | Shared | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md | 553948 | 70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B |
| R | Shared | features/FEAT-081-parent-ui-mobile-port/CONTEXT.md | 21613 | 58FC49D0F444512BB7D7513A348FB055698BCBEBC5242C70F99744A00050FBBB |
| R | Shared | features/FEAT-081-parent-ui-mobile-port/DECISIONS.md | 13613 | 4FC79E32E838C5A07E01CA601F28AED35B437334FE4D73493E84BB5DF4F94FB3 |
| R | Shared | features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_4.md | 18717 | 6D3FEF1B2C24595EBC4F6499368330C485471AF59A4E9C974CF1F5C97BD71E0A |
| R | Shared | features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVE3_20261113.md | 27257 | C3EB7AA66C45652F952B944A5DC1DE53440F10D383414558F934C8B1605F70AA |
| R | Shared | features/FEAT-081-parent-ui-mobile-port/status/STATUS.md | 16314 | BE3EEF0541B90A0105506C6B6371AB45B9A0C20C4E220B4804345AA633240C82 |


## 7. No-behavior-change proof and offline acceptance

Review the complete diff for each checkpoint. Only presentational styles, visual JSX grouping/order, spacing, color, typography and component shape may differ in E paths. Make no copy changes except text strictly required by layout with separate owner approval. New code is limited to the N token module and additive presentational exports described above plus the checkpoint evidence report. There must be no change to state hooks, state transitions, event handlers, callback payloads, routes, route availability, conditions/branching based on state, validation/business rules, API/port calls, storage, fixtures, test code, contracts or content sources. Reviewer compares screen props/exports, callbacks, route wiring, accessibility labels/roles, and all H pins. Any unapproved string change, behavioral difference or unexplained H mismatch stops the checkpoint.

The existing 59 tests and existing UI-copy validator must remain green at each checkpoint. Do not add or edit tests in this presentation wave. The coordinator runs the test and typecheck command set. Codex runs none. The apps/ui-mobile/scripts/validate-ui-copy.mjs validator is included in the existing test script but does not scan Parent screens; keep its script frozen. At acceptance, compare every string in every edited file before/after and require owner approval for any text strictly required by layout. Owner-run validators and emulator results are recorded in the checkpoint evidence report; screenshots are not committed, and the report keeps references and the owner result only.

Offline acceptance criteria:

- WV-AC1 — Scope: every changed existing path is in that checkpoint's E list; every new path is an exact N entry; no unlisted file, asset, package, lockfile, route, test, or contract changes.
- WV-AC2 — Native rendering: sample hierarchy and visual tokens are expressed only with React Native views/text/pressables/styles; no React DOM, HTML, CSS, browser frame, sample asset or sample implementation is copied.
- WV-AC3 — API compatibility: every ui.tsx existing named export, property shape, optional default, prop, callback signature and all screen APIs remain backward-compatible; ParentBottomBar retains its four tab IDs and activeTab/onNavigate API.
- WV-AC4 — Behavior: all existing callbacks, state transitions, form validation, loading/empty/error/disabled/confirmation states, content and route availability match the pre-checkpoint native baseline.
- WV-AC5 — Accessibility: 44 dp minimum interactive targets, 48 dp primary actions, system text scaling, safe areas/keyboard access, readable contrast, labels for icon controls, and non-color state cues are verified on the owner emulator.
- WV-AC6 — Regression and copy: the existing 59 tests and UI-copy validator pass; typecheck has no diagnostics; every string in edited files is compared before/after; there are no copy changes unless strictly required by layout and separately owner-approved; no tests or validators were run by Codex.
- WV-AC7 — Freeze: every H path is byte-identical to the pin in this draft; package and lockfile pins match; tests and scripts stay untouched.
- WV-AC8 — Visual review: owner runs the 6.1-inch portrait emulator walkthrough for all checkpoint screens and representative existing states; owner screenshots may support review but are not committed; the evidence report records their references and the owner result. Clipping, overlap, unreachable controls or text truncation blocks acceptance.
- WV-AC9 — Documentation: the checkpoint has its own implementation report at its exact N path, command log, owner screenshots/evidence references, pin result and separate commit reference.

Offline proof cannot prove appearance on a physical device, all Android OEM font/inset differences, live API responses, server state, real AI/video behavior or routes unavailable in the sample. The owner emulator walkthrough is required; real API acceptance belongs to separately authorized work.

## 8. Command ceilings, ownership and stop conditions

Per-checkpoint ceilings are independent. Run a baseline and a post-change check when appropriate; stop at the ceiling.
| Command and working directory | Ceiling per checkpoint | Runner |
|---|---:|---|
| pnpm run test from apps/ui-mobile | 2 | Coordinator |
| pnpm run typecheck from apps/ui-mobile | 2 | Coordinator |
| python tools/validate_harness.py from repository root | 2 | Owner |
| python tools/validate_repository_security.py from repository root | 2 | Owner |
| python tools/validate_architecture.py from repository root | 2 | Owner |
| git diff --check from repository root | 2 | Owner |
Codex runs none of these commands. Owner runs the listed validators and emulator walkthrough. Owner/coordinator record every invocation in that checkpoint report. There is no installation, network, Modal/provider call, backend or runtime request in this plan.

Stop a checkpoint if: its specific launch is absent; a file outside E/N changes; any H pin differs; an E file requires state/route/API/test changes; 59 tests or the copy validator fail; typecheck/owner validation fails; a new dependency or asset appears necessary; an existing state is missing or cannot be represented without behavior changes; accessibility/safe-area/keyboard criteria fail; or visual approval is withheld. Do not proceed to the next checkpoint or amend a shared record without separate owner authorization.

## 9. Explicit exclusions and approvals

No P07 video job status, P08 player/landscape/post-video state, P08b new activity flow, P08c session feedback, P14 recovery, P15 registration, API/backend/route/controller/state work, test edits, package/lockfile changes, dependencies, sample content/assets, brand art, fonts, or screen not currently present in apps/ui-mobile. P07-P09 behavior remains deferred until real APIs exist. Existing current screen presentation can be aligned only as listed and only with its current state machine.

This document is Plan Revision 5 and is not itself an approval record. D-013 is recorded in features/FEAT-081-parent-ui-mobile-port/DECISIONS.md and Addendum 11 approves this plan only; Wave V is NOT LAUNCHED. Each checkpoint still requires its own separate explicit launch instruction. No implementation, test run, validation, emulator activity, staging, commit or push is authorized by this plan alone.










