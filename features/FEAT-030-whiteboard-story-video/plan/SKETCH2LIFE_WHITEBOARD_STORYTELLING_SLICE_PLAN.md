# SKETCH2LIFE — WHITEBOARD STORYTELLING VERTICAL SLICE PLAN

Historical revision21. Superseded by [revision22 current plan](SKETCH2LIFE_WHITEBOARD_STORY_SLICE_PLAN.md): newly drawn object mandatory; focus-only no longer meets acceptance. Preserve this document as planning history.

2026-10-09 · FEAT-030 revision 21 · PLANNING COMPLETE / AWAITING_OWNER_APPROVAL

## 1. Quyết định ưu tiên và phạm vi duyệt

Mục tiêu chính: **Narration-Driven Whiteboard Storytelling Animation**. Câu chuyện phát triển trên bảng theo từng câu/speech beat, không vẽ toàn bộ tranh trước rồi dùng phim hoạt hình nhân vật làm pipeline bắt buộc. Giữ Whiteboard Engine V2, World Model, Asset Registry, stable IDs và source provenance. Limited rig/walk của revision20 giữ nguyên như experiment optional, không xóa, sửa lại hoặc coi là đã PASS.

Lượt hiện tại CHỈ đọc source, cập nhật kế hoạch và đưa đề xuất để duyệt. Không application-code edits, candidate art, audio, MP4 hay contact sheet mới. Slice dưới đây là **đề xuất**, không báo đã render. Full Golden55s, production HTTP/upload/Gates và Lightning đều chưa triển khai trong scope này.

Git trước cập nhật docs: branch `codex/feat-018-contract-plan`, local HEAD `93668ffdaa7f2890fe9498596c670006a87eba4a`; worktree có nhiều thay đổi cũ, index trống. Không stage/commit/push/merge/deploy/reset. Ba V1 files dirty, tất cả code/rig/assets/candidate01 và media cũ được bảo vệ. V1 vẫn mặc định, V2 flag OFF.

## 2. Nguồn và approval boundary

- Source family1.jpg là alias original familly.jpg đã xác nhận, JPEG RGB594×336, SHA-256 `52caf90a2242d04fc107afa1f17b8de738c5f8982200fc504fe725a5607ee3d3`.
- [Chín master masks và source manifest](D:/Codex/Sketch2Life/real_family_benchmark_2026-10-09/source-object-manifest.json); manifest SHA-256 `693647da0cc2cf2b2cb7261ba4c49451a75db7ed27b292e676fee81550ba0b14`. Giữ originals/master masks bất biến.
- [World Model benchmark](D:/Codex/Sketch2Life/real_schedule_debug_2026-10-09/benchmark-world.json): tái sử dụng source identities/assets, không biến fixture events thành authorization.
- [3B approval package](../approvals/SKETCH2LIFE_MILESTONE3B_APPROVAL.md) và [Motion Proof result](../evidence/SKETCH2LIFE_MILESTONE3B_MOTION_PROOF_RESULT.md): lịch sử được giữ nguyên.
- S1 đã LOCAL DEMO APPROVED cho nội dung bốn cảnh55s. T1 **chưa cấp phép external TTS execution**. Latest request duyệt hướng whiteboard-first và planning, không tự coi là đã duyệt chính xác script/cue revision hoặc quyền render slice.
- Script rút gọn ở mục3 là **NEEDS_OWNER_LOCAL_SCRIPT_APPROVAL**. Nội dung chỉ chọn thông tin source/demo intro sẵn có, không lời kể thật của bé, không sáng tạo sự kiện mới, không server-approved Gate A/B.
- Binding local sau duyệt phải lưu exact text/script hash, timeline revision/hash, source/mask/asset hashes và bằng chứng owner approval; sửa text/cue/content làm mất hiệu lực duyệt tương ứng. `review_ref` caller tự nhập không là xác thực của server. Server Gate A/B và immutable session/package/script binding vẫn deferred.

## 3. Slice đề xuất: một bảng liên tục, 14 giây mô phỏng

**Ưu tiên focus shift thay new asset**, để chứng minh vẽ theo lời kể mà không bị kẹt ở rig/bướm chưa có artwork đã duyệt. Không nhân vật đi dạo/buông tay trong slice. Cả ba giữ original pose/source layout. Không redraw cả canvas hoặc restart trắng giữa beats.

