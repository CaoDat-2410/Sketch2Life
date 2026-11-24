"""Catalog-backed Parent topic cards and adult-confirmed drawing subjects."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any
from uuid import UUID

from sketch2life.contracts.schemas.parent_topic_suggestions import (
    ParentCustomSubjectValidationV1,
    ParentDrawingSubjectSuggestionSetV1,
    ParentTopicSuggestionSetV1,
)
from sketch2life.resources.parent_topic_catalog_vi_v2 import CATALOG_REVISION, TOPICS

_TOPICS: dict[str, dict[str, Any]] = {
    row["topic_id"]: {
        "title_vi": row["title_vi"],
        "description_vi": row["description_vi"],
        "aliases": row["aliases"],
        "subjects": tuple(
            (subject_id, title, guide_subject, aliases, relation)
            for subject_id, title, guide_subject, relation, aliases in row["subjects"]
        ),
    }
    for row in TOPICS
}


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold())
    folded = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", folded.replace("đ", "d")).strip()


def _set_id(prefix: str, *parts: str) -> str:
    material = "|".join(parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(material).hexdigest()[:24]}"


class ParentTopicSuggestionService:
    @staticmethod
    def is_catalog_topic_id(topic_id: str | None) -> bool:
        return topic_id in _TOPICS

    def topic_set(
        self,
        *,
        draft_id: UUID,
        request_id: UUID,
        selected_topic_ids: tuple[str, ...],
        set_id: str,
        excluded_set_ids: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        if len(selected_topic_ids) != 3 or len(set(selected_topic_ids)) != 3:
            raise ValueError("PARENT_TOPIC_ROTATION_SELECTION_INVALID")
        if any(topic_id not in _TOPICS for topic_id in selected_topic_ids):
            raise ValueError("PARENT_TOPIC_ROTATION_CATALOG_MISMATCH")
        return ParentTopicSuggestionSetV1(
            contract="ParentTopicSuggestionSetV1",
            request_id=request_id,
            set_id=set_id,
            draft_id=draft_id,
            catalog_revision=CATALOG_REVISION,
            excluded_set_ids=list(excluded_set_ids),
            cards=[
                {
                    "topic_id": topic_id,
                    "title_vi": _TOPICS[topic_id]["title_vi"],
                    "description_vi": _TOPICS[topic_id]["description_vi"],
                }
                for topic_id in selected_topic_ids
            ],
        ).model_dump(mode="python")

    def drawing_subject_set(
        self,
        *,
        draft_id: UUID,
        request_id: UUID,
        topic_id: str | None,
        topic: str,
        selected_subject_ids: tuple[str, ...] = (),
        set_id: str | None = None,
        excluded_set_ids: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        normalized_topic = " ".join(topic.split())
        if not 2 <= len(normalized_topic) <= 120:
            raise ValueError("PARENT_TOPIC_INPUT_INVALID")
        category_id = self.resolve_topic(topic_id=topic_id, topic=normalized_topic)
        if category_id is None:
            custom_id = "custom-" + hashlib.sha256(
                _fold(normalized_topic).encode("utf-8")
            ).hexdigest()[:12]
            return ParentDrawingSubjectSuggestionSetV1(
                contract="ParentDrawingSubjectSuggestionSetV1",
                request_id=request_id,
                set_id=_set_id("pds", str(request_id), custom_id),
                draft_id=draft_id,
                topic_id=custom_id,
                topic=normalized_topic,
                catalog_revision=CATALOG_REVISION,
                generation_source="CUSTOM_INPUT_REQUIRED",
                review_required=True,
                excluded_set_ids=list(excluded_set_ids),
                cards=[],
            ).model_dump(mode="python")

        if len(selected_subject_ids) != 3 or len(set(selected_subject_ids)) != 3:
            raise ValueError("PARENT_TOPIC_ROTATION_SELECTION_INVALID")
        catalog_by_id = {
            subject[0]: subject
            for subject in _TOPICS[category_id]["subjects"]
        }
        if any(subject_id not in catalog_by_id for subject_id in selected_subject_ids):
            raise ValueError("PARENT_TOPIC_ROTATION_CATALOG_MISMATCH")
        if set_id is None:
            raise ValueError("PARENT_TOPIC_ROTATION_SET_ID_REQUIRED")

        cards = []
        for subject_id in selected_subject_ids:
            _subject_id, title, guide_subject, _aliases, relation = catalog_by_id[subject_id]
            cards.append(
                {
                    "subject_id": subject_id,
                    "title_vi": title,
                    "guide_subject": guide_subject,
                    "relation_to_topic_vi": relation,
                }
            )
        return ParentDrawingSubjectSuggestionSetV1(
            contract="ParentDrawingSubjectSuggestionSetV1",
            request_id=request_id,
            set_id=set_id,
            draft_id=draft_id,
            topic_id=category_id,
            topic=_TOPICS[category_id]["title_vi"],
            catalog_revision=CATALOG_REVISION,
            generation_source="CURATED_CATALOG",
            review_required=True,
            excluded_set_ids=list(excluded_set_ids),
            cards=cards,
        ).model_dump(mode="python")

    def catalog_subject_ids(self, topic_id: str) -> tuple[str, ...]:
        topic = _TOPICS.get(topic_id)
        if topic is None:
            return ()
        return tuple(subject[0] for subject in topic["subjects"])

    def validate_custom_subject(
        self, *, topic_id: str | None, topic: str, subject: str
    ) -> dict[str, Any]:
        resolved_topic = self.resolve_topic(topic_id=topic_id, topic=topic)
        clean_subject = " ".join(subject.split())
        if resolved_topic is None:
            return self._validation(
                "NEEDS_CLARIFICATION",
                None,
                "Chưa nhận diện được chủ đề. Hãy chọn một chủ đề gợi ý hoặc nói rõ chủ đề muốn vẽ.",
            )

        folded_subject = f" {_fold(clean_subject)} "
        topic_data = _TOPICS[resolved_topic]
        for entry in topic_data["subjects"]:
            if any(f" {_fold(alias)} " in folded_subject for alias in entry[3]):
                return self._validation(
                    "ON_TOPIC", entry[2], "Đối tượng này phù hợp với chủ đề đã chọn."
                )
        for other_id, data in _TOPICS.items():
            if other_id == resolved_topic:
                continue
            for entry in data["subjects"]:
                if any(f" {_fold(alias)} " in folded_subject for alias in entry[3]):
                    return self._validation(
                        "OUT_OF_TOPIC",
                        None,
                        f"“{clean_subject}” chưa khớp với chủ đề {topic_data['title_vi']}. Hãy chọn một thẻ gợi ý hoặc đổi chủ đề.",
                    )
        return self._validation(
            "NEEDS_CLARIFICATION",
            None,
            "Chưa xác định chắc đối tượng có thuộc chủ đề không. Hãy sửa tên đối tượng hoặc đổi chủ đề.",
        )

    @staticmethod
    def _validation(decision: str, normalized_subject: str | None, message: str) -> dict[str, Any]:
        return ParentCustomSubjectValidationV1(
            contract="ParentCustomSubjectValidationV1",
            decision=decision,
            normalized_subject=normalized_subject,
            message_vi=message,
        ).model_dump(mode="json")

    @staticmethod
    def resolve_topic(*, topic_id: str | None, topic: str) -> str | None:
        folded = _fold(topic)
        resolved_by_label = next(
            (
                key
                for key, data in _TOPICS.items()
                if folded == _fold(data["title_vi"])
                or any(folded == _fold(alias) for alias in data["aliases"])
            ),
            None,
        )
        if topic_id in _TOPICS:
            return topic_id if resolved_by_label in (None, topic_id) else None
        if resolved_by_label is not None:
            return resolved_by_label
        partial_matches = {
            key
            for key, data in _TOPICS.items()
            for alias in data["aliases"]
            if len(_fold(alias)) >= 4 and f" {_fold(alias)} " in f" {folded} "
        }
        return next(iter(partial_matches)) if len(partial_matches) == 1 else None


__all__ = ["CATALOG_REVISION", "ParentTopicSuggestionService"]
