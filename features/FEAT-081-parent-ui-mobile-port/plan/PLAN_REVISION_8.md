# Wave L — Parent Mobile Visual Rebuild Plan, Revision 8

**Status: DRAFT until Addendum 18 is recorded**
**Plan date:** 2026-11-14
**Baseline commit:** 8f1fef7dafa5c374b2cc2e80562b6a0a78d75288
**Owner call authorization:** OWNER_MODAL_CALL_APPROVED=NO
**Appendix:** PLAN_REVISION_8_SCREEN_MAP.md is the copied, pinned companion screen map.

This plan is approved only when Addendum 18 is recorded. Approval authorizes preparation of one merged L0–L3 goal but does not launch it. The goal begins only when the owner sends its goal text. No checkpoint is launched by this plan-writing task.

## 1. Goal, definition of done, and scope

Rebuild the presentation layout of every Parent mobile screen and shared visual component to match the owner-selected restrained-crayon concept, variant A, while preserving Wave R callbacks, routes, state transitions, API payloads, unavailable states, revision pins, and security boundaries. Wave L runs L0, L1, L2, and L3 sequentially inside one merged goal, with no pause between checkpoints unless the owner interrupts or a blocker stops progress.

Wave L changes presentation composition, information hierarchy, spacing, card and control treatment, decorative code-drawn illustration, and exactly the seven approved Vietnamese copy edits in Section 4.2. It does not change product behavior, route order, API contracts, or persisted data. A development-only preview harness is the sole conditional route-shell addition: it is available only behind an explicit development flag and never enters the normal production flow.

The merged goal is complete when all four checkpoints pass their static reviews, the required evidence sections and snapshots are recorded, the H rows still match, and the authorized coordinator and owner reviews have been completed within Addendum 18 ceilings. Visual review claims are limited to what the owner actually reviewed.

### Non-goals

- No API, controller, domain, route, database, provider, backend, Modal, Android-native, account, authorization, history, lifecycle, quota, video, transcript, or AI behavior changes.
- No production screen or normal navigation flow is added. The approved preview harness is development-only, explicitly flagged, synthetic, marked preview-only, and unreachable in normal production flow.
- No real child data, secrets, production assets, external fonts, new packages, copied assets, generated raster assets, or provider-generated media.
- No changes to SRS copies, Plan Revision 7, package files, or any record except the append-only D-020 and Addendum 18 required to approve this plan. CONTEXT.md and status/STATUS.md contain owner local edits and must remain untouched.
- No staging, commit, push, publishing, test, typecheck, validator, diff-check, installation, network, backend, emulator, ADB, Gradle, or Modal command by Codex.
- No parallel checkpoint implementation: checkpoints share ui.tsx, parentSrsBehavior.test.ts, and the ParentExpoApp preview boundary.

## 2. Authority, preflight, and evidence binding

### 2.1 Current product authority

For FEAT-081 Wave L, Person 2's owner decision dated 2026-11-14 selects the unsigned SRS Rev67 owner-supplied copy as the canonical working SRS. Rev60 is historical for this plan. The owner states that FEAT-063 decision D-203 is being written on the backend line. This is a feature-plan authority decision; it does not edit the repository SRS copy or docs/context/SRS_AUTHORITY.md and does not claim that Rev67 is formally signed.

The planning references are Rev67 §5.1, §7.2 and FR-P requirements, §21.5/21.6, §31.10, and the applicable NFR accessibility and Vietnamese-language requirements. Any requirement that the backend cannot support remains visibly unavailable under D-015 through D-019; the client does not invent route behavior or fields.

### 2.2 Step 0 preflight and pinned inputs

- Worktree: .worktrees/mobile.
- Branch: feature/fe-mobile-remediation.
- HEAD: 8f1fef7dafa5c374b2cc2e80562b6a0a78d75288.
- git status --short: only features/FEAT-081-parent-ui-mobile-port/CONTEXT.md and features/FEAT-081-parent-ui-mobile-port/status/STATUS.md are modified; both are owner local edits and must not be changed. No staged paths.
- Busy check at 2026-11-14 15:36 +07:00: no SOURCE, TEST, RECORD, PLAN, or EVIDENCE file under apps/ui-mobile/src, apps/ui-mobile/tests, features/FEAT-081-parent-ui-mobile-port, or tmp/fe081-waveR2/run_state had changed within the preceding ten minutes. Build caches and ignored files were excluded.

| Pinned planning input | Bytes | SHA-256 |
|---|---:|---|
| features/FEAT-081-parent-ui-mobile-port/DECISIONS.md | 41,836 | 73915C90B13A5A53B1A44D66B078EA041D0C0307070333466F959EE9DAC7E1E1 |
| features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md | 53,749 | F764C3FFF7BABECE29CE087300124CC73A3814DBB7B5B8694F0E783CDC88635C |
| features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_7.md | 70,512 | 7979A7A990C36F159303F3B011D56626CCAA1AB998A6C7C9C7CB25F47ED024C9 |
| apps/ui-mobile/src/parent/presentation/components/ui.tsx | 22,273 | 51BAE1F8E81B560AFEA5389864FE98FC44CB0104C7492FE4CC7D861663A829E8 |
| apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx | 17,590 | FCB0B797C424AB6176B59E88034B954ADA01B7B3544ADAAFCC41ECF7227DA8AA |
| features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md (Rev60 historical) | 553,948 | 70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B |
| tmp/fe081-waveR2/srs_new/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS_Rev67_owner_supplied.md (unsigned Wave L working authority) | 634,291 | B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996 |
| tmp/fe081-waveL/WAVEL_PLAN_DRAFT_1.md | 43,964 | 6FE7A1842B93B2DD1E38CE409F11657303BC4496F26E3AC0D678134794B8DD5A |
| tmp/fe081-waveL/PLAN_REVISION_8_SCREEN_MAP.md | 21,027 | 974C25C93574A32F29680A73B13ABF9D1F5E861B31CEC70DE4C86C2B9EB1FD12 |
| tmp/fe081-waveL/WAVEL_OWNER_QUESTIONS.md | 8,383 | 945E03A8722BBF067D4A00CBD439B0A2F5221AD4F4ABE1117A813FB768A47383 |

