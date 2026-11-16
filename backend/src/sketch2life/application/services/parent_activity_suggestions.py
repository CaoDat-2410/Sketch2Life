"""Parent-owned catalog-first activity selection and fallback quality gate."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from pydantic import ValidationError

from sketch2life.application.ports.parent_activity_catalog import (
    ParentActivityCatalogPort,
    ParentActivityLesson,
)
from sketch2life.contracts.schemas.modal_ai import (
    ParentActivitySuggestionWorkerRequestV3,
    ParentActivitySuggestionWorkerResponseV2,
    ParentSuggestedActivityV2,
)

_MAX_CANDIDATES = 12
_AGE_BAND_REF = re.compile(r"\Aage-(\d{2,3})-(\d{2,3})-months-v(\d+)\Z")
_PII_EMAIL = re.compile(r"\b[^\s@]+@[^\s@]+\.[A-Za-z]{2,}\b")
_PII_PHONE = re.compile(r"(?<!\d)(?:\+?\d[\d .()\-]{7,}\d)(?!\d)")
_PII_URL = re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE)
_NAME_PHRASE = re.compile(
    r"\b(?:con|bé|em|mình|tôi)\s+(?:có\s+)?(?:tên|tên gọi)\s+(?:là|:)\s*[^,.!?;]{1,60}",
    re.IGNORECASE,
)
_CASUAL_NAME_PHRASE = re.compile(r"\b(?:bé|con|em)\s+[A-ZÀ-ỸĐ][a-zà-ỹđ]{1,24}\b")
_STOP_WORDS = {
    "va", "la", "cua", "cho", "voi", "nhung", "mot", "cac", "nhieu", "tren",
    "duoi", "trong", "ngoai", "con", "be", "em", "minh", "toi", "thich", "muon",
    "ve", "nay", "do", "gi", "the", "nao", "nhu", "co", "duoc", "hay",
}
_INTEREST_TAG_ALIASES: dict[str, tuple[str, ...]] = {
    "nature": ("thien nhien", "vuon", "ngoai troi", "tu nhien"),
    "animals": ("dong vat", "con vat", "meo", "cho", "chim", "ca"),
    "insects": ("con trung", "buom", "ong", "kien", "chuon chuon", "sau"),
    "plants": ("cay", "hoa", "la cay", "la non", "hat", "mam"),
    "colors": ("mau", "xanh", "do", "vang", "tim", "cam", "trang", "den"),
    "water": ("nuoc", "bien", "song", "mua", "suoi"),
    "movement": ("van dong", "chay", "nhay", "di bo"),
    "art": ("ve", "to mau", "but ve", "dat nan"),
    "music": ("nhac", "hat", "am thanh"),
    "building": ("xep", "lap rap", "xay dung", "cong trinh"),
    "sky_and_weather": ("bau troi", "may", "mat troi", "trang", "sao", "gio"),
}
_UNSAFE_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"\b(?:keo sac|hoa chat|thuoc tru sau|o dien|day dien|bep gas)\b",
        r"\b(?:nuoc sau|song sau|bien dong|ho sau|kenh nuoc)\b",
        r"\b(?:leo len|treo len)\s+(?:cay|tuong|hang rao|mai nha)\b",
        r"\b(?:ra|bang qua)\s+(?:duong lon|duong xe|pho dong)\b",
        r"\b(?:bat|duoi bat|cham vao|cho an)\s+(?:con\s+)?(?:buom|ong|con trung|chim hoang da)\b",
        r"\ban thu\s+(?:la|qua|nam|hat|cay)\b",
    )
)
_UNSAFE_FIRE_ACTION = re.compile(
    r"\b(?:dot|nhom|bat|su dung|choi voi)\s+(?:ngon\s+)?lua\b|"
    r"\b(?:lua chay|bep lua|ngon lua)\b"
)
_NEGATION = re.compile(r"\b(?:khong|tranh|khong duoc|khong nen)\b")
_OUTDOOR_MARKERS = (
    "ngoai troi", "san truong", "san nha", "vuon", "cong vien", "bai co",
    "thien nhien", "khuon vien", "hien nha",
)
_CHILD_AGENCY_MARKERS = (
    "tre tu chon", "tre co the chon", "tre duoc chon", "tre tu quan sat",
    "tre quan sat", "tre thu nghiem", "tre tu quyet dinh", "con tu chon",
    "con co the chon", "theo lua chon cua tre", "khuyen khich tre",
    "tre chu dong chon", "tre chu dong quan sat", "tre chu dong thu nghiem",
    "tre co the tu chon", "tre tu kham pha", "con tu quan sat", "con tu kham pha",
    "tre tu di dao", "tre tu ve", "tre tu sap xep", "tre tu mo ta",
)
_ADULT_SUPPORT_MARKERS = (
    "nguoi lon", "phu huynh", "nguoi huong dan", "co the ho tro", "nguoi cham soc",
)
_MONTESSORI_EXPLORATION_MARKERS = (
    "quan sat", "thu nghiem", "kham pha", "so sanh", "phan loai", "tim hieu",
)
_SAFETY_MARKERS = ("khong", "tranh", "an toan", "giam sat", "dam bao")
_SENTENCE_ENDINGS = (".", "!", "?", "…", "。", "！", "？")


class ParentActivitySuggestionError(ValueError):
    def __init__(self, code: str, *, diagnostic_code: str | None = None) -> None:
        self.code = code
        self.diagnostic_code = diagnostic_code
        super().__init__(code)


@dataclass(frozen=True)
class PreparedParentActivitySuggestion:
    worker_input: dict[str, Any]
    candidates_by_ref: Mapping[str, _EligibleCandidate]
    context_terms: frozenset[str]
    candidate_count: int


@dataclass(frozen=True)
class _EligibleCandidate:
    candidate_ref: str
    lesson_id: str
    lesson_title: str
    lesson_topic: str
    lesson_drawing_subject: str
    version_id: str
    content_sha256: str
    activity_index: int
    activity: dict[str, Any]
    source: str


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold())
    folded = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return folded.replace("đ", "d")


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", _fold(value))
        if len(token) > 1 and token not in _STOP_WORDS
    }


def _contains_non_latin_letter(value: str) -> bool:
    return any(
        character.isalpha() and "LATIN" not in unicodedata.name(character, "")
        for character in value
    )


def _tags_from_user_text(value: str) -> list[str]:
    folded = f" {_fold(value)} "
    return [
        tag
        for tag, aliases in _INTEREST_TAG_ALIASES.items()
        if any(f" {_fold(alias)} " in folded for alias in aliases)
    ][:12]


def _sanitize_interest_context(value: str) -> list[str]:
    # Only send controlled tags; never forward arbitrary profile or narration text.
    sanitized = _NAME_PHRASE.sub(" ", value)
    sanitized = _PII_PHONE.sub(" ", sanitized)
    sanitized = _PII_EMAIL.sub(" ", sanitized)
    sanitized = _PII_URL.sub(" ", sanitized)
    return _tags_from_user_text(sanitized)


def _sanitize_context_label(value: str, *, limit: int) -> str:
    sanitized = _NAME_PHRASE.sub(" ", value)
    sanitized = _PII_PHONE.sub(" ", sanitized)
    sanitized = _PII_EMAIL.sub(" ", sanitized)
    sanitized = _PII_URL.sub(" ", sanitized)
    sanitized = _CASUAL_NAME_PHRASE.sub(" ", sanitized)
    return " ".join(sanitized.split())[:limit]


def _age_range(ref: str | None, version: int | None) -> tuple[int, int] | None:
    if ref is None or version is None:
        return None
    match = _AGE_BAND_REF.fullmatch(ref)
    if match is None:
        return None
    minimum, maximum, ref_version = (int(value) for value in match.groups())
    if (
        version != ref_version
        or minimum < 36
        or maximum > 120
        or minimum > maximum
    ):
        return None
    return minimum, maximum


def _age_band(age_months: int) -> tuple[str, str]:
    if 36 <= age_months <= 71:
        return "36-71", "age-36-71-months-v1"
    if 72 <= age_months <= 107:
        return "72-107", "age-72-107-months-v1"
    if 108 <= age_months <= 120:
        return "108-120", "age-108-120-months-v1"
    raise ParentActivitySuggestionError("PARENT_AGE_OUT_OF_SUPPORTED_RANGE")


def _contains_unsafe_action(value: str) -> bool:
    folded = _fold(value)
    for pattern in (*_UNSAFE_PATTERNS, _UNSAFE_FIRE_ACTION):
        for match in pattern.finditer(folded):
            if _NEGATION.search(folded[max(0, match.start() - 24) : match.start()]):
                continue
            return True
    return False


def _is_renderable_activity(activity: Mapping[str, Any]) -> dict[str, Any] | None:
    try:
        from sketch2life.contracts.schemas.modal_ai import ParentActivitySuggestionItemV1

        parsed = ParentActivitySuggestionItemV1.model_validate(dict(activity))
    except (TypeError, ValidationError):
        return None
    if parsed.activity_kind != "outdoor":
        return None
    text = " ".join(
        (
            parsed.title,
            parsed.objective,
            parsed.materials_text,
            parsed.preparation_text,
            parsed.instructions_text,
            parsed.observation_notes,
            parsed.safety_notes,
        )
    )
    if (
        _contains_unsafe_action(text)
        or _PII_EMAIL.search(text)
        or _PII_PHONE.search(text)
        or _PII_URL.search(text)
        or _NAME_PHRASE.search(text)
        or _CASUAL_NAME_PHRASE.search(text)
    ):
        return None
    return parsed.model_dump(mode="json")


def _bounded_worker_activity(activity: Mapping[str, Any]) -> dict[str, str]:
    field_limits = {
        "title": 160,
        "objective": 400,
        "materials_text": 300,
        "preparation_text": 300,
        "instructions_text": 700,
        "observation_notes": 300,
        "safety_notes": 300,
    }
    return {
        key: str(activity.get(key, "")).strip()[:limit]
        for key, limit in field_limits.items()
    } | {"activity_kind": "outdoor"}


def _lesson_from_pin(pin: Mapping[str, Any]) -> ParentActivityLesson:
    required = (
        "lesson_id", "version_id", "version_no", "content_sha256", "title", "topic",
        "drawing_subject", "activities",
    )
    if any(key not in pin for key in required):
        raise ParentActivitySuggestionError("PARENT_PIN_SNAPSHOT_INVALID")
    return ParentActivityLesson(
        lesson_id=str(pin["lesson_id"]),
        version_id=str(pin["version_id"]),
        version_no=int(pin["version_no"]),
        content_sha256=str(pin["content_sha256"]),
        title=str(pin["title"]),
        topic=str(pin["topic"]),
        drawing_subject=str(pin["drawing_subject"]),
        target_age_band_ref=(
            str(pin["target_age_band_ref"])
            if pin.get("target_age_band_ref") is not None
            else None
        ),
        target_age_band_version=(
            int(pin["target_age_band_version"])
            if pin.get("target_age_band_version") is not None
            else None
        ),
        access_source="PINNED_LESSON",
        activities=tuple(pin["activities"]),
    )


class ParentActivitySuggestionService:
    def __init__(self, catalog: ParentActivityCatalogPort) -> None:
        self._catalog = catalog

    def prepare(
        self,
        *,
        parent_principal_ref: str,
        context_snapshot: Mapping[str, Any],
        subject_label: str,
        visible_features: Sequence[str],
        pinned_lesson_snapshot: Mapping[str, Any] | None,
    ) -> PreparedParentActivitySuggestion:
        age_months = context_snapshot.get("age_months")
        if isinstance(age_months, bool) or not isinstance(age_months, int):
            raise ParentActivitySuggestionError("PARENT_AGE_CONTEXT_INVALID")
        age_band, age_band_ref = _age_band(age_months)
        if not subject_label.strip() or not visible_features:
            raise ParentActivitySuggestionError("PARENT_DRAWING_CONTEXT_REQUIRED")

        topic = _sanitize_context_label(str(context_snapshot.get("topic") or ""), limit=120)
        safe_idea = _sanitize_context_label(
            str(context_snapshot.get("adult_confirmed_idea") or ""), limit=300
        )
        safe_subject = _sanitize_context_label(subject_label, limit=160)
        safe_features = [
            _sanitize_context_label(str(value), limit=160)
            for value in visible_features[:4]
        ]
        safe_features = [value for value in safe_features if value]
        if not safe_subject or not safe_features:
            raise ParentActivitySuggestionError("PARENT_DRAWING_CONTEXT_REQUIRED")
        profile_tags = _sanitize_interest_context(
            str(context_snapshot.get("interests_summary") or "")
        )
        narration_tags = _sanitize_interest_context(
            str(context_snapshot.get("adult_confirmed_idea") or "")
        )
        safe_profile_interests = _sanitize_context_label(
            str(context_snapshot.get("interests_summary") or ""), limit=300
        )
        interest_aliases = [
            alias
            for tag in profile_tags
            for alias in _INTEREST_TAG_ALIASES.get(tag, ())
        ]
        narration_aliases = [
            alias
            for tag in narration_tags
            for alias in _INTEREST_TAG_ALIASES.get(tag, ())
        ]
        context_terms = _tokens(
            " ".join(
                (
                    topic,
                    safe_subject,
                    *safe_features,
                    safe_idea,
                    safe_profile_interests,
                    *interest_aliases,
                    *narration_aliases,
                )
            )
        )
        if not context_terms:
            raise ParentActivitySuggestionError("PARENT_DRAWING_CONTEXT_REQUIRED")
        lessons = (
            [_lesson_from_pin(pinned_lesson_snapshot)]
            if pinned_lesson_snapshot is not None
            else list(
                self._catalog.list_accessible_lessons(
                    parent_principal_ref=parent_principal_ref
                )
            )
        )
        eligible: list[tuple[int, _EligibleCandidate, dict[str, Any]]] = []
        for lesson in lessons:
            age_range = _age_range(
                lesson.target_age_band_ref, lesson.target_age_band_version
            )
            if age_range is None or not age_range[0] <= age_months <= age_range[1]:
                continue
            if lesson.access_source not in {"PINNED_LESSON", "PUBLIC", "SHARED"}:
                continue
            for activity_index, raw_activity in enumerate(lesson.activities):
                activity = _is_renderable_activity(raw_activity)
                if activity is None:
                    continue
                searchable = " ".join(
                    (
                        lesson.topic,
                        lesson.drawing_subject,
                        activity["title"],
                        activity["objective"],
                        activity["instructions_text"],
                        activity["materials_text"],
                        activity["preparation_text"],
                    )
                )
                activity_terms = _tokens(searchable)
                overlap = len(context_terms.intersection(activity_terms))
                if overlap == 0:
                    continue
                score = overlap
                if _tokens(topic).intersection(_tokens(lesson.topic)):
                    score += 4
                if _tokens(safe_subject).intersection(_tokens(lesson.drawing_subject)):
                    score += 3
                candidate = _EligibleCandidate(
                    candidate_ref="",
                    lesson_id=lesson.lesson_id,
                    lesson_title=lesson.title,
                    lesson_topic=lesson.topic,
                    lesson_drawing_subject=lesson.drawing_subject,
                    version_id=lesson.version_id,
                    content_sha256=lesson.content_sha256,
                    activity_index=activity_index,
                    activity=activity,
                    source=lesson.access_source,
                )
                eligible.append((score, candidate, activity))

        eligible.sort(
            key=lambda item: (
                -item[0],
                item[1].lesson_id,
                item[1].version_id,
                item[1].activity_index,
            )
        )
        chosen = eligible[:_MAX_CANDIDATES]
        candidates_by_ref: dict[str, _EligibleCandidate] = {}
        worker_candidates: list[dict[str, Any]] = []
        for index, (_, candidate, activity) in enumerate(chosen, start=1):
            candidate_ref = f"C{index:03d}"
            bound = _EligibleCandidate(
                candidate_ref=candidate_ref,
                lesson_id=candidate.lesson_id,
                lesson_title=candidate.lesson_title,
                lesson_topic=candidate.lesson_topic,
                lesson_drawing_subject=candidate.lesson_drawing_subject,
                version_id=candidate.version_id,
                content_sha256=candidate.content_sha256,
                activity_index=candidate.activity_index,
                activity=candidate.activity,
                source=candidate.source,
            )
            candidates_by_ref[candidate_ref] = bound
            worker_candidates.append(
                {
                    "candidate_ref": candidate_ref,
                    "lesson_topic": candidate.lesson_topic[:120],
                    "drawing_subject": candidate.lesson_drawing_subject[:160],
                    "age_band_months": age_band,
                    "activity": _bounded_worker_activity(activity),
                }
            )

        worker_input = ParentActivitySuggestionWorkerRequestV3(
            schema_version="sketch2life.parent-activity-suggest-input.v3",
            age_band_months=age_band,
            age_band_ref=age_band_ref,
            topic=topic,
            adult_confirmed_idea=safe_idea,
            confirmed_subject=safe_subject,
            visible_features=safe_features,
            profile_interest_tags=profile_tags,
            narration_interest_tags=narration_tags,
            candidate_activities=worker_candidates,
        ).model_dump(mode="json")
        return PreparedParentActivitySuggestion(
            worker_input=worker_input,
            candidates_by_ref=candidates_by_ref,
            context_terms=frozenset(context_terms),
            candidate_count=len(worker_candidates),
        )

    def resolve(
        self,
        *,
        prepared: PreparedParentActivitySuggestion,
        raw_result: Mapping[str, Any],
        request_id: str,
        story_run_id: str,
        understanding_revision: int,
        modal_call_id: str | None,
    ) -> dict[str, Any]:
        try:
            result = ParentActivitySuggestionWorkerResponseV2.model_validate(raw_result)
        except (TypeError, ValidationError):
            raise ParentActivitySuggestionError("MODAL_OUTPUT_CONTRACT_INVALID") from None
        if result.age_band_months != prepared.worker_input["age_band_months"]:
            raise ParentActivitySuggestionError("PARENT_ACTIVITY_AGE_BAND_MISMATCH")

        activities: list[ParentSuggestedActivityV2] = []
        if result.decision == "CATALOG_MATCH":
            if not prepared.candidates_by_ref:
                raise ParentActivitySuggestionError("MODAL_OUTPUT_CONTRACT_INVALID")
            for selection in result.selected_candidates:
                candidate = prepared.candidates_by_ref.get(selection.candidate_ref)
                if candidate is None:
                    raise ParentActivitySuggestionError("MODAL_OUTPUT_CONTRACT_INVALID")
                activities.append(
                    ParentSuggestedActivityV2(
                        **candidate.activity,
                        source=(
                            "PINNED_LESSON"
                            if candidate.source == "PINNED_LESSON"
                            else "PUBLISHED_SHARED_LESSON"
                        ),
                        source_lesson_id=candidate.lesson_id,
                        source_lesson_title=candidate.lesson_title,
                        source_lesson_version_id=candidate.version_id,
                        source_content_sha256=candidate.content_sha256,
                        source_activity_index=candidate.activity_index,
                        match_reason=selection.match_reason.strip(),
                    )
                )
            selection_mode = "CATALOG_SELECTION"
        else:
            self._quality_gate(
                activities=result.fallback_activities,
                age_band=prepared.worker_input["age_band_months"],
                context_terms=prepared.context_terms,
                candidates=prepared.candidates_by_ref.values(),
            )
            activities = [
                ParentSuggestedActivityV2(
                    **item.model_dump(mode="json"),
                    source="AI_GENERATED_DRAFT",
                    source_lesson_id=None,
                    source_lesson_title=None,
                    source_lesson_version_id=None,
                    source_content_sha256=None,
                    source_activity_index=None,
                    match_reason=result.no_match_reason.strip(),
                )
                for item in result.fallback_activities
            ]
            selection_mode = "AI_GENERATED_FALLBACK"

        return {
            "contract": "ParentActivitySuggestionResponseV2",
            "request_id": request_id,
            "story_run_id": story_run_id,
            "understanding_revision": understanding_revision,
            "selection_mode": selection_mode,
            "catalog_candidate_count": prepared.candidate_count,
            "review_required": True,
            "modal_call_id": modal_call_id,
            "activities": [item.model_dump(mode="json") for item in activities],
        }

    @staticmethod
    def _quality_gate(
        *,
        activities: Sequence[Any],
        age_band: str,
        context_terms: frozenset[str],
        candidates: Sequence[_EligibleCandidate],
    ) -> None:
        def reject(reason: str) -> None:
            raise ParentActivitySuggestionError(
                "PARENT_ACTIVITY_QUALITY_GATE_REJECTED",
                diagnostic_code=reason,
            )

        if len(activities) != 3:
            reject("FALLBACK_COUNT_INVALID")
        normalized_titles: set[str] = set()
        combined_texts: list[str] = []
        candidate_texts = [
            _fold(" ".join(candidate.activity.values()))
            for candidate in candidates
        ]
        for activity in activities:
            text = " ".join(
                (
                    activity.title,
                    activity.objective,
                    activity.materials_text,
                    activity.preparation_text,
                    activity.instructions_text,
                    activity.observation_notes,
                    activity.safety_notes,
                )
            )
            folded = _fold(text)
            instructions = _fold(
                " ".join((activity.instructions_text, activity.preparation_text))
            )
            adult_role = _fold(
                " ".join((activity.instructions_text, activity.preparation_text))
            )
            materials_and_steps = _fold(
                " ".join(
                    (
                        activity.materials_text,
                        activity.preparation_text,
                        activity.instructions_text,
                    )
                )
            )
            safety = _fold(activity.safety_notes)
            title_key = " ".join(sorted(_tokens(activity.title)))
            if any(
                value.strip() and not value.strip().endswith(_SENTENCE_ENDINGS)
                for value in (
                    activity.objective,
                    activity.preparation_text,
                    activity.instructions_text,
                    activity.safety_notes,
                )
            ):
                reject("ACTIVITY_TEXT_INCOMPLETE")
            if activity.activity_kind != "outdoor":
                reject("ACTIVITY_NOT_OUTDOOR")
            if len(activity.instructions_text.strip()) < 40:
                reject("ACTIVITY_INSTRUCTIONS_TOO_SHORT")
            if len(activity.safety_notes.strip()) < 12:
                reject("SAFETY_NOTE_TOO_SHORT")
            if not any(marker in instructions for marker in _OUTDOOR_MARKERS):
                reject("OUTDOOR_SETTING_NOT_EXPLICIT")
            if not any(marker in instructions for marker in _CHILD_AGENCY_MARKERS):
                reject("CHILD_AGENCY_NOT_EXPLICIT")
            if not any(
                marker in instructions for marker in _MONTESSORI_EXPLORATION_MARKERS
            ):
                reject("EXPLORATION_NOT_EXPLICIT")
            if not any(marker in adult_role for marker in _ADULT_SUPPORT_MARKERS):
                reject("ADULT_SUPPORT_NOT_EXPLICIT")
            if not any(marker in safety for marker in _SAFETY_MARKERS):
                reject("SAFETY_NOTE_MISSING")
            if _contains_unsafe_action(materials_and_steps):
                reject("UNSAFE_ACTION_TEXT")
            if not (context_terms & _tokens(text)):
                reject("ACTIVITY_CONTEXT_MISMATCH")
            if not title_key or title_key in normalized_titles:
                reject("ACTIVITY_TITLE_DUPLICATE")
            if _PII_EMAIL.search(text) or _PII_PHONE.search(text) or _PII_URL.search(text):
                reject("PERSONAL_CONTACT_DATA_PRESENT")
            if _contains_non_latin_letter(text):
                reject("NON_VIETNAMESE_SCRIPT")
            if any(
                SequenceMatcher(None, folded, prior).ratio() >= 0.78
                for prior in combined_texts
            ):
                reject("ACTIVITIES_TOO_SIMILAR")
            if any(
                SequenceMatcher(None, folded, prior).ratio() >= 0.82
                for prior in candidate_texts
            ):
                reject("DUPLICATES_CATALOG_ACTIVITY")
            normalized_titles.add(title_key)
            combined_texts.append(folded)


__all__ = [
    "ParentActivitySuggestionError",
    "ParentActivitySuggestionService",
    "PreparedParentActivitySuggestion",
]
