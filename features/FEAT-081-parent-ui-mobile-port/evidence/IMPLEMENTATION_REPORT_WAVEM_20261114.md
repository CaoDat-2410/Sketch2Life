# Wave M implementation report — 2026-11-14

Baseline: `a0b382f8c21de0dc66f23c5aa752a3a67388a093` plus accepted, uncommitted Wave L working state. Branch: `feature/fe-mobile-remediation`. Task SRS: owner-pinned unsigned Rev67; repository-wide Rev60 authority mismatch remains open. `OWNER_MODAL_CALL_APPROVED=NO`.

## M0 — design system, shell, and rendering defects

### Changed files and pins

| File | Before bytes / SHA-256 | After bytes / SHA-256 | Snapshot pin |
|---|---|---|---|
| `apps/ui-mobile/src/parent/presentation/components/ui.tsx` | 23,584 / `D9DDB27DC8647247100A4F60560494226402BB613EC116186A28FB87FE92DA2D` | 23,872 / `2C5637C50D71BE4779E27862C35DF7FF24EF4A71DE4DE9311109BE221D6036C9` | `2C5637C50D71BE4779E27862C35DF7FF24EF4A71DE4DE9311109BE221D6036C9` |
| `apps/ui-mobile/src/parent/presentation/screens/ParentBottomBar.tsx` | 3,135 / `EFEDFF30D482A886747AF483E3F012C1477B483B26D6BC782159A75B4DFFF58C` | 3,204 / `E023F8FE108A8EABDAFACD3993D80CE931D0AC2FAC50B13791452255EBFEA11B` | `E023F8FE108A8EABDAFACD3993D80CE931D0AC2FAC50B13791452255EBFEA11B` |
| `apps/ui-mobile/src/parent/presentation/ParentVisualPreviewHarness.tsx` | 11,033 / `5FE38D9D768715FD8DFC2AEBD53BA65385DCE034075463A36E1FC7D4ACE01DB6` | 20,075 / `0E56EABCC599FEECB498BD9C51737E0BB3ECD417E034863F053FC7605F9B995C` | `0E56EABCC599FEECB498BD9C51737E0BB3ECD417E034863F053FC7605F9B995C` |
| `apps/ui-mobile/src/parent/presentation/screens/ContextScreen.tsx` | 3,915 / `FB6AAED7D6824475C17279F52E2809803E5612C4C5D05763E6F86E2C8FB9191F` | 4,314 / `F8F23D8A6A7BD534CC24AFB963464305EF41AEB406D1F43ACEE694AF9247B9A1` | `F8F23D8A6A7BD534CC24AFB963464305EF41AEB406D1F43ACEE694AF9247B9A1` |
| `apps/ui-mobile/src/parent/presentation/screens/LessonGalleryScreen.tsx` | 11,554 / `2139E4F3940B74630E0420F95D47F67916D48E053CCB829EF93DFD6E07E8363C` | 12,062 / `5503F4855B7AF9FF63AFDFC6D6A3272171830DDD50B7B73C873A3F56517537E5` | `5503F4855B7AF9FF63AFDFC6D6A3272171830DDD50B7B73C873A3F56517537E5` |
| `apps/ui-mobile/tests/parentSrsBehavior.test.ts` | 41,464 / `BB91D5746913B4F84F35C350B3410C02AA71CB92D6AC209352F76CA95E12C3A3` | 44,707 / `450D14E4A7B20AE051B07369E8CF0539FCA09F59840DE33A1CBAE9B51E3A3037` | `450D14E4A7B20AE051B07369E8CF0539FCA09F59840DE33A1CBAE9B51E3A3037` |

Snapshots are copied under `tmp/fe081-waveM/snapshots/M0/` using these repository-relative paths. The six snapshot hashes must equal the after hashes above.

### Acceptance results

| Surface / defect | Static result |
|---|---|
| Shared Card and controls | PASS. Card is a content-sized native `View` border at 1.6 dp with per-corner radii 22/25/19/23. The absolute SVG outline and non-uniform stretch are removed. Card content stays in normal flow. Fields/other controls meet 44 dp; primary controls meet 52 dp. |
| Preview harness frame | PASS. Marker is exactly `BẢN XEM TRƯỚC · DỮ LIỆU MÔ PHỎNG`, one line with font scaling disabled for the compact marker. The horizontal strip is height/max-height 56 dp with `flexGrow: 0` and `flexShrink: 0`; chips are one row with 44 dp minimum height. The test viewport is `flex: 1, minHeight: 0`. Existing `__DEV__` plus exact environment-string gate remains unchanged in the frozen app shell. |
| Context overlap | PASS. The post-card notice is a following normal-flow sibling; snapshot text can shrink/wrap and the card uses a 14 dp gap. The former decorative outline no longer paints over the text. Existing pre/post modes, data, labels, and callbacks remain. |
| Lesson Gallery overlap | PASS. Lesson rows remain children of the catalog card in normal flow; row text has shrink/wrap constraints, rows use the shared content-driven 60 dp minimum, and separators stay inside each invitation/activity row. No absolute layer or negative overlap margin remains. |
| Bottom navigation | PASS. Four destinations and order remain unchanged. The bar is 62 dp, icons 19 dp, labels 9 dp, and each target is at least 52 dp. Four dp vertical padding leaves sufficient interior for the target beneath the top border. |
| Preview coverage and behavior | PASS. The harness exposes 25 Vietnamese-labeled screen/component previews with deterministic `Mô phỏng` data, typed unavailable states, no controller/API/fetch path, and inert async callbacks that never resolve as simulated success. |

### Assertions and copy

- Added native Card outline/radii and no-SVG-outline assertions; reason: prevent the Wave L outline mismatch and enforce the measured concept border.
- Added bottom-bar dimensions, target, padding, and selected-state shape assertions; reason: preserve the measured 62 dp navigation bar while meeting the 52 dp target floor.
- Updated the app-shell preview assertion to bind the existing exact development-only flag and status-bar placement; reason: keep the harness inaccessible in normal app flow.
- Added Context/Gallery normal-flow, card containment, wrapping, and absence-of-absolute-layer assertions; reason: guard the two reported overlap defects.
- Added harness marker, one-line layout, compact strip, viewport flex, synthetic-data, typed-unavailable, async no-fake-success, and current-screen coverage assertions; reason: make the comparison harness robust and keep previews local and deterministic.
- Updated only visual-structure expectations in `parentSrsBehavior.test.ts`; no flow, route, controller, H-file, or behavior assertion was weakened.
- Production visible Vietnamese copy is unchanged in M0. The new preview marker and tab labels exist only in the development-only harness. All harness samples are prefixed or explicitly labeled as simulated data.

### SRS/concept decisions and static review

- M0 introduces no SRS-versus-concept behavior decision. Context confirmation and Gallery selection/invitation actions remain wired exactly as before. D-016 consent behavior remains informational and non-blocking; no consent field, gate, or success state was added. The existing D-017 O1 story-path deviation remains unchanged and is not described as Rev67 conformance.
- Re-read all six changed files completely. Imports/declarations are unique; Card and screen content is content-driven; no absolute positioning, negative overlap margin, stretched outline, or new English UI phrase was found. Text styles wrap/shrink; the preview marker deliberately does not scale to preserve one-line fit. Numeric M0 dimensions match Plan Revision 9 and its concept mapping.
- Exact source strings for the changed structural assertions were checked with `rg`; prohibited overlay/overlap patterns returned no matches in the M0 surfaces.
- Plan Revision 9 R/H re-hash: 20 rows checked, zero mismatches. Unchanged E rows outside M0: 21 unique paths checked, zero mismatches. No new component file was added.

### Open notes for the coordinator

