# FEAT-087 — Chủ thể chính/phụ và video LTX-2.5 dựng theo khung mốc

**Trạng thái:** DESIGN — AWAITING_APPROVAL (chưa được implement)
**Ngày:** 2026-11-24
**Worktree:** `<LOCAL_ROOT>\.codex-worktrees\fe`, branch `feature/fe-mobile-remediation`
**Kế thừa:** FEAT-086 Rev1/Rev2 (prompt-only, chưa có video thật để kiểm chứng). FEAT-087 tách riêng vì đổi contract công khai (nhận diện tranh, xác nhận chủ thể, story) mà FEAT-086 đã loại khỏi phạm vi.
**SRS:** FEAT-063 v2.7-draft (unsigned). Liên quan FR-AI-02/03/04/05/06, UC-02. Không sửa SRS; xem §9 về điểm cần owner xác nhận.

---

## 1. Ý định và lý do

Video Parent hiện tại không ra gì: kịch bản "rùa ăn lá" nhưng lá không bao giờ mất, nét rùa trôi dần thành hình vector sạch, và có vật lạ xuất hiện (que cạnh miệng rùa). Owner muốn video LTX-2.5 **đúng kịch bản, hợp lý về vật lý, giữ được nét tranh của bé**.

Nguyên nhân gốc (đã đọc code, 2026-11-24):

1. **Nhận diện chỉ trả một chủ thể.** `drawing_vlm_app.py` (Qwen3.8-27B-FP8) trả `candidate_subject`, `visible_features`, `confidence`. Không có khái niệm nhiều vật hay vị trí.
2. **Backend khoá cả bức tranh thành một thực thể.** `_build_input_manifest` trong `parent_video_candidate_service.py` luôn tạo đúng 1 entity `subject-main` = cả bức tranh, mọi cảnh `visible=[subject-main]`, `removed=[]`, `continuity_in = "preserve its full composition"`. `validate_story_visual_plan` còn bắt buộc đúng một entity `source_drawing`. → Lá vẽ trong tranh không có cách nào biến mất.
3. **Prompt tự mâu thuẫn.** `compile_scene_prompt` (story-i2v-v7) vừa ra lệnh "keep all other marks and the paper still / preserve composition" vừa ra lệnh "ăn lá"; đuôi prompt là danh sách dài "no X, no Y". `DistilledPipeline` không dùng negative prompt/CFG, nên từ cấm dễ thành gợi ý.
4. **Trôi nét cộng dồn.** Cảnh 2..N được điều kiện bằng frame cuối của cảnh trước (`_extract_continuity_frame`), lỗi tái tạo của VAE/model chồng lên nhau.
5. **Chỉ có khung đầu.** Mỗi cảnh chỉ có `ImageConditioningInput` ở `frame_idx=0`; trạng thái kết thúc (lá đã mất, rùa đứng chỗ mới) hoàn toàn để model tự đoán.

## 2. Mục tiêu, không làm, phản mục tiêu

### Mục tiêu
- G1. Nhận diện tranh trả **1 chủ thể chính + 0–3 chủ thể phụ**, mỗi cái có tên, đặc điểm, vị trí (khung bao).
- G2. Phụ huynh **xem và sửa nhẹ** ở màn xác nhận chủ thể: sửa tên, bỏ chọn vật phụ, đổi một vật phụ thành chủ thể chính.
- G3. Story biết vật phụ và ghi trạng thái của mỗi vật qua từng cảnh (còn / thay đổi một phần / di chuyển / mất) cùng vị trí chủ thể chính cuối cảnh.
- G4. Video theo hướng **B**: chủ thể chính được di chuyển trong khung; trong lúc chuyển động có thể lệch nét, nhưng **khung đầu và khung cuối mỗi cảnh là nét gốc thật**. Vật phụ đổi đúng trạng thái kịch bản (ví dụ lá mất hẳn ở cảnh cuối).
- G5. Không còn trôi nét qua các cảnh; không vật lạ ngoài kế hoạch.
- G6. Có bộ đo tự động + bộ tranh synthetic để so sánh trước/sau bằng số liệu, không chỉ bằng mắt.

