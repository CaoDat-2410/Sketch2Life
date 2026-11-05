from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
MODAL_DIR = Path(__file__).resolve().parents[1]
BACKEND_SRC = REPO_ROOT / "backend" / "src"
for import_path in (str(MODAL_DIR), str(BACKEND_SRC)):
    if import_path not in sys.path:
        sys.path.insert(0, import_path)

MODULE_SPEC = importlib.util.spec_from_file_location(
    "sketch2life_modal_language_audio_app",
    MODAL_DIR / "language_audio_app.py",
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
story_worker = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(story_worker)

from sketch2life.contracts.schemas.ai_story import StoryRevisionDraftV1


def _valid_story() -> dict[str, Any]:
    return {
        "schema_version": "sketch2life.story-revision.v1",
        "language": "vi",
        "title": "Hành trình của bướm",
        "story": {
            "opening": "Trên chiếc lá có một chấm trứng nhỏ.",
            "middle": "Trứng nở thành sâu bướm. Sâu bướm ăn lá, lớn lên rồi hóa nhộng.",
            "ending": "Bướm trưởng thành chui ra khỏi nhộng và bay đến bông hoa.",
        },
        "duration_ms": 30_000,
        "scenes": [
            {
                "scene_index": index,
                "title": f"Cảnh {index}",
                "action": "Một chấm trứng nằm trên chiếc lá."
                if index == 1
                else "Sâu bướm quan sát chiếc lá.",
                "visual_prompt": "Giữ nét cánh bướm đơn giản, nhất quán với tranh.",
                "narration": "Cùng quan sát chiếc lá.",
                "start_ms": (index - 1) * 6_000,
                "duration_ms": 6_000,
                "character_anchors": ["viền cánh tròn", "thân bướm mảnh"],
            }
            for index in range(1, 6)
        ],
    }


def _parse(payload: dict[str, Any] | str) -> dict[str, Any]:
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    return story_worker._parse_story_output(text, {"confirmed_subject": "bướm"})


def _valid_content() -> dict[str, Any]:
    story = _valid_story()
    return {
        "title": story["title"],
        "story": story["story"],
        "scenes": [
            {
                key: scene[key]
                for key in ("title", "action", "visual_prompt", "narration", "character_anchors")
            }
            for scene in story["scenes"]
        ],
    }


def _parse_content(payload: dict[str, Any] | str) -> dict[str, Any]:
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    return story_worker._parse_story_content_output(text)


def _assert_rejected(payload: dict[str, Any] | str, reason_code: str) -> None:
    with pytest.raises(story_worker.StoryOutputValidationError) as error:
        _parse(payload)
    assert error.value.reason_code == reason_code
    assert str(error.value) == "MODAL_MODEL_OUTPUT_INVALID"


def test_valid_modal_story_matches_backend_contract() -> None:
    parsed = _parse(_valid_story())
    backend_contract = StoryRevisionDraftV1.model_validate(parsed)
    assert backend_contract.model_dump() == parsed
    assert len(parsed["scenes"]) == 5
    assert parsed["duration_ms"] == 30_000


def test_valid_model_content_is_assembled_and_matches_backend_contract() -> None:
    content = _parse_content(_valid_content())
    assembled = story_worker._assemble_parent_story_output(content)
    parsed = _parse(assembled)
    backend_contract = StoryRevisionDraftV1.model_validate(parsed)

    assert backend_contract.model_dump() == parsed
    assert [scene["scene_index"] for scene in parsed["scenes"]] == [1, 2, 3, 4, 5]
    assert [scene["start_ms"] for scene in parsed["scenes"]] == [0, 6_000, 12_000, 18_000, 24_000]
    assert [scene["duration_ms"] for scene in parsed["scenes"]] == [6_000] * 5
    assert parsed["duration_ms"] == 30_000


def test_parent_story_generation_schema_uses_compact_fields_with_srs_scene_count() -> None:
    schema = story_worker._parent_story_content_json_schema()
    scene_schema = schema["properties"]["scenes"]
    scene_fields = scene_schema["items"]["properties"]

    assert scene_schema["minItems"] == scene_schema["maxItems"] == 5
    assert scene_fields["visual_prompt"]["maxLength"] == 180
    assert scene_fields["action"]["maxLength"] == 120
    assert scene_fields["narration"]["maxLength"] == 120
    assert scene_fields["character_anchors"]["maxItems"] == 2
    assert story_worker.STORY_GENERATION_BUDGET == 4_096


def test_generation_diagnostics_report_json_shape_without_generated_text() -> None:
    complete = story_worker._json_output_diagnostics(
        '{"steps":[{"instruction":"short"}]}'
    )
    partial = story_worker._json_output_diagnostics(
        '{"steps":[{"instruction":"unfinished'
    )

    assert complete["json_complete"] is True
    assert complete["json_root_keys"] == ["steps"]
    assert partial["json_complete"] is False
    assert partial["unterminated_string_key"] == "instruction"
    assert partial["unterminated_string_character_count"] == len("unfinished")
    assert "unfinished" not in str(partial)


def test_generation_pad_uses_model_eos_token_not_tokenizer_alias() -> None:
    model = type(
        "Model",
        (),
        {"generation_config": type("Config", (), {"eos_token_id": 248044})()},
    )()
    tokenizer = type("Tokenizer", (), {"eos_token_id": 248046})()

    assert story_worker._generation_pad_token_id(model, tokenizer) == 248044


def test_lmfe_token_data_excludes_model_eos_from_regular_tokens() -> None:
    from lmformatenforcer.tokenenforcer import TokenEnforcerTokenizerData

    class FakeTokenizer:
        eos_token_id = 7

        def __init__(self) -> None:
            self.all_special_ids = [9]

        def __len__(self) -> int:
            return 10

        def encode(self, text: str) -> list[int]:
            return [0] if text == "0" else [1]

        def decode(self, token_ids: list[int]) -> str:
            return "".join({0: "0", 1: "x", 7: "<eos>", 9: "<special>"}.get(item, "�") for item in token_ids)

    tokenizer = FakeTokenizer()
    data = story_worker._build_lmfe_tokenizer_data(
        tokenizer,
        TokenEnforcerTokenizerData,
        eos_token_id=7,
    )

    assert 7 not in {token_id for token_id, _, _ in data.regular_tokens}
    assert 9 not in {token_id for token_id, _, _ in data.regular_tokens}
    assert data.eos_token_id == 7


def test_vietnamese_characters_keep_json_parser_inside_bounded_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from lmformatenforcer import JsonSchemaParser

    monkeypatch.setenv(
        "LMFE_DEFAULT_ALPHABET", story_worker.LMFE_VIETNAMESE_JSON_ALPHABET
    )
    parser = JsonSchemaParser(
        {
            "type": "object",
            "properties": {
                "value": {"type": "string", "minLength": 1, "maxLength": 4}
            },
            "required": ["value"],
            "additionalProperties": False,
        }
    )
    vietnamese_prefix = '{"value":"b' + chr(0x01B0) + chr(0x1EDB)
    for character in vietnamese_prefix:
        parser = parser.add_character(character)

    assert parser.object_stack
    assert parser.can_end() is False
    assert parser.shortcut_key() == ("json_freetext", 3, 1, 4)
    assert '"' in parser.get_allowed_characters()


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda value: value.update(extra="not allowed"), "CONTENT_SCHEMA_INVALID"),
        (lambda value: value.pop("title"), "CONTENT_SCHEMA_INVALID"),
        (lambda value: value.update(title="t" * 121), "CONTENT_FIELDS_INVALID"),
        (lambda value: value.update(scenes=value["scenes"][:4]), "CONTENT_FIELDS_INVALID"),
        (
            lambda value: value["scenes"][0].update(extra="not allowed"),
            "CONTENT_SCENE_SCHEMA_INVALID",
        ),
        (
            lambda value: value["scenes"][0].update(action="a" * 501),
            "CONTENT_SCENE_TEXT_INVALID",
        ),
        (
            lambda value: value["scenes"][0].update(character_anchors=[]),
            "CONTENT_SCENE_ANCHORS_INVALID",
        ),
        (
            lambda value: value["scenes"][0].update(character_anchors=["a" * 121]),
            "CONTENT_SCENE_ANCHORS_INVALID",
        ),
    ],
)
def test_content_parser_rejects_invalid_model_content(mutate: Any, reason: str) -> None:
    payload = _valid_content()
    mutate(payload)
    with pytest.raises(story_worker.StoryOutputValidationError) as error:
        _parse_content(payload)
    assert error.value.reason_code == reason
    assert str(error.value) == "MODAL_MODEL_OUTPUT_INVALID"


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("not json", "CONTENT_JSON_INVALID"),
        ('{"title":"one","title":"two"}', "DUPLICATE_JSON_KEY"),
    ],
)
def test_content_parser_rejects_invalid_json(text: str, reason: str) -> None:
    with pytest.raises(story_worker.StoryOutputValidationError) as error:
        _parse_content(text)
    assert error.value.reason_code == reason


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("preface {} ", "JSON_INVALID"),
        ('{"schema_version":"x","schema_version":"y"}', "DUPLICATE_JSON_KEY"),
        ("{} trailing", "JSON_INVALID"),
    ],
)
def test_parser_rejects_non_json_and_duplicate_keys(text: str, reason: str) -> None:
    _assert_rejected(text, reason)


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda value: value.update(extra="not allowed"), "TOP_LEVEL_SCHEMA_INVALID"),
        (lambda value: value.pop("language"), "TOP_LEVEL_SCHEMA_INVALID"),
        (lambda value: value.update(schema_version="wrong"), "STORY_FIELDS_INVALID"),
        (lambda value: value.update(language="en"), "STORY_FIELDS_INVALID"),
        (lambda value: value.update(title=" " * 121), "STORY_FIELDS_INVALID"),
        (lambda value: value.update(title="t" * 121), "STORY_FIELDS_INVALID"),
        (lambda value: value["story"].update(opening=""), "STORY_FIELDS_INVALID"),
        (lambda value: value["story"].update(middle="m" * 901), "STORY_FIELDS_INVALID"),
        (lambda value: value.update(scenes=value["scenes"][:4]), "STORY_FIELDS_INVALID"),
        (
            lambda value: value.update(scenes=value["scenes"] * 4),
            "STORY_FIELDS_INVALID",
        ),
        (lambda value: value.update(duration_ms=True), "STORY_FIELDS_INVALID"),
        (lambda value: value.update(duration_ms=29_999), "STORY_FIELDS_INVALID"),
        (
            lambda value: value.update(story={**value["story"], "unexpected": "key"}),
            "STORY_FIELDS_INVALID",
        ),
        (
            lambda value: value["scenes"][0].update(title="t" * 101),
            "SCENE_FIELDS_INVALID",
        ),
        (
            lambda value: value["scenes"][0].update(action="a" * 501),
            "SCENE_FIELDS_INVALID",
        ),
        (
            lambda value: value["scenes"][0].update(visual_prompt="v" * 901),
            "SCENE_FIELDS_INVALID",
        ),
        (
            lambda value: value["scenes"][0].update(narration="n" * 501),
            "SCENE_FIELDS_INVALID",
        ),
        (
            lambda value: value["scenes"][0].update(character_anchors=["a" * 121]),
            "SCENE_FIELDS_INVALID",
        ),
        (
            lambda value: value["scenes"][0].update(character_anchors=[]),
            "SCENE_FIELDS_INVALID",
        ),
        (
            lambda value: value["scenes"][0].update(character_anchors=[" "]),
            "SCENE_FIELDS_INVALID",
        ),
        (lambda value: value["scenes"][0].update(scene_index=True), "SCENE_FIELDS_INVALID"),
        (lambda value: value["scenes"][0].update(start_ms=False), "SCENE_FIELDS_INVALID"),
        (
            lambda value: value["scenes"][0].update(duration_ms=20_001),
            "SCENE_FIELDS_INVALID",
        ),
        (
            lambda value: value["scenes"][0].update(extra="not allowed"),
            "SCENE_FIELDS_INVALID",
        ),
        (lambda value: value["scenes"][1].update(start_ms=5_000), "TIMELINE_INVALID"),
        (lambda value: value["scenes"][0].update(duration_ms=5_000), "TIMELINE_INVALID"),
    ],
)
def test_parser_rejects_contract_violations(mutate: Any, reason: str) -> None:
    payload = _valid_story()
    mutate(payload)
    _assert_rejected(payload, reason)