- Emulator/font-scale appearance remains unreviewed because the owner explicitly prohibited Codex emulator commands. Coordinator visual review should use the compact preview harness for all 25 tabs; dynamic long-text cases should be checked there at large font scale.
- The Wave M task pin Rev67 conflicts with the repository-wide Rev60 register. Resolve that governance mismatch after this run; this checkpoint does not edit the authority register.
- `D-017 O1` remains a pre-existing approved deviation from Rev67's activity-selection requirement; M0 preserves it.

### NOT RUN

Tests, typecheck, validators, `git diff --check`, install, network, backend, Android, emulator, and Modal commands. No staging, commit, or push.

## M2 — lesson discovery, capture, transcript, understanding, and context

### Changed files and pins

| File | Before bytes / SHA-256 | After bytes / SHA-256 | Snapshot pin |
|---|---|---|---|
| `apps/ui-mobile/src/parent/presentation/screens/LessonGalleryScreen.tsx` | 12,062 / `5503F4855B7AF9FF63AFDFC6D6A3272171830DDD50B7B73C873A3F56517537E5` | 12,103 / `772F38540DA20CC31FB231F1EC8C4DE1667523505513B8955E30BF8BFCAC1E33` | `772F38540DA20CC31FB231F1EC8C4DE1667523505513B8955E30BF8BFCAC1E33` |
| `apps/ui-mobile/src/parent/presentation/screens/LessonPickerScreen.tsx` | 1,839 / `8799184C230824B3017D54F76884EB0FE9902C85A9CA65A5AEE7B5F6840D9B7B` | 2,385 / `359E351119BA0833ACAAC86C17AB6492E28FDA37E7906B53D69736F568BF1820` | `359E351119BA0833ACAAC86C17AB6492E28FDA37E7906B53D69736F568BF1820` |
| `apps/ui-mobile/src/parent/presentation/screens/TopicScreen.tsx` | 7,384 / `A5980CDDFBA2675D882E03E7849F5A9D46AE7E2A6BE9AF0E8A6F5DCD5D21B5D8` | 10,872 / `CC9899F414497CD34BD209F607AF9EABA740F307078B8A27A92BB04C8F10EC4D` | `CC9899F414497CD34BD209F607AF9EABA740F307078B8A27A92BB04C8F10EC4D` |
| `apps/ui-mobile/src/parent/presentation/screens/DrawingGuideScreen.tsx` | 2,512 / `8B41F49C3D3E04571515939EF87D377B0C20BCA74014835D5CC4F57D58A8D0CD` | 2,655 / `D63EB73C90B6754C9644B20ACFAD06D82E286A41DF70A91B9AF102941FE0D615` | `D63EB73C90B6754C9644B20ACFAD06D82E286A41DF70A91B9AF102941FE0D615` |
| `apps/ui-mobile/src/parent/presentation/screens/CaptureScreen.tsx` | 6,389 / `A451907BDB2D17458D1B0A17EE5A8F375B7627102FCC4591B343FBF5544B2E67` | 7,755 / `D61FBF7F3F24115CEED8F6971A4A58309242C2B38F61B102803EAAF2D7637664` | `D61FBF7F3F24115CEED8F6971A4A58309242C2B38F61B102803EAAF2D7637664` |
| `apps/ui-mobile/src/parent/presentation/screens/TranscriptReviewScreen.tsx` | 2,867 / `54EE458DF46A25282BFC508FA386E728E5D4C4FDDBF7EED309B5A98BDA6FC4E7` | 3,102 / `3E5B46A1F759C8BA2D05851DCCA4A29E96CC4FE57E5B3E09A5861BAB4FB3549E` | `3E5B46A1F759C8BA2D05851DCCA4A29E96CC4FE57E5B3E09A5861BAB4FB3549E` |
| `apps/ui-mobile/src/parent/presentation/screens/UnderstandingScreen.tsx` | 2,908 / `0B33491F936696DF044B1D4A6F452CDF9E690CAD8CA61D24FA0ECC1BD44B1E5C` | 3,357 / `D2065B687FCE9F2878B0FE06EA58D7F64B536011EE0BD50D4EADF60DEA3A09E0` | `D2065B687FCE9F2878B0FE06EA58D7F64B536011EE0BD50D4EADF60DEA3A09E0` |
| `apps/ui-mobile/src/parent/presentation/screens/ContextScreen.tsx` | 4,314 / `F8F23D8A6A7BD534CC24AFB963464305EF41AEB406D1F43ACEE694AF9247B9A1` | 5,487 / `C9301CF190FEBC60C9148BD789F41C5C3EFD37BBA824B10A4D4FDD6BF931C015` | `C9301CF190FEBC60C9148BD789F41C5C3EFD37BBA824B10A4D4FDD6BF931C015` |
| `apps/ui-mobile/tests/parentSrsBehavior.test.ts` | 50,278 / `7CD0BE0D25886776E290C7E67E955759B1A73548D4EABE6CFFE318EC3DAF8115` | 51,352 / `9D3A636D3C237BF1C552FE60C63CA3376499C889B7D6665689BA3B59E063C3DE` | `9D3A636D3C237BF1C552FE60C63CA3376499C889B7D6665689BA3B59E063C3DE` |

The nine checkpoint snapshots are copied under `tmp/fe081-waveM/snapshots/M2/` using repository-relative paths. Each snapshot byte count and hash matches the corresponding after-pin above.

### Acceptance results

| Surface | Static result |
|---|---|
| Lesson gallery | PASS. Topic filters, catalog rows, loading/error/empty states, exact lesson detail/version/hash, objectives, activities, and invitation states/actions remain. The full gallery has no concept screen, so its cards, chips, rows, spacing, and separators use the measured variant-A system while its data-bound copy remains intact. M0's normal-flow row/card containment and wrap constraints remain. |
| Lesson picker | PASS. Concept title, eligibility subtitle, selected/empty card states, and a wrapping list of actual lesson/version rows are present. Selection still calls the original `onSelect(lesson_id)` callback; no clear or no-preset continue control was added. The exact lesson gate remains in the existing flow. |
| Topic and idea | PASS. Topic suggestions and clearing update the existing `onTopic` value; typed idea remains wired to `onIdea`. Audio recording keeps its permission, timer, stop, and fallback states; the transcription capability remains truthfully unavailable. Lesson selection still opens the existing library callback and continuation remains controlled by `canContinue` and the exact pinned lesson. Guide toggle/generation callbacks remain unchanged. |
| Drawing guide | PASS. Only `parseDrawingGuideSteps` output is displayed and its current index remains clamped. Unsupported guide content retains the existing unavailable notice. The “Bỏ qua hướng dẫn” button invokes the existing `onContinue` path to photo selection; no sample steps or new step action were added. |
| Capture | PASS. Camera/gallery handlers, permission/error branches, one-photo locking, pre-compression 20 MiB guard, post-compression size/format checks, and analysis-state gating remain. The empty art uses a code-only SVG with the measured 280:190 viewBox/aspect ratio, uniform `xMidYMid meet`, token colors, and a native outer border. |
| Transcript review | PASS. The screen remains component-only. A missing result stays visibly unavailable and offers the existing continue-without-audio callback. A real transcript remains editable and requires the existing confirmation callback; no generated result or production route was added. |
| Understanding | PASS. Actual candidate/confidence/features remain data-bound and the adult subject remains editable and required before confirmation. The screen explicitly avoids mismatch inference; no retake control or route was added. |
| Context | PASS. Pre-capture and post-understanding modes, existing data, gates, confirmation, retry, continue, and return actions remain. Profile revision, age months, interests, topic/idea, and pinned version render from current props only. No consent field or copy is present. Notice and text siblings remain in normal flow with content-driven cards and wrapping styles. |
| Layout, touch, and tokens | PASS by source review. Cards use the M0 native edge, children have non-negative gaps and remain in normal flow, text rows have `minWidth: 0`/shrink constraints, and no negative overlap margin or content-independent absolute layer was added. Interactive topic chips are at least 44 dp; shared primary/navigation controls retain the 52 dp floor. The only fixed-height image is the existing generated-guide image; the selected-photo image fills its aspect-constrained frame and neither container holds text or controls. |

