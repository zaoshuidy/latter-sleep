from __future__ import annotations

import copy
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from ai.book_component_kb.build import build_library
from ai.book_component_kb.retrieve import retrieve
from ai.book_component_kb.validate import validate_library
from ai.contracts import validate_data


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "component-kb"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class ChapterOpenerKnowledgeBaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.library_root = Path(self.temp_dir.name) / "book-component-libraries"
        self.component_root = self.library_root / "chapter-opener"
        self.records_root = self.component_root / "records"
        self.assets_root = self.component_root / "assets"
        self.records_root.mkdir(parents=True)
        self.assets_root.mkdir()
        self.registry_path = self.library_root / "source-registry.json"
        registry = load_json(FIXTURE_ROOT / "source-registry.json")
        registry["sources"] = registry["sources"][:1]
        write_json(self.registry_path, registry)

    def _png_bytes(self, seed: str = "chapter-opener") -> bytes:
        digest = hashlib.sha256(seed.encode("utf-8")).digest()
        output = io.BytesIO()
        Image.new("RGB", (18, 24), tuple(digest[:3])).save(output, format="PNG")
        return output.getvalue()

    def _record(self, index: int = 1) -> dict[str, object]:
        record = copy.deepcopy(load_json(FIXTURE_ROOT / "cover-record.json"))
        record_id = f"CHO-CN-{index:04d}"
        asset = self._png_bytes(record_id)
        record.update(
            {
                "record_id": record_id,
                "component_type": "chapter-opener",
                "component_profile": {
                    "opening_mode": "single-page",
                    "visual_strategy": "mixed",
                    "chapter_number_zone": "top",
                    "chapter_title_zone": "center",
                    "image_role": "decoration",
                    "text_image_relationship": "separate",
                    "whitespace": "high",
                },
            }
        )
        record["identity"]["book_case_id"] = f"BOOK-CN-{index + 50:04d}"
        record["asset"] = {
            "relative_path": f"chapter-opener/assets/{record_id}.png",
            "sha256": hashlib.sha256(asset).hexdigest(),
            "mime_type": "image/png",
            "width": 18,
            "height": 24,
        }
        return record

    def _write_record_and_asset(self, index: int = 1) -> None:
        record = self._record(index)
        record_id = record["record_id"]
        (self.assets_root / f"{record_id}.png").write_bytes(self._png_bytes(record_id))
        write_json(self.records_root / f"{record_id}.json", record)

    def test_schema_requires_a_closed_chapter_opener_profile(self) -> None:
        record = self._record()

        self.assertEqual([], validate_data(record, "book-component-reference-record"))
        del record["component_profile"]["chapter_title_zone"]

        self.assertTrue(validate_data(record, "book-component-reference-record"))

    def test_builder_derives_chapter_specific_categories_and_index(self) -> None:
        self._write_record_and_asset()

        result = build_library(self.component_root, self.registry_path)

        self.assertEqual("building", result["status"])
        self.assertEqual([], result["errors"])
        expected_categories = {
            "by-chapter-title-zone.json",
            "by-image-role.json",
            "by-opening-mode.json",
            "by-publication-year.json",
            "by-visual-strategy.json",
        }
        self.assertEqual(
            expected_categories,
            {path.name for path in (self.component_root / "categories").iterdir()},
        )
        retrieval = load_json(self.component_root / "retrieval-index.json")
        self.assertEqual("chapter-opener", retrieval["component"])
        self.assertEqual(
            {
                "record_id",
                "book_case_id",
                "source_registry_id",
                "component",
                "publication_year",
                "lifecycle",
                "opening_mode",
                "visual_strategy",
                "chapter_number_zone",
                "chapter_title_zone",
                "image_role",
                "text_image_relationship",
                "whitespace",
                "style_tags",
                "content_tags",
                "color_tags",
                "mood_tags",
            },
            set(retrieval["entries"][0]),
        )

    def test_validator_accepts_the_built_chapter_library_without_repairing_it(self) -> None:
        self._write_record_and_asset()
        build_library(self.component_root, self.registry_path)

        report = validate_library(self.component_root, self.registry_path, required_count=1)

        self.assertTrue(report["valid"])
        self.assertEqual("available", report["status"])
        self.assertEqual(1, report["record_count"])
        self.assertEqual([], report["errors"])
        self.assertEqual(
            {"records": 1, "assets": 1, "books": 1, "categories": 5, "derived": 7},
            report["counts"],
        )

    def test_chapter_retrieval_scores_its_own_fields_and_returns_five_books(self) -> None:
        for index in range(1, 51):
            self._write_record_and_asset(index)
        build_library(self.component_root, self.registry_path)
        query = {
            "schema_version": "1.0",
            "query_id": "QUERY-CHO-0001",
            "component_type": "chapter-opener",
            "field_targets": {
                "opening_mode": ["single-page"],
                "visual_strategy": ["mixed"],
                "chapter_number_zone": ["top"],
                "chapter_title_zone": ["center"],
                "image_role": ["decoration"],
                "text_image_relationship": ["separate"],
                "whitespace": ["high"],
            },
            "selection_policy": {"max_results": 5, "diversity": "strict"},
        }

        result = retrieve(self.component_root, self.registry_path, query, limit=5)

        self.assertEqual("chapter-opener", result["component_type"])
        self.assertEqual(5, len(result["candidates"]))
        self.assertEqual(5, len({item["book_case_id"] for item in result["candidates"]}))
        self.assertEqual(
            {
                "opening_mode": 0.15,
                "visual_strategy": 0.15,
                "chapter_number_zone": 0.15,
                "chapter_title_zone": 0.20,
                "image_role": 0.15,
                "text_image_relationship": 0.10,
                "whitespace": 0.10,
            },
            result["candidates"][0]["field_scores"],
        )
        self.assertEqual(1.0, result["candidates"][0]["total_score"])

    def test_production_library_keeps_the_second_research_batch_closed(self) -> None:
        library_root = REPOSITORY_ROOT / "knowledge" / "book-component-libraries"
        component_root = library_root / "chapter-opener"
        registry_path = library_root / "source-registry.json"

        build_library(component_root, registry_path)
        first_manifest = (component_root / "manifest.json").read_bytes()
        build_library(component_root, registry_path)
        second_manifest = (component_root / "manifest.json").read_bytes()
        report = validate_library(component_root, registry_path)

        self.assertEqual(first_manifest, second_manifest)
        self.assertTrue(report["valid"])
        self.assertGreaterEqual(report["record_count"], 35)
        self.assertEqual([], report["errors"])
        self.assertEqual(report["record_count"], report["counts"]["assets"])
        self.assertEqual(report["record_count"], report["counts"]["books"])
        expected_status = "available" if report["record_count"] >= 50 else "building"
        self.assertEqual(expected_status, report["status"])


if __name__ == "__main__":
    unittest.main()
