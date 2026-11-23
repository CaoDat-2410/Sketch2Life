"""Catalog-first Parent topic and drawable-subject suggestion sets."""

from __future__ import annotations

import hashlib
import itertools
import re
import unicodedata
from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sketch2life.contracts.schemas.parent_topic_suggestions import (
    ParentCustomSubjectValidationV1,
    ParentDrawingSubjectSuggestionSetV1,
    ParentTopicSuggestionSetV1,
)

CATALOG_REVISION = "parent-topic-catalog-2026-11-v1"

_TOPICS: dict[str, dict[str, Any]] = {
    "animals": {
        "title_vi": "Động vật",
        "description_vi": "Những người bạn quanh bé",
        "aliases": ("động vật", "con vật", "thú vật", "animals"),
        "subjects": (
            ("butterfly", "Con bướm", "con bướm", ("bướm", "butterfly")),
            ("hen", "Gà mái", "con gà mái", ("gà", "gà mái", "gà trống", "hen", "chicken")),
            ("cat", "Con mèo", "con mèo", ("mèo", "cat")),
            ("turtle", "Rùa con", "con rùa", ("rùa", "turtle")),
            ("dog", "Chú chó", "con chó", ("chó", "dog")),
            ("fish", "Cá nhỏ", "con cá", ("cá", "fish")),
            ("deer", "Hươu con", "con hươu", ("hươu", "nai", "deer")),
            ("elephant", "Voi con", "con voi", ("voi", "elephant")),
            ("bird", "Chim nhỏ", "con chim", ("chim", "bird")),
        ),
    },
    "nature": {
        "title_vi": "Thiên nhiên",
        "description_vi": "Khu vườn, cây lá và bầu trời",
        "aliases": ("thiên nhiên", "khu vườn", "vườn", "cây cỏ", "khu rừng", "rừng xanh", "nature"),
        "subjects": (
            ("flower", "Bông hoa", "bông hoa", ("hoa", "bông hoa", "flower")),
            ("tree", "Cây xanh", "cây xanh", ("cây", "cây xanh", "tree")),
            ("leaf", "Chiếc lá", "chiếc lá", ("lá", "chiếc lá", "leaf")),
            ("mushroom", "Nấm nhỏ", "cây nấm", ("nấm", "mushroom")),
            ("snail", "Ốc sên", "con ốc sên", ("ốc sên", "snail")),
            ("ladybug", "Bọ rùa", "con bọ rùa", ("bọ rùa", "ladybug")),
            ("sun", "Mặt trời", "mặt trời", ("mặt trời", "sun")),
        ),
    },
    "transport": {
        "title_vi": "Phương tiện",
        "description_vi": "Xe cộ và những chuyến đi",
        "aliases": ("phương tiện", "giao thông", "xe cộ", "transport"),
        "subjects": (
            ("car", "Ô tô", "chiếc ô tô", ("ô tô", "xe hơi", "car")),
            ("bicycle", "Xe đạp", "chiếc xe đạp", ("xe đạp", "bicycle")),
            ("train", "Tàu hỏa", "đoàn tàu", ("tàu hỏa", "tàu", "train")),
            ("airplane", "Máy bay", "chiếc máy bay", ("máy bay", "airplane")),
            ("boat", "Thuyền nhỏ", "chiếc thuyền", ("thuyền", "tàu thủy", "boat")),
            ("bus", "Xe buýt", "chiếc xe buýt", ("xe buýt", "bus")),
        ),
    },
    "ocean": {
        "title_vi": "Đại dương",
        "description_vi": "Cá và những người bạn biển",
        "aliases": ("đại dương", "biển", "động vật biển", "ocean"),
        "subjects": (
            ("fish", "Cá nhỏ", "con cá", ("cá", "fish")),
            ("turtle", "Rùa biển", "con rùa biển", ("rùa", "rùa biển", "turtle")),
            ("whale", "Cá voi", "con cá voi", ("cá voi", "whale")),
            ("octopus", "Bạch tuộc", "con bạch tuộc", ("bạch tuộc", "octopus")),
            ("starfish", "Sao biển", "con sao biển", ("sao biển", "starfish")),
            ("crab", "Cua nhỏ", "con cua", ("cua", "crab")),
        ),
    },
    "space": {
        "title_vi": "Vũ trụ",
        "description_vi": "Các hành tinh và chuyến bay xa",
        "aliases": ("vũ trụ", "không gian", "hành tinh", "space"),
        "subjects": (
            ("rocket", "Tên lửa", "chiếc tên lửa", ("tên lửa", "rocket")),
            ("planet", "Hành tinh", "hành tinh", ("hành tinh", "planet")),
            ("moon", "Mặt trăng", "mặt trăng", ("mặt trăng", "trăng", "moon")),
            ("star", "Ngôi sao", "ngôi sao", ("sao", "ngôi sao", "star")),
            ("sun", "Mặt trời", "mặt trời", ("mặt trời", "sun")),
            ("astronaut", "Phi hành gia", "phi hành gia", ("phi hành gia", "astronaut")),
        ),
    },
    "fairy-tale": {
        "title_vi": "Thế giới cổ tích",
        "description_vi": "Nhân vật và lâu đài kỳ diệu",
        "aliases": ("thế giới cổ tích", "cổ tích", "truyện cổ tích", "fairy tale"),
        "subjects": (
            ("castle", "Lâu đài", "lâu đài", ("lâu đài", "castle")),
            ("dragon", "Rồng con", "con rồng", ("rồng", "dragon")),
            ("unicorn", "Kỳ lân", "con kỳ lân", ("kỳ lân", "unicorn")),
            ("fairy", "Nàng tiên", "nàng tiên", ("tiên", "nàng tiên", "fairy")),
            ("crown", "Chiếc vương miện", "chiếc vương miện", ("vương miện", "crown")),
        ),
    },
    "home": {
        "title_vi": "Đồ vật quanh em",
        "description_vi": "Đồ dùng quen thuộc ở nhà",
        "aliases": ("đồ vật", "đồ vật quanh em", "đồ dùng", "trong nhà", "home"),
        "subjects": (
            ("cup", "Chiếc cốc", "chiếc cốc", ("cốc", "ly", "cup")),
            ("chair", "Chiếc ghế", "chiếc ghế", ("ghế", "chair")),
            ("lamp", "Đèn bàn", "chiếc đèn bàn", ("đèn", "đèn bàn", "lamp")),
            ("clock", "Đồng hồ", "chiếc đồng hồ", ("đồng hồ", "clock")),
            ("book", "Quyển sách", "quyển sách", ("sách", "book")),
            ("kettle", "Ấm nước", "chiếc ấm nước", ("ấm nước", "ấm", "kettle")),
        ),
    },
}


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold())
    folded = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", folded.replace("đ", "d")).strip()


