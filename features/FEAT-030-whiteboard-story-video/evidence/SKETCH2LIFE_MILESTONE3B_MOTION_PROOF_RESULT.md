# SKETCH2LIFE — MILESTONE 3B MOTION PROOF RESULT

2026-10-09 · FEAT-030 revision 20 · **TECHNICAL_PROTOTYPE_PARTIAL / MOTION_PROOF_NOT_PASSED / VISUAL_QA_NOT_PASSED**.

Một candidate local có **tay/chân đổi tư thế thật** đã được tạo, render và decode: 6 giây, 24 FPS, 144 frames. Nhưng source-part splits, khớp, matte boundary và background patch **chưa đạt hình ảnh**. Không dùng candidate này cho Golden Story; không sửa/tuning/render tiếp sau phát hiện blockers. Người dùng chưa xem/chấp nhận nên không có MOTION_PROOF_PASS.

## 1. Scope, approval và baseline được bảo vệ

- Owner conditional approval S1 local demo story 4 scenes/55s/bướm ở kết, M1 Option A rig thật, A1 candidates, V1 Enhanced Hand-Drawn source-derived style, C1 local only. I1 chỉ candidates/rig/5–8s proof/tests/report. **T1 external TTS chưa được phép thực thi.** Không coi đây là server Gate A/B hoặc final asset approval.
- Branch `codex/feat-018-contract-plan`; HEAD `93668ffdaa7f2890fe9498596c670006a87eba4a`; staged files trống. [Git/code trước sửa](D:/Codex/Sketch2Life/motion_proof_3b_2026-10-09/git-before.json) ghi cả existing dirty worktree và Python hashes.
- Original `familly.jpg` là `family1.jpg` alias đã xác minh: JPEG 594×336, SHA-256 `52caf90a2242d04fc107afa1f17b8de738c5f8982200fc504fe725a5607ee3d3`. Original, chín master masks và source assets cũ không sửa; kiểm tra hashes trước/sau. Real source/derived pixels ở ngoài Git.
- Không import/tích hợp vào production pipeline/HTTP/jobs; không đổi V1, V2 flag default OFF, Gates hoặc dữ liệu người dùng. Ba file V1 dirty từ trước, drafts tay chưa duyệt, MP4/artifacts các vòng cũ được bảo vệ.
- **Không** TTS/audio, GPU rental, paid/remote inference, image upload/training, butterfly render, Golden55s, commit/push/merge/deploy. Một motion candidate, hai encodings clean/debug cùng timeline, không phải hai vòng visual refinement.

## 2. Những gì thực sự đã triển khai

### Generic limited rig

[limited_character_rig_v2.py](../../../backend/src/sketch2life/infrastructure/media/limited_character_rig_v2.py) là module CPU/offline độc lập. Không hardcode ảnh gia đình/object ID trong engine. Nhận source-bound full-canvas RGBA parts, hash, bones/joints, explicit pose targets; kiểm tra source identity/asset bytes/decoded image, coordinate system, limits.

- Two-bone IK giữ chiều dài upper/lower limbs; target ngoài reach trả NEEDS_POSE_REVIEW, không tự stretch thêm.
- Similarity affine warping từng part với RGBA premultiplication; đầu/torso chỉ root translation, không generate/flip/deform mặt.
- Foot swing có easing/lift, foot endpoint world-lock trong pha planted. Camera light eased zoom 1→1.035, same canvas. Không lấy whole-cutout translate làm posture animation.
- Limits: 32 parts, canvas edge≤2048 / area≤2.07MP; proof 5–8s/12–30 FPS/≤240 frames; cooperative 120s deadline. Đây không phải hard realtime hoặc process-level memory quota. Peak memory chưa đo, không bịa số MiB.
- Error boundaries có SOURCE_ASSET_MISMATCH, NEEDS_MASK_REVIEW, NEEDS_POSE_REVIEW, MOTION_RESOURCE_LIMIT, explicit candidate permission, repository-media refusal. Không fallback V1.

### Actual child candidate / proof

