from __future__ import annotations

import copy
import unittest

from ai.contracts import validate_data
from tests.test_component_kb_contracts import (
    valid_component_prompt,
    valid_contract_examples,
)


INTEGRATED_TEXT = [
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
BACKUP = {item["text_id"]: item["value"] for item in INTEGRATED_TEXT}
TEXT_CHECKS = (
    "integrated_text_exact",
    "no_extra_text",
    "typography_usable",
    "machine_identifiers_absent",
)


def integrated_prompt() -> dict:
    prompt = valid_component_prompt()
    prompt["text_rendering_mode"] = "integrated-typography"
    prompt["compiled_blocks"]["INTEGRATED_TEXT"] = (
        "front/title=失落人间; front/subtitle=在所有归途之外; "
        "front/author=早睡的猫"
    )
    prompt["generation_constraints"]["readable_text"] = "exact-project-text"
    prompt["integrated_text"] = copy.deepcopy(INTEGRATED_TEXT)
    prompt["editable_text_backup"] = copy.deepcopy(BACKUP)
    return prompt


def integrated_review() -> dict:
    review = valid_contract_examples()["book-component-image-review"]
    review["text_rendering_mode"] = "integrated-typography"
    review["integrated_text"] = copy.deepcopy(INTEGRATED_TEXT)
    review["checks"].update({name: True for name in TEXT_CHECKS})
    return review


class CoverIntegratedTypographyContractTests(unittest.TestCase):
    def test_project_accepts_optional_structured_author_and_subtitle(self) -> None:
        project = {
            "version": "1.0",
            "project_id": "BOOK-LOST-HUMAN-WORLD",
            "title": "失落人间",
            "subtitle": "在所有归途之外",
            "author": "早睡的猫",
            "mode": "template",
            "primary_category": "literary-fiction",
            "tags": ["double-displacement"],
            "confirmer": "用户",
            "page_plan": {"fixed_pages": 1},
        }
        self.assertEqual([], validate_data(project, "project-config"))

    def test_legacy_prompt_remains_valid_without_mode(self) -> None:
        self.assertEqual([], validate_data(valid_component_prompt(), "book-component-prompt"))

    def test_integrated_cover_prompt_requires_closed_text_contract(self) -> None:
        prompt = integrated_prompt()
        self.assertEqual([], validate_data(prompt, "book-component-prompt"))
        for field in ("integrated_text", "editable_text_backup"):
            with self.subTest(field=field):
                broken = copy.deepcopy(prompt)
                del broken[field]
                self.assertTrue(validate_data(broken, "book-component-prompt"))
        broken = copy.deepcopy(prompt)
        del broken["compiled_blocks"]["INTEGRATED_TEXT"]
        self.assertTrue(validate_data(broken, "book-component-prompt"))

    def test_integrated_typography_is_cover_only(self) -> None:
        prompt = integrated_prompt()
        prompt["component_type"] = "toc"
        self.assertTrue(validate_data(prompt, "book-component-prompt"))

    def test_integrated_entry_schema_is_closed_and_restricts_surface_and_role(self) -> None:
        entry = copy.deepcopy(INTEGRATED_TEXT[0])
        self.assertEqual(
            [], validate_data(entry, "book-component-integrated-text-entry")
        )
        for mutation in ("surface", "role", "extra"):
            with self.subTest(mutation=mutation):
                broken = copy.deepcopy(entry)
                if mutation == "surface":
                    broken["surface"] = "flap"
                elif mutation == "role":
                    broken["role"] = "isbn"
                else:
                    broken["free_text"] = "unsafe"
                self.assertTrue(
                    validate_data(broken, "book-component-integrated-text-entry")
                )

    def test_integrated_review_requires_all_text_checks(self) -> None:
        review = integrated_review()
        self.assertEqual([], validate_data(review, "book-component-image-review"))
        for name in TEXT_CHECKS:
            with self.subTest(name=name):
                broken = copy.deepcopy(review)
                del broken["checks"][name]
                self.assertTrue(validate_data(broken, "book-component-image-review"))


if __name__ == "__main__":
    unittest.main()
