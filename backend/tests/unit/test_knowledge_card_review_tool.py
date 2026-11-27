"""FEAT-094: the owner reviews and approves knowledge cards from the command line."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from sketch2life.infrastructure.knowledge.card_repository import (  # noqa: E402
    CARD_DIRECTORY,
    KnowledgeCardRepository,
)
from tools import knowledge_cards as tool  # noqa: E402


def _copy_card(tmp_path: Path) -> str:
    source = CARD_DIRECTORY / "vi.transport.bicycle.json"
    (tmp_path / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return "vi.transport.bicycle"


def test_show_prints_every_fact_for_the_reviewer(tmp_path, capsys) -> None:
    card_id = _copy_card(tmp_path)

    assert tool.main(["--directory", str(tmp_path), "show", card_id]) == 0

    out = capsys.readouterr().out
    assert "DRAFT" in out and "Hai bánh xe lăn đưa xe tiến tới." in out


def test_approve_needs_a_source_then_makes_the_card_servable(tmp_path, capsys) -> None:
    card_id = _copy_card(tmp_path)
    path = tmp_path / f"{card_id}.json"
    unsourced = {**json.loads(path.read_text(encoding="utf-8")), "sources": []}
    path.write_text(json.dumps(unsourced, ensure_ascii=False), encoding="utf-8")
    base = [
        "--directory",
        str(tmp_path),
        "approve",
        card_id,
        "--reviewer",
        "owner",
        "--date",
        "2026-11-26",
    ]

    assert tool.main(base) == 1
    assert "KNOWLEDGE_CARD_SOURCE_REQUIRED" in capsys.readouterr().out
    assert KnowledgeCardRepository(tmp_path).approved_for_subject("xe đạp") is None

    assert tool.main([*base, "--source", "Nguồn tổng hợp|https://example.test/xe-dap"]) == 0

    approved = KnowledgeCardRepository(tmp_path).approved_for_subject("xe đạp")
    assert approved is not None and approved.reviewed_by == "owner"
    saved = json.loads((tmp_path / f"{card_id}.json").read_text(encoding="utf-8"))
    assert saved["sources"][0]["checked_on"] == "2026-11-26"


def test_list_shows_the_status_of_each_card(tmp_path, capsys) -> None:
    card_id = _copy_card(tmp_path)

    assert tool.main(["--directory", str(tmp_path), "list"]) == 0

    assert f"{card_id}\tDRAFT" in capsys.readouterr().out


def test_every_card_names_the_pages_it_was_compared_with_and_stays_a_draft() -> None:
    cards = KnowledgeCardRepository().all_cards()

    assert len(cards) == 40
    for card in cards:
        assert card.status == "DRAFT" and card.reviewed_by is None, card.card_id
        assert card.sources and all(source.url.startswith("https://") for source in card.sources), card.card_id
