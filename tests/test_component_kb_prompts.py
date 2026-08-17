from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import ai.book_component_kb.prompts as prompts_module
from ai.contracts import validate_data
from ai.book_component_kb.prompts import (
    EXPECTED_BLOCK_ORDER,
    compile_component_prompt,
    validate_selection,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def valid_project() -> dict:
    return {
        "version": "1.0",
        "project_id": "P-COVER-001",
        "title": "四时来信",
        "mode": "memorial",
        "primary_category": "letters-diaries",
        "tags": ["书信", "四季"],
        "confirmer": "项目维护人",
        "purpose": "制作一本克制而温暖的人生纪念书",
        "primary_readers": "家人与朋友",
        "page_size": "140mm x 210mm",
        "brand_profile": "paper-boat",
        "page_plan": {"min_pages": 96, "max_pages": 160},
    }


def valid_genome() -> dict:
    return {
        "version": "1.0",
        "project_id": "P-COVER-001",
        "direction_id": "DIRECTION-A",
        "reference_ids": ["COV-CN-0001", "COV-CN-0002"],
        "brand_profile": "paper-boat",
        "color": {"paper": "warm white", "ink": "muted ink blue"},
        "fonts": {"display": "editable later", "body": "industry default"},
        "grid": {"columns": 6, "character": "open and quiet"},
        "toc": {"scope": "multi-page", "text_layer": "editable"},
        "chapter_opener": {"image_optional": True, "text_layer": "editable"},
        "running_headers": {"template_id": "paired-standard"},
        "page_families": [
            "cover-interface",
            "toc",
            "chapter-opener",
            "body",
            "image-page",
            "running-headers",
        ],
    }


def valid_retrieval() -> dict:
    scores = {
        "visual_strategy": 0.2,
        "composition": 0.2,
        "title_zone": 0.15,
        "color": 0.15,
        "material": 0.1,
        "mood": 0.1,
        "cover_scope": 0.05,
        "book_category": 0.05,
    }
    return {
        "schema_version": "1.0",
        "query_id": "QUERY-COV-0001",
        "component_type": "cover",
        "status": "available",
        "candidates": [
            {
                "record_id": f"COV-CN-{index:04d}",
                "book_case_id": f"BOOK-CN-{index:04d}",
                "field_scores": scores,
                "total_score": 1.0,
                "match_explanation": "受控测试候选",
            }
            for index in range(1, 6)
        ],
    }


def valid_selection() -> dict:
    return {
        "schema_version": "1.0",
        "selection_id": "SEL-COV-0001",
        "query_id": "QUERY-COV-0001",
        "component_type": "cover",
        "selected_references": [
            {
                "record_id": "COV-CN-0001",
                "include_fields": ["composition", "title_zone"],
                "existing_baseline": "上方留白和偏轴构图",
                "adjustment_instruction": "将具体物件替换为项目自身的季节意象",
                "preserve_elements": ["上方安全区", "克制的视觉重心"],
                "required_changes": ["不复制原图形", "改用项目自身内容"],
                "exclude_fields": ["原书名", "原作者名"],
            },
            {
                "record_id": "COV-CN-0002",
                "include_fields": ["color", "material"],
                "existing_baseline": "米白与墨蓝的低饱和关系",
                "adjustment_instruction": "按设计基因调整色彩面积与纸张触感",
                "preserve_elements": ["低饱和关系", "纸张温度"],
                "required_changes": ["替换具体纹样", "降低装饰密度"],
                "exclude_fields": ["原出版社标识", "原系列标识"],
            },
        ],
        "status": "approved",
    }


def valid_chapter_opener_retrieval() -> dict:
    scores = {
        "opening_mode": 0.15,
        "visual_strategy": 0.15,
        "chapter_number_zone": 0.15,
        "chapter_title_zone": 0.20,
        "image_role": 0.15,
        "text_image_relationship": 0.10,
        "whitespace": 0.10,
    }
    return {
        "schema_version": "1.0",
        "query_id": "QUERY-CHAPTER-0001",
        "component_type": "chapter-opener",
        "status": "available",
        "candidates": [
            {
                "record_id": f"CHO-CN-{index:04d}",
                "book_case_id": f"BOOK-CN-{index:04d}",
                "field_scores": scores,
                "total_score": 1.0,
                "match_explanation": "受控章首页测试候选",
            }
            for index in range(1, 6)
        ],
    }


def valid_chapter_opener_selection() -> dict:
    return {
        "schema_version": "1.0",
        "selection_id": "SEL-CHAPTER-0001",
        "query_id": "QUERY-CHAPTER-0001",
        "component_type": "chapter-opener",
        "selected_references": [
            {
                "record_id": "CHO-CN-0001",
                "include_fields": [
                    "visual_strategy",
                    "text_image_relationship",
                    "whitespace",
                ],
                "existing_baseline": "本项目使用统一章首页母版",
                "adjustment_instruction": "按本项目自身内容重组抽象边界",
                "preserve_elements": ["可编辑文字层", "高留白"],
                "required_changes": ["重设具体轮廓", "改变元素比例"],
                "exclude_fields": ["原书文字", "原书具体图形"],
            },
            {
                "record_id": "CHO-CN-0002",
                "include_fields": [
                    "chapter_title_zone",
                    "text_image_relationship",
                    "whitespace",
                ],
                "existing_baseline": "本项目保留可编辑章题",
                "adjustment_instruction": "按项目自身章题长度重排纵向区域",
                "preserve_elements": ["单侧聚焦", "章题可编辑"],
                "required_changes": ["重设断行", "调整纵向尺度"],
                "exclude_fields": ["原书断行", "原书纸张效果"],
            },
        ],
        "status": "approved",
    }


def valid_output_spec() -> dict:
    return {
        "prompt_id": "PROMPT-COV-0001",
        "aspect_ratio": "2:3",
        "component_role": "front cover background",
        "composition": "portrait cover, quiet upper-third safe zone, restrained focal point",
        "image_content": "abstract seasonal correspondence carried by paper and water motifs",
        "color_light_material": "warm paper white, muted ink blue, soft side light, uncoated-paper tactility",
        "editable_text_safe_zones": "reserve title and author areas plus a clear publisher-mark corner",
        "print_and_crop": "include 3mm bleed; keep essential image content inside the trim safe area",
        "negative_constraints": [
            "no readable text",
            "no title glyphs",
            "no author glyphs",
            "no logo",
            "no watermark",
            "no one-to-one case copy",
        ],
        "editable_text_overlay": ["title", "author", "publisher_mark", "spine_text"],
        "editable_text_values": {
            "title": "四时来信",
            "author": "待确认（可编辑文字层）",
            "publisher_mark": "待确认（可编辑文字层）",
            "spine_text": "待确认（可编辑文字层）",
        },
    }


class SelectionValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.retrieval = valid_retrieval()

    def test_selection_requires_two_or_three_retrieved_records(self) -> None:
        selection = valid_selection()
        selection["selected_references"] = selection["selected_references"][:1]
        with self.assertRaisesRegex(ValueError, "2 or 3"):
            validate_selection(selection, self.retrieval)

    def test_selection_rejects_four_references(self) -> None:
        selection = valid_selection()
        selection["selected_references"] += [
            {
                **copy.deepcopy(selection["selected_references"][0]),
                "record_id": "COV-CN-0003",
                "include_fields": ["mood"],
            },
            {
                **copy.deepcopy(selection["selected_references"][1]),
                "record_id": "COV-CN-0004",
                "include_fields": ["visual_strategy"],
            },
        ]
        with self.assertRaisesRegex(ValueError, "2 or 3"):
            validate_selection(selection, self.retrieval)

    def test_selection_rejects_duplicate_records(self) -> None:
        selection = valid_selection()
        selection["selected_references"][1]["record_id"] = "COV-CN-0001"
        with self.assertRaisesRegex(ValueError, "distinct record"):
            validate_selection(selection, self.retrieval)

    def test_selection_rejects_nonretrieved_record(self) -> None:
        selection = valid_selection()
        selection["selected_references"][1]["record_id"] = "COV-CN-9999"
        with self.assertRaisesRegex(ValueError, "retrieved candidate"):
            validate_selection(selection, self.retrieval)

    def test_selection_allows_field_overlap_when_each_mapping_remains_explicit(self) -> None:
        selection = valid_selection()
        selection["selected_references"][1]["include_fields"] = ["title_zone", "color"]
        self.assertIsNone(validate_selection(selection, self.retrieval))

    def test_selection_rejects_unknown_include_field(self) -> None:
        selection = valid_selection()
        selection["selected_references"][0]["include_fields"] = [
            "composition",
            "not-a-real-field",
        ]

        with self.assertRaisesRegex(ValueError, "unknown include_fields"):
            validate_selection(selection, self.retrieval)

    def test_chapter_opener_uses_component_specific_include_fields(self) -> None:
        self.assertIsNone(
            validate_selection(
                valid_chapter_opener_selection(),
                valid_chapter_opener_retrieval(),
            )
        )

    def test_cover_rejects_chapter_opener_include_field(self) -> None:
        selection = valid_selection()
        selection["selected_references"][0]["include_fields"] = [
            "chapter_title_zone"
        ]
        with self.assertRaisesRegex(ValueError, "unknown include_fields"):
            validate_selection(selection, self.retrieval)

    def test_selection_rejects_include_field_without_retrieval_evidence(self) -> None:
        selection = valid_selection()
        selection["selected_references"][0]["include_fields"] = ["material"]
        self.retrieval["candidates"][0]["field_scores"] = {
            **self.retrieval["candidates"][0]["field_scores"],
            "material": 0.0,
        }

        with self.assertRaisesRegex(ValueError, "matched evidence"):
            validate_selection(selection, self.retrieval)

    def test_selection_rejects_normalized_duplicate_include_fields(self) -> None:
        selection = valid_selection()
        selection["selected_references"][0]["include_fields"] = [
            "composition",
            " COMPOSITION ",
        ]

        with self.assertRaisesRegex(ValueError, "include_fields.*unique"):
            validate_selection(selection, self.retrieval)

    def test_selection_rejects_normalized_duplicate_exclude_fields(self) -> None:
        selection = valid_selection()
        selection["selected_references"][0]["exclude_fields"] = [
            "原书文字",
            " 原书文字 ",
        ]

        with self.assertRaisesRegex(ValueError, "exclude_fields.*unique"):
            validate_selection(selection, self.retrieval)

    def test_selection_rejects_missing_mapping_field(self) -> None:
        selection = valid_selection()
        del selection["selected_references"][0]["existing_baseline"]
        with self.assertRaisesRegex(ValueError, "selection schema validation failed"):
            validate_selection(selection, self.retrieval)

    def test_selection_rejects_include_exclude_conflict(self) -> None:
        selection = valid_selection()
        selection["selected_references"][0]["exclude_fields"].append(" COMPOSITION ")
        with self.assertRaisesRegex(ValueError, "include/exclude conflict"):
            validate_selection(selection, self.retrieval)

    def test_selection_rejects_unapproved_and_mismatched_context(self) -> None:
        selection = valid_selection()
        selection["status"] = "draft"
        with self.assertRaisesRegex(ValueError, "approved"):
            validate_selection(selection, self.retrieval)

        selection = valid_selection()
        selection["query_id"] = "QUERY-OTHER"
        with self.assertRaisesRegex(ValueError, "query_id"):
            validate_selection(selection, self.retrieval)

    def test_valid_selection_passes(self) -> None:
        self.assertIsNone(validate_selection(valid_selection(), self.retrieval))


class SelectionPromptSafetyPreflightTests(unittest.TestCase):
    def preflight(self):
        function = getattr(prompts_module, "validate_selection_prompt_safety", None)
        self.assertTrue(
            callable(function),
            "prompts must publicly export validate_selection_prompt_safety",
        )
        return function

    def test_draft_rejects_real_title_anywhere_in_reference_transfer_block(self) -> None:
        cases = (
            ("existing_baseline", "本项目四时来信采用安静留白"),
            ("adjustment_instruction", "为《四时来信》重新调整重心"),
            ("preserve_elements", ["保留四时来信的上方安全区"]),
            ("required_changes", ["按四时来信四字书名重新校准"]),
            ("exclude_fields", ["排除四时来信的最终文字"]),
        )
        for field, value in cases:
            with self.subTest(field=field):
                selection = valid_selection()
                selection["status"] = "draft"
                selection["selected_references"][0][field] = value
                with self.assertRaisesRegex(ValueError, "final project title"):
                    self.preflight()(valid_project(), selection)

    def test_draft_rejects_readable_text_requests_in_all_positive_mapping_fields(
        self,
    ) -> None:
        cases = (
            ("existing_baseline", "the source clearly displays the author name"),
            ("adjustment_instruction", "render the publisher name at the bottom"),
            ("preserve_elements", ["在封面显示作者姓名"]),
            ("required_changes", ["在书脊加入书名文字"]),
        )
        for field, value in cases:
            with self.subTest(field=field):
                selection = valid_selection()
                selection["status"] = "draft"
                selection["selected_references"][0][field] = value
                with self.assertRaisesRegex(ValueError, "readable-text request"):
                    self.preflight()(valid_project(), selection)

    def test_prompt_safe_demo_draft_preflights_then_compiles_after_approval(self) -> None:
        example_root = PROJECT_ROOT / "examples" / "component-kb-cover-demo"
        project = json.loads((example_root / "project.json").read_text(encoding="utf-8"))
        selection = json.loads(
            (example_root / "reference-selection-A.json").read_text(encoding="utf-8")
        )
        genome = json.loads(
            (example_root / "compiler-inputs" / "direction-A-genome.json").read_text(
                encoding="utf-8"
            )
        )
        output_spec = json.loads(
            (
                example_root
                / "compiler-inputs"
                / "direction-A-output-spec.json"
            ).read_text(encoding="utf-8")
        )
        selection["status"] = "draft"

        self.assertIsNone(self.preflight()(project, selection))

        selection["status"] = "approved"
        prompt = compile_component_prompt(project, genome, selection, output_spec)
        self.assertEqual(
            selection["selection_id"],
            prompt["selection_id"],
        )
        self.assertEqual([], validate_data(prompt, "book-component-prompt"))

    def test_preflight_is_importable_and_callable_from_an_external_process(self) -> None:
        self.preflight()
        command = (
            "from ai.book_component_kb.prompts import "
            "validate_selection_prompt_safety as preflight; "
            "print(preflight.__name__)"
        )
        with tempfile.TemporaryDirectory() as external_directory:
            result = subprocess.run(
                [sys.executable, "-c", command],
                cwd=external_directory,
                env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("validate_selection_prompt_safety", result.stdout.strip())
        self.assertIn("validate_selection_prompt_safety", prompts_module.__all__)


class PromptCompilationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = valid_project()
        self.genome = valid_genome()
        self.selection = valid_selection()
        self.output_spec = valid_output_spec()

    def test_cover_prompt_has_fixed_blocks_and_no_final_text(self) -> None:
        prompt = compile_component_prompt(
            self.project, self.genome, self.selection, self.output_spec
        )
        self.assertEqual(EXPECTED_BLOCK_ORDER, tuple(prompt["compiled_blocks"]))
        self.assertEqual("none", prompt["generation_constraints"]["readable_text"])
        self.assertEqual("四时来信", prompt["editable_text_overlay"]["title"])
        self.assertNotIn(self.project["title"], prompt["background_prompt"])
        self.assertIn("no readable text", prompt["background_prompt"])
        self.assertEqual([], validate_data(prompt, "book-component-prompt"))

    def test_studio_mark_is_a_supported_editable_non_pixel_layer(self) -> None:
        self.output_spec["editable_text_overlay"] = ["title", "author", "studio_mark"]
        self.output_spec["editable_text_values"] = {
            "title": "四时来信",
            "author": "待确认（可编辑文字层）",
            "studio_mark": "待确认（可编辑文字层）",
        }

        prompt = compile_component_prompt(
            self.project, self.genome, self.selection, self.output_spec
        )

        self.assertEqual(
            "待确认（可编辑文字层）", prompt["editable_text_overlay"]["studio_mark"]
        )
        self.assertNotIn("studio_mark", prompt["background_prompt"].split("NEGATIVE")[0])
        self.assertEqual([], validate_data(prompt, "book-component-prompt"))

    def test_output_spec_binds_exact_overlay_values_without_background_leak(self) -> None:
        self.output_spec["editable_text_overlay"] = ["title", "author", "studio_mark"]
        self.output_spec["editable_text_values"] = {
            "title": "四时来信",
            "author": "待确认（可编辑文字层）",
            "studio_mark": "待确认（可编辑文字层）",
        }

        prompt = compile_component_prompt(
            self.project, self.genome, self.selection, self.output_spec
        )

        self.assertEqual(
            self.output_spec["editable_text_values"], prompt["editable_text_overlay"]
        )
        for value in self.output_spec["editable_text_values"].values():
            self.assertNotIn(value, prompt["background_prompt"])

    def test_output_spec_overlay_values_require_exact_keys_and_nonempty_strings(self) -> None:
        cases = [
            ("missing key", {"title": "四时来信"}),
            (
                "extra key",
                {
                    "title": "四时来信",
                    "author": "待确认",
                    "publisher_mark": "not requested",
                },
            ),
            ("empty value", {"title": "四时来信", "author": " "}),
        ]
        for case_name, values in cases:
            with self.subTest(case_name=case_name):
                output_spec = valid_output_spec()
                output_spec["editable_text_overlay"] = ["title", "author"]
                output_spec["editable_text_values"] = values
                with self.assertRaisesRegex(ValueError, "editable_text_values"):
                    compile_component_prompt(
                        self.project, self.genome, self.selection, output_spec
                    )

    def test_reference_block_contains_every_closed_mapping_field(self) -> None:
        prompt = compile_component_prompt(
            self.project, self.genome, self.selection, self.output_spec
        )
        block = prompt["compiled_blocks"]["REFERENCE_TRANSFERS"]
        for record_id in ("COV-CN-0001", "COV-CN-0002"):
            self.assertIn(record_id, block)
        for label in (
            "record_id",
            "include_fields",
            "existing_baseline",
            "adjustment_instruction",
            "preserve_elements",
            "required_changes",
            "exclude_fields",
        ):
            self.assertEqual(2, block.count(f'"{label}"'), label)

    def test_compiler_rejects_unapproved_selection(self) -> None:
        self.selection["status"] = "draft"
        with self.assertRaisesRegex(ValueError, "approved"):
            compile_component_prompt(
                self.project, self.genome, self.selection, self.output_spec
            )

    def test_compiler_rejects_project_genome_mismatch(self) -> None:
        self.genome["project_id"] = "P-OTHER"
        with self.assertRaisesRegex(ValueError, "project_id"):
            compile_component_prompt(
                self.project, self.genome, self.selection, self.output_spec
            )

    def test_compiler_rejects_request_for_readable_text_pixels(self) -> None:
        forbidden_requests = [
            {"title_text": "四时来信"},
            {"author_text": "林舟"},
            {"publisher_text": "某出版社"},
            {"spine_text": "四时来信"},
            {"page_number": "12"},
            {"readable_text": "请渲染文字"},
        ]
        for request in forbidden_requests:
            with self.subTest(request=request):
                output_spec = valid_output_spec()
                output_spec.update(request)
                with self.assertRaisesRegex(ValueError, "readable text"):
                    compile_component_prompt(
                        self.project, self.genome, self.selection, output_spec
                    )

    def test_compiler_rejects_final_title_leaking_through_generation_prose(self) -> None:
        self.output_spec["image_content"] = "render the final title 四时来信 over the water"
        with self.assertRaisesRegex(ValueError, "final project title"):
            compile_component_prompt(
                self.project, self.genome, self.selection, self.output_spec
            )

        output_spec = valid_output_spec()
        selection = valid_selection()
        selection["selected_references"][0]["adjustment_instruction"] = (
            "在画面上显示四时来信"
        )
        with self.assertRaisesRegex(ValueError, "final project title"):
            compile_component_prompt(self.project, self.genome, selection, output_spec)

    def test_compiler_rejects_controlled_english_and_chinese_readable_text_requests(self) -> None:
        requests = [
            ("image_content", "render the author name Lin Zhou clearly"),
            ("composition", "place the publisher name in the lower-left corner"),
            ("color_light_material", "add spine text in muted ink blue"),
            ("print_and_crop", "print page number 12 inside the trim"),
            ("component_role", "show readable words over the cover background"),
            ("image_content", "在水面上显示作者姓名林舟"),
            ("composition", "在左下角加入出版社名称"),
            ("color_light_material", "用墨蓝色写入书脊文字"),
            ("print_and_crop", "在裁切线内印上页码12"),
            ("component_role", "在封面底图放置可读文字"),
        ]
        for field, value in requests:
            with self.subTest(field=field, value=value):
                output_spec = valid_output_spec()
                output_spec[field] = value
                with self.assertRaisesRegex(ValueError, "readable-text request"):
                    compile_component_prompt(
                        self.project, self.genome, self.selection, output_spec
                    )

    def test_compiler_rejects_plain_readable_text_object_bypasses(self) -> None:
        bypasses = [
            ("image_content", "write the words 春夏秋冬 on the cover"),
            ("composition", "put the author name Lin Zhou at the bottom"),
            ("composition", "把作者姓名林舟放在左下角"),
            ("print_and_crop", "写上页码12并放在裁切线内"),
        ]
        for field, value in bypasses:
            with self.subTest(field=field, value=value):
                output_spec = valid_output_spec()
                output_spec[field] = value
                with self.assertRaisesRegex(ValueError, "readable-text object"):
                    compile_component_prompt(
                        self.project, self.genome, self.selection, output_spec
                    )

    def test_author_person_portrait_and_reader_meanings_are_allowed(self) -> None:
        project_cases = [
            ("primary_readers", "作者本人及家人"),
            ("purpose", "为作者本人及家人制作一本克制的纪念书"),
        ]
        for field, value in project_cases:
            with self.subTest(channel="project", field=field):
                project = valid_project()
                project[field] = value
                prompt = compile_component_prompt(
                    project, self.genome, self.selection, self.output_spec
                )
                self.assertIn(value, prompt["compiled_blocks"]["PROJECT_TRUTH"])

        for value in (
            "a quiet photographic portrait of the author by a window",
            "author and family walking beside a calm lake",
        ):
            with self.subTest(channel="output", value=value):
                output_spec = valid_output_spec()
                output_spec["image_content"] = value
                prompt = compile_component_prompt(
                    self.project, self.genome, self.selection, output_spec
                )
                self.assertIn(value, prompt["compiled_blocks"]["IMAGE_CONTENT"])

        reference_cases = [
            ("existing_baseline", "作者肖像位于画面中央，背景保持克制"),
            ("adjustment_instruction", "保留作者本人的安静姿态并替换背景环境"),
        ]
        for field, value in reference_cases:
            with self.subTest(channel="reference", field=field):
                selection = valid_selection()
                selection["selected_references"][0][field] = value
                prompt = compile_component_prompt(
                    self.project, self.genome, selection, self.output_spec
                )
                self.assertIn(
                    value, prompt["compiled_blocks"]["REFERENCE_TRANSFERS"]
                )

    def test_author_text_qualifiers_remain_rejected(self) -> None:
        for value in (
            "put the author name Lin Zhou at the bottom",
            "place the author's lettering at the bottom",
            "place the author-name at the bottom",
            "在底部显示作者姓名林舟",
            "在底部显示作者的署名",
            "在右下角加入作者文字",
        ):
            with self.subTest(value=value):
                output_spec = valid_output_spec()
                output_spec["image_content"] = value
                with self.assertRaisesRegex(ValueError, "readable-text object"):
                    compile_component_prompt(
                        self.project, self.genome, self.selection, output_spec
                    )

    def test_quality_review_readable_text_bypasses_and_final_title_leak_are_rejected(self) -> None:
        cases = [
            ("editable_text_safe_zones", "在标题安全区显示四时来信", "final project title"),
            ("image_content", "add text reading SPRING at the bottom", "readable-text request"),
            ("image_content", "在封面底部添加文字：春夏秋冬", "readable-text request"),
            ("composition", "show a caption saying SPRING in the lower third", "readable-text request"),
        ]
        for field, value, message in cases:
            with self.subTest(field=field, value=value):
                output_spec = valid_output_spec()
                output_spec[field] = value
                with self.assertRaisesRegex(ValueError, message):
                    compile_component_prompt(
                        self.project, self.genome, self.selection, output_spec
                    )

    def test_quality_rereview_additional_action_and_lettering_bypasses_are_rejected(self) -> None:
        cases = [
            ("image_content", "insert text reading SPRING at the bottom"),
            ("image_content", "overlay the words SPRING across the lower third"),
            ("composition", "render SPRING in bold letters at the bottom"),
            ("image_content", "在封面底部嵌入文字“春天”"),
        ]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                output_spec = valid_output_spec()
                output_spec[field] = value
                with self.assertRaisesRegex(ValueError, "readable-text request"):
                    compile_component_prompt(
                        self.project, self.genome, self.selection, output_spec
                    )

    def test_short_project_titles_do_not_match_unrelated_prompt_text(self) -> None:
        for title in ("家", "a"):
            with self.subTest(title=title):
                project = valid_project()
                project["title"] = title
                prompt = compile_component_prompt(
                    project, self.genome, self.selection, self.output_spec
                )
                self.assertEqual([], validate_data(prompt, "book-component-prompt"))

        project = valid_project()
        project["title"] = "a"
        output_spec = valid_output_spec()
        output_spec["image_content"] = "render a quiet landscape with no text"
        prompt = compile_component_prompt(
            project, self.genome, self.selection, output_spec
        )
        self.assertIn(
            output_spec["image_content"], prompt["compiled_blocks"]["IMAGE_CONTENT"]
        )

    def test_single_cjk_title_is_rejected_in_direct_pixel_action_context(self) -> None:
        project = valid_project()
        project["title"] = "家"
        output_spec = valid_output_spec()
        output_spec["image_content"] = "在封面中央显示家"
        with self.assertRaisesRegex(ValueError, "final project title"):
            compile_component_prompt(
                project, self.genome, self.selection, output_spec
            )

    def test_single_cjk_title_does_not_match_common_cjk_compounds(self) -> None:
        for value in (
            "显示家庭团聚场景",
            "家庭场景中显示三代人物",
            "生成温暖的家居环境",
        ):
            with self.subTest(value=value):
                project = valid_project()
                project["title"] = "家"
                output_spec = valid_output_spec()
                output_spec["image_content"] = value
                prompt = compile_component_prompt(
                    project, self.genome, self.selection, output_spec
                )
                self.assertIn(
                    value, prompt["compiled_blocks"]["IMAGE_CONTENT"]
                )

    def test_explicit_short_and_safe_zone_project_title_requests_remain_rejected(self) -> None:
        cases = [
            ("家", "image_content", "在封面中央显示《家》"),
            ("a", "image_content", 'render the title "a" in the center'),
            ("四时来信", "editable_text_safe_zones", "在标题安全区显示四时来信"),
        ]
        for title, field, value in cases:
            with self.subTest(title=title, field=field):
                project = valid_project()
                project["title"] = title
                output_spec = valid_output_spec()
                output_spec[field] = value
                with self.assertRaisesRegex(ValueError, "final project title"):
                    compile_component_prompt(
                        project, self.genome, self.selection, output_spec
                    )

    def test_physical_letters_remain_valid_image_content(self) -> None:
        output_spec = valid_output_spec()
        output_spec["image_content"] = (
            "place a bundle of old letters and envelopes on a quiet wooden table"
        )
        prompt = compile_component_prompt(
            self.project, self.genome, self.selection, output_spec
        )
        self.assertIn(
            output_spec["image_content"], prompt["compiled_blocks"]["IMAGE_CONTENT"]
        )

    def test_title_zone_and_typography_safe_structure_descriptions_are_allowed(self) -> None:
        descriptions = [
            "标题区域保持大面积留白，不生成任何字形",
            "preserve an empty title zone for the editable overlay",
            "preserve quiet typography-safe negative space",
        ]
        for value in descriptions:
            with self.subTest(value=value):
                selection = valid_selection()
                selection["selected_references"][0]["existing_baseline"] = value
                prompt = compile_component_prompt(
                    self.project, self.genome, selection, self.output_spec
                )
                self.assertIn(
                    value, prompt["compiled_blocks"]["REFERENCE_TRANSFERS"]
                )

    def test_editable_genome_metadata_is_allowed_and_omitted_from_pixel_genome_block(self) -> None:
        genome = valid_genome()
        genome["chapter_opener"]["instruction"] = (
            "chapter title should remain visible only in an editable text layer"
        )
        prompt = compile_component_prompt(
            self.project, genome, self.selection, self.output_spec
        )
        genome_block = prompt["compiled_blocks"]["DESIGN_GENOME"]
        self.assertEqual(
            {"direction_id", "brand_profile", "color", "grid", "page_families"},
            set(json.loads(genome_block)),
        )
        self.assertNotIn("chapter title", genome_block)
        self.assertNotIn("chapter_opener", genome_block)
        self.assertNotIn("editable text layer", prompt["background_prompt"])

        genome = valid_genome()
        genome["color"]["note"] = "四时来信"
        with self.assertRaisesRegex(ValueError, "final project title"):
            compile_component_prompt(
                self.project, genome, self.selection, self.output_spec
            )

    def test_compiler_rejects_project_truth_fields_that_repeat_real_title(self) -> None:
        for field, value in (
            ("purpose", "为《四时来信》制作一本纪念书"),
            ("primary_readers", "《四时来信》的家庭读者"),
        ):
            with self.subTest(field=field):
                project = valid_project()
                project[field] = value
                with self.assertRaisesRegex(ValueError, "final project title"):
                    compile_component_prompt(
                        project, self.genome, self.selection, self.output_spec
                    )

    def test_compiler_rejects_readable_text_requests_in_positive_reference_fields(self) -> None:
        requests = [
            ("existing_baseline", "the source clearly displays the author name"),
            ("adjustment_instruction", "render the publisher name at the bottom"),
            ("preserve_elements", ["在封面显示作者姓名"]),
            ("required_changes", ["在书脊加入书名文字"]),
        ]
        for field, value in requests:
            with self.subTest(field=field):
                selection = valid_selection()
                selection["selected_references"][0][field] = value
                with self.assertRaisesRegex(ValueError, "readable-text request"):
                    compile_component_prompt(
                        self.project, self.genome, selection, self.output_spec
                    )

    def test_text_guard_does_not_reject_negative_exclusions_or_editable_safe_zones(self) -> None:
        output_spec = valid_output_spec()
        output_spec["negative_constraints"].extend(
            ["do not render the author name", "不要显示出版社名称或页码"]
        )
        output_spec["editable_text_safe_zones"] = (
            "reserve safe zones for title, author, publisher mark, and spine text"
        )
        selection = valid_selection()
        selection["selected_references"][0]["exclude_fields"].extend(
            ["readable words", "作者姓名", "出版社名称", "书脊文字", "页码"]
        )
        prompt = compile_component_prompt(
            self.project, self.genome, selection, output_spec
        )
        self.assertEqual("四时来信", prompt["editable_text_overlay"]["title"])
        self.assertIn("do not render the author name", prompt["negative_constraints"])

    def test_compiler_rejects_unknown_overlay_and_bad_output_spec(self) -> None:
        self.output_spec["editable_text_overlay"].append("page_number")
        with self.assertRaisesRegex(ValueError, "editable_text_overlay"):
            compile_component_prompt(
                self.project, self.genome, self.selection, self.output_spec
            )

        output_spec = valid_output_spec()
        del output_spec["aspect_ratio"]
        with self.assertRaisesRegex(ValueError, "output_spec"):
            compile_component_prompt(
                self.project, self.genome, self.selection, output_spec
            )

    def test_compilation_is_byte_deterministic(self) -> None:
        first = compile_component_prompt(
            self.project, self.genome, self.selection, self.output_spec
        )
        second = compile_component_prompt(
            copy.deepcopy(self.project),
            copy.deepcopy(self.genome),
            copy.deepcopy(self.selection),
            copy.deepcopy(self.output_spec),
        )
        self.assertEqual(
            json.dumps(first, ensure_ascii=False, separators=(",", ":")),
            json.dumps(second, ensure_ascii=False, separators=(",", ":")),
        )

    def test_cli_writes_only_prompt_sidecar_json(self) -> None:
        script = PROJECT_ROOT / "scripts" / "book_component_kb" / "compile_prompt.py"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = {
                "project": self.project,
                "genome": self.genome,
                "selection": self.selection,
                "output-spec": self.output_spec,
            }
            arguments: list[str] = []
            for name, value in inputs.items():
                path = root / f"{name}.json"
                path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
                arguments.extend([f"--{name}", str(path)])
            output = root / "cover-prompt.json"
            completed = subprocess.run(
                [sys.executable, str(script), *arguments, "--output", str(output)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual("", completed.stdout)
            prompt = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual([], validate_data(prompt, "book-component-prompt"))
            self.assertEqual(["cover-prompt.json", "genome.json", "output-spec.json", "project.json", "selection.json"], sorted(path.name for path in root.iterdir()))
            self.assertFalse(any(path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} for path in root.iterdir()))

    def test_cli_rejects_output_aliasing_any_input_without_changing_bytes(self) -> None:
        script = PROJECT_ROOT / "scripts" / "book_component_kb" / "compile_prompt.py"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            values = {
                "project": self.project,
                "genome": self.genome,
                "selection": self.selection,
                "output-spec": self.output_spec,
            }
            paths: dict[str, Path] = {}
            for name, value in values.items():
                path = root / f"{name}.json"
                path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
                paths[name] = path
            original = {name: path.read_bytes() for name, path in paths.items()}

            base_arguments: list[str] = []
            for name, path in paths.items():
                base_arguments.extend([f"--{name}", str(path)])

            alias_parent = root / "alias-parent"
            alias_parent.mkdir()
            conflicts = [
                ("project-dotdot", alias_parent / ".." / "project.json"),
                ("genome", paths["genome"]),
                ("selection", paths["selection"]),
                ("output-spec", paths["output-spec"]),
            ]
            symlink_output = root / "project-symlink.json"
            symlink_output.symlink_to(paths["project"])
            hardlink_output = root / "project-hardlink.json"
            os.link(paths["project"], hardlink_output)
            conflicts.extend(
                [("project-symlink", symlink_output), ("project-hardlink", hardlink_output)]
            )

            for label, output in conflicts:
                for name, path in paths.items():
                    path.write_bytes(original[name])
                with self.subTest(label=label):
                    completed = subprocess.run(
                        [
                            sys.executable,
                            str(script),
                            *base_arguments,
                            "--output",
                            str(output),
                        ],
                        cwd=PROJECT_ROOT,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(1, completed.returncode, completed.stderr)
                    self.assertIn("must not alias", completed.stderr)
                    self.assertEqual(
                        original,
                        {name: path.read_bytes() for name, path in paths.items()},
                    )
                    if output.exists():
                        self.assertEqual(original["project"] if "project" in label else original[label], output.read_bytes())


class IntegratedTypographyPromptCompilationTests(unittest.TestCase):
    def integrated_inputs(self):
        project = valid_project()
        project.update(
            {
                "title": "失落人间",
                "subtitle": "在所有归途之外",
                "author": "早睡的猫",
            }
        )
        output = valid_output_spec()
        output["text_rendering_mode"] = "integrated-typography"
        output["integrated_text"] = [
            {
                "text_id": "TITLE-001",
                "surface": "front",
                "role": "title",
                "value": "失落人间",
                "language": "zh-CN",
            },
            {
                "text_id": "SUBTITLE-001",
                "surface": "front",
                "role": "subtitle",
                "value": "在所有归途之外",
                "language": "zh-CN",
            },
            {
                "text_id": "AUTHOR-001",
                "surface": "front",
                "role": "author",
                "value": "早睡的猫",
                "language": "zh-CN",
            },
        ]
        output["editable_text_backup"] = {
            item["text_id"]: item["value"] for item in output["integrated_text"]
        }
        output["editable_text_overlay"] = ["title", "author", "other_text"]
        output["editable_text_values"] = {
            "title": "失落人间",
            "author": "早睡的猫",
            "other_text": "在所有归途之外",
        }
        return project, valid_genome(), valid_selection(), output

    def test_integrated_cover_compiles_exact_registered_text(self) -> None:
        project, genome, selection, output = self.integrated_inputs()
        prompt = compile_component_prompt(project, genome, selection, output)
        self.assertEqual("integrated-typography", prompt["text_rendering_mode"])
        self.assertEqual(
            "exact-project-text",
            prompt["generation_constraints"]["readable_text"],
        )
        self.assertEqual(output["integrated_text"], prompt["integrated_text"])
        self.assertEqual(
            output["editable_text_backup"], prompt["editable_text_backup"]
        )
        self.assertIn("INTEGRATED_TEXT", prompt["compiled_blocks"])
        self.assertIn("失落人间", prompt["compiled_blocks"]["INTEGRATED_TEXT"])
        for block_name, block in prompt["compiled_blocks"].items():
            if block_name != "INTEGRATED_TEXT":
                self.assertNotIn("失落人间", block, block_name)
        self.assertEqual([], validate_data(prompt, "book-component-prompt"))

    def test_integrated_mode_removes_legacy_no_text_contradictions(self) -> None:
        project, genome, selection, output = self.integrated_inputs()
        prompt = compile_component_prompt(project, genome, selection, output)
        negatives = " ".join(prompt["negative_constraints"]).casefold()
        self.assertNotIn("no readable text", negatives)
        self.assertNotIn("no title glyphs", negatives)
        self.assertNotIn("no author glyphs", negatives)
        self.assertIn("no unregistered readable text", negatives)
        self.assertIn("no isbn", negatives)

    def test_integrated_cover_compilation_is_deterministic(self) -> None:
        inputs = self.integrated_inputs()
        first = compile_component_prompt(*copy.deepcopy(inputs))
        second = compile_component_prompt(*copy.deepcopy(inputs))
        self.assertEqual(first, second)

    def test_machine_identifier_cannot_hide_in_positive_prompt_fields(self) -> None:
        for field, value in (
            ("composition", "在画面下方放置 ISBN 9787553784182"),
            ("image_content", "draw a barcode area"),
            ("color_light_material", "定价 58 元使用暗红色"),
            ("editable_text_safe_zones", "保留二维码区域"),
            ("component_role", "CIP information cover"),
        ):
            with self.subTest(field=field):
                project, genome, selection, output = self.integrated_inputs()
                output[field] = value
                with self.assertRaisesRegex(ValueError, "machine identifier"):
                    compile_component_prompt(project, genome, selection, output)

    def test_legacy_prompt_keeps_original_shape(self) -> None:
        prompt = compile_component_prompt(
            valid_project(), valid_genome(), valid_selection(), valid_output_spec()
        )
        self.assertNotIn("text_rendering_mode", prompt)
        self.assertNotIn("INTEGRATED_TEXT", prompt["compiled_blocks"])
        self.assertEqual("none", prompt["generation_constraints"]["readable_text"])
        self.assertEqual(tuple(EXPECTED_BLOCK_ORDER), tuple(prompt["compiled_blocks"]))


if __name__ == "__main__":
    unittest.main()