The owner decisions from WAVEL_OWNER_QUESTIONS.md are transcribed into D-020 and this plan. The approved screen map is copied to the feature plan folder as PLAN_REVISION_8_SCREEN_MAP.md so later execution does not depend on the scratch input.

### 2.3 Concept and Wave R evidence pins

| Input | Bytes | SHA-256 |
|---|---:|---|
| tmp/fe081-waveR2/concept/index.html | 159,187 | E463FB8C6FF17B757C46D9130D4D2FCB20F3E6B1EE526AB594DD6FDB6B2B8E74 |
| tmp/fe081-waveR2/concept/tokens.json | 9,034 | FF85727B3B328FF7E4D137FCA6DE9BFDBF4D1B921B41034E65ECB5B2ED5AD6DF |
| tmp/fe081-waveR2/concept/contrast.md | 3,672 | E8F741655B689FBEED92F5A5D8C3B9D2BDA4E9F4FE8AF3BE88359E02DBDC197D |
| tmp/fe081-waveR2/concept/README.md | 10,742 | 994AD5B3F71F6138C253BF77E8CF42B81643004DBBD080A6B5B28636518655C3 |

The owner selected variant A. The concept is a 360 × 760 CSS preview, not a React Native implementation. It uses warm paper (#FFF8EA), card paper (#FFFEF8), ink (#342E28), restrained pastel accents, irregular crayon-style outlines, light paper shadows, system fonts, and decorative card tilt up to 0.7 degrees. The contrast report lists minimum normal-text contrast 6.51:1, large-text 12.67:1, focus 5.84:1, and non-text outline 5.13:1. Wave L targets remain at least 4.5:1 for text and 3:1 for UI components.

| Wave R evidence | Bytes | SHA-256 |
|---|---:|---|
| features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R0_20261113.md | 11,562 | 6EB5A9D1BF6F2C261890B36CE23E675D528809D999F2A3DDBE1E82463F37ABDA |
| features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R1_20261113.md | 24,614 | DBD223A8F1D61C22F6F222A9EFF3A1CF5ABBB17855483230A90E86A974E98DF9 |
| features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R2_20261113.md | 16,025 | 1151AD773868DBFEE5620AA18829B993D2D0A0E62F2D5570BACE6963452F96B6 |
| features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R3_20261113.md | 23,761 | A636B5A90D73FB080745A0015F1F122AEDFE8862A88B325B1622682CBB8ADED8 |
| features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_WAVER_R4_20261113.md | 34,437 | 57A494150C069463B592C80EF391F693949333158B79F8AB9F000E88A6D422CE |
| tmp/fe081-waveR2/run_state/RUN_STATE.md | 44,790 | C2197021B4E5F52D0623B09F4DE839011F387E9F410DD61F83A8ECD839652880 |

### 2.4 Wave R verification gate

The Wave R gate is SATISFIED by the owner-reported post-correction run on 2026-11-14 at 13:54: pnpm run test passed 8 files / 83 tests and pnpm run typecheck exited 0. The owner also reports validate_harness = HARNESS_VALID, validate_repository_security = REPOSITORY_SECURITY_VALID for 7,259 files, validate_architecture = ARCHITECTURE_VALID, and git diff --check was silent. The owner emulator re-check of PE1, PE2, and PE2b passed.

The earlier coordinator post-run 1 failure (one uncompiled suite and 11 type errors) and its source corrections remain historical evidence in the R3/R4 reports and RUN_STATE. The successful run above is the corrected Wave R result. Its shared run set is used up and is NOT a Wave L baseline run. Codex did not run any of these commands or emulator reviews.

## 3. Frozen behavior and design constraints

The following items are read-only constraints for every Wave L checkpoint.

| Frozen item | Wave L must preserve |
|---|---|
| D-015 route table | Use only the current authorized routes. Missing routes and fields remain typed, visible unavailable states. No local success, empty result, retry, route, or server field may be inferred. |
| D-016 consent and no-preset | Unknown, pending, or unavailable consent is informational and non-blocking; server-confirmed denial/revocation remains blocking. Consent grant/revoke stays unavailable until a route exists. Rev67's no-preset requirement is NOT AVAILABLE while the backend contract is absent; starting a run still requires the exact lesson ID/version/hash pin. |
| D-017 O1 | Story creation can proceed without a selected main activity. Preserve the state currently shown in Vietnamese as “Hoạt động chính: chưa khả dụng.” Do not add an activity to the story request. The quoted English phrase in the task names the state; it must not be rendered as English UI copy. |
| D-017 O2 | Never infer topic/artwork mismatch from keywords, string matching, color, or a model-confidence threshold. Keep the adult subject-edit and confirmation path. |
| D-017 O3 | Active-run recovery only resumes the run. Cancel, restart, delete, and “new run” actions remain unavailable unless an authorized contract is added later. |
| D-018 / PE1 | JavaScript StatusBar remains dark-content with palette.background on every app step. Do not add a second status-bar/safe-area inset to ScreenFrame. Preserve the current route and loading shell. |
| D-019 / PE2 | Ages 36–120 months remain eligible with both age-band values null and show “Nhóm tuổi chưa khả dụng”; do not invent a band. Ages 121–155 remain read/delete only. A one-field band pair remains unavailable. |
| D-014 child gender | The field remains an empty local draft only. Never save, send, persist, infer, or use it in story/model input. |
| Revision/hash integrity | Preserve profile revision preconditions, exact pinned lesson ID/version/hash, context revision/snapshot hash, story revision/hash, action identity, and reconciliation behavior. Do not hide selectable hash values if they are part of the current adult review. |
| Capture limits and recovery | Preserve the 20 MiB photo cap before compression, the current one-photo-per-run rule, audio duration/size limits, permission-denied alternatives, and no duplicate submission after an ambiguous outcome. |
| Safe errors | Never render raw provider, backend, OAuth, SQL, filesystem, stack, or exception messages. Keep Vietnamese safe recovery text and typed unavailable explanations. |
| Accessibility | Light theme, 6.1-inch portrait review, font scaling, screen-reader labels and state, visible focus, 44 dp minimum controls, 52 dp primary/navigation targets, text contrast at least 4.5:1 and UI contrast at least 3:1. Android review follows WCAG2ICT/platform guidance; this is not a certification claim. |

The current ContextScreen is intentionally reused in two states: its first state creates the run before capture; its later state follows adult subject confirmation and confirms the context snapshot before story generation. Keep those states distinct and preserve their current order. Do not convert the screen into a single unconditional confirmation.

### Owner decisions and resolved concept conflicts

1. SRS authority is resolved for FEAT-081 Wave L by Q1 and D-020: unsigned Rev67 is the canonical working SRS for this plan; Rev60 is historical. FEAT-063 D-203 is being written on the backend line. No SRS file or authority register is edited here.
2. The concept's optional lesson selection does not alter D-016. A run remains unavailable without the exact pinned lesson ID, version, and content hash. Under Rev67, the optional no-preset behavior is an SRS requirement that the current backend does not provide.
3. Activity-before-Story is aligned with Rev67 §5.1 step 9 and FR-P-05: the Parent chooses a main activity before the script and sees it after video. D-017 O1 remains the sole recorded deviation: story generation may proceed without a chosen activity because the activity route is absent. Wave L does not change route or order, and L3 has no ordering gate.
4. D-017 O2 remains binding: do not infer topic/artwork mismatch, warn from a heuristic, or offer a heuristic-triggered retake.
5. D-016 remains binding: consent that is unknown, pending, or unavailable is informational and non-blocking; no grant/revoke success is claimed without a route.
6. D-014 remains binding: child gender is an empty local draft; never persist, send, infer, or use it as story/model input.
7. Rev67 history, sharing, lesson feedback, notifications, quota/purchase, video, cancellation, and completion requirements remain subject to backend availability. Show typed unavailable states where the required route is absent; do not fabricate lists, success, or actions.
8. Decorative guide artwork must not invent lesson instructions or resemble an unavailable AI result. Show only validated pinned lesson steps or the existing unavailable state.
9. Rev67 age-band-version, optional no-preset, and history rules are SRS requirements, but the current backend does not provide the corresponding fields/routes. Preserve D-016 and D-019 behavior: exact-pin no-preset stays unavailable, and no age band or version is invented. History remains typed unavailable where its route is absent.

These owner decisions are incorporated in the pinned plan and recorded in D-020. They are not new checkpoint gates.

## 4. Visual system and copy policy

### 4.1 Code-only visual treatment

- Keep the concept’s existing colors and named tokens as the baseline. Extend only with named spacing, radius, outline, shadow, and illustration tokens where the layout needs them.
- Build cards, uneven crayon edges, underlines, doodles, and decorative illustrations with the existing React Native component layer, react-native-svg, expo-linear-gradient, and @expo/vector-icons already present in the app.
- No new package, font, raster asset, copied web CSS, WebView, or provider-generated media. Any request for one is an owner decision and a separate asset/provenance/visual-approval gate.
- Decorative artwork must not convey an unavailable feature, show a fictional child’s personal data, or replace lesson/provider content. Use tilt only on decorative cards, never on text or controls.
- Preserve semantic labels, focus rings, selected/busy/disabled states, scalable text, minimum touch sizes, keyboard/screen-reader meaning, and error summaries. Do not rely on color or crayon texture alone to communicate state.
- Keep D-018 status-bar behavior and avoid a second top inset.

### 4.2 Explicit visible-copy whitelist

The owner approves exactly the seven visible-string edits below for NFR-13/NFR-21 Vietnamese UX. Every other existing app-visible string must remain byte-identical. No English phrase may be added to the UI; concept captions are design annotations and are never application copy.

| Current string | Proposed Vietnamese string | Reason |
|---|---|---|
| “Tài khoản được tạo trên Firebase Authentication và backend Sketch2Life.” | “Tài khoản dùng để đăng nhập vào Sketch2Life.” | Replace user-facing implementation jargon with a plain Vietnamese explanation; do not change the authentication flow. |
| “Mật khẩu đã được cập nhật trên Firebase Authentication.” | “Mật khẩu đã được cập nhật.” | Keep the confirmed result while removing provider jargon. |
| “Google Sign-In chưa cấu hình. Điền SKETCH2LIFE_GOOGLE_WEB_CLIENT_ID và SKETCH2LIFE_GOOGLE_ANDROID_CLIENT_ID trong .env gốc.” | “Đăng nhập bằng Google hiện chưa khả dụng. Bạn có thể dùng email để tiếp tục.” | The current developer configuration notice is rendered to the user; replace it with a safe Vietnamese alternative. |
| “Chỉ tạo line-sketch khi người lớn bật tùy chọn này trong buổi học.” | “Chỉ tạo gợi ý nét vẽ khi người lớn bật tùy chọn này trong buổi học.” | Translate an English feature phrase while preserving the opt-in constraint. |
| “Bật gợi ý line-sketch trong phiên hiện tại” | “Bật gợi ý nét vẽ trong phiên hiện tại” | Keep the accessible switch label Vietnamese. |
| “Gợi ý line sketch được tạo bởi AI” | “Gợi ý nét vẽ do AI tạo” | Keep the image’s accessible name Vietnamese. |
| “Whisper · tiếng Việt” | “Bản ghi lời nói · tiếng Việt” | Replace the English product-facing heading with a Vietnamese label; transcription behavior is unchanged. |

The mixed technical fallback “Google chưa trả về ID token. Kiểm tra OAuth client và redirect URI.” is currently passed through AuthScreen’s safe Vietnamese onError handler, not rendered as written. Preserve that safe mapping. If a future call site can render the raw fallback, the implementation must route it through a safe Vietnamese message before release; do not expand the whitelist silently.

## 5. Work breakdown and dependencies

| ID | Task | Depends on | Parallel with | Acceptance check | Effort | Risk |
|---|---|---|---|---|---|---|
| L0 | Shared crayon foundations and bottom navigation | Approved Plan Revision 8 and Wave R gate satisfied | None | Apply variant-A shared primitives and bottom bar; preserve tokens, contrast, semantics, 44/52 dp targets, four tab IDs/order, D-018 status bar and inset behavior. | Medium | Shared primitives affect every screen; preserve all behavior assertions while updating only source-shape assertions. |
| L1 | Adult entry, account/settings, home, and profile surfaces | L0 complete and static review clean | None; parentSrsBehavior.test.ts is shared | Restyle auth, account, settings, home, profile list/form/sharing, and Google sign-in; preserve consent, age, gender, deletion, resume, and safe-auth states. Apply only the five L1 copy edits listed in Section 4.2. | Large | Copy and profile-state regressions; concept gender and consent samples conflict with D-014/D-016. |
| L2 | Lesson discovery, topic, guide, capture, transcript, understanding, and context | L1 complete and static review clean | None; shared test file and ParentExpoApp make parallel editing unsafe | Adapt the full gallery to variant-A cards/tokens while preserving its content/states; preserve exact lesson pin, no-preset gate, capture limits/permission alternatives, unavailable transcript/guide, no mismatch inference, and both context states. Add the approved development-only preview harness behind an explicit flag. | Large | Preview is synthetic and must remain unmistakably marked; preserve route and payload behavior. |
| L3 | Activity, story, handoff, history, quota, and notifications | L2 complete and static review clean | None | Preserve D-017 O1/O3, story revision/hash confirmation, unavailable video/lifecycle/history/quota/inbox states, and all recovery boundaries. The Activity-before-Story order is aligned under Rev67; O1 remains the only deviation and is not an L3 gate. | Large | AI-backed screens require the approved synthetic preview; never present preview values as provider output. |

Critical path: L0 → L1 → L2 → L3 in one merged goal. No pause or parallel implementation occurs between checkpoints unless the owner interrupts or a static-review/blocker condition stops the goal. After each checkpoint, append evidence, create the checkpoint snapshot, and continue only if its static review is clean. The roadmap and team sprint allocation remain separate; integration still requires its own approval.

## 6. Checkpoint manifests and baseline pins

Manifest modes: E = editable only in its named checkpoint inside the approved merged goal; N = new path within the owner-authorized conditional scope; R = read-only; H = frozen. All listed values are the current Wave L planning pre-pins, not after-pins. Before each checkpoint, compare them with the latest accepted snapshot/evidence and record any new after-pin. There are no separate checkpoint launches.

The 75 app-file manifest rows were re-hashed with Get-FileHash at Step 0 on 2026-11-14. All 75 matched the current file sizes and SHA-256 values; zero rows differed. The conditional ParentVisualPreviewHarness.tsx N path is absent and its manifest absence pin matches. The tables below carry those current pins.

The three H tests are frozen for every checkpoint:
- parentLearningI2.test.ts — lesson pin, context confirmation, and active-run recovery.
- catalogViewModel.test.ts — profile summary, catalog filtering, sorting, and empty states.
- storyDraft.test.ts — story schema, Vietnamese language, scene count, and timing.

The four R tests below remain unchanged in every checkpoint:
- apiRetryIdentity.test.mjs — retry/action identity and no duplicate request behavior.
- mainFlowSafety.test.mjs — image, narration, upload, and single-flight safety.
- parentApiI2Contract.test.ts — route, payload, revision, action key, and safe error contract.
- parentFlowV1.test.ts — pure flow, age, consent, lesson pin, guide, recovery, and story decision logic. It does not read presentation source text.

### L0 — Shared foundations

| Mode | Path | Bytes / planning pin | Planned use |
|---|---|---|---|
| E | apps/ui-mobile/src/parent/presentation/components/ui.tsx | 22,273 / 51BAE1F8E81B560AFEA5389864FE98FC44CB0104C7492FE4CC7D861663A829E8 | Refine shared card, button, field, notice, choice, section, and frame composition. |
| E | apps/ui-mobile/src/parent/presentation/screens/ParentBottomBar.tsx | 2,770 / 901A7D6FC53C744D2F056B6DFA0057770AD3DA0A03BD0C372FFC1257D334F9B0 | Match variant A’s four-tab bar while retaining current tab IDs, labels, accessibility, and 52 dp targets. |
| E | apps/ui-mobile/tests/parentSrsBehavior.test.ts | 32,816 / 3887402F4FA913BB8BA217A5934078733789ECC922C2095D07841A9FCA2DDEF3 | Update source-shape and visual-token assertions to the approved primitives; preserve every behavior assertion. |
| R | apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx | 17,590 / FCB0B797C424AB6176B59E88034B954ADA01B7B3544ADAAFCC41ECF7227DA8AA | StatusBar shell and route contracts; no edit in L0. |
| R | apps/ui-mobile/tests/apiRetryIdentity.test.mjs | 3,188 / C0DC06450146667AC16C8108960E892F30B4D34AD0A1B0AD3EBB3EC19D5C6054 | Shared read-only regression. |
| R | apps/ui-mobile/tests/mainFlowSafety.test.mjs | 7,985 / 41B82F60E83B17DBB09F7195ACF122E3653046A49822D42D5416E39B53582D74 | Shared read-only regression. |
| R | apps/ui-mobile/tests/parentApiI2Contract.test.ts | 17,370 / C7FC2FB9421AF32553EDABB4F633547C842A825161FA41AB524CA8DCAC541075 | Shared read-only regression. |
| R | apps/ui-mobile/tests/parentFlowV1.test.ts | 24,490 / D64638EADBD7FDEB43B04D56831F9CBF7D8A06B576FB2FE7CC751537371129CF | Shared read-only behavior regression. |
| H | apps/ui-mobile/tests/parentLearningI2.test.ts | 5,841 / E92C927657EE1AF2AD3152DEEE6519AF56B866BDECCDB00E7A7BD5BC03884892 | Frozen. |
| H | apps/ui-mobile/tests/catalogViewModel.test.ts | 3,254 / 8FAA29A92BD4D750C27E2109256611BA3DA8ECFE1BE72044127A81B78699C978 | Frozen. |
| H | apps/ui-mobile/tests/storyDraft.test.ts | 1,770 / 07C8BE23A875F2082CDC2626A23E4462A46CF61525BD487F9053CCD00CBCFC50 | Frozen. |
| N | None | — | No new path in this checkpoint. |

### L1 — Adult entry, account/settings, home, and profile surfaces

| Mode | Path | Bytes / planning pin | Planned use |
|---|---|---|---|
| E | apps/ui-mobile/src/parent/presentation/screens/AuthScreen.tsx | 4,251 / 01D8CB5C220026D14EDCE1FA7C19A63F6E4BE21A674CFA9FADC7EF2F509497AB | Rebuild sign-in, sign-up, reset, and error hierarchy without changing auth callbacks. |
| E | apps/ui-mobile/src/parent/presentation/screens/AccountScreen.tsx | 3,189 / C6E483B2DA1DE0E86640D7F48AF65FC0D52C3374E95450CC8EC00F418459E61F | Restyle account and password recovery sections; apply only listed copy edits. |
| E | apps/ui-mobile/src/parent/presentation/screens/SettingsScreen.tsx | 2,191 / FD1015ACF453F3C303392F4A005F60EDBBD3F791BDF365AD6996F4316C81A185 | Group adult preferences and management actions; the guide switch stays session-only. |
| E | apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx | 5,012 / 05AB783965739E3520B6E30B38EBEF7AC457218DE8BD2032789C8AB8A46D7D46 | Add concept hierarchy and code-only decoration while preserving selected profile and resume-only run behavior. |
| E | apps/ui-mobile/src/parent/presentation/screens/ProfileScreen.tsx | 7,527 / E3CBDD2119DF0D233750155C6A13C599CAA2E4350D4842CB368C931DD16FC917 | Restyle list, consent, age-band, deletion-pending, and selected-profile states. |
| E | apps/ui-mobile/src/parent/presentation/screens/ProfileFormScreen.tsx | 4,422 / EBB01020299AA5B2963B32EB916D8349844FFF753A5F6E5D0A0F34E32830B2E1 | Restyle create/edit forms; gender remains empty local draft. |
| E | apps/ui-mobile/src/parent/presentation/screens/ProfileSharingScreen.tsx | 5,886 / 22E2859094ED8DD1D882F442C3AD4045AC085017DFCBF943936A3A0F129700A0 | Restyle the visible unavailable state; no invitation success. |
| E | apps/ui-mobile/src/parent/presentation/components/GoogleSignInButton.tsx | 2,562 / 26F0BF8BAB3AC1BB47AEC341539ADDCC870AE49D2CE76DD58716053B791EF5C9 | Match the auth card and keep missing configuration safe and Vietnamese. |
| E | apps/ui-mobile/tests/parentSrsBehavior.test.ts | 32,816 / 3887402F4FA913BB8BA217A5934078733789ECC922C2095D07841A9FCA2DDEF3 | Update presentation source assertions for approved layout/copy only. |
| R | apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx | 17,590 / FCB0B797C424AB6176B59E88034B954ADA01B7B3544ADAAFCC41ECF7227DA8AA | Existing routing and app shell. |
| R | apps/ui-mobile/src/parent/presentation/navigation/workflowTypes.ts | 7,811 / D0863F5436E885A022FDF651AE837CB3E7523FAB2F8B0BCBF6B1D640C4D42D9C | Frozen profile, consent, age, and capability decisions. |
| R | apps/ui-mobile/src/parent/presentation/navigation/parentFlowV1.ts | 23,746 / 492E22E55E2FD4B51EAE49947CDA2F57BA8786A86070405A29F3A12D29172143 | Frozen flow decisions and safe copy mapping. |
| R | apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts | 64,014 / BE1DBF7D057A2F775E55137CEA39AA07BE5184E5786B2B9216D50009E76C8B11 | Frozen callbacks, profile state, and action/revision behavior. |
| R | apps/ui-mobile/src/parent/infrastructure/auth/ParentAuth.ts | 10,305 / BBFEEF77C3CABD2632AFE7EE96D6996509C809BB8521FBD80326223961DD6077 | Auth adapter contract; no edit. |
| R | apps/ui-mobile/tests/apiRetryIdentity.test.mjs | 3,188 / C0DC06450146667AC16C8108960E892F30B4D34AD0A1B0AD3EBB3EC19D5C6054 | Shared read-only regression. |
| R | apps/ui-mobile/tests/mainFlowSafety.test.mjs | 7,985 / 41B82F60E83B17DBB09F7195ACF122E3653046A49822D42D5416E39B53582D74 | Shared read-only regression. |
| R | apps/ui-mobile/tests/parentApiI2Contract.test.ts | 17,370 / C7FC2FB9421AF32553EDABB4F633547C842A825161FA41AB524CA8DCAC541075 | Shared read-only regression. |
| R | apps/ui-mobile/tests/parentFlowV1.test.ts | 24,490 / D64638EADBD7FDEB43B04D56831F9CBF7D8A06B576FB2FE7CC751537371129CF | Shared read-only behavior regression. |
| H | apps/ui-mobile/tests/parentLearningI2.test.ts | 5,841 / E92C927657EE1AF2AD3152DEEE6519AF56B866BDECCDB00E7A7BD5BC03884892 | Frozen. |
| H | apps/ui-mobile/tests/catalogViewModel.test.ts | 3,254 / 8FAA29A92BD4D750C27E2109256611BA3DA8ECFE1BE72044127A81B78699C978 | Frozen. |
| H | apps/ui-mobile/tests/storyDraft.test.ts | 1,770 / 07C8BE23A875F2082CDC2626A23E4462A46CF61525BD487F9053CCD00CBCFC50 | Frozen. |
| N | None | — | No new path in this checkpoint. |

### L2 — Lesson discovery and the drawing/context journey

| Mode | Path | Bytes / planning pin | Planned use |
|---|---|---|---|
| E | apps/ui-mobile/src/parent/presentation/screens/LessonGalleryScreen.tsx | 11,467 / D71F0B14A5826701C7447A7677E59829AF2D1AFA628B9B4E10E2ECE1ED3B1847 | Q3 approves adapting the existing gallery layout to variant-A cards and tokens while preserving all content and states. |
| E | apps/ui-mobile/src/parent/presentation/screens/LessonPickerScreen.tsx | 1,579 / ADD6C6606C4FE10AF125D6D3FA90B4152B03C6A5B7A24A809A7D7D48A3B4EF41 | Preserve exact lesson pin and the no-preset unavailable gate. |
| E | apps/ui-mobile/src/parent/presentation/screens/TopicScreen.tsx | 6,918 / 3F33560E469CA5DE34AC36E638A863C26637A27864EF8F9B61582F797364B0FA | Restyle topic/idea/audio/guide cards without implying a missing route is available. |
| E | apps/ui-mobile/src/parent/presentation/screens/DrawingGuideScreen.tsx | 2,150 / C532892764F14E68D9A3E3B4B189BA8048CF9A8A52879F885682D203D745588F | Restyle only validated pinned lesson steps and unavailable states; add no instructional content. |
| E | apps/ui-mobile/src/parent/presentation/screens/CaptureScreen.tsx | 6,045 / 7D67C512C4036CFA0BF29E308376A0D67A3F9452FDFBF17227F8CD1E73DBDAF4 | Restyle image preview and camera/gallery actions; preserve permissions, size cap, and recovery. |
| E | apps/ui-mobile/src/parent/presentation/screens/TranscriptReviewScreen.tsx | 2,360 / 8834A9E90745BEBD3F83483A2A5C0A85F92231D2073A91E92BAFEBFE93944823 | Restyle the existing component only; it is not currently routed in ParentExpoApp. |
| E | apps/ui-mobile/src/parent/presentation/screens/UnderstandingScreen.tsx | 2,371 / 58E758B6E301794CB8A9009AC2B2AB7D8FC620086D0B0CD9A3137ADE4E7CCEB7 | Keep adult subject edit and confirmation; no mismatch heuristic or inferred retake. |
| E | apps/ui-mobile/src/parent/presentation/screens/ContextScreen.tsx | 3,700 / 8A5B1A06D027A68E2F94304A5B6073059723054E712673D9B7934AA3D9FED883 | Preserve pre-capture run-create and post-understanding context-confirmation modes. |
| E | apps/ui-mobile/tests/parentSrsBehavior.test.ts | 32,816 / 3887402F4FA913BB8BA217A5934078733789ECC922C2095D07841A9FCA2DDEF3 | Update source assertions for layout while preserving all R2/R3 safety assertions. |
| E, conditional | apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx | 17,590 / FCB0B797C424AB6176B59E88034B954ADA01B7B3544ADAAFCC41ECF7227DA8AA | Q4 approves only an explicit development-flag preview entry; production route order and D-018 shell remain unchanged. |
| N, conditional | apps/ui-mobile/src/parent/presentation/ParentVisualPreviewHarness.tsx | ABSENT / E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 | Q4 approves a development-only harness rendering real screens from deterministic synthetic props, with no network/backend/provider calls and an unmistakable preview-only marker; an explicit development flag gates access, and normal production flow never renders it. |
| R | apps/ui-mobile/src/parent/presentation/navigation/parentFlowV1.ts | 23,746 / 492E22E55E2FD4B51EAE49947CDA2F57BA8786A86070405A29F3A12D29172143 | Frozen flow, guide parser, capture, and safe recovery contracts. |
| R | apps/ui-mobile/src/parent/presentation/navigation/workflowTypes.ts | 7,811 / D0863F5436E885A022FDF651AE837CB3E7523FAB2F8B0BCBF6B1D640C4D42D9C | Frozen lesson pin and current capability states. |
| R | apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts | 64,014 / BE1DBF7D057A2F775E55137CEA39AA07BE5184E5786B2B9216D50009E76C8B11 | Frozen API actions, revisions, and route state. |
| R | apps/ui-mobile/src/parent/presentation/screens/catalogViewModel.ts | 1,962 / 5BE1210C95C9F1CEBABADEE7DAD2169620B5B438BA85DE24941236DF018630F0 | Read-only topic filtering and sorting behavior. |
| R | apps/ui-mobile/src/parent/application/use-cases/ParentLearningUseCases.ts | 7,831 / 82C3117CE7F5B9A32DFCF51EEEBA879039DB8A8D2F2B0668D90760603B518709 | Frozen story-run and context contracts. |
| R | apps/ui-mobile/tests/apiRetryIdentity.test.mjs | 3,188 / C0DC06450146667AC16C8108960E892F30B4D34AD0A1B0AD3EBB3EC19D5C6054 | Shared read-only regression. |
| R | apps/ui-mobile/tests/mainFlowSafety.test.mjs | 7,985 / 41B82F60E83B17DBB09F7195ACF122E3653046A49822D42D5416E39B53582D74 | Shared read-only regression. |
| R | apps/ui-mobile/tests/parentApiI2Contract.test.ts | 17,370 / C7FC2FB9421AF32553EDABB4F633547C842A825161FA41AB524CA8DCAC541075 | Shared read-only regression. |
| R | apps/ui-mobile/tests/parentFlowV1.test.ts | 24,490 / D64638EADBD7FDEB43B04D56831F9CBF7D8A06B576FB2FE7CC751537371129CF | Shared read-only behavior regression. |
| H | apps/ui-mobile/tests/parentLearningI2.test.ts | 5,841 / E92C927657EE1AF2AD3152DEEE6519AF56B866BDECCDB00E7A7BD5BC03884892 | Frozen. |
| H | apps/ui-mobile/tests/catalogViewModel.test.ts | 3,254 / 8FAA29A92BD4D750C27E2109256611BA3DA8ECFE1BE72044127A81B78699C978 | Frozen. |
| H | apps/ui-mobile/tests/storyDraft.test.ts | 1,770 / 07C8BE23A875F2082CDC2626A23E4462A46CF61525BD487F9053CCD00CBCFC50 | Frozen. |

### L3 — Activity, story, handoff, and unavailable destination screens

| Mode | Path | Bytes / planning pin | Planned use |
|---|---|---|---|
| E | apps/ui-mobile/src/parent/presentation/screens/ActivityScreen.tsx | 3,626 / EAF21898A45ADA590ACD5E8FED5F3C5F7E05E7996C41D59C8ABA2969FC426C9A | Preserve read-only pinned activities or unavailable state; no activity selection. |
| E | apps/ui-mobile/src/parent/presentation/screens/StoryScreen.tsx | 5,818 / B65736A7FB11829E9B935EB697AB424B2B33DC8DEE42CB4A9262B0FD136BB026 | Restyle story and rewrite cards; preserve up to three rewrites and exact revision/hash confirmation. |
| E | apps/ui-mobile/src/parent/presentation/screens/HandoffScreen.tsx | 2,912 / 51F48ED38D68D06231BB3626203CBB149C1540398FF2C3BCCBB2C48CA4F121DE | Keep video unavailable, no player, no completion claim, and resume-only action. |
| E | apps/ui-mobile/src/parent/presentation/screens/StoryHistoryScreen.tsx | 4,279 / F7517C99404F5A3551568D7BB4CBBD4E186BD8C344E359FA71A90BA700569B90 | Restyle typed unavailable state; do not display an empty-success list or lifecycle controls. |
| E | apps/ui-mobile/src/parent/presentation/screens/LessonHistoryScreen.tsx | 3,992 / 15654949EDEA7656691B8EC6C8DBDC75C0957C338BF29C9BA579C5FDA08F6983 | Restyle typed unavailable state; do not imply history retention or feedback works. |
| E | apps/ui-mobile/src/parent/presentation/screens/QuotaScreen.tsx | 2,158 / 0B48EB7BF6970B5192B9249BB4255A2E9F4836BE765249D1EA2B4954BB63E48D | Keep quota unavailable and purchase absent. |
| E | apps/ui-mobile/src/parent/presentation/screens/NotificationsScreen.tsx | 2,368 / BC85C0B49A9C65D96CFF5132BF50585A7392F44BABAA88AA478695D853719C10 | Keep inbox unavailable and read/close actions absent. |
| E | apps/ui-mobile/tests/parentSrsBehavior.test.ts | 32,816 / 3887402F4FA913BB8BA217A5934078733789ECC922C2095D07841A9FCA2DDEF3 | Update source assertions for visual changes; retain no-player, no-empty-success, and no-purchase checks. |
| R | apps/ui-mobile/src/parent/presentation/navigation/useParentPlatformController.ts | 5,985 / B931616B88BA6C30C0F219291DF91B7162B647C1B9855B412AC2E7B2ACD2EB74 | Frozen unavailable job/video/share operations. |
| R | apps/ui-mobile/src/parent/application/ports/ParentCapabilityPorts.ts | 1,810 / 4A09B08EDE15DA22A1A027FA1202826E21C97A0776AA242803A1D52B213F172B | Frozen typed capability states. |
| R | apps/ui-mobile/src/parent/infrastructure/unavailable/ParentUnavailableCapabilityAdapter.ts | 838 / 59334ABC207EB27FCE48CE1FA95FC73A3A6C75005C55ABAF668DC4E6E964BF40 | Frozen unavailable adapter. |
| R | apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts | 22,638 / 43212F92BB83371D2ED0ED6EC65426C81BDEA9B0DD5BD0AA51A8B2E9110EAB02 | Frozen route boundary. |
| R | apps/ui-mobile/src/parent/domain/types.ts | 11,117 / E5FE9502A3FC902F16D41B12477498FF76BACA577CD1B7CE6D1D332846B2477F | Frozen optional API fields and story/run data shapes. |
| R | apps/ui-mobile/tests/apiRetryIdentity.test.mjs | 3,188 / C0DC06450146667AC16C8108960E892F30B4D34AD0A1B0AD3EBB3EC19D5C6054 | Shared read-only regression. |
| R | apps/ui-mobile/tests/mainFlowSafety.test.mjs | 7,985 / 41B82F60E83B17DBB09F7195ACF122E3653046A49822D42D5416E39B53582D74 | Shared read-only regression. |
| R | apps/ui-mobile/tests/parentApiI2Contract.test.ts | 17,370 / C7FC2FB9421AF32553EDABB4F633547C842A825161FA41AB524CA8DCAC541075 | Shared read-only regression. |
| R | apps/ui-mobile/tests/parentFlowV1.test.ts | 24,490 / D64638EADBD7FDEB43B04D56831F9CBF7D8A06B576FB2FE7CC751537371129CF | Shared read-only behavior regression. |
| H | apps/ui-mobile/tests/parentLearningI2.test.ts | 5,841 / E92C927657EE1AF2AD3152DEEE6519AF56B866BDECCDB00E7A7BD5BC03884892 | Frozen. |
| H | apps/ui-mobile/tests/catalogViewModel.test.ts | 3,254 / 8FAA29A92BD4D750C27E2109256611BA3DA8ECFE1BE72044127A81B78699C978 | Frozen. |
| H | apps/ui-mobile/tests/storyDraft.test.ts | 1,770 / 07C8BE23A875F2082CDC2626A23E4462A46CF61525BD487F9053CCD00CBCFC50 | Frozen. |
| N | None | — | No new path unless the owner chooses the conditional L2 preview harness. |

### Tests to update

Exactly one existing test file is planned for editing: apps/ui-mobile/tests/parentSrsBehavior.test.ts. It contains the current accessibility, source-shape, D-018, D-019, route-boundary, privacy, revision, recovery, and unavailable-state assertions. Across L0–L3 update only assertions whose presentation structure or one of the seven approved strings changes. Preserve the behavioral proof of all 153 existing source-text assertions; do not delete or weaken a behavior assertion to make a visual refactor pass. Re-read the full file after every checkpoint and exact-match each changed/added assertion to its final source with rg.

The three H tests remain byte-identical. The four R test files remain byte-identical. The full test suite still runs under the coordinator’s approved checkpoint ceiling.

## 7. Acceptance criteria

- WL-AC01: The approved variant-A paper, ink, accent, crayon-outline, card, and spacing system is applied consistently across all approved screens.
- WL-AC02: Every one of the 22 Parent screens and four shared visual surfaces in PLAN_REVISION_8_SCREEN_MAP.md has an explicit EXACT, ADAPTED, or NO CONCEPT disposition. The full Lesson Gallery keeps the NO CONCEPT coverage classification but follows Q3's approved variant-A card/token adaptation while preserving all content and states.
- WL-AC03: Existing callbacks, route order, screen props, backend payloads, controller/domain contracts, and D-018 shell remain unchanged. The conditional preview entry is dev-flag-only and never part of the normal production flow.
- WL-AC04: D-014 through D-019 behaviors remain intact; unavailable states remain visible and honest; Rev67 requirements unsupported by backend routes/fields are not fabricated.
- WL-AC05: Only the seven copy edits in Section 4.2 are made. Every other existing visible string remains byte-identical; all added/changed display copy is Vietnamese and no English phrase is introduced into the UI.
- WL-AC06: 44 dp minimum controls, 52 dp primary/navigation targets, 4.5:1 text contrast, 3:1 UI contrast, screen-reader semantics, visible focus, font scaling, light theme, and 6.1-inch portrait review are preserved and reviewed within the two-review cap.
- WL-AC07: No new package, font, raster/copied asset, provider call, backend route, external network request, child data, or fake success is introduced.
- WL-AC08: Exact lesson version/hash, capture and subject checks, typed unavailable outcomes, and all revision/action identity fences remain intact.
- WL-AC09: L2's approved preview harness uses deterministic synthetic props, has an unmistakable preview-only marker, makes no network/backend/provider calls, is reached only by an explicit development flag, and never appears in normal production flow. Synthetic content never looks like a real AI result.
- WL-AC10: Each checkpoint appends its required evidence section and snapshot pins; static review is clean before the next checkpoint. Coordinator and owner verification results are recorded within Addendum 18's total ceilings.
- WL-AC11: L0–L3 execute sequentially under one merged goal without a pause between checkpoints. The owner may interrupt with stop-and-save. A checkpoint static-review failure stops progression.
- WL-AC12: Under Rev67 §5.1 step 9 and FR-P-05, Activity-before-Story is aligned. D-017 O1 remains the only recorded deviation because the activity route is absent; no route/order change or L3 ordering gate is introduced.

## 8. Merged-goal command and emulator ceilings

The successful Wave R verification set is complete and used; it is not repeated as a Wave L baseline. Codex runs none of the commands below.

- Coordinator ceiling for the entire merged goal: pnpm run test at most twice total and pnpm run typecheck at most twice total. The first allowed run is after L3; the second is one correction run. No test/typecheck run occurs between L0 and L3.
- Owner ceiling for the entire merged goal: validate_harness, validate_repository_security, validate_architecture, and git diff --check at most twice each. The first allowed set is after L3; the second is one correction set.
- Owner emulator ceiling: at most two reviews total. Each review may cover multiple checkpoint surfaces. The checklists below are coverage items, not per-checkpoint run authorizations.
- Any additional run beyond these ceilings requires a new owner record. If the correction run/review fails, stop and preserve outputs; do not make an unapproved third run.
- Codex runs no test, typecheck, validator, diff-check, install, network, backend, provider, Android, emulator, ADB, Gradle, or Modal command.

### Owner emulator checklist

| Checkpoint | Coverage item |
|---|---|
| L0 | 6.1-inch portrait; paper status bar; no duplicate top inset; 44/52 dp targets; tab labels/order/selection; focus ring; contrast; large font; screen-reader selected/busy/disabled names. |
| L1 | Sign-in/sign-up/reset and safe auth errors; Google-unconfigured fallback; password update copy; session-only Settings switch; profile create/edit; empty gender draft; null age-band text and eligibility; consent informational state; DELETE_PENDING; sharing unavailable. |
| L2 | Home start/resume; catalog empty/loading/error distinction; full gallery adaptation and preserved states; exact lesson pin; no-preset gate; topic/idea/audio alternatives; guide skip/unavailable state; denied camera/gallery permission alternative; 20 MiB boundary; transcript typed-unavailable; subject edit without mismatch heuristic; both ContextScreen states; preview marker and dev-only reachability. |
| L3 | Pinned activity read-only/unavailable; Story without a selected activity; story revision/hash and rewrite limit; no video player or success claim; resume-only; unavailable history/quota/inbox; no cancel/delete/purchase/read action. Review synthetic preview states only when clearly marked. |

## 9. Stop conditions and blocker protocol

Stop the merged goal before or during a checkpoint if its current pin/manifest differs unexpectedly, a required path is outside the Plan Revision 8 E/N rows, any H file would change, a fake success is required, the D-015 route table appears wrong, or a changed source/assertion fails static review. Report exact evidence and a proposed resolution. Do not widen the allowlist, edit owner-local CONTEXT.md or status/STATUS.md, or start the next checkpoint after a blocker.

For a concept element that would require a new package, font, raster asset, copied asset, backend/provider call, or production route, implement the code-only ADAPTED alternative and record the deviation; stop only if no safe in-scope alternative exists. Keep all unavailable states truthful.

After each checkpoint, preserve its changes and create a snapshot before proceeding. Do not revert, delete, clean, stage, commit, or push. The owner may interrupt with a stop-and-save request; then finish only a minimal coherent in-progress file if safe, update WAVEL_RUN_STATE.md, and stop.

## 10. Risks and recorded owner decisions

The owner has resolved the prior authority, Activity ordering, full-gallery direction, preview review, copy, no-preset, and verification-gate questions. Remaining implementation risks are source-text tests coupled to layout, inaccessible AI-backed screens that require a marked synthetic preview, and Rev67 requirements that the current backend cannot fulfill. D-014 through D-019 unavailable/security decisions remain binding. No unresolved owner choice blocks L0–L3 under the recorded scope.

## 11. Approval and merged-goal sequence

This plan's initial status is DRAFT until Addendum 18 is recorded. Addendum 18 records Plan Revision 8 as APPROVED and Wave L as NOT LAUNCHED; it approves one merged L0–L3 goal with the stated ceilings. The owner answer record is D-020.

The merged-goal instruction file is tmp/fe081-waveL/GOAL_L0_L3_INSTRUCTIONS.md. Preparing that file and approving the plan do not start execution. No checkpoint begins until the owner sends the goal text. Once started, the goal runs L0 → L1 → L2 → L3 sequentially without a pause, subject to static review and the blocker/owner-interruption protocol. There are no separate launch instructions for each checkpoint.

No app, test, package, native, context, or status file is edited by this plan/approval preparation task.