Script demo rút gọn cần duyệt:

> Đây là bố, mẹ và em. Cả nhà ở trước ngôi nhà. Bên cạnh là vườn hoa.

Đây là ba câu mô tả ảnh và nội dung intro, không xác nhận người nói là trẻ. Nếu người dùng muốn câu khác, cập nhật mapping và xin duyệt lại trước render.

| Beat | Cửa sổ mô phỏng | Exact text / nguồn | Visual task đề xuất |
| --- | --- | --- | --- |
| slice-family-01 | 0–7s | “Đây là bố, mẹ và em.”; local demo intro/source family | Bố → mẹ → bé theo thứ tự được duyệt; mỗi object outline → detail → color; không màu vườn/nền chạy trước. Có thể interleave tay liên kết chỉ với region/phase và reason được duyệt. |
| slice-house-02 | 7–10s | “Cả nhà ở trước ngôi nhà.”; local demo intro/source house | Gia đình đã vẽ giữ nguyên; vẽ/tô nhà từ source pixels tại vị trí gốc. Không vẽ lại gia đình. |
| slice-garden-03 | 10–13s | “Bên cạnh là vườn hoa.”; local demo intro/source garden | Vẽ/tô garden source region theo structural paths và localized texture brush; không phát sinh hoa/bướm mới. |
| slice-focus-04 | 13–14s | Tiếp nối garden cue, không thêm câu/sự kiện | Giữ artwork đã có, camera easing nhẹ về vườn, không làm crop mất toàn bộ family. Nhấn trọng tâm hình ảnh theo câu nói về hoa. |

14s là **SIMULATED_CUES_ONLY**, không thời lượng nói đã đo, không giả measured TTS. MP4 slice sau duyệt sẽ silent có nhãn câu/beat/time; không tạo giọng giả hoặc dùng audio khác để báo speech sync. Nhu cầu10–15s được chứng minh dưới timing mô phỏng trước; nếu chuyển sang audio thật, đo lại và xin điều chỉnh scope/script nếu lệch10–15s. Không time-stretch hoặc cắt lời âm thầm.

Budget7/3/3/1 là draft, không hứa đủ để natural drawing mọi chi tiết. Phải chạy stroke feasibility trước render: nếu số strokes/path travel cần thời gian lớn hơn slot, trả `DRAW_TIMING_INFEASIBLE`, kèm object/phase/travel/minimum-duration reasoning. Không tăng tốc cực độ để đủ14s, không loại bỏ mắt/tóc/kính/hoa mà không báo, không tăng thresholds lặp vô hạn. Có thể xin duyệt crop/focus nhỏ hơn hoặc dài hơn; không tự đổi nội dung.

Các source IDs chọn: `family-52caf90a-father`, `family-52caf90a-mother`, `family-52caf90a-child`, `family-52caf90a-house`, `family-52caf90a-garden`. Source tree/sky/path/remaining-background giữ registry nhưng không bắt buộc dựng trong slice vì chưa được nhắc ở script rút gọn. Board trắng ở vùng chưa vẽ là whiteboard chưa hoàn thiện, **không là restored hidden background**. Final slice chỉ cần fidelity vùng/object đã thực sự vẽ, không báo full original reconstructed. Original full board55s vẫn là tác vụ riêng.

Mastergarden là region chứa cả hoa và cỏ, không có individual flower masks. Nếu cần onset riêng từng bông hoa, dùng derived contour masks/cue regions reviewable có parentID/source SHA và nằm trong garden; không thay master, không rectangle làm mask. Phiên bản tối thiểu cue cả garden, không bịa semantic segmentation mỗi hoa.

## 4. Narration-to-Draw Timeline contract đề xuất

Thêm local versioned contract riêng, không nới ApprovedStoryPackageV1 hoặc biến14s thành full V2 story hợp lệ.