### Assertions and visible copy

- Updated the picker empty-state assertion to the new `bài học` wording and the Topic pinned-lesson assertion to the exact-pin requirement; reason: verify the concept copy without weakening D-016's required lesson pin.
- Added picker-title, typed-transcription-unavailable, and topic-chip-to-existing-`onTopic` assertions; reason: preserve the new concept labels, truthful capability state, and existing value callback.
- Updated the localized guide-image label assertion and added an absence check for the old `AI` label; reason: keep app-facing copy Vietnamese. The pre-existing check against the “line sketch” wording remains.
- Updated picker, Capture, Transcript, and Understanding layout assertions for the measured palette card, 280:190 capture frame, and content-driven card spacing; reason: replace stale Wave L-era geometry with the M2 concept layout.
- Added Drawing Guide title/skip-callback, Capture required-badge, Understanding confirmation-label, and Context snapshot-interest/no-consent assertions; reason: bind the visible concept composition while explicitly guarding flow and D-016.
- Updated transcript title/content-label/card-spacing assertions; reason: localize the review surface and retain a typed unavailable presentation rather than implying a transcript result.
- These are source assertions only. The flow, controller, route, revision/hash, photo-cap, H-file, and R-file assertions were not weakened. Final-source matches were checked with `rg`; the test suite was not run.

#### Visible-copy changes by screen

| Screen | Changed/added app copy |
|---|---|
| Lesson gallery | In picker mode, `Chọn bài giảng` → `Bài học từ thư viện`; `Chọn và ghim phiên bản bài giảng bạn muốn dùng.` → `Chỉ nội dung công khai hoặc được chia sẻ mới có thể chọn.` Full-gallery copy and data-driven states remain unchanged. |
| Lesson picker | `Thư viện giáo án` → `Bài học từ thư viện`; old pin subtitle → `Chỉ nội dung công khai hoặc được chia sẻ mới có thể chọn.`; empty copy now says `Chưa có bài học phù hợp. Bạn chưa thể tiếp tục nếu chưa ghim một phiên bản bài học.` Added `Chưa ghim bài học` / `Bài học đang được chọn` and `Hãy chọn một phiên bản bài học chính xác để tiếp tục.` |
| Topic and idea | `Chọn chủ đề` → `Chọn gợi ý (tùy chọn)` with an exact-pin subtitle; topic/idea labels and prompts now use `Chủ đề`, `Ý tưởng của gia đình`, `Viết hoặc nói một ý ngắn.`, and `Ý tưởng (tùy chọn)`. Added the concept topic choices and `Bỏ qua chủ đề`, all wired to the existing topic setter. Recording copy now uses `Ghi âm ý tưởng`, `Thử nhập bằng giọng nói`, `Micro chưa được cấp quyền. Bạn vẫn có thể nhập ý tưởng bằng chữ.`, and `Chuyển giọng nói thành chữ hiện chưa khả dụng; bạn vẫn có thể nhập ý tưởng bằng chữ.`; no transcript-success claim is shown. The lesson card uses `Bài học đã ghim` / `Bài học từ thư viện`, an exact-pin notice, and `Mở thư viện`. Guide copy uses `Gợi ý vẽ (tùy chọn)` and the concept skip notice; the generated-image accessibility label says `Gợi ý nét vẽ do trí tuệ nhân tạo tạo`. The existing continue action is labeled `Tiếp tục`. |
| Drawing guide | `Hướng dẫn vẽ từng bước` → `Gợi ý vẽ (tùy chọn)`; subtitle now says the guide may be skipped without affecting photo capture; `Bước tiếp theo` → `Bước tiếp`; `Tiếp tục chọn ảnh` → `Bỏ qua hướng dẫn`. The unavailable notice is unchanged. |
| Capture | Title/subtitle now use `Chụp hoặc chọn tranh` and `Ảnh tranh giấy là bắt buộc.`; camera/gallery permission errors are localized to `Máy ảnh chưa được cấp quyền...` and `Thư viện ảnh chưa được cấp quyền...`; the required badge is `BẮT BUỘC`; placeholder is `Ảnh tranh giấy sẽ hiện ở đây`; the notice/CTA now say `Chỉ tiếp tục sau khi chọn một ảnh tranh hợp lệ. Buổi học chưa được mở trước khi có ảnh.` and `Tiếp tục sau khi chọn ảnh`. Existing lock, size, format, and safe error states remain. |
| Transcript review | `Nghe và sửa ý tưởng` → `Rà soát bản chép lời`; subtitle becomes `Sửa lại trước khi xác nhận.`; transcript field/button copy is localized to `Nội dung nhận dạng`, `Chỉnh sửa ý tưởng`, and `Xác nhận bản chép lời đã sửa`. Empty/busy states say no result is available or that the user may continue with typed idea/art; `Tiếp tục bằng ý tưởng đã nhập` invokes the existing callback. |
| Understanding | `AI nhìn thấy gì?` → `Xác nhận chủ thể`; subtitle uses `Người lớn kiểm tra trước khi tiếp tục.`; `Chủ thể dự đoán` → `Ứng viên chủ thể`; the field is `Chủ thể người lớn xác nhận`; empty features say `Chưa có đặc điểm được cung cấp.`; notices clarify adult confirmation and no automatic topic/image match; the existing confirmation action is `Xác nhận chủ thể này`. |
| Context | `Kiểm tra ngữ cảnh` → `Rà soát thông tin buổi`; subtitle is `Chỉ xem dữ liệu cần cho buổi học này.`; the card is `Hồ sơ và bản nội dung`, with data-backed `Bản hồ sơ`, `Tuổi trong buổi học`, `Sở thích được phép dùng`, `Chủ đề`, `Ý tưởng của gia đình`, and `Bài học đã ghim` rows. Empty copy says `Thông tin buổi học sẽ xuất hiện sau khi tạo buổi.` The redundant success notice for a pinned lesson was removed because its actual version is now shown in the card. No consent wording was added. |

### SRS/concept decisions and static review

- The concept's claim that both topic and lesson can be skipped and its “continue with no selection” copy were excluded. Topic remains optional; exact lesson pin remains required by D-016. The new topic chips only set the existing topic field. `Bỏ qua hướng dẫn` invokes the pre-existing continue-to-photo action, and “Mở thư viện” invokes the existing lesson-library callback.
- Full Lesson Gallery has no concept screen; it retains all existing catalog content/states/actions and uses the concept tokens/components. Transcript review remains outside the production route and typed-unavailable where no result exists. Drawing steps remain server/lesson-derived only. Understanding adds no mismatch heuristic or retake action. Context adds no consent field, gate, or payload value.
- Re-read all nine touched files completely. Imports/declarations are unique; the added React Native `View` import is present; palette references map to existing tokens; no type/domain/controller/navigation changes or new package/assets were made. Numeric style values use the measured token geometry/project touch floors; the capture SVG uses the measured 280:190 canvas and only concept palette colors. No fixed text/control parent, absolute overlay, stretched SVG, negative overlap margin, or sibling overlap remains by source review. Text children wrap/shrink; large-font device appearance remains for coordinator review.
- Changed and added M2 assertion strings were checked against the final source with `rg`. Plan Revision 9 R/H re-hash: 20 rows checked, zero mismatches. Unchanged E rows outside M2 remain at their M0/M1 or launch pins; no other checkpoint source was modified in M2.
- Flow, selected IDs, version/hash binding, lesson-pin gate, validated guide parser, one-photo rule, safe unavailable states, context fields, and current callbacks remain unchanged. D-016, D-017 O2, D-018, D-019, and D-014 behavior is preserved.

