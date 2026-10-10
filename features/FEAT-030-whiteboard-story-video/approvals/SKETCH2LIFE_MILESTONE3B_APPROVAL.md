# SKETCH2LIFE — FINAL STORY & MOTION APPROVAL PACKAGE

**Milestone 3B · 2026-10-09 · package proposal v1 · AWAITING_OWNER_APPROVAL**

Mục tiêu đề xuất: một Golden Story demo **55 giây, 4 cảnh**, từ tranh gia đình gốc. Tài liệu này để duyệt trước triển khai; không phải quyết định đã duyệt, báo cáo đã tạo animation, hoặc authorization của server. Trong lượt này chỉ đọc/kiểm tra và viết tài liệu: **không viết application code, tạo rig/pose/ảnh/audio hoặc render MP4**.

## 1. Kết luận và phương án đề nghị duyệt

Đề nghị **Hybrid 2D có hỗ trợ thủ công**: Whiteboard Engine V2 vẽ nguồn ở cảnh 1; source-derived rigs/key poses làm chuyển động giới hạn ở cảnh 2–4; bướm mới do người dùng cung cấp hoặc vẽ thủ công được duyệt; camera chung, narration demo và FFmpeg assembly.

Điểm khác quan trọng so với 3A: **không dùng trượt nguyên hình làm minh chứng animation**. Nhân vật phải đổi tư thế tay/chân bằng rigs/pose assets được review; walk cycle cách điệu cần contact/lift/swing/plant thật. Không hứa chuyển động như phim hoạt hình chuyên nghiệp từ chín mask tĩnh.

Engine hiện tại **chưa có** walk cycle, rig, hand-release pose, time-varying object/camera executor hoặc reviewed-new-asset reveal. Các phần này cần chuẩn bị/triển khai sau approval. AI/GPU không bắt buộc cho phương án ưu tiên. Nếu manual assets không đạt nhận diện/phong cách, phải báo blocker; không tự chuyển sang diffusion hoặc nâng Animation PASS.

### Baseline không thay đổi

Git branch `codex/feat-018-contract-plan`, HEAD `93668ffdaa7f2890fe9498596c670006a87eba4a`, index trống. Existing dirty worktree được giữ nguyên. Đã đối chiếu toàn bộ Python source/test/tool trong snapshot 3A: **không đổi**. V1 mặc định, V2 OFF; không thay Gate A/B hoặc mở HTTP/upload V2.

Source được xác nhận: `family1.jpg` là alias của original `familly.jpg`, JPEG RGB **594×336**; SHA-256 `52caf90a2242d04fc107afa1f17b8de738c5f8982200fc504fe725a5607ee3d3`. Kiểm tra lại source, chín mask và chín world cutouts: hashes khớp artifact 3A. Không dùng ảnh thay thế; không đưa ảnh/derived child assets vào Git.

Baseline hình ảnh vẫn revision 15 `visual/object_first`, giữ schedule safeguards revision 17. Bản đã render là 20s; chất lượng khi dựng nguồn trong slot 18s **chưa kiểm chứng**. **EXPERIMENTAL / VISUAL_QA_NOT_PASSED** không thay đổi.

## 2. Các nguồn đầu vào và trạng thái approval

- [Golden Story Plan 3A](../plan/SKETCH2LIFE_GOLDEN_STORY_PLAN.md).
- [Scene Plan draft](D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/scene-plan.draft.json).
- [Action & Transition draft](D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/action-transition-plan.draft.json).
- [Bốn StoryScriptSegments draft](D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/story-script-segments.draft.json).
- [Source/new asset requirements](D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/asset-requirements.json).
- [Manifest chín mask](D:/Codex/Sketch2Life/real_family_benchmark_2026-10-09/source-object-manifest.json), SHA-256 `693647da0cc2cf2b2cb7261ba4c49451a75db7ed27b292e676fee81550ba0b14`.
- [World benchmark](D:/Codex/Sketch2Life/real_schedule_debug_2026-10-09/benchmark-world.json): chỉ tái dùng source identity/initial states, **không kế thừa fixture events như approval thật**.
- [Storyboard 3A](D:/Codex/Sketch2Life/golden_story_3a_review_2026-10-09/storyboard-4-scenes.png) chỉ là framing/annotation. Chưa cho thấy pose buông tay, walk cycle hoặc bướm đã được tạo.

