# FEAT-020 — PixiJS Domain Asset Library Plan

**Ngày cập nhật:** 2026-09-13  
**Trạng thái:** PLANNED / bổ sung phạm vi, chưa triển khai PixiJS  
**Phạm vi:** domain assets dùng chung cho toàn bộ activity catalog  
**Không bao gồm:** UI, system-state illustration, PixiJS renderer, video generation và AI asset generation lúc runtime

## 1. Quyết định phạm vi đã chốt

Plan này bổ sung và mở rộng `PIXI_ASSET_PLAN.md`. Gói 12 SVG hiện có vẫn được giữ lại như **starter/smoke set**, nhưng không còn được coi là thư viện asset đầy đủ.

Các quyết định của task:

| Quyết định | Quy định thực thi |
|---|---|
| Độ bao phủ | Bao phủ toàn bộ 100 activity trong MVP activity catalog, không chỉ 20 golden activity. |
| Cách tái sử dụng | Asset được tổ chức theo semantic/material family dùng chung; không tạo một bộ asset riêng cho từng activity nếu cùng biểu tượng vật liệu/đối tượng. |
| Kiểu asset | Hand-authored vector/SVG, deterministic, không gọi ImageGen/model/API tạo ảnh khi chạy workflow. |
| Khả năng animation | Asset phải có layer, crop, mask và biến thể nền trong suốt khi semantic đó cần chuyển động hoặc compositing. |
| UI/system state | Chưa làm asset cho loading, error, navigation, button, empty state, modal hoặc UI chrome. Chỉ làm domain asset phục vụ story, scene, learning và off-screen activity. |
| Backend boundary | Backend chỉ resolve và emit `assetId`, variant, layer/mask references và render intent; không nhúng SVG markup, không import PixiJS. |
| Tính trung thực | Original child drawing vẫn là source identity và không bị asset trang trí thay thế. |

## 2. Snapshot coverage của catalog hiện tại

Số liệu được đọc trực tiếp từ các file source hiện tại và được lưu lại trong `PIXI_ASSET_COVERAGE_TARGET.json`.

| Nguồn | Số lượng | Ý nghĩa |
|---|---:|---|
| MVP activities | 100 | Tập activity bắt buộc phải có coverage row và asset resolution path. |
| MVP material-group instances | 236 | Số group reference trong 100 activity; một activity có thể cần 1–4 group. |
| MVP unique material option IDs | 380 | Các token vật liệu/đồ thay thế cần được resolve về asset family hoặc một loại non-visual được khai báo. |
| Golden activities | 20 | Tập reviewed để regression/hardening, không phải toàn bộ catalog. |
| Golden material groups | 20 | Group reviewed tương ứng golden subset. |
| Golden material options | 40 | 20 primary + 20 household substitute. |
| Learning objectives | 20 | Metadata domain; không biến mỗi objective thành một asset riêng một cách máy móc. |

Phân bố 100 activity theo area hiện tại:

| Area | Activity |
|---|---:|
| `movement` | 5 |
| `sensorial` | 13 |
| `language` | 15 |
| `practical_life` | 21 |
| `mathematics` | 20 |
| `cosmic_education` | 4 |
| `science` | 13 |
| `cultural_studies` | 4 |
| `social_studies` | 5 |

### 2.1 Nguồn dữ liệu chuẩn

Asset coverage phải được dựng từ các file sau, không hard-code danh sách activity trong backend:

1. `data/activity-catalog/mvp/activities.v1.json` — authority cho 100 activity, area, material references, objective và safety.
2. `data/activity-catalog/golden/v1/activities.v2.json` — reviewed subset để kiểm tra chất lượng.
3. `data/activity-catalog/golden/v1/material-registry.v1.json` — reviewed material contract hiện có.
4. `data/activity-catalog/mvp/learning-objectives.v1.json` — objective metadata.

Khi catalog thay đổi, coverage snapshot phải được regenerate và review lại; không silently giữ manifest cũ.

## 3. Mục tiêu kiến trúc

Mục tiêu không phải là tạo 380 hình khác nhau. Mục tiêu là:

```text
100 activities
  -> 236 material-group instances
    -> 380 material option tokens
      -> shared semantic asset families
        -> approved SVG/layer/crop/mask variants
          -> backend render intents
            -> future PixiJS loader
```

Một asset family có thể phục vụ nhiều activity, nhiều age band và cả primary/substitute variant khi hình thái trực quan tương đương. Việc reuse phải được khai báo trong mapping, không suy luận bằng tên file gần giống.

### 3.1 Ba lớp identity

Mỗi asset entry phân biệt ba identity sau:

- `semanticId`: ý nghĩa domain, ví dụ `material.low_tray` hoặc `living.butterfly`.
- `assetId`: file/version cụ thể được backend tham chiếu, ví dụ `pixi.domain.material.low_tray.v1`.
- `sourceArtifactId`: nguồn gốc/biên bản/provenance của SVG; không dùng `assetId` để thay thế provenance.

Điều này cho phép đổi artwork mà không đổi contract semantic, đồng thời giữ được lịch sử và checksum của file cũ.

## 4. Taxonomy asset bắt buộc

Taxonomy dưới đây là domain taxonomy, không phải UI taxonomy.

### 4.1 Shared context và scene primitives

- `scene.nature`: mặt trời, mây, cỏ, cây, đất, nước, đá, nền trời.
- `scene.plant`: hoa, lá, thân cây, hạt, quả và các phần thực vật cần tách lớp.
- `scene.animal`: côn trùng, chim, cá, động vật nuôi và các silhouette liên quan.
- `scene.weather`: nắng, mưa, gió, bóng và dấu hiệu thời tiết đơn giản.
- `scene.geometry`: chấm, đường, vòng, khối, pattern, footprint và path dùng để minh họa thao tác.

### 4.2 Material và household primitives

- `material.container`: khay, giỏ, hộp, bát, cốc, lọ, túi/hộp an toàn.
- `material.textile`: khăn, vải, dây/ribbon được phép, miếng lót, vật mềm.
- `material.object`: bóng, vòng, khối, que, thẻ, nút lớn, đồ vật quen thuộc.
- `material.tool`: thìa, kẹp, phễu, cọ, bút, kéo an toàn, dụng cụ xúc/rót.
- `material.natural`: lá, hoa, hạt, sỏi, vỏ, đất, nước và vật tự nhiên có kiểm soát.
- `material.paper`: giấy, thẻ, tranh, nhãn, bảng, khung và surface để đặt vật.
- `material.measurement`: số lượng, thanh, chuỗi, thước, đồng hồ và token đo lường.

### 4.3 Learning subject primitives

- `learning.language`: picture cards, letter/word token, sound cue, story object.
- `learning.mathematics`: countable objects, numeral token, quantity group, pattern, shape.
- `learning.science`: plant/animal parts, experiment container, observation marker, state change.
- `learning.culture`: map/landmark/cultural object ở mức minh họa domain, không phải UI.
- `learning.practical_life`: pour, scoop, transfer, fold, wash, sort, open/close và action affordance.
- `learning.movement`: trajectory, balance, reach, grasp, slow-motion path và safe boundary.
- `learning.social`: turn-taking, cooperation, emotion/interaction cue được kiểm soát.

### 4.4 Workflow domain overlays

Đây là overlay cho context của activity, không phải UI chrome:

- `domain.learning_goal` — objective cue.
- `domain.adult_guide` — adult/guide participation cue.
- `domain.safety` — safety cue gắn với activity.
- `domain.feedback` — observation/feedback cue.
- `domain.time` — duration/time cue khi activity contract yêu cầu.

Các overlay này được giới hạn trong render intent và không được biến thành screen/control asset.

## 5. Asset contract cho từng semantic family

Mỗi family phải có một manifest entry có tối thiểu:

```json
{
  "semanticId": "material.low_tray",
  "assetId": "pixi.domain.material.low_tray.v1",
  "category": "material.container",
  "sourcePath": "assets/generated/pixi/domain/material/container/low-tray/base.svg",
  "variants": {
    "base": ".../base.svg",
    "transparent": ".../transparent.svg",
    "crop": ".../crop.svg",
    "mask": ".../mask.svg"
  },
  "layers": ["body", "rim", "contents-shadow"],
  "motionAnchors": ["center", "grasp-left", "grasp-right"],
  "allowedUses": ["activity_material", "scene_context"],
  "sourcePolicy": "HAND_AUTHORED_VECTOR",
  "reviewStatus": "GENERATED_PENDING_REVIEW",
  "provenance": {
    "authoredFor": "FEAT-020",
    "derivedFrom": [],
    "sha256": "..."
  }
}
```

`sha256` chỉ được điền sau khi file thật tồn tại. Không được dùng placeholder trong manifest đã được backend load.

### 5.1 Các file variant bắt buộc

Không phải semantic nào cũng cần mọi variant, nhưng manifest phải khai báo rõ `requiredVariants`:

- `base.svg`: artwork nguyên vẹn, dùng cho static reference.
- `transparent.svg`: không có background rectangle; dùng khi đặt lên scene khác.
- `crop.svg`: crop theo bounding box semantic; không cắt mất vùng safe margin.
- `mask.svg`: silhouette/alpha mask đơn sắc, không có decoration; dùng cho reveal/clip/compositing.
- `layers/*.svg`: các part độc lập có thể animate hoặc hide/show.
- `variants/*.svg`: chỉ dành cho biến thể semantic thật sự khác nhau, ví dụ primary/substitute hoặc state domain hợp lệ.

PNG chỉ là derivative export khi pipeline PixiJS cần raster fallback; SVG source vẫn là authority. Không tạo raster AI ở runtime.

### 5.2 Quy tắc SVG để sẵn sàng animation

- Có `viewBox` ổn định và không phụ thuộc vào external CSS/font/image.
- Không dùng external reference, remote URL hoặc embedded secret.
- Mỗi layer có ID ổn định, không đổi ngẫu nhiên giữa các lần export.
- Origin/anchor được ghi trong manifest; không suy luận từ pixel tại runtime.
- Crop không làm mất vùng chuyển động dự kiến; mask phải có margin được ghi rõ.
- Nét và màu giữ được khi scale trong dải viewport dự kiến.
- Không đặt chữ, nút, frame, spinner hoặc icon UI vào domain asset.
- Artwork trang trí không được mô phỏng lại hay thay thế nét vẽ gốc của trẻ.

## 6. Chiến lược coverage toàn bộ catalog

### 6.1 Activity coverage row

Mỗi `ACT-*` phải có một row trong coverage matrix với:

- `activityId`, `version`, `ageBand`, `area`;
- danh sách `materialGroupIds` lấy trực tiếp từ activity catalog;
- danh sách `materialOptionIds` từ tất cả `any_of`;
- `requiredSemanticIds` cho context/action/learning goal;
- `assetResolutionPolicy` (`PRIMARY`, `APPROVED_SUBSTITUTE`, `NON_VISUAL`, hoặc `MISSING`);
- `reviewStatus` và evidence path.

Không được coi một activity là covered chỉ vì có một asset chung như `learning-goal` hoặc `adult-guide`.

### 6.2 Material coverage row

Mỗi 236 material-group instance phải resolve được toàn bộ `any_of` token của nó:

- token primary map tới semantic family chính;
- token substitute map tới cùng family nếu có thể, hoặc family variant có `substituteFor` rõ ràng;
- token không biểu diễn trực quan phải khai báo `NON_VISUAL` và lý do, không tạo hình giả;
- token chưa có artwork là `MISSING`, làm fail coverage gate trước khi coi asset library hoàn tất.

`golden/v1/material-registry.v1.json` chỉ xác nhận 20 reviewed groups/40 options. Nó không được dùng như lý do để bỏ qua 216 group instance còn lại trong MVP catalog.

### 6.3 Shared asset family rule

Asset family được dùng chung khi thỏa cả ba điều kiện:

1. Cùng semantic vật lý hoặc cùng affordance trực quan.
2. Không làm mất distinction cần thiết cho safety, age band hoặc activity instruction.
3. Có mapping rõ từ catalog token tới `semanticId` và variant.

Nếu một asset chỉ “trông gần giống” nhưng làm sai material, safety hoặc action, phải tách family/variant thay vì reuse.

## 7. Những deliverable cần tạo ở các bước sau

Bước cập nhật plan này **chưa tạo các deliverable implementation**. Sau khi feature được APPROVED, thứ tự tạo sẽ là:

1. `assets/generated/pixi/domain/` — SVG hand-authored theo taxonomy.
2. `assets/generated/pixi/PIXI_ASSET_LIBRARY_MANIFEST.v1.json` — asset identity, variants, layers, provenance.
3. `assets/generated/pixi/PIXI_ASSET_COVERAGE.v1.json` — 100 activity rows, 236 group references, 380 option mappings.
4. `assets/generated/pixi/PIXI_MATERIAL_ASSET_MAP.v1.json` — canonical shared-family mapping.
5. `assets/generated/pixi/PIXI_LAYER_MANIFEST.v1.json` — layer IDs, anchors, masks, crop bounds và motion readiness.
6. `assets/REVIEW.md` và `assets/generated/pixi/REVIEW.md` — provenance, visual review checklist và evidence.
7. Chỉ sau visual approval mới copy/reference vào `assets/approved/` và `assets/applied/` theo harness.

Các manifest trên là versioned contracts. Backend không scan thư mục rồi tự chọn file gần đúng.

## 8. Integration boundary với backend workflow

Backend hiện tại chỉ cần nối ở mức contract:

```text
activity selector
  -> selected activity + material choice
  -> asset resolver
  -> asset IDs + variants + render intents
  -> story/scene/art/activity handoff manifest
```