### Không làm (non-goals)
- Không đổi số cảnh (5), thời lượng (30–90s), video vẫn **câm**.
- Không thêm provider/model video mới, không ComfyUI, không LoRA/IC-LoRA motion-track (để sau nếu cần).
- Không đổi quota/payment, auth, consent, safety policy, admission.
- Không nối auto-retry theo điểm chất lượng (FR-AI-06 retry) trong feature này; điểm chỉ để báo cáo và chọn tham số.
- Không hỗ trợ tranh có nền tô kín/nhiều màu nền ở mức chất lượng cao (xem §6.6 giới hạn).

### Phản mục tiêu (dù chạy được vẫn coi là thất bại)
- Chủ thể chính bị vẽ lại/đổi phong cách ở khung cuối cảnh.
- Hình tranh bị nhân đôi, thu nhỏ thành ảnh lồng/khung/thẻ (lỗi FEAT-086 D3).
- Vật phụ phụ huynh đã bỏ chọn vẫn bị story dùng như đối tượng tương tác; hoặc AI tự thêm vật không có trong tranh/kịch bản.
- Tranh chỉ có một vật mà chất lượng tệ hơn hiện tại.
- Lộ nội dung model thô vào log, hoặc dùng dữ liệu trẻ thật.

## 3. Ràng buộc

- Tuân `AGENTS.md`: feature folder, plan + acceptance trước, approval trong `approvals/TASK_APPROVAL.md`, evidence trong feature folder.
- Không commit/push/stage/branch switch. Không đụng DB chia sẻ/production; migration chỉ local nếu thật cần (thiết kế này cố tránh migration, §6.2).
- Dữ liệu synthetic. Live inference chỉ trong gói đã duyệt ở §6.9 (cả gói một lần); `OWNER_VIDEO_INFERENCE_APPROVED` chỉ chuyển YES cho gói này khi thiết kế được duyệt. Không auto-retry, không warm GPU.
- LMFE 0.11.3 **không ép min/max số** (bài học FEAT-081 Rev20C) → mọi số trong output model phải là enum/grid đóng.
- Giữ nguyên tranh gốc và provenance (FR-AI-03): mask, sprite, keyframe là artifact dẫn xuất có hash.
- Giữ cổng duyệt của người lớn (subject review, script review).

## 4. Các phương án đã cân nhắc

| # | Phương án | Đánh đổi | Kết luận |
|---|---|---|---|
| 1 | Chỉ sửa kế hoạch hình ảnh + prompt: nhiều thực thể, trạng thái từng cảnh, prompt viết khẳng định, mỗi cảnh bắt đầu từ tranh gốc | Rẻ, không thêm model; nhưng lá có mất hay không và rùa có giữ nét hay không vẫn do LTX tự đoán | Làm như nền móng, không đủ một mình |
| **2** | **Phương án 1 + tách vùng bằng SAM 2.1 + ghép khung đầu/cuối mỗi cảnh từ nét gốc; LTX chỉ vẽ chuyển động ở giữa** | Đúng hướng B, lá mất chắc chắn, hết trôi nét; tốn thêm bước GPU, đưa SAM từ thử nghiệm vào luồng chính, cần kiểm chứng LTX nhận ảnh ở frame cuối | **Owner chọn (2026-11-24)** |
| 3 | Hoạt hình cắt ghép 2D (sprite + biến hình), không dùng LTX cho chuyển động chính | Nét tuyệt đối, rẻ; nhưng trông như rối giấy, mất cử động tự nhiên, đi ngược mục tiêu dùng LTX-2.5 | Loại |

Owner cũng đã chọn: **hướng B** (chủ thể chính được di chuyển, cuối cảnh về nét gốc) và **phụ huynh xem + sửa nhẹ** vai trò chính/phụ.

## 5. Luồng tổng thể