| Nội dung | Trạng thái thực tế |
| --- | --- |
| Sử dụng original và chín mask cho static benchmark local | Đã có PROVISIONAL BENCHMARK APPROVAL; không là motion/product approval |
| Demo gia đình đi dạo, bé tới vườn, bướm xuất hiện, bé trở lại | Người dùng đề xuất story beat; **chưa Final Story Approval** |
| Script, rigs/poses, bướm bay/đập cánh, TTS/external processing | **NEEDS_APPROVAL**, chưa được chạy/tạo |
| Nội dung đã được Gate A/B production duyệt cho Golden này | **Chưa có bản ghi server được xác minh** |
| Naturalness, animation acceptance, Golden/Lightning runtime PASS | **Chưa đạt/chưa test** |

Các event vẫn phải liên kết segment/quote và facts/anchors sau review. Hiện approved_fact_ids/confirmed_anchor_ids để trống, review_ref/server record null. Không tạo approved DTO bằng ID giả. Approval của người dùng trong chat cho local demo sau này phải được ghi đúng loại, không gọi server-approved; production vẫn cần trusted immutable approval binding.

## 3. Storyboard và kịch bản 55 giây để duyệt

Timeline giữ **18 + 14 + 13 + 10 = 55s**; bốn cảnh 5–20s, tổng trong 40–60s. Đây là video script gồm thoại, action và khoảng nghỉ; **không khẳng định riêng phần TTS dài đúng 55s** trước khi đo audio.

### Cảnh 1 — Tranh gia đình: 0–18s

**Hình:** whiteboard vẽ/tô mẹ, bố, bé rồi ngôi nhà, cây, vườn và nền; outline → detail → color đúng lượt từng object. Kết thúc bằng artwork nguồn hoàn chỉnh, không snap/fade toàn ảnh để che phần chưa vẽ. Ưu tiên giữ nhịp đã được đánh giá tốt; không tiếp tục threshold tuning vô hạn.

**Lời kể đề nghị giữ nguyên segment-1:**

> Đây là bức tranh gia đình của em. Có bố, mẹ và em trước ngôi nhà, bên cây xanh và vườn hoa.

**Nhịp nháp:** 0–16.5s dựng nguồn; 16.5–18s giữ hình. Cửa sổ thoại dự kiến 2–11s, phần còn lại nghe im lặng/xem tranh. Nhịp cụ thể phải đo/review; nếu renderer không đạt trong 18s, báo blocker hoặc xin đổi phân bổ trong 55s, không tự nén tốc độ.

**Bổ sung:** không thêm object mới; quá trình vẽ là presentation, không phải fact mới về câu chuyện.

### Cảnh 2 — Gia đình đi dạo: 18–32s

**Hình:** cả ba đi vài bước ngắn trước nhà bằng **limited 2D walk**, tay vẫn liên kết. Chân phải đổi trạng thái chạm đất/nhấc chân/đưa chân, không chỉ đổi tọa độ cả silhouette. Camera nhẹ theo nhóm; nhà/cây/nền không bị tái sinh.

**Lời kể đề nghị, chỉnh nhẹ segment-2:**

> Bố, mẹ và em cùng đi dạo trước nhà. Em nắm tay bố mẹ, vừa đi vừa ngắm cây xanh và những bông hoa.

**Nhịp nháp:** 18–19s camera vào family framing; 19–30s vài bước giới hạn và nghỉ tự nhiên; 30–32s giữ endpoint. Thoại dự kiến 19–28s, đo lại trước chốt. Không bắt walk loop liên tục 11s chỉ để lấp slot.

**Bổ sung cần duyệt:** động tác bước chân, nắm tay khi đi, camera follow và phần nền vừa được lộ ra. Tranh tĩnh không chứng minh các sự kiện này đã xảy ra.

### Cảnh 3 — Buông tay, tới vườn, bướm: 32–45s

**Hình:** bé buông tay; bố mẹ dừng lại. Bé đi vài bước tới vườn bằng reviewed child rig/poses. Sau khi bé dừng, whiteboard vẽ riêng bướm, sau đó bướm đập cánh/bay nhẹ phía trên hoa. Camera chuyển hướng vườn; không xóa/mất bố mẹ hoặc thay nhân vật.

