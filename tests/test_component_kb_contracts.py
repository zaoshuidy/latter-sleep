import copy
import json
import unittest
from pathlib import Path

from ai.contracts import validate_data


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "component-kb"
COMPILED_BLOCKS = (
    "PROJECT_TRUTH",
    "COMPONENT_ROLE",
    "DESIGN_GENOME",
    "REFERENCE_TRANSFERS",
    "COMPOSITION",
    "IMAGE_CONTENT",
    "COLOR_LIGHT_MATERIAL",
    "EDITABLE_TEXT_SAFE_ZONES",
    "PRINT_AND_CROP",
    "NEGATIVE",
    "OUTPUT_SPEC",
)


def fixture(name):
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def valid_cover_record():
    return {
        "schema_version": "1.0",
        "record_id": "COV-CN-0001",
        "component_type": "cover",
        "identity": {
            "book_case_id": "BOOK-CN-0001",
            "book_title": "四时来信",
            "author": None,
            "designer": None,
            "publisher": None,
            "publication_year": 2024,
            "language": "zh-CN",
        },
        "source": {
            "source_registry_id": "SRC-CN-0001",
            "source_url": "https://example.com/books/BOOK-CN-0001",
            "platform": "出版社官网",
            "collected_at": "2026-08-10",
            "publication_year": 2024,
            "publication_year_source_url": "https://example.com/books/BOOK-CN-0001/bibliography",
        },
        "asset": {
            "relative_path": "cover/assets/COV-CN-0001.jpg",
            "sha256": "a" * 64,
            "mime_type": "image/jpeg",
            "width": 1200,
            "height": 1800,
        },
        "component_profile": {
            "cover_scope": "front",
            "visual_strategy": "illustration",
            "composition": "whitespace",
            "title_zone": "top",
            "spine_relationship": "not-visible",
            "thumbnail_recognition": "strong",
        },
        "visual_decomposition": {
            "overall_strategy": "纸船与水纹构成留白封面",
            "observations": [
                {
                    "aspect": "主体",
                    "value": "纸船位于画面下方",
                    "visibility": "clear",
                    "confidence": 0.95,
                    "evidence": "封面图像可见纸船轮廓",
                    "content_tags": ["纸船", "水纹"],
                }
            ],
        },
        "reference_transfer": {
            "transferable": ["上方标题留白", "低饱和蓝色"],
            "avoid_copying": ["不复用具体纸船插画"],
            "adaptation_notes": ["以项目自身意象替换纸船"],
        },
        "retrieval_features": {
            "style_tags": ["克制", "编辑感"],
            "content_tags": ["纸船", "书信"],
            "color_tags": ["米白", "墨蓝"],
            "mood_tags": ["安静", "回忆"],
        },
        "lifecycle": {
            "status": "accumulation",
            "created_at": "2026-08-10",
            "updated_at": "2026-08-10",
        },
    }


def valid_component_prompt():
    return {
        "schema_version": "1.0",
        "prompt_id": "PROMPT-COV-0001",
        "component_type": "cover",
        "selection_id": "SEL-COV-0001",
        "compiled_blocks": {block: f"{block} block" for block in COMPILED_BLOCKS},
        "background_prompt": "A restrained Chinese book cover background with a calm blue water surface and generous upper whitespace.",
        "generation_constraints": {
            "readable_text": "none",
            "logo": "none",
            "watermark": "none",
            "aspect_ratio": "2:3",
        },
        "editable_text_overlay": {
            "title": "四时来信",
            "author": "林舟",
            "studio_mark": "纸舟设计",
        },
        "negative_constraints": ["no readable text", "no logo"],
    }