[story_character_motion_proof.py](../../../tools/story_character_motion_proof.py) nhận manifest và **private manual rig definition**, không gọi model. Anatomy joints/polygons nằm ở private definition, không gắn source children/coords vào engine/tests.

Nhân vật proof: `family-52caf90a-child`, 11 parts: body/head + hai upper arms + hai forearms + hai thighs + hai shins + hai shoes. Manual polygon selection được intersect với **master silhouette thật**; không bbox/ellipse thay segmentation. Part overlaps chỉ ở derived rig; chín master masks bất biến.

Body remainder ban đầu = original child mask trừ moving part regions. Điều này dựng bind pose chính xác nhưng **không chứng minh decomposition có nghĩa giải phẫu hoặc đủ coverage khi pose thay đổi** — chính đây là failure của candidate.

Timeline: 0–0.3s original bind; khoảng 0.3–1.6s buông tay/standing preparation; sau 2s ba foot-swing intervals luân phiên, root tiến 20 native pixels; end hold đến 6s. Không natural walk claim: là một limited articulation candidate với các lỗi rõ.

Bố/mẹ là **static source references** trong proof; chưa có parent rig/release/walk samples. Không coi proof của bé là M1 full-family acceptance. Butterfly chưa tạo vì ưu tiên proof bước đi/buông tay; sample bướm chờ art approval.

## 3. Style và source/new pixel provenance

[Style comparison original/enhanced/diff](D:/Codex/Sketch2Life/motion_proof_3b_2026-10-09/candidate-01/original-enhanced-style-comparison.png).

`ENHANCED_HAND_DRAWN_SOURCE_DERIVED_CANDIDATE`: RGB Gaussian radius **0.4 px**, blend **0.12**; alpha không blur; no palette replacement/3D/anime/flat-vector regeneration. Original không đổi. RGB MAE so decoded source **0.2035584/255**. Đây chỉ light smoothing candidate, không chứng minh chất lượng “enhanced” đã được duyệt. Texture và bảng màu vẫn nhìn thấy; không pixel-exact claim cho enhanced RGB.

Provenance tách rõ:

1. Original/master source: immutable bytes/hash.
2. `.source.png` part: source RGB bên trong derived part mask; alpha từ source silhouette/selection.
3. `.enhanced.png`: bounded RGB smoothing, same selected alpha; source-derived candidate, cần review.
4. Posed pixels: resampling/transforms từng part; mới theo nghĩa vị trí/interpolation, không original pixel-exact frame.
5. Occluded-background patch: **source-cloned donor pixels, new location**; sample box `[365,155,390,200]`, donor coordinate map và applied-mask. Không AI/inpainting, không white rectangle/fade. **Không phải recovered hidden original background**, và đã bị đánh giá không đạt continuity.

Master mask/identity permissions chỉ conditional candidate/static history; candidate-asset review vẫn pending. Không đưa local approval vào server-approved package.

## 4. Artifacts thực tế

Private directory: `D:/Codex/Sketch2Life/motion_proof_3b_2026-10-09/`. Không chứa asset nào được duyệt cho Golden.