**Lời kể đề nghị, revision mới của segment-3:**

> Em buông tay bố mẹ và đi tới vườn hoa. Một con bướm nhỏ hiện ra, đập cánh bay nhẹ trên những bông hoa. Em dừng lại ngắm bướm.

**Nhịp nháp:** 32–33s hand release; 33–37s child travel + camera; 37–40s vẽ bướm; 40–43s butterfly flap/flight; 43–45s quan sát/hold. Chỉnh so với 3A: dành riêng thời gian cho bướm bay thay vì chỉ vẽ/hold đến 45s. Lời phải chia theo các beat sau khi đo audio, không nói bướm đang bay trước khi hình bướm có mặt.

**Bổ sung cần duyệt:** buông tay, independent walk pose, bướm là **object mới**, kiểu/tông màu/chuyển động của bướm. Không coi bướm là source object đã có trong tranh. Garden vẫn là source region; không giả từng bông hoa đã có mask riêng.

### Cảnh 4 — Trở về và toàn cảnh: 45–55s

**Hình:** bé quay lại bố mẹ bằng pose/cycle hợp lệ; bố mẹ trở về vị trí nguồn nếu cảnh 2 đã di chuyển. Cả ba kết ở original arrangement, tay/giày đúng chỗ. Camera mở về full composition; giữ 53–55s. Bướm có thể còn bay rất nhẹ trên vườn, chỉ nếu người dùng duyệt giữ asset ở đoạn kết.

**Lời kể đề nghị, revision mới của segment-4:**

> Em quay lại với bố mẹ. Cả nhà lại ở bên nhau trước ngôi nhà, còn con bướm vẫn bay nhẹ bên vườn hoa.

**Nhịp nháp:** 45–49s return; 49–53s camera rộng dần; 53–55s end hold. Thoại dự kiến 46–53s; cần đo, không ép audio quá dài vào hold cuối.

**Bổ sung cần duyệt:** bướm còn hiện diện ở kết, bố mẹ trở về original position. Nếu bỏ bướm ở kết, chỉnh lại segment-4 và event state trước review, không để narration/hình mâu thuẫn.

### Script/plan changes phải được duyệt, không ghi đè 3A

Original JSON 3A được giữ nguyên như lịch sử. Package này là **proposed revision**: scene 2 thay sliding-only bằng rigs/poses; scene 3 thêm buông tay và butterfly flight/flap; scene 4 xác định bướm còn hiện diện. Sau approval mới tạo revision JSON/hash mới; không chạy bản JSON 3A cũ rồi coi như đã thực hiện package này.

Stable scene IDs `scene-1..4`, segments `segment-1..4`, parent events `event-golden-demo-scene-1..4` được giữ conceptually; script sửa làm approval/hash cũ mất hiệu lực. Có thể bổ sung subevents cho `child-release`, `child-travel`, `butterfly-reveal`, `butterfly-flight`, `family-return`, mỗi subevent exact quote/segment và trạng thái NEEDS_APPROVAL trước duyệt. Chúng chưa phải executable ReviewedEventV2; hiện prototype planner chỉ chấp nhận một action/event cho một segment, nên composite beat execution cần local adapter rõ ràng, không giả production planner đã hỗ trợ.

## 4. Phương án chuyển động — phân loại trung thực

Quy ước: **C** = có code đang thực thi ở layer được nêu; **R** = cần rig/pose mới; **M** = hỗ trợ thủ công, không bắt buộc AI; **U** = chưa thể bảo đảm chất lượng. “2D làm được” về kỹ thuật không đồng nghĩa “engine đã triển khai”.