def _set_id(prefix: str, ids: tuple[str, ...]) -> str:
    digest = hashlib.sha256("|".join(ids).encode("utf-8")).hexdigest()[:24]
    return f"{prefix}_{digest}"


def _choose_three(
    *,
    pool: tuple[Any, ...],
    draft_id: UUID,
    excluded_set_ids: tuple[str, ...],
    prefix: str,
    stable_id: Any,
) -> tuple[tuple[Any, ...], str]:
    options = tuple(itertools.combinations(pool, 3))
    if len(options) < 2:
        raise ValueError("SUGGESTION_CATALOG_TOO_SMALL")
    seed = int(hashlib.sha256(str(draft_id).encode("ascii")).hexdigest()[:16], 16)
    start = seed % len(options)
    for offset in range(len(options)):
        selected = options[(start + offset) % len(options)]
        ids = tuple(stable_id(item) for item in selected)
        set_id = _set_id(prefix, ids)
        if set_id not in excluded_set_ids:
            return selected, set_id
    raise ValueError("SUGGESTION_SET_UNAVAILABLE")


class ParentTopicSuggestionService:
    @staticmethod
    def is_catalog_topic_id(topic_id: str | None) -> bool:
        return topic_id in _TOPICS

    def topic_set(
        self, *, draft_id: UUID, excluded_set_ids: tuple[str, ...] = ()
    ) -> dict[str, Any]:
        pool = tuple(_TOPICS.items())
        selected, set_id = _choose_three(
            pool=pool,
            draft_id=draft_id,
            excluded_set_ids=excluded_set_ids,
            prefix="pts",
            stable_id=lambda item: item[0],
        )
        return ParentTopicSuggestionSetV1(
            contract="ParentTopicSuggestionSetV1",
            set_id=set_id,
            draft_id=draft_id,
            catalog_revision=CATALOG_REVISION,
            excluded_set_ids=list(excluded_set_ids),
            cards=[
                {
                    "topic_id": topic_id,
                    "title_vi": data["title_vi"],
                    "description_vi": data["description_vi"],
                }
                for topic_id, data in selected
            ],
        ).model_dump(mode="python")

    def drawing_subject_set(
        self,
        *,
        draft_id: UUID,
        topic_id: str | None,
        topic: str,
        excluded_set_ids: tuple[str, ...] = (),
        excluded_subjects: tuple[str, ...] = (),
        generated_subjects: tuple[dict[str, str], ...] = (),
    ) -> dict[str, Any]:
        category_id = self.resolve_topic(topic_id=topic_id, topic=topic)
        normalized_topic = " ".join(topic.split())
        if not 2 <= len(normalized_topic) <= 120:
            raise ValueError("PARENT_TOPIC_INPUT_INVALID")
        if category_id is None:
            resolved_topic_id = "custom-" + hashlib.sha256(
                _fold(normalized_topic).encode("utf-8")
            ).hexdigest()[:12]
            topic_title = normalized_topic
            catalog_pool: tuple[tuple[Any, ...], ...] = ()
        else:
            resolved_topic_id = category_id
            topic_data = _TOPICS[category_id]
            topic_title = topic_data["title_vi"]
            catalog_pool = self.eligible_catalog_subjects(
                topic_id=category_id,
                topic=topic_title,
                excluded_subjects=excluded_subjects,
            )

        cards: list[dict[str, str]] = []
        stable_ids: list[str] = []
        selected_catalog = catalog_pool
        if len(catalog_pool) >= 3:
            selected_catalog, _ = _choose_three(
                pool=catalog_pool,
                draft_id=draft_id,
                excluded_set_ids=excluded_set_ids,
                prefix="pds",
                stable_id=lambda item: f"{resolved_topic_id}:{item[0]}",
            )
        for item in selected_catalog:
            stable_id = f"{resolved_topic_id}:{item[0]}"
            stable_ids.append(stable_id)
            cards.append(
                {"subject_id": item[0], "title_vi": item[1], "guide_subject": item[2]}
            )

        generated_count = 0
        if len(cards) < 3:
            if len(generated_subjects) != 3:
                raise ValueError("PARENT_TOPIC_SUBJECTS_NEEDS_AI_DRAFT")
            excluded = {_fold(value) for value in excluded_subjects}
            used_names = {
                _fold(value)
                for card in cards
                for value in (card["title_vi"], card["guide_subject"])
            }
            for subject in generated_subjects:
                title = " ".join(subject["title_vi"].split())
                guide_subject = " ".join(subject["guide_subject"].split())
                relation = " ".join(subject["relation_to_topic_vi"].split())
                title_key = _fold(title)
                guide_key = _fold(guide_subject)
                if not title_key or not guide_key or not relation:
                    raise ValueError("PARENT_TOPIC_SUBJECT_AI_OUTPUT_INVALID")
                if title_key in excluded or guide_key in excluded:
                    continue
                if title_key in used_names or guide_key in used_names:
                    continue
                subject_id = "ai-" + hashlib.sha256(
                    f"{resolved_topic_id}|{title_key}".encode("utf-8")
                ).hexdigest()[:12]
                stable_ids.append(f"{resolved_topic_id}:{subject_id}")
                cards.append(
                    {
                        "subject_id": subject_id,
                        "title_vi": title,
                        "guide_subject": guide_subject,
                        "relation_to_topic_vi": relation,
                    }
                )
                used_names.update({title_key, guide_key})
                generated_count += 1
                if len(cards) == 3:
                    break
            if len(cards) != 3:
                raise ValueError("PARENT_TOPIC_SUBJECT_AI_OUTPUT_INVALID")

        set_id = _set_id("pds", tuple(stable_ids))
        if set_id in excluded_set_ids:
            raise ValueError("SUGGESTION_SET_UNAVAILABLE")
        return ParentDrawingSubjectSuggestionSetV1(
            contract="ParentDrawingSubjectSuggestionSetV1",
            set_id=set_id,
            draft_id=draft_id,
            topic_id=resolved_topic_id,
            topic=topic_title,
            catalog_revision=(
                "parent-topic-subject-qwen35-draft-v1"
                if category_id is None
                else CATALOG_REVISION
                if generated_count == 0
                else "parent-topic-subject-mixed-qwen35-v1"
            ),
            generation_source="QWEN_DRAFT" if generated_count else "CURATED_CATALOG",
            review_required=True,
            excluded_set_ids=list(excluded_set_ids),
            cards=cards,
        ).model_dump(mode="python")

    def eligible_catalog_subjects(
        self,
        *,
        topic_id: str | None,
        topic: str,
        excluded_subjects: tuple[str, ...] = (),
    ) -> tuple[tuple[Any, ...], ...]:
        category_id = self.resolve_topic(topic_id=topic_id, topic=topic)
        if category_id is None:
            return ()
        excluded = {_fold(value) for value in excluded_subjects}
        return tuple(
            item
            for item in _TOPICS[category_id]["subjects"]
            if not any(_fold(label) in excluded for label in (item[1], item[2], *item[3]))
        )

    def validate_custom_subject(
        self, *, topic_id: str | None, topic: str, subject: str
    ) -> dict[str, Any]:
        resolved_topic = self.resolve_topic(topic_id=topic_id, topic=topic)
        clean_subject = " ".join(subject.split())
        if resolved_topic is None:
            return ParentCustomSubjectValidationV1(
                contract="ParentCustomSubjectValidationV1",
                decision="NEEDS_CLARIFICATION",
                normalized_subject=None,
                message_vi="Chưa nhận diện được chủ đề. Hãy chọn một chủ đề gợi ý hoặc nói rõ chủ đề muốn vẽ.",
            ).model_dump(mode="json")

        folded_subject = f" {_fold(clean_subject)} "
        matching_topic = _TOPICS[resolved_topic]
        for entry in matching_topic["subjects"]:
            if any(f" {_fold(alias)} " in folded_subject for alias in entry[3]):
                return ParentCustomSubjectValidationV1(
                    contract="ParentCustomSubjectValidationV1",
                    decision="ON_TOPIC",
                    normalized_subject=entry[2],
                    message_vi="Đối tượng này phù hợp với chủ đề đã chọn.",
                ).model_dump(mode="json")
        for topic_key, data in _TOPICS.items():
            if topic_key == resolved_topic:
                continue
            for entry in data["subjects"]:
                if any(f" {_fold(alias)} " in folded_subject for alias in entry[3]):
                    selected_title = matching_topic["title_vi"]
                    return ParentCustomSubjectValidationV1(
                        contract="ParentCustomSubjectValidationV1",
                        decision="OUT_OF_TOPIC",
                        normalized_subject=None,
                        message_vi=f"“{clean_subject}” chưa khớp với chủ đề {selected_title}. Hãy chọn một thẻ gợi ý hoặc đổi chủ đề.",
                    ).model_dump(mode="json")
        topic_terms = set(_fold(topic).split())
        subject_terms = set(_fold(clean_subject).split())
        if topic_terms and subject_terms.intersection(topic_terms):
            return ParentCustomSubjectValidationV1(
                contract="ParentCustomSubjectValidationV1",
                decision="ON_TOPIC",
                normalized_subject=clean_subject,
                message_vi="Đối tượng có vẻ phù hợp với chủ đề đã chọn.",
            ).model_dump(mode="json")
        return ParentCustomSubjectValidationV1(
            contract="ParentCustomSubjectValidationV1",
            decision="NEEDS_CLARIFICATION",
            normalized_subject=None,
            message_vi="Chưa xác định chắc đối tượng có thuộc chủ đề không. Hãy chọn một trong ba thẻ hoặc sửa nội dung nhập.",
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
            if resolved_by_label is not None and resolved_by_label != topic_id:
                return None
            return topic_id
        partial_matches = [
            (len(_fold(alias)), key)
            for key, data in _TOPICS.items()
            for alias in data["aliases"]
            if len(_fold(alias)) >= 4 and f" {_fold(alias)} " in f" {folded} "
        ]
        if partial_matches:
            longest = max(length for length, _ in partial_matches)
            best = {key for length, key in partial_matches if length == longest}
            if len(best) == 1:
                return next(iter(best))
        for key, data in _TOPICS.items():
            for alias in data["aliases"]:
                if folded == _fold(alias):
                    return key
        return None


__all__ = ["CATALOG_REVISION", "ParentTopicSuggestionService"]
