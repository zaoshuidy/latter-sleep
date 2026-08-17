import importlib.util
import json
import unittest
from pathlib import Path

from ai.contracts import validate_data


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "design-book-editorial" / "scripts" / "check_case_library.py"
INDEX = ROOT / "knowledge" / "indexes" / "design-case-index.json"
TEMPLATES = ROOT / "templates" / "running-headers"
SKILL = ROOT / "skills" / "design-book-editorial" / "SKILL.md"
FONTS_REFERENCE = ROOT / "skills" / "design-book-editorial" / "references" / "fonts.md"
RUNNING_HEADERS_REFERENCE = (
    ROOT / "skills" / "design-book-editorial" / "references" / "running-headers.md"
)
COMPONENTS = ["cover", "toc", "chapter-opener", "body", "image-page", "running-headers"]


def load_checker():
    spec = importlib.util.spec_from_file_location("check_case_library", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_case_library.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.check_case_library


class EditorialDesignTests(unittest.TestCase):
    def test_standard_32mo_literary_body_uses_consensus_defaults_without_reasking(self):
        skill = SKILL.read_text(encoding="utf-8")
        fonts = FONTS_REFERENCE.read_text(encoding="utf-8")
        running_headers = RUNNING_HEADERS_REFERENCE.read_text(encoding="utf-8")

        for required in (
            "145 × 210 mm",
            "10.5 pt",
            "17—18 pt",
            "2 em",
            "0 pt",
            "不再逐项询问用户",
        ):
            with self.subTest(required=required):
                self.assertIn(required, skill + fonts)

        for required in (
            "folio-outer",
            "外侧底部",
            "12 mm",
            "不设置书名或章名页眉",
            "不得放在装订侧",
        ):
            with self.subTest(required=required):
                self.assertIn(required, running_headers)

    def test_case_library_has_ten_confirmed_cases_per_component(self):
        checker = load_checker()
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        result = checker(index, COMPONENTS, minimum=10)
        self.assertTrue(result["ok"], result["missing"])
        self.assertEqual({component: 10 for component in COMPONENTS}, result["confirmed_counts"])

    def test_confirmed_cases_are_traceable_and_transform_references(self):
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        required = {
            "case_id", "source_url", "source_type", "book_category", "page_component",
            "verification_status", "verified_at", "design_facts", "reuse_scope",
            "borrowed_elements", "changed_elements",
        }
        for case in index["cases"]:
            self.assertTrue(required.issubset(case), case.get("case_id"))
            if case["verification_status"] == "confirmed":
                self.assertTrue(case["source_url"].startswith("https://"))
                self.assertTrue(case["design_facts"])
                self.assertTrue(case["borrowed_elements"])
                self.assertTrue(case["changed_elements"])

    def test_design_genome_keeps_five_to_eight_page_families(self):
        base = {
            "version": "1.0", "project_id": "P-300", "direction_id": "D1",
            "reference_ids": ["CASE-001"], "brand_profile": "paper-boat",
            "color": {}, "fonts": {}, "grid": {}, "toc": {}, "chapter_opener": {},
            "running_headers": {},
        }
        base["page_families"] = ["cover", "toc", "chapter", "body"]
        self.assertTrue(validate_data(base, "design-genome"))
        base["page_families"].append("image")
        self.assertEqual([], validate_data(base, "design-genome"))

    def test_running_header_templates_are_reusable_and_exclude_copyright_page(self):
        required = {"template_id", "left_source", "right_source", "folio_position", "hidden_page_types", "long_title_fallback", "variables"}
        expected = {"paired-standard", "folio-centered", "folio-outer"}
        found = set()
        for path in TEMPLATES.glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            found.add(data["template_id"])
            self.assertEqual(required, set(data))
            self.assertNotIn("copyright", data["hidden_page_types"])
            self.assertEqual({"font", "color", "book_title", "chapter_title"}, set(data["variables"]))
        self.assertEqual(expected, found)


if __name__ == "__main__":
    unittest.main()