def valid_contract_examples():
    return {
        "book-component-source-registry": {
            "schema_version": "1.0",
            "source_mode": "accumulation",
            "sources": [
                {
                    "source_registry_id": "SRC-CN-0001",
                    "source_type": "book",
                    "title": "四时来信",
                    "source_url": "https://example.com/books/BOOK-CN-0001",
                    "platform": "出版社官网",
                    "collected_at": "2026-08-10",
                    "publication_year": 2024,
                    "publication_year_source_url": "https://example.com/books/BOOK-CN-0001/bibliography",
                    "authorization_status": "accumulation",
                },
                {
                    "source_registry_id": "SRC-CN-0002",
                    "source_type": "series",
                    "title": "纸船文学丛书",
                    "source_url": "https://example.com/series/SER-CN-0001",
                    "platform": "出版社官网",
                    "collected_at": "2026-08-10",
                    "publication_year": 2024,
                    "publication_year_source_url": "https://example.com/series/SER-CN-0001/bibliography",
                    "authorization_status": "accumulation",
                },
            ],
        },
        "book-component-retrieval-query": {
            "schema_version": "1.0",
            "query_id": "QUERY-COV-0001",
            "component_type": "cover",
            "field_targets": {
                "visual_strategy": ["illustration"],
                "composition": ["whitespace"],
                "title_zone": ["top"],
                "color": ["墨蓝"],
                "material": ["无涂布纸"],
                "mood": ["安静"],
                "cover_scope": ["front"],
                "book_category": ["memoir"],
            },
            "selection_policy": {"max_results": 5, "diversity": "balanced"},
        },
        "book-component-retrieval-result": {
            "schema_version": "1.0",
            "query_id": "QUERY-COV-0001",
            "component_type": "cover",
            "status": "available",
            "candidates": [
                {
                    "record_id": "COV-CN-0001",
                    "book_case_id": "BOOK-CN-0001",
                    "field_scores": {
                        "visual_strategy": 0.2,
                        "composition": 0.2,
                        "title_zone": 0.15,
                        "color": 0.15,
                        "material": 0.1,
                        "mood": 0.1,
                        "cover_scope": 0.05,
                        "book_category": 0.05,
                    },
                    "total_score": 0.92,
                    "match_explanation": "封面构图、色彩和情绪标签与查询匹配。",
                }
            ],
        },
        "book-component-reference-selection": {
            "schema_version": "1.0",
            "selection_id": "SEL-COV-0001",
            "query_id": "QUERY-COV-0001",
            "component_type": "cover",
            "selected_references": [
                {
                    "record_id": "COV-CN-0001",
                    "include_fields": ["composition", "title_zone"],
                    "existing_baseline": "上方留白与低饱和蓝色",
                    "adjustment_instruction": "替换为项目自身意象。",
                    "preserve_elements": ["标题留白关系"],
                    "required_changes": ["不复制纸船图形"],
                    "exclude_fields": ["原书名", "原作者名"],
                },
                {
                    "record_id": "COV-CN-0002",
                    "include_fields": ["color"],
                    "existing_baseline": "米白与墨蓝配色",
                    "adjustment_instruction": "按项目设计基因调整色彩比例。",
                    "preserve_elements": ["低饱和关系"],
                    "required_changes": ["替换具体图形"],
                    "exclude_fields": ["原出版社标识"],
                }
            ],
            "status": "approved",
        },
        "book-component-prompt": valid_component_prompt(),
        "book-component-image-review": {
            "schema_version": "1.0",
            "review_id": "REVIEW-COV-0001",
            "prompt_id": "PROMPT-COV-0001",
            "component_type": "cover",
            "image": {
                "relative_path": "generated/COV-0001.png",
                "sha256": "b" * 64,
                "mime_type": "image/png",
            },
            "observations": [
                {
                    "aspect": "标题区",
                    "value": "上方留白充足",
                    "visibility": "clear",
                    "confidence": 0.9,
                    "evidence": "图像上方约三分之一为空白",
                    "content_tags": ["留白", "标题区"],
                }
            ],
            "checks": {
                "no_unwanted_text": True,
                "safe_zones_clear": True,
                "genome_consistent": True,
                "reference_transformed": True,
                "print_crop_valid": True,
                "truthfulness_valid": True,
                "provenance_complete": True,
            },
            "human_selection": {
                "decision": "selected",
                "approval_id": "APPROVAL-COV-0001",
                "approved_by": "项目维护人",
                "selected_version": "V001",
                "selected_image_sha256": "b" * 64,
                "approval_artifact_sha256": "a" * 64,
            },
            "status": "selected",
        },
        "book-component-kb-promotion": {
            "schema_version": "1.0",
            "promotion_id": "PROMOTE-COV-0001",
            "review_id": "REVIEW-COV-0001",
            "record_id": "COV-CN-0001",
            "component_type": "cover",
            "status": "proposed",
            "human_approval": "pending",
            "target_lifecycle": "accumulation",
        },
    }


