import hashlib
import html as html_module
import json
import re
import unittest
from pathlib import Path

from ai.contracts import validate_data
from ai.book_component_kb.integrated_text import contains_machine_identifier
from ai.book_component_kb.paths import read_image_metadata, sha256_file


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "projects" / "lost-human-world-cover"


class LostHumanWorldCoverProjectTests(unittest.TestCase):
    def load(self, relative: str) -> dict:
        return json.loads((PROJECT / relative).read_text(encoding="utf-8"))

    def test_project_and_query_are_schema_valid_and_truthful(self):
        project = self.load("inputs/project.json")
        query = self.load("inputs/query.json")

        self.assertEqual([], validate_data(project, "project-config"))
        self.assertEqual([], validate_data(query, "book-component-retrieval-query"))
        self.assertEqual("BOOK-LOST-HUMAN-WORLD", project["project_id"])
        self.assertEqual("失落人间", project["title"])
        self.assertEqual("literary-fiction", project["primary_category"])
        self.assertEqual("145mm × 210mm", project["page_size"])
        self.assertEqual("在所有归途之外", project["subtitle"])
        self.assertEqual("早睡的猫", project["author"])
        self.assertNotIn("subtitle:在所有归途之外", project["tags"])
        self.assertNotIn("author:早睡的猫", project["tags"])
        self.assertEqual("cover", query["component_type"])
        self.assertEqual(5, query["selection_policy"]["max_results"])

    def test_front_integrated_text_is_exact_and_has_editable_fallback(self):
        text = self.load("inputs/integrated-text-front.json")
        expected = [
            ("TITLE-001", "front", "title", "失落人间"),
            ("SUBTITLE-001", "front", "subtitle", "在所有归途之外"),
            ("AUTHOR-001", "front", "author", "早睡的猫"),
        ]
        self.assertEqual("integrated-typography", text["text_rendering_mode"])
        self.assertEqual(
            expected,
            [
                (item["text_id"], item["surface"], item["role"], item["value"])
                for item in text["integrated_text"]
            ],
        )
        self.assertEqual(
            {item["text_id"]: item["value"] for item in text["integrated_text"]},
            text["editable_text_backup"],
        )
        self.assertFalse(
            any(
                contains_machine_identifier(item["value"])
                for item in text["integrated_text"]
            )
        )
        self.assertTrue(all(item["surface"] == "front" for item in text["integrated_text"]))

    def test_chapter_opener_v001_is_bound_to_the_approved_gate_and_keeps_text_editable(self):
        generated = PROJECT / "chapter-opener" / "generated"
        version = self.load("chapter-opener/versions/chapter-opener-v001.json")
        selection = self.load("chapter-opener/reference-selection-A.json")
        svg = (generated / "chapter-opener-v001.svg").read_text(encoding="utf-8")

        self.assertEqual("approved", selection["status"])
        self.assertEqual(selection["selection_id"], version["selection_id"])
        self.assertEqual("draft", version["status"])
        self.assertTrue((generated / "chapter-opener-background-v001.png").is_file())
        self.assertTrue((generated / "chapter-opener-v001-preview.png").is_file())
        self.assertIn('id="editable-chapter-text"', svg)
        self.assertIn('id="chapter-number"', svg)
        self.assertIn('id="chapter-title"', svg)
        self.assertIn("第一章", svg)
        self.assertIn("车", svg)
        self.assertIn("故", svg)

    def test_selected_chapter_opener_has_human_approval_and_300dpi_export(self):
        approval = self.load(
            "chapter-opener/approvals/chapter-opener-v001-selection.json"
        )
        review = self.load(
            "chapter-opener/reviews/chapter-opener-v001-selected-review.json"
        )
        export = self.load(
            "chapter-opener/versions/chapter-opener-v001-production-export.json"
        )
        approved_preview = (
            PROJECT / "chapter-opener" / review["image"]["relative_path"]
        )
        production_png = (
            PROJECT / "chapter-opener" / export["raster_preview"]["path"]
        )

        self.assertEqual(
            [], validate_data(approval, "book-project-image-selection-approval")
        )
        self.assertEqual([], validate_data(review, "book-component-image-review"))
        self.assertEqual("selected", review["status"])
        self.assertEqual("selected", export["selection_status"])
        self.assertEqual(sha256_file(approved_preview), approval["selected_image_sha256"])
        self.assertEqual(sha256_file(production_png), export["raster_preview"]["sha256"])
        self.assertEqual(
            {"width": 3425, "height": 2480},
            {
                "width": read_image_metadata(production_png)["width"],
                "height": read_image_metadata(production_png)["height"],
            },
        )

    def test_body_opening_v001_uses_exact_source_text_and_approved_layout(self):
        source_path = PROJECT / "manuscript/chapter-01.md"
        html_path = PROJECT / "body-opening/body-opening-v001.html"
        layout_path = PROJECT / "body-opening/body-opening-v001-layout.json"
        preview_path = PROJECT / "body-opening/body-opening-v001-preview.png"
        self.assertTrue(layout_path.is_file())
        self.assertTrue(html_path.is_file())
        self.assertTrue(preview_path.is_file())
        layout = json.loads(layout_path.read_text(encoding="utf-8"))
        page_html = html_path.read_text(encoding="utf-8")
        source_paragraphs = [
            part.strip()
            for part in source_path.read_text(encoding="utf-8").split("\n\n")[1:]
            if part.strip()
        ]
        rendered = [
            html_module.unescape(re.sub(r"<[^>]+>", "", value)).strip()
            for value in re.findall(
                r'<p data-source-index="\d+">(.*?)</p>', page_html, flags=re.S
            )
        ]

        self.assertEqual(source_paragraphs[:10], rendered)
        self.assertEqual(
            hashlib.sha256(source_path.read_bytes()).hexdigest(),
            layout["source_sha256"],
        )
        self.assertEqual([1, 10], layout["source_paragraph_range"])
        self.assertEqual([145, 210], layout["page_trim_mm"])
        self.assertEqual("folio-outer", layout["running_header_template"])
        self.assertEqual("approved", layout["design_spec_status"])
        self.assertIn('data-text-layer="editable"', page_html)
        self.assertNotIn("第一章", page_html)
        self.assertNotIn("车窗里的故乡", page_html)

    def test_chapter_01_body_pages_v001_preserve_remaining_text_and_folios(self):
        source_path = PROJECT / "manuscript/chapter-01.md"
        html_path = PROJECT / "body-pages/chapter-01-body-pages-v001.html"
        layout_path = PROJECT / "body-pages/chapter-01-body-pages-v001-layout.json"
        preview_path = PROJECT / "body-pages/chapter-01-body-pages-v001-preview.png"

        self.assertTrue(html_path.is_file())
        self.assertTrue(layout_path.is_file())
        self.assertTrue(preview_path.is_file())

        layout = json.loads(layout_path.read_text(encoding="utf-8"))
        page_html = html_path.read_text(encoding="utf-8")
        source_paragraphs = [
            part.strip()
            for part in source_path.read_text(encoding="utf-8").split("\n\n")[1:]
            if part.strip()
        ]
        rendered_matches = re.findall(
            r'<p data-source-index="(\d+)">(.*?)</p>', page_html, flags=re.S
        )
        rendered_indexes = [int(index) for index, _ in rendered_matches]
        rendered_text = [
            html_module.unescape(re.sub(r"<[^>]+>", "", value)).strip()
            for _, value in rendered_matches
        ]

        self.assertEqual(list(range(11, 50)), rendered_indexes)
        self.assertEqual(source_paragraphs[10:], rendered_text)
        self.assertEqual(
            hashlib.sha256(source_path.read_bytes()).hexdigest(),
            layout["source_sha256"],
        )
        self.assertEqual([11, 49], layout["source_paragraph_range"])
        self.assertEqual(
            {
                "8": [11, 16],
                "9": [17, 22],
                "10": [23, 29],
                "11": [30, 35],
                "12": [36, 42],
                "13": [43, 49],
            },
            layout["page_paragraph_ranges"],
        )
        self.assertEqual([8, 9, 10, 11, 12, 13], layout["folios"])
        self.assertEqual("folio-outer", layout["running_header_template"])
        self.assertEqual("approved-body-opening-v001", layout["design_basis"])
        self.assertIn('data-text-layer="editable"', page_html)
        self.assertEqual(
            ["8", "9", "10", "11", "12", "13"],
            re.findall(r'data-folio="(\d+)"', page_html),
        )
        self.assertNotIn("失落人间</span>", page_html)
        self.assertNotIn("车窗里的故乡</span>", page_html)

    def test_chapter_01_typeset_v002_applies_literary_publishing_baseline(self):
        source_path = PROJECT / "manuscript/chapter-01.md"
        html_path = PROJECT / "typeset/chapter-01-typeset-v002.html"
        layout_path = PROJECT / "typeset/chapter-01-typeset-v002-layout.json"
        preview_path = PROJECT / "typeset/chapter-01-typeset-v002-preview.png"

        self.assertTrue(html_path.is_file())
        self.assertTrue(layout_path.is_file())
        self.assertTrue(preview_path.is_file())

        layout = json.loads(layout_path.read_text(encoding="utf-8"))
        page_html = html_path.read_text(encoding="utf-8")
        source_paragraphs = [
            part.strip()
            for part in source_path.read_text(encoding="utf-8").split("\n\n")[1:]
            if part.strip()
        ]
        rendered_matches = re.findall(
            r'<p data-source-index="(\d+)">(.*?)</p>', page_html, flags=re.S
        )

        self.assertEqual(
            list(range(1, 50)), [int(index) for index, _ in rendered_matches]
        )
        self.assertEqual(
            source_paragraphs,
            [
                html_module.unescape(re.sub(r"<[^>]+>", "", value)).strip()
                for _, value in rendered_matches
            ],
        )
        self.assertEqual(
            hashlib.sha256(source_path.read_bytes()).hexdigest(),
            layout["source_sha256"],
        )
        self.assertEqual(
            {
                "6": [1, 5],
                "7": [6, 10],
                "8": [11, 18],
                "9": [19, 26],
                "10": [27, 39],
                "11": [40, 49],
            },
            layout["page_paragraph_ranges"],
        )
        self.assertEqual([6, 7, 8, 9, 10, 11], layout["folios"])
        self.assertEqual([145, 210], layout["page_trim_mm"])
        self.assertEqual(10.5, layout["typography"]["body_font_size_pt"])
        self.assertEqual(17.5, layout["typography"]["body_line_height_pt"])
        self.assertEqual(2, layout["typography"]["paragraph_indent_em"])
        self.assertEqual(0, layout["typography"]["paragraph_spacing_pt"])
        self.assertEqual("outer-bottom", layout["folio"]["position"])
        self.assertEqual(12, layout["folio"]["bottom_mm"])
        self.assertEqual("standardized", layout["status"])
        self.assertIn('data-text-layer="editable"', page_html)
        self.assertEqual(
            ["6", "7", "8", "9", "10", "11"],
            re.findall(r'data-folio="(\d+)"', page_html),
        )
        self.assertEqual(
            {"width": 1740, "height": 3840},
            {
                "width": read_image_metadata(preview_path)["width"],
                "height": read_image_metadata(preview_path)["height"],
            },
        )

    def test_toc_direction_b_v001_keeps_test_entries_editable_and_aligned(self):
        layout = self.load("toc/toc-direction-b-v001-layout.json")
        page_html = (PROJECT / "toc/toc-direction-b-v001.html").read_text(
            encoding="utf-8"
        )
        expected = [
            ("序章", "灯灭以前", 1),
            ("第一章", "车窗里的故乡", 6),
            ("第二章", "白昼的缝隙", 24),
            ("第三章", "没有回声的房间", 42),
            ("第四章", "雨停在城外", 62),
            ("第五章", "旧门向里开", 84),
            ("第六章", "乡音之外", 106),
            ("第七章", "临时住址", 130),
            ("第八章", "人间无岸", 154),
        ]

        self.assertEqual(
            expected,
            [(item["level"], item["title"], item["page"]) for item in layout["entries"]],
        )
        self.assertEqual([145, 210], layout["page_trim_mm"])
        self.assertEqual("prototype", layout["status"])
        self.assertTrue(layout["test_content"]["synthetic_titles"])
        self.assertTrue(layout["test_content"]["provisional_pages"])
        self.assertIn('data-text-layer="editable"', page_html)
        self.assertEqual(9, page_html.count('class="toc-entry"'))
        self.assertNotIn("toc-component-selection", layout)
        self.assertEqual(
            {"width": 1740, "height": 1260},
            {
                "width": read_image_metadata(
                    PROJECT / "toc/toc-direction-b-v001-preview.png"
                )["width"],
                "height": read_image_metadata(
                    PROJECT / "toc/toc-direction-b-v001-preview.png"
                )["height"],
            },
        )

    def test_title_page_v001_uses_exact_editable_text_and_studio_mark(self):
        layout_path = PROJECT / "title-page/title-page-v001-layout.json"
        html_path = PROJECT / "title-page/title-page-v001.html"
        preview_path = PROJECT / "title-page/title-page-v001-preview.png"

        self.assertTrue(layout_path.is_file(), layout_path)
        self.assertTrue(html_path.is_file(), html_path)
        self.assertTrue(preview_path.is_file(), preview_path)

        layout = json.loads(layout_path.read_text(encoding="utf-8"))
        page_html = html_path.read_text(encoding="utf-8")
        expected = [
            ("title", "失落人间"),
            ("subtitle", "在所有归途之外"),
            ("author", "早睡的猫"),
            ("studio_mark", "纸船工作室"),
        ]

        self.assertEqual("TITLE-PAGE-LOST-HUMAN-WORLD-V001", layout["layout_id"])
        self.assertEqual([145, 210], layout["page_trim_mm"])
        self.assertEqual([290, 210], layout["spread_trim_mm"])
        self.assertEqual("blank-verso", layout["left_page"])
        self.assertFalse(layout["visible_running_headers"])
        self.assertFalse(layout["visible_folios"])
        self.assertEqual(
            expected,
            [(item["role"], item["value"]) for item in layout["text_layers"]],
        )
        self.assertNotIn("publisher", json.dumps(layout, ensure_ascii=False))
        self.assertEqual(4, page_html.count('data-text-layer="editable"'))
        for role, value in expected:
            with self.subTest(role=role):
                self.assertIn(f'data-role="{role}"', page_html)
                self.assertIn(value, page_html)
        self.assertNotIn('data-role="publisher"', page_html)
        self.assertEqual(
            {"width": 1740, "height": 1260},
            {
                "width": read_image_metadata(preview_path)["width"],
                "height": read_image_metadata(preview_path)["height"],
            },
        )

    def test_running_headers_b_v001_use_real_text_and_mirrored_sources(self):
        source = (PROJECT / "manuscript/chapter-01.md").read_text(encoding="utf-8")
        source_paragraphs = [
            value.strip() for value in source.split("\n\n")[1:] if value.strip()
        ]
        layout = self.load("running-headers/running-headers-b-v001-layout.json")
        page_html = (
            PROJECT / "running-headers/running-headers-b-v001.html"
        ).read_text(encoding="utf-8")
        rendered = [
            html_module.unescape(re.sub(r"<[^>]+>", "", value)).strip()
            for value in re.findall(
                r'<p data-source-index="\d+">(.*?)</p>', page_html, flags=re.S
            )
        ]

        self.assertEqual(source_paragraphs[10:18], rendered)
        self.assertEqual(
            "失落人间", layout["running_headers"]["verso_source_value"]
        )
        self.assertEqual(
            "车窗里的故乡", layout["running_headers"]["recto_source_value"]
        )
        self.assertEqual("outer-bottom", layout["folio"]["position"])
        self.assertEqual(12, layout["folio"]["bottom_mm"])
        self.assertEqual(
            ["chapter-opener", "blank", "full-bleed-image"],
            layout["hidden_page_types"],
        )
        self.assertIn('data-running-source="book-title"', page_html)
        self.assertIn('data-running-source="chapter-title"', page_html)
        self.assertEqual(
            {"width": 1740, "height": 1260},
            {
                "width": read_image_metadata(
                    PROJECT
                    / "running-headers/running-headers-b-v001-preview.png"
                )["width"],
                "height": read_image_metadata(
                    PROJECT
                    / "running-headers/running-headers-b-v001-preview.png"
                )["height"],
            },
        )

    def test_approved_chapter_selection_is_bound_to_the_two_user_chosen_cases(self):
        selection = self.load("chapter-opener/reference-selection-A.json")

        self.assertEqual(
            [], validate_data(selection, "book-component-reference-selection")
        )
        self.assertEqual("approved", selection["status"])
        self.assertEqual(
            "SEL-LOST-HUMAN-WORLD-CHAPTER-A-001",
            selection["selection_id"],
        )
        self.assertEqual(
            ["CHO-CN-0006", "CHO-CN-0011"],
            [item["record_id"] for item in selection["selected_references"]],
        )

    def test_chapter_opener_master_is_reusable_and_keeps_text_editable(self):
        master = self.load("chapter-opener/chapter-opener-master.json")
        preview = (PROJECT / "chapter-opener/chapter-opener-preview.html").read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            {
                "version",
                "project_id",
                "component_type",
                "master_id",
                "page_geometry",
                "reference_ids",
                "palette",
                "layout",
                "editable_text",
                "background",
                "visibility_rules",
                "reuse_rules",
            },
            set(master),
        )
        self.assertEqual("BOOK-LOST-HUMAN-WORLD", master["project_id"])
        self.assertEqual("chapter-opener", master["component_type"])
        self.assertEqual([145, 210], master["page_geometry"]["trim_mm"])
        self.assertEqual(3, master["page_geometry"]["bleed_mm"])
        self.assertEqual(["CHO-CN-0006", "CHO-CN-0011"], master["reference_ids"])
        self.assertEqual("第一章", master["editable_text"]["chapter_number"]["value"])
        self.assertEqual("车窗里的故乡", master["editable_text"]["chapter_title"]["value"])
        self.assertTrue(master["editable_text"]["chapter_number"]["editable"])
        self.assertTrue(master["editable_text"]["chapter_title"]["editable"])
        self.assertEqual("hidden", master["visibility_rules"]["running_header"])
        self.assertEqual("hidden", master["visibility_rules"]["folio"])
        self.assertIn('data-layer="editable-text"', preview)
        self.assertIn("第一章", preview)
        self.assertIn("车窗里的", preview)
        self.assertIn("故乡", preview)
        self.assertNotIn("<img", preview.lower())
        self.assertNotIn("<canvas", preview.lower())

    def test_ebook_v001_is_a_browsable_single_file_with_complete_chapter_one(self):
        ebook_path = PROJECT / "ebook/lost-human-world-ebook-v001.html"
        preview_path = PROJECT / "ebook/lost-human-world-ebook-v001-preview.png"
        source = (PROJECT / "manuscript/chapter-01.md").read_text(encoding="utf-8")
        source_paragraphs = [
            value.strip() for value in source.split("\n\n")[1:] if value.strip()
        ]
        self.assertTrue(ebook_path.is_file(), ebook_path)
        self.assertTrue(preview_path.is_file(), preview_path)
        ebook = ebook_path.read_text(encoding="utf-8")
        rendered = [
            html_module.unescape(re.sub(r"<[^>]+>", "", value)).strip()
            for value in re.findall(
                r'<p data-source-index="\d+">(.*?)</p>', ebook, flags=re.S
            )
        ]

        self.assertEqual(49, len(source_paragraphs))
        self.assertEqual(source_paragraphs, rendered)
        self.assertEqual(
            [
                "cover",
                "title-page",
                "toc",
                "chapter-opener",
                "body-6-7",
                "body-8-9",
                "body-10-11",
            ],
            re.findall(r'data-spread-id="([^"]+)"', ebook),
        )
        self.assertIn('data-book-id="BOOK-LOST-HUMAN-WORLD"', ebook)
        self.assertIn('src="../generated/cover-v001.png"', ebook)
        self.assertIn('data-role="studio_mark">纸船工作室</', ebook)
        self.assertIn('id="previous-spread"', ebook)
        self.assertIn('id="next-spread"', ebook)
        self.assertIn('id="toc-toggle"', ebook)
        self.assertIn('aria-keyshortcuts="ArrowLeft"', ebook)
        self.assertIn('aria-keyshortcuts="ArrowRight"', ebook)
        self.assertIn('data-reader-state="ready"', ebook)
        self.assertNotRegex(ebook, r"(?i)\b(?:TBD|TODO|Lorem ipsum)\b")
        self.assertEqual(
            {"width": 1740, "height": 1260},
            {
                "width": read_image_metadata(preview_path)["width"],
                "height": read_image_metadata(preview_path)["height"],
            },
        )

    def test_retrieval_is_available_exactly_five_and_book_distinct(self):
        result = self.load("retrieval/retrieval-result.json")

        self.assertEqual([], validate_data(result, "book-component-retrieval-result"))
        self.assertEqual("available", result["status"])
        self.assertEqual("cover", result["component_type"])
        self.assertEqual("QUERY-COV-LOST-HUMAN-WORLD-0001", result["query_id"])
        self.assertEqual(5, len(result["candidates"]))
        self.assertEqual(
            5,
            len({candidate["book_case_id"] for candidate in result["candidates"]}),
        )


if __name__ == "__main__":
    unittest.main()
