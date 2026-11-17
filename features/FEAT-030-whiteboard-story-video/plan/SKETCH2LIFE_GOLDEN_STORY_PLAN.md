# SKETCH2LIFE — MILESTONE 3A: GOLDEN STORY PLAN

2026-10-09 · FEAT-030 revision 18 · **PLANNING COMPLETE / GOLDEN RENDERING AWAITING_APPROVAL**.

Đây là đề xuất demo 4 cảnh, 55 giây; không phải lời bé đã kể, package được server duyệt, hay báo cáo đã dựng Story Video. Whiteboard hiện vẫn **EXPERIMENTAL / VISUAL_QA_NOT_PASSED**. Không triển khai motion, audio, transition, inference, HTTP V2 hoặc Milestone 3B trong tác vụ này.

## 1. Baseline và dữ liệu được bảo vệ

- Git branch `codex/feat-018-contract-plan`; local HEAD và remote-tracking hiện có cùng `93668ffdaa7f2890fe9498596c670006a87eba4a`. Không fetch, reset, stage, commit, push hoặc deploy. Index trống. Snapshot status và SHA-256 source/test/tool ở [git-and-code-baseline.json](D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/git-and-code-baseline.json).
- Có sẵn 16 tracked files modified, cùng tests/report/pilot/hand drafts untracked. Ba file V1 đã sửa từ trước, bốn hand drafts chưa duyệt và toàn bộ artifact cũ được giữ nguyên. Không giả định mọi dirty file là của nhiệm vụ này.
- `family1.jpg` trong yêu cầu là alias đã được xác nhận cho **original `familly.jpg`**, không phải ảnh AI. JPEG RGB 594×336, SHA-256 `52caf90a2242d04fc107afa1f17b8de738c5f8982200fc504fe725a5607ee3d3`. Đường dẫn cá nhân chỉ nằm trong private manifest, không đưa ảnh trẻ vào repository.
- [Manifest chín mask gốc](D:/Codex/Sketch2Life/real_family_benchmark_2026-10-09/source-object-manifest.json), SHA-256 `693647da0cc2cf2b2cb7261ba4c49451a75db7ed27b292e676fee81550ba0b14`. Đã kiểm tra lại hash cả chín mask và world cutouts, partition không chồng/gap, RGB trong mask khớp decoded JPEG tuyệt đối. Không sửa source/mask/asset.
- [World tham chiếu](D:/Codex/Sketch2Life/real_schedule_debug_2026-10-09/benchmark-world.json) chỉ được dùng để giữ identity, source provenance và initial states. **Không kế thừa event/approval fixture benchmark để cấp phép câu chuyện mới.** Manifest cũ có trạng thái review lịch sử; consent bổ sung trong chat chỉ là provisional static benchmark, không sửa lịch sử thành server-approved.

### Baseline renderer được chọn

**Revision 15 visual/object-first** là baseline hình ảnh có phản hồi người dùng tốt nhất về thứ tự dựng tranh và xuất hiện màu, không phải phiên bản đã PASS. Bản pencil sau đó bị người dùng từ chối; revision 17 sửa an toàn schedule nhưng chưa chứng minh naturalness tốt hơn revision 15.

- [MP4 revision 15](D:/Codex/Sketch2Life/real_visual_refinement_2026-10-09/real-family-v2-static.mp4), SHA-256 `8e6a167a132f5e45119faa7b1d4fb3bd3027642a519b761fe48586520e68d16f`.
- Extraction `strategy="visual"`, method `MASK_BOUNDARY_AND_COHERENT_TEXTURE_V4`; scheduler `object_first=True`, không pencil timing/seed preview. Outline → detail → color cho từng object. Bản đã render là **20 giây**, chưa có bằng chứng giữ chất lượng khi rút xuống 18 giây.
- Snapshot revision-15 renderer/schedule/extractor và SHA-256 trong [baseline-lock.json](D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/baseline-lock.json). Đây là version lock bằng artifact/source snapshots của dirty worktree, không phải một Git commit riêng.
- Giữ safety revision 17: reject unscheduled preview, validate phase/path coverage/overlap và shared clock cho cursor/reveal. **Không rollback source về snapshot revision 15**; sau approval chỉ dùng lại visual strategy với safeguards hiện tại và kiểm thử tương thích.
- [MP4 revision 17](D:/Codex/Sketch2Life/real_schedule_debug_2026-10-09/real-family-v2-static.mp4) là reference an toàn, SHA-256 `7ef31b9d524c0a565f8200b87a2642531b3a06f3e18338d416cb661cba5ccbee`. Cả hai vẫn VISUAL_QA_NOT_PASSED. Không có MP4 Golden mới trong tác vụ này.