class ComponentKnowledgeContractsTests(unittest.TestCase):
    def test_cover_record_requires_real_source_asset_and_cover_profile(self):
        record = fixture("cover-record.json")
        self.assertEqual([], validate_data(record, "book-component-reference-record"))
        for field in ["identity", "source", "asset", "component_profile", "visual_decomposition", "reference_transfer", "retrieval_features", "lifecycle"]:
            broken = copy.deepcopy(record)
            del broken[field]
            self.assertTrue(validate_data(broken, "book-component-reference-record"), field)

    def test_cover_record_closes_fields_and_restricts_cover_values(self):
        record = valid_cover_record()
        record["unreviewed_note"] = "must not be accepted"
        self.assertTrue(validate_data(record, "book-component-reference-record"))
        record = valid_cover_record()
        record["component_profile"]["title_zone"] = "freeform"
        self.assertTrue(validate_data(record, "book-component-reference-record"))

    def test_final_text_is_an_editable_overlay(self):
        prompt = valid_component_prompt()
        self.assertEqual([], validate_data(prompt, "book-component-prompt"))
        prompt["generation_constraints"]["readable_text"] = "四时来信"
        self.assertTrue(validate_data(prompt, "book-component-prompt"))

    def test_compiled_prompt_requires_all_eleven_fixed_blocks(self):
        prompt = valid_component_prompt()
        self.assertEqual([], validate_data(prompt, "book-component-prompt"))
        self.assertEqual(COMPILED_BLOCKS, tuple(prompt["compiled_blocks"]))
        del prompt["compiled_blocks"]["OUTPUT_SPEC"]
        self.assertTrue(validate_data(prompt, "book-component-prompt"))
        prompt = valid_component_prompt()
        prompt["compiled_blocks"]["UNTRACKED_BLOCK"] = "must be rejected"
        self.assertTrue(validate_data(prompt, "book-component-prompt"))

    def test_every_observation_has_evidence_and_nonempty_content_tags(self):
        review = valid_contract_examples()["book-component-image-review"]
        self.assertEqual([], validate_data(review, "book-component-image-review"))
        del review["observations"][0]["evidence"]
        self.assertTrue(validate_data(review, "book-component-image-review"))
        review = valid_contract_examples()["book-component-image-review"]
        review["observations"][0]["content_tags"] = []
        self.assertTrue(validate_data(review, "book-component-image-review"))

    def test_each_shared_contract_accepts_its_canonical_example(self):
        for schema_name, example in valid_contract_examples().items():
            with self.subTest(schema_name=schema_name):
                self.assertEqual([], validate_data(example, schema_name))

    def test_source_registry_allows_an_empty_accumulation_library(self):
        registry = {"schema_version": "1.0", "source_mode": "accumulation", "sources": []}
        self.assertEqual([], validate_data(registry, "book-component-source-registry"))

    def test_reference_and_registry_ids_use_component_specific_canonical_formats(self):
        registry = valid_contract_examples()["book-component-source-registry"]
        registry["sources"][0]["source_registry_id"] = "freeform-source"
        self.assertTrue(validate_data(registry, "book-component-source-registry"))

        for field, value in (
            (("record_id",), "TOC-CN-0001"),
            (("identity", "book_case_id"), "book-1"),
            (("source", "source_registry_id"), "BOOK-CN-0001"),
        ):
            with self.subTest(field=field):
                record = valid_cover_record()
                target = record
                for key in field[:-1]:
                    target = target[key]
                target[field[-1]] = value
                self.assertTrue(validate_data(record, "book-component-reference-record"))

    def test_retrieval_query_requires_nonempty_closed_field_targets(self):
        canonical = valid_contract_examples()["book-component-retrieval-query"]
        self.assertEqual([], validate_data(canonical, "book-component-retrieval-query"))
        for mutation in ("grouped", "empty", "unknown", "empty_values"):
            with self.subTest(mutation=mutation):
                query = copy.deepcopy(canonical)
                if mutation == "grouped":
                    query["query_features"] = {
                        "style_tags": ["illustration"],
                        "content_tags": ["memoir"],
                        "color_tags": ["墨蓝"],
                        "mood_tags": ["安静"],
                    }
                    del query["field_targets"]
                elif mutation == "empty":
                    query["field_targets"] = {}
                elif mutation == "unknown":
                    query["field_targets"]["freeform"] = ["must fail"]
                else:
                    query["field_targets"]["material"] = []
                self.assertTrue(validate_data(query, "book-component-retrieval-query"))

    def test_retrieval_result_uses_status_and_explainable_candidates(self):
        result = valid_contract_examples()["book-component-retrieval-result"]
        self.assertEqual([], validate_data(result, "book-component-retrieval-result"))
        legacy = copy.deepcopy(result)
        legacy["matches"] = legacy.pop("candidates")
        self.assertTrue(validate_data(legacy, "book-component-retrieval-result"))
        del result["candidates"][0]["match_explanation"]
        self.assertTrue(validate_data(result, "book-component-retrieval-result"))

    def test_reference_selection_requires_two_or_three_closed_mappings(self):
        selection = valid_contract_examples()["book-component-reference-selection"]
        self.assertEqual([], validate_data(selection, "book-component-reference-selection"))
        selection["selected_references"] = selection["selected_references"][:1]
        self.assertTrue(validate_data(selection, "book-component-reference-selection"))
        selection = valid_contract_examples()["book-component-reference-selection"]
        selection["selected_references"].extend(copy.deepcopy(selection["selected_references"]))
        self.assertTrue(validate_data(selection, "book-component-reference-selection"))
        selection = valid_contract_examples()["book-component-reference-selection"]
        del selection["selected_references"][0]["include_fields"]
        self.assertTrue(validate_data(selection, "book-component-reference-selection"))
        selection = valid_contract_examples()["book-component-reference-selection"]
        selection["selected_references"][0]["freeform_transfer"] = "must be rejected"
        self.assertTrue(validate_data(selection, "book-component-reference-selection"))

    def test_selected_review_requires_each_explicit_boolean_check(self):
        review = valid_contract_examples()["book-component-image-review"]
        self.assertEqual([], validate_data(review, "book-component-image-review"))
        self.assertEqual("selected", review["status"])
        for check_name in review["checks"]:
            broken = copy.deepcopy(review)
            del broken["checks"][check_name]
            self.assertTrue(validate_data(broken, "book-component-image-review"), check_name)

    def test_promotion_is_only_a_pending_human_proposal(self):
        promotion = valid_contract_examples()["book-component-kb-promotion"]
        self.assertEqual([], validate_data(promotion, "book-component-kb-promotion"))
        for field, value in [("human_approval", "approved"), ("target_lifecycle", "confirmed"), ("status", "promoted")]:
            broken = copy.deepcopy(promotion)
            broken[field] = value
            self.assertTrue(validate_data(broken, "book-component-kb-promotion"), field)

    def test_record_allows_unstated_credits_and_rejects_invalid_source_metadata(self):
        record = valid_cover_record()
        self.assertEqual([], validate_data(record, "book-component-reference-record"))
        for field in ["author", "designer", "publisher"]:
            self.assertIsNone(record["identity"][field])
        invalid_cases = [
            ("identity is closed", lambda data: data["identity"].update({"unverified_credit": "x"})),
            ("year lower bound", lambda data: data["identity"].update({"publication_year": 2016})),
            ("year upper bound", lambda data: data["identity"].update({"publication_year": 2027})),
            ("component enum", lambda data: data.update({"component_type": "poster"})),
            ("invalid url", lambda data: data["source"].update({"source_url": "not-a-url"})),
            ("invalid date", lambda data: data["source"].update({"collected_at": "2026-99-99"})),
            ("evidence year lower bound", lambda data: data["source"].update({"publication_year": 2016})),
            ("invalid evidence url", lambda data: data["source"].update({"publication_year_source_url": "not-a-url"})),
        ]
        for case_name, mutate in invalid_cases:
            with self.subTest(case_name=case_name):
                broken = copy.deepcopy(record)
                mutate(broken)
                self.assertTrue(validate_data(broken, "book-component-reference-record"))

    def test_record_and_registry_require_publication_year_evidence(self):
        record = valid_cover_record()
        registry = valid_contract_examples()["book-component-source-registry"]
        for field in ("publication_year", "publication_year_source_url"):
            with self.subTest(contract="record", field=field):
                broken = copy.deepcopy(record)
                del broken["source"][field]
                self.assertTrue(validate_data(broken, "book-component-reference-record"))
            with self.subTest(contract="registry", field=field):
                broken = copy.deepcopy(registry)
                del broken["sources"][0][field]
                self.assertTrue(validate_data(broken, "book-component-source-registry"))

    def test_calendar_dates_reject_non_leap_day_across_record_and_registry(self):
        record_paths = [
            ("source collected_at", lambda data, value: data["source"].update({"collected_at": value})),
            ("lifecycle created_at", lambda data, value: data["lifecycle"].update({"created_at": value})),
            ("lifecycle updated_at", lambda data, value: data["lifecycle"].update({"updated_at": value})),
        ]
        for path_name, set_date in record_paths:
            with self.subTest(path_name=path_name, date="2024-02-29"):
                record = valid_cover_record()
                set_date(record, "2024-02-29")
                self.assertEqual([], validate_data(record, "book-component-reference-record"))
            with self.subTest(path_name=path_name, date="2026-08-10"):
                record = valid_cover_record()
                set_date(record, "2026-08-10")
                self.assertEqual([], validate_data(record, "book-component-reference-record"))
            with self.subTest(path_name=path_name, date="2025-02-29"):
                record = valid_cover_record()
                set_date(record, "2025-02-29")
                self.assertTrue(validate_data(record, "book-component-reference-record"))

        for date, expected_errors in [("2024-02-29", []), ("2026-08-10", []), ("2025-02-29", None)]:
            with self.subTest(registry_date=date):
                registry = valid_contract_examples()["book-component-source-registry"]
                registry["sources"][0]["collected_at"] = date
                errors = validate_data(registry, "book-component-source-registry")
                if expected_errors is None:
                    self.assertTrue(errors)
                else:
                    self.assertEqual(expected_errors, errors)

    def test_empty_overlay_is_rejected_in_a_table_driven_contract_check(self):
        cases = [
            ("empty overlay", {}),
            ("unknown overlay field", {"untracked_text": "x"}),
        ]
        for case_name, overlay in cases:
            with self.subTest(case_name=case_name):
                prompt = valid_component_prompt()
                prompt["editable_text_overlay"] = overlay
                self.assertTrue(validate_data(prompt, "book-component-prompt"))

    def test_fixtures_have_canonical_source_and_cover_ids(self):
        registry = fixture("source-registry.json")
        record = fixture("cover-record.json")
        self.assertEqual([], validate_data(registry, "book-component-source-registry"))
        self.assertEqual("SRC-CN-0001", registry["sources"][0]["source_registry_id"])
        self.assertEqual("SRC-CN-0002", registry["sources"][1]["source_registry_id"])
        self.assertEqual("COV-CN-0001", record["record_id"])


if __name__ == "__main__":
    unittest.main()