| Hành động | Với engine hiện tại | Phương án 3B đề nghị | Phân loại và điểm dừng |
| --- | --- | --- | --- |
| Vẽ/tô tranh nguồn | C: silent static V2 MP4 | Visual/object-first, safeguards revision 17 | C; chất lượng nét/timing 18s vẫn U đến khi xem sample |
| Gia đình đi dạo | Không walk executor/rig; target TRANSLATE chỉ still | Rigs giới hạn cho cả ba, 4 key poses/cycle: contact → down/lift → passing → next contact; relative limb transforms + root displacement | R + M, cần Python motion; natural walk hiện U. Không dùng nguyên silhouette slide/bob làm walk PASS |
| Bé buông tay | Mask tay đang liên kết; chưa release pose | Review shared-hand ownership; rig riêng arm/forearm/hand của bé và phần tay bố/mẹ cần đổi; key poses linked → release → arms lowered | R + M. Không cắt tay/gắn hình học; thiếu joint pixels thì tạo derived art được duyệt |
| Bé tới vườn | Child static pose có một chân nhấc, không phải cycle | Child 2D rig/cycle vài bước; chân planted giữ contact, chân swing đi theo keyframes; mặt/tóc/áo nguồn giữ nguyên | R + M. Root path chỉ bổ trợ pose; nếu feet slide/body méo, U/blocker, không animation PASS |
| Bướm được vẽ, bay, đập cánh | New object bị current V2 pilot từ chối | Reviewed butterfly art 3 layers body/left-wing/right-wing; draw outline/color một lần, sau đó wing pivots mở/khép và body chạy đường cong ngắn | M cho art, R cho wing layers/keyframes, cần new-asset adapter. Không bắt buộc AI; chất lượng chưa được test |
| Bé/gia đình trở lại | Chưa time-varying action executor | Reviewed facing/return cycle; parents nếu cần reverse root path kèm bước; endpoint exact original pose | R + M. Không reverse footage một cách làm chân đi lùi trái narration; không lật ngang mặt/đảo túi/chi tiết bất đối xứng |
| Camera pan/zoom, transition | C cho static crop và V1 concat; không temporal V2 camera | Interpolate bounded keyframes, same camera state tại scene joins; matched-state cut không jump | C tái dùng primitives, motion executor phải viết sau duyệt |

### Rig/pose specification tối thiểu

- **Identity anchors giữ nguồn:** mặt, mắt, tóc mẹ/bé, kính bố, áo/cổ áo, màu váy/quần, túi và giày. Không generate lại head/torso để làm pose.
- Derived limb masks/parts là bản mới có parent stable object ID và source hash; **chín mask master bất biến**. Không dùng crop bbox/ellipse thay mask silhouette.
- Bé ưu tiên rig đầy đủ tay/chân cho release/travel/return; bố/mẹ cần lower-limb/tay liên kết rig phù hợp. Váy mẹ không tự deform thành quần/chân; phần chân bị váy che là unknown art, phải review.
- Cycle có ít nhất bốn key poses khác nhau, ankle/foot contact và root advance tương thích; constraints tay giữa nhóm giữ điểm nắm chung. Không tăng body bob để che missing limb poses.
- Dùng source pixels cho những phần nhìn thấy; vùng khớp, tay/giày mới hoặc hidden portions là **DERIVED_POSE_PIXELS**, không claim 100% source pixels toàn frame motion.
- Nếu quay mặt không đủ ảnh nguồn: ưu tiên lộ trình/pose cùng hướng hình vẽ, không flip source bất đối xứng hoặc generate mặt khác. Muốn turn pose mới phải duyệt riêng.
- Rig sample ngắn phải được người dùng xem trước full render. Sample chấp nhận được mới dựng toàn story; không tự loop repair vô hạn.

**Điều kiện minimum “real posture change”:** có thể chỉ rõ object ID, timestamp, arm/leg keyframe/pose ID và thấy relative joint/limb placement đổi theo thời gian. Một global TRANSLATE/SCALE/ROTATE của whole cutout, camera pan hoặc bướm bay riêng **không đáp ứng thay đổi tư thế nhân vật**. Walk PASS còn cần cyclic leg/contact changes; hand-release PASS không tự chứng minh walking PASS.

## 5. Assets thủ công và tự động hóa

Chín stable IDs: `family-52caf90a-{mother,father,child,house,tree,garden,sky,path,remaining-background}`. Source registry/initial states dùng lại; character parts nằm dưới parent identity, không thêm ba “người mới”.

