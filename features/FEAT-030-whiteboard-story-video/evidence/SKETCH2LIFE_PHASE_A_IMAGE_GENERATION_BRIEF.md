# SKETCH2LIFE — Phase A: Gold Visual Reference / Image Generation Brief
Revision32 — 2026-10-10

## Trạng thái thực tế

BLOCKED_NEEDS_IMAGE_GENERATION.
Chưa tạo asset pack/storyboard mới đạt Gold Reference. Chưa render video. Những artwork local thô/crop ghép trước đây không phải baseline chất lượng hoặc kết quả Phase A.

Gold Visual Reference do người dùng gửi được ghi nhận là chuẩn thẩm mỹ. Bốn cảnh:gia đình trước nhà,bé vào vườn,bé cúi hái hoa,bé thấy bướm. Nội dung demo local,không phải Gate A/B production hay lời kể thật của bé.

## Đầu vào được xác minh

- Original: ${PRIVATE_SOURCE_DIR}/familly.jpg (family1.jpg là alias benchmark), SHA256:
52caf90a2242d04fc107afa1f17b8de738c5f8982200fc504fe725a5607ee3d3.
- Gold do người dùng gửi: ${PRIVATE_REFERENCE_DIR}/gold-storyboard.png (original attachment; private path recorded in external backup).
- Bản sao Gold bền hơn, ngoài Git: D:/Codex/Sketch2Life/phase_a_gold_reference_2026-10-10/reference/gold-storyboard.png.
SHA256:9e54836bdb15639e4f8d7204dde2e44561b413ecba1d2bcbc49cc6046640b090.
-9master masks được kiểm hash:9checked,0mismatches;không chỉnh mask/ảnh nguồn.
-Source crops từ manifest hiện có chỉ dùng làm identity inputs;không được trả crop collage làm artwork cuối.

## Read-only runtime evidence

GPU:nvidia-smi xác nhận NVIDIA GeForce RTX3060,12288MiB,driver591.86.
RAM:CIM total33360056KiB (~31.8GiB),free15729808KiB (~15.0GiB) tại thời điểm kiểm.
Disk free:C11.6GiB,D173.6GiB.
Backend venv thiếu torch,diffusers,transformers,accelerate,safetensors;import torch thực tế báo ModuleNotFoundError.
Không tìm được weights/model_index trong project/D:/Codex/Sketch2Life và HuggingFace hub cache được kiểm. Đây là phạm vi kiểm tra,không khẳng định mọi thư mục trên toàn máy đều không có model.

Built-in image generation tool có sẵn trong phiên. Không gọi vì yêu cầu hiện tại chưa cho phép gửi ảnh trẻ/source derivatives tới dịch vụ ngoài. Không cần API key khi dùng built-in;model/runtime/cách tính phí cụ thể của tool không được metadata hiện tại xác nhận,không tự bịa tên model hay giá.

Chưa có truy cập runtime LightningAI trong phiên này. Screenshot/log các lượt trước không chứng minh một model image-edit đang sẵn sàng hiện tại.

## Code hiện có và khoảng trống liên quan

tools/lightning_whiteboard_provider.py:
- /v1/story-video/illustration đọc một source_image base64/hash.
- Khoảng dòng955:AutoPipelineForImage2Image;pipe(prompt=...,image=image,strength=...,guidance_scale=...,num_inference_steps=...).
- Khoảng dòng632:_story_image_pipe tải model_id từ cấu hình và CPU offload.
- Cache/IllustrationAssetV1/provenance có thể tái sử dụng sau khi được phép tích hợp.

Hiện chưa truyền riêng Gold style reference,canonical boy sheet,parents/object references vào cùng model call. Không thể chỉ đổi model_id sang QwenImageEditPlus rồi coi adapter tương thích vì lớp pipeline và tham số khác.
WAN là video model path riêng;không giải quyết blocker chất lượng image-to-image của Phase A. Không thay renderer hoặc mở thêm engine trong lượt này.

## Phương án xử lý cần lựa chọn và phê duyệt

### A — Built-in image generation với ảnh tham chiếu

Công cụ đã có,phù hợp tạo/style-translate illustration từ ảnh tham chiếu. Cần người dùng cho phép gửi:
1.original family drawing và các crop/mask-derived identity inputs cần thiết;
2.Gold Reference;
3.candidate character/assets tạo ra trong cùng job để giữ consistency;
4.các prompt demo.

Phạm vi:7asset jobs+4scene jobs,output candidate private local,không training workflow,không gọi paid API fallback bằng key,không MP4. Không tự cam kết chính sách retention/training của nhà cung cấp khi chưa được xác minh. Chỉ thực hiện generation sau route/data/cost permission.
Khả năng giữ identity và đạt Gold style phải được đánh giá trên output thật,không bảo đảm bằng prompt.
Model dưới built-in tool không được pin/hiển thị metadata;không ghi là Qwen hay GPT-Image cụ thể.

### B — Local image-edit runtime, không upload ảnh

Ứng viên cụ thể:Qwen/Qwen-Image-Edit-2511 với QwenImageEditPlusPipeline.
Model card chính thức thể hiện multi-image inputs,character-consistency improvements,Apache2.0 và20B/BF16:
https://huggingface.co/Qwen/Qwen-Image-Edit-2511
API multi-reference:
https://huggingface.co/docs/diffusers/en/api/pipelines/qwenimage