## 2. Storyboard bốn cảnh và timeline 55 giây

**18 + 14 + 13 + 10 = 55 giây**; đáp ứng 3–6 cảnh, mỗi cảnh 5–20 giây, tổng 40–60. Transition/camera nằm bên trong các khoảng này; không cộng thêm giây ở đường nối. Timing hiện là ESTIMATE, chưa đo narration/TTS.

| Cảnh | Timeline | Story beat đề xuất | Blocking/hình ảnh cần duyệt | Kết thúc và continuity |
| --- | --- | --- | --- | --- |
| 1 | 0–18 s | Giới thiệu gia đình, nhà, cây và vườn | Dựng tranh bằng V2 visual/object-first; ưu tiên mẹ → bố → bé, rồi nhà/cây/vườn/nền. Outline/detail/color đúng object, không nét màu ngoài lượt. Không vẽ lại toàn tranh ở cảnh sau. | Giữ composition nguồn hoàn thiện. Điểm chốt: 18s có đủ cho chất lượng chấp nhận được không? Nếu không, xin đổi phân bổ trong 55s, không âm thầm time-compress. |
| 2 | 18–32 s | Gia đình đi dạo trước nhà | Yêu cầu đúng nghĩa: walk poses. Phương án nhỏ hơn: nhóm mẹ-bố-bé dịch chuyển 2D nhẹ cùng nhau, tay liên kết; **không gọi là walk cycle**. Camera theo nhóm sau khi motion được triển khai. | Endpoint nhóm là starting state cảnh 3; nền lộ ra phải có asset được duyệt. |
| 3 | 32–45 s | Bé đến vườn hoa và thấy bướm được vẽ thêm | Cần pose bé buông tay, silhouette/occlusion review. Bé tới vườn bằng chuyển động 2D cách điệu nếu người dùng đồng ý; sau đó vẽ riêng asset bướm. Không tái sinh nhân vật/cảnh. | Bướm xuất hiện có event riêng, không có từ đầu; bố/mẹ giữ cùng identity/state. |
| 4 | 45–55 s | Bé trở về với bố mẹ, toàn cảnh kết thúc | Bé trở về đúng vị trí và pose gốc; camera zoom-out nhẹ về full source composition. Giữ kết 1–2s theo audio thực. | Source layer trở về initial states; bướm là lớp mới có provenance riêng, chỉ giữ nếu người dùng duyệt. |

Camera keyframes đề xuất: full `(0.5,0.5,1.0)` → family focus `(0.45,0.59,1.12)` → garden `(0.68,0.64,1.3)` → full `(0.5,0.5,1.0)`. Tọa độ normalized, còn phải kiểm tra crop không cắt chân/tay hoặc mất nội dung khi asset chuyển vị trí. Static crop không đồng nghĩa camera đã animate.

[Storyboard preview 4 cảnh](D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/storyboard-4-scenes.png) là **annotated source / camera-framing proposal**, không phải frame của motion renderer. Cảnh 2/4 vẫn giữ pose nguồn và chú thích hướng chuyển động; cảnh 3 là crop để xem vườn, có nhãn placeholder bướm, chưa dựng bé tới vườn. Preview không kiểm chứng pose mới, background reconstruction, temporal motion hay style bướm.

### StoryScriptSegments nháp để người dùng chỉnh

