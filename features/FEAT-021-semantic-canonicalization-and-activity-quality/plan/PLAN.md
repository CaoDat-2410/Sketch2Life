# FEAT-021 — Semantic Canonicalization and Activity Quality

## 1. Trạng thái và mục tiêu

- **Trạng thái:** `AWAITING_APPROVAL`
- **Loại:** backend contract, semantic decisioning, activity catalog và evaluation
- **Feature trước:** `FEAT-020-backend-ai-workflow-demo`
- **Phạm vi runtime:** backend-only; acceptance chạy real ASR/VLM trên Lightning Studio
- **Không triển khai trong feature này:** UI, PixiJS runtime rendering, video generation, human gate production, caregiver persistence

### Mục tiêu chính

Sửa toàn bộ các lỗi semantic và contract đã được audit:

1. Đưa V2 thành canonical source of truth.
2. Bảo đảm tất cả age band sử dụng cùng một scene understanding.
3. Ưu tiên concept mà trẻ trực tiếp kể bằng narration khi ASR đạt ngưỡng tin cậy.
4. Tách điểm semantic match, child-interest alignment, age fit và safety.
5. Loại bỏ mismatch giữa activity ID/version ở các contract lồng nhau.
6. Làm cho V1 chỉ còn là compatibility adapter được derive từ V2.
7. Bắt buộc activity cuối cùng phải tồn tại trong catalog đã duyệt.
8. Trả về trạng thái unavailable rõ ràng khi một age band không có activity hợp lệ.
9. Cải thiện objective, complexity, duration và supervision theo từng age band.
10. Mở rộng catalog từ baseline hiện tại lên khoảng 200–250 activity/approved variant theo coverage, không tạo activity mới trong runtime bằng AI.
11. Tạo evaluation/test suite đủ để chứng minh recommendation không chỉ đúng trên một sample.

## 2. Các quyết định đã chốt

| Quyết định | Kết luận |
|---|---|
| Canonical contract | V2 là canonical public/backend contract |
| V1 | Chỉ tồn tại dưới dạng compatibility adapter |
| ASR/VLM conflict | Ưu tiên narration của trẻ khi ASR đạt confidence threshold |
| Age không có activity | Trả `UNAVAILABLE_AGE_BAND`, không fallback im lặng |
| AI tạo activity | Không được tạo activity ngoài catalog |
| Unit tests | Được dùng provider doubles để test logic/contract |
| Acceptance | Bắt buộc real ASR/VLM trên Lightning Studio |
| Pixi/video/human/feedback thật | Tách thành feature sau |
| Catalog target | Khoảng 200–250 activity/variant, đo bằng coverage chứ không chỉ số lượng |

## 3. Tình trạng baseline

Baseline hiện tại đã có:

- CLI `python -m sketch2life.workflow_demo` chạy được real adapter.
- V2 semantic personalization và scene-understanding layer.
- Age matrix `0-3`, `3-6`, `6-9`, `9-12`.
- Activity semantic catalog và activity handoff.
- Art render intent giữ nguyên original image.
- Video handoff ở trạng thái `DEFERRED`.
- Real AI E2E test opt-in bằng `SKETCH2LIFE_RUN_REAL_AI_E2E=1`.

Các lỗi/gap cần xử lý:

- Selected activity có thể lấy secondary visual concept thay vì primary child interest.
- `semantic_relevance` đang gánh quá nhiều ý nghĩa.
- V2 và legacy representation có thể chứa hai semantic truth khác nhau.
- Activity version có thể mismatch giữa `experience_spec` và `semantic_match`.
- Objective theo age còn generic ở một số trường hợp.
- Catalog chưa đủ candidate để recommendation có diversity.
- Chưa có explicit invariant cho child-interest priority, V1/V2 parity và activity identity.
- Một sample chạy thành công chưa chứng minh coverage trên nhiều scene.

## 4. Kiến trúc mục tiêu

