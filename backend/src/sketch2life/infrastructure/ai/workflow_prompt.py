"""Reviewed Vietnamese structured-output prompt for the FEAT-020 real VLM call."""

from __future__ import annotations

from hashlib import sha256

_PROMPT = "\n".join(
    (
        "Trả về đúng một JSON object compact và không có văn bản nào khác. "
        "Chỉ mô tả nội dung nhìn thấy trực tiếp trong tranh; không suy đoán tính cách, "
        "cảm xúc, ý định, chẩn đoán, năng lực, ý nghĩa biểu tượng hay trạng thái tâm lý của trẻ.",
        "Root keys bắt buộc và duy nhất: entities, actions, relations, themes, "
        "ambiguous_regions. Tất cả đều là array; dùng [] nếu không có. Tối đa 5 entities, "
        "2 actions, 3 relations, 2 themes và 2 ambiguous_regions; ưu tiên ít nhưng chắc chắn.",
        "Nhãn phải bằng tiếng Việt, ngắn gọn 1-5 từ, giữ dấu tiếng Việt khi có thể. "
        'Mỗi text field có dạng {"value":"...","language":{"status":"DECLARED",'
        '"tags":["vi"]}}. Mỗi observation_id là duy nhất, chữ thường, không dấu cách, '
        "chỉ gồm a-z, 0-9 và dấu gạch ngang.",
        "Entity có các key observation_id,label,confidence; confidence là số từ 0 đến 1 "
        "hoặc null. Action có observation_id,label,actor_ref,object_ref,confidence; "
        "actor_ref và object_ref là entity ID hoặc null.",
        "Relation có observation_id,predicate,subject_ref,object_ref,confidence; các ref "
        "phải trỏ tới entity/action ID khác nhau. Theme có observation_id,label,evidence_refs,"
        "confidence; evidence_refs phải trỏ tới entity/action/relation ID.",
        "Ambiguous region có observation_id,note với note là text field như trên.",
        "Không thêm key ngoài schema, không dùng markdown fence, không dùng comment, không dùng "
        "bbox/geometry/metadata. Nếu không chắc, bỏ qua quan sát thay vì bịa.",
        "Với vật thể có thể đếm được, dùng nhãn tiếng Việt tự nhiên như “một bông hoa” "
        "chỉ khi số lượng thực sự nhìn thấy.",
    )
)


def workflow_prompt_text() -> str:
    return _PROMPT


def workflow_prompt_protocol_id() -> str:
    return "fe020-vietnamese-observation-v1"


def workflow_prompt_sha256() -> str:
    return sha256(_PROMPT.encode("utf-8")).hexdigest()


__all__ = ["workflow_prompt_protocol_id", "workflow_prompt_sha256", "workflow_prompt_text"]