1. `segment-1` / INTRO: “Đây là bức tranh gia đình của em. Có bố, mẹ và em trước ngôi nhà, bên cây xanh và vườn hoa.”
2. `segment-2` / DEMONSTRATE: “Cả nhà cùng đi dạo trước nhà. Em ở giữa bố và mẹ, cùng ngắm cảnh quanh sân.”
3. `segment-3` / EXPLAIN: “Em đến gần vườn hoa và nhìn thấy một con bướm. Em dừng lại để ngắm bướm bên những bông hoa.”
4. `segment-4` / RECAP: “Sau đó em trở lại với bố mẹ. Cả nhà lại ở bên nhau trước ngôi nhà.”

Đây là lời demo đề xuất, **không trích lời bé** và không mặc định bé đã kể về bướm. Người dùng cần duyệt/chỉnh cả nội dung lẫn cách thể hiện chuyển động. Nhận dạng mẹ/bố/bé theo manifest benchmark, không suy thêm quan hệ/story facts ngoài review.

## 3. Draft contracts và approval boundary

- [Scene Plan JSON](D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/scene-plan.draft.json): `GoldenStoryPlanningProposal`, không phải executable `StoryScenePlanV2`. Có scene/event/segment IDs, timeline, requested actions, giản lược cần approval, starting/target source states và camera proposal.
- [StoryScriptSegments JSON](D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/story-script-segments.draft.json): draft review contract; tất cả `NEEDS_APPROVAL`, `approved_fact_ids=[]`, `confirmed_anchor_ids=[]`, không review record giả.
- `event-golden-demo-scene-1..4` có stable IDs, exact source_quote và mapping `EXPLICIT_USER_DEMO_PROPOSAL`, truy về từng đoạn. **Chưa truy về facts/anchors approved** vì chưa có Gate A/B thật. `review_ref=null`, `server_approval_record_id=null`.
- Production `StoryScriptSegmentV1` bắt buộc facts/anchors approved không rỗng; `ReviewedEventV2` cũng cần binding reviewed quote. Vì vậy **không instantiate approved contracts bằng fake fixture IDs** chỉ để draft validate. Tất cả preview chỉ planning, không đi qua `run_v2_prototype` hoặc HTTP job.
- Sau content approval, offline demo phải mang label local/demo review và hash source/script/mask/assets; vẫn không đồng nghĩa production authorization. Production sau này phải fetch server record bind immutable session version/package/script/source/mask/event hashes qua `ServerApprovalVerificationPort`, không tin caller review_ref. Interface này hiện chưa có trusted adapter.
- Draft source state endpoints liên tục qua bốn cảnh đã kiểm tra bằng JSON equality. Đây chỉ là **continuity của đề xuất**, không chứng minh video/pose continuity; new asset còn pending, không tạo WorldModel approved chứa bướm.
- Bản ba cảnh/52s [trước đó](SKETCH2LIFE_GOLDEN_STORY_VIDEO_PLAN.md) được giữ nguyên như lịch sử, **superseded** bởi đề xuất bốn cảnh này.

## 4. Asset requirements và provenance

Chi tiết hash/refs: [asset-requirements.json](D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/asset-requirements.json).

