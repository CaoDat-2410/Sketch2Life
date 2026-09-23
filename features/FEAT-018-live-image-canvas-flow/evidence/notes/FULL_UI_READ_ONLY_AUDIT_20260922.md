# FEAT-018 full UI read-only audit — 2026-09-22

Status: `UI_AUDIT_COMPLETE — NO CODE CHANGED`

## Audit identity

- Inspected branch: `codex/feat-018-contract-plan`
- Inspected base commit: `f98958f6690e6d233ca79d8be1defec56fdd85be`
- Device: Android Emulator `emulator-5554`, 1080x2424, density 420
- Package: `com.sketch2life.mobile/.MainActivity`
- Local surfaces observed: Metro `:8081`, backend `127.0.0.1:8000`
- Audit method: Android `adb screencap`, UIAutomator hierarchy, developer quick-switch traversal of all
  12 reachable BaoVC screens, read-only React Native source/style inspection, and comparison with the
  owner-provided bird/Pixi/activity screenshots.
- Live-provider use: none. No Lightning/model request was sent.
- Data: existing synthetic/non-child bird drawing and process-local demo state only.

## No-code checkpoint

No application source, runtime configuration, contract, fixture, style or asset was edited while
this audit was performed. Before the audit, the worktree already contained uncommitted FEAT-018
application/test changes from the prior approved activity recovery task; their path set remained
unchanged during this audit. Only the approved plan, task approval record, context and this audit
record were written.

Checkpoint: `UI_AUDIT_COMPLETE — NO CODE CHANGED`

## Screen coverage

The following current screens were opened and inspected without source changes:

1. Splash
2. Onboarding
3. Home Dashboard
4. Child Profile
5. Capture / Upload, including manual narration text
6. Voice Recording
7. AI Processing
8. Scene Understanding / adult confirmation
9. Story Preview
10. Activity Recommendation
11. Activity Detail and Pixi WebView area
12. Feedback Loop

Source inspection additionally covered busy/disabled/error branches, navigation history, hidden dev
mode, renderer bootstrap/messages, text inputs, inline workflow errors and existing result recovery.

## Finding matrix

