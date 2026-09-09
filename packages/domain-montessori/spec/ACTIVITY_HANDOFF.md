# ActivityHandoff v1 specification

ActivityHandoff is the deterministic contract that ends screen use and begins the approved physical Montessori task.

## Required fields

| Field | Requirement |
|---|---|
| `activity_id`, `activity_version` | Exact activity approved at Gate B |
| `learning_objective_id`, `learning_objective_version` | Exact objective approved at Gate B |
| `task_variant_id` | Optional; must explicitly map to the approved activity/version |
| `locale` | `vi-VN` for the current catalog |
| `cta_vi` | One or two short sentences connecting digital content to the physical task |
| `materials_vi` | Required materials and allowed home substitutes |
| `setup_steps_vi` | Adult preparation steps |
| `activity_steps_vi` | Short ordered physical actions |
| `safety_supervision_vi` | Hazards, stop conditions, and adult-only instructions |
| `screen_exit_policy` | Must stop/close media; no autoplay into another entertainment clip |
| `completion_evidence` | Adult-observed attempted/completed/with-help outcome; never inferred from watch time alone |

## Example

```json
{
  "activity_id": "ACT-0023",
  "activity_version": 1,
  "learning_objective_id": "OBJ_NUMBER_QUANTITY_PLACE_VALUE",
  "learning_objective_version": 1,
  "task_variant_id": null,
  "locale": "vi-VN",
  "cta_vi": "Bây giờ mình cùng mang các con số ra bàn và thử bằng tay nhé.",
  "materials_vi": ["chữ số nhám"],
  "setup_steps_vi": ["Đặt vật liệu trên thảm làm việc."],
  "activity_steps_vi": ["Tô theo nét chữ số.", "Gọi tên chữ số."],
  "safety_supervision_vi": ["Người lớn ở gần và dừng hoạt động nếu vật liệu hỏng."],
  "screen_exit_policy": "STOP_MEDIA_AND_HANDOFF",
  "completion_evidence": "ADULT_OBSERVATION_REQUIRED"
}
```