| Asset | Hiện có | Yêu cầu trước story rendering |
| --- | --- | --- |
| `family-52caf90a-mother/father/child` | Source masks/cutouts, stable IDs, pixel nguyên bản | Chỉ provisional static; review shared hands, túi, chân/giày, z-order, mask/identity cho motion. Không sửa chín mask gốc, tạo derived motion version nếu cần. |
| `family-52caf90a-house/tree/garden/sky/path/remaining-background` | Sáu source regions, partition ảnh | Garden là vùng gồm nhiều hoa, không phải từng flower asset; tree gồm cành nguồn. Static dùng được; không khẳng định automatic object splitting. |
| Family group composite | Có thể tạo từ source cutouts, chưa có motion adapter | Giữ provenance từng thành viên và quan hệ tay; không hợp nhất ID rồi mất traceability. Dịch chuyển cả group chỉ là 2D cutout motion. |
| Bé buông tay/pose đi riêng | **Chưa có** | Pose/motion masks mới cần review; không lấy pose đang nắm hai tay rồi trượt ngang và gọi tự nhiên. Phần vẽ mới có provenance DERIVED_POSE, không giả source pixels. |
| Nền bị người che khuất | **Chưa có** | Original không chứa hidden pixels. White/median placeholder hiện tại không đủ. Cần manual offline background patch được review, hoặc đổi action/blocking để không lộ. Patch là DERIVED_NEW_PIXELS, không claim preserved source. |
| `golden-demo-butterfly-1` | **Chưa có** | Bướm nhỏ bằng chì màu kiểu trẻ em; dùng owner-supplied hoặc manual offline art sau approval; AI chỉ tùy chọn được duyệt riêng. Hash candidate, outline/color mask/paths và visual approval riêng. |
| Voice/audio/subtitles | Có code V1, chưa có file audio cho demo | Văn bản/voice được duyệt, record hoặc TTS thực rồi đo timing; không voice clone, không music/SFX chưa có license. |

Giữ master source asset/hash nguyên trạng; scale/rotate camera resampling không được gọi là exact source-pixel identity ở frame biến đổi. Final full-view source layer phải khớp nguồn ở pose gốc; butterfly/derived patch kiểm tra riêng. Không so sánh whole frame có bướm với original rồi yêu cầu MAE=0 hoặc báo source sai vì thêm đồ được duyệt.

## 5. Capability audit — code thực tế

`IMPLEMENTED` dưới đây nghĩa có code chạy tại layer được chỉ rõ, **không đồng nghĩa production/GPU/Golden runtime acceptance**.

