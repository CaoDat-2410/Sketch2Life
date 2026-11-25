"""Regression: byte-fragment tokens must not bypass the drawing JSON constraint.

Uses the real lm-format-enforcer with a tiny byte-level tokenizer in which a
Vietnamese character is split across two tokens, mirroring Qwen byte-level BPE.
No model, network or GPU is used.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("lmformatenforcer")
from lmformatenforcer import JsonSchemaParser  # noqa: E402
from lmformatenforcer.tokenenforcer import (  # noqa: E402
    TokenEnforcer,
    TokenEnforcerTokenizerData,
)

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))
SPEC = importlib.util.spec_from_file_location(
    "sketch2life_modal_drawing_byte_fragments", MODAL_DIR / "drawing_vlm_app.py"
)
assert SPEC is not None and SPEC.loader is not None
drawing_worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(drawing_worker)

_ASCII = list('0123456789.{}[]":, ') + list("abcdefghijklmnopqrstuvwxyz_")
_PIECES: list[bytes] = [b"<eos>"] + [c.encode() for c in _ASCII] + [b"\xc6", b"\xb0"]
EOS = 0
FRAG_A = len(_PIECES) - 2  # first byte of "ư" (U+01B0)
FRAG_B = len(_PIECES) - 1


class ByteTokenizer:
    eos_token_id = EOS
    all_special_ids = [EOS]

    def __len__(self) -> int:
        return len(_PIECES)

    def encode(self, text: str) -> list[int]:
        return [_PIECES.index(ch.encode()) for ch in text]

    def decode(self, ids: list[int]) -> str:
        return b"".join(_PIECES[i] for i in ids if i != EOS).decode("utf-8", errors="replace")


def _enforcer() -> TokenEnforcer:
    data = drawing_worker._build_qwen_tokenizer_data(
        ByteTokenizer(), TokenEnforcerTokenizerData, eos_token_id=EOS
    )
    return TokenEnforcer(data, JsonSchemaParser(drawing_worker._drawing_output_json_schema()))


def _ids(text: str) -> list[int]:
    return ByteTokenizer().encode(text)


PROMPT = [_PIECES.index(b"0")]
_V2_DONE = (
    '{"main_subject":{"label":"rua","visible_features":["mai"],"facing":"left",'
    '"box":[1,1,5,5]},"secondary_subjects":[],"confidence":0.8}'
)


def _allowed_after(enforcer: TokenEnforcer, generated: list[int]) -> set[int]:
    """Feed tokens one at a time after a prompt, as HF generate does."""
    seq = list(PROMPT)
    enforcer.get_allowed_tokens(seq)
    for token in generated:
        seq.append(token)
        allowed = enforcer.get_allowed_tokens(seq)
    return set(allowed.allowed_tokens) if generated else set(enforcer.get_allowed_tokens(seq).allowed_tokens)


def test_fragment_tokens_are_not_empty_new_word_tokens() -> None:
    captured: dict[str, list[tuple[int, str, bool]]] = {}

    def capture(regular_tokens, decode, eos, *, use_bitmask, vocab_size):
        captured["tokens"] = regular_tokens

    drawing_worker._build_qwen_tokenizer_data(ByteTokenizer(), capture, eos_token_id=EOS)
    by_id = {tid: (text, new_word) for tid, text, new_word in captured["tokens"]}
    for frag in (FRAG_A, FRAG_B):
        text, new_word = by_id[frag]
        assert text != "", "fragment token must not be an empty prefix-tree entry"


def test_after_closing_brace_only_eos_is_allowed() -> None:
    enforcer = _enforcer()
    allowed = _allowed_after(enforcer, _ids(_V2_DONE))
    assert EOS in allowed
    assert FRAG_A not in allowed and FRAG_B not in allowed


def test_split_vietnamese_character_inside_string_is_still_allowed() -> None:
    enforcer = _enforcer()
    prefix = _ids('{"main_subject":{"label":"r')
    assert FRAG_A in _allowed_after(enforcer, prefix)
    after_first = prefix + [FRAG_A]
    assert FRAG_B in _allowed_after(_enforcer(), after_first)
    rest = _V2_DONE.split('"label":"rua"')[1]
    text = ByteTokenizer().decode(
        _ids('{"main_subject":{"label":"r') + [FRAG_A, FRAG_B] + _ids("a\"" + rest)
    )
    assert json.loads(text)["main_subject"]["label"] == "rưa"


def test_extra_data_is_classified_without_text() -> None:
    private = _V2_DONE + "ư"
    diagnostics = drawing_worker._drawing_json_diagnostics(private)
    assert diagnostics["json_error_type"] == "ExtraData"
    assert private not in repr(diagnostics)


def test_box_values_are_a_closed_enum_0_to_20() -> None:
    head = '{"main_subject":{"label":"rua","visible_features":["mai"],"facing":"left","box":{"left":'
    after_two = _allowed_after(_enforcer(), _ids(head + "2"))
    pieces = {i: p for i, p in enumerate(_PIECES)}
    allowed_text = {pieces[i] for i in after_two}
    assert b"0" in allowed_text and b"," in allowed_text  # 20 or just 2
    assert b"5" not in allowed_text and b"9" not in allowed_text  # 25 / 29 are out of the grid
    after_one = {pieces[i] for i in _allowed_after(_enforcer(), _ids(head + "1"))}
    assert b"5" in after_one  # 15 is valid