| Phần | Tự động được sau khi có code/assets hợp lệ | Cần người hỗ trợ và duyệt |
| --- | --- | --- |
| Hashes, alpha compositing, source stroke extraction, encoding | Máy xử lý/caching/kiểm tra | Review intermediate drawing vẫn cần người |
| Rig/body-part cutouts, shared hands/feet | Keyframe interpolation/constraints theo rig đã chốt | Annotation joints, limb masks, cut order, occluded joint/hand art và key pose corrections; chưa có auto rig |
| Hidden background khi người di chuyển | Composite patch đã review | Background pixels chưa tồn tại trong nguồn; manual patch cho các vùng thật sự lộ. Không white/median fill rồi báo phục hồi thành công |
| Butterfly | Animate reviewed 3-layer asset; source-colored reveal paths | Owner-supplied/manual chì màu art + outline/color masks/paths; chưa có asset để duyệt style |
| Speech/subtitles | TTS nếu permission, timing/decode/chunking/assembly | Duyệt text/voice, kiểm tra nghe thực tế và chỉnh script nếu slot không đủ |

**Không fully automatic image→55s story trong 3B.** Cần một người xử lý/review rig/pose/art, và người dùng duyệt kết quả. Codex có thể hỗ trợ chuẩn bị/kiểm tra ở task được phép tiếp theo nhưng không có bằng chứng chất lượng manual assets hiện chưa tạo; không hứa không cần animator/artist.

## 6. Chọn công nghệ cụ thể

| Layer | Chọn cho demo ưu tiên | Hiện có / cần thêm |
| --- | --- | --- |
| Whiteboard | `LocalObjectAwareStrokeEngine(strategy="visual")` + V2 source-pixel renderer | Có; không thay source hoặc mở lại endless extraction tuning |
| 2D motion | Python CPU, Pillow/NumPy compositing, per-frame transform và bounded timeline | Primitives có; temporal/rig executor chưa có |
| Keyframe/rig | Source-derived layered rig, reviewed joints/key poses, constrained hand/foot contacts | Chuẩn bị thủ công + implementation nhỏ; không có auto rig model |
| Butterfly | Manual/owner art, reviewed colored-pencil style, separate body/wing layers | Asset và reviewed-new-asset reveal/motion adapter chưa có; không sửa source-only renderer để silent accept new objects |
| Camera/transitions | One shared camera track; smooth eased keyframes; matched-state cut | Static crop có, per-frame interpolation/state handoff cần thêm. Không chọn wipe/fade để che missing art |
| Audio | V1 TTS adapter/caching, demo voice sau permission hoặc recording được phép | Measured speech windows và silence/hold timeline adapter cần thêm |
| Subtitle/final mux | V1 chunk/SRT/FFmpeg concat, H.264/AAC, explicit stream/duration/hash checks | Tái dùng utilities, không gọi whole V1 pipeline vì nó sinh ảnh riêng từng scene |
| Lightning GPU/WAN | **Không dùng ở phương án ưu tiên** | Optional inference/runtime acceptance riêng, chưa được phép chạy/upload source |

Native source fidelity kiểm tra tại 594×336. Resolution output có thể giữ native hoặc upscale để trình chiếu, nhưng upscaling không bổ sung chi tiết thực. Subtitle phải tránh che chân/vườn, có thể đề xuất neutral band ngoài artwork nếu người dùng đồng ý; không crop/đè hình nguồn để đủ chỗ chữ.

### AI dự phòng — không cần cho phương án ưu tiên, không tự chạy