- Timeline: timeline_id/version, mode `SIMULATED_CUES_ONLY | MEASURED_AUDIO_CUES`, canvas_id, source hash, script hash, approval scope/ref, audio_ref/hash nullable, measured_duration nullable, cue_source, cue revision/hash, explicit local-demo-only.
- Beat: stable beat_id; segment_id + exact quote/character span/text hash; approved_fact_ids/confirmed_anchor_ids/event IDs + mapping rule/provenance. Chưa có trusted IDs thì để empty và server status NOT_VERIFIED, không fake approval.
- Cue: onset/offset, source `OWNER_SIMULATED | MANUAL_AUDIO_ALIGNED` (local measured/imported alternative sau này), evidence/ref, audio hash khi measured. Tổng duration không được dùng thay các onset câu thực tế.
- Draw task: object/asset ID, parent provenance `SOURCE | APPROVED_NEW`, source/mask/asset hashes, explicit stroke subset/phase, start/end, dependencies, persistent revealed state, authorized region, optional interleave reason.
- Camera/action: explicit beat-bound focus/keyframes/easing, start/end. No walk event trong script chỉ mô tả static. Optional unsupported action phải fail `UNSUPPORTED_ACTION`, không hidden fallback V1.
- State: object/phase/stroke progress và color coverage tích lũy theo canvas ID, xuất checkpoint trước/sau mỗi beat. Beat sau không tự reset progress.
- Validation: unknown object/stroke/unauthorized asset hoặc cue không map exact approved text phải block; audio cues out of range/overlap trái quy tắc, stale hash hoặc thiếu approval phải block. Các lỗi `NARRATION_CUES_INVALID`, `SCRIPT_APPROVAL_REQUIRED` là **proposed** contract codes, chưa code chạy.

Approval nội dung mới và approval artwork là hai gate riêng. Nếu lời kể đã duyệt nhắc bướm: tạo stable new-object ID/event với quote/provenance, local manual candidate hoặc model chỉ khi quyền riêng được duyệt; review asset/style/hash trước append draw tasks; tuyệt đối không sinh cảnh độc lập hoặc tự gán bướm là source. Bướm không cần cho slice focus-shift tối thiểu, không xóa khỏi Golden content đã duyệt.

## 5. Actual code gap và module change map sau duyệt

| Module | Hiện có từ source kiểm tra | Thay đổi nhỏ nhất dự kiến, CHƯA triển khai |
| --- | --- | --- |
| `contracts/schemas/story_strokes_v2.py` | ScheduledStrokeV2 có beat_ref, phases và timestamps; SceneDrawScheduleV2 có duration/hold. | Giữ contract cũ; bổ sung additive timeline/task contracts ở file riêng `story_narration_draw_timeline_v2.py`. Không giả beat_ref tự chứng minh alignment. |
| `application/services/story_draw_schedule_v2.py` | build_draw_schedule phân bổ theo path length/phase budgets; mọi stroke có beat_ref = scene.segment_ids[0]. validate đòi every path exactly once trong scene. New objects bị UNSUPPORTED_ACTION. | Giữ legacy builder/validator. Thêm local compiler `narration_draw_timeline_v2.py` chia allowed strokes vào explicit beat windows, validate subset/dependencies/checkpoints/timebudget. Không ép full scene validator chạy trên partial canvas bằng cách nới guard âm thầm. |
| `infrastructure/media/whiteboard_renderer_v2.py` | Shared stroke fraction điều khiển reveal/pen; outline/detail brush cũng reveal sourceRGBA, tức có thể lộ màu từ đầu. _frame rebuild board theo elapsed; background có offset riêng nếu không trắng. Camera hiện là static per scene. | Opt-in timeline entrypoint trên cùng V2 primitives: một absolute audio/cue clock; không autonomous background offset; phase-specific source-ink selection rồi texture/source-color brush; persisted reveal; cùng geometry cho pen/audit. Không full-opacity fade/whole-region show/final snap. |
| `infrastructure/media/object_stroke_engine_v2.py` | Complexity-aware source mask structural/detail/color extraction; naturalness còn NOT_PASSED. | Reuse, trước hết đo feasibility. Chỉ chỉnh nếu evidence cho thấy path ordering/phase pixel-role chưa đủ, bounded patch không threshold search. Phải preserve important structural source pixels; nếu không đủ trả NEEDS_STROKE_REVIEW. |
| `application/services/story_world_model.py` — SourceAssetRegistry + World Model | Verified source assets/masks/stable IDs đã có. | Reuse immutable; approved new-asset resolver adapter chỉ khi slice được chọn có new content. Không cần thay registry identity để làm focus shift. |
| `infrastructure/media/scene_state_composer.py` | Target-state still, source/background placeholders và static crop; chưa persistent stroke-canvas giữa speech beats. | Không dùng still target thay animation; reuse source-bound placement. Persistent canvas executor và eased temporal camera ở local timeline renderer. |
| `infrastructure/media/limited_character_rig_v2.py` và `tools/story_character_motion_proof.py` | Experimental limb/IK/camera + failed candidate01. | **KHÔNG SỬA**. Có thể reuse camera easing helper qua adapter phù hợp; rig/walk không dependency. |
| V1 StoryVisualCueV1/StoryboardDrawBeatV1, planner, TTS/subtitles/assembly | Có scene-level visual cue/beat và measured TTS duration contracts; không là phrase-level verified V2 speech alignment. | Read/reuse mechanics sau kiểm tra adapter; không sửa V1 contract/pipeline cho slice. TTS execution không được gọi. Silent MP4 encode và burned cue labels local; audio integration deferred. |
| `tools/story_whiteboard_storytelling_slice.py` (mới đề xuất) + dedicated tests | Chưa có. | Private source/manifest/script/cues input, explicit permission, dry-run validator rồi one clean/debug10–15s render; snapshots/coverage/cue audits; không production HTTP/jobs. |