| ID | Screen/state | Audience | Severity | Current behavior and evidence | Expected behavior | Approved repair/acceptance | Phase |
|---|---|---|---|---|---|---|---|
| UI-001 | Understanding | Child/adult | P1 DEMO_BLOCKER | Bird response shows English `branch`, `leaf`, `perching`, aggregate phrases and duplicate leaves; cards expose `subject` and `confidence`. | Canonical, deduplicated Vietnamese labels with simple roles; raw evidence remains backend-only. | Closed localization/dedup policy; no covered English or duplicate canonical concepts in rendered cards. | B–D/G |
| UI-002 | Understanding/topic | Child/adult | P1 DEMO_BLOCKER | Header says the AI understood the story completely and displays 100% confidence while output is visibly incomplete/mislabeled. | Calibrated language that invites adult confirmation and does not overclaim certainty. | Replace certainty claims with concise review copy; confidence is optional adult detail, not child headline. | C/D/G |
| UI-003 | Story Preview | Child | P1 DEMO_BLOCKER | Preview is hard-coded to butterfly scenes `Thức dậy`, `Bay lượn`, `Hút mật` even for a bird image. | Preview derives only from current topic/source art and no unsupported pseudo-scenes. | Replace fixed butterfly scene cards with grounded topic/source preview; no video implication. | G |
| UI-004 | Recommendation | Adult | P0 FLOW_BLOCKER | UI renders one already-selected age-baseline activity instead of allowing choice; bird led to `TPL-ACT-0026-V2` pouring. | Up to three prioritized, strict-fit, topic-related cards; adult selects one before compilation. | V2 runtime + bounded recommendation contract + exact selected-option chain; unrelated fallback absent. | E/F/G |
| UI-005 | Recommendation | Child/adult | P1 DEMO_BLOCKER | Displays template/activity IDs, backend/catalog/mock wording and an English fallback reason. | Vietnamese title, one-sentence action, duration and friendly relevance reason only. | IDs remain transport/audit fields and are never rendered in primary UI. | E–G |
| UI-006 | Activity Detail | Child/adult | P1 DEMO_BLOCKER | Title is `TPL-ACT-0026-V2`; material cards are `GMAT 0026 PRIMARY/SUBSTITUTE`; age renders `3.5–5.916666666666667 tuổi`. | Reviewed Vietnamese title/material labels and human age band such as `5–6 tuổi`. | Display metadata read model; bounded age formatter; no IDs in rendered detail. | E–G |
| UI-007 | Activity Detail | Adult | P1 DEMO_BLOCKER | Raw safety IDs `ACT-0026:HAZARD/STOP` are presented as instructions. | Plain Vietnamese safety guidance, with adult details collapsed by default. | Map catalog safety text; raw IDs remain diagnostics only. | E/G |
| UI-008 | Activity continuity | Child/adult | P0 FLOW_BLOCKER | Bridge inserts `con chim` into unrelated pouring steps, making the activity appear personalized without semantic continuity. | Every displayed instruction directly continues the confirmed image/narration topic and objective. | Strict viability before exposure; no generic age-only fallback; identity continuity tests. | E/F |
| UI-009 | Pixi | Child/adult | P0 FLOW_BLOCKER | Renderer HTML loads, but launch fails Zod validation; empty stage remains and technical error is inline. | Source drawing reveals in WebView; failure preserves source preview and offers retry/back. | Omit Python `None` fields, parse actual command with actual TS schema, modal recovery. | H/G |
| UI-010 | Errors, all workflow screens | Child/adult | P1 DEMO_BLOCKER | Errors are inline red text and may contain backend, provider, schema, protocol, version or workflow jargon. | Friendly modal with one safe sentence and recovery action; no code/details rendered. | Closed UI error taxonomy, app-level modal, internal diagnostics only in development logs/tests. | G |
| UI-011 | AI Processing | Child | P1 DEMO_BLOCKER | Copy exposes backend, admission, ASR, Vision, Lightning and Pixi; CTA asks the user to call the backend. | Simple child-facing progress stages and one clear retry/start action. | Replace technical checklist with 3–4 plain-language steps; provider details hidden. | G |
| UI-012 | Global workflow notices | All | P1 DEMO_BLOCKER | Old notice `Hoạt động đã được bàn giao...` appears on unrelated screens after dev navigation, showing global notice leakage/stale state. | Notice belongs to the operation/screen that created it and clears on incompatible navigation/new flow. | Scope notices by screen/operation or consume them on navigation; regression test stale success state. | G |
| UI-013 | Feedback | Adult | P1 DEMO_BLOCKER | Defaults mention `chú bướm`, `vòi bướm`, paper wings regardless of selected topic/activity. | Feedback labels/tags start neutral or derive from exact selected activity. | Remove butterfly defaults; derive concise observable prompts from selected activity; no fabricated completion. | G |
| UI-014 | Feedback | Adult | P2 CHILD_UX | Labels mix English (`Interest`, `Independence`, `Fine Motor`) and default to completed, 5/5 interest, 4/5 independence. | Vietnamese-only labels and neutral unselected initial values. | Require deliberate adult input; no pre-filled success bias. | G |
| UI-015 | Native frame | All | P2 CHILD_UX | Android system status bar and an in-app fake status bar are both visible, producing duplicate clocks/network/battery UI. | One status bar on native Android; optional simulated frame only on web preview. | Hide the mock mobile status bar/home chrome on native; retain web device frame. | G |
| UI-016 | Capture | Adult | P2 CHILD_UX | Two adjacent image actions (`Chọn ảnh tổng hợp`, `Đổi ảnh đã chọn`) compete even when one image is already visible; explanatory copy includes TTS/AI. | One state-aware image action plus simple narration choices. | Use `Chọn ảnh`/`Đổi ảnh`; explain manual text without TTS/AI jargon. | G |
| UI-017 | Voice | Child/adult | P2 CHILD_UX | Initial state visually emphasizes a red stop button at `00:00`, while instruction says tap the red middle button to continue; recording/start meaning is ambiguous. | Clear `Bắt đầu kể`, recording and `Dừng ghi âm` states with matching icon/color. | State-specific accessible controls and copy; no stop affordance before recording. | G |
| UI-018 | Text inputs/keyboard | Adult | P1 DEMO_BLOCKER | Capture and feedback screens have no `KeyboardAvoidingView`; CTA can be covered and scrolling/focus behavior is not defined. | Inputs and CTA remain reachable with keyboard and large text. | Add keyboard avoidance/tap persistence and emulator test for manual narration and feedback notes. | G |
| UI-019 | Accessibility | All | P1 DEMO_BLOCKER | Static audit found 60 `TouchableOpacity` instances plus shared button with zero explicit accessibility labels/roles in the audited files. | Interactive controls expose role, label, hint/state and at least 48x48 target. | Upgrade shared controls and critical touchables; accessibility tree regression/smoke. | G |
| UI-020 | Typography/touch targets | Child | P2 CHILD_UX | Many labels use 9–11px fonts; several controls are 26–44px and text truncates in pills/cards. | Readable hierarchy at Android text scaling and minimum touch target. | Raise critical text/control sizes, allow wrapping, test default and enlarged font scale. | G |
| UI-021 | Dev mode | Demo integrity | P1 DEMO_BLOCKER | Triple-tapping the fake clock enables a full English technical screen switcher on native. | Dev navigation requires an explicit development flag and is unreachable in normal demo mode. | Remove native hidden gesture; gate switcher behind explicit development configuration. | G |
| UI-022 | Dashboard | Adult | P3 POLISH | Recent stories and suggested activity are hard-coded and can be mistaken for saved runtime history before auth/persistence exists. | Clearly labeled sample/empty state consistent with process-local demo. | Mark as sample or use a friendly empty state; do not imply persistence. | G |
| UI-023 | Profile | Adult | P2 CHILD_UX | `Bỏ qua` is offered although image workflow needs a valid age/profile to filter activities safely. | Demo profile/age remains explicit and required before recommendation. | Disable ambiguous skip or explain/use the safe default profile deliberately. | G |
| UI-024 | Back/retry/double tap | Adult | P1 DEMO_BLOCKER | Existing code uses mixed local/global busy state; some generic touchables have no visible disabled reason. | One operation at a time, stable prior result, predictable back/retry. | Preserve synchronous locks, contextual disabled copy and exact-state recovery tests. | F/G |
| UI-025 | No-video boundary | All | P1 DEMO_BLOCKER | An unreachable legacy `VideoPlayerScreen` still contains play/share/save-video UI and butterfly story content. | Normal BaoVC routing cannot reach or imply generated video. | Keep the screen excluded from route metadata/exports used by production demo; add reachability test. | G |

