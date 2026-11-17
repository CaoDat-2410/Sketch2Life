"""Model-facing text for choosing among a bounded, approved topic-asset shortlist."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from sketch2life.contracts.schemas.pixi_topic_asset_selection import (
    TopicAssetCandidateContextV1,
)

_PROMPT = (
    "Bạn chỉ xếp hạng asset trong danh sách ứng viên được cung cấp. Chủ đề đã được người lớn "
    "xác nhận là nguồn sự thật; không sửa nghĩa, không suy đoán thêm từ trẻ, và không tạo asset "
    "hoặc ID mới. Đây chỉ là dữ liệu văn bản; không có ảnh gốc của trẻ trong yêu cầu này. "
    "Chọn tối đa 4 asset thật sự phù hợp dựa trên nhãn, mô tả hình, tag, vai trò và mục "
    "confusableWith. Chỉ trả JSON đúng schema {assetIds: string[], noMatch: boolean}; "
    "mọi ID phải có trong candidateAssets. Nếu không ứng viên nào phù hợp, trả "
    '{"assetIds":[],"noMatch":true}. Không thêm lý do hay trường khác.'
)


def build_topic_asset_model_input(
    context: TopicAssetCandidateContextV1,
) -> dict[str, Any]:
    """Create a compact, privacy-minimized payload; never include media refs or file paths."""
    if context.status != "READY":
        raise ValueError("model input requires a ready candidate context")
    payload = {
        "confirmedTopicLabels": list(context.confirmed_topic_labels),
        "confirmedTopicTags": list(context.confirmed_topic_tags),
        "candidateAssets": [
            candidate.model_dump(mode="json", by_alias=True) for candidate in context.candidates
        ],
    }
    return {
        "protocolId": topic_asset_prompt_protocol_id(),
        "system": _PROMPT,
        "userJson": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    }


def topic_asset_prompt_protocol_id() -> str:
    return "fe028-topic-asset-ranker-v1"


def topic_asset_prompt_sha256() -> str:
    return sha256(_PROMPT.encode("utf-8")).hexdigest()


__all__ = [
    "build_topic_asset_model_input",
    "topic_asset_prompt_protocol_id",
    "topic_asset_prompt_sha256",
]