Một lỗi gốc cần giải quyết: gọi source pixel reveal cho OUTLINE/DETAIL khiến texture/màu xuất hiện cùng nét. Cần **source-derived structural ink coverage riêng** và color coverage chỉ đi theo authorized COLOR path sau prerequisite. Không recolor toàn nguồn thành vector; original sourceRGB không thay đổi. Phase mask/selectors là derivative có provenance, cần giữ textural màu trong COLOR. Nếu source ink không thể tách mà mất features, trả NEEDS_STROKE_REVIEW và owner review, không giả natural stroke.

Renderer/timeline adapter nằm sau opt-in local path, V2 default vẫnOFF. Slice là isolated diagnostic clip; không phá quy tắc full story3–6 cảnh,5–20s/cảnh,40–60s tổng. Không ép 1canvas/14s vào full ScenePlan như production READY.

## 6. Audio và continuity

Hiện không có quyền gọi EdgeTTS. Chọn **silent simulation**; cue labels không coi là audio thật hoặc đo sync. Phương án tiếp theo: người dùng cung cấp approved audio demo local hoặc duyệt riêng voice/data trước TTS. Khi có audio: decode/probe duration thật, kiểm tra script text, nghe và annotate exact sentence/speech onset/offset local, lưu audio SHA + cue evidence; trình cue review rồi compile. Không phân bổ thời gian theo số từ hoặc chia đều measured tổng rồi nói đó là speech cues thực.

Cùng địa điểm: dùng cùng board/state/camera/source coordinates; focus không làm biến mất/xóa đối tượng đã vẽ. Source-fidelity so ở canonical unzoomed canvas. Pan/zoom chỉ crop/resample presentation, báo riêng lossy encoder difference.
Partial erase/redraw/page transition có thể lên kế hoạch khi script thật đổi bối cảnh: explicit authorized region, erase path, retained state, redraw/new page event, và dependency. **Chưa có executor hoàn chỉnh, ngoài slice**, không dựng chuyển cảnh không được kể chỉ vì hiệu ứng. No fade substitute for drawing. Butterfly flight/poses là optional enhancement trong Golden, không là điều kiện mọi whiteboard story.

## 7. Quality gates và artifact sau implementation approval