- [Clean Motion Proof MP4](D:/Codex/Sketch2Life/motion_proof_3b_2026-10-09/candidate-01/motion-proof.mp4).
- [Joints-debug MP4](D:/Codex/Sketch2Life/motion_proof_3b_2026-10-09/candidate-01/motion-proof-joints-debug.mp4). Markers/bones chỉ debug overlay, không artwork thay nhân vật.
- [Actual encoded-video time contact sheet](D:/Codex/Sketch2Life/motion_proof_3b_2026-10-09/actual-mp4-time-contact-sheet.png), frame samples 0/24/48/72/96/120/143.
- [Native rig/source overlay](D:/Codex/Sketch2Life/motion_proof_3b_2026-10-09/candidate-01/rig-source-overlay.png).
- [Full pose contact sheet](D:/Codex/Sketch2Life/motion_proof_3b_2026-10-09/candidate-01/pose-contact-sheet.png) và [child pose detail](D:/Codex/Sketch2Life/motion_proof_3b_2026-10-09/candidate-01/child-pose-detail-sheet.png) tại 0/1.6/2.7/3.7/4.7/6s.
- [Source identity/head comparison](D:/Codex/Sketch2Life/motion_proof_3b_2026-10-09/source-identity-head-contact-sheet.png). Head cùng nguồn, translated/crop rounded; không face recognition score hoặc identity model PASS.
- [Source-derived asset manifest đầy đủ](D:/Codex/Sketch2Life/motion_proof_3b_2026-10-09/source-derived-asset-manifest.json): refs/hash source/enhanced/derived masks, parent identity, StyleProfile, donor map, master masks, review status.
- [Manual joints/part definition](D:/Codex/Sketch2Life/motion_proof_3b_2026-10-09/child-rig-definition.json).
- [Per-frame joint transforms](D:/Codex/Sketch2Life/motion_proof_3b_2026-10-09/candidate-01/joint-transform-timeline.json): 144 poses, phase/plant flags, root offset và inverse affine cho mỗi part.
- [Render/decode metrics](D:/Codex/Sketch2Life/motion_proof_3b_2026-10-09/candidate-01/motion-metrics.json).
- [Visual findings](D:/Codex/Sketch2Life/motion_proof_3b_2026-10-09/visual-quality-findings.json) cùng [numeric diagnostic correction](D:/Codex/Sketch2Life/motion_proof_3b_2026-10-09/visual-quality-findings-correction.json). Phải đọc correction; số 69 green residual trong audit đầu **không hợp lệ** do uint8 overflow.

Hai videos: **6.0s / 24 FPS / 144 frames / 1188×672**, full sequential decode thành công. Artwork native 594×336, output upscale2× không bổ sung detail. Silent, không audio stream/narration. Không phải whiteboard story55s.

## 5. Bằng chứng chuyển động và Visual Quality

### Những kiểm tra kỹ thuật đạt trong phạm vi prototype

- Bind reconstruction của 11 layers = enhanced source RGBA inside original child mask, kiểm tra before encoding; không sửa source mask để cho test pass.
- Relative hand/leg angles thay đổi: left arm ≈**87.56°** shortest rotation, right arm ≈**94.40°**, right thigh ≈**66.63°** từ bind đến gần1.6s. Root chỉ `(20,3)` px cuối clip; rõ không một global whole-character affine.
- Independent per-frame audit: max leg-length error **3.1974e-14 px**; consecutive planted endpoint world delta **0 px**. Đây là foot endpoint constraints, **không đủ** cho no-visible-foot-skating/sole-contact PASS.
- Decode tất cả 144 clean frames và debug frames, duration đúng6s; max global adjacent encoded-frame MAE **1.987531/255**. Global delta không thay visual naturalness.
- Candidate preparation/render/decode ghi thời gian **37.578s**, không bao gồm subsequent independent audit/tests; không benchmark GPU hoặc controlled performance study.

### Blockers nhìn thấy trên pose sheets và encoded video samples

| Vùng | Quan sát | Nguyên nhân/phạm vi sửa cần thiết |
| --- | --- | --- |
| Vai/cánh tay | Blue sleeve/core có notch/hở và forearm/hand chưa nối hình mượt | Manual part boundaries/pivot overlap không đủ tạo continuous anatomy. Cần anatomical masks + shoulder/elbow joint art được review, không thay root travel/speed để che |
| Hip/knee/shoes | Legs/shorts/shoes có mảnh đứt, vị trí nối thô; chưa thành walk đẹp | Original single pose thiếu hidden joint surfaces, semantic split chưa đủ; IK lengths đúng không đảm bảo texture/silhouette continuity |
| Nét chi cũ | Còn ghost outline ở vị trí source khi limb mới di chuyển | Body remainder giữ **19 pixels dưới y275**; còn source shoe-colored boundary pixels nằm ngoài child master mask, thuộc static partition khác. Source partition đúng về hash/disjointness nhưng không motion-ready matte |
| Nền vùng child cũ | Beige donor patches sai grass/path local continuity, còn hình/vệt không tự nhiên | Copy source texture không khôi phục unknown occluded background. Cần manual background art/cleanup mask có provenance/approval, không khẳng định texture-preserved đồng nghĩa background correct |
| Bố/mẹ | Tay vẫn giơ trong khi bé buông; chưa có interaction rig | Parent release/walk chưa thực hiện, không full-family story readiness |
| Foot contact | Endpoint không trượt theo world math, nhưng fragmented soles/khớp làm contact chưa thuyết phục | Không thể tuyên bố không có foot skating nhìn thấy. Cần xem/duyệt sole art và chân ở stance dưới camera compensation |