```
Ảnh tranh ─► [1] Nhận diện v2 (Qwen VLM): main + secondaries + bbox
           ─► [2] Phụ huynh xác nhận/sửa (UI) ─► roles đã duyệt (backend lưu)
           ─► [3] Story v2 (Qwen text): 5 cảnh + staging ẩn từng cảnh
           ─► [4] Phụ huynh duyệt script (không đổi UX)
           ─► [5] Video worker (L40S):
                 a. SAM 2.1 mask theo bbox từng vật (cùng GPU, không gọi app khác)
                 b. Ghép khung mốc K0..K5 từ nét gốc theo staging
                 c. Mỗi cảnh i: LTX(start=K(i-1), end=K(i), prompt khẳng định)
                 d. Đo chất lượng từng cảnh, ghép MP4 câm
```

## 6. Thiết kế theo thành phần

### 6.1 Nhận diện tranh v2 (`drawing_vlm_app.py`)
- Schema output mới `sketch2life.drawing-understanding.v2`:
  ```json
  {
    "main_subject": {"label": "con rùa", "visible_features": ["mai có ba ô tròn", "..."], "box": [x0, y0, x1, y1]},
    "secondary_subjects": [{"label": "chiếc lá", "visible_features": ["lá có gân giữa"], "box": [...]}],
    "confidence": 0.8
  }
  ```
- Thêm `facing` (enum `left|right|front`) cho chủ thể chính để compositor biết có cần lật sprite. *(quyết định của người viết thiết kế)*
- `box` dùng **lưới 0–20** (mỗi số là enum 21 giá trị) vì LMFE không ép range; đủ để làm prompt cho SAM. `confidence` giữ enum 0.0–1.0 hiện có. `secondary_subjects` 0–3 phần tử; `visible_features` của vật phụ 0–2.
- Prompt: giải thích chủ thể chính = vật lớn/trung tâm/sinh vật có thể hành động; vật phụ = vật khác vẽ riêng biệt (đồ ăn, đồ chơi, cây…); không liệt kê nền, mặt đất, đường kẻ trang trí; không bịa vật không thấy.
- Parser kiểm tra: box hợp lệ (x0<x1, y0<y1, diện tích tối thiểu), label không trùng, không quá 3 vật phụ. Thêm code `contract_violation` mới (content-free) cho các lỗi này.
- Tương thích: backend đọc được cả bản ghi v1 cũ (coi như `secondary_subjects=[]`, không có box → video đi đường fallback §6.7).

### 6.2 Backend: lưu và xác nhận vai trò
- Kết quả v2 lưu trong `understanding_revisions.result_snapshot` (JSONB, đã có) → **không cần migration** cho phần lưu kết quả AI. `subject_label` vẫn là label chủ thể chính.
- Mỗi vật có `entity_id` ổn định do backend gán (`main`, `sec-1..3`) khi nhận kết quả.
- API xác nhận chủ thể (`confirmSubjectV1`) nhận thêm (tùy chọn, tương thích ngược) danh sách vai trò cuối: `{entity_id, label, role: main|secondary|excluded}`. Ràng buộc: đúng 1 main; chỉ được dùng entity_id có trong snapshot của đúng `understanding_revision`; label 1–100 ký tự; idempotency/stale giữ như hiện tại.
- Gọi API **không kèm** danh sách vai trò (client cũ) → mọi vật phụ coi là `excluded`, story chỉ dùng chủ thể chính. Lý do: không đưa vào truyện vật mà người lớn chưa duyệt. *(quyết định của người viết thiết kế)*
- Lưu vai trò đã duyệt cùng quyết định xác nhận chủ thể. Builder kiểm tra bảng `review_decisions` có cột JSONB phù hợp không; nếu không, chọn nơi lưu không cần migration (ví dụ snapshot của confirmation) và ghi vào DECISIONS. Chỉ khi bắt buộc mới thêm migration local, ghi rõ.
- `ParentStoryRunV1` trả thêm `subject_roles` để UI hiển thị lại khi resume.