def test_parser_rejects_butterfly_fact_failure_separately() -> None:
    payload = _valid_story()
    payload["story"]["ending"] = "Trứng nở thành bướm. Bướm đi tìm tổ."
    _assert_rejected(payload, "EDUCATIONAL_FACT_INVALID")


def test_fact_validation_uses_canonical_story_section_order() -> None:
    payload = _valid_story()
    payload["story"] = {
        "ending": payload["story"]["ending"],
        "opening": payload["story"]["opening"],
        "middle": payload["story"]["middle"],
    }
    parsed = _parse(payload)
    assert list(parsed["story"]) == ["opening", "middle", "ending"]


def test_constrained_decoder_receives_worker_story_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}
    lmfe = ModuleType("lmformatenforcer")
    tokenenforcer = ModuleType("lmformatenforcer.tokenenforcer")

    class FakeJsonSchemaParser:
        def __init__(self, schema: dict[str, Any]) -> None:
            captured["schema"] = schema

    class FakeTokenEnforcerTokenizerData:
        pass

    class FakeTokenEnforcer:
        def __init__(self, tokenizer_data: object, parser: FakeJsonSchemaParser) -> None:
            captured["tokenizer_data"] = tokenizer_data
            captured["parser"] = parser

        def get_allowed_tokens(self, token_ids: list[int]) -> object:
            captured["token_ids"] = token_ids
            return type("Allowed", (), {"allowed_tokens": [1, 2]})()

    lmfe.JsonSchemaParser = FakeJsonSchemaParser  # type: ignore[attr-defined]
    tokenenforcer.TokenEnforcer = FakeTokenEnforcer  # type: ignore[attr-defined]
    tokenenforcer.TokenEnforcerTokenizerData = FakeTokenEnforcerTokenizerData  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "lmformatenforcer", lmfe)
    monkeypatch.setitem(sys.modules, "lmformatenforcer.tokenenforcer", tokenenforcer)

    def build_tokenizer_data(
        tokenizer: object,
        _data_type: object,
        *,
        eos_token_id: int | list[int] | None = None,
    ) -> str:
        captured["tokenizer"] = tokenizer
        captured["eos_token_id"] = eos_token_id
        return "tokenizer-data"

    monkeypatch.setattr(
        story_worker,
        "_build_lmfe_tokenizer_data",
        build_tokenizer_data,
    )
    monkeypatch.setattr(story_worker, "_CACHED_STORY_VOCAB_DATA", None)
    monkeypatch.setattr(story_worker, "_CACHED_STORY_EOS_IDS", None)

    tokenizer = object()
    prefix_fn = story_worker._build_story_prefix_allowed_tokens_fn(
        tokenizer, eos_token_id=248044
    )
    schema = captured["schema"]
    assert captured["tokenizer"] is tokenizer
    assert captured["eos_token_id"] == 248044
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["title", "story", "scenes"]
    assert set(schema["properties"]) == {"title", "story", "scenes"}
    assert schema["properties"]["scenes"]["minItems"] == 5
    assert schema["properties"]["scenes"]["maxItems"] == 5
    assert schema["properties"]["story"]["required"] == ["opening", "middle", "ending"]
    assert schema["properties"]["scenes"]["items"]["properties"]["visual_prompt"]["maxLength"] == 180
    assert "scene_index" not in schema["properties"]["scenes"]["items"]["properties"]
    assert "start_ms" not in schema["properties"]["scenes"]["items"]["properties"]
    assert "duration_ms" not in schema["properties"]["scenes"]["items"]["properties"]
    assert prefix_fn(0, type("Input", (), {"tolist": lambda _self: [7, 8]})()) == [1, 2]
    assert captured["token_ids"] == [7, 8]