1. **Content/cue gate:** owner duyệt exact ba câu, focus-shift phương án, simulated mode và timebudget. No external audio permission inferred.
2. **Source/path gate:** verify original9mask hashes, semantic cue masks/ink candidates, count/travel feasibility. Nếu blocked báo cụ thể, không render thử vô hạn.
3. **One slice render:** local silent14s nominal24FPS, one clean/debug candidate, actual encoded decode full; no full55s or newrig/newdiffusion.
4. **Evidence gate:** contact sheet actual encoded frames tại beat onset/mid/end và0/25/50/75/100%, hàng text/beat/object/phase/camera/actual time; clean/debug paths; timeline JSON, source/phase coverage maps, pen/cue audit, source-fidelity report. Overlay debug tách khỏi clean image.
5. **Owner visual gate:** speech-beat simulated alignment, continuous intelligible main paths, source texture through brush trajectories, no early unmentioned colors/strokes, no block/fade region, no finish snap, old objects preserved, meaningful gardenfocus. Unit tests không là VISUAL_QA_PASS.

Tolerances kỹ thuật dự kiến: onset nằm approved window và sai lệch scheduling ≤1frame tại24FPS; không beat nào lộ source pixels trước authorization; COLOR không chạy trước outline/detail prerequisite; raw completed sourceRGB unchanged tại canonical scale, coverage≥declared completed source mask. Nếu scope partial thì đánh giá trên authorized completed mask, không báo whole-art fidelity. Pen audit path/time/camera transformed positions đồng bộ; deterministic timebudget và resource limits giữ nguyên.

Naturalness phải xem actual MP4 ở24FPS và matching frames; nếu chỉ rải điểm hoặc brush mở mảng, giữ VISUAL_QA_NOT_PASSED và nêu raster/path limitation. Cho phép reviewed local source-bound path correction riêng nếu được duyệt, không geometry replacement người/AI redraw. Chỉ one bounded slice; không automated infinite refinement.

Artifacts dự kiến nằm ngoài Git ở `D:/Codex/Sketch2Life/whiteboard_storytelling_slice_2026-10-09/` (chưa tạo media): silent MP4 clean/debug, timeline/contact sheet, exact-script/cue manifest, persistent checkpoints, stroke/camera audit, final authorized-region frame/difference map và SHA-256 manifest.

## 8. Tests sau duyệt và trạng thái hiện tại

Kế hoạch tests: exact approved text/hash mapping, pending new asset rejection, source ID/mask containment, timeline overlap/bounds, no early color, phase dependency/interleave reason, persistent checkpoints, audio stale hashes/measured vs simulated distinction, camera/pen coordinate agreement, insufficient travel budget and explicit unsupported action. Related V1/world/multi-drawing/draw engine regressions; Ruff/Mypy scoped, whitespace/security, original/mask/code hash checks. Không sửa VisionV3 missing fixtures để báo repoPASS.

Lượt này không chạy pytest mới vì không sửa executable code; 131PASS thuộc prior Motion Proof, **không là bằng chứng slice đã hoạt động**. Chưa có MP4/contactsheet/audio/speech-sync/visual acceptance cho direction này. Planning verification: 327 existing Python files hash unchanged, zero new Python files; source SHA matches, nine mask hashes unchanged; HEAD unchanged/index empty; V2 default false in settings/pipeline. `git diff --check` PASS; repository security PASS (1,671 publishable files scanned); plan links zero broken links. Không external research/inference cần thiết cho đề xuất dùng existing local code.

V1 planner audit bổ sung: `story_video_planner.py` chia visual cues đều trong segment duration (cue_index/len), không phải word/phrase timing được xác minh. Không tái dùng phân bổ đó rồi tuyên bố actual speech alignment; local measured cue annotation/import là đầu vào bắt buộc khi chuyển khỏi simulated mode.

## 9. Các mục xin duyệt trước triển khai

- **W1:** exact script ba câu ở mục3, không lời kể thật của trẻ.
- **W2:** one continuous board14s simulated silent + cue labels; actual audio/TTS chưa dùng.
- **W3:** thứ tự bố→mẹ→bé→nhà→vườn, outline/detail/color theo object, optional purposeful hand-region interleave phải trình rõ.
- **W4:** garden focus thay new butterfly art cho slice; Golden vẫn giữ butterfly approved story content, asset review riêng.
- **W5:** one bounded candidate, chỉ additive opt-in timeline/phase execution; feasibility fail thì báo blocker, không tăng tốc/simplify ngoài duyệt; giữ rig intact/V1default/V2OFF/Gates/production nguyên trạng.

**Dừng tại kế hoạch. AWAITING_OWNER_APPROVAL cho implementation và render slice.** Golden55s chưa render.