### 6.3 UI mobile (màn xác nhận chủ thể)
- Giữ khối chủ thể chính như hiện tại (tên sửa được).
- Thêm mục **"Vật khác trong tranh"** (ẩn nếu rỗng). Mỗi dòng: tên (sửa được), công tắc "Dùng trong truyện", nút "Đặt làm chủ thể chính" (đổi chỗ: chính cũ thành vật phụ).
- Gửi danh sách vai trò khi bấm xác nhận. Resume/cold start hiển thị lại vai trò đã lưu.
- Copy tiếng Việt qua `validate-ui-copy.mjs`. Không thêm asset hình mới (nếu cần icon, theo FRONTEND_ASSET_GATE).
- Builder xác định màn chính xác (`UnderstandingScreen.tsx` hoặc `DrawingSubjectScreen.tsx`) theo luồng hiện tại.

### 6.4 Story v2 (`language_audio_app.py`)
- Prompt nhận `main_subject` và `secondary_subjects` đã duyệt (vật `excluded` không được gửi). Story dùng vật phụ như đối tượng tương tác tự nhiên khi hợp lý; không bắt buộc dùng hết.
- Output version mới `sketch2life.story-revision.v2`: mỗi scene thêm khối **`staging`** (ẩn với phụ huynh, chỉ cho video):
  - `main_end`: `{"position": <enum 9 ô: left|center|right × top|middle|bottom>, "facing": "left|right", "scale": "same|slightly_bigger|slightly_smaller"}`
  - `secondary_end`: danh sách `{"entity_id", "state": "unchanged|moved|partly_gone|gone", "position"? (khi moved)}`; mọi vật phụ đã duyệt phải có mặt.
- Validator: trạng thái hợp lệ theo trình tự (đã `gone` thì không quay lại); vật phụ không được `moved` vào ô của chủ thể chính; tối đa một thay đổi lớn mỗi cảnh cho mỗi vật.
- v1 cũ vẫn đọc được (không có staging → fallback §6.7). Phụ huynh không sửa trực tiếp chữ script; viết lại đi qua `rewrite_instruction` và model sinh lại cả story lẫn staging, nên staging luôn đi cùng bản story hiện tại.
- Staging sai validator **không** làm fail story: story vẫn lưu và cho phụ huynh duyệt, staging bị bỏ, video chạy fallback, ghi mã lý do content-free. Lý do: lỗi phần kỹ thuật ẩn không nên chặn phụ huynh. *(quyết định của người viết thiết kế)*
- UI script review không đổi (staging không hiển thị). Lý do: staging là dữ liệu kỹ thuật dẫn xuất từ hành động phụ huynh đã duyệt; đây là quyết định của người viết thiết kế, owner có thể yêu cầu hiển thị.

### 6.5 Tách vùng (SAM 2.1 trong video worker)
- Đưa SAM 2.1 hiera-small (checkpoint đã ghim trong `drawing_segment_app.py`) vào image của `video_app.py`; chạy **box-prompt** cho từng vật ngay đầu job, trên cùng GPU L40S → không thêm Modal app call, không thêm workload duyệt riêng.
- Kiểm tra mask: diện tích trong box tối thiểu, mask chủ thể chính không chồng quá ngưỡng lên mask vật phụ, mask phủ phần lớn nét mực trong box. Fail → fallback §6.7, ghi lý do content-free.
- Mask, sprite đều có SHA-256 ghi trong output manifest (FR-AI-03). Không thay đổi tranh gốc.

### 6.6 Ghép khung mốc (compositor, CPU, PIL/numpy)
- `K0` = tranh gốc đặt vào canvas 1280×768 (như `_prepare_story_drawing` hiện tại).
- Nền giấy: lấy màu giấy ước lượng từ vùng ngoài mọi mask; xóa một vật = tô vùng mask (nở vài px) bằng màu giấy.
- `K(i)` từ `K(i-1)` và `staging` cảnh i:
  - Chủ thể chính: cắt sprite từ **tranh gốc** (không bao giờ từ frame model sinh), đặt ở ô `position`, lật ngang theo `facing`, scale trong [0.85, 1.15]; luôn nằm trọn trong khung an toàn của crop 720p.
  - Vật phụ: `unchanged` giữ nguyên; `moved` đặt sprite gốc vào ô mới; `gone` xóa; `partly_gone` xóa khoảng 40–60% mask ở phía gần chủ thể chính (cắt bằng đường cong đơn giản), phần còn lại là nét gốc.
