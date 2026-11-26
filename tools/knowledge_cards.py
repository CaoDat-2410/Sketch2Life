"""Review knowledge cards: list them, read one, approve one (FEAT-094).

    python tools/knowledge_cards.py list
    python tools/knowledge_cards.py show vi.transport.bicycle
    python tools/knowledge_cards.py approve vi.transport.bicycle \
        --reviewer "<name>" --source "<title>|<https url>"

Approving stores a hash of the content. Editing a card afterwards makes it unusable until it is
approved again; raise its ``version`` when you do.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from sketch2life.domain.knowledge_card import (  # noqa: E402
    KnowledgeCardError,
    approve_card,
    is_servable,
    parse_card,
)
from sketch2life.infrastructure.knowledge.card_repository import CARD_DIRECTORY  # noqa: E402


def _load(directory: Path, card_id: str) -> tuple[Path, dict]:
    path = directory / f"{card_id}.json"
    if not path.is_file() or path.parent != directory:
        raise KnowledgeCardError("KNOWLEDGE_CARD_NOT_FOUND", detail=card_id)
    return path, json.loads(path.read_text(encoding="utf-8"))


def _state(raw: dict) -> str:
    card = parse_card(raw)
    if card.status == "APPROVED" and not is_servable(card):
        return "EDITED_AFTER_APPROVAL"
    return card.status


def _show(raw: dict) -> None:
    print(f"{raw['card_id']} v{raw['version']} [{_state(raw)}]")
    print("Chủ thể:", ", ".join(raw["subject_labels"]))
    for fact in raw["facts"]:
        part = f" ({fact['part']})" if fact.get("part") else ""
        print(f"- {fact['kind']}{part}, từ {fact['min_age_months']} tháng: {fact['text']}")
    print("Bối cảnh:", raw["setting"])
    print("Chuyển động:", "; ".join(raw["motion_hints"]))
    for source in raw["sources"]:
        print(f"Nguồn: {source['title']} <{source['url']}> kiểm ngày {source['checked_on']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--directory", type=Path, default=CARD_DIRECTORY)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    commands.add_parser("show").add_argument("card_id")
    approve = commands.add_parser("approve")
    approve.add_argument("card_id")
    approve.add_argument("--reviewer", required=True)
    approve.add_argument("--date", default=date.today().isoformat())
    approve.add_argument("--source", action="append", default=[], metavar="TITLE|URL")
    arguments = parser.parse_args(argv)
    for stream in (sys.stdout,):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    directory = arguments.directory
    try:
        if arguments.command == "list":
            for path in sorted(directory.glob("*.json")):
                raw = json.loads(path.read_text(encoding="utf-8"))
                print(f"{raw['card_id']}\t{_state(raw)}\t{raw['subject_labels'][0]}")
            return 0
        path, raw = _load(directory, arguments.card_id)
        if arguments.command == "show":
            _show(raw)
            return 0
        for entry in arguments.source:
            title, _, url = entry.partition("|")
            raw["sources"].append(
                {"title": title.strip(), "url": url.strip(), "checked_on": arguments.date}
            )
        approved = approve_card(
            parse_card(raw), reviewer=arguments.reviewer, reviewed_on=arguments.date
        )
        path.write_text(
            json.dumps(approved.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"{approved.card_id} APPROVED")
        return 0
    except KnowledgeCardError as error:
        print(error.code)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