| Khả năng | Phân loại | Bằng chứng và giới hạn |
| --- | --- | --- |
| Static source-object whiteboard PNG/MP4 | IMPLEMENTED, experimental | [object_stroke_engine_v2.py](../../../backend/src/sketch2life/infrastructure/media/object_stroke_engine_v2.py), [whiteboard_renderer_v2.py](../../../backend/src/sketch2life/infrastructure/media/whiteboard_renderer_v2.py). Real silent MP4 đã có. Outline/detail/color raster reconstruction chưa naturalness PASS. |
| Masked source assets / stable IDs | IMPLEMENTED local | [story_world_model.py](../../../backend/src/sketch2life/application/services/story_world_model.py). In-memory registry + private fixture files, chưa durable storage/upload readiness. |
| STATIC/TRANSLATE/SCALE/ROTATE target still | IMPLEMENTED **target-state still only** | [SceneStateComposer](../../../backend/src/sketch2life/infrastructure/media/scene_state_composer.py) nhận action này nhưng render target state. V2 MP4 `_frame` đọc cùng `scene.target_states` cho mọi frame, không tween từ starting states. |
| Motion interpolation/2D puppet/group movement | REQUIRES_IMPLEMENTATION | `SceneMotionTransitionPort` chỉ Protocol. Chưa có time-varying object state executor trong pilot. |
| Walking/running pose/cycle | UNSUPPORTED current engine | WALK/RUN có enum mô tả ý định, không có rig/pose generator. Composer/pilot trả UNSUPPORTED_ACTION. Translation không tương đương walking. Nếu bắt buộc tự nhiên cần task khác có rig/pose review, không tối thiểu hóa bằng fake claim. |
| Source character reuse qua cảnh | IMPLEMENTED dữ liệu/stills; motion readiness cần implementation/review | Source identity/state continuity contracts có; split hands, new pose, occlusion repair chưa có. |
| Bướm mới đúng phong cách + reveal | REQUIRES_IMPLEMENTATION + asset approval | `ApprovedNewAssetGenerationPort` chỉ interface. Composer/pilot từ chối `new_object_ids`; không thể chỉ append butterfly rồi báo engine hiện tại đã hỗ trợ. Cần riêng reviewed-new-asset layer/reveal, giữ source strokes không đổi. |
| Camera crop/zoom một trạng thái | IMPLEMENTED static | `_camera` và SceneStateComposer crop theo camera target. Planner PAN chỉ đặt center, ZOOM đặt giá trị, không animate theo thời gian. |
| Camera pan/zoom-out theo thời gian | REQUIRES_IMPLEMENTATION | Cần interpolate camera keyframes, giới hạn crop và endpoint continuity; không sinh lại scene. |
| Scene CUT / concat MP4 | IMPLEMENTED V1 assembly | `story_video_assembly` trong [lightning_whiteboard_provider.py](../../../tools/lightning_whiteboard_provider.py), FFmpeg concat demuxer. CUT ở mức ghép file đã có; `transition_intent` của V2 chỉ metadata, không có executor liên cảnh. |
| CONTINUE matched-state cut | REQUIRES_IMPLEMENTATION V2 handoff | Reuse concat sau khi uniform fps/size/timebase và endpoint checks; không redraw/restart characters. |
| Dissolve/crossfade/wipe/story transitions | REQUIRES_IMPLEMENTATION | Không thấy FFmpeg xfade/transition engine trong V2/V1 assembly hiện tại. Minimal Golden chọn matched cut; không gọi fade toàn ảnh là quá trình vẽ. |
| TTS / measured segment timings | IMPLEMENTED V1 provider, Golden reuse cần adapter | Provider có `edge-tts` voice default `vi-VN-HoaiMyNeural`, optional ElevenLabs model default `eleven_flash_v2_5`. TTS gọi ngoài máy; chưa chạy cho draft và cần approval. [WhiteboardTtsAdapter](../../../backend/src/sketch2life/infrastructure/media/whiteboard_tts_adapter.py) provider-neutral không tự chọn/huấn luyện voice. |
| Subtitle text chunking, timing, UTF-8 SRT | IMPLEMENTED V1 | `_subtitle_cues` trong [story_video_pipeline.py](../../../backend/src/sketch2life/application/services/story_video_pipeline.py), `_subtitle_srt` và libass burn-in ở provider. Cues theo measured segment, chưa hỗ trợ slot có silence/holds và motion timeline theo cách Golden cần. |
| H.264 + AAC final assembly/hash checks | IMPLEMENTED V1; V2 integration required | FFmpeg concat + narration, source/scene/audio SHA checks, `-shortest`, stream/duration checks. Không phải audio-capable V2 renderer. Chú ý `-shortest` có thể cắt 55s nếu audio ngắn; explicit padding/timeline cần thiết. |
| WAN video generation adapter | IMPLEMENTED V1 integration path, không là capability V2 | Provider gọi external Wan `generate.py --task ti2v-5B` bằng image/prompt và checkpoints cấu hình. Pipeline default `whiteboard-stroke-v1`, không phải WAN. Chưa kiểm chứng Wan cho Golden này; không chạy hoặc chọn Wan làm phương án tối thiểu bảo toàn source pixels. |
| Live Gate A/B V2, upload/Lightning final acceptance | UNSUPPORTED current V2 integration | Default OFF, prototype only, approval verification port không có server adapter. Không mở HTTP V2 hoặc tuyên bố Lightning PASS. |

## 6. Hybrid animation đề xuất — không mở rộng architecture

**Một canvas/source registry chung**, không diffusion độc lập mỗi cảnh. Whiteboard V2 dựng source một lần ở cảnh 1; giữ final source/state rồi dùng layers này cho cảnh 2–4. Audio theo approved script, cuối cùng ghép FFmpeg.

