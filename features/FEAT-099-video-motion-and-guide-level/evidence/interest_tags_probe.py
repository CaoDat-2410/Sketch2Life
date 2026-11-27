"""FEAT-099 research: what does today's interest filter make of ordinary Vietnamese notes about a child?

Throwaway, read-only, invented sentences (no child data). Run from the repository root:

    python features/FEAT-099-video-motion-and-guide-level/evidence/interest_tags_probe.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "backend" / "src"))

from sketch2life.application.services.parent_activity_suggestions import interest_tags  # noqa: E402

SENTENCES = [
    "Bé mê ô tô, xe cẩu và máy xúc.",
    "Con thích khủng long.",
    "Bé thích tìm hiểu vũ trụ và phi hành gia.",
    "Thích đồ chơi xếp hình.",
    "Bé thích đá bóng.",
    "Bé hay đi mua sắm cùng mẹ.",
    "Bé thích công chúa và lâu đài.",
    "Con sợ bóng tối, không thích tiếng to.",
    "Bé thích vẽ, thích hát.",
    "Bé thích vẽ và nhạc",
    "Bé thích ăn cay.",
    "Bé khó tập trung lâu.",
]


def main() -> None:
    rows = [{"note": note, "tags": interest_tags(note)} for note in SENTENCES]
    text = json.dumps(rows, ensure_ascii=False, indent=2) + "\n"
    (HERE / "interest_tags.json").write_text(text, encoding="utf-8")
    for row in rows:
        print(row["note"], "->", row["tags"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