### Open notes for the coordinator

- Emulator and large-font review remain unperformed by Codex per the owner's command restriction. Use preview tabs for Lesson Gallery, Lesson Picker, Topic, Drawing Guide, Capture (empty/photo/permission states), Transcript (typed unavailable and real-result component state), Understanding, and both Context modes; check long Vietnamese strings and the capture art at the narrowest supported width.
- The generated guide image retains its existing 240 dp image-only display box with `resizeMode="contain"`; it is not a text/control container. The SVG capture art is new code-only decoration, not a user drawing or sample child data.
- The task's Rev67 pin vs. repository-wide Rev60 register and the pre-existing D-017 O1 activity-selection deviation remain open for coordinator/governance review; M2 did not change either.

### NOT RUN

Tests, typecheck, validators, `git diff --check`, install, network, backend, Android, emulator, and Modal commands. No staging, commit, or push.

## M1 — authentication, account, home, and profiles

### Changed files and pins

| File | Before bytes / SHA-256 | After bytes / SHA-256 | Snapshot pin |
|---|---|---|---|
| `apps/ui-mobile/src/parent/presentation/screens/AuthScreen.tsx` | 4,900 / `D9E6834072DB2D64372D797DCB52E37E7CD430034ECCE98C687090267B791072` | 7,078 / `74D11A625AEAC49AB7A634438FC67A6A3E562EC3752EF1DED883AD318B9DDABE` | `74D11A625AEAC49AB7A634438FC67A6A3E562EC3752EF1DED883AD318B9DDABE` |
| `apps/ui-mobile/src/parent/presentation/screens/AccountScreen.tsx` | 4,241 / `C1D337642D5E09852E3D16CE97DCD0B268DDD6ACBF5EC76AF2A1BE29264BD68D` | 5,144 / `02705D01F1ED3C6FB64193868EBE39E17F061E71ED704369A3C9AF0ACBE952DF` | `02705D01F1ED3C6FB64193868EBE39E17F061E71ED704369A3C9AF0ACBE952DF` |
| `apps/ui-mobile/src/parent/presentation/screens/SettingsScreen.tsx` | 3,022 / `3BBBCE6A66D495BDAAA405BE194CCA602BED105DB571CB3B5C7687C0FFA4B870` | 3,342 / `7FC242B3CCD27FAA46663E9BD19BD7192C4D041195A9A4B0BBA4D76910BBE6BE` | `7FC242B3CCD27FAA46663E9BD19BD7192C4D041195A9A4B0BBA4D76910BBE6BE` |
| `apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx` | 5,520 / `3E286A143BBA5E0F9A98CB2B41B7E6CE3CD8CD502F06C3158C99BF10F1BB9C9E` | 6,960 / `58D88EB3B4E4A8A9AD55296036A080C01950D315F1F7202DB406DAD1B7B84E9A` | `58D88EB3B4E4A8A9AD55296036A080C01950D315F1F7202DB406DAD1B7B84E9A` |
| `apps/ui-mobile/src/parent/presentation/screens/ProfileScreen.tsx` | 7,979 / `2E8445B95E862CEEB4F168497BEFF5E2A4C91D1737208F296A6E3E72FCC7BBB7` | 8,070 / `50507C3E8F7D56B48DD6D73544B835C32C15666A758F890C73C4B9D957448554` | `50507C3E8F7D56B48DD6D73544B835C32C15666A758F890C73C4B9D957448554` |
| `apps/ui-mobile/src/parent/presentation/screens/ProfileFormScreen.tsx` | 4,767 / `6D290382A6946AAAF77D024558F74AB5350D4AA2F0475EE08693F770F709E65D` | 6,679 / `BCACBD95202DDB39F93B6230B1F1A5B35C6CEE21756F66CE23FA5A576AA37A16` | `BCACBD95202DDB39F93B6230B1F1A5B35C6CEE21756F66CE23FA5A576AA37A16` |
| `apps/ui-mobile/src/parent/presentation/screens/ProfileSharingScreen.tsx` | 6,134 / `5DE1B63CB13FA10B53CF7B2AF5EEF8E69DB8D8E38258ED71484DD458CDA3E19E` | 6,219 / `AE1CAE845858E8D87B69DA3D19B3BB02F1CDF349AD3290D5D1E0E714CA089BDD` | `AE1CAE845858E8D87B69DA3D19B3BB02F1CDF349AD3290D5D1E0E714CA089BDD` |
| `apps/ui-mobile/src/parent/presentation/components/GoogleSignInButton.tsx` | 2,693 / `9E7901A7C80D246B9363CCE16C64974C30A7C298A165385C049B817777D3ADF9` | 4,247 / `AB536CEEF1A859042109D5BBA6D55167BD95D224F0FD782546C8D6AA22BE5B7A` | `AB536CEEF1A859042109D5BBA6D55167BD95D224F0FD782546C8D6AA22BE5B7A` |
| `apps/ui-mobile/tests/parentSrsBehavior.test.ts` | 44,707 / `450D14E4A7B20AE051B07369E8CF0539FCA09F59840DE33A1CBAE9B51E3A3037` | 50,278 / `7CD0BE0D25886776E290C7E67E955759B1A73548D4EABE6CFFE318EC3DAF8115` | `7CD0BE0D25886776E290C7E67E955759B1A73548D4EABE6CFFE318EC3DAF8115` |

All nine checkpoint snapshots are under `tmp/fe081-waveM/snapshots/M1/`, preserve repository-relative paths, and match the source after-pins above.

### Acceptance results

| Surface | Static result |
|---|---|
| Auth sign-in, sign-up, and recovery | PASS. Sign-in/sign-up share the same email/password form and invoke the existing respective handlers. Recovery remains local to the existing auth step, calls the existing `onReset`, returns to sign-in locally, and uses a neutral acknowledgment. The concept intro/form/notice hierarchy is in normal flow; Google remains an outlined secondary control inside the form card. |
| Account and Settings | PASS. Identity, password, sign-out, locale, session-only guide toggle, and existing destinations use the concept card/field/row hierarchy. Password-change success is shown only after the existing handler resolves; reset feedback stays neutral. No account verification badge is inferred. |
| Home | PASS. Variant-A intro card, title/badge row, exact `280 × 120` illustration geometry, selected-profile card, and separate lesson row render in concept order. The drawing scales uniformly by matching the SVG viewBox and container aspect ratio. Existing destination callbacks remain available below. An active run still exposes only the existing resume action; otherwise the existing start action runs. |
| Profile list | PASS. The one-profile-per-run notice precedes the list card. Actual profile values, selection, age eligibility, pending deletion, consent status, and resume/create/edit/delete conditions remain data-bound and unchanged. Consent status stays informational and non-blocking. |
| Profile form | PASS. Create begins with blank name, age, interests, and gender; edit initializes only actual saved name/age/interests. The age guard/error and create/update handlers remain. Gender choices are a 2-column wrapping local draft, empty on entry, with a visible D-014 notice; the mutation mapper still excludes gender. Form fields share one card; the draft notice and save/back controls follow as normal-flow siblings. |
| Profile sharing | PASS. The typed unavailable branch shows `Chỉ mời giáo viên được nêu tên.` and the truthful unavailable notice with no invite controls. No sample grant, 90-day claim, or false success was added. Existing controls remain conditional on the current capability state. |
| Google sign-in | PASS. Existing OAuth request and ID-token callback remain. The button is a 52 dp outlined secondary action. Provider diagnostics are rendered as generic Vietnamese safe messages, not raw English descriptions. |
| Layout and touch targets | PASS by source review. M1 content containers are height-driven; no negative overlap margin or content-independent absolute layer was added. Text in rows/cards can shrink and wrap. Shared fields/text controls meet 44 dp; primary, navigation, and lesson row targets meet 52 dp. The Home SVG uses matching 280:120 geometry. |