- Giới hạn chấp nhận: tranh nét trên nền giấy sáng. Tranh nền tô kín → chỉ cho phép trạng thái `unchanged`/không dịch chủ thể (fallback từng phần), ghi lý do.

### 6.7 Điều kiện LTX và prompt (`video_app.py`, `story_visual_plan.py`)
- Mỗi cảnh i: `images=[ImageConditioningInput(K(i-1), frame_idx=0, strength=1.0), ImageConditioningInput(K(i), frame_idx=last, strength=s_end)]`. `s_end` chọn qua đánh giá (đề xuất bắt đầu 1.0, thử 0.8). Cảnh sau bắt đầu từ **khung ghép** K(i-1), không từ frame model sinh → hết trôi nét.
- **Một cảnh = một lượt gọi LTX.** Code hiện tại gọi `_run_ltx` đúng một lần mỗi cảnh, giới hạn `MAX_VIDEO_SECONDS = 20` mỗi lượt; cảnh 6–18s nằm gọn. Vì vậy mỗi cảnh chỉ cần 2 khung mốc (đầu, cuối), không có khung trung gian. *(đã kiểm tra trong code)*
- **Cổng M0 bắt buộc:** đọc code LTX đã ghim (v1.6.2 / commit `f0f2f86…`) xác nhận `DistilledPipeline` nhận nhiều ảnh điều kiện với `frame_idx` ở frame cuối và hành vi đúng (khung cuối khớp ảnh). Nếu không hỗ trợ → dừng, báo owner, không tự đổi pipeline.
- Visual plan v3: nhiều entity (`main` kind subject + vật phụ kind `drawn_secondary` source `source_drawing` + prop story_directed như cũ). Validator sửa: đúng 1 subject, 0–3 drawn_secondary; `removed` khớp `gone`.
- Prompt `story-i2v-v8`: mô tả **chuyển động giữa hai khung** bằng câu khẳng định (chủ thể đi từ đâu đến đâu, làm gì với vật phụ, vật phụ thay đổi ra sao), giữ phong cách nét vẽ tay và giấy; bỏ phần lớn danh sách "no …", chỉ giữ 1 câu ngắn về không chữ/không khung.
- **Fallback** (v1 record, không box, SAM fail, staging thiếu): dùng đường phương án 1 — kế hoạch nhiều thực thể nếu có, prompt v8, mỗi cảnh bắt đầu từ K0 (không chaining frame model), không khung cuối. Ghi `render_mode` = `keyframe|fallback` trong manifest.

### 6.8 Đo chất lượng (báo cáo, không auto-retry)
Mỗi cảnh, tính trên frame cuối và vài frame giữa:
- **Giữ nét chủ thể chính:** IoU của edge map trong mask chủ thể giữa frame cuối và K(i).
- **Trạng thái vật phụ:** tỉ lệ mực trong vùng mask vật phụ ở frame cuối so với kỳ vọng (`gone` ≈ 0, `partly_gone` ~ một nửa, `unchanged` ≈ gốc).
- **Vật lạ/nhân đôi:** mực xuất hiện ngoài vùng của mọi entity (sau nở mask) vượt ngưỡng.
- **Chuyển động có thật:** độ lệch trung bình giữa các frame giữa (tránh video đứng im).
Kết quả ghi vào output manifest và evidence; ngưỡng ban đầu chọn sau đợt đánh giá đầu.

### 6.9 Bộ đánh giá
- 3 tranh synthetic nét đen (provenance ghi rõ): rùa + lá (ăn), mèo + quả bóng (đẩy/lăn), chim + quả táo hoặc tương đương (mang đi). Thêm tranh rùa một vật hiện có (`synthetic_turtle_lineart.png`) để kiểm tra không tệ hơn.
- Offline: test contract cho mọi schema/validator/compositor; compositor chạy CPU tạo K0..K5 và lưu PNG làm evidence để owner xem trước **khi** tốn GPU.
- **Gói live inference (owner chọn duyệt một lần cả gói, 2026-11-24; có hiệu lực khi thiết kế được duyệt):**
  - Deploy lại 3 app Modal `dev`: drawing VLM, language/story, video (thêm SAM). Không chạy inference khi deploy.
  - M1: 4 lượt gọi VLM nhận diện (4 tranh synthetic).
  - M4: 3 lượt gọi story v2.
  - M6 spike: 2 lượt gọi thẳng worker video, 1 cảnh tranh rùa + lá, `s_end` = 1.0 và 0.8; manifest dựng tay, không qua backend.
  - M7: 3 video đầy đủ qua luồng app, mỗi tranh 1 lần.
  - Không retry, không warm GPU, không đụng production. Bước nào lỗi thì dừng và báo owner, không chạy bù. Ngoài gói này cần duyệt mới.