Head/hair/eyes/blue-shirt/pink-shorts/green-shoes còn nhận diện nguồn, không sinh người khác; tuy nhiên clothing silhouette bị cắt/hở bởi moving parts. **Identity anchor retention không đủ để vượt blocker deform/joints**.

Independent diagnostic ban đầu có bug uint8 RGB+15 overflow, báo69 green-body residual sai. Đã recompute signed int16: **0 green pixels trong body remainder dưới y260**; có **46 green source pixels trong vùng feet native nằm ngoài child master mask**. Audit gốc giữ nguyên, correction tách riêng, script được sửa phép tính. Pixel classification này chỉ gợi ý cleanup boundary, không auto human identity/segmentation approval. Không có second render hoặc visual parameter tuning từ sửa diagnostic.

Kết luận: có tư thế thay đổi thật nhưng **liên kết limb silhouettes/background không đạt**. Giữ **MOTION_PROOF_NOT_PASSED / candidate assets NEEDS_VISUAL_REVIEW**. Không auto enhance tiếp hoặc fallback Option B.

## 6. Tests thực tế

Lệnh regression đã chạy:

```text
backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_limited_character_rig_v2.py backend/tests/unit/test_story_world_v2.py backend/tests/unit/test_story_world_v2_multidrawing.py backend/tests/unit/test_story_video_planner.py backend/tests/unit/test_whiteboard_mvp_renderer.py backend/tests/unit/test_whiteboard_stroke_extraction.py backend/tests/unit/test_whiteboard_v2_engine.py backend/tests/unit/test_whiteboard_v2_schedule_debug.py backend/tests/contract/test_story_video_file_api.py
```

**131 passed, 0 failed, 76.71s, exit0**, không skip/deselect trong selection. New rig suite22 tests; 109 existing selected V1/V2/world/multi-drawing/planner/file API tests. Synthetic family/ocean PNG/JPEG regression là tests cơ chế, không dùng thay real image để báo proof PASS.

New tests kiểm tra bind RGB/alpha, relative part rotation, fixed-length IK, unreachable/nonfinite/error handling, world foot lock/lift/easing, immutable source alpha, bounded style/camera, changed asset/identity/missing joints và refusal Golden55s/Git private output/permission thiếu. Không synthetic anatomy hoặc mathematical assertion được gọi visual acceptance.

First isolated new test run: **21 pass, 1 fail** vì assertion đòi RGB pixel-exact trong enhanced output. Enhanced cố ý derived; test sửa thành bounded RGB delta≤3 cho synthetic sample và kiểm tra `blend=0` exact. Không sửa enhancement/thresholds của video để làm tests pass. Final regression22 new cases đều pass.

Checks:

```text
backend/.venv/Scripts/python.exe -m ruff check backend/src/sketch2life/infrastructure/media/limited_character_rig_v2.py tools/story_character_motion_proof.py backend/tests/unit/test_limited_character_rig_v2.py
backend/.venv/Scripts/python.exe -m mypy --follow-imports=silent backend/src/sketch2life/infrastructure/media/limited_character_rig_v2.py
backend/.venv/Scripts/python.exe tools/validate_repository_security.py
git diff --check
```