### Assertions and visible copy

- Updated/added `parentSrsBehavior.test.ts` source assertions for Auth role/header, intro/form/recovery cards, neutral recovery, same existing handlers, and no added route; reason: bind the default in-component flow and concept composition.
- Added/updated Account and Settings copy/composition assertions; reason: keep sign-out/reset safety copy, account hierarchy, and the session-only guide setting visible.
- Added Google unavailable/secondary-size and generic-error assertions, including absence of `response.params.error_description`; reason: preserve the provider callback while preventing raw English provider diagnostics from reaching the app.
- Added Home illustration viewBox/aspect-ratio, gallery-row accessibility/callback, and active-run resume assertions; reason: guard concept geometry and the D-017 O3 resume-only behavior.
- Added Profile notice-before-list ordering and existing age/eligibility/consent condition assertions; reason: preserve the concept order without changing gates.
- Added Profile Form blank-create values, blank local gender, `ageMonths.trim().length > 0` warning guard, one-card gender grid/badge, and no sample placeholder assertions; reason: enforce D-014/D-019 and prevent sample values from entering production UI.
- Kept sharing-unavailable/no-90-day assertions; updated the former gender policy-note expectation to the D-014 local-draft notice. This strengthens the concept/SRS boundary and does not weaken a flow assertion.
- Visible copy now follows the concept for Auth (`Chào mừng trở lại`, `Dành cho người lớn cùng đồng hành với trẻ.`, `PHỤ HUYNH`, `Sketch2Life · Phụ huynh`, `Một bức vẽ, một hành trình khám phá.`, `Đăng nhập để tiếp tục với hồ sơ gia đình.`, `Tạo tài khoản phụ huynh`, `Quên mật khẩu?`, `Khôi phục tài khoản`, `Đăng nhập bằng tài khoản phụ huynh đã xác thực.`, recovery title/instructions/fields/actions and neutral acknowledgment). Sign-up uses truthful Vietnamese title/helper copy for the same form.
- Account uses `Cài đặt và tài khoản`, `Quản lý đăng nhập phụ huynh.`, `TÀI KHOẢN`, `TÀI KHOẢN ĐANG ĐĂNG NHẬP`, `Bảo mật tài khoản`, the concept password labels/placeholders, `Đổi mật khẩu`, neutral reset feedback, and the session-ending notice. The existing password-update success remains conditional on handler success.
- Settings shares the concept title/subtitle and retains Vietnamese language, session-only guide, and management labels. Home uses `Cùng con bắt đầu một hành trình khám phá.`, `Bắt đầu cùng con`, `BUỔI MỚI`/the truthful active-run badge, the concept static-illustration notice, `Bắt đầu buổi vẽ`/the existing resume label, `Hồ sơ đang chọn`, `Quản lý hồ sơ`, and `Khám phá bài giảng`.
- Profile copy includes `Hồ sơ của bé`, `Chọn một hồ sơ cho buổi học.`, and `Mỗi buổi học chỉ gắn với một hồ sơ trẻ.`; profile values and status/error copy remain actual state-bound Vietnamese. Form copy uses the concept title/subtitle, `HỒ SƠ`, name/age/gender/interests labels, `Nhập tên hiển thị`, `Hãy nhập tuổi được hệ thống hỗ trợ.`, `Không muốn chia sẻ`, the local-draft notice, `Lưu hồ sơ`, and `Quay lại danh sách`. Sharing uses `Chia sẻ hồ sơ` and `Chỉ mời giáo viên được nêu tên.`. The Google control and safe errors use Vietnamese copy.

### SRS/concept decisions and static review

- Applied instruction §5: recovery is rendered within the existing Auth step; signup switches the same form; all three auth actions retain their existing handlers. No route, step, controller, or navigation logic changed.
- The concept's verified-email badge is omitted because `ParentUser` has no verified-state field; its example email/badge is sample data. The app does not infer verification.
- D-014 keeps gender empty and local; it is excluded from submitted profile input. D-019 age eligibility and supported-age errors remain. D-016 consent remains non-blocking; the concept wording is not used to add a gate. D-015 sharing remains typed unavailable where the capability is unavailable, without 90-day sample grants. D-017 O3 keeps the active-run action resume-only; D-017 O1 remains a pre-existing Rev67 deviation, unchanged.
- The exact concept Home drawing paths were copied into code SVG with a matching 280:120 viewBox/container ratio and a native outer border. No new asset or package was added.
- Re-read all nine touched source/test files completely. Imports/declarations are unique; no unused imports were found by source review. M1 assertions were matched to final source with `rg`. No raw provider error text, sample profile values, 90-day sharing claim, negative overlap margin, fixed text/control container height, or independent absolute drawing layer remains in the M1 surfaces. All M1 static copy is Vietnamese, apart from the concept/provider/brand terms `SVG`, `Google`, and `Sketch2Life`.
- Plan Revision 9 H/R re-hash: 20 files checked, zero mismatches. E rows outside M1: 18 files checked, zero mismatches (13 untouched M2/M3 baseline paths, two Context/Gallery paths at their M0 after-pins, and three retained M0 shared-source paths). No new component (`N`) was added.

### Open notes for the coordinator

- Emulator and large-font visual appearance remain unreviewed. Use the preview harness for Auth sign-in/sign-up/recovery, Account, Settings, Home, Profile list/create/edit, and Sharing; M1 source review cannot establish final device geometry.
- The task's owner-pinned Rev67 still conflicts with the repository-wide Rev60 authority register; resolve this governance mismatch after the run. D-017 O1 remains the pre-existing deviation already called out in M0.
- The signed-in identity has no verified flag in the current type, so the sample `ĐÃ XÁC THỰC` badge remains intentionally absent.

### NOT RUN

Tests, typecheck, validators, `git diff --check`, install, network, backend, Android, emulator, and Modal commands. No staging, commit, or push.


## M3 — activity, story, handoff, and secondary surfaces (STOPPED at preview-state coverage)

### Changed files and pins