Asset resolver phải:

- nhận `activityId`, `materialOptionId`, age band và render purpose;
- trả về canonical `assetId`, variant, layer references, mask/crop references và provenance;
- giữ nguyên original child-art artifact ID/SHA-256;
- không load PixiJS và không generate asset;
- trả `ASSET_CATALOG_MISS` nếu thiếu mapping hoặc file/checksum không hợp lệ;
- không tự động chọn primary thay cho substitute hoặc ngược lại khi selection contract chưa cho phép.

Render intent có thể nêu `static`, `reveal`, `float`, `trace`, `highlight`, `group`, nhưng đây chỉ là intent data. Việc thực thi animation thuộc PixiJS ở phase sau.

## 9. Review và governance

Asset lifecycle:

```text
HAND_AUTHORED_SOURCE
  -> assets/generated/
  -> GENERATED_PENDING_REVIEW
  -> visual/contract/provenance review
  -> assets/approved/
  -> assets/applied/ (chỉ khi có consumer đã approved)
```

Review bắt buộc:

- visual: silhouette, màu, crop, transparent background, layer separation;
- domain: semantic đúng với material/activity;
- safety: không tạo cue trái với safety record;
- animation readiness: layer/mask/anchor có thể dùng mà không redraw source;
- provenance: source path, authoring method, checksum, review evidence;
- coverage: không còn `MISSING` ngoài các row được phê duyệt rõ là `NON_VISUAL`.

Không commit credential, child data thật, provider token, hoặc asset có nguồn không truy vết được.

## 10. Milestones thực hiện sau khi được approve

### M0 — Catalog audit

- Freeze snapshot counts.
- Sinh coverage target từ catalog.
- Xác định mọi `materialOptionId` chưa có semantic family.
- Không tạo file artwork ở milestone này.

### M1 — Contract và family taxonomy

- Chốt schema manifest/coverage/material map/layer manifest.
- Chốt naming, anchor, variant và missing policy.
- Tách domain asset khỏi UI asset.

### M2 — Shared family library

- Tạo common scene, material, learning và domain overlay family.
- Mỗi family có base/transparent/crop/mask/layers theo requirement.
- Ghi provenance ngay khi tạo, không gom evidence sau cùng.

### M3 — Catalog closure

- Map đủ 100 activity.
- Resolve đủ 236 group instance và 380 option ID.
- Kiểm tra golden subset 20/20/40 trước rồi chạy toàn bộ catalog.
- Dừng nếu còn `MISSING` hoặc mapping ambiguous.

### M4 — Review và approval

- Render contact sheet/asset audit nếu cần.
- Visual/domain/safety/provenance review.
- Chuyển approved/applied theo harness, không bypass review.

### M5 — Backend contract integration

- Backend load manifest đã approved.
- Emit asset selection/render intents trong workflow E2E.
- Test missing, substitute, primary, layer/mask và original-art preservation.
- Vẫn chưa cần load PixiJS renderer hoặc nối UI.

## 11. Acceptance criteria của asset plan

Plan được coi là đủ để bắt đầu implementation khi và chỉ khi:

- [ ] Có một source-of-truth duy nhất cho 100 activity coverage.
- [ ] Có row cho toàn bộ 236 material-group instance.
- [ ] Có mapping hoặc explicit `NON_VISUAL` cho toàn bộ 380 unique material option ID.
- [ ] Có mapping riêng cho golden subset 20 activity / 20 group / 40 option.
- [ ] Shared family reuse được khai báo bằng contract, không dựa vào filename convention.
- [ ] Mọi asset cần animation có layer/crop/mask/transparent requirement rõ ràng.
- [ ] Asset source là hand-authored vector/SVG; không có runtime AI generation.
- [ ] Original child drawing vẫn immutable và được reference bằng artifact ID/SHA-256.
- [ ] Không có UI/system-state asset trong domain library.
- [ ] Backend chỉ emit IDs/intents và fail rõ bằng `ASSET_CATALOG_MISS` khi thiếu.
- [ ] Có provenance/review path theo harness trước khi approved/applied.
- [ ] Coverage manifest có thể regenerate khi catalog version thay đổi.

## 12. Kết luận phạm vi

Gói 12 asset hiện tại nên được giữ để smoke test, nhưng target production-like của FEAT-020 là một **shared domain asset library có coverage toàn catalog**, không phải 12 file minh họa. Việc bổ sung asset sẽ được thực hiện sau khi plan này và feature approval được chấp nhận; trong bước backend demo đầu tiên, workflow chỉ cần emit asset IDs/render intents theo contract và chưa cần chạy PixiJS.
