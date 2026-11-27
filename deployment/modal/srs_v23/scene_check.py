"""FEAT-094 phase 5: what the Qwen worker looks for in one rendered scene (plan 7.3). Pure code."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from typing import Any

MAX_SHEET_BYTES = 8 * 1024 * 1024
_QUESTIONS = (
    ("new_person_or_animal", "NEW_CHARACTER"),
    ("new_object", "NEW_OBJECT"),
    ("main_subject_changed", "SUBJECT_CHANGED"),
    ("style_changed", "STYLE_CHANGED"),
    ("text_or_logo", "TEXT_OR_LOGO"),
)
KEYFRAME_KIND = "keyframe"
SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [name for name, _code in _QUESTIONS],
    "properties": {name: {"type": "boolean"} for name, _code in _QUESTIONS},
}
PROMPT = (
    "This sheet has six pictures of one short animation made from a child's drawing, in reading order. The top left "
    "picture is the first frame; the other five are later moments. Compare each later moment with the first frame and "
    "answer true only when you clearly see it: new_person_or_animal (a person, a hand, fingers or an animal that is not "
    "in the first frame, also when only partly visible at an edge), new_object (a clearly new large object), "
    "main_subject_changed (the main drawn subject disappears, leaves the picture, turns into a smeared or blurred patch, "
    "loses or grows body parts or changes colour; bending, pecking, turning the head, closing the eyes or lifting a part "
    "is normal and false), style_changed (it no longer looks like the same crayon drawing), text_or_logo (letters, a "
    "logo or a picture inside a frame appear). Small movement and a small camera change are not problems."
)


KEYFRAME_PROMPT = (
    "This sheet has two pictures. The left one is a child's own drawing. The right one is the first frame of an "
    "animation: the same drawn subject placed on a newly painted crayon background. New scenery (sky, ground, trees, "
    "houses, plants, objects of the place) is expected and fine. Answer true only when you clearly see it in the right "
    "picture: new_person_or_animal (a person, a hand, fingers or an animal painted in the background, also a second one "
    "of the same kind as the drawn subject, large or small, flat or realistic), "
    "new_object (always false), main_subject_changed (the drawn subject is missing or unrecognisable), style_changed "
    "(the background is a photograph or a 3D picture instead of a drawing), text_or_logo (letters or a logo)."
)


def read_sheet(data: Any) -> tuple[bytes, str]:
    """The verified sheet and the question that belongs to it."""

    fields = {"sheet_png_b64", "sheet_sha256"}
    if not isinstance(data, dict) or not (
        set(data) == fields or set(data) == fields | {"kind"} and data["kind"] == KEYFRAME_KIND
    ):
        raise ValueError("MODAL_INPUT_NOT_ALLOWED")
    try:
        sheet = base64.b64decode(data["sheet_png_b64"], validate=True)
    except (binascii.Error, TypeError, ValueError):
        raise ValueError("MODAL_INPUT_NOT_ALLOWED") from None
    if (
        not sheet.startswith(b"\x89PNG")
        or len(sheet) > MAX_SHEET_BYTES
        or hashlib.sha256(sheet).hexdigest() != data["sheet_sha256"]
    ):
        raise ValueError("MODAL_INPUT_NOT_ALLOWED")
    return sheet, KEYFRAME_PROMPT if "kind" in data else PROMPT


def problems(answer: str) -> list[str]:
    try:
        value = json.loads(answer)
        if not isinstance(value, dict) or any(type(value.get(name)) is not bool for name, _code in _QUESTIONS):
            raise ValueError
    except (TypeError, ValueError):
        raise RuntimeError("MODAL_MODEL_OUTPUT_INVALID") from None
    return [code for name, code in _QUESTIONS if value[name]]


__all__ = ["KEYFRAME_PROMPT", "PROMPT", "SCHEMA", "problems", "read_sheet"]