| File | Before bytes / SHA-256 | After bytes / SHA-256 | Snapshot SHA-256 |
|---|---|---|---|
| apps/ui-mobile/src/parent/presentation/screens/ActivityScreen.tsx | 4,027 / 9283E204D75AF6EBF1857AA4C472046CA4A4B2AB6826CCE39BAC6391EB0C4C47 | 4,825 / 15E8EE976D72D16C33B419C6536C8EFC9525EA3940E39407D80FBB84C7A0EA33 | 15E8EE976D72D16C33B419C6536C8EFC9525EA3940E39407D80FBB84C7A0EA33 |
| apps/ui-mobile/src/parent/presentation/screens/StoryScreen.tsx | 6,333 / A783E7338B83075176DCFED602FCBEC518D3CA3F31CE670CAAAB0A8340E30AD4 | 7,417 / 6EF4C70D357D205D5B877C75133DE7A6DEBA7EEB23A5F5072ACC7C3968CB9554 | 6EF4C70D357D205D5B877C75133DE7A6DEBA7EEB23A5F5072ACC7C3968CB9554 |
| apps/ui-mobile/src/parent/presentation/screens/HandoffScreen.tsx | 3,216 / 8455BAD30CEB20C258F6BAF63C91387CC43D4CBDDDCAD6F5D3FB8065F19D16FA | 4,574 / D186E279D14F42C532965D67BAC993EE77573B1DC2C8C76BB1E6138571A359D6 | D186E279D14F42C532965D67BAC993EE77573B1DC2C8C76BB1E6138571A359D6 |
| apps/ui-mobile/src/parent/presentation/screens/StoryHistoryScreen.tsx | 4,451 / 90CC02912242B62FA5C22AE10C5E8FE42B901FE8A4DCE7D6AA957D987A97F2A2 | 4,759 / 0DB9969F5577B4B5E203B5032ABD200EC6DF6EE13023508D3BD3AE6345FE8386 | 0DB9969F5577B4B5E203B5032ABD200EC6DF6EE13023508D3BD3AE6345FE8386 |
| apps/ui-mobile/src/parent/presentation/screens/LessonHistoryScreen.tsx | 4,174 / 054C8516DF750B1678B2302655FBEEFCFC774FA7A2AC949DC3BC41AE4A113701 | 4,453 / 6DD62C98C003C292A5BE62720441A66DE92B155BD8B0A757CEA9A9748D2A6C35 | 6DD62C98C003C292A5BE62720441A66DE92B155BD8B0A757CEA9A9748D2A6C35 |
| apps/ui-mobile/src/parent/presentation/screens/QuotaScreen.tsx | 2,334 / 5CE622EC73E56BF967BD82BB776EFCC910A7160B1028C0338866D95DD7D39F53 | 2,737 / 0E35C3955C66A69C4F05F4B2198A94C34BC2B4F298B104D17C701712E410B199 | 0E35C3955C66A69C4F05F4B2198A94C34BC2B4F298B104D17C701712E410B199 |
| apps/ui-mobile/src/parent/presentation/screens/NotificationsScreen.tsx | 2,656 / B28593CE90E9FD8363CFF5C821D68CE59588A63B995F5F4C692DEBFB459916AD | 3,085 / F0A6FF0803461E19F8D8ECCF817CD68D29E02A2B608FC7593724E67C72383D85 | F0A6FF0803461E19F8D8ECCF817CD68D29E02A2B608FC7593724E67C72383D85 |
| apps/ui-mobile/tests/parentSrsBehavior.test.ts | 51,352 / 9D3A636D3C237BF1C552FE60C63CA3376499C889B7D6665689BA3B59E063C3DE | 52,820 / 535556608CA77EA278015FEDDF50C57B57A5F1C2E37BAFF578CC9AC167A0C174 | 535556608CA77EA278015FEDDF50C57B57A5F1C2E37BAFF578CC9AC167A0C174 |

All eight changed files were copied under tmp/fe081-waveM/snapshots/M3/ with repository-relative paths. Each snapshot byte count and hash matches the source after-pin above.

### Acceptance results

| Surface | Static result |
|---|---|
| Activity | PASS for the source change. The concept heading and wrapping cards are present. Pinned lesson activity remains read-only, the unavailable notice remains, and the only continuation calls the existing onSkip callback. Unknown activity kinds use a Vietnamese fallback. No activity selection or new handler was introduced. |
| Story | PASS for the source change. Generation, retry of the same request, rewrite, and exact current revision/hash confirmation keep their existing callbacks and gates. The three-rewrite limit remains; sample placeholder text is removed and language codes map to Vietnamese labels. |
| Handoff | PASS for the source change. There is no player, duration, percentage, estimated wait, queue position, or completion action. Stage names map to Vietnamese with a safe unknown fallback. The only continuation remains onResumeActiveRun. |
| Story history | PASS for the source change. The typed unavailable branch still precedes any available-state controls. Data-backed cancel/delete conditions and callbacks are unchanged; unknown run states no longer leak raw enum text. |
| Lesson history | PASS for the source change. Typed unavailable, loading, error, empty, delivery, feedback, and pagination branches remain. Existing data-bound feedback controls and callbacks are unchanged. |
| Quota | PASS for the source change. Unavailable and unconfigured states remain explicit. Values are rendered only from the server-backed quota prop; there is no purchase or price action. |
| Notifications | PASS for the source change. The typed unavailable branch remains. Only supplied inbox records render, and mark-read remains attached to unread records and the existing callback. No sample inbox row was added. |
| Preview harness | SCREEN COVERAGE PASS: the existing development-only harness has 25 Vietnamese-labeled tabs, including all seven M3 surfaces, and the deterministic sample data is marked as simulated. STATE COVERAGE BLOCKER: Capture is represented only by photo=null with onPhoto wired to ignoreAction. There is no selectable permission-denied or selected-photo preview state. The M3 acceptance requires important state coverage including capture permission/photo. Updating ParentVisualPreviewHarness.tsx is outside the M3 E rows. Per instruction section 8(a), M3 stops here. |

### Assertions and visible copy

- Replaced the prior Activity card-spacing assertion with checks for the concept heading, the existing skip callback, a Vietnamese unknown-kind fallback, and normal-flow wrapping card styles. Reason: protect the read-only D-017 O1 behavior and the new composition.
- Replaced Story assertions for the old top-border card and divider with checks for the concept title, localized language label, no sample placeholder, the three-rewrite limit, and measured normal-flow card/divider geometry. Reason: protect revision-bound confirmation while guarding the new copy and layout.
- Updated Handoff structural assertions for the wrapping event row; added checks for the concept heading, Vietnamese stage mapping, the concept notice excluding guessed progress, and absence of durationMs rendering. Reason: keep stage state understandable without exposing raw timing or adding a player.
- Updated Story History, Lesson History, Quota, and Notifications assertions from old top-border styling to the native Card composition; added title/copy and unknown-state fallback checks. Reason: bind the concept hierarchy while preserving typed capability boundaries and data-backed controls. The existing R3/R4 flow and unavailable-state assertions remain intact.
- Activity: “Hoạt động trong bài học” becomes “Gợi ý hoạt động”; unknown activity kinds render “Chưa xác định loại hoạt động”. Existing unavailable, pinned-source, and continue copy is retained.
- Story: “Câu chuyện từ bức vẽ” becomes “Rà soát kịch bản”; the subtitle becomes “Xác nhận đúng bản đang hiển thị.” The generation action now says “Tạo kịch bản bằng trí tuệ nhân tạo”. The draft language label is localized; “SHA-256” is labeled “Mã SHA-256”; scene headings use “Cảnh”. The rewrite field uses “Gợi ý viết lại · tối đa 3 lần”, placeholder “Nhập gợi ý viết lại”, and the concept action “Gửi gợi ý viết lại · tối đa 3 lần”. The revision notice and confirmation action now say “Mọi thay đổi tạo bản nội dung mới; xác nhận cũ không được dùng lại.” and “Xác nhận bản nội dung đang xem”. No example story or hash was added.
- Handoff: title/subtitle become “Trạng thái buổi học” and “Hiển thị giai đoạn được xác nhận.” “Kết quả các yêu cầu” becomes “Các giai đoạn đã xác nhận”; event names/statuses are mapped to Vietnamese and elapsed-time text is removed. Added “Không hiển thị phần trăm, thời gian dự kiến hoặc vị trí hàng đợi.” The existing unavailable notice, no-video text, and resume action remain.
- Story History: title becomes “Lịch sử buổi học”; available-state subtitle becomes “Các buổi của hồ sơ đang chọn.” Unknown run states render “Trạng thái chưa xác định”. Existing visible “worker lifecycle” and “backend” terminology was localized to “tiến trình xử lý vòng đời” and “máy chủ”.
- Lesson History: title becomes “Bài học đã xem”; available-state subtitle becomes “Lịch sử trong 30 ngày từ lần mở đầu.”
- Quota: subtitle becomes “Tóm tắt từ dữ liệu máy chủ.” The summary uses “Tóm tắt lượt dùng”, “CHƯA CẤU HÌNH”, “Chưa có số liệu để hiển thị”, and “Số dư và kỳ sử dụng phải đến từ máy chủ.” Existing server values and update action remain.
- Notifications: subtitle becomes “Thông tin dành riêng cho tài khoản phụ huynh.” The section label is “HỘP THƯ”, the existing read action becomes “Đánh dấu đã đọc”, and the privacy notice is shown only when actual items exist.

### SRS/concept decisions and static review