```text
Input image + narration.wav
            |
            v
    Media validation / provenance
            |
            v
       ASR transcript --------+
                              |
       VLM observations ------+----> Scene fusion
                                     |
                                     v
                         ConfirmedSceneUnderstandingV2
                                     |
                                     +--> primary child-interest concept
                                     +--> secondary visual concepts
                                     +--> evidence/conflicts/confidence
                                     |
                                     v
                         Age-specific candidate ranking
                                     |
                                     v
                            Catalog policy gate
                                     |
                  +------------------+------------------+
                  |                  |                  |
                  v                  v                  v
             Activity V2        Story/scene       Art render intent
                  |                                     |
                  +------------------+------------------+
                                     |
                                     v
                             Deferred video handoff
                                     |
                                     v
                              Backend V2 result
                                     |
                                     v
                             Optional V1 adapter
```

### Nguyên tắc dependency

```text
interfaces/adapters -> application -> domain/contracts
infrastructure implements ports
catalog/policy không phụ thuộc UI hoặc provider cụ thể
```

AI chỉ cung cấp observation, transcript và candidate suggestion. Quyết định activity cuối cùng phải đi qua domain policy và catalog gate.

## 5. Workstream W0 — Feature setup và governance

### Công việc

1. Tạo feature folder:

   ```text
   features/FEAT-021-semantic-canonicalization-and-activity-quality/
   ├── plan/PLAN.md
   ├── approvals/TASK_APPROVAL.md
   ├── decisions/
   ├── evidence/
   └── tests/
   ```

2. Tạo ADR cho:
   - V2 canonical contract;
   - V1 compatibility window;
   - ASR-first child-interest policy;
   - catalog-only activity policy;
   - unavailable-age behavior;
   - activity family/variant/version model.

3. Ghi rõ feature không bao gồm PixiJS runtime, video generation và production human gates.

### Deliverables

- ADR được approve.
- `TASK_APPROVAL.md` chuyển từ `AWAITING_APPROVAL` sang approved trước implementation.
- Baseline output và baseline test result được lưu trong feature evidence.

## 6. Workstream W1 — Canonical semantic contract

### Mục tiêu

Tạo một representation duy nhất cho scene, concept, evidence và selected activity.

### Schema dự kiến

#### `ConceptEvidenceV2`

```json
{
  "source": "ASR",
  "reference": "asr:phrase-1",
  "label_vi": "con bướm",
  "confidence": 0.98,
  "support_type": "DIRECT_CHILD_NARRATION"
}
```

#### `SelectedConceptV2`

```json
{
  "concept_id": "ANIMAL_BUTTERFLY",
  "concept_role": "PRIMARY_CHILD_INTEREST",
  "evidence": [],
  "selection_rationale_vi": "Trẻ trực tiếp kể về con bướm và VLM xác nhận vật thể",
  "concept_match_confidence": 0.96,
  "child_interest_alignment": 1.0
}
```

#### `PersonalizationScoreBreakdownV2`

```json
{
  "concept_match_confidence": 0.96,
  "child_interest_alignment": 1.0,
  "age_fit_score": 0.91,
  "activity_safety_score": 1.0,
  "catalog_quality_score": 0.85,
  "overall_personalization_score": 0.94
}
```

#### `ActivityIdentityV2`

```json
{
  "activity_family_id": "ACT-FAMILY-PLANT-CARE",
  "activity_id": "ACT-0034",
  "activity_version": 2,
  "variant_id": "ACT-0034-3-6-NEARBY",
  "catalog_revision": "catalog-2026-09"
}
```

### Quy tắc

- `scene_understanding_id` được tạo một lần cho mỗi workflow run.
- Tất cả age band phải trỏ về cùng `scene_understanding_id`.
- `selected_concept` là dữ liệu canonical của age band.
- Activity, story, art intent và video handoff đều nhận selected concept từ cùng một object.
- Không cho legacy field ghi đè V2.
- Tất cả ID/version phải có provenance và catalog revision.

### Deliverables

- Schema mới hoặc schema được chuẩn hóa.
- Mapper từ internal domain model sang V2.
- Validation invariant.
- Contract round-trip tests.

## 7. Workstream W2 — Scene fusion và child-interest ranking

### Mục tiêu

Tách rõ việc hiểu tranh khỏi việc chọn activity.

### Pipeline

```text
ASR transcript
    -> phrase extraction
    -> child-interest concepts

VLM observation
    -> object/action/theme extraction
    -> visual concepts

ASR + VLM
    -> concept normalization
    -> evidence reconciliation
    -> primary/secondary roles
```

### Policy