## 7. Thứ tự làm (milestone)

- **M0** — Đọc code LTX ghim, xác nhận đa ảnh điều kiện + frame cuối. Ghi kết luận. Dừng nếu không hỗ trợ.
- **M1** — Nhận diện v2 + parser + test (offline, LMFE thật).
- **M2** — Backend: lưu v2, API vai trò, `subject_roles` trong run, test.
- **M3** — UI "Vật khác trong tranh" + test + validate-ui-copy.
- **M4** — Story v2 + staging + validator + test.
- **M5** — SAM trong video worker + compositor + visual plan v3 + prompt v8 + fallback + metric; test offline; xuất K0..K5 PNG cho owner xem.
- **M6** — (trong gói §6.9) live spike 2 lượt một cảnh → chỉnh `s_end`/ngưỡng.
- **M7** — (trong gói §6.9) 3 lượt đánh giá, báo cáo so sánh trước/sau, cập nhật evidence/STATUS.

## 8. Tiêu chí chấp nhận

- A1. Nhận diện trả đúng schema v2 với tranh rùa + lá (synthetic), lá nằm ở `secondary_subjects`, box đúng vùng; tranh một vật trả `secondary_subjects=[]`.
- A2. Phụ huynh sửa tên, bỏ chọn, đổi chính/phụ được; backend từ chối vai trò sai (0 hoặc 2 main, entity lạ, revision cũ); resume hiển thị lại vai trò.
- A3. Story v2 qua validator; vật bị bỏ chọn không xuất hiện; staging hợp lệ.
- A4. Khung K(i) chứa sprite chủ thể giống tranh gốc từng pixel (trước mọi xử lý model); lá ở K5 đã mất với kịch bản "ăn lá".
- A5. Live: frame cuối mỗi cảnh đạt ngưỡng giữ nét chủ thể; trạng thái lá đúng kịch bản; không nhân đôi/ảnh lồng; có chuyển động thật. Owner xem video và đồng ý tốt hơn bản hiện tại.
- A6. Fallback chạy với record v1 cũ; tranh một vật không kém hiện tại.
- A7. Không dữ liệu trẻ thật, không auto-retry, không commit/push; mọi artifact dẫn xuất có hash.

## 9. Điểm cần owner xác nhận / rủi ro

- SRS FR-AI-05 "giữ chủ thể dễ nhận biết" và AT "one child subject": thiết kế giữ **một** chủ thể chính; vật phụ là chi tiết trong tranh được phép đổi. Mình coi đây là cách hiện thực, không sửa SRS. Nếu owner muốn SRS ghi rõ, cần một thay đổi SRS riêng.
- Rủi ro LTX: khung cuối có thể sinh "cut" đột ngột hoặc ảnh lồng (giống FEAT-086 D3). M0 + M6 kiểm tra; có fallback.
- Rủi ro chi phí: mỗi video thêm SAM (vài giây GPU) + có thể chậm hơn vì 2 ảnh điều kiện.
- Rủi ro nhận diện box của Qwen kém trên tranh trẻ thật; tranh synthetic không chứng minh được điều này.

## 10. Để lại cho builder
- Tên file/màn UI chính xác, layout dòng "Vật khác trong tranh" theo design system hiện có.
- Nơi lưu vai trò đã duyệt không cần migration (§6.2).
- Thuật toán cụ thể cho `partly_gone`, màu giấy, nở mask; ngưỡng metric ban đầu.
- Cách đưa SAM vào image video (pip từ commit đã ghim, checkpoint trên volume hiện có).
