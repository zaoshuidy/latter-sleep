import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "build-template-book" / "scripts" / "validate_slots.py"


def load_validate_slots():
    spec = importlib.util.spec_from_file_location("book_validate_slots", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load validate_slots.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_slots


def sample_template():
    return {
        "version": "1.0",
        "template_id": "T-24",
        "fixed_pages": 2,
        "pages": [
            {
                "page_number": 1,
                "family_id": "chapter-opener",
                "slots": [
                    {
                        "slot_id": "P01-T01",
                        "slot_type": "text",
                        "required": True,
                        "capacity_chars": 20,
                        "source_asset_id": "TXT-001",
                    }
                ],
            },
            {
                "page_number": 2,
                "family_id": "image-text",
                "slots": [
                    {
                        "slot_id": "P02-I01",
                        "slot_type": "image",
                        "required": True,
                        "aspect_ratio": 1.5,
                        "source_asset_id": "IMG-001",
                    },
                    {
                        "slot_id": "P02-I02",
                        "slot_type": "image",
                        "required": False,
                        "aspect_ratio": 1.0,
                    },
                ],
            },
        ],
    }


class TemplateBookTests(unittest.TestCase):
    def test_ready_required_and_unfilled_optional_slots(self):
        validate_slots = load_validate_slots()
        report = validate_slots(
            sample_template(),
            {
                "TXT-001": {"asset_type": "text", "char_count": 12},
                "IMG-001": {"asset_type": "image", "aspect_ratio": 1.5},
            },
        )
        by_id = {item["slot_id"]: item for item in report}
        self.assertEqual("ready", by_id["P01-T01"]["status"])
        self.assertEqual("unfilled_optional", by_id["P02-I02"]["status"])
        self.assertEqual(
            {"slot_id", "status", "source_asset_id", "reason", "suggested_actions"},
            set(by_id["P01-T01"]),
        )

    def test_missing_required_slot_is_reported(self):
        validate_slots = load_validate_slots()
        template = sample_template()
        del template["pages"][0]["slots"][0]["source_asset_id"]
        report = validate_slots(template, {"IMG-001": {"asset_type": "image", "aspect_ratio": 1.5}})
        self.assertEqual("missing_required", report[0]["status"])

    def test_duplicate_asset_is_not_silent(self):
        validate_slots = load_validate_slots()
        template = sample_template()
        template["pages"][1]["slots"][1]["source_asset_id"] = "IMG-001"
        report = validate_slots(
            template,
            {
                "TXT-001": {"asset_type": "text", "char_count": 12},
                "IMG-001": {"asset_type": "image", "aspect_ratio": 1.5},
            },
        )
        self.assertEqual("duplicate_asset", report[-1]["status"])

    def test_text_overflow_never_suggests_rewriting_or_illegal_shrinking(self):
        validate_slots = load_validate_slots()
        report = validate_slots(
            sample_template(),
            {
                "TXT-001": {"asset_type": "text", "char_count": 80},
                "IMG-001": {"asset_type": "image", "aspect_ratio": 1.5},
            },
        )
        overflow = report[0]
        self.assertEqual("text_overflow", overflow["status"])
        joined = " ".join(overflow["suggested_actions"])
        for forbidden in ["删", "改写", "压缩原文", "缩小字号"]:
            self.assertNotIn(forbidden, joined)
        self.assertIn("增加可变页", joined)

    def test_image_ratio_mismatch_is_reported(self):
        validate_slots = load_validate_slots()
        report = validate_slots(
            sample_template(),
            {
                "TXT-001": {"asset_type": "text", "char_count": 12},
                "IMG-001": {"asset_type": "image", "aspect_ratio": 0.8},
            },
        )
        self.assertEqual("ratio_mismatch", report[1]["status"])

    def test_fixed_page_count_must_match_declared_pages(self):
        validate_slots = load_validate_slots()
        template = sample_template()
        template["fixed_pages"] = 24
        report = validate_slots(template, {})
        self.assertEqual("__template__", report[0]["slot_id"])
        self.assertEqual("page_count_mismatch", report[0]["status"])


if __name__ == "__main__":
    unittest.main()