1. Nếu ASR có phrase rõ và confidence đạt threshold:
   - concept được ASR nhắc đến trở thành primary child-interest candidate;
   - VLM chỉ dùng để xác nhận hoặc đánh dấu conflict.

2. Nếu ASR không có speech hoặc confidence thấp:
   - VLM được phép chọn visual primary concept;
   - output phải ghi `VLM_ONLY`.

3. Nếu ASR và VLM conflict:
   - không discard evidence;
   - ghi `ASR_VLM_CONFLICT`;
   - dùng policy deterministic để quyết định;
   - warning phải xuất hiện trong result.

4. Background-only concept không được vượt primary child-interest nếu không có:
   - activity safety reason;
   - age-fit reason;
   - catalog availability reason;
   - explicit selection rationale.

### Không được làm

- Không dùng token đơn lẻ làm semantic truth.
- Không để mỗi age band gọi VLM/fusion riêng để tự xác định scene.
- Không dùng random để che việc thiếu candidate.

### Deliverables

- Fusion policy version.
- Concept role assignment.
- Explainable ranking rationale.
- Conflict/error codes.
- Unit tests cho ASR/VLM agreement và conflict.

## 8. Workstream W3 — Activity catalog model và quality gate

### Catalog model

Mỗi activity/variant phải khai báo:

```text
activity_family_id
activity_id
activity_version
variant_id
supported_concepts
supported_age_bands
learning_objective_by_age
duration_by_age
complexity_by_age
supervision_by_age
materials
home_substitutes
context
safety_constraints
prerequisites
production_eligibility
owner_review_status
semantic_profile_version
```

### Core/variant model

Không cần tạo 250 activity hoàn toàn độc lập. Cho phép:

```text
Activity Core
    + Age Variant
    + Material Variant
    + Challenge Variant
```

Ví dụ:

```text
PLANT_OBSERVATION_CORE
├── 3-6: gọi tên bộ phận cây
├── 6-9: vẽ và gắn nhãn
└── 9-12: lập giả thuyết và observation log
```

Mỗi approved variant vẫn phải có identity và version riêng để không nhầm lẫn khi handoff.

### Quality gate

Activity chỉ được chọn nếu:

```text
catalog tồn tại
activity owner-reviewed
age phù hợp
safety pass
prerequisite pass
material pass hoặc có substitute
production eligibility phù hợp với mode
```

AI được phép gợi ý candidate ID nhưng không được tạo record mới trong runtime.

## 9. Workstream W4 — Catalog expansion và coverage

### Baseline

- Giữ nguyên catalog hiện tại làm baseline.
- Không xóa activity cũ chỉ vì chưa đủ coverage.
- Đánh dấu activity quality/eligibility rõ ràng.

### Coverage dimensions

```text
Age:
  0-3, 3-6, 6-9, 9-12

Concept family:
  animal, plant, nature, movement, color, shape,
  space, sound, number, people, vehicle, weather, water

Learning objective:
  practical life, sensory, science, math, language, cosmic

Difficulty:
  foundation, concrete, standard, extension

Context:
  indoor, outdoor

Supervision:
  direct, nearby
```

### Target

- Tổng số: khoảng 200–250 activity/approved variant.
- Concept phổ biến: tối thiểu 3 candidate hợp lệ mỗi age band.
- Concept rất phổ biến: 5–8 candidate.
- Ít nhất 90% scene phổ biến có 3 candidate sau age/safety/prerequisite filtering.
- Một activity không được chiếm phần lớn recommendation trong evaluation set.

### Ưu tiên bổ sung

```text
con vật
cây/hoa
gia đình/con người
phương tiện
nhà cửa
thời tiết
Mặt Trời/Mặt Trăng
nước
màu sắc
hình dạng
chuyển động
số lượng
```

### Quy trình mở rộng

1. Chạy evaluation set 100–300 scene.
2. Đo `NO_MATCH`, `single_candidate`, concentration và unavailable age.
3. Group gap theo concept × age × objective.
4. Author activity/variant mới ngoài runtime.
5. Owner review và safety review.
6. Cập nhật catalog revision.
7. Chạy lại coverage report.
8. Chỉ publish activity đã đạt eligibility.

## 10. Workstream W5 — Age adaptation

### Required fields theo age

```text
objective_vi
duration_minutes
complexity
supervision
materials
home_substitutes
success_observation
extension_or_simplification
```

### Policy