1. **Stroke renderer:** giữ visual/object-first và safeguards. Chưa sửa extraction nữa trong 3A. Sau approval cần sample 18s; nếu không đạt nhịp, xin duyệt đổi scene allocation trong 55s hoặc style có semantic/manual paths riêng. Không tự vẽ chọn lọc rồi fade/snap toàn ảnh để báo hoàn thành.
2. **Stable assets:** dùng cùng source bytes/IDs/masks qua cảnh; assets derived cho release pose/occluded pixels version riêng. Hash freeze đầu vào, never replace originals. Local disk session manifest đủ cho demo offline, không giả durable production registry.
3. **2D object motion:** chọn phiên bản nhỏ nhất **cutout/puppet cách điệu**, nếu người dùng chấp nhận. Cảnh 2 move group nhẹ giữ nắm tay; cảnh 3 cần riêng pose buông tay trước khi move child; cảnh 4 reverse path/return original pose. Giữ head/face/hair/glasses/clothes source texture. Không leg-cycle giả bằng bobbing, không ellipse/rectangle thay người.
4. **New-asset reveal:** chỉ bướm đã duyệt được thêm bằng layer riêng. Manual outline paths + source-colored asset brush nếu art supplied; không reuse source-only engine để bypass unsupported action. Optional nhẹ rotate/flap 2D nếu review style, không cần natural butterfly physics.
5. **Camera/transition:** camera interpolation cùng clock với object motion. Chọn matched-state CUT, không xfade ở scope tối thiểu. Đầu cảnh sau bằng endpoint cảnh trước, không nhân vật bật về vị trí cũ. Camera return 1.0 và original family pose ở kết.
6. **Audio timeline/assembly:** narration track theo measured speech windows, hold/silence explicit; captions không kéo trên silent holds. Normalize dimensions/FPS/codec, concat/mux narration + SRT; verify exactly 55s within frame/encoder tolerance.

Nếu chưa có approved release pose và hidden background: **BLOCK cảnh 3 travel**, không trả một video camera-only rồi tuyên bố đã thực hiện hành động. Camera-only observational story là phương án đổi nội dung cần người dùng duyệt riêng, không fallback âm thầm.

## 7. Audio/Narration Plan

[audio-narration-plan.json](D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/audio-narration-plan.json).

- Người dùng chọn giữ draft trên hoặc thay lời kể thật, duyệt trước render. Không lấy thời lượng slot 18/14/13/10 làm duration TTS đã đo.
- Ưu tiên recording được cho phép sử dụng, offline decode/measure; có thể dùng local synthesizer đã có, nhưng voice/runtime chất lượng tiếng Việt chưa được xác minh. TTS V1 Edge là lựa chọn external, cần chấp thuận text transmission/voice/service; không gọi trong 3A.
- Đo từng đoạn, fit narration window cùng drawing/action holds. Nếu quá dài: trả DURATION_OUT_OF_RANGE/SCENE_PARTITION_IMPOSSIBLE kèm đoạn và số giây, xin sửa script/timing; không tự tăng speed, loop voice, truncate lời hay đổi câu.
- Reuse `_caption_chunks`/SRT serialize nhưng thêm adapter cho gaps. Hiện `_subtitle_cues` và planner ràng buộc tổng measured narration bằng scene duration; không trực tiếp dùng pipeline V1 nguyên xi cho story có thời gian hành động không thoại.
- Audio timeline cần ghi silence/start/end rõ, tạo total track 55s. Existing assembly `-shortest` chỉ dùng khi total audio/video xác minh bằng nhau. End subtitle không nhất thiết bằng end video nếu hold cuối; adapt duration check để check timeline đúng, không bỏ validation.
- Không music/SFX ở scope tối thiểu; thêm sau chỉ khi có license và approval. Không clone voice.

## 8. AI steps và chi phí

Không cần GPU/diffusion để lập storyboard, hash/mask checks, source cutouts, paths hiện có, 2D motion, camera, FFmpeg hoặc audio file của người dùng. **3A thực tế: 0 model/API calls, 0 audio syntheses, 0 video renders.** Local CPU/disk không đồng nghĩa chi phí điện/máy bằng 0.

