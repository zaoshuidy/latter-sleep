import unittest

from ai.contracts import validate_data


class ContractValidationTests(unittest.TestCase):
    def test_project_requires_project_id(self):
        data = {
            "version": "1.0",
            "title": "样书",
            "mode": "memorial",
            "primary_category": "life-memorial",
            "tags": [],
            "confirmer": "Edy",
            "page_plan": {"min_pages": 80, "max_pages": 120},
        }
        self.assertIn("project_id", "\n".join(validate_data(data, "project-config")))

    def test_hybrid_requires_primary_mode(self):
        data = {
            "version": "1.0",
            "project_id": "P-001",
            "title": "混合样书",
            "mode": "hybrid",
            "primary_category": "family-memorial",
            "tags": ["old-photos"],
            "confirmer": "Edy",
            "page_plan": {"min_pages": 64, "max_pages": 96},
        }
        self.assertIn("primary_mode", "\n".join(validate_data(data, "project-config")))

    def test_template_requires_fixed_pages(self):
        data = {
            "version": "1.0",
            "project_id": "P-002",
            "title": "模板样书",
            "mode": "template",
            "primary_category": "growth-memorial",
            "tags": [],
            "confirmer": "Edy",
            "page_plan": {"min_pages": 24, "max_pages": 24},
        }
        self.assertIn("fixed_pages", "\n".join(validate_data(data, "project-config")))

    def test_literary_fiction_category_is_supported(self):
        data = {
            "version": "1.0",
            "project_id": "BOOK-LOST-HUMAN-WORLD",
            "title": "失落人间",
            "mode": "template",
            "primary_category": "literary-fiction",
            "tags": ["double-displacement"],
            "confirmer": "用户",
            "page_size": "145mm × 210mm",
            "page_plan": {"fixed_pages": 1},
        }
        self.assertEqual([], validate_data(data, "project-config"))

    def test_unknown_editorial_category_is_rejected(self):
        data = {
            "version": "1.0",
            "project_id": "BOOK-LOST-HUMAN-WORLD",
            "title": "失落人间",
            "mode": "template",
            "primary_category": "novel-anything",
            "tags": [],
            "confirmer": "用户",
            "page_plan": {"fixed_pages": 1},
        }
        self.assertTrue(validate_data(data, "project-config"))

    def test_asset_state_is_restricted(self):
        data = {
            "version": "1.0",
            "project_id": "P-001",
            "assets": [
                {
                    "asset_id": "IMG-001",
                    "asset_type": "image",
                    "original_path": "assets/photo.jpg",
                    "state": "ready",
                }
            ],
        }
        self.assertIn("received", "\n".join(validate_data(data, "asset-manifest")))

    def test_image_manifest_rejects_inline_prompt(self):
        data = {
            "version": "1.0",
            "project_id": "P-001",
            "images": [
                {
                    "image_id": "GEN-001",
                    "image_role": "design",
                    "use": "chapter-opener",
                    "skill": "imagegen",
                    "prompt": "a long inline prompt",
                    "output_file": "images/GEN-001.png",
                    "status": "selected",
                }
            ],
        }
        self.assertIn("prompt", "\n".join(validate_data(data, "image-manifest")))


if __name__ == "__main__":
    unittest.main()