#### 0–3

- Foundation.
- Direct supervision.
- 4–7 phút.
- Một chuỗi thao tác ngắn.
- Không dùng activity cần abstraction hoặc nhiều bước nguy hiểm.

#### 3–6

- Foundation/nearby supervision.
- 8–12 phút.
- Chuỗi thao tác có thứ tự.
- Bắt đầu có cleanup/independence.

#### 6–9

- Concrete/standard.
- 20–30 phút.
- Phân loại, so sánh, đo lường, quan sát có ghi nhận.

#### 9–12

- Abstract/extension.
- 25–40 phút.
- Giải thích quan hệ, mô hình hóa, hypothesis, giới hạn mô hình.

### Acceptance

Objective phải khác nhau có nghĩa, không chỉ khác string chứa age band.

## 11. Workstream W6 — V1/V2 migration

### Runtime behavior

```text
--contract-version v2  -> canonical V2
--contract-version v1  -> V1 adapter từ V2
```

V2 mặc định không được tạo bằng cách ghép một V1 result cũ rồi bọc thêm field mới.

### Migration rules

- V1 không được chọn activity riêng.
- V1 không được tạo primary anchor riêng.
- V1 chỉ map từ selected concept/activity của V2.
- Legacy fields trong V2 chỉ còn ở debug/migration mode.
- Public mobile response tương lai chỉ dùng V2.

### Deliverables

- V1 adapter.
- Deprecation note.
- V1/V2 parity test.
- Consumer migration checklist.

## 12. Workstream W7 — Explicit unavailable và partial result

### States

```text
SUCCEEDED
UNAVAILABLE
FAILED
PARTIAL_SUCCESS
```

`UNAVAILABLE` dùng khi workflow hiểu được scene nhưng catalog không có activity hợp lệ cho age đó.

`FAILED` dùng khi ASR/VLM/runtime/provider bị lỗi.

Không được biến provider failure thành unavailable hoặc safe fallback.

### Required unavailable details

```text
age_band
candidate_count_before_filter
candidate_count_after_age_filter
candidate_count_after_safety_filter
reason_code
missing_coverage
```

## 13. Workstream W8 — Test strategy

### Contract tests

- Schema round-trip.
- Unknown/duplicate fields.
- Activity identity/version parity.
- V1 adapter parity.
- Canonical scene ID consistency.
- Unavailable contract.

### Semantic unit tests

- ASR/VLM agree on butterfly.
- ASR primary, VLM secondary.
- VLM-only input.
- ASR/VLM conflict.
- Background object không override child interest.
- Empty/low-confidence ASR.

### Activity unit tests

- Catalog-only selection.
- AI candidate ngoài catalog bị reject.
- Age mismatch bị reject.
- Safety mismatch bị reject.
- Prerequisite mismatch bị reject.
- Không candidate trả unavailable.
- Activity version mismatch bị reject.

### Integration tests

Assert cùng selected concept được truyền qua:

```text
scene understanding
→ activity handoff
→ story scene
→ art render intent
→ video handoff
→ feedback context
```

### Evaluation tests

Bộ test gồm các nhóm:

- animal-only;
- plant/flower;
- people/family;
- vehicle/house;
- weather/space;
- multiple competing concepts;
- narration/image conflict;
- no speech;
- unclear image;
- no eligible catalog activity.

Unit/evaluation test có thể dùng provider double. Acceptance test không được dùng model output giả.

### Real Lightning E2E

Acceptance phải chạy:

```bash
export SKETCH2LIFE_RUN_REAL_AI_E2E=1
python -m pytest backend/tests/e2e/test_lightning_backend_workflow.py -q \
  -p no:cacheprovider --basetemp=tmp/lightning-e2e
```

Required:

- real Qwen VLM;
- real faster-whisper;
- all four age bands;
- no fallback for eligible sample;
- unavailable state explicit nếu có age không đủ catalog;
- valid manifest hash;
- no activity ID ngoài catalog;
- no V1/V2 mismatch.

## 14. Workstream W9 — Evidence và observability

Evidence lưu trong feature folder, không dùng shared dump:

```text
evidence/
├── baseline/
├── contract/
├── semantic-ranking/
├── catalog-coverage/
├── migration/
├── regression/
└── lightning-real-ai/
```

Mỗi evidence phải ghi:

- commit SHA;
- command;
- environment/model revision nếu cần;
- input artifact hash;
- result summary;
- pass/fail/skip rõ ràng;
- không lưu raw child media hoặc secret.

## 15. Thứ tự implementation

### Milestone M1 — Contract foundation

- W0, W1.
- Canonical V2.
- Activity identity.
- Schema invariants.

### Milestone M2 — Semantic ranking

- W2.
- ASR-first policy.
- Child-interest score.
- Conflict handling.

### Milestone M3 — Activity policy

- W3, W5, W7.
- Catalog-only gate.
- Age objective.
- Explicit unavailable.

### Milestone M4 — Migration

- W6.
- V1 adapter.
- V1/V2 parity tests.

### Milestone M5 — Catalog coverage

- W4.
- Evaluation set.
- Coverage report.
- Bổ sung activity/variant theo gap.

### Milestone M6 — Verification

- W8, W9.
- Full backend tests.
- Security/harness validation.
- Real AI E2E trên Lightning.

Không commit rải rác các thay đổi nhỏ. Sau khi tất cả milestone đạt, tạo một implementation commit/PR coherent; evidence có thể được cập nhật trong cùng commit hoặc một commit verification duy nhất nếu cần.

## 16. Acceptance criteria tổng

### Canonical truth

- [ ] Mỗi run có đúng một `scene_understanding_id`.
- [ ] Tất cả age band dùng cùng scene truth.
- [ ] Activity/story/art/video handoff dùng cùng selected concept.
- [ ] Legacy không thể ghi đè V2.

### Child interest

- [ ] ASR child narration được ưu tiên khi đạt threshold.
- [ ] Có `child_interest_alignment` riêng.
- [ ] Conflict ASR/VLM được ghi rõ.
- [ ] Background-only concept không tự override primary interest.

### Activity identity

- [ ] ID và version nhất quán ở mọi nested contract.
- [ ] Activity ngoài catalog bị reject.
- [ ] Activity chưa owner-review không được production select.

### Age behavior

- [ ] Objective từng age có nội dung cụ thể.
- [ ] Duration/complexity/supervision đúng age.
- [ ] Không có candidate hợp lệ trả `UNAVAILABLE_AGE_BAND`.
- [ ] Không dùng fallback im lặng.

### Catalog

- [ ] Catalog đạt khoảng 200–250 approved activity/variant hoặc có evidence coverage tương đương.
- [ ] Concept phổ biến có ít nhất 3 candidate/age.
- [ ] >=90% scene phổ biến có >=3 candidate sau filtering.
- [ ] Không một activity chiếm áp đảo evaluation set.

### Migration

- [ ] V2 là default.
- [ ] V1 chỉ là adapter.
- [ ] V1/V2 parity test pass.
- [ ] Không còn duplicate semantic decision trong public response.

### Runtime/test

- [ ] Unit, contract, integration test pass.
- [ ] Real AI E2E pass trên Lightning.
- [ ] `validate_repository_security.py` pass.
- [ ] `validate_harness.py` pass.
- [ ] Evidence nằm trong FEAT-021.

## 17. Rủi ro và cách xử lý

| Rủi ro | Cách xử lý |
|---|---|
| ASR sai nhưng vẫn được ưu tiên | Dùng confidence threshold và VLM cross-check |
| Catalog tăng số lượng nhưng chất lượng thấp | Owner review, safety gate, coverage report |
| V1 consumer vẫn phụ thuộc legacy field | Giữ adapter và migration contract test |
| Activity recommendation bị lặp | Candidate diversity metric và concentration report |
| Model output thay đổi giữa lần chạy | Seed/replay cho debug, không claim deterministic model |
| Không đủ activity cho một age | `UNAVAILABLE_AGE_BAND`, không fallback im lặng |
| Payload V2 quá lớn | Tách debug legacy khỏi public response |
| Real AI test tốn GPU/thời gian | Unit doubles + một acceptance E2E thật trên Lightning |

## 18. Điều kiện bắt đầu implementation

Chỉ bắt đầu code sau khi:

1. Plan này được approve.
2. `TASK_APPROVAL.md` có explicit approval.
3. ADR canonical V2/V1 được ghi nhận.
4. Catalog baseline được snapshot/hash.
5. Acceptance test matrix được chốt.