- D-017 O1 continues to win over the concept’s required activity-selection step: Activity stays read-only/unavailable and continues through its existing story callback. This remains a pre-existing Rev67 deviation, not SRS conformance. No mismatch inference or activity-selection action was added.
- Story continues to bind confirmation to the currently displayed revision ID/hash and the existing adult confirmation gate. The three-rewrite limit remains. The concept’s video/player/lifecycle success states are not implemented because their routes are unavailable.
- Handoff hides timing details and keeps the resume-only action required by D-017 O3. Known event stage keys are translated; unknown keys use a fixed Vietnamese label.
- Story History, Lesson History, Quota, and Notifications preserve their existing unavailable branches and conditional controls. Concept sample rows, prices, purchases, messages, and success claims remain excluded.
- All seven presentation files and the changed assertion file were re-read completely. Imports are unique; no new unused import was found by source review. All changed assertion phrases were matched against the final source text with read-only search. Text content uses wrapping/shrink constraints; cards stay in normal flow; no absolute outline layer, negative overlap margin, or fixed text/control height was introduced. Card outlines come from the shared native Card border. Changed spacing, type, chip, and divider values use the concept measurements/token scale.
- R/H re-hash: 20 rows checked against Plan Revision 9, zero mismatches. Earlier E rows outside M3: 19 unique paths checked against their latest M0–M2 snapshots, zero mismatches. No M3 harness edit or new component was made.

### Open notes for the coordinator

- M3 source changes are saved and snapshotted, but M3 is not complete because the approved M3 manifest does not permit the harness change required by acceptance 3. Resolve the scope by authorizing a Plan Revision 9 manifest amendment or by formally accepting the current one-state-per-screen coverage. If expanded, add deterministic selectable capture permission/photo states without invoking a controller, API, or network, then re-review and complete M3.
- Emulator appearance and large-font behavior remain unreviewed because the owner prohibited Codex emulator commands. The 25-tab harness can be used for screen review; the missing Capture state selector is recorded above.
- The task-pinned Rev67 still conflicts with the repository-wide Rev60 authority register. Coordinator resolution remains open. D-017 O1 remains the pre-existing approved deviation.

### NOT RUN

Tests, typecheck, validators, git diff --check, install, network, backend, Android, emulator, and Modal commands. No staging, commit, or push.

## Bounded post-run remediation (2026-11-14)

Status: STATIC REVIEW COMPLETE; READY FOR COORDINATOR POST-RUN. This section records the owner-authorized remediation after the supplied post-run logs. The initial test and typecheck results are not rerun results and do not establish that the corrected source passes either command.

### Incoming post-run findings

- The coordinator-supplied `pnpm run test` log reports 89/91 passing and two failed assertions in `apps/ui-mobile/tests/parentSrsBehavior.test.ts`. Vitest stopped before `node scripts/validate-ui-copy.mjs` ran.
- The coordinator-supplied `pnpm run typecheck` log reports three errors: missing `palette.line` in `components/ui.tsx` and `HomeScreen.tsx`, and a redundant unavailable-state comparison in `ProfileSharingScreen.tsx`.
- Both supplied commands count as consumed runs under Addendum 20. No counter was reset. Codex performed no test, typecheck, or validator run.

### Remediation files and pins

| File | Before bytes / SHA-256 | After bytes / SHA-256 | Snapshot SHA-256 |
|---|---|---|---|
| `apps/ui-mobile/src/parent/presentation/components/ui.tsx` | 23,872 / `2C5637C50D71BE4779E27862C35DF7FF24EF4A71DE4DE9311109BE221D6036C9` | 23,875 / `0BB724D1934F0A96F694F67AE5B5AFE8833DCCAF131C560BD486B49F62D07D61` | `0BB724D1934F0A96F694F67AE5B5AFE8833DCCAF131C560BD486B49F62D07D61` |
| `apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx` | 6,960 / `58D88EB3B4E4A8A9AD55296036A080C01950D315F1F7202DB406DAD1B7B84E9A` | 6,963 / `A502E72387370A9EDEAE5A836941D64B05F777E81D65DFDBE33C16113C8454A4` | `A502E72387370A9EDEAE5A836941D64B05F777E81D65DFDBE33C16113C8454A4` |
| `apps/ui-mobile/src/parent/presentation/screens/ProfileSharingScreen.tsx` | 6,219 / `AE1CAE845858E8D87B69DA3D19B3BB02F1CDF349AD3290D5D1E0E714CA089BDD` | 6,175 / `14691E21B24D2819742602221481A511DA6A40E290D39E1DFACFBF129FD17511` | `14691E21B24D2819742602221481A511DA6A40E290D39E1DFACFBF129FD17511` |
| `apps/ui-mobile/src/parent/presentation/screens/CaptureScreen.tsx` | 7,755 / `D61FBF7F3F24115CEED8F6971A4A58309242C2B38F61B102803EAAF2D7637664` | 7,735 / `F53CF3C8E5FD67AFA9817F4D0B94CA8CF2F4251AB8E7743D16556B10E34852F7` | `F53CF3C8E5FD67AFA9817F4D0B94CA8CF2F4251AB8E7743D16556B10E34852F7` |
| `apps/ui-mobile/tests/parentSrsBehavior.test.ts` | 55,558 / `B912CE440C9873F34F1C06D58F63D78AC14D6C3048352AEAB520259A667BD064` | 55,756 / `08D1C0BF4AC260E5E4FD26602A92E66CCDE2ECC387F29A36FE33AA0B4778A7D2` | `08D1C0BF4AC260E5E4FD26602A92E66CCDE2ECC387F29A36FE33AA0B4778A7D2` |

The test file's first remediation pass was 55,568 bytes / SHA-256 `96ABB2469BA65A14FE0A0F6076C8F821A72A20649B7AC4813C1F909111FB0DB8`. Addendum 24 recorded this as the follow-up incoming pin and the exact-copy assertion result as 55,756 bytes / SHA-256 `08D1C0BF4AC260E5E4FD26602A92E66CCDE2ECC387F29A36FE33AA0B4778A7D2`. All five final files are copied under `tmp/fe081-waveM/snapshots/POST_RUN_REMEDIATION/` preserving repository-relative paths; source and snapshot byte counts and SHA-256 values match.

### Fixes and static acceptance

| Finding | Static result |
|---|---|
| Bottom-bar assertion omitted the zero-width constraint | PASS. The source assertion now names `flex: 1, minWidth: 0, minHeight: 52`; it retains the 52 dp minimum target check. `ParentBottomBar.tsx` was not changed. |
| Capture required-photo copy differed from Plan Revision 9 | PASS. Production Capture and the preview use `Chỉ tiếp tục sau khi có một ảnh tranh hợp lệ. Chưa mở buổi học trước ảnh.` The test directly checks the full production sentence and locates that full literal in the preview source-order check. |
| `palette.line` caused two typecheck errors | PASS by static inspection. The existing `palette.outline` token is used in `ui.tsx` and `HomeScreen.tsx`; no token was added, and no `palette.line` reference remains in those files. |
| Redundant capability comparison caused the Profile Sharing typecheck error | PASS by static inspection. The button is inside the existing available-only branch and its disabled expression is now `!teacherSubject.trim() || props.loading`. The outer unavailable branch and all existing handlers remain. |

All five final source/test files were read completely. Read-only search matched the final assertions and user-visible copy to the final source. The exact bottom-bar target, production Capture sentence, preview Capture sentence, and Profile Sharing branch were found. No Capture handler, photo guard, route, payload, step order, controller, or product flow changed. The four non-test files retain the Plan Revision 9 expected after pins. The test's follow-up after pin matches Addendum 24. The 20 shared R/H rows were rehashed against Plan Revision 9: 20 checked, zero mismatches. No DECISIONS.md change was made.

### Approval, report, and coordinator handoff

