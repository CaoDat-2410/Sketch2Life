"""Conservative no-diagnosis screen for adult-entered free text (BR-20, SRS l.266, FR-C-07 l.501).

The SRS says a health or psychological note only represents a need for help that the adult
enters; it is not a diagnosis, and the system never infers one. This module refuses text that
names a diagnosis. It is a fixed, versioned list of Vietnamese and English diagnosis stems,
matched after a Unicode fold (NFKD, marks removed, ``d`` with stroke mapped to ``d``, lower case)
at the start of a word. Separators (spaces, hyphens, underscores, dots) collapse to one space,
zero-width and other format characters are dropped, and a run of single letters (``a.d.h.d``) is
joined. The list is versioned and conservative, not a medical vocabulary. It infers nothing,
stores nothing and never echoes the matched text. A false
positive costs one rejected label; a false negative is possible (the list is not a medical
vocabulary), which is why the field stays access limited and out of AI context as well.

Pure: no framework, no database, no clock.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Final

SCREEN_VERSION: Final = 2

# Folded stems. A stem matches where a word starts; ``$`` marks a whole word (short acronyms).
_STEMS: Final[tuple[str, ...]] = (
    # Vietnamese (folded: no marks, d for the stroked d)
    "chan doan",
    "tu ky",
    "tu ki",
    "giam chu y",
    "roi loan",
    "tram cam",
    "lo au",
    "dong kinh",
    "tam than phan liet",
    "benh tam than",
    "cham phat trien",
    "khuyet tat tri tue",
    "chung kho doc",
    "thieu nang tri tue",
    # English
    "diagnos",
    "autis",
    "asperger",
    "adhd$",
    "ocd$",
    "ptsd$",
    "asd$",
    "dyslex",
    "dyscalc",
    "dyspraxi",
    "dysgraph",
    "tourette",
    "epilep",
    "schizo",
    "bipolar",
    "depress",
    "anxiety",
    "down syndrome",
    "cerebral palsy",
    "intellectual disabilit",
    "developmental delay",
    "disorder",
    "syndrome",
    "psychosis",
    "psychotic",
)


# Ambiguous without tones ("tang dong" also reads "tặng đồng"): matched on the NFC text with its
# tones, or on the folded text only when the text carries no tone mark at all.
_TONED: Final[tuple[str, ...]] = ("tăng động", "hội chứng", "bại não")
_TONELESS: Final[tuple[str, ...]] = ("tang dong", "hoi chung", "bai nao")
_TONE_MARKS: Final = frozenset("\u0300\u0301\u0303\u0309\u0323")
_SEPARATORS: Final = re.compile(r"[\W_]+")
_SINGLE_LETTERS: Final = re.compile(r"(?<![a-z0-9])(?:[a-z] ){2,}[a-z](?![a-z0-9])")


def _drop_format(text: str) -> str:
    return "".join(ch for ch in text if unicodedata.category(ch) != "Cf")


def _tidy(text: str) -> str:
    return _SEPARATORS.sub(" ", text).strip()


def fold(text: str) -> str:
    """NFKD, marks and format characters removed, stroked d mapped to d, lower case, tidy."""
    decomposed = unicodedata.normalize(
        "NFKD", _drop_format(text).replace("đ", "d").replace("Đ", "D")
    )
    plain = "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()
    return _SINGLE_LETTERS.sub(lambda m: m.group().replace(" ", ""), _tidy(plain))


def _compile(stem: str) -> re.Pattern[str]:
    if stem.endswith("$"):
        return re.compile(r"(?<![a-z0-9])" + re.escape(stem[:-1]) + r"(?![a-z0-9])")
    return re.compile(r"(?<![a-z0-9])" + re.escape(stem))


_PATTERNS: Final[tuple[re.Pattern[str], ...]] = tuple(_compile(stem) for stem in _STEMS)
_WHOLE: Final[tuple[re.Pattern[str], ...]] = tuple(
    re.compile(r"(?<!\w)" + re.escape(stem) + r"(?!\w)") for stem in _TONED
)
_WHOLE_FOLDED: Final[tuple[re.Pattern[str], ...]] = tuple(
    re.compile(r"(?<![a-z0-9])" + re.escape(stem) + r"(?![a-z0-9])") for stem in _TONELESS
)


def looks_like_diagnosis(text: str) -> bool:
    """True when the text names a diagnosis (see the module docstring); never returns the match."""
    folded = fold(text)
    if any(pattern.search(folded) is not None for pattern in _PATTERNS):
        return True
    nfc = _tidy(unicodedata.normalize("NFC", _drop_format(text)).lower())
    if any(pattern.search(nfc) is not None for pattern in _WHOLE):
        return True
    toneless = not any(ch in _TONE_MARKS for ch in unicodedata.normalize("NFD", text))
    return toneless and any(pattern.search(folded) is not None for pattern in _WHOLE_FOLDED)