| Bước tương lai | Phương án nhỏ nhất | AI/API và trạng thái phí |
| --- | --- | --- |
| Butterfly | Owner-supplied hoặc manual offline art được review | Không inference; chưa tạo art. Nếu chọn AI: provider/model chưa chọn, token/GPU/API quote **TBD**, cần duyệt trước gọi. |
| Child release pose / background patch | Manual derived assets, review cùng source | Có thể offline. Nếu dùng AI/inpainting: không được thay source, cần riêng task/permission, quote chưa xác minh. |
| Character animation | Source-layer 2D puppet, limited motion | Không model; cần implementation/review và asset mới cho release pose. Natural walk ngoài khả năng engine hiện tại. |
| Narration | Recording, hoặc approved external TTS | Code có Edge và ElevenLabs; không khẳng định phí bằng 0 hoặc mức USD khi chưa xác minh provider terms/account. Quota/pricing/network/runtime **TBD**. |
| Whole-scene SDXL / WAN | **Không chọn cho minimum Golden** | Provider có configurable `AutoPipelineForImage2Image`; ảnh SDXL cấu hình cũ không chứng minh model runtime hiện tại. WAN là optional V1 external adapter, không chứng minh source preservation. Không chạy, không báo phí hay fidelity chưa đo. |
| Lightning | Optional acceptance sau offline demo | Chưa chọn machine/session time, không quote tiền ước đoán. Không cần bật GPU để review plan; runtime acceptance phải test riêng sau approval. |

Không có quyết định mua dịch vụ/model nên không tra/gán bảng giá giả. Nếu người dùng chọn AI/TTS trả phí, bước đầu tiên trước inference là xác minh giá official và đưa budget/consent để duyệt.

## 9. Blockers và smallest implementation plan sau approval

**Không bước nào dưới đây đã triển khai trong 3A.** Không cần mở upload/BE, queue, HTTP V2 hay đổi domain/Gates để có một private demo. Chỉ một offline runner dùng artifact manifests và local review, luôn ghi không server-approved.

| Thứ tự | Phần tái sử dụng / thay đổi nhỏ dự kiến | Exit/acceptance |
| --- | --- | --- |
| 0 | Owner review script 4 scenes + 2D simplification + visuals/assets/voice/budget | Content/style approved local; nguồn duyệt ghi rõ, không server Gate stamp. Chưa đủ thì dừng. |
| 1 | Asset preparation, không sửa original nine masks | Child release/hands/motion/occlusion assets và butterfly có review/hash; thiếu thì block đúng scene. Freeze master source/world identity. |
| 2 | Source drawing sample 18s bằng visual strategy/safeguards | Người dùng xem nhịp thật; không early color/major pop, end source exact raw; naturalness status vẫn honest. Không đạt thì chỉ xin điều chỉnh style/timeline, không vòng tuning vô hạn. |
| 3 | Offline per-frame motion adapter, source-layer reuse, camera interpolation | Scene 2–4 time-varying motion thật; same IDs; no source redraw; hand-release/occlusion validated. Cutout motion ghi đúng tên, không gọi natural walking. |
| 4 | Reviewed butterfly layer/semantic path reveal | Event chỉ thực thi sau local review; bướm xuất hiện đúng cảnh, palette/style duyệt; renderer unsupported trước khi adapter có. |
| 5 | Audio timeline adapter + existing subtitle/FFmpeg utilities | Measured audio/captions fit slots/holds; không reuse V1 independent-scene generation; no audio loop/cutoff, normalize streams. |
| 6 | Một bounded four-scene render và final mux | Một MP4 55s + per-scene MP4, state/asset/audio manifests, comparison/contact sheets, decoded/fidelity/timing evidence. Retry chỉ đoạn lỗi có log, không gen lại cả story. |
| 7 | Owner full video review rồi runtime test riêng nếu yêu cầu | VISUAL_QA_PASS chỉ sau review thực đạt; Lightning Level 2 chỉ sau chạy thật. Không auto deploy/BE integration. |

### Golden MP4 acceptance criteria