Ruff3 files pass; Mypy **1 new source module only** pass, không tool/full backend. Security final handoff pass (1.670 publishable files scanned), `git diff --check` pass. Report links: zero broken links. SHA-256 final verification: tất cả Python đã có trước tác vụ, ảnh gốc, source manifest, 9 master masks và 9 source cutouts không thay đổi. HEAD/remote-tracking vẫn `93668ffdaa7f2890fe9498596c670006a87eba4a`, branch `codex/feat-018-contract-plan`, index empty. V2 default false ở settings/pipeline; không sửa các module đó. Không Ruff/Mypy toàn repository. Other suites/Vision V3, child-voice, GPU/model, Lightning, family walk, butterfly/full55s không chạy. Vision fixture issues không được sửa hoặc coi PASS trong tác vụ này.

## 7. Danh sách file thay đổi thuộc tác vụ này

Repository code mới, không sửa file engine/V1 hiện có:

1. `backend/src/sketch2life/infrastructure/media/limited_character_rig_v2.py` — source-bound candidate part transforms, StyleProfile, IK/contact/easing helpers.
2. `tools/story_character_motion_proof.py` — explicit private local candidate prep, one proof clean/debug encode/decode and manifests.
3. `backend/tests/unit/test_limited_character_rig_v2.py` — 22 synthetic unit/guard tests.

Feature documents updated/add:

4. `features/FEAT-030-whiteboard-story-video/approvals/TASK_APPROVAL.md` — revision20 conditional scope, recorded before implementation.
5. `features/FEAT-030-whiteboard-story-video/plan/PLAN.md` — bounded proof plan/acceptance.
6. `features/FEAT-030-whiteboard-story-video/CONTEXT.md` — actual outcome/limits.
7. `features/FEAT-030-whiteboard-story-video/DECISIONS.md` — source/matte/rig/candidate stop decisions.
8. `features/FEAT-030-whiteboard-story-video/status/STATUS.md` — NOT_PASSED, waiting review.
9. `features/FEAT-030-whiteboard-story-video/evidence/README.md` — evidence index.
10. `features/FEAT-030-whiteboard-story-video/evidence/SKETCH2LIFE_MILESTONE3B_MOTION_PROOF_RESULT.md` — this report.

Private new files: `git-before.json`, `child-rig-definition.json`, `inspect_source.py`, `audit_candidate.py`, complete asset/diagnostic manifests, style/identity/pose/encoded sheets, source-derived part PNGs, donor map/patch, raw poses/frames, two MP4s, per-frame transforms/metrics and handoff evidence. Paths ở mục4; không stage/copy vào Git.

Existing dirty source/test/tool files, three V1 files, previous approval package/3A plans, hand drafts/artifacts không phải thay đổi mới của tác vụ. Baseline hashes phải giữ để phân biệt; không ghi “clean worktree” hoặc tất cả uncommitted files là proof code.

## 8. Điều kiện trước Golden Story full render

1. Người dùng review actual MP4 và xác nhận assessment; candidate hiện chưa được chấp nhận, **không full55s render**.
2. Source-derived **motion matte và semantic part masks** cần sửa/duyệt riêng: cover true color/outline extents, không để shoe/arm residue trong static body/background. Giữ chín master masks nguyên bản; derived cleanup region riêng có owner/parent IDs/provenance.
3. Cần anatomical joint/occluded limb artwork và background patches được chuẩn bị thủ công/review. Đây là asset problem; thêm smoothing/speed/IK constraints không tạo hidden anatomy đúng.
4. Child proof mới phải không hở/ghost/biến dạng, foot shape/contact hợp lý và owner acceptance. Parent rigs/release/walk chưa có; cần candidates/sample riêng trước full family story.
5. Butterfly body/wing art phải trình duyệt rồi mới separate sample draw/flap/flight. TTS chỉ concept-approved, cần voice-sample/data/permission trước external call; không chạy ở proof này.
6. Golden55s, audio/subtitle/story timeline integration và Lightning acceptance vẫn deferred. V1/default/V2 OFF/Gates/production không thay.

**Dừng tại proof candidate01. Không mở vòng refinement vô hạn. Kết quả là prototype chuyển động có bằng chứng nhưng Visual/Motion QA failed, chưa phải animation đẹp hoặc Golden Story sẵn sàng.**
