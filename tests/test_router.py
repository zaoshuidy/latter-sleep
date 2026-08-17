import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "book-production-router" / "scripts" / "create_project.py"


def load_create_project():
    spec = importlib.util.spec_from_file_location("book_create_project", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load create_project.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.create_project


class RouterTests(unittest.TestCase):
    def test_memorial_project_can_start_with_missing_assets(self):
        create_project = load_create_project()
        project, manifest, open_items = create_project(
            {
                "project_id": "P-100",
                "title": "父亲的四季",
                "mode": "memorial",
                "primary_category": "family-memorial",
                "tags": ["old-photos"],
                "confirmer": "Edy",
                "page_plan": {"min_pages": 80, "max_pages": 120},
                "assets": [
                    {"asset_id": "TXT-001", "asset_type": "text", "original_path": "text/01.md", "state": "received"},
                    {"asset_id": "IMG-001", "asset_type": "image", "original_path": "images/childhood.jpg", "state": "missing"},
                ],
            }
        )
        self.assertEqual("memorial", project["mode"])
        self.assertEqual("family-memorial", project["primary_category"])
        self.assertEqual(2, len(manifest["assets"]))
        self.assertEqual("IMG-001", open_items[0]["asset_id"])

    def test_hybrid_project_requires_primary_mode(self):
        create_project = load_create_project()
        with self.assertRaisesRegex(ValueError, "primary_mode"):
            create_project(
                {
                    "project_id": "P-101",
                    "title": "混合项目",
                    "mode": "hybrid",
                    "primary_category": "life-memorial",
                    "tags": [],
                    "confirmer": "Edy",
                    "page_plan": {"min_pages": 64, "max_pages": 96},
                    "assets": [],
                }
            )

    def test_template_project_requires_fixed_pages(self):
        create_project = load_create_project()
        with self.assertRaisesRegex(ValueError, "fixed_pages"):
            create_project(
                {
                    "project_id": "P-102",
                    "title": "成长模板书",
                    "mode": "template",
                    "primary_category": "growth-memorial",
                    "tags": [],
                    "confirmer": "Edy",
                    "page_plan": {"min_pages": 24, "max_pages": 24},
                    "assets": [],
                }
            )


if __name__ == "__main__":
    unittest.main()