## Prioritized repair backlog

1. P0 first: V2 activity continuity/selection (`UI-004`, `UI-008`) and Pixi bridge (`UI-009`).
2. P1 data truthfulness: understanding/topic normalization (`UI-001`, `UI-002`), real display
   metadata (`UI-005`–`UI-007`), contextual preview/feedback (`UI-003`, `UI-013`), modal error
   architecture and state hygiene (`UI-010`–`UI-012`, `UI-018`, `UI-019`, `UI-021`, `UI-024`,
   `UI-025`).
3. P2 child-friendly polish: capture/voice clarity, Vietnamese-only adult labels, native frame,
   typography/touch sizing and safe profile flow (`UI-014`–`UI-017`, `UI-020`, `UI-023`).
4. P3 demo truthfulness polish: dashboard sample/empty state (`UI-022`).

All findings fit the already approved vision/topic/catalog/Pixi/child-UX plan. No new visual asset,
video, authentication, persistence or incompatible frozen-contract scope was discovered, so no
approval expansion is required before implementation.

## Evidence commands

```text
D:\AndroidStudio\platform-tools\adb.exe devices -l
D:\AndroidStudio\platform-tools\adb.exe shell wm size
D:\AndroidStudio\platform-tools\adb.exe shell wm density
D:\AndroidStudio\platform-tools\adb.exe exec-out screencap -p
D:\AndroidStudio\platform-tools\adb.exe shell uiautomator dump /sdcard/window.xml
rg -n "Backend|Gate|ExperienceSpec|Pixi|protocol|ASR|VLM|catalog|ACT-|TPL-|confidence" apps/ui-mobile
rg -n "TouchableOpacity|accessibilityLabel|accessibilityRole|KeyboardAvoidingView|Modal" apps/ui-mobile
```

Transient audit screenshots were inspected locally and contain only the synthetic bird demo state.
Owner-provided source screenshots remain the attributable visual evidence for the reported live
bird, activity and Pixi defects. Final before/after screenshots will be stored with implementation
evidence after the fixes are verified.