Nếu người dùng chọn AI để hỗ trợ **background patch hoặc limb/pose candidate**: model đề nghị khảo sát là `diffusers/stable-diffusion-xl-1.0-inpainting-0.1`; model card có image/mask/prompt input. Đầu vào chỉ crop liên quan, edit mask chính xác, source hash, pose/line guide do người hỗ trợ tạo và prompt giới hạn; candidate không thay master source. Đây là đề xuất R&D adapter, không một capability đã có trong V2. [Model card SDXL Inpainting](https://huggingface.co/diffusers/stable-diffusion-xl-1.0-inpainting-0.1).

Tùy chọn style reference có thể dùng `h94/IP-Adapter`, SDXL weights `ip-adapter-plus_sdxl_vit-h.safetensors`, với crop/style reference qua image conditioning; không phải pose/rig guarantee. **Suy luận cho bài này:** conditioning có thể giúp style, nhưng chưa benchmark tranh chì màu gia đình, không bảo đảm mặt/tay/identity hoặc pixel fidelity. Bất kỳ pixel ngoài edit region phải composite nguyên bản trở lại; bên trong region là NEW/DERIVED, cần visual review. Không dùng FaceID/face recognition hoặc tái sinh toàn nhân vật. [Diffusers IP-Adapter documentation](https://huggingface.co/docs/diffusers/main/using-diffusers/ip_adapter).

Không chọn independent whole-scene SDXL hoặc WAN video generation cho demo bảo toàn tranh: engine/source fidelity hiện không chứng minh những provider này giữ identity qua bốn cảnh. Không training/fine-tuning trên ảnh trẻ, không gửi private source tới inference service khi chỉ có consent local benchmark.

### Chi phí và permission

- **Phương án đề nghị:** không trả phí AI image/video inference, không GPU rental cho local CPU/FFmpeg; chi phí người chuẩn bị art/rig, điện/máy chưa được định giá. Không gọi toàn bộ dự án “miễn phí”.
- **AI fallback:** chưa có giá GPU/account/machine thực tế được xác minh, chưa benchmark time; do đó total USD **TBD**, không bịa số tiền. Cost estimate phải là `verified rate/hour × billed session hours + storage/other charges`, gồm setup/download/idle nếu bị tính, không chỉ kernel inference.
- Đã mở [Lightning pricing](https://lightning.ai/pricing) nhưng dữ liệu giá theo machine không hiển thị qua công cụ; không thể xác minh L4 rate từ đó. Trước GPU: người dùng cung cấp/chọn rate trong account, duyệt budget trần và thời lượng; không bật máy trước. Một time cap có thể đề xuất sau, không được hiểu là thời gian model đã đo.
- Nếu chọn paid API khác: phải chốt provider/model/rate/quantity, consent truyền dữ liệu và budget mới. Không chuyển sang ElevenLabs hoặc image API trả phí nếu TTS/manual pipeline lỗi.
- Consent local benchmark **không cấp quyền upload tranh sang Lightning/remote AI**. Muốn remote inference phải duyệt riêng source/asset nào được truyền, provider và purpose. Hiện không có upload/inference.

## 7. Audio/TTS demo và subtitle

Chưa có child recording cho Golden story được xác minh. Demo đề nghị dùng **TTS người kể chuyện tiếng Việt**, không gọi giọng của trẻ dù đọc ngôi “em”. Default voice trong provider hiện có là `vi-VN-HoaiMyNeural`; tên này là config hiện tại, cần kiểm tra live availability/sample sau approval, không claim đã nghe hoặc đã synthesize.

`edge-tts` dùng dịch vụ TTS online của Microsoft Edge, không phải model TTS tự huấn luyện/local weights. Tái dùng adapter V1; chỉ truyền **văn bản demo đã được duyệt**, không ảnh/mask/giọng thật của trẻ. Cần người dùng cho phép external text processing riêng. README mô tả client không cần API key, nhưng không chứng minh pricing/SLA/availability cho tài khoản hoặc sản phẩm này; không dùng thay xác minh chính sách production. [Upstream edge-tts](https://github.com/rany2/edge-tts).

- Voice label: “Giọng TTS minh họa — không phải bản ghi/giọng thật của trẻ”. Không voice clone hoặc tự nâng pitch để giả giọng bé.
- Sau duyệt: synthesize/record từng segment một lần, cache theo script/voice hashes, decode/đo duration và speech cues. Không mặc định các slot là audio thật đã đo.
- Cửa sổ thoại 2–11, 19–28, 33–44, 46–53s chỉ là layout nháp. Segment-3 phải split cues đúng release/travel/reveal/flight; bướm bay chỉ sau reveal.
- Nếu text không vừa: report đoạn/thời lượng, xin chỉnh script hoặc redistribute scenes trong 55s/5–20s. Không loop/cắt câu/tự time-stretch hoặc cố kéo giọng cho đủ 55s.
- Track tổng 55s có explicit silence/holds; subtitle chạy theo speech chứ không kéo kín silent slot. Không subtitle sớm hơn hình/thoại; không nghe tiếng TTS lặp scene.
- Existing assembler dùng `-shortest`; nếu audio ngắn, phải pad timeline/đổi adapter đúng semantics để không cắt story. Hash/stream/timing checks không bỏ qua. Không coi last subtitle end luôn là video end khi có hold cuối.
- Không music/SFX trong demo tối thiểu, trừ khi duyệt license/volume riêng. Recording người dùng cung cấp là phương án offline thay thế; local synthesizer chất lượng tiếng Việt chưa được chốt, không auto fallback.

## 8. Camera, transition và source continuity

Giữ camera full → family → garden → full như 3A, nhưng motion track nối endpoint liên tục và giới hạn crop tránh mất tay/giày/nhân vật. Interpolate center/zoom bằng easing, không thay scene style hoặc draw lại source từ đầu.

Matched-state cuts tại 18/32/45s; đầu cảnh sau = cuối cảnh trước về pose/root/camera/new-object state, không reset canvas. Không cần crossfade/wipe trong minimum demo. Bướm không hiện ở scene 1/2, chỉ có sau reveal; cuối story state phải đúng lựa chọn script-4.

Tách nguồn thành background/characters khi story motion, nhưng hidden source pixels chưa tồn tại. Chỉ render travel sau khi approved occlusion patches có; camera đổi không tự giải quyết mọi vùng nền thiếu. Final arrangement source trở về original, derived rig/new butterfly layer kiểm tra riêng; không whole-frame MAE=0 claim cho frame chứa bướm/motion.

## 9. Nghiệm thu Milestone 3B — không chỉ tests

| Mục | Bằng chứng cần có | Fail/blocker |
| --- | --- | --- |
| Story/approval | Approved local script/story/motion/assets/voice records + immutable hashes; demo label rõ | Không fake server Gate A/B; chưa review → NEEDS_APPROVAL |
| 4 scenes/55s | 18/14/13/10s hoặc redistribution được duyệt, tổng 55s; final decode/ffprobe; sai số mux tối đa 0.1s | Speech không fit → structural timing error; không silent truncate |
| Identity/style | Original/nine master masks unchanged; native crops mặt/tóc/kính/áo/váy/giày đối chiếu ở key poses | Mất chi tiết, đổi người/màu/style → VISUAL_QA_NOT_PASSED |
| Posture animation | Ít nhất một nhân vật có relative arm/leg pose changes thấy rõ trong video + pose/timestamp evidence | Chỉ whole-cutout slide/camera/scale/rotation không tính; thiếu → ANIMATION_NOT_PASSED/BLOCKED |
| Walk và hand release | Các cycle có foot contact/swing, hands release hợp lý; rig strips/source comparisons; xem MP4 thực | Foot skating, đứt tay/khớp, nguyên hình trượt → walk/release FAIL; không đổi nhãn thành PASS |
| Butterfly | Reviewed colored-pencil new asset được vẽ trước rồi visible wing flap + flight đúng script | Static butterfly hoặc root-only motion không đáp ứng “đập cánh”; thiếu asset → block |
| Continuity/camera/transitions | Boundary frame pairs ở 18/32/45s, state logs và smooth camera movement; bố mẹ không duplicate/mất | Reset pose/canvas, nhảy camera hoặc lộ nền trắng → FAIL |
| Whiteboard | Scene-1 source drawing và scene-3 butterfly draw xem trực tiếp; no early unscheduled marks/no final snap | Fidelity cuối không đủ cho naturalness PASS; vẫn giữ QA failed nếu nét/tô không đạt |
| Audio/subtitle | Audio thật đã đo, đúng chữ/beat, không loop/cắt lời; captions sync/readable; H.264/AAC streams valid | TTS bị gọi giọng trẻ hoặc lyrics/audio unapproved → FAIL |
| Privacy/runtime | Private local artifacts, no HTTP V2/production changes, no paid/remote calls ngoài scope | Lightning Level 2 chỉ PASS khi chạy thật riêng; local demo không thay thế |

Trước khi đánh dấu Golden/Visual QA PASS, người dùng phải xem **toàn bộ MP4** và chấp nhận cả nét/tô, pose/motion, style, story, voice. Unit tests, source fidelity, rig metrics hoặc có file MP4 không đủ. Nét vẽ hiện chưa đạt hoàn toàn; không được tự nâng Visual QA vì thêm bướm/audio.

## 10. Execution gates sau khi có approval riêng

1. Duyệt script revision này, bướm/bay ở kết, limited-2D style, manual support và audio/cost/privacy choices. Chốt rõ phạm vi approval, không giả final asset approval khi chưa thấy art.
2. Chuẩn bị **candidates** cho motion-ready parts/key poses, hand release, background patches và butterfly; original/masks không đổi. Contact sheets/pose strips trình duyệt riêng trước render story.
3. Sau asset approval, implement offline bounded rig/motion/camera/new-asset/timeline adapters; tests cho unsupported action, identity/mask/source/hash/state continuity. Giữ V1/default/V2 OFF, không HTTP job.
4. Render các sample kiểm chứng ngắn sau khi được phép: source-drawing 18s và rig/hand/butterfly motion. Nếu không đạt chất lượng, báo blocker cụ thể; không GPU/AI tự cứu hoặc loop threshold tuning.
5. Khi samples được duyệt, render một candidate 4 scenes/final mux 55s + narration/subtitles. Artifacts cần có: final/per-scene MP4, original/pose contact sheets, boundary frames, event/pose/state/audio manifests và fidelity/timing/source-new reports.
6. Người dùng review Golden MP4; nếu failed thì report quality limits và stop. Local commit/deploy/backend integration/Lightning test đều cần yêu cầu khác.

**Phương án B tiết kiệm manual work nếu A bị chặn:** sửa story scene-2 thành gia đình đứng cùng ngắm sân, bỏ walking; giữ child hand-release/limited steps thực và butterfly trong scene-3. Đây là **thay nội dung cần duyệt lại**, không fallback đã được phép. Nếu child posture cũng không đạt thì chỉ có static story illustration, không đủ Milestone 3B Animation Acceptance.

## 11. Bảng quyết định để người dùng duyệt

Tất cả đang **PENDING**; không checkbox nào được tick hộ. Có thể duyệt/chỉnh từng mục. Việc duyệt package concept không tự duyệt unseen assets hoặc remote costs.

- [ ] **S1 — Story:** script bốn đoạn revision này, 55s gồm action/holds; giữ bướm bay nhẹ ở cảnh kết hay bỏ/chỉnh segment-4.
- [ ] **M1 — Motion:** chọn A limited 2D rig/walk cho cả ba + child release/travel/return; không yêu cầu tự nhiên như animation studio, nhưng không chấp nhận whole-image sliding. Hoặc yêu cầu phương án khác/chọn B đổi story.
- [ ] **A1 — Asset preparation:** cho phép tạo local derived limb/pose/background/butterfly candidates thủ công từ/reference original, không sửa chín mask master; art candidates vẫn cần visual approval tiếp theo.
- [ ] **V1 — Visual baseline:** giữ visual/object-first/safeguards và thử 18s sau approval; không mặc định naturalness PASS hoặc chấp nhận full-image fade/snap.
- [ ] **T1 — Audio:** TTS người kể demo với voice config hiện có, cho phép gửi approved demo text tới Edge service; **không phải giọng trẻ**. Hoặc người dùng gửi recording/đề nghị voice khác.
- [ ] **C1 — Costs/privacy:** ưu tiên offline/no paid AI/no GPU rental; AI/Lightning/remote child assets **không được phép** nếu chưa có approval riêng kèm verified quote/budget/data scope.
- [ ] **I1 — Implementation authorization:** sau duyệt concept, cho phép Milestone 3B chỉ trong local/demo scope; asset review/sample quality gates vẫn bắt buộc, không HTTP/upload/Gate changes, commit/push/deploy.

## 12. Kết quả lượt chuẩn bị này

Chỉ lập approval package và cập nhật feature records. Git HEAD/index, original/chín masks/world cutouts và source/test/tool code được kiểm tra; không thay application code, không tạo asset/audio/video mới. Các draft 3A và artifact cũ giữ nguyên. Không chạy regression/Ruff/Mypy như một vòng implementation; không có test/visual/animation PASS mới. Nguồn web nêu trên chỉ dùng để xác minh candidate technology/service boundary, không thực hiện inference.

Kiểm tra lượt này: source + 9 mask/asset hashes khớp; Python source/test/tool hashes khớp snapshot 3A; `git diff --check` không lỗi; `tools/validate_repository_security.py` trả REPOSITORY_SECURITY_VALID, 1.666 publishable files scanned. HEAD không đổi, staged files rỗng. Security/whitespace checks không phải bằng chứng renderer/rig/Golden runtime PASS.

**Dừng tại FINAL_APPROVAL_PACKAGE_READY / AWAITING_OWNER_APPROVAL.** Milestone 3B rendering/animation chưa bắt đầu; Visual QA vẫn NOT_PASSED.