def test_lm_format_enforcer_accepts_only_structural_contract_shapes() -> None:
    lmfe = pytest.importorskip("lmformatenforcer")
    parser_config = pytest.importorskip("lmformatenforcer.characterlevelparser")
    valid = _valid_content()
    alphabet_text = json.dumps(valid, ensure_ascii=False) + "unapproved_field" + ("x" * 121)
    alphabet = "".join(sorted(set(alphabet_text)))

    def schema_allows(payload: dict[str, Any]) -> bool:
        parser = lmfe.JsonSchemaParser(
            story_worker._parent_story_content_json_schema(),
            config=parser_config.CharacterLevelParserConfig(alphabet=alphabet),
        )
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        for character in encoded:
            if character not in parser.get_allowed_characters():
                return False
            parser = parser.add_character(character)
        return parser.can_end()

    assert schema_allows(valid)
    assert not schema_allows({**valid, "extra": "not allowed"})
    assert not schema_allows({**valid, "scenes": valid["scenes"][:4]})
    assert not schema_allows({**valid, "title": "t" * 121})


def test_transformers5_compatible_prefix_adapter_enforces_json_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("lmformatenforcer")

    class CharacterTokenizer:
        def __init__(self) -> None:
            self.tokens = ["<eos>", "0", *list(dict.fromkeys('{"ok":true}'))]
            self.ids = {token: index for index, token in enumerate(self.tokens)}
            self.all_special_ids = [0]
            self.eos_token_id = 0

        def __len__(self) -> int:
            return len(self.tokens)

        def encode(self, text: str) -> list[int]:
            return [self.ids[character] for character in text]

        def decode(
            self,
            token_ids: list[int],
            *,
                skip_special_tokens: bool = False,
                clean_up_tokenization_spaces: bool = True,
        ) -> str:
            del clean_up_tokenization_spaces
            return "".join(
                "" if skip_special_tokens and token_id == 0 else self.tokens[token_id]
                for token_id in token_ids
            )

    monkeypatch.setattr(story_worker, "_CACHED_STORY_VOCAB_DATA", None)
    tokenizer = CharacterTokenizer()
    prefix_fn = story_worker._build_json_prefix_allowed_tokens_fn(
        tokenizer,
        {
            "type": "object",
            "properties": {"ok": {"type": "boolean"}},
            "required": ["ok"],
            "additionalProperties": False,
        },
    )
    prefix = [tokenizer.eos_token_id]

    for character in '{"ok":true}':
        allowed = prefix_fn(0, type("Input", (), {"tolist": lambda _self: prefix})())
        assert tokenizer.ids[character] in allowed
        prefix.append(tokenizer.ids[character])

    terminal_allowed = prefix_fn(
        0, type("Input", (), {"tolist": lambda _self: prefix})()
    )
    assert tokenizer.eos_token_id in terminal_allowed
    assert tokenizer.ids["t"] not in terminal_allowed


def test_parent_story_prompt_spells_out_timeline_and_butterfly_order() -> None:
    prompt = story_worker._parent_story_prompt(
        {
            "confirmed_subject": "bướm",
            "visible_features": ["cánh tròn"],
            "child_age_months": 60,
            "adult_confirmed_idea": "",
            "rewrite_instruction": None,
        }
    )
    assert "đúng 5 cảnh" in prompt
    assert "hệ thống sẽ tự thêm số thứ tự và thời gian" in prompt
    assert "start_ms lần lượt" not in prompt
    assert "trứng”, “sâu bướm”, “nhộng”, “bướm trưởng thành” theo đúng thứ tự" in prompt

    generic_prompt = story_worker._parent_story_prompt(
        {
            "confirmed_subject": "chiếc lá",
            "visible_features": ["gân lá"],
            "child_age_months": 60,
            "adult_confirmed_idea": "",
            "rewrite_instruction": None,
        }
    )
    assert "trứng”" not in generic_prompt