- Plan Revision 9 includes the remediation manifest and exact-copy assertion follow-up: 84,346 bytes / SHA-256 `974A3267FA66C54D17278EAB03EA40F853ED3A750CBEB58FF1C91FE093624B97`.
- Addendum 23 records the five-path remediation. Addendum 24 clarifies the exact-copy assertion pin without expanding scope. `TASK_APPROVAL.md` after Addendum 24: 72,812 bytes / SHA-256 `AF5B092841F0A648F38E8FF3A447D29267D39206EFD73DEB71A99812F299DC5C`.
- The run-state and remediation ledger record final pins and preserve the source log findings. The three-run total ceilings in Addendum 20 remain unchanged; coordinator run accounting is cumulative.
- Open coordinator action: rerun `pnpm run test` and `pnpm run typecheck` only within the remaining Addendum 20 totals, and account for the earlier supplied runs. The UI-copy validator was not reached by the supplied test command and was not run by Codex.
- `OWNER_MODAL_CALL_APPROVED=NO`. No staging, commit, or push.

### NOT RUN

Corrected test suite, corrected typecheck, validators, `git diff --check`, install, network, backend, Android, emulator, and Modal commands. The supplied initial logs are recorded above and remain consumed runs.


## M3 continuation — owner-approved Capture preview states (COMPLETE)

The previous M3 stop was resolved by the owner's direct approval on 2026-11-14. Before editing the harness, Plan Revision 9 was amended to add `ParentVisualPreviewHarness.tsx` as an M3 E row, specify the Capture-state acceptance, and record the incoming M0 snapshot pin. Addendum 21 records the approval; Addendum 22 corrects only the plan pin presentation and does not expand scope. The final amended plan is 79,202 bytes / SHA-256 `FDA7CE1620BA7B354F492430C52CC446599E6D694F446EB37760F4B174E0ED42`. `TASK_APPROVAL.md` after both append-only addenda is 67,098 bytes / SHA-256 `3335F5A4209E3E33D8A6BFD89D7915019F5E53A3C1D7BA7ADF785E59D7F5325C`. The amendment ledger is `tmp/fe081-waveM/records/WAVEM_M3_SCOPE_AMENDMENT_RECORD.md`.

### Continuation files and pins

| File | Before bytes / SHA-256 | After bytes / SHA-256 | Snapshot SHA-256 |
|---|---|---|---|
| `apps/ui-mobile/src/parent/presentation/ParentVisualPreviewHarness.tsx` | 20,075 / `0E56EABCC599FEECB498BD9C51737E0BB3ECD417E034863F053FC7605F9B995C` (M0 after-pin) | 24,232 / `FA0A77FEDF790EE349B9D6AB42D95C9C938867AC75EB904D01210C9F85DAD481` | `FA0A77FEDF790EE349B9D6AB42D95C9C938867AC75EB904D01210C9F85DAD481` |
| `apps/ui-mobile/tests/parentSrsBehavior.test.ts` | 52,820 / `535556608CA77EA278015FEDDF50C57B57A5F1C2E37BAFF578CC9AC167A0C174` (prior M3 after-pin) | 55,558 / `B912CE440C9873F34F1C06D58F63D78AC14D6C3048352AEAB520259A667BD064` | `B912CE440C9873F34F1C06D58F63D78AC14D6C3048352AEAB520259A667BD064` |

Both continuation files are saved under `tmp/fe081-waveM/snapshots/M3/` with repository-relative paths. The final M3 snapshot audit covers all nine E rows and reports zero source/snapshot mismatches.

### Acceptance results

| Check | Static result |
|---|---|
| Capture state selection | PASS. The harness has separate selectable tabs for empty capture, camera permission denied, and selected photo. The preview now has 27 tabs, including all existing screens/states. |
| Permission-denied state | PASS. The deterministic camera-denied branch displays the concept copy `Camera chưa được cấp quyền. Vẫn có thể chọn tranh từ thư viện.` and retains the gallery alternative. No platform permission request is needed to view it. |
| Selected-photo state | PASS. A code-drawn 280:190 SVG illustration is shown as simulated art and labeled `Ảnh minh họa mô phỏng · không phải tranh thật`. It uses the concept palette and uniform `xMidYMid meet` scaling; no image asset was added. |
| Preview behavior and boundaries | PASS. Capture screen actions are inert. The required-photo notice follows the concept copy `Chỉ tiếp tục sau khi có một ảnh tranh hợp lệ. Chưa mở buổi học trước ảnh.` The harness Capture tabs render a harness-only composition using the existing shared primitives; they do not import `CaptureScreen`, ImagePicker, controller, application API, or network code. The production `CaptureScreen`, controller, route, step order, handlers, and flow were not changed. The dev/environment gate and compact 56 dp tab row remain unchanged. |
| Layout/static robustness | PASS. The image-only frame is aspect constrained at 280/190 with a 190 dp minimum; text wraps with shrink constraints; all card children remain in normal flow. No absolute overlay, negative overlap margin, non-uniform SVG stretch, or fixed text/control height was added. Preview buttons remain accessible through the shared primitives. |

### Assertions and visible copy

- Replaced the older harness assertion requiring a direct `<CaptureScreen>` render with the empty-state `CapturePreviewScreen` fixture assertion. Reason: the harness-only state preview must not expose camera/gallery APIs.
- Added assertions for all three selectable Capture states, the concept denial copy, simulated-photo label, and absence of `CaptureScreen`, `ImagePicker`, camera/library permission requests, `ParentApi`, controllers, and `fetch`. Reason: make the owner-approved preview boundary and deterministic states explicit. The final copy pass also aligned the required-photo notice to the plan's concept wording. Existing production Capture permission, file-size, and one-photo assertions remain in the R3 behavior section; no flow assertion was removed.
- Added a source-order acceptance assertion from the required badge through the permission notice, camera/gallery actions, photo frame, required-photo notice, and continue action. Reason: retain the concept's top-to-bottom hierarchy and keep these card children in ordinary flow.
- Added the Vietnamese tab labels `Chụp · từ chối quyền` and `Chụp · đã chọn ảnh`. The preview uses the concept Capture strings `Chụp hoặc chọn tranh`, `Ảnh tranh giấy là bắt buộc.`, `BẮT BUỘC`, `Camera chưa được cấp quyền`, `Vẫn có thể chọn tranh từ thư viện.`, `Mở camera`, `Chọn từ thư viện ảnh`, and `Tiếp tục sau khi chọn ảnh`; the required-photo notice uses the plan's localized concept wording. Empty and selected-photo states are labeled, with selected art marked `Ảnh minh họa mô phỏng · không phải tranh thật`. No production-screen copy changed in this continuation.
- New test assertions were matched against the final source using read-only search. No test suite was run.

### Static review and integrity

- Re-read the complete harness and complete `parentSrsBehavior.test.ts` after their final edits. Imports and local declarations are unique; the new SVG primitives are used; there is no `CaptureScreen`, ImagePicker, controller, application API, or fetch reference in the harness. Capture preview callbacks resolve to inert `ignoreAction` functions.
- R/H re-hash against the amended Plan Revision 9: 20 rows, zero mismatches. E rows outside M3: 18 unique source/snapshot pairs, zero mismatches. All nine M3 E source/snapshot pairs match.
- M0, M1 and M2 results remain unchanged. M3 now passes acceptance 3; no production source or additional source file outside the amended M3 allowlist was needed.

### Open notes for the coordinator

- All 27 harness tabs are available for visual review. Capture denial and selected-photo previews are deterministic and do not require device permissions. Emulator and large-font visual review remain for the coordinator; Codex did not run an emulator.
- Resolve the task-pinned Rev67 versus repository-wide Rev60 authority mismatch after the run. D-017 O1 remains the pre-existing Rev67 deviation already recorded in the original M3 section.

### NOT RUN

Tests, typecheck, validators, `git diff --check`, install, network, backend, Android, emulator, and Modal commands. No staging, commit, or push.
