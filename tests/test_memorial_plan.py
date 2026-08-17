import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "plan-memorial-book" / "scripts" / "plan_memorial.py"


def load_module():
    spec = importlib.util.spec_from_file_location("book_plan_memorial", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load plan_memorial.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MemorialPlanTests(unittest.TestCase):
    def test_content_map_covers_axes_and_preserves_source_bytes(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "memory.txt"
            original = "父亲在桥边等我。\n".encode("utf-8")
            source.write_bytes(original)
            content_map = module.build_content_map(
                "P-200",
                {"TXT-001": source},
                {
                    "people": [{"name": "父亲", "source_ids": ["TXT-001"]}],
                    "times": [],
                    "places": [{"name": "桥边", "source_ids": ["TXT-001"]}],
                    "events": [],
                    "themes": [],
                    "image_links": [],
                    "gaps": [{"field": "time", "status": "待确认"}],
                },
            )
            self.assertEqual(original, source.read_bytes())
            self.assertEqual(hashlib.sha256(original).hexdigest(), content_map["source_text_hashes"]["TXT-001"])
            for key in ["people", "times", "places", "events", "themes", "image_links", "gaps"]:
                self.assertIn(key, content_map)

    def test_structure_options_require_two_or_three_candidates(self):
        module = load_module()
        one = [{"option_id": "S1", "bases": ["time"], "rationale": "按明确年代线索组织", "unit_order": ["U1"]}]
        with self.assertRaisesRegex(ValueError, "2 or 3"):
            module.validate_structure_options(one)
        with self.assertRaisesRegex(ValueError, "2 or 3"):
            module.validate_structure_options(one * 4)

    def test_non_chronological_structures_are_first_class(self):
        module = load_module()
        options = [
            {"option_id": "S1", "bases": ["object"], "rationale": "以有来源的物件为记忆入口", "unit_order": ["U2", "U1"]},
            {"option_id": "S2", "bases": ["place", "relationship"], "rationale": "按地点与关系交叉组织", "unit_order": ["U1", "U2"]},
        ]
        self.assertEqual(options, module.validate_structure_options(options))

    def test_toc_titles_keep_source_title_and_confirmation_state(self):
        module = load_module()
        entries = [
            {
                "entry_id": "C01",
                "source_title": "桥边",
                "candidate_title": "桥边等候的人",
                "source_unit_ids": ["U1"],
                "confirmation_status": "pending",
            }
        ]
        brief = module.build_toc_brief("P-200", entries)
        self.assertEqual("桥边", brief["entries"][0]["source_title"])
        self.assertEqual("pending", brief["entries"][0]["confirmation_status"])


if __name__ == "__main__":
    unittest.main()