Dữ liệu:image=[source/crop,GoldReference,selected consistent character asset] theo số lượng reference thực sự được model/runtime hỗ trợ và thử nghiệm. Đây là suy luận workflow từ API,không phải benchmark Gold đã PASS.
Full20B BF16 weights có quy mô khoảng40GB theo phép tính20B×2byte,chưa gồm text encoder/VAE/activations. Không thể nằm toàn bộ trong12GBVRAM. Quantization+CPU offload có thể cần nhưng chưa chọn bản weights/precision và chưa kiểm memory/quality.
Không khẳng định RAM32GB+GPU12GB chắc chạy ổn. Cần pin supported build/weights,license/hash,download size,peak memory và thử synthetic reference trước. Dùng env/model cache riêng trênD,không cài nặng vàoC còn11.6GiB.
Chưa tải/cài/runtime/inference. Local downloads vẫn dùng network lấy weights,nhưng ảnh đầu vào không cần rời máy.
Không tự chuyển sang LightningAI:đó là nơi xử lý ảnh ngoài máy/có thể rental,cần permission riêng.

### Quyết định cần thiết

Người dùng chọn A (cho phép external processing bằng built-in) hoặc B (local runtime/weights installation + bounded capability pilot). Đây là blocker quyền xử lý/tài nguyên thực tế theo yêu cầu người dùng,không phải thiếu kịch bản hoặc cần thêm architecture plan.

## Concrete generation brief đã chuẩn bị

D:/Codex/Sketch2Life/phase_a_gold_reference_2026-10-10/phase-a-prompt-pack.json
11prompt jobs đã viết sẵn,NOT_EXECUTED.

7asset jobs:
- boy-character-sheet:4poses đồng nhất,hair/face/proportions/clothes/pocket/shoes.
- mother-character:hair,orange top,red skirt,pink handbag.
- father-character:black hair,glasses,orange/green trim,gray trousers.
- house:two stories,red roofs,blue doors/windows,pink walls.
- tree:green canopy,natural branches/trunk.
- garden-flowers:flowers/leaves/stems cùng style.
- butterfly:orange/cyan,new demo asset.

4scene jobs:
- Scene1 family holding hands in front of home/tree/path/flowers.
- Scene2 boy step pose entering garden,house recedes.
- Scene3 bent torso/knees,hand genuinely contacts picked flower stem.
- Scene4 same boy/flower notices butterfly;gaze/expression demonstrate discovery.

Mỗi job ghi role source vsGold vsselectedcandidate. Không text-only generic replacement. Selected candidate chỉ là khóa consistency nội bộ trong PhaseA,chưa được gọi owner-approved asset.
Output PNG riêng từngscene;không chèn subtitle/tiêu đề vào artwork để sau này typeset/draw riêng.
Không crop Gold thành bốn hình rồi báo là đã sinh storyboard. Không dùng kết quả code-native sơ sài để thay generation.

## Quality acceptance và thứ tự trong Phase A

- Boy sheet cùng khuôn mặt,tóc cam/nâu,áo xanh/túi cam,quần tím,giày xanh;poses anatomy hợp lý.
- Parents/object pack cùng nét đen mềm,tươi sáng,hatching crayon/pencil,bgwhite;không generic clipart.
- Bốncomposition vàaction khác nhau;không clone toànsource.
- Scene3 hand/flower/neck/knees/feet plausible,scene4gaze/butterfly/flower consistent.
- Không đổi nhà thành một tầng hoặc mất kính/túi/màuoutfit.
- So sánh source/candidate/Gold,cùng character sheet và asset manifests/hashes.
- Chỉ khi generation có output thật mới đánh giá style/fidelity;dừng cho người dùng review trướcPhaseB.
- Artwork và drawing-control tách biệt;không yêu cầu pixel tracing/micro-paths.
- Timing/video/audio chưa triển khai trongPhaseA;45–60s là targetPhaseC,dựaaudio đã duyệt.

## Repository protection và kết quả kiểm tra

HEAD93668ffdaa7f2890fe9498596c670006a87eba4a,branch codex/feat-018-contract-plan.
Staged diff empty;git diff --check pass.
345existing backend/tools Python files giữ nguyên aggregate digest:
b3820e289ef084d817ea9cf951438346e4796a9db16ca7c7c5f20009959b3c5d.
Không sửa runtime,không chạy pytest không liên quan. Không báo whole-repository PASS.
V1 mặc định,V2OFF,Gates không đổi.
Không inference/model installation/image upload/commit/push/merge/deploy.
Chỉ feature documentation/prompt brief/Gold copy tạo mới. Các ảnh/code cũ được giữ và không được coi acceptedbaseline.

## Skill sử dụng

imagegen skill:
${CODEX_SKILLS_DIR}/.system/imagegen/SKILL.md.
Instruction:"Use the built-in image_gen tool by default for normal image generation and editing requests."
Skill được dùng để chuẩn bị reference roles/prompts và tránh vector substitutes. Việc chưa gọi tool đến từ giới hạn trực tiếp của người dùng về external processing/paid inference;không phải skill yêu cầu thêm một visual approval loop.

## Handoff

PhaseA chưa hoàn thành artwork. Trạng thái cuối BLOCKED_NEEDS_IMAGE_GENERATION.
Prompt pack vàroute brief đã cụ thể để lựa chọn quyền xử lý. Không tiếp tục các phương pháp thô hoặc chuyểnPhaseB/C.
