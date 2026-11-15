from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import patch

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))

MODULE_SPEC = importlib.util.spec_from_file_location(
    "sketch2life_modal_svg_topic_stroke_guide_contract",
    MODAL_DIR / "language_audio_app.py",
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
worker = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(worker)


def _valid_guide() -> dict[str, Any]:
    paths = [
        {
            "path_id": f"stroke_{index:02d}",
            "d": f"M {20 + index * 20} 40 C {25 + index * 20} 50 {30 + index * 20} 60 {35 + index * 20} 70",
            "fill": "none",
            "stroke": "#202938",
            "stroke_width": 4,
        }
        for index in range(8)
    ]
    parts = [
        {
            "part_id": f"part_{index:02d}",
            "label_vi": f"Nét {index}",
            "path_ids": [path["path_id"]],
            "depends_on": [],
        }
        for index, path in enumerate(paths, start=1)
    ]
    stages = []
    for index in range(4):
        new_paths = [path["path_id"] for path in paths[index * 2 : index * 2 + 2]]
        part_ids = [part["part_id"] for part in parts[index * 2 : index * 2 + 2]]
        stages.append(
            {
                "step_index": index + 1,
                "instruction_vi": f"Vẽ thêm nét {index + 1}.",
                "part_ids": part_ids,
                "new_path_ids": new_paths,
                "animation_order": list(new_paths),
            }
        )
    return {
        "schema_version": "SvgTopicStrokeGuideContentV1",
        "title_vi": "Con gà",
        "document": {
            "schema_version": "SvgDocumentV1",
            "view_box": "0 0 512 512",
            "paths": paths,
        },
        "parts": parts,
        "stages": stages,
    }


class SvgTopicStrokeGuideContractTests(unittest.TestCase):
    def assert_rejected(
        self, mutate: Callable[[dict[str, Any]], None], expected_code: str
    ) -> None:
        content = _valid_guide()
        mutate(content)
        with self.assertRaisesRegex(RuntimeError, expected_code):
            worker._parse_svg_topic_stroke_guide(
                json.dumps(content, ensure_ascii=False)
            )

    def test_schema_constrains_path_fields_to_worker_and_backend_contract(self) -> None:
        schema = worker._svg_topic_guide_json_schema()
        path_fields = schema["properties"]["document"]["properties"]["paths"]["items"]["properties"]

        self.assertEqual(worker.SVG_TOPIC_GUIDE_MAX_OUTPUT_TOKENS, 12_288)
        self.assertEqual(
            schema["properties"]["document"]["properties"]["paths"]["maxItems"],
            28,
        )
        self.assertEqual(schema["properties"]["parts"]["maxItems"], 28)
        self.assertEqual(path_fields["path_id"]["pattern"], r"^[a-z][a-z0-9_]{0,95}$")
        self.assertEqual(path_fields["d"]["minLength"], 1)
        self.assertEqual(path_fields["d"]["maxLength"], 256)
        self.assertNotIn("pattern", path_fields["d"])
        self.assertFalse({"minLength", "maxLength"} & set(path_fields["path_id"]))
        self.assertEqual(path_fields["fill"]["enum"], ["none"])
        self.assertEqual(path_fields["stroke"]["enum"], ["#202938"])
        self.assertEqual(path_fields["stroke_width"]["minimum"], 3)
        self.assertEqual(path_fields["stroke_width"]["maximum"], 7)

    def test_chicken_schema_uses_bounded_open_path_pattern_without_length_keywords(self) -> None:
        schema = worker._svg_topic_guide_json_schema(chicken_reference=True)
        path_data = schema["properties"]["document"]["properties"]["paths"]["items"]["properties"]["d"]

        self.assertEqual(path_data["pattern"], r"^[MLCQ0-9+.,\-eE\s]{1,256}$")
        self.assertFalse({"minLength", "maxLength"} & set(path_data))
        self.assertIsNotNone(worker.re.fullmatch(path_data["pattern"], "M 20 40 C 25 50 30 60 35 70"))
        self.assertIsNone(worker.re.fullmatch(path_data["pattern"], "M 20 40 Z"))
        self.assertIsNone(worker.re.fullmatch(path_data["pattern"], "M" + " 20" * 86))

    def test_chicken_schema_is_supported_by_pinned_lmfe_parser(self) -> None:
        try:
            from lmformatenforcer import JsonSchemaParser
        except ImportError:
            self.skipTest("LMFE is installed only in the pinned Modal worker image")

        schema = worker._svg_topic_guide_json_schema(chicken_reference=True)
        worker.os.environ["LMFE_DEFAULT_ALPHABET"] = worker.LMFE_VIETNAMESE_JSON_ALPHABET
        prefix = (
            '{"schema_version":"SvgTopicStrokeGuideContentV1",'
            '"title_vi":"Chicken","document":{"schema_version":"SvgDocumentV1",'
            '"view_box":"0 0 512 512","paths":[{"path_id":"chicken_body","d":"'
        )
        parser = JsonSchemaParser(schema)
        for character in prefix:
            parser = parser.add_character(character)
        allowed_at_path_start = parser.get_allowed_characters()
        self.assertIn("M", allowed_at_path_start)
        self.assertNotIn("Z", allowed_at_path_start)

        exactly_bounded_path = "M" + " 20" * 85
        self.assertEqual(len(exactly_bounded_path), 256)
        for character in exactly_bounded_path:
            parser = parser.add_character(character)
        allowed_at_path_limit = parser.get_allowed_characters()
        self.assertIn('"', allowed_at_path_limit)
        self.assertNotIn("M", allowed_at_path_limit)
        self.assertNotIn("Z", allowed_at_path_limit)

    def test_svg_decoder_failure_logs_are_detailed_but_content_free(self) -> None:
        decoder_values = {
            "callback_calls": 12_289,
            "force_stop_parser_calls": 0,
            "last_parser_can_end": False,
            "last_model_eos_allowed": False,
            "last_parser_state_class": "StringParser",
            "final_model_eos_was_allowed_at_previous_prefix": False,
            "final_model_eos_prefix_parser_can_end": False,
            "generated_special_token_count": 0,
            "generated_non_eos_special_token_count": 0,
            "enforcer_decoder_decoded_character_count": 6_534,
            "enforcer_decoder_json_complete": False,
            "enforcer_decoder_json_error_type": "JSONDecodeError",
            "enforcer_decoder_json_error_category": "UNTERMINATED_STRING",
            "enforcer_decoder_json_error_position": 6_534,
            "enforcer_decoder_unterminated_string_character_count": 0,
            "enforcer_decoder_unterminated_string_key": "d",
            "replay_parser_can_end": False,
            "replay_parser_error_count": 0,
            "incremental_vs_replay_can_end_mismatch": False,
            "replay_parser_diagnostic_error": False,
            "enforcer_decoder_json_error": "raw generated snippet",
            "generated_text": "private SVG content",
        }
        diagnostic: dict[str, Any] = {"event": "svg_topic_stroke_guide_output_truncated"}

        with patch.object(
            worker,
            "_json_prefix_decoder_diagnostics",
            return_value=decoder_values,
        ):
            worker._attach_svg_topic_guide_decoder_diagnostics(
                diagnostic,
                object(),
                generated=object(),
                input_token_count=1_653,
            )

        self.assertEqual(diagnostic["callback_calls"], 12_289)
        self.assertFalse(diagnostic["last_parser_can_end"])
        self.assertFalse(diagnostic["last_model_eos_allowed"])
        self.assertEqual(diagnostic["enforcer_decoder_json_error_type"], "JSONDecodeError")
        self.assertEqual(
            diagnostic["enforcer_decoder_json_error_category"], "UNTERMINATED_STRING"
        )
        self.assertEqual(diagnostic["active_json_string_field"], "d")
        self.assertEqual(diagnostic["replay_parser_error_count"], 0)
        self.assertNotIn("enforcer_decoder_json_error", diagnostic)
        self.assertNotIn("enforcer_decoder_unterminated_string_key", diagnostic)
        self.assertNotIn("generated_text", diagnostic)
        self.assertNotIn("raw generated snippet", repr(diagnostic))
        self.assertNotIn("private SVG content", repr(diagnostic))

        decoder_values["enforcer_decoder_unterminated_string_key"] = "private field"
        safe = worker._safe_svg_topic_guide_decoder_diagnostics(decoder_values)
        self.assertNotIn("active_json_string_field", safe)

    def test_generation_requires_model_eos_before_json_parse(self) -> None:
        is_complete = worker._svg_topic_guide_generation_is_complete

        self.assertTrue(
            is_complete(
                output_token_count=1200,
                max_new_tokens=6144,
                final_token_id=2,
                eos_token_ids=[2],
            )
        )
        self.assertFalse(
            is_complete(
                output_token_count=6144,
                max_new_tokens=6144,
                final_token_id=2,
                eos_token_ids=[2],
            )
        )
        self.assertFalse(
            is_complete(
                output_token_count=1200,
                max_new_tokens=6144,
                final_token_id=17,
                eos_token_ids=[2],
            )
        )

    def test_json_diagnostic_contains_counts_not_generated_text(self) -> None:
        parse_error = json.JSONDecodeError(
            "Expecting value", '{"private":"generated text"', 10
        )
        diagnostic = worker._svg_topic_guide_diagnostic_payload(
            reason_code="SVG_TOPIC_GUIDE_JSON_INVALID",
            output_token_count=1200,
            input_token_count=800,
            max_new_tokens=6144,
            final_token_id=2,
            eos_token_ids=[2],
            tokenizer_eos_token_id=2,
            decoded_character_count=64,
            generation_seconds=240.5,
            parse_error=parse_error,
        )

        self.assertEqual(diagnostic["reason_code"], "SVG_TOPIC_GUIDE_JSON_INVALID")
        self.assertEqual(diagnostic["json_error_type"], "JSONDecodeError")
        self.assertEqual(diagnostic["json_error_category"], "EXPECTING_VALUE")
        self.assertEqual(diagnostic["json_error_position"], 10)
        self.assertEqual(diagnostic["decoded_character_count"], 64)
        self.assertFalse(diagnostic["token_limit_reached"])
        self.assertTrue(diagnostic["ended_with_model_eos"])
        self.assertNotIn("private", repr(diagnostic))
        self.assertNotIn("generated text", repr(diagnostic))

    def test_unterminated_svg_path_diagnostic_identifies_only_allowlisted_field(self) -> None:
        diagnostic = worker._json_output_diagnostics(
            '{"document":{"paths":[{"d":"M 10 20 C private generated path'
        )

        self.assertFalse(diagnostic["json_complete"])
        self.assertEqual(diagnostic["json_error_category"], "UNTERMINATED_STRING")
        self.assertEqual(diagnostic["active_json_string_field"], "d")
        self.assertGreater(diagnostic["unterminated_string_character_count"], 0)
        self.assertNotIn("private generated path", repr(diagnostic))

    def test_worker_accepts_valid_four_stage_progressive_guide(self) -> None:
        parsed = worker._parse_svg_topic_stroke_guide(
            json.dumps(_valid_guide(), ensure_ascii=False)
        )

        self.assertEqual(len(parsed["document"]["paths"]), 8)
        self.assertEqual(len(parsed["stages"]), 4)
        self.assertEqual(
            parsed["stages"][-1]["new_path_ids"], ["stroke_06", "stroke_07"]
        )

    def test_worker_reports_safe_specific_path_failures(self) -> None:
        cases = [
            (
                lambda value: value["document"]["paths"][0].update(path_id="bad id"),
                "SVG_TOPIC_GUIDE_PATH_ID_INVALID",
            ),
            (
                lambda value: value["document"]["paths"][0].update(
                    d="M 20 40 A 1 1 0 0 0 30 50"
                ),
                "SVG_TOPIC_GUIDE_PATH_DATA_INVALID",
            ),
            (
                lambda value: value["document"]["paths"][0].update(fill="#ffffff"),
                "SVG_TOPIC_GUIDE_PATH_FILL_INVALID",
            ),
            (
                lambda value: value["document"]["paths"][0].update(stroke="red"),
                "SVG_TOPIC_GUIDE_PATH_STROKE_INVALID",
            ),
            (
                lambda value: value["document"]["paths"][1].update(stroke="#ffffff"),
                "SVG_TOPIC_GUIDE_PATH_COLOR_INCONSISTENT",
            ),
            (
                lambda value: value["document"]["paths"][0].update(stroke_width=12),
                "SVG_TOPIC_GUIDE_PATH_WIDTH_INVALID",
            ),
            (
                lambda value: value["document"]["paths"][1].update(
                    d=value["document"]["paths"][0]["d"]
                ),
                "SVG_TOPIC_GUIDE_PATH_DUPLICATE_GEOMETRY",
            ),
            (
                lambda value: value["document"]["paths"][0].update(extra="unexpected"),
                "SVG_TOPIC_GUIDE_PATH_FIELDS_INVALID",
            ),
            (
                lambda value: value["document"]["paths"][1].update(
                    path_id=value["document"]["paths"][0]["path_id"]
                ),
                "SVG_TOPIC_GUIDE_PATH_ID_DUPLICATE",
            ),
        ]
        for mutate, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                self.assert_rejected(mutate, expected_code)

    def test_example_prompt_matches_constrained_path_contract(self) -> None:
        prompt = worker._svg_topic_guide_prompt(
            {
                "schema_version": "sketch2life.svg-topic-stroke-guide-input.v1",
                "topic": "con gà",
                "difficulty": "beginner",
            },
            reference_source={"asset_id": "approved-reference"},
        )

        self.assertIn('"path_id":"chicken_body"', prompt)
        self.assertIn('"stroke":"#202938"', prompt)
        self.assertIn("path_id chỉ dùng chữ thường ASCII", prompt)
        self.assertIn("M/L/C/Q/Z viết hoa", prompt)
        self.assertIn("hộp bao control-point rộng ít nhất 200 và cao ít nhất 90", prompt)
        self.assertIn("không vẽ thân thành một nét ngang mỏng", prompt)
        self.assertIn("d ngắn hơn 256 ký tự", prompt)
        self.assertIn("không dùng lại cùng chuỗi d", prompt)
        self.assertIn("Path ví dụ phía trên chỉ minh họa cú pháp", prompt)
        self.assertIn("kéo ra thành mỏ dài ít nhất 24 đơn vị viewBox", prompt)
        self.assertIn("mỗi chân đi xuống ít nhất 100 đơn vị", prompt)
        self.assertIn("điểm cuối mỏ phải cách điểm đầu ít nhất 24 đơn vị", prompt)
        self.assertIn("chicken_neck bắt đầu trong vùng thân và kết thúc trong vùng đầu", prompt)
        self.assertIn("một đầu chicken_wing phải nằm trong vùng thân", prompt)
        self.assertIn("một đầu chicken_tail phải chạm vùng phía sau thân", prompt)
        self.assertIn("một đầu chicken_comb phải nằm trong vùng đầu", prompt)
        self.assertIn("điểm đầu chicken_beak phải nằm trong vùng đầu", prompt)
        self.assertIn("không để khe hở và không dừng gần bên cạnh", prompt)

    @staticmethod
    def _catalog_paths(count: int = 8) -> list[dict[str, Any]]:
        return [
            {
                "path_id": f"oc_path_{index:03d}",
                "d": f"M {index} 10 L {index + 2} 12",
                "fill": "#d8aa64",
                "stroke": "#202938",
                "stroke_width": 1,
                "stroke_linecap": "round",
                "stroke_linejoin": "round",
            }
            for index in range(1, count + 1)
        ]

    @staticmethod
    def _segmentable_catalog_paths() -> list[dict[str, Any]]:
        long_contour = "M 5 5 " + " ".join(
            "c 1 0 1 1 2 1" for _ in range(28)
        )
        paths = [
            {
                "path_id": "source_contour",
                "d": long_contour,
                "fill": "#d8aa64",
                "stroke": "#202938",
                "stroke_width": 1,
                "stroke_linecap": "round",
                "stroke_linejoin": "round",
            }
        ]
        paths.extend(
            {
                "path_id": f"source_detail_{index:02d}",
                "d": f"M {index + 10} 60 L {index + 20} 65",
                "fill": "#d8aa64",
                "stroke": "#202938",
                "stroke_width": 1,
                "stroke_linecap": "round",
                "stroke_linejoin": "round",
            }
            for index in range(7)
        )
        return paths

    @staticmethod
    def _catalog_plan(paths: list[dict[str, Any]]) -> dict[str, Any]:
        stage_count = 4
        return {
            "schema_version": "SvgOpenclipartSourceStrokePlanV3",
            "title_vi": "Con mèo",
            "stages": [
                {
                    "label_vi": f"Nét {index}",
                    "instruction_vi": f"Vẽ thêm phần {index}.",
                }
                for index in range(1, stage_count + 1)
            ],
            "path_stage_assignments": {
                path["path_id"]: min((index // 2) + 1, stage_count)
                for index, path in enumerate(paths)
            },
        }

    def test_catalog_schema_requires_every_source_path_as_one_assignment_key(self) -> None:
        paths = self._catalog_paths(20)
        schema = worker._svg_catalog_source_plan_schema(paths)
        assignment_schema = schema["properties"]["path_stage_assignments"]

        self.assertEqual(
            schema["properties"]["schema_version"]["enum"],
            ["SvgOpenclipartSourceStrokePlanV3"],
        )
        self.assertNotIn(
            "step_index",
            schema["properties"]["stages"]["items"]["properties"],
        )
        self.assertEqual(assignment_schema["required"], [path["path_id"] for path in paths])
        self.assertEqual(
            set(assignment_schema["properties"]),
            {path["path_id"] for path in paths},
        )
        self.assertFalse(assignment_schema["additionalProperties"])
        self.assertEqual(
            assignment_schema["properties"][paths[0]["path_id"]]["enum"],
            list(range(1, 9)),
        )
        self.assertNotIn("path_ids", schema["properties"]["stages"]["items"]["properties"])
        self.assertNotIn("step_index", schema["properties"]["stages"]["items"]["properties"])

    def test_catalog_schema_supports_twenty_source_derived_segments(self) -> None:
        paths = self._catalog_paths(20)
        schema = worker._svg_catalog_source_plan_schema(paths)
        assignments = schema["properties"]["path_stage_assignments"]

        self.assertEqual(assignments["required"], [path["path_id"] for path in paths])
        self.assertEqual(len(assignments["properties"]), 20)
        self.assertFalse(assignments["additionalProperties"])

    def test_catalog_assignment_schema_is_accepted_by_pinned_lmfe_parser(self) -> None:
        try:
            from lmformatenforcer import JsonSchemaParser
        except ImportError:
            self.skipTest("LMFE is installed only in the pinned Modal worker image")

        paths = self._catalog_paths(20)
        schema = worker._svg_catalog_source_plan_schema(paths)
        encoded = json.dumps(self._catalog_plan(paths), ensure_ascii=False)
        worker.os.environ["LMFE_DEFAULT_ALPHABET"] = worker.LMFE_VIETNAMESE_JSON_ALPHABET
        parser = JsonSchemaParser(schema)
        for character in encoded:
            self.assertIn(character, parser.get_allowed_characters())
            parser = parser.add_character(character)
        self.assertTrue(parser.can_end())

    def test_catalog_plan_derives_complete_ordered_stage_paths_from_assignments(self) -> None:
        paths = self._catalog_paths()
        raw = json.dumps(self._catalog_plan(paths), ensure_ascii=False)

        parsed = worker._parse_svg_catalog_source_plan(raw, paths)
        flattened = [
            path_id for stage in parsed["stages"] for path_id in stage["path_ids"]
        ]

        self.assertEqual(len(parsed["stages"]), 4)
        self.assertEqual(flattened, [path["path_id"] for path in paths])
        self.assertEqual(len(flattened), len(set(flattened)))

    def test_source_path_segmenter_handles_relative_repeated_commands_and_close_edges(self) -> None:
        segments = worker._parse_source_svg_path_segments(
            "M 10 10 c 10 0 10 10 20 10 10 0 10 10 20 10 z m 30 0 h 10 v 10"
        )

        self.assertEqual([segment["kind"] for segment in segments], ["cubic", "cubic", "line", "line", "line"])
        self.assertEqual([segment["subpath_index"] for segment in segments], [1, 1, 1, 2, 2])
        self.assertEqual(segments[0]["start"], (10.0, 10.0))
        self.assertEqual(segments[1]["end"], (50.0, 30.0))
        self.assertEqual(segments[2]["end"], (10.0, 10.0))
        self.assertEqual(segments[3]["start"], (40.0, 10.0))
        self.assertEqual(segments[4]["end"], (50.0, 20.0))

    def test_source_segmenter_preserves_disconnected_subpaths_without_connectors(self) -> None:
        candidate = {
            "parsed_svg": {
                "view_box": "0 0 100 100",
                "paths": [{
                    "path_id": "source_shape",
                    "d": "M 10 10 C 15 10 20 15 25 20 Z M 70 70 C 75 70 80 75 85 80 Z",
                }],
            }
        }

        chunks = worker._chunk_source_segments(candidate, max_commands_per_chunk=8)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["source_subpath_indices"], [1, 2])
        self.assertEqual(len(worker.re.findall(r"M", chunks[0]["d"])), 2)
        self.assertEqual(len(worker.re.findall(r"L", chunks[0]["d"])), 2)

    def test_source_segmenter_normalizes_and_covers_all_catalog_source_commands(self) -> None:
        paths = self._segmentable_catalog_paths()
        candidate = {"parsed_svg": {"view_box": "0 0 100 100", "paths": paths}}

        chunks, manifest = worker._segment_openclipart_candidate(candidate)

        source_segment_count = sum(
            len(worker._parse_source_svg_path_segments(path["d"])) for path in paths
        )
        self.assertTrue(8 <= len(chunks) <= 20)
        self.assertEqual(manifest["source_segment_count"], source_segment_count)
        self.assertEqual(len({chunk["path_id"] for chunk in chunks}), len(chunks))
        self.assertEqual({chunk["source_path_id"] for chunk in chunks}, {path["path_id"] for path in paths})
        self.assertEqual(len(manifest["first_step_segment_ids"]), 2)
        first_step = [
            next(chunk for chunk in chunks if chunk["path_id"] == path_id)
            for path_id in manifest["first_step_segment_ids"]
        ]
        self.assertEqual(first_step[0]["source_path_id"], first_step[1]["source_path_id"])
        self.assertEqual(first_step[0]["source_segment_end"] + 1, first_step[1]["source_segment_start"])
        self.assertEqual(first_step[0]["source_subpath_indices"], first_step[1]["source_subpath_indices"])
        self.assertTrue(all(len(worker.re.findall(r"[MLCQZ]", chunk["d"])) <= 8 for chunk in first_step))
        self.assertGreater(manifest["first_step_bbox_area"], 0)
        self.assertTrue(all(len(chunk["d"]) <= 680 for chunk in chunks))
        self.assertTrue(all(len(worker.re.findall(r"[MLCQZ]", chunk["d"])) <= 24 for chunk in chunks))
        for chunk in chunks:
            coordinates = [float(value) for value in worker.re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", chunk["d"])]
            self.assertTrue(all(16 <= coordinate <= 496 for coordinate in coordinates))

    def test_source_segmenter_rejects_unsupported_arc_commands(self) -> None:
        with self.assertRaisesRegex(
            worker._SvgSourceSegmentationError,
            "SVG_SOURCE_SEGMENT_COMMAND_UNSUPPORTED",
        ):
            worker._parse_source_svg_path_segments("M 10 10 A 5 5 0 0 1 20 20")

    def test_segment_guide_builder_uses_exact_segments_and_keeps_original_color_reference(self) -> None:
        source_paths = self._segmentable_catalog_paths()
        candidate = {
            "parsed_svg": {"view_box": "0 0 100 100", "paths": source_paths},
            "asset_id": "openclipart-friendly-kitten-icon",
            "source_sha256": "a" * 64,
        }
        segments, manifest = worker._segment_openclipart_candidate(candidate)
        plan_object = self._catalog_plan(segments)
        first_step_ids = manifest["first_step_segment_ids"]
        for path_id in first_step_ids:
            plan_object["path_stage_assignments"][path_id] = 1
        for path_id, stage_index in list(plan_object["path_stage_assignments"].items()):
            if stage_index == 1 and path_id not in first_step_ids:
                plan_object["path_stage_assignments"][path_id] = 2
        plan = worker._parse_svg_catalog_source_plan(
            json.dumps(plan_object, ensure_ascii=False),
            segments,
            first_step_segment_ids=first_step_ids,
        )
        plan["stages"][0]["label_vi"] = "Đường cong mở đầu"
        plan["stages"][0]["instruction_vi"] = "Vẽ hai đoạn cong liền nhau theo đường viền."

        with patch.object(worker, "_catalog_color", side_effect=lambda value: value):
            content, reference = worker._build_openclipart_segment_guide(candidate, segments, plan)

        self.assertEqual(len(content["strokes"]), len(segments))
        self.assertEqual([stroke["d"] for stroke in content["strokes"]], [segment["d"] for segment in segments])
        self.assertEqual([path["d"] for path in reference["paths"]], [path["d"] for path in source_paths])
        self.assertEqual([path["fill"] for path in reference["paths"]], [path["fill"] for path in source_paths])
        self.assertEqual([stage["step_index"] for stage in content["stages"]], [1, 2, 3, 4])
        self.assertEqual(sum(len(stage["stroke_ids"]) for stage in content["stages"]), len(segments))
        first_ids = set(manifest["first_step_segment_ids"])
        self.assertEqual(
            set(content["stages"][0]["stroke_ids"]),
            {
                f"guide_stroke_{segments.index(next(segment for segment in segments if segment['path_id'] == path_id)) + 1:02d}"
                for path_id in first_ids
            },
        )

    def test_model_segment_plan_uses_assignment_schema_not_primitive_stroke_schema(self) -> None:
        source_paths = self._segmentable_catalog_paths()
        candidate = {
            "parsed_svg": {"view_box": "0 0 100 100", "paths": source_paths},
            "asset_id": "openclipart-friendly-kitten-icon",
            "source_sha256": "a" * 64,
        }
        segments, manifest = worker._segment_openclipart_candidate(candidate)
        first_step_ids = manifest["first_step_segment_ids"]
        plan = self._catalog_plan(segments)
        for path_id in first_step_ids:
            plan["path_stage_assignments"][path_id] = 1
        for path_id, stage_index in list(plan["path_stage_assignments"].items()):
            if stage_index == 1 and path_id not in first_step_ids:
                plan["path_stage_assignments"][path_id] = 2
        model_output = json.dumps(plan, ensure_ascii=False)
        schema = worker._svg_catalog_source_plan_schema(
            segments,
            first_step_segment_ids=first_step_ids,
        )
        assignments_schema = schema["properties"]["path_stage_assignments"]["properties"]
        self.assertTrue(all(assignments_schema[path_id]["enum"] == [1] for path_id in first_step_ids))
        self.assertTrue(
            all(
                assignments_schema[path["path_id"]]["enum"] == list(range(2, 9))
                for path in segments
                if path["path_id"] not in first_step_ids
            )
        )
        prompt = worker._svg_catalog_segment_plan_prompt(
            {"topic": "con mèo", "difficulty": "beginner"},
            candidate,
            segments,
            first_step_segment_ids=first_step_ids,
        )
        self.assertIn(json.dumps(first_step_ids, ensure_ascii=False), prompt)
        self.assertIn("hai nét đầu chạy từ đỉnh tai trái", prompt)
        self.assertIn("tuyệt đối không gọi là cổ, vai hoặc thân", prompt)
        self.assertIn("Không áp đặt thứ tự chung kiểu thân trước", worker.SVG_CATALOG_SEGMENT_PLAN_SYSTEM_PROMPT)

        with patch.object(
            worker,
            "_normalize_svg_catalog_construction_output",
            side_effect=AssertionError("segment plan must not enter primitive parser"),
        ):
            content, reference = worker._build_openclipart_segment_guide_from_plan_text(
                model_output,
                candidate,
                segments,
                first_step_segment_ids=first_step_ids,
            )

        self.assertEqual(len(content["strokes"]), len(segments))
        self.assertEqual(len(content["stages"]), 4)
        self.assertEqual(
            [stroke["d"] for stroke in content["strokes"]],
            [segment["d"] for segment in segments],
        )
        self.assertEqual(
            [path["d"] for path in reference["paths"]],
            [path["d"] for path in source_paths],
        )
        self.assertEqual(len(content["stages"][0]["stroke_ids"]), 2)

        invalid_plan = json.loads(model_output)
        invalid_plan["path_stage_assignments"][first_step_ids[0]] = 2
        with self.assertRaises(worker._SvgCatalogPlanValidationError) as raised:
            worker._parse_svg_catalog_source_plan(
                json.dumps(invalid_plan, ensure_ascii=False),
                segments,
                first_step_segment_ids=first_step_ids,
            )
        self.assertEqual(
            raised.exception.error_code,
            "SVG_CATALOG_STROKE_PLAN_FIRST_STEP_ASSIGNMENT_INVALID",
        )

        invalid_stage = json.loads(model_output)
        invalid_stage["stages"][0]["step_index"] = 2
        with self.assertRaises(worker._SvgCatalogPlanValidationError) as stage_raised:
            worker._parse_svg_catalog_source_plan(
                json.dumps(invalid_stage, ensure_ascii=False),
                segments,
                first_step_segment_ids=first_step_ids,
            )
        self.assertEqual(
            stage_raised.exception.error_code,
            "SVG_CATALOG_STROKE_PLAN_STAGE_INVALID",
        )
        self.assertEqual(
            stage_raised.exception.safe_diagnostics["stage_failure"],
            "stage_fields_invalid",
        )

    def test_reviewed_kitten_starter_caption_uses_visible_head_contour(self) -> None:
        candidate = {"asset_id": "openclipart-friendly-kitten-icon"}
        qwen_stage = {
            "step_index": 1,
            "instruction_vi": "Vẽ phần cổ của mèo.",
        }
        self.assertEqual(
            worker._openclipart_segment_instruction(candidate, qwen_stage),
            "Vẽ hai nét cong trên đỉnh đầu, nối vùng giữa hai tai.",
        )
        later_stage = {**qwen_stage, "step_index": 2}
        self.assertEqual(
            worker._openclipart_segment_instruction(candidate, later_stage),
            qwen_stage["instruction_vi"],
        )

    def test_curated_kitten_sequence_is_source_hash_pinned_and_preserves_all_segments(self) -> None:
        source_hash = "a5b74eed392104ff9baa2a335b5e8dde9aef40ca7775949a7fbc4a29b7f36594"
        candidate = {
            "asset_id": "openclipart-friendly-kitten-icon",
            "source_sha256": source_hash,
        }
        segments = [
            {
                "path_id": f"source_segment_{index:03d}",
                "source_path_id": f"oc_path_{(index + 1) // 2:03d}",
                "d": f"M {index} 20 L {index + 1} 21",
            }
            for index in range(1, 21)
        ]
        pinned = ["source_segment_005", "source_segment_006"]

        plan = worker._curated_openclipart_source_plan(
            candidate, segments, first_step_segment_ids=pinned
        )

        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan["title_vi"], "Cùng vẽ mèo con")
        self.assertEqual(len(plan["stages"]), 6)
        self.assertEqual(plan["stages"][0]["path_ids"], pinned)
        self.assertEqual(
            [stage["instruction_vi"] for stage in plan["stages"]],
            [
                "Vẽ hai nét cong trên đỉnh đầu, nối vùng giữa hai tai.",
                "Nối hai đầu nét xuống hai má rồi khép viền khuôn mặt.",
                "Thêm hai tai nhọn, đôi mắt tròn và miệng nhỏ ở giữa.",
                "Thêm nét bên trong hai tai và hoàn thiện cả hai mắt cùng lúc nhé.",
                "Vẽ chiếc đuôi cong ở bên phải đầu mèo.",
                "Thêm hai bàn chân nhỏ bên dưới để hoàn thiện mèo con.",
            ],
        )
        self.assertEqual(
            [stage["path_ids"] for stage in plan["stages"]],
            [
                ["source_segment_005", "source_segment_006"],
                ["source_segment_001", "source_segment_002", "source_segment_003", "source_segment_004"],
                ["source_segment_007", "source_segment_008", "source_segment_009", "source_segment_018"],
                [
                    "source_segment_010",
                    "source_segment_011",
                    "source_segment_012",
                    "source_segment_013",
                    "source_segment_014",
                    "source_segment_015",
                ],
                ["source_segment_016", "source_segment_017"],
                ["source_segment_019", "source_segment_020"],
            ],
        )
        self.assertEqual(
            {segment_id for stage in plan["stages"] for segment_id in stage["path_ids"]},
            {segment["path_id"] for segment in segments},
        )
        self.assertTrue(all(segment["d"].startswith("M ") for segment in segments))

    def test_curated_kitten_adds_both_eye_details_in_the_same_stage(self) -> None:
        candidate = {
            "asset_id": "openclipart-friendly-kitten-icon",
            "source_sha256": "a5b74eed392104ff9baa2a335b5e8dde9aef40ca7775949a7fbc4a29b7f36594",
        }
        segments = [
            {"path_id": f"source_segment_{index:03d}", "d": f"M {index} 20 L {index + 1} 21"}
            for index in range(1, 21)
        ]

        plan = worker._curated_openclipart_source_plan(
            candidate,
            segments,
            first_step_segment_ids=["source_segment_005", "source_segment_006"],
        )

        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(len(plan["stages"]), 6)
        eye_detail_ids = {
            f"source_segment_{index:03d}" for index in range(10, 16)
        }
        self.assertEqual(
            [set(stage["path_ids"]) & eye_detail_ids for stage in plan["stages"]],
            [set(), set(), set(), eye_detail_ids, set(), set()],
        )
        self.assertIn("cả hai mắt cùng lúc", plan["stages"][3]["instruction_vi"])

    def test_curated_kitten_guide_preserves_each_source_segment_geometry(self) -> None:
        source_hash = "a5b74eed392104ff9baa2a335b5e8dde9aef40ca7775949a7fbc4a29b7f36594"
        segments = [
            {
                "path_id": f"source_segment_{index:03d}",
                "source_path_id": f"oc_path_{(index + 1) // 2:03d}",
                "d": f"M {index} 20 L {index + 1} 21",
            }
            for index in range(1, 21)
        ]
        source_ids = sorted({segment["source_path_id"] for segment in segments})
        candidate = {
            "asset_id": "openclipart-friendly-kitten-icon",
            "source_sha256": source_hash,
            "parsed_svg": {
                "view_box": "0 0 512 512",
                "paths": [
                    {
                        "path_id": source_id,
                        "d": f"M {index} 1 L {index} 2",
                        "fill": "#000000",
                        "stroke": "none",
                        "stroke_width": 1.0,
                        "stroke_linecap": "round",
                        "stroke_linejoin": "round",
                    }
                    for index, source_id in enumerate(source_ids, start=1)
                ],
            },
        }
        plan = worker._curated_openclipart_source_plan(
            candidate,
            segments,
            first_step_segment_ids=["source_segment_005", "source_segment_006"],
        )
        self.assertIsNotNone(plan)
        assert plan is not None

        guide, _ = worker._build_openclipart_segment_guide(candidate, segments, plan)

        self.assertEqual(
            [stroke["d"] for stroke in guide["strokes"]],
            [segment["d"] for segment in segments],
        )
        self.assertEqual(len(guide["stages"]), 6)
        self.assertEqual(
            [stage["stroke_ids"] for stage in guide["stages"]],
            [
                ["guide_stroke_05", "guide_stroke_06"],
                ["guide_stroke_01", "guide_stroke_02", "guide_stroke_03", "guide_stroke_04"],
                ["guide_stroke_07", "guide_stroke_08", "guide_stroke_09", "guide_stroke_18"],
                [
                    "guide_stroke_10",
                    "guide_stroke_11",
                    "guide_stroke_12",
                    "guide_stroke_13",
                    "guide_stroke_14",
                    "guide_stroke_15",
                ],
                ["guide_stroke_16", "guide_stroke_17"],
                ["guide_stroke_19", "guide_stroke_20"],
            ],
        )

    def test_curated_kitten_sequence_does_not_apply_to_other_source_revision_or_segment_set(self) -> None:
        candidate = {
            "asset_id": "openclipart-friendly-kitten-icon",
            "source_sha256": "0" * 64,
        }
        segments = [
            {"path_id": f"source_segment_{index:03d}", "d": f"M {index} 20 L {index + 1} 21"}
            for index in range(1, 21)
        ]
        pinned = ["source_segment_005", "source_segment_006"]
        self.assertIsNone(
            worker._curated_openclipart_source_plan(
                candidate, segments, first_step_segment_ids=pinned
            )
        )
        candidate["source_sha256"] = (
            "a5b74eed392104ff9baa2a335b5e8dde9aef40ca7775949a7fbc4a29b7f36594"
        )
        self.assertIsNone(
            worker._curated_openclipart_source_plan(
                candidate, segments[:-1], first_step_segment_ids=pinned
            )
        )

    def test_segment_atlas_preserves_whole_animal_context_and_highlights_exact_segment(self) -> None:
        import sys
        import xml.etree.ElementTree as ET
        from io import BytesIO
        from types import SimpleNamespace

        from PIL import Image

        segments = [
            {"path_id": "segment_head", "d": "M 40 40 L 80 40"},
            {"path_id": "segment_eye", "d": "M 60 60 L 70 60"},
        ]
        candidate = {
            "parsed_svg": {
                "view_box": "0 0 512 512",
                "paths": [{
                    "path_id": "source_outline",
                    "d": "M 20 20 L 90 90",
                    "fill": "none",
                    "stroke": "#17243e",
                    "stroke_width": 2,
                    "stroke_linecap": "round",
                    "stroke_linejoin": "round",
                }],
            }
        }
        rendered_roots: list[ET.Element] = []

        def fake_svg2png(
            *, bytestring: bytes, output_width: int, output_height: int,
            background_color: str,
        ) -> bytes:
            rendered_roots.append(ET.fromstring(bytestring))
            image = Image.new("RGB", (output_width, output_height), background_color)
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            return buffer.getvalue()

        with patch.dict(sys.modules, {"cairosvg": SimpleNamespace(svg2png=fake_svg2png)}):
            _, atlas = worker._render_openclipart_candidate(
                candidate,
                atlas_paths=segments,
                atlas_view_box="0 0 512 512",
            )

        self.assertEqual(atlas.size, (832, 224))
        # One render is the color source; each atlas tile contains every segment in context
        # and then draws its selected segment again in blue.
        self.assertEqual(len(rendered_roots), 3)
        for index, segment in enumerate(segments, start=1):
            paths = rendered_roots[index].findall("{http://www.w3.org/2000/svg}path")
            self.assertEqual([node.attrib["d"] for node in paths], [
                segments[0]["d"], segments[1]["d"], segment["d"]
            ])
            self.assertEqual([node.attrib["stroke"] for node in paths], [
                "#d3dbe7", "#d3dbe7", "#075dff"
            ])
        self.assertNotEqual(atlas.getpixel((10, 10)), (243, 246, 250))

    def test_cumulative_visual_review_renders_only_exact_source_segments(self) -> None:
        import sys
        import xml.etree.ElementTree as ET
        from io import BytesIO
        from types import SimpleNamespace

        from PIL import Image

        candidate = {"parsed_svg": {"view_box": "0 0 512 512"}}
        segments = [
            {
                "path_id": f"segment_{index:02d}",
                "source_path_id": "source_path",
                "d": f"M {20 + index * 5} 40 L {25 + index * 5} 45",
            }
            for index in range(8)
        ]
        draft = {
            "stages": [
                {"step_index": 1, "path_ids": ["segment_00", "segment_01"]},
                {"step_index": 2, "path_ids": ["segment_02", "segment_03"]},
                {"step_index": 3, "path_ids": ["segment_04", "segment_05"]},
                {"step_index": 4, "path_ids": ["segment_06", "segment_07"]},
            ]
        }
        rendered_segments: list[list[tuple[str, str]]] = []

        def fake_svg2png(
            *, bytestring: bytes, output_width: int, output_height: int,
            background_color: str,
        ) -> bytes:
            root = ET.fromstring(bytestring)
            rendered_segments.append([
                (node.attrib["d"], node.attrib["stroke"])
                for node in root
            ])
            image = Image.new("RGB", (output_width, output_height), background_color)
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            return buffer.getvalue()

        with patch.dict(sys.modules, {"cairosvg": SimpleNamespace(svg2png=fake_svg2png)}):
            sheet, manifest = worker._render_openclipart_cumulative_stage_review(
                candidate, segments, draft
            )

        self.assertEqual(sheet.mode, "RGB")
        self.assertEqual(sheet.size, (1_120, 330))
        self.assertEqual(len(manifest), 4)
        self.assertEqual(len(rendered_segments), 4)
        cumulative: list[str] = []
        for index, stage in enumerate(draft["stages"]):
            cumulative.extend(stage["path_ids"])
            self.assertEqual(manifest[index]["new_segment_ids"], stage["path_ids"])
            self.assertEqual(
                manifest[index]["new_segment_labels"],
                [f"P{int(path_id.rsplit('_', 1)[1]) + 1:02d}" for path_id in stage["path_ids"]],
            )
            self.assertEqual(manifest[index]["cumulative_segment_ids"], cumulative)
            expected = [
                (
                    segment["d"],
                    "#1769ff" if segment["path_id"] in stage["path_ids"] else "#aeb8c8",
                )
                for segment in segments
                if segment["path_id"] in cumulative
            ]
            self.assertEqual(rendered_segments[index], expected)

    def test_visual_review_schema_and_parser_lock_draft_scope_and_geometry_ids(self) -> None:
        segments = [
            {
                "path_id": f"segment_{index:02d}",
                "source_path_id": "source_path",
                "source_segment_start": index,
                "source_segment_end": index,
                "source_subpath_indices": [1],
                "d": f"M {20 + index} 20 L {30 + index} 30",
            }
            for index in range(8)
        ]
        pinned = ["segment_00", "segment_01"]
        draft_object = self._catalog_plan(segments)
        draft_object["title_vi"] = "Mèo con"
        draft_object["path_stage_assignments"]["segment_00"] = 1
        draft_object["path_stage_assignments"]["segment_01"] = 1
        for path_id, step in list(draft_object["path_stage_assignments"].items()):
            if step == 1 and path_id not in pinned:
                draft_object["path_stage_assignments"][path_id] = 2
        draft_plan = worker._parse_svg_catalog_source_plan(
            json.dumps(draft_object, ensure_ascii=False),
            segments,
            first_step_segment_ids=pinned,
        )
        schema = worker._svg_catalog_visual_review_schema(
            segments,
            first_step_segment_ids=pinned,
            title_vi=draft_plan["title_vi"],
            stage_count=len(draft_plan["stages"]),
        )

        self.assertEqual(schema["properties"]["title_vi"]["enum"], ["Mèo con"])
        self.assertEqual(schema["properties"]["stages"]["minItems"], 4)
        self.assertEqual(schema["properties"]["stages"]["maxItems"], 4)
        assignments = schema["properties"]["path_stage_assignments"]["properties"]
        self.assertEqual(assignments["segment_00"]["enum"], [1])
        self.assertEqual(assignments["segment_01"]["enum"], [1])
        self.assertEqual(assignments["segment_02"]["enum"], [2, 3, 4])

        reviewed_object = json.loads(json.dumps(draft_object))
        reviewed_object["stages"] = [
            {
                "label_vi": f"Bước {index}",
                "instruction_vi": f"Quan sát và vẽ nét mới ở bước {index}.",
            }
            for index in range(1, 5)
        ]
        reviewed = worker._parse_svg_catalog_visual_review_plan(
            json.dumps(reviewed_object, ensure_ascii=False),
            segments,
            first_step_segment_ids=pinned,
            draft_plan=draft_plan,
        )
        self.assertEqual(reviewed["title_vi"], draft_plan["title_vi"])
        self.assertEqual(len(reviewed["stages"]), len(draft_plan["stages"]))
        self.assertEqual(
            [stage["step_index"] for stage in reviewed["stages"]],
            [1, 2, 3, 4],
        )
        self.assertEqual(set(reviewed["stages"][0]["path_ids"]), set(pinned))

        reviewed_object["title_vi"] = "Tên đã bị đổi"
        with self.assertRaises(worker._SvgCatalogPlanValidationError) as raised:
            worker._parse_svg_catalog_visual_review_plan(
                json.dumps(reviewed_object, ensure_ascii=False),
                segments,
                first_step_segment_ids=pinned,
                draft_plan=draft_plan,
            )
        self.assertEqual(
            raised.exception.error_code,
            "SVG_CATALOG_VISUAL_REVIEW_SCOPE_INVALID",
        )

    def test_catalog_segment_schema_pinned_first_step_is_accepted_by_lmfe(self) -> None:
        try:
            from lmformatenforcer import JsonSchemaParser
        except ImportError:
            self.skipTest("LMFE is installed only in the pinned Modal worker image")

        source_paths = self._segmentable_catalog_paths()
        candidate = {"parsed_svg": {"view_box": "0 0 100 100", "paths": source_paths}}
        segments, manifest = worker._segment_openclipart_candidate(candidate)
        first_step_ids = manifest["first_step_segment_ids"]
        plan = self._catalog_plan(segments)
        for path_id in first_step_ids:
            plan["path_stage_assignments"][path_id] = 1
        for path_id, stage_index in list(plan["path_stage_assignments"].items()):
            if stage_index == 1 and path_id not in first_step_ids:
                plan["path_stage_assignments"][path_id] = 2
        encoded = json.dumps(plan, ensure_ascii=False)
        parser = JsonSchemaParser(
            worker._svg_catalog_source_plan_schema(
                segments,
                first_step_segment_ids=first_step_ids,
            )
        )
        for character in encoded:
            self.assertIn(character, parser.get_allowed_characters())
            parser = parser.add_character(character)
        self.assertTrue(parser.can_end())

    def test_construction_schema_anchors_new_strokes_to_existing_source_ids(self) -> None:
        paths = self._catalog_paths(12)
        schema = worker._svg_catalog_construction_schema(paths)
        stroke_ids = [
            f"guide_stroke_{index:02d}"
            for index in range(1, worker.SVG_TOPIC_GUIDE_GENERATION_STROKE_COUNT + 1)
        ]
        strokes_by_id = schema["properties"]["strokes_by_id"]
        stroke_fields = strokes_by_id["properties"][stroke_ids[0]]["properties"]
        anchor_schema = stroke_fields["source_path_ids"]

        self.assertEqual(
            schema["properties"]["schema_version"]["enum"],
            ["SvgTopicStrokeGuideConstructionContentV1"],
        )
        self.assertEqual(strokes_by_id["required"], stroke_ids)
        self.assertEqual(set(strokes_by_id["properties"]), set(stroke_ids))
        self.assertEqual(
            anchor_schema["items"]["enum"],
            [path["path_id"] for path in paths],
        )
        self.assertEqual(
            stroke_fields["role"]["enum"],
            ["construction", "outline", "feature"],
        )
        self.assertEqual(
            stroke_fields["geometry"]["properties"]["primitive"]["enum"],
            ["ellipse", "cubic", "polyline"],
        )
        self.assertEqual(
            stroke_fields["geometry"]["properties"]["points"]["required"],
            ["p0", "p1", "p2", "p3"],
        )
        coordinate_schema = (
            stroke_fields["geometry"]["properties"]["points"]["properties"]["p0"]
            ["properties"]["x"]
        )
        self.assertEqual(coordinate_schema["type"], "integer")
        self.assertEqual(coordinate_schema["minimum"], 16)
        self.assertEqual(coordinate_schema["maximum"], 496)
        self.assertNotIn("d", stroke_fields)
        self.assertNotIn("strokes", schema["properties"])
        self.assertFalse(schema["additionalProperties"])

    def test_construction_schema_is_accepted_by_pinned_lmfe_parser(self) -> None:
        try:
            from lmformatenforcer import JsonSchemaParser
        except ImportError:
            self.skipTest("LMFE is installed only in the pinned Modal worker image")

        paths = self._catalog_paths(12)
        schema = worker._svg_catalog_construction_schema(paths)
        encoded = json.dumps(self._construction_generation_output(paths), ensure_ascii=False)
        worker.os.environ["LMFE_DEFAULT_ALPHABET"] = worker.LMFE_VIETNAMESE_JSON_ALPHABET
        parser = JsonSchemaParser(schema)
        for character in encoded:
            self.assertIn(character, parser.get_allowed_characters())
            parser = parser.add_character(character)
        self.assertTrue(parser.can_end())

    @classmethod
    def _construction_generation_output(cls, paths: list[dict[str, Any]]) -> dict[str, Any]:
        guide = cls._construction_guide(paths)
        return {
            "schema_version": guide["schema_version"],
            "title_vi": guide["title_vi"],
            "strokes_by_id": {
                f"guide_stroke_{index:02d}": {
                    "geometry": cls._generation_geometry(index),
                    "role": (
                        "construction"
                        if index <= 2
                        else "outline"
                        if index <= 6
                        else "feature"
                    ),
                    "feature_vi": f"nét số {index}",
                    "source_path_ids": [paths[(index - 1) % len(paths)]["path_id"]],
                }
                for index in range(1, worker.SVG_TOPIC_GUIDE_GENERATION_STROKE_COUNT + 1)
            },
            "stages": guide["stages"],
        }

    @staticmethod
    def _generation_geometry(index: int) -> dict[str, Any]:
        if index == 1:
            center_x = 190
            center_y = 150
            return {
                "primitive": "ellipse",
                "points": {
                    "p0": {"x": center_x, "y": center_y - 30},
                    "p1": {"x": center_x + 25, "y": center_y},
                    "p2": {"x": center_x, "y": center_y + 30},
                    "p3": {"x": center_x - 25, "y": center_y},
                },
            }
        if index == 2:
            return {
                "primitive": "cubic",
                "points": {
                    "p0": {"x": 70, "y": 120},
                    "p1": {"x": 110, "y": 80},
                    "p2": {"x": 160, "y": 80},
                    "p3": {"x": 200, "y": 120},
                },
            }
        return {
            "primitive": "polyline",
            "points": {
                f"p{point_index}": {
                    "x": 40 + index * 20 + point_index * 8,
                    "y": 80 + index * 11 + point_index * 7,
                }
                for point_index in range(4)
            },
        }

    def test_construction_primitive_renderer_emits_canonical_paths(self) -> None:
        cases = [
            (
                "cubic",
                {
                    "p0": {"x": 40, "y": 80},
                    "p1": {"x": 60, "y": 40},
                    "p2": {"x": 100, "y": 40},
                    "p3": {"x": 120, "y": 80},
                },
                "M 40 80 C 60 40 100 40 120 80",
                2,
            ),
            (
                "polyline",
                {
                    "p0": {"x": 40, "y": 80},
                    "p1": {"x": 60, "y": 40},
                    "p2": {"x": 100, "y": 40},
                    "p3": {"x": 120, "y": 80},
                },
                "M 40 80 L 60 40 L 100 40 L 120 80",
                4,
            ),
            (
                "ellipse",
                {
                    "p0": {"x": 256, "y": 120},
                    "p1": {"x": 336, "y": 256},
                    "p2": {"x": 256, "y": 392},
                    "p3": {"x": 176, "y": 256},
                },
                "M 256 120",
                6,
            ),
        ]

        for primitive, points, expected_prefix, expected_commands in cases:
            with self.subTest(primitive=primitive):
                geometry = {"primitive": primitive, "points": points}
                first = worker._render_svg_construction_primitive(
                    geometry, stroke_index=1
                )
                second = worker._render_svg_construction_primitive(
                    geometry, stroke_index=1
                )

                self.assertEqual(first, second)
                self.assertEqual(first[1], primitive)
                self.assertEqual(first[2], expected_commands)
                self.assertTrue(first[0].startswith(expected_prefix))
                self.assertLessEqual(len(first[0]), 256)
                self.assertNotIn("<", first[0])

    def test_construction_primitive_renderer_rejects_invalid_and_degenerate_geometry(self) -> None:
        valid_points = {
            "p0": {"x": 40, "y": 80},
            "p1": {"x": 60, "y": 40},
            "p2": {"x": 100, "y": 40},
            "p3": {"x": 120, "y": 80},
        }
        invalid_coordinate = json.loads(json.dumps(valid_points))
        invalid_coordinate["p1"]["x"] = True
        out_of_bounds_coordinate = json.loads(json.dumps(valid_points))
        out_of_bounds_coordinate["p1"]["x"] = 497
        duplicate_polyline_points = {
            "p0": {"x": 40, "y": 80},
            "p1": {"x": 40, "y": 80},
            "p2": {"x": 100, "y": 40},
            "p3": {"x": 100, "y": 40},
        }
        too_small_ellipse = {
            "p0": {"x": 256, "y": 250},
            "p1": {"x": 262, "y": 256},
            "p2": {"x": 256, "y": 262},
            "p3": {"x": 250, "y": 256},
        }
        cases = [
            (
                {"primitive": "cubic", "points": invalid_coordinate},
                "SVG_CONSTRUCTION_GUIDE_PRIMITIVE_COORDINATE_INVALID",
            ),
            (
                {"primitive": "cubic", "points": out_of_bounds_coordinate},
                "SVG_CONSTRUCTION_GUIDE_PRIMITIVE_COORDINATE_INVALID",
            ),
            (
                {"primitive": "polyline", "points": duplicate_polyline_points},
                "SVG_CONSTRUCTION_GUIDE_PRIMITIVE_DEGENERATE",
            ),
            (
                {"primitive": "ellipse", "points": too_small_ellipse},
                "SVG_CONSTRUCTION_GUIDE_PRIMITIVE_DEGENERATE",
            ),
        ]

        for geometry, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(worker._SvgCatalogPlanValidationError) as raised:
                    worker._render_svg_construction_primitive(
                        geometry, stroke_index=3
                    )
                self.assertEqual(raised.exception.error_code, expected_code)
                self.assertEqual(raised.exception.safe_diagnostics["stroke_index"], 3)

    def test_fixed_key_generation_normalizes_to_existing_guide_contract(self) -> None:
        source_paths = self._catalog_paths(12)
        encoded = json.dumps(
            self._construction_generation_output(source_paths), ensure_ascii=False
        )

        normalized = json.loads(worker._normalize_svg_catalog_construction_output(encoded))
        parsed = worker._parse_svg_catalog_construction_guide(
            json.dumps(normalized, ensure_ascii=False), source_paths
        )

        self.assertEqual(len(parsed["strokes"]), worker.SVG_TOPIC_GUIDE_GENERATION_STROKE_COUNT)
        self.assertEqual(len(parsed["stages"]), 4)
        self.assertTrue(all("d" in stroke for stroke in parsed["strokes"]))
        self.assertTrue(all("geometry" not in stroke for stroke in parsed["strokes"]))
        self.assertEqual(
            len({stroke["d"] for stroke in parsed["strokes"]}),
            worker.SVG_TOPIC_GUIDE_GENERATION_STROKE_COUNT,
        )
        self.assertEqual(
            {stroke["path_id"] for stroke in parsed["strokes"]},
            {
                f"guide_stroke_{index:02d}"
                for index in range(1, worker.SVG_TOPIC_GUIDE_GENERATION_STROKE_COUNT + 1)
            },
        )

    def test_fixed_key_generation_rejects_missing_required_stroke(self) -> None:
        paths = self._catalog_paths(12)
        generated = self._construction_generation_output(paths)
        generated["strokes_by_id"].pop(
            f"guide_stroke_{worker.SVG_TOPIC_GUIDE_GENERATION_STROKE_COUNT:02d}"
        )
        encoded = json.dumps(generated, ensure_ascii=False)

        with self.assertRaises(worker._SvgCatalogPlanValidationError) as raised:
            worker._normalize_svg_catalog_construction_output(encoded)

        self.assertEqual(
            raised.exception.error_code,
            "SVG_CONSTRUCTION_GUIDE_GENERATION_STROKE_SET_INVALID",
        )
        self.assertEqual(raised.exception.safe_diagnostics["missing_stroke_count"], 1)

    def test_generation_rejects_model_authored_svg_path_even_with_primitive(self) -> None:
        generated = self._construction_generation_output(self._catalog_paths(12))
        generated["strokes_by_id"]["guide_stroke_01"]["d"] = "M 20 20 L 40 40"

        with self.assertRaises(worker._SvgCatalogPlanValidationError) as raised:
            worker._normalize_svg_catalog_construction_output(
                json.dumps(generated, ensure_ascii=False)
            )

        self.assertEqual(
            raised.exception.error_code,
            "SVG_CONSTRUCTION_GUIDE_GENERATION_STROKE_INVALID",
        )

    @staticmethod
    def _construction_guide(paths: list[dict[str, Any]]) -> dict[str, Any]:
        strokes = [
            {
                "path_id": f"guide_stroke_{index:02d}",
                "d": f"M {40 + index * 5} 80 L {60 + index * 5} 100",
                "role": "construction" if index <= 2 else "outline" if index <= 6 else "feature",
                "feature_vi": f"nét số {index}",
                "source_path_ids": [paths[(index - 1) % len(paths)]["path_id"]],
            }
            for index in range(1, 9)
        ]
        return {
            "schema_version": "SvgTopicStrokeGuideConstructionContentV1",
            "title_vi": "Con mèo",
            "strokes": strokes,
            "stages": [
                {
                    "step_index": 1,
                    "label_vi": "Khối đầu và thân",
                    "instruction_vi": "Vẽ hai hình bầu dục lớn.",
                    "stroke_ids": ["guide_stroke_01", "guide_stroke_02"],
                },
                {
                    "step_index": 2,
                    "label_vi": "Nối các phần",
                    "instruction_vi": "Nối đầu với thân bằng nét cong.",
                    "stroke_ids": ["guide_stroke_03", "guide_stroke_04"],
                },
                {
                    "step_index": 3,
                    "label_vi": "Thêm chân và đuôi",
                    "instruction_vi": "Thêm chân ở dưới và đuôi phía sau.",
                    "stroke_ids": ["guide_stroke_05", "guide_stroke_06"],
                },
                {
                    "step_index": 4,
                    "label_vi": "Thêm nét nhận dạng",
                    "instruction_vi": "Vẽ mắt và vài nét ria mép.",
                    "stroke_ids": ["guide_stroke_07", "guide_stroke_08"],
                },
            ],
        }

    def test_construction_guide_uses_its_own_geometry_and_can_omit_source_paths(self) -> None:
        source_paths = self._catalog_paths(12)
        raw = json.dumps(self._construction_guide(source_paths), ensure_ascii=False)

        parsed = worker._parse_svg_catalog_construction_guide(raw, source_paths)

        self.assertEqual(parsed["schema_version"], "SvgTopicStrokeGuideConstructionContentV1")
        self.assertEqual(len(parsed["strokes"]), 8)
        self.assertEqual(len(parsed["stages"]), 4)
        self.assertNotEqual(
            [stroke["d"] for stroke in parsed["strokes"]],
            [path["d"] for path in source_paths[:8]],
        )
        self.assertEqual(
            {anchor for stroke in parsed["strokes"] for anchor in stroke["source_path_ids"]},
            {path["path_id"] for path in source_paths[:8]},
        )

    def test_construction_prompt_links_feature_role_to_final_stage_path(self) -> None:
        paths = self._catalog_paths(11)
        prompt = worker._svg_catalog_construction_prompt(
            {"topic": "con mèo", "difficulty": "beginner"},
            {
                "parsed_svg": {"paths": paths},
                "title": "Kitten",
                "description": "A simple cat illustration.",
                "tags": "cat kitten",
            },
        )

        self.assertIn("role đúng bằng 'feature'", prompt)
        self.assertIn("stroke_ids của stage cuối cùng", prompt)
        self.assertIn("instruction_vi của stage cuối", prompt)
        self.assertIn("strokes_by_id", prompt)
        self.assertIn("chính xác 8 nét", prompt)
        self.assertIn("feature_vi phải gọi tên một bộ phận", prompt)
        self.assertIn("không dùng lại cùng một primitive/điểm", prompt)
        self.assertIn("tuyệt đối KHÔNG viết chuỗi SVG d/path", prompt)
        self.assertIn("step_index của stage đầu là 1", prompt)
        self.assertIn("phải xuất hiện trong đúng một stage", prompt)
        self.assertNotIn("M/L/C/Q/Z viết hoa", prompt)

    def test_construction_guide_reports_stage_index_failure_without_model_text(self) -> None:
        source_paths = self._catalog_paths(12)
        guide = self._construction_guide(source_paths)
        guide["stages"][0]["step_index"] = 2

        with self.assertRaises(worker._SvgCatalogPlanValidationError) as raised:
            worker._parse_svg_catalog_construction_guide(
                json.dumps(guide, ensure_ascii=False), source_paths
            )

        self.assertEqual(
            raised.exception.error_code,
            "SVG_CONSTRUCTION_GUIDE_STAGE_INVALID",
        )
        self.assertEqual(raised.exception.safe_diagnostics["stage_array_index"], 1)
        self.assertEqual(raised.exception.safe_diagnostics["stage_failure"], "step_index")
        self.assertNotIn("instruction_vi", raised.exception.safe_diagnostics)

    def test_construction_guide_reports_feature_stage_mismatch_safely(self) -> None:
        source_paths = self._catalog_paths(12)
        guide = self._construction_guide(source_paths)
        guide["stages"][2]["stroke_ids"] = [
            "guide_stroke_05",
            "guide_stroke_07",
            "guide_stroke_08",
        ]
        guide["stages"][3]["stroke_ids"] = ["guide_stroke_06"]

        with self.assertRaises(worker._SvgCatalogPlanValidationError) as raised:
            worker._parse_svg_catalog_construction_guide(
                json.dumps(guide, ensure_ascii=False), source_paths
            )

        self.assertEqual(
            raised.exception.error_code,
            "SVG_CONSTRUCTION_GUIDE_FINAL_FEATURE_MISSING",
        )
        self.assertEqual(raised.exception.safe_diagnostics["feature_stroke_count"], 2)
        self.assertEqual(
            raised.exception.safe_diagnostics["final_stage_feature_stroke_count"],
            0,
        )
        self.assertEqual(
            raised.exception.safe_diagnostics["last_feature_stage_index"], 3
        )

    def test_construction_guide_accepts_contract_maximum_geometry_budget(self) -> None:
        source_paths = self._catalog_paths(12)
        guide = self._construction_guide(source_paths)
        guide["strokes"] = []
        for index in range(1, worker.SVG_TOPIC_GUIDE_MAX_CONSTRUCTION_STROKES + 1):
            path_data = (
                f"M {40 + index} 80 L {60 + index} 100"
                if index <= 3
                else (
                    f"M {30 + index}.1234567890 {40 + index}.1234567890 "
                    + " ".join(
                        f"L {31 + index}.{point:011d} {41 + index}.{point + 1:011d}"
                        for point in range(23)
                    )
                )
            )
            guide["strokes"].append(
                {
                    "path_id": f"guide_stroke_{index:02d}",
                    "d": path_data,
                    "role": (
                        "construction"
                        if index <= 3
                        else "feature"
                        if index == worker.SVG_TOPIC_GUIDE_MAX_CONSTRUCTION_STROKES
                        else "outline"
                    ),
                    "feature_vi": f"nét số {index}",
                    "source_path_ids": [source_paths[(index - 1) % len(source_paths)]["path_id"]],
                }
            )
        guide["stages"] = [
            {
                "step_index": 1,
                "label_vi": "Khung lớn",
                "instruction_vi": "Vẽ hình lớn cho đầu và thân.",
                "stroke_ids": ["guide_stroke_01", "guide_stroke_02", "guide_stroke_03"],
            },
            {
                "step_index": 2,
                "label_vi": "Nối hình",
                "instruction_vi": "Nối các hình lớn lại với nhau.",
                "stroke_ids": [f"guide_stroke_{index:02d}" for index in range(4, 9)],
            },
            {
                "step_index": 3,
                "label_vi": "Thêm bộ phận",
                "instruction_vi": "Vẽ thêm chân và đuôi.",
                "stroke_ids": [f"guide_stroke_{index:02d}" for index in range(9, 15)],
            },
            {
                "step_index": 4,
                "label_vi": "Nhận ra con mèo",
                "instruction_vi": "Thêm tai và mắt cho mèo.",
                "stroke_ids": [f"guide_stroke_{index:02d}" for index in range(15, 21)],
            },
        ]
        total_path_chars = sum(len(stroke["d"]) for stroke in guide["strokes"])
        self.assertGreater(total_path_chars, 12_288)
        self.assertLessEqual(
            max(len(stroke["d"]) for stroke in guide["strokes"]),
            worker.SVG_TOPIC_GUIDE_MAX_STROKE_CHARS,
        )

        parsed = worker._parse_svg_catalog_construction_guide(
            json.dumps(guide, ensure_ascii=False), source_paths
        )

        self.assertEqual(len(parsed["strokes"]), 20)

    def test_construction_guide_diagnoses_duplicate_stroke_geometry(self) -> None:
        source_paths = self._catalog_paths(12)
        guide = self._construction_guide(source_paths)
        guide["strokes"][1]["d"] = guide["strokes"][0]["d"]

        with self.assertRaises(worker._SvgCatalogPlanValidationError) as raised:
            worker._parse_svg_catalog_construction_guide(
                json.dumps(guide, ensure_ascii=False), source_paths
            )

        self.assertEqual(
            raised.exception.safe_diagnostics["geometry_failure"],
            "DUPLICATE_STROKE_GEOMETRY",
        )
        self.assertEqual(raised.exception.safe_diagnostics["stroke_count"], 2)
        self.assertEqual(raised.exception.safe_diagnostics["stage_count"], 4)
        self.assertEqual(raised.exception.safe_diagnostics["unique_geometry_count"], 1)
        self.assertEqual(raised.exception.safe_diagnostics["duplicate_geometry_count"], 1)
        self.assertEqual(raised.exception.safe_diagnostics["first_duplicate_stroke_index"], 2)

    def test_construction_guide_rejects_repeated_feature_description(self) -> None:
        source_paths = self._catalog_paths(12)
        guide = self._construction_guide(source_paths)
        guide["strokes"][1]["feature_vi"] = guide["strokes"][0]["feature_vi"]

        with self.assertRaises(worker._SvgCatalogPlanValidationError) as raised:
            worker._parse_svg_catalog_construction_guide(
                json.dumps(guide, ensure_ascii=False), source_paths
            )

        self.assertEqual(
            raised.exception.error_code,
            "SVG_CONSTRUCTION_GUIDE_FEATURE_LABEL_DUPLICATE",
        )
        self.assertEqual(
            raised.exception.safe_diagnostics["duplicate_feature_label_count"], 1
        )

    def test_construction_guide_rejects_a_finished_outline_in_step_one(self) -> None:
        source_paths = self._catalog_paths(8)
        guide = self._construction_guide(source_paths)
        guide["strokes"][0]["role"] = "outline"

        with self.assertRaisesRegex(
            worker._SvgCatalogPlanValidationError,
            "SVG_CONSTRUCTION_GUIDE_FIRST_STEP_NOT_CONSTRUCTION",
        ):
            worker._parse_svg_catalog_construction_guide(
                json.dumps(guide, ensure_ascii=False), source_paths
            )

    def test_construction_guide_rejects_unknown_source_anchor(self) -> None:
        source_paths = self._catalog_paths(8)
        guide = self._construction_guide(source_paths)
        guide["strokes"][0]["source_path_ids"] = ["not-a-source-path"]

        with self.assertRaisesRegex(
            worker._SvgCatalogPlanValidationError,
            "SVG_CONSTRUCTION_GUIDE_SOURCE_ANCHOR_INVALID",
        ):
            worker._parse_svg_catalog_construction_guide(
                json.dumps(guide, ensure_ascii=False), source_paths
            )

    def test_catalog_plan_reports_missing_path_as_safe_counts(self) -> None:
        paths = self._catalog_paths()
        plan = self._catalog_plan(paths)
        plan["path_stage_assignments"].pop(paths[-1]["path_id"])

        with self.assertRaisesRegex(
            worker._SvgCatalogPlanValidationError,
            "SVG_CATALOG_STROKE_PLAN_PATH_ASSIGNMENT_INVALID",
        ) as raised:
            worker._parse_svg_catalog_source_plan(
                json.dumps(plan, ensure_ascii=False), paths
            )

        self.assertEqual(raised.exception.safe_diagnostics["expected_path_count"], 8)
        self.assertEqual(raised.exception.safe_diagnostics["assigned_path_count"], 7)
        self.assertEqual(raised.exception.safe_diagnostics["missing_path_count"], 1)
        self.assertEqual(raised.exception.safe_diagnostics["unknown_path_count"], 0)
        self.assertNotIn(paths[-1]["path_id"], repr(raised.exception.safe_diagnostics))

    def test_catalog_plan_rejects_unknown_path_keys(self) -> None:
        paths = self._catalog_paths()
        plan = self._catalog_plan(paths)
        plan["path_stage_assignments"]["invented_path"] = 1

        with self.assertRaisesRegex(
            worker._SvgCatalogPlanValidationError,
            "SVG_CATALOG_STROKE_PLAN_PATH_ASSIGNMENT_INVALID",
        ) as raised:
            worker._parse_svg_catalog_source_plan(
                json.dumps(plan, ensure_ascii=False), paths
            )

        self.assertEqual(raised.exception.safe_diagnostics["unknown_path_count"], 1)
        self.assertEqual(raised.exception.safe_diagnostics["missing_path_count"], 0)

    def test_catalog_plan_rejects_duplicate_json_object_keys_without_echoing_key(self) -> None:
        paths = self._catalog_paths()
        plan = self._catalog_plan(paths)
        assignments = plan.pop("path_stage_assignments")
        prefix = json.dumps(plan, ensure_ascii=False)[:-1]
        assignment_pairs = [
            json.dumps(path_id) + ":" + json.dumps(stage_index)
            for path_id, stage_index in assignments.items()
        ]
        assignment_pairs.insert(1, assignment_pairs[0])
        raw = (
            prefix
            + ',"path_stage_assignments":{'
            + ",".join(assignment_pairs)
            + "}}"
        )

        with self.assertRaisesRegex(
            worker._SvgCatalogPlanValidationError,
            "SVG_CATALOG_STROKE_PLAN_DUPLICATE_JSON_KEY",
        ) as raised:
            worker._parse_svg_catalog_source_plan(raw, paths)

        self.assertEqual(raised.exception.safe_diagnostics["duplicate_object_key_count"], 1)
        self.assertNotIn(paths[0]["path_id"], repr(raised.exception.safe_diagnostics))
        self.assertNotIn(raw, repr(raised.exception.safe_diagnostics))

    def test_catalog_plan_rejects_out_of_range_and_empty_stages(self) -> None:
        paths = self._catalog_paths()
        out_of_range = self._catalog_plan(paths)
        first_path = paths[0]["path_id"]
        out_of_range["path_stage_assignments"][first_path] = 8
        with self.assertRaisesRegex(
            worker._SvgCatalogPlanValidationError,
            "SVG_CATALOG_STROKE_PLAN_PATH_ASSIGNMENT_INVALID",
        ) as raised:
            worker._parse_svg_catalog_source_plan(
                json.dumps(out_of_range), paths
            )
        self.assertEqual(raised.exception.safe_diagnostics["out_of_range_stage_count"], 1)

        empty_stage = self._catalog_plan(paths)
        empty_stage["path_stage_assignments"] = {
            path["path_id"]: min(index // 3 + 1, 4)
            for index, path in enumerate(paths)
        }
        with self.assertRaisesRegex(
            worker._SvgCatalogPlanValidationError,
            "SVG_CATALOG_STROKE_PLAN_EMPTY_STAGE",
        ) as raised:
            worker._parse_svg_catalog_source_plan(
                json.dumps(empty_stage), paths
            )
        self.assertEqual(raised.exception.safe_diagnostics["empty_stage_count"], 1)

    def test_catalog_renderer_preserves_exact_source_path_ids_and_geometry(self) -> None:
        paths = self._catalog_paths()
        plan = worker._parse_svg_catalog_source_plan(
            json.dumps(self._catalog_plan(paths)), paths
        )
        candidate = {"parsed_svg": {"view_box": "0 0 512 512", "paths": paths}}

        with patch.object(worker, "_catalog_color", side_effect=lambda value: value):
            content, _ = worker._build_openclipart_source_guide(candidate, plan)

        self.assertEqual(
            [path["path_id"] for path in content["document"]["paths"]],
            [path["path_id"] for path in paths],
        )
        self.assertEqual(
            [path["d"] for path in content["document"]["paths"]],
            [path["d"] for path in paths],
        )
        assigned = [
            path_id for stage in content["stages"] for path_id in stage["new_path_ids"]
        ]
        self.assertCountEqual(assigned, [path["path_id"] for path in paths])
        self.assertEqual(len(assigned), len(set(assigned)))


if __name__ == "__main__":
    unittest.main()