- Bốn scenes đúng story đã duyệt, duration 55s (tolerance tối đa một frame cho raw schedule, encoder/audio rounding báo riêng; final mux không vượt 0.1s). Mọi scene 5–20s, không cộng transition ngoài 55s.
- Ít nhất có **time-varying object action**, không chỉ pan/crop trên static picture; cutout/puppet scope được duyệt rõ. Nếu yêu cầu natural walking không đạt, báo UNSUPPORTED_ACTION/task khác, không claim hoàn thành.
- Bé thực sự tách khỏi bố mẹ bằng pose hợp lệ, tới vườn rồi quay lại; không đứt tay vô cớ, mất kính/áo/giày, đổi danh tính, nền trắng lộ ra hoặc người bị duplicate.
- Scene 1 end nguyên bản decoded source ở native resolution, raw source layer MAE 0; source asset hashes unchanged throughout. Source/new/derived pixels phân biệt trong fidelity report; codec/resampling error báo riêng, không giấu bằng metric chung.
- Bướm chỉ thêm sau approval/event đúng narration; source identities/style/colors không thay đổi, no independent scene regeneration. Camera framing giữ nội dung quan trọng; matched-cut endpoints không jump state.
- Audio đọc đúng script, captions theo measured speech, không loop/cắt câu; final video có H.264/AAC streams valid, decode toàn bộ được, duration/audio sync kiểm tra bằng artifact.
- Người dùng xem **MP4 thực** và duyệt story/motion/nét/tô/chuyển cảnh/voice. Unit tests/fidelity không thay Visual QA. Nếu vẫn không tự nhiên, giữ VISUAL_QA_NOT_PASSED và nêu giới hạn, không tự tăng cấp vì story có thêm motion.

## 10. Bàn giao và verification

Private directory: `D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/`. Chứa draft JSON, bốn preview, contact sheet, baseline/hash/status snapshot, validation và script tái tạo. Private preview chứa ảnh được cho phép local: **không copy vào Git**.

- [Scene 1](D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/scene-1-preview.png), [Scene 2](D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/scene-2-preview.png), [Scene 3](D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/scene-3-preview.png), [Scene 4](D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/scene-4-preview.png).
- [Planning validation](D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/planning-validation.json): source/nine masks/cutout RGB verified; 4 scenes/55s/duration bounds/declared endpoint continuity pass, all events NEEDS_APPROVAL. Không production contract, motion/new-asset/audio/video execution test.
- Actual selected regression: `backend/.venv/Scripts/python.exe -m pytest -o addopts= -q backend/tests/unit/test_story_world_v2.py backend/tests/unit/test_story_video_planner.py backend/tests/contract/test_story_video_file_api.py` → **40 passed in 53.59s, exit 0**, không fail/skip trong selection. Bao gồm V2 flag OFF/no silent V1 replacement, planner V1 và file API contracts; không toàn bộ repository.
- Final checks/log/status: [handoff-final-verification.json](D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/handoff-final-verification.json). Security, whitespace, source/test/tool hash comparison, link existence và Ruff hai private preparation/verification scripts được chạy; không sửa application code. Mypy không chạy lại vì không đổi production Python/contracts; các suite khác/Vision V3/GPU/Lightning/motion/audio/full video không chạy.
- Preparation từng ngắt vì draft audio slot dùng singular `segment_id` thay `segment_ids[0]`; sửa **private planning script** rồi resume, giữ JSON đã tạo nếu nội dung giống. Ruff đầu tiên phát hiện bốn lỗi style/import/pairwise/check-argument ở private scripts, sửa rồi chạy lại; log fail ban đầu được giữ. Không có renderer bug fix hoặc source replacement trong 3A. Các checks chỉ phục vụ handoff planning, không hợp thức hóa Visual QA hoặc toàn repository PASS.
- User review cần quyết định: (1) nội dung/demo narration; (2) chấp nhận 2D cutout/puppet hay bắt buộc walk cycle; (3) pose/background/butterfly artwork; (4) recording hoặc TTS + external data/cost permission; (5) mức whiteboard scene-1 quality/time. **Dừng sau kế hoạch, chờ duyệt trước Golden Story Rendering.**
